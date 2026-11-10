"""Declarative FFmpeg complex-filtergraph builder with speed ramps, cinematic looks, and ASS burn-in."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from backend.api.schemas import (
    AspectRatio,
    ColorGradePreset,
    MediaAsset,
    MediaClip,
    ResolutionPreset,
    SpeedRampPreset,
    TimelinePlan,
    TransitionType,
)
from backend.audio_engine.mixer import (
    ResolvedAudioSource,
    build_atempo_chain,
    build_music_mix_filters,
)
from backend.video_engine.typography import format_ass_filter_arg

_SHORT_EDGE = {
    "540p": 540,
    "720p": 720,
    "1080p": 1080,
    "4k": 2160,
}

_ASPECT_RATIOS: dict[AspectRatio, tuple[int, int]] = {
    "16:9": (16, 9),
    "9:16": (9, 16),
    "1:1": (1, 1),
    "4:5": (4, 5),
    "21:9": (21, 9),
}

_COLOR_GRADE_FILTERS: dict[ColorGradePreset, str] = {
    "natural": "",
    "golden_hour": (
        "colorbalance=rs=0.08:gs=0.02:bs=-0.08:rm=0.06:bm=-0.06,"
        "eq=saturation=1.22:contrast=1.08:brightness=0.02"
    ),
    "cinematic_teal_orange": (
        "colorbalance=rs=-0.10:gs=0.02:bs=0.12:rh=0.10:gh=0.02:bh=-0.10,"
        "eq=contrast=1.18:saturation=1.15"
    ),
    "moody_dark": "eq=contrast=1.20:saturation=0.78:brightness=-0.06",
    "vintage_film": (
        "eq=contrast=0.95:saturation=0.82:gamma=1.05,"
        "colorbalance=rs=0.06:gs=0.03:bs=-0.05"
    ),
    "high_contrast_bw": "hue=s=0,eq=contrast=1.28",
    "bleach_bypass": "eq=contrast=1.32:saturation=0.45:brightness=-0.03",
}

_XFADE_MAP: dict[TransitionType, str] = {
    "crossfade": "fade",
    "fade_from_black": "fadeblack",
    "fade_to_black": "fadeblack",
    "slide_left": "slideleft",
    "slide_right": "slideright",
    "wipe_left": "wipeleft",
    "wipe_right": "wiperight",
    "zoom_in": "circleopen",
    "zoom_out": "radial",
}


@dataclass(frozen=True)
class ResolvedVideoSource:
    """Timeline clip paired with its verified local asset metadata."""

    clip: MediaClip
    asset: MediaAsset


def resolve_canvas_dimensions(aspect_ratio: AspectRatio, resolution: ResolutionPreset) -> tuple[int, int]:
    """Compute even width and height matching target aspect ratio and resolution tier."""
    rw, rh = _ASPECT_RATIOS[aspect_ratio]
    short_edge = _SHORT_EDGE[resolution]

    if rw >= rh:
        height = short_edge
        width = int(round(height * rw / rh))
    else:
        width = short_edge
        height = int(round(width * rh / rw))

    width += width % 2
    height += height % 2
    return width, height


def build_encoder_args(encoder: str, preset: str, quality: int) -> list[str]:
    """Build hardware-specific or CPU H.264 encoder parameters."""
    if encoder == "h264_qsv":
        return ["-c:v", "h264_qsv", "-preset", "medium", "-global_quality", str(quality)]
    if encoder == "h264_nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", str(quality)]
    if encoder == "h264_amf":
        return ["-c:v", "h264_amf", "-quality", "balanced", "-qp_i", str(quality), "-qp_p", str(quality)]
    return ["-c:v", "libx264", "-preset", preset, "-crf", str(quality)]


def _speed_ramp_segments(raw_dur: float, ramp: SpeedRampPreset, base_speed: float) -> list[tuple[float, float, float]]:
    """Return piecewise `(rel_start, rel_end, speed)` segments for a clip."""
    if ramp == "none" or raw_dur < 1.2:
        return [(0.0, raw_dur, base_speed)]

    if ramp == "fast_to_slow":
        split_t = round(raw_dur * 0.4, 3)
        return [(0.0, split_t, 1.6), (split_t, raw_dur, 0.65)]

    if ramp == "slow_to_fast":
        split_t = round(raw_dur * 0.5, 3)
        return [(0.0, split_t, 0.7), (split_t, raw_dur, 1.55)]

    # ease_in_out: gentle 0.75x -> fast 1.5x burst -> smooth 0.75x landing
    t1 = round(raw_dur * 0.3, 3)
    t2 = round(raw_dur * 0.7, 3)
    return [(0.0, t1, 0.75), (t1, t2, 1.5), (t2, raw_dur, 0.75)]


def build_render_command(
    timeline: TimelinePlan,
    resolved_clips: list[ResolvedVideoSource],
    resolved_audio: list[ResolvedAudioSource],
    output_path: str,
    resolution: ResolutionPreset = "1080p",
    encoder: str = "libx264",
    preset: str = "fast",
    quality: int = 21,
    subtitle_ass_path: Optional[Path] = None,
) -> tuple[list[str], float]:
    """Construct complete FFmpeg argument list and return `(args, expected_duration_seconds)`."""
    if not resolved_clips:
        raise ValueError("Timeline must contain at least one resolved video or image clip.")

    width, height = resolve_canvas_dimensions(timeline.aspect_ratio, resolution)
    fps = timeline.fps
    effects = timeline.cinematic_effects

    input_args: list[str] = ["-y", "-hide_banner"]
    filter_parts: list[str] = []
    norm_durations: list[float] = []
    any_foreground_audio = False

    # 1. Add video/image inputs and normalize every stream
    for idx, item in enumerate(resolved_clips):
        clip = item.clip
        asset = item.asset
        is_image = asset.media_kind == "image"

        raw_dur = max(0.2, clip.end_time_seconds - clip.start_time_seconds)
        segments = [(0.0, raw_dur, clip.playback_speed)] if is_image else _speed_ramp_segments(
            raw_dur, clip.speed_ramp, clip.playback_speed
        )
        eff_dur = round(max(0.2, sum((e - s) / sp for s, e, sp in segments)), 3)
        norm_durations.append(eff_dur)

        if is_image:
            input_args.extend(["-loop", "1", "-t", f"{eff_dur:.3f}", "-i", asset.file_path])
        else:
            input_args.extend(
                [
                    "-ss",
                    f"{clip.start_time_seconds:.3f}",
                    "-t",
                    f"{raw_dur:.3f}",
                    "-i",
                    asset.file_path,
                ]
            )

        # Handle multi-segment speed ramps before scaling
        if not is_image and len(segments) > 1:
            split_labels = [f"vr_{idx}_{si}" for si in range(len(segments))]
            filter_parts.append(f"[{idx}:v]split={len(segments)}" + "".join(f"[{lbl}]" for lbl in split_labels))
            ramped_outs: list[str] = []
            for si, (seg_s, seg_e, seg_sp) in enumerate(segments):
                out_lbl = f"vr_done_{idx}_{si}"
                filter_parts.append(
                    f"[{split_labels[si]}]trim=start={seg_s:.3f}:end={seg_e:.3f},"
                    f"setpts=(PTS-STARTPTS)/{seg_sp:.4f}[{out_lbl}]"
                )
                ramped_outs.append(f"[{out_lbl}]")
            v_src_label = f"v_ramped_{idx}"
            filter_parts.append(f"{''.join(ramped_outs)}concat=n={len(segments)}:v=1:a=0[{v_src_label}]")
            v_chain: list[str] = ["setpts=PTS-STARTPTS"]
        else:
            v_src_label = f"{idx}:v"
            if not is_image and abs(clip.playback_speed - 1.0) >= 1e-3:
                v_chain = [f"setpts=(PTS-STARTPTS)/{clip.playback_speed:.4f}"]
            else:
                v_chain = ["setpts=PTS-STARTPTS"]

        # Ken Burns smooth push-in on still images when enabled
        if is_image and effects.ken_burns_on_images:
            total_frames = max(10, int(round(eff_dur * fps)))
            v_chain.extend(
                [
                    f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=decrease",
                    f"pad={width * 2}:{height * 2}:(ow-iw)/2:(oh-ih)/2:color=#0B0D13",
                    f"zoompan=z='min(zoom+0.0008,1.12)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}",
                    "setsar=1",
                    "format=yuv420p",
                    f"trim=duration={eff_dur:.3f}",
                    "setpts=PTS-STARTPTS",
                    "settb=AVTB",
                ]
            )
        else:
            v_chain.extend(
                [
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease",
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=#0B0D13",
                    "setsar=1",
                    f"fps={fps}",
                    "format=yuv420p",
                    f"trim=duration={eff_dur:.3f}",
                    "setpts=PTS-STARTPTS",
                    "settb=AVTB",
                ]
            )

        grade_preset = clip.color_grade or timeline.color_grade
        grade_filter = _COLOR_GRADE_FILTERS.get(grade_preset, "")
        if grade_filter:
            v_chain.append(grade_filter)

        if idx == 0 and clip.transition_in and clip.transition_in.type == "fade_from_black":
            fade_d = min(clip.transition_in.duration_seconds, eff_dur * 0.45)
            if fade_d > 0.05:
                v_chain.append(f"fade=t=in:st=0:d={fade_d:.3f}")

        if idx == len(resolved_clips) - 1 and clip.transition_out and clip.transition_out.type == "fade_to_black":
            fade_d = min(clip.transition_out.duration_seconds, eff_dur * 0.45)
            if fade_d > 0.05:
                v_chain.append(f"fade=t=out:st={round(eff_dur - fade_d, 3)}:d={fade_d:.3f}")

        filter_parts.append(f"[{v_src_label}]{','.join(v_chain)}[v_norm_{idx}]")

        # Audio normalization pipeline (with piecewise atempo for speed ramps, or synthetic silence)
        if not is_image and asset.metadata.has_audio:
            any_foreground_audio = True
            if len(segments) > 1:
                asplit_labels = [f"ar_{idx}_{si}" for si in range(len(segments))]
                filter_parts.append(
                    f"[{idx}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                    f"asplit={len(segments)}" + "".join(f"[{lbl}]" for lbl in asplit_labels)
                )
                aramped_outs: list[str] = []
                for si, (seg_s, seg_e, seg_sp) in enumerate(segments):
                    out_lbl = f"ar_done_{idx}_{si}"
                    at_chain = build_atempo_chain(seg_sp)
                    seg_filters = [
                        f"atrim=start={seg_s:.3f}:end={seg_e:.3f}",
                        "asetpts=PTS-STARTPTS",
                    ]
                    if at_chain:
                        seg_filters.append(at_chain)
                    filter_parts.append(f"[{asplit_labels[si]}]{','.join(seg_filters)}[{out_lbl}]")
                    aramped_outs.append(f"[{out_lbl}]")
                a_src = f"a_ramped_{idx}"
                filter_parts.append(f"{''.join(aramped_outs)}concat=n={len(segments)}:v=0:a=1[{a_src}]")
                a_chain = [f"atrim=duration={eff_dur:.3f}", "asetpts=PTS-STARTPTS"]
            else:
                a_src = f"{idx}:a"
                a_chain = ["aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"]
                atempo = build_atempo_chain(clip.playback_speed)
                if atempo:
                    a_chain.append(atempo)
                a_chain.extend([f"atrim=duration={eff_dur:.3f}", "asetpts=PTS-STARTPTS"])

            if idx == 0 and clip.transition_in and clip.transition_in.type == "fade_from_black":
                fade_d = min(clip.transition_in.duration_seconds, eff_dur * 0.45)
                if fade_d > 0.05:
                    a_chain.append(f"afade=t=in:st=0:d={fade_d:.3f}")
            if idx == len(resolved_clips) - 1 and clip.transition_out and clip.transition_out.type == "fade_to_black":
                fade_d = min(clip.transition_out.duration_seconds, eff_dur * 0.45)
                if fade_d > 0.05:
                    a_chain.append(f"afade=t=out:st={round(eff_dur - fade_d, 3)}:d={fade_d:.3f}")
            filter_parts.append(f"[{a_src}]{','.join(a_chain)}[a_norm_{idx}]")
        else:
            filter_parts.append(
                f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=duration={eff_dur:.3f},asetpts=PTS-STARTPTS[a_norm_{idx}]"
            )

    # 2. Background audio inputs
    music_input_pairs: list[tuple[int, ResolvedAudioSource]] = []
    next_input_idx = len(resolved_clips)
    for resolved_cue in resolved_audio:
        cue = resolved_cue.cue
        input_args.extend(
            [
                "-ss",
                f"{cue.start_time_seconds:.3f}",
                "-t",
                f"{cue.duration_seconds:.3f}",
                "-i",
                resolved_cue.file_path,
            ]
        )
        music_input_pairs.append((next_input_idx, resolved_cue))
        next_input_idx += 1

    # 3. Sequence video/audio clips with xfade or clean concat
    prev_v = "v_norm_0"
    prev_a = "a_norm_0"
    accumulated_dur = norm_durations[0]

    for k in range(1, len(resolved_clips)):
        curr_clip = resolved_clips[k].clip
        prev_clip = resolved_clips[k - 1].clip
        curr_dur = norm_durations[k]

        trans = curr_clip.transition_in or prev_clip.transition_out
        t_type: TransitionType = trans.type if trans else "none"
        req_overlap = trans.duration_seconds if trans else 0.0

        out_v = f"v_seq_{k}"
        out_a = f"a_seq_{k}"

        if t_type == "none" or req_overlap <= 0.05 or t_type not in _XFADE_MAP:
            filter_parts.append(f"[{prev_v}][v_norm_{k}]concat=n=2:v=1:a=0[{out_v}]")
            filter_parts.append(f"[{prev_a}][a_norm_{k}]concat=n=2:v=0:a=1[{out_a}]")
            accumulated_dur = round(accumulated_dur + curr_dur, 3)
        else:
            overlap = round(min(req_overlap, accumulated_dur * 0.45, curr_dur * 0.45), 3)
            if overlap <= 0.05:
                filter_parts.append(f"[{prev_v}][v_norm_{k}]concat=n=2:v=1:a=0[{out_v}]")
                filter_parts.append(f"[{prev_a}][a_norm_{k}]concat=n=2:v=0:a=1[{out_a}]")
                accumulated_dur = round(accumulated_dur + curr_dur, 3)
            else:
                offset = round(max(0.0, accumulated_dur - overlap), 3)
                xfade_name = _XFADE_MAP[t_type]
                filter_parts.append(
                    f"[{prev_v}][v_norm_{k}]xfade=transition={xfade_name}:duration={overlap:.3f}:offset={offset:.3f}[{out_v}]"
                )
                filter_parts.append(
                    f"[{prev_a}][a_norm_{k}]acrossfade=d={overlap:.3f}:c1=tri:c2=tri[{out_a}]"
                )
                accumulated_dur = round(accumulated_dur + curr_dur - overlap, 3)

        prev_v = out_v
        prev_a = out_a

    # 4. Global cinematic finishing (vignette, film grain, and ASS animated typography)
    finishing_filters: list[str] = []
    if effects.vignette:
        finishing_filters.append("vignette=angle=PI/5")
    if effects.film_grain:
        finishing_filters.append("noise=alls=8:allf=t+u")
    if subtitle_ass_path is not None:
        finishing_filters.append(format_ass_filter_arg(subtitle_ass_path))

    final_v_label = prev_v
    if finishing_filters:
        final_v_label = "v_master"
        filter_parts.append(f"[{prev_v}]{','.join(finishing_filters)}[{final_v_label}]")

    # 5. Final background audio mixing, sidechain ducking & loudness normalization
    mix_filters = build_music_mix_filters(
        base_audio_label=prev_a,
        music_inputs=music_input_pairs,
        total_video_duration=accumulated_dur,
        output_label="a_final",
        has_foreground_audio=any_foreground_audio,
        allow_ducking=effects.audio_ducking,
        allow_loudnorm=effects.loudness_normalize,
    )
    filter_parts.extend(mix_filters)

    filter_complex = ";".join(filter_parts)

    cmd = [
        *input_args,
        "-filter_complex",
        filter_complex,
        "-map",
        f"[{final_v_label}]",
        "-map",
        "[a_final]",
        *build_encoder_args(encoder, preset, quality),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    return cmd, accumulated_dur
