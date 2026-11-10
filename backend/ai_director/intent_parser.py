"""Natural-language creative instruction parser for the CINEFLOW AI Director."""

from __future__ import annotations

import re
from typing import Optional

from backend.api.schemas import AspectRatio, ColorGradePreset, DirectorIntent, PacingStyle

_WORD_NUMBERS = {
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "half": 0.5,
    "ten": 10.0,
    "fifteen": 15.0,
    "twenty": 20.0,
    "thirty": 30.0,
    "forty": 40.0,
    "forty-five": 45.0,
    "sixty": 60.0,
    "ninety": 90.0,
}

_THEME_LEXICON = [
    "deepavali",
    "diwali",
    "diya",
    "fireworks",
    "rangoli",
    "sunset",
    "sunrise",
    "travel",
    "fest",
    "festival",
    "campus",
    "bmsit",
    "college",
    "wedding",
    "documentary",
    "lifestyle",
    "celebration",
    "crowd",
    "people",
    "portrait",
    "drone",
    "landscape",
    "emotional",
    "night",
]


def _extract_duration_seconds(text: str) -> float:
    lower = text.lower()
    # Numeric durations like "2 min", "2-minute", "90 seconds", "45s"
    min_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:-|\s)?(?:minutes?|mins?)\b", lower)
    if min_match:
        return round(min(3600.0, max(5.0, float(min_match.group(1)) * 60.0)), 1)

    sec_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:-|\s)?(?:seconds?|secs?|s)\b", lower)
    if sec_match:
        return round(min(3600.0, max(5.0, float(sec_match.group(1)))), 1)

    # Word durations like "two-minute", "three minutes", "thirty seconds"
    for word, val in _WORD_NUMBERS.items():
        if re.search(rf"\b{re.escape(word)}[\s-]+(?:minutes?|mins?)\b", lower):
            return round(min(3600.0, max(5.0, val * 60.0)), 1)
        if re.search(rf"\b{re.escape(word)}[\s-]+(?:seconds?|secs?)\b", lower):
            return round(min(3600.0, max(5.0, val)), 1)

    if any(k in lower for k in ("reel", "short", "shorts", "tiktok")):
        return 30.0
    if any(k in lower for k in ("documentary", "wedding", "aftermovie")):
        return 120.0
    return 60.0


def _detect_aspect_ratio(text: str) -> AspectRatio:
    lower = text.lower()
    if "9:16" in lower or any(k in lower for k in ("reel", "reels", "shorts", "vertical", "portrait video")):
        return "9:16"
    if "1:1" in lower or "square" in lower:
        return "1:1"
    if "4:5" in lower:
        return "4:5"
    if "21:9" in lower or "anamorphic" in lower or "widescreen" in lower:
        return "21:9"
    return "16:9"


def _detect_color_grade(text: str) -> ColorGradePreset:
    lower = text.lower()
    if any(k in lower for k in ("black and white", "monochrome", "noir", "b&w")):
        return "high_contrast_bw"
    if any(k in lower for k in ("deepavali", "diwali", "diya", "golden", "warm", "sunset", "festive")):
        return "golden_hour"
    if any(k in lower for k in ("vintage", "retro", "wedding", "nostalgic", "film grain")):
        return "vintage_film"
    if any(k in lower for k in ("moody", "dark", "documentary", "dramatic night")):
        return "moody_dark"
    if any(k in lower for k in ("travel", "teal", "cinema", "cinematic", "blockbuster")):
        return "cinematic_teal_orange"
    return "natural"


def _detect_title(text: str, themes: list[str]) -> str:
    lower = text.lower()
    if "deepavali" in lower or "diwali" in lower:
        return "Deepavali Cinematic Story"
    if "travel" in lower:
        return "Cinematic Travel Film"
    if "wedding" in lower:
        return "Wedding Highlight Film"
    if "fest" in lower or "bmsit" in lower or "college" in lower:
        return "Campus Festival Aftermovie"
    if "reel" in lower or "shorts" in lower:
        return "Dynamic Highlight Reel"
    if themes:
        return f"{themes[0].capitalize()} Cinematic Cut"
    return "CINEFLOW AI Production"


def parse_director_instruction(
    instruction: str,
    *,
    duration_override: Optional[float] = None,
    aspect_override: Optional[AspectRatio] = None,
) -> DirectorIntent:
    """Parse natural creative directions into structured `DirectorIntent` constraints."""
    lower = instruction.lower()
    themes = [kw for kw in _THEME_LEXICON if re.search(rf"\b{re.escape(kw)}\b", lower)]

    target_dur = duration_override if duration_override is not None else _extract_duration_seconds(instruction)
    aspect_ratio = aspect_override if aspect_override is not None else _detect_aspect_ratio(instruction)
    color_grade = _detect_color_grade(instruction)

    # Intro style
    intro_style: str = "standard"
    if any(w in lower for w in ("slow", "dramatic", "gentle", "calm")) and any(
        w in lower for w in ("intro", "introduction", "opening", "start", "beginning")
    ):
        intro_style = "slow_dramatic"
    elif any(w in lower for w in ("punchy", "fast hook", "energetic start", "grab")):
        intro_style = "punchy_hook"

    # Climax keywords (e.g., "fast transitions during the fireworks")
    climax_keywords: list[str] = []
    for kw in ("fireworks", "action", "celebration", "crowd", "dance", "highlight", "drop"):
        if kw in lower:
            climax_keywords.append(kw)

    # Outro style
    outro_style: str = "standard"
    if any(w in lower for w in ("emotional", "touching", "slow", "heartfelt")) and any(
        w in lower for w in ("end", "ending", "outro", "finale", "closing")
    ):
        outro_style = "emotional"
    elif "emotional" in lower:
        outro_style = "emotional"

    # Overall pacing curve
    has_fast = any(w in lower for w in ("fast", "quick", "energetic", "punchy", "hype", "montage"))
    has_slow = any(w in lower for w in ("slow", "dramatic", "emotional", "calm", "peaceful"))

    pacing: PacingStyle = "dynamic_arc"
    if has_fast and not (intro_style == "slow_dramatic" or outro_style == "emotional"):
        pacing = "fast"
    elif has_slow and not has_fast and not climax_keywords:
        pacing = "slow"

    mood = "festive" if any(k in themes for k in ("deepavali", "diwali", "festival", "celebration")) else (
        "emotional" if outro_style == "emotional" else (
            "energetic" if pacing == "fast" else "cinematic"
        )
    )

    return DirectorIntent(
        mood=mood,
        theme_keywords=themes,
        target_duration_seconds=target_dur,
        aspect_ratio=aspect_ratio,
        color_grade=color_grade,
        pacing=pacing,
        intro_style=intro_style,  # type: ignore[arg-type]
        climax_keywords=climax_keywords,
        outro_style=outro_style,  # type: ignore[arg-type]
        title_suggestion=_detect_title(instruction, themes),
    )

