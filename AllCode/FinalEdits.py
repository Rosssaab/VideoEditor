"""
FinalEdits - Spinning text on BBC background — config via FinalEdits_settings.json.

Outputs to AllCode/Temp/media/ (Manim default structure).

Edit FinalEdits_settings.json to set:
  - lines: any number of text lines
  - font_size, font, color, stroke_color, stroke_width
  - text_position_y, weight, duration_seconds

Render: manim -p FinalEdits.py FinalEdits  (from AllCode folder)
"""

import json
import os
from pathlib import Path

from manim import *

# Suppress pydub ffmpeg warning by using imageio-ffmpeg
try:
    import imageio_ffmpeg
    from pydub import AudioSegment
    AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass

# AllCode layout
DIR = Path(__file__).parent.resolve()
config.media_dir = str(DIR / "Temp" / "media")

# 9:16 portrait format
config.frame_width = 9
config.frame_height = 16
config.pixel_width = 1080
config.pixel_height = 1920

SETTINGS_PATH = DIR / "FinalEdits_settings.json"
BG_IMAGE = DIR / "BBC-Bg.jpg"


def load_settings():
    """Load text/layout from JSON. Fallback defaults if file missing."""
    defaults = {
        "duration_seconds": 5,
        "font_size": 72,
        "font": "Comic Sans MS",
        "color": "#FFFFFF",
        "stroke_color": "#1a1a1a",
        "stroke_width": 6,
        "weight": "BOLD",
        "text_position_y": 3,
        "lines": ["Line one", "Line two", "Line three", "Line four"],
    }
    if not SETTINGS_PATH.is_file():
        return defaults
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.pop("_comment", None)
        defaults.update(data)
    except Exception:
        pass
    return defaults


class FinalEdits(Scene):
    """Spinning text on BBC background; text and style from FinalEdits_settings.json."""

    def construct(self):
        settings = load_settings()
        duration = float(settings.get("duration_seconds", 5))
        font_size = int(settings.get("font_size", 72))
        font = settings.get("font", "Comic Sans MS")
        color = settings.get("color", "#FFFFFF")
        stroke_color = settings.get("stroke_color", "#1a1a1a")
        stroke_width = float(settings.get("stroke_width", 6))
        weight = settings.get("weight", "BOLD")
        text_position_y = float(settings.get("text_position_y", 3))
        lines = settings.get("lines", ["Line one", "Line two", "Line three", "Line four"])
        if not isinstance(lines, list):
            lines = [str(lines)]
        lines = [str(ln).strip() for ln in lines if ln]

        if BG_IMAGE.is_file():
            bg = ImageMobject(str(BG_IMAGE))
            scale_w = config.frame_width / bg.get_width()
            scale_h = config.frame_height / bg.get_height()
            bg.scale(max(scale_w, scale_h))
            bg.move_to(ORIGIN)
            bg.set_opacity(0.5)
            self.add(bg)

        text_block = Paragraph(
            *lines,
            font_size=font_size,
            color=color,
            font=font,
            weight=weight,
            line_spacing=0.5,
            alignment="center",
        )
        text_block.move_to(UP * text_position_y)
        text_block.set_stroke(color=stroke_color, width=stroke_width)

        animation_time = 4.0   # All animation finishes by 4s
        hold_time = 1.0       # Last 1s: static, text at 100%, no animation
        # Total: 5 seconds. At 4s: narrator off, text 100%. Hold 1s.

        text_block.scale(0.1)
        self.add(text_block)
        # 3 cycles + final zoom (all within 4s), then hold 1s
        t_per_half = animation_time / 7  # 6 half-cycles + 1 final zoom
        for _ in range(3):
            self.play(text_block.animate.scale(10), run_time=t_per_half, rate_func=rush_into)
            self.play(text_block.animate.scale(0.1), run_time=t_per_half, rate_func=rush_from)
        # Final zoom to 100% of base size
        self.play(text_block.animate.scale(10), run_time=t_per_half, rate_func=rush_into)
        self.wait(hold_time)
