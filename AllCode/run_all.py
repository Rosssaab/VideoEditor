"""
Run full pipeline: Manim background -> composite with narrator -> add audio.

Requires:
  - NaratorMp4/ : green screen video (.mp4)
  - SoundFile/  : audio (.m4a, .mp3, or .wav)

Outputs:
  - FinishedMp4/final_output_with_audio.mp4

Usage: python run_all.py
"""

import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).parent


def run_cmd(cmd: list[str], cwd: Path | None = None) -> bool:
    result = subprocess.run(cmd, cwd=cwd or DIR)
    return result.returncode == 0


def main():
    print("=== 1. Render Manim background (FinalEdits) ===")
    # -qh = high quality, no -p = don't open player when Manim finishes
    if not run_cmd([sys.executable, "-m", "manim", "-qh", "--disable_caching", "FinalEdits.py", "FinalEdits"]):
        print("Manim failed. Aborting.")
        sys.exit(1)

    # Fix metadata so players display portrait correctly
    manim_out = DIR / "Temp" / "media" / "videos" / "FinalEdits" / "1920p60" / "FinalEdits.mp4"
    if manim_out.exists():
        try:
            from fix_manim_video_metadata import fix_metadata
            fix_metadata(manim_out)
            print("Metadata fixed.")
        except Exception as e:
            print(f"Metadata fix warning: {e}")

    print("\n=== 2. Composite narrator + background + audio ===")
    if not run_cmd([sys.executable, "create_final_video.py"]):
        print("Composite failed. Aborting.")
        sys.exit(1)

    final_video = DIR / "FinishedMp4" / "final_output_with_audio.mp4"
    print(f"\n✓ Done. Output: {final_video}")
    if final_video.exists():
        import os
        os.startfile(str(final_video))


if __name__ == "__main__":
    main()
