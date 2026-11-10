"""Safe FFmpeg and FFprobe discovery and subprocess execution wrappers."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

from backend.api.config import get_settings


class FFmpegNotFoundError(RuntimeError):
    """Raised when ffmpeg or ffprobe executable cannot be located."""


class FFmpegExecutionError(RuntimeError):
    """Raised when an ffmpeg or ffprobe subprocess returns non-zero status."""

    def __init__(self, message: str, returncode: int, stderr: str = "") -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


def _candidate_windows_dirs() -> list[Path]:
    """Return common package-manager directories on Windows where FFmpeg is placed."""
    dirs: list[Path] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        winget_root = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_root.exists():
            dirs.extend(winget_root.glob("Gyan.FFmpeg*"))
            dirs.extend(winget_root.glob("**/bin"))
        winget_links = Path(local_app_data) / "Microsoft" / "WinGet" / "Links"
        if winget_links.exists():
            dirs.append(winget_links)

    for static_dir in (
        Path("C:/ProgramData/chocolatey/bin"),
        Path("C:/ffmpeg/bin"),
        get_settings().BASE_DIR / "scripts" / "bin",
    ):
        if static_dir.exists():
            dirs.append(static_dir)
    return dirs


@lru_cache(maxsize=4)
def resolve_binary(binary_name: str) -> str:
    """Resolve an executable (`ffmpeg` or `ffprobe`) strictly without shell lookup."""
    settings = get_settings()
    override = settings.FFMPEG_PATH if binary_name == "ffmpeg" else settings.FFPROBE_PATH
    if override and Path(override).is_file():
        return str(Path(override).resolve())

    found = shutil.which(binary_name)
    if found:
        return str(Path(found).resolve())

    exe_name = f"{binary_name}.exe" if os.name == "nt" else binary_name
    for directory in _candidate_windows_dirs():
        direct = directory / exe_name
        if direct.is_file():
            return str(direct.resolve())
        nested = next(directory.glob(f"**/{exe_name}"), None)
        if nested and nested.is_file():
            return str(nested.resolve())

    raise FFmpegNotFoundError(
        f"Executable '{binary_name}' was not found in PATH or standard installation paths. "
        "Install FFmpeg (e.g. `winget install Gyan.FFmpeg`) or set FFMPEG_PATH / FFPROBE_PATH in .env."
    )


def clear_binary_cache() -> None:
    """Clear cached binary paths (useful after installing FFmpeg or in tests)."""
    resolve_binary.cache_clear()


def run_ffmpeg_sync(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    """Execute ffmpeg with explicit argument array (`shell=False`)."""
    ffmpeg_bin = resolve_binary("ffmpeg")
    cmd = [ffmpeg_bin, *args]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )
    if proc.returncode != 0:
        raise FFmpegExecutionError(
            f"FFmpeg command failed with code {proc.returncode}",
            returncode=proc.returncode,
            stderr=proc.stderr,
        )
    return proc


def run_ffprobe_sync(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Execute ffprobe with explicit argument array (`shell=False`)."""
    ffprobe_bin = resolve_binary("ffprobe")
    cmd = [ffprobe_bin, *args]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )
    if proc.returncode != 0:
        raise FFmpegExecutionError(
            f"FFprobe command failed with code {proc.returncode}",
            returncode=proc.returncode,
            stderr=proc.stderr,
        )
    return proc


async def run_ffmpeg_with_progress(
    args: list[str],
    total_duration_seconds: float,
    on_progress: Optional[Callable[[float, str], None]] = None,
    process_holder: Optional[dict] = None,
) -> None:
    """Run ffmpeg asynchronously while streaming progress percentage from `-progress pipe:1`."""
    ffmpeg_bin = resolve_binary("ffmpeg")
    cmd = [ffmpeg_bin, "-progress", "pipe:1", "-nostats", *args]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    if process_holder is not None:
        process_holder["process"] = proc

    stderr_chunks: list[bytes] = []

    async def _drain_stderr() -> None:
        assert proc.stderr is not None
        while True:
            chunk = await proc.stderr.read(4096)
            if not chunk:
                break
            stderr_chunks.append(chunk)

    stderr_task = asyncio.create_task(_drain_stderr())

    try:
        assert proc.stdout is not None
        while True:
            raw_line = await proc.stdout.readline()
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace").strip()
            if line.startswith("out_time_us=") and total_duration_seconds > 0 and on_progress:
                val = line.split("=", 1)[1].strip()
                if val.isdigit():
                    elapsed_sec = int(val) / 1_000_000.0
                    pct = min(99.0, max(0.0, (elapsed_sec / total_duration_seconds) * 100.0))
                    on_progress(pct, f"Encoding video ({elapsed_sec:.1f}s / {total_duration_seconds:.1f}s)")
    finally:
        await stderr_task
        returncode = await proc.wait()

    stderr_text = b"".join(stderr_chunks).decode("utf-8", errors="replace")
    if returncode != 0:
        raise FFmpegExecutionError(
            f"FFmpeg render failed with code {returncode}",
            returncode=returncode,
            stderr=stderr_text,
        )


def get_binary_info() -> dict[str, Optional[str]]:
    """Return discovered FFmpeg & FFprobe paths and version lines."""
    info: dict[str, Optional[str]] = {
        "ffmpeg_path": None,
        "ffprobe_path": None,
        "ffmpeg_version": None,
        "ffprobe_version": None,
    }
    try:
        ffmpeg_bin = resolve_binary("ffmpeg")
        info["ffmpeg_path"] = ffmpeg_bin
        res = subprocess.run([ffmpeg_bin, "-version"], capture_output=True, text=True, timeout=10, shell=False)
        if res.returncode == 0 and res.stdout:
            info["ffmpeg_version"] = res.stdout.splitlines()[0].strip()
    except Exception:
        pass

    try:
        ffprobe_bin = resolve_binary("ffprobe")
        info["ffprobe_path"] = ffprobe_bin
        res = subprocess.run([ffprobe_bin, "-version"], capture_output=True, text=True, timeout=10, shell=False)
        if res.returncode == 0 and res.stdout:
            info["ffprobe_version"] = res.stdout.splitlines()[0].strip()
    except Exception:
        pass

    return info

