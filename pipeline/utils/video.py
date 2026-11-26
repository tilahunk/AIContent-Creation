import glob
import shutil
from pathlib import Path


def find_ffmpeg() -> str:
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    candidates = glob.glob(str(Path.home() / "AppData/Local/Microsoft/WinGet/Packages/*FFmpeg*/**/ffmpeg.exe"), recursive=True)
    if candidates:
        return candidates[0]
    raise RuntimeError("FFmpeg executable is unavailable")
