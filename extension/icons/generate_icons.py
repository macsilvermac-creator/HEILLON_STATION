#!/usr/bin/env python3
"""Generate Heillon Legal extension icons (16/48/128 PNG).

Design:
- Background: deep-space navy `#0A0E1A`
- Foreground: stylized "H" with gold chain motif `#D4AF37`
- Subtle gold border for premium feel
- All icons rendered at 4x supersampling then downsampled for crisp edges

Usage:
    pip install Pillow
    python generate_icons.py

Output:
    icon-16.png, icon-48.png, icon-128.png in the current directory
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BG = (10, 14, 26, 255)            # deep-space-900
GOLD = (212, 175, 55, 255)        # gold-500
GOLD_DIM = (212, 175, 55, 180)
TEXT_WHITE = (244, 244, 245, 255)

SUPERSAMPLE = 4
SIZES = [16, 48, 128]


def draw_h_glyph(size: int) -> Image.Image:
    """Render Heillon glyph at given size with 4x supersampling."""
    target = size * SUPERSAMPLE
    img = Image.new("RGBA", (target, target), BG)
    draw = ImageDraw.Draw(img)

    # Outer subtle gold border (1px at target size)
    border = max(SUPERSAMPLE, target // 32)
    draw.rectangle([(0, 0), (target - 1, target - 1)], outline=GOLD_DIM, width=border)

    # Stylized "H" — two vertical bars + horizontal bar with subtle chain notch
    margin = target // 5
    bar_w = max(SUPERSAMPLE * 2, target // 8)
    left_x = margin
    right_x = target - margin - bar_w
    bar_top = margin
    bar_bottom = target - margin

    # Left vertical bar
    draw.rectangle([(left_x, bar_top), (left_x + bar_w, bar_bottom)], fill=GOLD)
    # Right vertical bar
    draw.rectangle([(right_x, bar_top), (right_x + bar_w, bar_bottom)], fill=GOLD)
    # Horizontal cross-bar
    cross_top = target // 2 - bar_w // 2
    cross_bottom = target // 2 + bar_w // 2
    draw.rectangle([(left_x, cross_top), (right_x + bar_w, cross_bottom)], fill=GOLD)

    # Chain-of-custody dot accent in the center (subtle)
    dot_r = max(SUPERSAMPLE, target // 24)
    cx, cy = target // 2, target // 2
    draw.ellipse(
        [(cx - dot_r, cy - dot_r), (cx + dot_r, cy + dot_r)],
        fill=BG,
    )

    # Downsample to final size with LANCZOS for crisp edges
    final = img.resize((size, size), Image.LANCZOS)
    return final


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    for size in SIZES:
        path = out_dir / f"icon-{size}.png"
        img = draw_h_glyph(size)
        img.save(path, format="PNG", optimize=True)
        print(f"  -> {path.name} ({size}x{size}, {path.stat().st_size if path.exists() else 0} bytes)")
    print(f"\nGenerated {len(SIZES)} icons in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
