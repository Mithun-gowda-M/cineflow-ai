"""FFmpeg audio filter builders for tempo scaling, sidechain ducking, and loudness normalization."""

from __future__ import annotations

from dataclasses import dataclass

from backend.api.schemas import AudioTrackCue


@dataclass(frozen=True)
class ResolvedAudioSource:
    """Audio track cue paired with its verified local filesystem path."""

    cue: AudioTrackCue
    file_path: str


def build_atempo_chain(speed: float) -> str:
    """Build chained `atempo` filters within FFmpeg's [0.5, 2.0] per-stage safe bounds."""
    if abs(speed - 1.0) < 1e-3:
        return ""
    stages: list[float] = []
    remaining = speed
    while remaining > 2.0:
        stages.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        stages.append(0.5)
        remaining /= 0.5
    stages.append(round(remaining, 4))
    return ",".join(f"atempo={s}" for s in stages)


def build_music_mix_filters(
    base_audio_label: str,
    music_inputs: list[tuple[int, ResolvedAudioSource]],
    total_video_duration: float,
    output_label: str = "a_final",
    *,
    has_foreground_audio: bool = False,
    allow_ducking: bool = True,
    allow_loudnorm: bool = True,
) -> list[str]:
    """Generate filtergraph stages for sidechain ducking, mixing, and EBU R128 loudness normalization."""
    post_filter = ",loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.95" if allow_loudnorm else ",alimiter=limit=0.95"
    if not music_inputs:
        if allow_loudnorm:
            return [f"[{base_audio_label}]loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.95[{output_label}]"]
        return [f"[{base_audio_label}]anull[{output_label}]"]

    filters: list[str] = []
    music_labels: list[str] = []
    ducking_requested = False

    for idx, (input_index, resolved) in enumerate(music_inputs):
        cue = resolved.cue
        max_play_dur = max(0.2, min(cue.duration_seconds, total_video_duration - cue.timeline_start_seconds))
        if max_play_dur <= 0.2:
            continue

        if cue.ducking_enabled:
            ducking_requested = True

        # Static gentle trim when foreground audio exists without sidechain, or baseline user volume
        base_vol = cue.volume if has_foreground_audio else cue.volume
        chain = [
            "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo",
            f"atrim=duration={max_play_dur:.3f}",
            "asetpts=PTS-STARTPTS",
            f"volume={round(base_vol, 3)}",
        ]
        if max_play_dur > 1.5:
            fade_start = round(max_play_dur - 1.0, 3)
            chain.append(f"afade=t=out:st={fade_start}:d=1.0")
        if cue.timeline_start_seconds > 0.01:
            delay_ms = int(round(cue.timeline_start_seconds * 1000))
            chain.append(f"adelay={delay_ms}|{delay_ms}")

        label = f"a_music_{idx}"
        filters.append(f"[{input_index}:a]{','.join(chain)}[{label}]")
        music_labels.append(label)

    if not music_labels:
        if allow_loudnorm:
            return [f"[{base_audio_label}]loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.95[{output_label}]"]
        return [f"[{base_audio_label}]anull[{output_label}]"]

    # Combine multiple music cues if present
    if len(music_labels) == 1:
        combined_music = music_labels[0]
    else:
        combined_music = "a_music_bus"
        filters.append(
            f"{''.join(f'[{m}]' for m in music_labels)}amix=inputs={len(music_labels)}:duration=longest:normalize=0[{combined_music}]"
        )

    if has_foreground_audio and ducking_requested and allow_ducking:
        # True sidechain audio ducking: music automatically compresses smoothly under active speech/foreground
        filters.append(f"[{base_audio_label}]asplit=2[fg_mix][fg_sc]")
        filters.append(
            f"[{combined_music}][fg_sc]sidechaincompress=threshold=0.02:ratio=4.5:attack=120:release=500[a_music_ducked]"
        )
        filters.append(
            f"[fg_mix][a_music_ducked]amix=inputs=2:duration=first:dropout_transition=2:normalize=0"
            f"{post_filter}[{output_label}]"
        )
        return filters

    filters.append(
        f"[{base_audio_label}][{combined_music}]amix=inputs=2:duration=first:dropout_transition=2:normalize=0"
        f"{post_filter}[{output_label}]"
    )
    return filters
