"""Declarative FFmpeg complex-filtergraph builder for multi-clip cinematic timelines."""

from __future__ import annotations

from dataclasses import dataclass

from backend.api.schemas import (
    AspectRatio,
    ColorGradePreset,
    MediaAsset,
    MediaClip,
    ResolutionPreset,
    TimelinePlan,
    TransitionType,
)
from backend.audio_engine.mixer import (
    ResolvedAudioSource,
    build_atempo_chain,
    build_music_mix_filters,
)

# Short-edge base sizes for each resolution tier
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

    # Enforce even pixel dimensions required by yuv420p and H.264 encoders
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


def build_render_command(
    timeline: TimelinePlan,
    resolved_clips: list[ResolvedVideoSource],
    resolved_audio: list[ResolvedAudioSource],
    output_path: str,
    resolution: ResolutionPreset = "1080p",
    encoder: str = "libx264",
    preset: str = "fast",
    quality: int = 21,
) -> tuple[list[str], float]:
    """Construct complete FFmpeg argument list and return `(args, expected_duration_seconds)`."""
    if not resolved_clips:
        raise ValueError("Timeline must contain at least one resolved video or image clip.")

    width, height = resolve_canvas_dimensions(timeline.aspect_ratio, resolution)
    fps = timeline.fps

    input_args: list[str] = ["-y", "-hide_banner"]
    filter_parts: list[str] = []
    norm_durations: list[float] = []

    # 1. Add video/image inputs and normalize every stream to identical WxH, fps, SAR, pixel format, timebase
    for idx, item in enumerate(resolved_clips):
        clip = item.clip
        asset = item.asset
        is_image = asset.media_kind == "image"

        raw_dur = max(0.2, clip.end_time_seconds - clip.start_time_seconds)
        eff_dur = round(max(0.2, raw_dur / clip.playback_speed), 3)
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

        # Video normalization pipeline
        v_chain: list[str] = []
        if not is_image and abs(clip.playback_speed - 1.0) >= 1e-3:
            v_chain.append(f"setpts=(PTS-STARTPTS)/{clip.playback_speed:.4f}")
        else:
            v_chain.append("setpts=PTS-STARTPTS")

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

        # Apply per-clip or global color grade
        grade_preset = clip.color_grade or timeline.color_grade
        grade_filter = _COLOR_GRADE_FILTERS.get(grade_preset, "")
        if grade_filter:
            v_chain.append(grade_filter)

        # Opening fade-in on first clip if requested
        if idx == 0 and clip.transition_in and clip.transition_in.type == "fade_from_black":
            fade_d = min(clip.transition_in.duration_seconds, eff_dur * 0.45)
            if fade_d > 0.05:
                v_chain.append(f"fade=t=in:st=0:d={fade_d:.3f}")

        # Closing fade-out on final clip if requested
        if idx == len(resolved_clips) - 1 and clip.transition_out and clip.transition_out.type == "fade_to_black":
            fade_d = min(clip.transition_out.duration_seconds, eff_dur * 0.45)
            if fade_d > 0.05:
                fade_st = round(eff_dur - fade_d, 3)
                v_chain.append(f"fade=t=out:st={fade_st}:d={fade_d:.3f}")

        filter_parts.append(f"[{idx}:v]{','.join(v_chain)}[v_norm_{idx}]")

        # Audio normalization pipeline (or synthetic silence if image / silent video)
        if not is_image and asset.metadata.has_audio:
            a_chain = [
                "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo",
            ]
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
            filter_parts.append(f"[{idx}:a]{','.join(a_chain)}[a_norm_{idx}]")
        else:
            filter_parts.append(
                f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=duration={eff_dur:.3f},asetpts=PTS-STARTPTS[a_norm_{idx}]"
            )

    # 2. Add background audio track inputs (starting after video inputs)
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

    # 4. Final background audio mixing & limiting
    mix_filters = build_music_mix_filters(
        base_audio_label=prev_a,
        music_inputs=music_input_pairs,
        total_video_duration=accumulated_dur,
        output_label="a_final",
    )
    filter_parts.extend(mix_filters)

    filter_complex = ";".join(filter_parts)

    cmd = [
        *input_args,
        "-filter_complex",
        filter_complex,
        "-map",
        f"[{prev_v}]",
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

