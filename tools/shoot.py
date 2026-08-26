#!/usr/bin/env python3
"""Screenshot the local Jekyll site at several widths x both themes.

Why the iframe wrapper: on macOS Chrome clamps a window to a ~500px minimum, so
`--window-size=390` lays the page out at 500px and then crops the capture to 390
-- which looks exactly like horizontal overflow but is pure artifact. (Verified
with a page printing its own window.innerWidth: it reported 500 for
--window-size=390.) An iframe of the target width inside a wide window gives a
genuinely narrow layout viewport with no extra dependencies.

--headless=new also sometimes never exits after writing the PNG, so each
invocation is killed after TIMEOUT; the file is already flushed by then.

Usage: python3 tools/shoot.py <outdir> [port]
"""
import os
import shutil
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGES = {"home": "", "publications": "publications/", "experience": "experience/", "news": "news/"}
WIDTHS = (390, 768, 1280)
TIMEOUT = 30
TALL = 4000

out = sys.argv[1]
port = sys.argv[2] if len(sys.argv) > 2 else "4123"
base = f"http://localhost:{port}"
os.makedirs(out, exist_ok=True)

WRAPPER = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{{margin:0;padding:0;background:#fff}}
iframe{{width:{w}px;height:{h}px;border:0;display:block}}</style></head>
<body><iframe src="{url}"></iframe></body></html>"""

for slug, path in PAGES.items():
    for w in WIDTHS:
        for mode in ("light", "dark"):
            dest = f"{out}/{slug}-{w}-{mode}.png"
            profile = tempfile.mkdtemp()
            wrapper = os.path.join(profile, "wrap.html")
            with open(wrapper, "w") as f:
                f.write(WRAPPER.format(w=w, h=TALL, url=f"{base}/{path}"))

            cmd = [
                CHROME, "--headless=new", "--disable-gpu",
                f"--user-data-dir={profile}/p",
                "--hide-scrollbars",
                "--allow-file-access-from-files",
                f"--window-size={max(w, 520)},{TALL}",
                "--virtual-time-budget=8000",
                f"--screenshot={dest}",
            ]
            if mode == "dark":
                # Fresh profile => localStorage['theme'] is null, so theme.js
                # falls through to prefers-color-scheme. WebContentsForceDark
                # must stay off or Chrome double-darkens our own CSS.
                cmd += ["--force-dark-mode", "--disable-features=WebContentsForceDark"]
            cmd.append(f"file://{wrapper}")

            try:
                subprocess.run(cmd, timeout=TIMEOUT,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                pass
            shutil.rmtree(profile, ignore_errors=True)
            size = os.path.getsize(dest) if os.path.exists(dest) else 0
            print(f"{'ok  ' if size else 'FAIL'} {slug}-{w}-{mode}  {size // 1024}KB", flush=True)
