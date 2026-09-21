#!/usr/bin/env python3
"""Create a Social preview image from demo.gif.

Requirements:
    pip install Pillow

Output:
    code/docs/images/social_preview.png (1280x640)

Usage:
    cd code
    python tools/make_social_preview.py
    python tools/make_social_preview.py --frame 20    # 特定フレーム指定
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GIF_PATH = REPO_ROOT / "code" / "docs" / "images" / "demo.gif"
OUT_PATH = REPO_ROOT / "code" / "docs" / "images" / "social_preview.png"

TARGET_SIZE = (1280, 640)

# Text overlay
TITLE = "StaTable"
SUBTITLE = "MISRA C:2012-aware state machine code generation"


def parse_args(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, default=0,
                    help="Frame index to extract (default: 0)")
    ap.add_argument("--no-text", action="store_true",
                    help="Skip text overlay")
    return ap.parse_args(argv)


def crop_to_aspect(img: Image.Image, target: tuple[int, int]) -> Image.Image:
    """Center-crop to the target aspect ratio, then resize."""
    tw, th = target
    target_ratio = tw / th
    w, h = img.size
    current_ratio = w / h

    if current_ratio > target_ratio:
        # too wide -> crop sides
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # too tall -> crop top/bottom
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    return img.resize(target, Image.LANCZOS)


def try_load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    return ImageFont.load_default()


def main(argv):
    args = parse_args(argv)

    if not GIF_PATH.exists():
        print(f"error: {GIF_PATH} not found")
        return 1

    print(f"Opening {GIF_PATH}")
    img = Image.open(GIF_PATH)

    # Seek to the requested frame
    frame_idx = max(0, min(args.frame, img.n_frames - 1))
    img.seek(frame_idx)
    frame = img.convert("RGB")
    print(f"Frame {frame_idx}/{img.n_frames}: size={frame.size}")

    # Crop to 2:1 aspect ratio
    cropped = crop_to_aspect(frame, TARGET_SIZE)

    # Optional: darken bottom area for text readability
    if not args.no_text:
        draw = ImageDraw.Draw(cropped, "RGBA")
        # gradient-like band at bottom
        band_h = 140
        for i in range(band_h):
            alpha = int(180 * (i / band_h))
            y = TARGET_SIZE[1] - band_h + i
            draw.rectangle([(0, y), (TARGET_SIZE[0], y + 1)],
                           fill=(0, 0, 0, alpha))

        title_font = try_load_font(72)
        sub_font = try_load_font(32)

        # Title
        draw.text((48, TARGET_SIZE[1] - 110), TITLE,
                  font=title_font, fill=(255, 255, 255, 255))
        # Subtitle
        draw.text((48, TARGET_SIZE[1] - 40), SUBTITLE,
                  font=sub_font, fill=(220, 220, 220, 255))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(OUT_PATH, "PNG", optimize=True)
    print(f"Saved {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")
    print(f"Size: {cropped.size}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))