"""FFmpeg audio filter builders for tempo scaling, normalization, and music mixing."""

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
) -> list[str]:
    """Generate filtergraph stages to trim, delay, duck, and mix background music with video audio."""
    if not music_inputs:
        return [f"[{base_audio_label}]alimiter=limit=0.95[{output_label}]"]

    filters: list[str] = []
    mix_labels: list[str] = [f"[{base_audio_label}]"]

    for idx, (input_index, resolved) in enumerate(music_inputs):
        cue = resolved.cue
        max_play_dur = max(0.2, min(cue.duration_seconds, total_video_duration - cue.timeline_start_seconds))
        if max_play_dur <= 0.2:
            continue

        effective_vol = cue.duck_volume if cue.ducking_enabled else cue.volume
        # Respect explicit user volume cap while gently dipping under foreground video audio when ducking is on
        target_vol = round(min(cue.volume, effective_vol) if cue.ducking_enabled else cue.volume, 3)

        chain = [
            "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo",
            f"atrim=duration={max_play_dur:.3f}",
            "asetpts=PTS-STARTPTS",
            f"volume={target_vol}",
        ]
        if max_play_dur > 1.5:
            fade_start = round(max_play_dur - 1.0, 3)
            chain.append(f"afade=t=out:st={fade_start}:d=1.0")
        if cue.timeline_start_seconds > 0.01:
            delay_ms = int(round(cue.timeline_start_seconds * 1000))
            chain.append(f"adelay={delay_ms}|{delay_ms}")

        label = f"a_music_{idx}"
        filters.append(f"[{input_index}:a]{','.join(chain)}[{label}]")
        mix_labels.append(f"[{label}]")

    if len(mix_labels) == 1:
        filters.append(f"[{base_audio_label}]alimiter=limit=0.95[{output_label}]")
        return filters

    filters.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=2:normalize=0,"
        f"alimiter=limit=0.95[{output_label}]"
    )
    return filters

