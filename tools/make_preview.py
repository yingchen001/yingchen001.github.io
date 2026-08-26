#!/usr/bin/env python3
"""Convert one image to a WebP publication preview, matching the sizing used by
tools/compress_images.py (800px longest edge, q78).

Usage: python3 tools/make_preview.py <src> <name-without-extension>
"""
import os
import sys

from PIL import Image

src, name = sys.argv[1], sys.argv[2]
dest = f"assets/img/publication_preview/{name}.webp"

im = Image.open(src)
has_alpha = im.mode in ("RGBA", "LA") or (
    im.mode == "P" and "transparency" in im.info)
# Flatten onto white: these previews render on the page background, and keeping
# alpha would leave the figure's text sitting on a transparent hole in dark mode.
if has_alpha:
    im = im.convert("RGBA")
    bg = Image.new("RGB", im.size, "white")
    bg.paste(im, mask=im.split()[-1])
    im = bg
else:
    im = im.convert("RGB")

im.thumbnail((800, 800), Image.LANCZOS)
im.save(dest, "WEBP", quality=78, method=6)
print(f"{dest}  {im.size[0]}x{im.size[1]}  {os.path.getsize(dest) // 1024}KB")
