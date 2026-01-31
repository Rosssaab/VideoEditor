"""
FINAL COMPOSITE: Man with transparent bg on BBC globe with spinning text.

Uses AllCode folder layout:
  - NaratorMp4/  : green screen video of you (put your .mp4 here)
  - SoundFile/   : audio track (put .m4a here)
  - Temp/        : Manim background video (background_globe.mp4), intermediate output
  - FinishedMp4/ : final video with audio

Animation:
  - Man starts at original size, shrinks and moves to bottom right over 2 seconds
"""

import cv2
import numpy as np
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
NARATOR_DIR = SCRIPT_DIR / "NaratorMp4"
SOUND_DIR = SCRIPT_DIR / "SoundFile"
TEMP_DIR = SCRIPT_DIR / "Temp"
FINISHED_DIR = SCRIPT_DIR / "FinishedMp4"

# Manim outputs to Temp/media/videos/FinalEdits/1920p60/FinalEdits.mp4
BACKGROUND_GLOBE = TEMP_DIR / "media" / "videos" / "FinalEdits" / "1920p60" / "FinalEdits.mp4"

OUTPUT_VIDEO_ONLY = TEMP_DIR / "final_output.mp4"
OUTPUT_WITH_AUDIO = FINISHED_DIR / "final_output_with_audio.mp4"

# Green screen removal
GREEN_LOWER_H = 40
GREEN_UPPER_H = 80
GREEN_MIN_SAT = 80
GREEN_MIN_VAL = 80

ANIMATION_DURATION = 2.0
START_SCALE = 1.0
END_SCALE = 0.68   # 50% larger than 0.45
MARGIN = 40

TARGET_DURATION = 5.0       # Total video length (seconds)
NARRATOR_VISIBLE = 4.0      # Narrator shown for first 4s, removed for last 1s

# Manim text timeline: 3 cycles (10%-100%-10%) + final zoom to 150%, then hold
ANIMATION_TIME = 4.0
T_PER_HALF = ANIMATION_TIME / 7


def _text_scale_pct(t: float) -> float:
    """Estimate text scale % from time (matches FinalEdits.py)."""
    if t >= 4.0:
        return 100.0
    seg_idx = int(t / T_PER_HALF)
    frac = (t / T_PER_HALF) - seg_idx
    if seg_idx % 2 == 0:
        return 10 + 90 * min(frac, 1.0)
    return 100 - 90 * min(frac, 1.0)


def _first_file(folder: Path, *extensions: str) -> Path | None:
    """Find first file in folder with given extension(s)."""
    if not folder.is_dir():
        return None
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() in {e.lower() for e in extensions}:
            return f
    return None


def remove_green_screen(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(
        hsv,
        np.array([GREEN_LOWER_H, GREEN_MIN_SAT, GREEN_MIN_VAL]),
        np.array([GREEN_UPPER_H, 255, 255]),
    )
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    black_mask = cv2.inRange(gray, 0, 10)
    remove_mask = cv2.bitwise_or(green_mask, black_mask)
    keep_mask = cv2.bitwise_not(remove_mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    keep_mask = cv2.morphologyEx(keep_mask, cv2.MORPH_CLOSE, kernel)
    keep_mask = cv2.erode(keep_mask, kernel, iterations=1)
    keep_mask = cv2.GaussianBlur(keep_mask, (5, 5), 0)
    return keep_mask


def ease_in_out(t):
    return t * t * (3.0 - 2.0 * t)


def composite_frame(fg_frame, fg_mask, bg_frame, scale, position_ratio):
    bg_h, bg_w = bg_frame.shape[:2]
    fg_h, fg_w = fg_frame.shape[:2]
    result = bg_frame.copy()

    new_w = int(fg_w * scale)
    new_h = int(fg_h * scale)
    if new_w <= 0 or new_h <= 0:
        return result

    fg_scaled = cv2.resize(fg_frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    mask_scaled = cv2.resize(fg_mask, (new_w, new_h), interpolation=cv2.INTER_AREA)

    start_x = (bg_w - new_w) // 2
    start_y = (bg_h - new_h) // 2
    end_x = bg_w - new_w - MARGIN
    end_y = bg_h - new_h - MARGIN

    x = int(start_x + (end_x - start_x) * position_ratio)
    y = int(start_y + (end_y - start_y) * position_ratio)

    src_x1 = max(0, -x)
    src_y1 = max(0, -y)
    src_x2 = min(new_w, bg_w - x)
    src_y2 = min(new_h, bg_h - y)

    dst_x1 = max(0, x)
    dst_y1 = max(0, y)
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)

    if src_x2 <= src_x1 or src_y2 <= src_y1:
        return result

    fg_region = fg_scaled[src_y1:src_y2, src_x1:src_x2]
    mask_region = mask_scaled[src_y1:src_y2, src_x1:src_x2]
    bg_region = result[dst_y1:dst_y2, dst_x1:dst_x2]

    alpha = mask_region.astype(float) / 255.0
    alpha_3ch = np.stack([alpha, alpha, alpha], axis=2)
    blended = fg_region.astype(float) * alpha_3ch + bg_region.astype(float) * (1 - alpha_3ch)
    result[dst_y1:dst_y2, dst_x1:dst_x2] = blended.astype(np.uint8)
    return result


def create_final_video():
    foreground = _first_file(NARATOR_DIR, ".mp4")
    audio = _first_file(SOUND_DIR, ".m4a", ".mp3", ".wav")
    background = BACKGROUND_GLOBE

    if not foreground:
        raise FileNotFoundError(f"Put your green screen video in: {NARATOR_DIR}")
    if not background.exists():
        raise FileNotFoundError(
            f"Background not found: {background}\n"
            "Run 'manim -p FinalEdits.py FinalEdits' first (or run_all.py)"
        )

    print("Loading videos...")
    print(f"  Foreground: {foreground}")
    print(f"  Background: {background}")

    fg_cap = cv2.VideoCapture(str(foreground))
    bg_cap = cv2.VideoCapture(str(background))

    if not fg_cap.isOpened():
        raise FileNotFoundError(f"Cannot open: {foreground}")
    if not bg_cap.isOpened():
        raise FileNotFoundError(f"Cannot open: {background}")

    fps = int(fg_cap.get(cv2.CAP_PROP_FPS)) or 30
    bg_fps = bg_cap.get(cv2.CAP_PROP_FPS) or 60
    bg_frames_total = int(bg_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    bg_w = int(bg_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    bg_h = int(bg_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    total_frames = int(TARGET_DURATION * fps)
    narrator_frames = int(NARRATOR_VISIBLE * fps)
    animation_frames = int(ANIMATION_DURATION * fps)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(OUTPUT_VIDEO_ONLY), fourcc, fps, (bg_w, bg_h))

    print(f"Processing... (total {TARGET_DURATION}s, narrator first {NARRATOR_VISIBLE}s, text-only last 1s)")
    print(f"  Output: {fps} fps, {total_frames} frames | Background: {bg_fps:.0f} fps, {bg_frames_total} frames")
    print(f"{'Time(s)':<8} {'Narrator %':<14} {'Text %':<10}")
    print("-" * 42)
    last_printed_half = -1
    for frame_count in range(total_frames):
        t_sec = frame_count / fps
        # Seek to correct bg frame (bg may be 60fps, output 30fps - must align by time)
        bg_frame_idx = int(t_sec * bg_fps)
        if bg_frame_idx >= bg_frames_total:
            bg_frame_idx = bg_frames_total - 1
        bg_cap.set(cv2.CAP_PROP_POS_FRAMES, bg_frame_idx)
        ret_bg, bg_frame = bg_cap.read()
        if not ret_bg:
            bg_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret_bg, bg_frame = bg_cap.read()

        show_narrator = frame_count < narrator_frames
        if show_narrator:
            ret_fg, fg_frame = fg_cap.read()
            if not ret_fg:
                fg_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret_fg, fg_frame = fg_cap.read()
            mask = remove_green_screen(fg_frame)
            if frame_count < animation_frames:
                progress = ease_in_out(frame_count / animation_frames)
                scale = START_SCALE + (END_SCALE - START_SCALE) * progress
                position = progress
            else:
                scale = END_SCALE
                position = 1.0
            narrator_pct = round(scale * 100, 1)
            result = composite_frame(fg_frame, mask, bg_frame, scale, position)
        else:
            narrator_pct = 0.0
            result = bg_frame

        text_pct = round(_text_scale_pct(t_sec), 1)
        narrator_str = f"{narrator_pct}%" if show_narrator else "hidden"
        half_sec = int(t_sec * 2)
        if half_sec > last_printed_half:
            print(f"{t_sec:<8.2f} {narrator_str:<14} {text_pct}%")
            last_printed_half = half_sec

        out.write(result)
        if (frame_count + 1) % 30 == 0:
            print(f"  frames {frame_count + 1}/{total_frames}")

    print("-" * 42)

    fg_cap.release()
    bg_cap.release()
    out.release()

    print(f"\n✓ Video: {OUTPUT_VIDEO_ONLY}")
    add_audio_to_video(audio)


def add_audio_to_video(audio_path: Path | None):
    FINISHED_DIR.mkdir(parents=True, exist_ok=True)

    if not audio_path or not audio_path.exists():
        print(f"⚠ No audio in {SOUND_DIR}, skipping audio merge")
        return

    print(f"Adding audio: {audio_path}")
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = "ffmpeg"

    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(OUTPUT_VIDEO_ONLY),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-t", str(TARGET_DURATION),
        str(OUTPUT_WITH_AUDIO),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ Final: {OUTPUT_WITH_AUDIO}")
    else:
        print("⚠ Audio merge failed:", result.stderr[:300] if result.stderr else "?")


if __name__ == "__main__":
    create_final_video()
