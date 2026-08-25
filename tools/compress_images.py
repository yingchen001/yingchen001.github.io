#!/usr/bin/env python3
"""Compress assets/img/ for the ~200px display size the thumbnails render at.

Writes to an output directory and never touches the originals -- inspect the
result and check the byte budget before copying anything into assets/. Animated
GIFs become animated WebP (Pillow handles this; there is no cwebp or
ImageMagick on this machine, and sips cannot write WebP at all).

Usage: python3 tools/compress_images.py <outdir>
"""
import os
import struct
import sys

from PIL import Image

SRC = "assets/img/publication_preview"
PROFILE = "assets/img/prof_pic.jpg"

STATIC_MAX = 800     # longest edge; thumbnails display at ~200 CSS px
STATIC_Q = 78
ANIM_W = 400
ANIM_Q = 58
ANIM_FRAME_STEP = 2  # keep every Nth frame, doubling duration to hold timing

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
os.makedirs(f"{out}/publication_preview", exist_ok=True)

tot_in = tot_out = 0
rows = []


def webp_frame_durations(path):
    """Frame durations (ms) read straight from the WebP ANMF chunks.

    Pillow's WebP reader does not surface per-frame durations, so this walks the
    RIFF container instead. Each ANMF payload puts a 24-bit little-endian
    duration at offset 12.
    """
    data = open(path, "rb").read()
    off, out = 12, []
    while off + 8 <= len(data):
        tag = data[off:off + 4]
        size = struct.unpack("<I", data[off + 4:off + 8])[0]
        if tag == b"ANMF":
            out.append(struct.unpack("<I", data[off + 20:off + 23] + b"\0")[0])
        off += 8 + size + (size & 1)
    return out


def save_static(src, dest, longest, quality):
    im = Image.open(src)
    has_alpha = im.mode in ("RGBA", "LA") or (
        im.mode == "P" and "transparency" in im.info)
    im = im.convert("RGBA" if has_alpha else "RGB")
    im.thumbnail((longest, longest), Image.LANCZOS)
    im.save(dest, "WEBP", quality=quality, method=6)


def save_animated(src, dest):
    im = Image.open(src)
    # Read every source duration up front: seeking again later (as the frame
    # loop does) can leave im.info pointing at the wrong frame, which silently
    # produced 0ms durations and animations that played at full speed.
    src_durations = []
    for i in range(im.n_frames):
        im.seek(i)
        src_durations.append(im.info.get("duration") or 80)

    frames, durations = [], []
    for i in range(im.n_frames):
        if i % ANIM_FRAME_STEP:
            continue
        im.seek(i)
        f = im.convert("RGBA")
        scale = ANIM_W / f.width
        if scale < 1:
            f = f.resize((ANIM_W, max(1, round(f.height * scale))), Image.LANCZOS)
        frames.append(f)
        # Absorb the dropped frames' time so the loop keeps its wall-clock length.
        durations.append(sum(src_durations[i:i + ANIM_FRAME_STEP]))

    frames[0].save(dest, "WEBP", save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, quality=ANIM_Q, method=4)

    # Verify the timing survived rather than trusting it. Pillow writes WebP
    # frame durations but does NOT report them back on read -- im.info["duration"]
    # is 0 even for a clean round-trip -- so read the ANMF chunks directly.
    total = sum(webp_frame_durations(dest))
    if total == 0:
        raise RuntimeError(f"{dest}: frame durations lost, animation would "
                           f"play at full speed")
    return im.n_frames, len(frames), sum(src_durations), total


for name in sorted(os.listdir(SRC)):
    src = os.path.join(SRC, name)
    if not os.path.isfile(src):
        continue
    size_in = os.path.getsize(src)
    stem = os.path.splitext(name)[0]
    dest = f"{out}/publication_preview/{stem}.webp"

    im = Image.open(src)
    animated = getattr(im, "n_frames", 1) > 1
    im.close()

    if animated:
        n_all, n_kept, ms_in, ms_out = save_animated(src, dest)
        note = f"anim {n_kept}/{n_all}f {ms_in}->{ms_out}ms"
    else:
        save_static(src, dest, STATIC_MAX, STATIC_Q)
        note = ""

    size_out = os.path.getsize(dest)
    tot_in += size_in
    tot_out += size_out
    rows.append((name, size_in, size_out, note))

# The profile photo is 413x531 and displays at ~260px; keep it a touch larger.
save_static(PROFILE, f"{out}/prof_pic.webp", 900, 86)
p_in, p_out = os.path.getsize(PROFILE), os.path.getsize(f"{out}/prof_pic.webp")
tot_in += p_in
tot_out += p_out
rows.append(("prof_pic.jpg", p_in, p_out, ""))

rows.sort(key=lambda r: -r[1])
for name, a, b, note in rows:
    print(f"  {name:26s} {a/1e6:6.2f}MB -> {b/1e6:5.2f}MB  "
          f"({100*b/a:4.1f}%) {note}")
print(f"\nTOTAL {tot_in/1e6:.2f}MB -> {tot_out/1e6:.2f}MB "
      f"({100*tot_out/tot_in:.1f}%)")
