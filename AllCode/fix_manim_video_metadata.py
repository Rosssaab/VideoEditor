"""
Fix metadata on Manim output (9:16) so players open at correct portrait size.
Sets rotate=0 and aspect 9:16 via ffmpeg (no re-encode).
"""

import subprocess
import sys
from pathlib import Path

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"

DIR = Path(__file__).parent
DEFAULT_INPUT = DIR / "Temp" / "media" / "videos" / "FinalEdits" / "1920p60" / "FinalEdits.mp4"


def fix_metadata(input_path: Path, output_path: Path | None = None) -> Path:
    if output_path is None:
        temp_path = input_path.parent / f"_temp_meta{input_path.suffix}"
        output_path = temp_path
    cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(input_path),
        "-metadata:s:v:0", "rotate=0",
        "-aspect", "9:16",
        "-c", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[:300]}")
    if output_path != input_path and output_path.name.startswith("_temp_"):
        output_path.replace(input_path)
        return input_path
    return output_path


def main():
    path = Path(sys.argv[1]) if len(sys.argv) >= 2 else DEFAULT_INPUT
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    fix_metadata(path)
    print(f"Metadata fixed: {path}")


if __name__ == "__main__":
    main()
