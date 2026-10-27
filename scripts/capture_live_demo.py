"""Capture a real browser interaction sequence from the static AutoRAG lab.

Optional tools: pip install playwright; Chromium; ffmpeg.
Runs the checked-in docs/index.html + app.js + styles.css directly in a browser.
Does not download models, call remote APIs or synthesize fake evidence.
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets"


def capture() -> None:
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="./styles.css">', "")
    html = html.replace('<script src="./app.js" defer></script>', "")
    css = (DOCS / "styles.css").read_text(encoding="utf-8")
    js = (DOCS / "app.js").read_text(encoding="utf-8")
    ASSETS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="autorag-demo-") as folder:
        folder_path = Path(folder)
        sequence = 0
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1360, "height": 920}, device_scale_factor=1)
            exceptions = []
            page.on("pageerror", lambda error: exceptions.append(str(error)))
            page.set_content(html)
            page.add_style_tag(content=css)
            page.add_script_tag(content=js)

            def frame(repeat=1):
                nonlocal sequence
                image = page.screenshot(animations="allow")
                for _ in range(repeat):
                    (folder_path / f"frame_{sequence:04}.png").write_bytes(image)
                    sequence += 1

            frame(5)
            for strategy, expected in [
                ("graph", "Graph RAG"),
                ("structured", "Structured RAG"),
                ("multimodal", "Multimodal RAG"),
                ("agentic", "Agentic RAG"),
                ("hybrid", "Hybrid RAG"),
                ("no_rag", "No-RAG"),
            ]:
                page.locator(f'.example[data-scenario="{strategy}"]').click()
                frame(2)
                page.locator("#run").click()
                frame(2)
                page.wait_for_timeout(300)
                frame(2)
                page.wait_for_timeout(500)
                actual = page.locator("#selectedStrategy").inner_text()
                if actual != expected:
                    raise AssertionError(f"{strategy}: expected {expected}, got {actual}")
                frame(6)
            if exceptions:
                raise AssertionError("Browser errors: " + " | ".join(exceptions))
            page.locator('.example[data-scenario="graph"]').click()
            page.locator("#run").click()
            page.wait_for_timeout(800)
            frame(3)
            page.screenshot(path=str(ASSETS / "real-routing-preview.png"), full_page=False)
            browser.close()
        raw = str(folder_path / "frame_%04d.png")
        mp4 = ASSETS / "real-router-walkthrough.mp4"
        gif = ASSETS / "real-router-walkthrough.gif"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "5",
            "-i", raw, "-vf", "scale=1280:-2:flags=lanczos,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-movflags", "+faststart", str(mp4)
        ], check=True)
        palette = folder_path / "palette.png"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "5",
            "-i", raw, "-vf", "fps=5,scale=1000:-1:flags=lanczos,palettegen=stats_mode=diff",str(palette)
        ], check=True)
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "5",
            "-i", raw, "-i", str(palette),
            "-lavfi", "fps=5,scale=1000:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
            "-loop", "0", str(gif)
        ], check=True)
    print(f"Recorded {sequence} actual browser frames")
    print(f"Animated GIF: {gif} ({gif.stat().st_size:,} bytes)")
    print(f"MP4: {mp4} ({mp4.stat().st_size:,} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    capture()
