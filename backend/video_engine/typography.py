"""ASS (Advanced SubStation Alpha) animated typography & subtitle generator for FFmpeg libass."""

from __future__ import annotations

from pathlib import Path

from backend.api.schemas import SubtitleCue


def _format_ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds % 1.0) * 100))
    if centis == 100:
        secs += 1
        centis = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def _escape_ass_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def format_ass_filter_arg(ass_path: Path) -> str:
    """Escape local path for FFmpeg's `ass=filename=...` filter across Windows and POSIX."""
    posix_str = str(ass_path.resolve()).replace("\\", "/")
    escaped = posix_str.replace(":", "\\:")
    return f"ass=filename='{escaped}'"


def generate_ass_file(
    subtitles: list[SubtitleCue],
    width: int,
    height: int,
    out_path: Path,
) -> Path:
    """Write a styled ASS subtitle script with smooth animated fade transitions."""
    base_font = max(24, int(round(min(width, height) * 0.048)))
    reel_font = max(30, int(round(min(width, height) * 0.058)))
    margin_v = max(40, int(round(height * 0.075)))

    # ASS colors are &HAABBGGRR (Champagne Gold #E5B869 -> BGR 69B8E5)
    header = "\n".join(
        [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {width}",
            f"PlayResY: {height}",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding",
            (
                f"Style: cinematic_gold_bottom,Arial,{base_font},&H0069B8E5,&H00FFFFFF,&H00130D0B,&H800B0D13,"
                f"1,0,0,0,100,100,1.5,0,1,2.5,1.5,2,40,40,{margin_v},1"
            ),
            (
                f"Style: bold_center_reel,Arial,{reel_font},&H00FFFFFF,&H0069B8E5,&H000B0D13,&H900B0D13,"
                "1,0,0,0,100,100,1.0,0,3,3.0,2.0,5,36,36,40,1"
            ),
            (
                f"Style: subtle_white,Arial,{max(20, int(base_font * 0.85))},&H00F3F4F6,&H00FFFFFF,&H000B0D13,&H700B0D13,"
                f"0,0,0,0,100,100,0.5,0,1,2.0,1.0,2,40,40,{margin_v},1"
            ),
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
    )

    events: list[str] = []
    for cue in subtitles:
        start_s = _format_ass_time(cue.start_seconds)
        end_s = _format_ass_time(cue.end_seconds)
        fade_ms = 220 if cue.style == "bold_center_reel" else 350
        text = _escape_ass_text(cue.text)
        events.append(
            f"Dialogue: 0,{start_s},{end_s},{cue.style},,0,0,0,,{{\\fad({fade_ms},{fade_ms})}}{text}"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + "\n" + "\n".join(events) + "\n", encoding="utf-8")
    return out_path

