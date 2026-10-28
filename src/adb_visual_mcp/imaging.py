from __future__ import annotations

import base64
import io
import math
import os

from PIL import Image, ImageDraw, ImageFont


def _font(size: int = 16):
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def overlay_grid(png: bytes, rows: int = 0, cols: int = 0) -> tuple[bytes, int, int]:
    if not 0 <= rows <= 200 or not 0 <= cols <= 200:
        raise ValueError("grid_rows/grid_cols must be between 0 and 200")
    im = Image.open(io.BytesIO(png)).convert("RGB")
    w, h = im.size
    if rows or cols:
        draw = ImageDraw.Draw(im, "RGBA")
        font = _font(15)
        line = (255, 35, 35, 220)
        fg = (255, 255, 255, 255)
        bg = (0, 0, 0, 190)
        if cols:
            for i in range(1, cols):
                x = round(i * w / cols)
                draw.line((x, 0, x, h), fill=line, width=2)
            cellw = w / cols
            stride = max(1, math.ceil(52 / max(1, cellw)))
            for i in range(0, cols, stride):
                s = f"C{i}"
                box = draw.textbbox((0, 0), s, font=font)
                tw, th = box[2] - box[0], box[3] - box[1]
                cx = (i + 0.5) * cellw
                x0 = int(cx - tw / 2 - 3)
                draw.rectangle((x0, 2, x0 + tw + 6, th + 8), fill=bg)
                draw.text((x0 + 3, 4), s, font=font, fill=fg)
        if rows:
            for i in range(1, rows):
                y = round(i * h / rows)
                draw.line((0, y, w, y), fill=line, width=2)
            cellh = h / rows
            stride = max(1, math.ceil(34 / max(1, cellh)))
            for i in range(0, rows, stride):
                s = f"R{i}"
                box = draw.textbbox((0, 0), s, font=font)
                tw, th = box[2] - box[0], box[3] - box[1]
                cy = (i + 0.5) * cellh
                y0 = int(cy - th / 2 - 3)
                draw.rectangle((2, y0, tw + 8, y0 + th + 6), fill=bg)
                draw.text((5, y0 + 2), s, font=font, fill=fg)
    out = io.BytesIO()
    im.save(out, format="PNG", optimize=True)
    return out.getvalue(), w, h


def png_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
