"""Render the MCP explainer animation to MP4, frame by frame.

The page exposes its GSAP timeline in `?record=1` mode; each frame is seeked
exactly and screenshotted, so the video is smooth regardless of machine speed.

Usage (from repo root):
    uv run --with playwright python scripts/render_mcp_explainer.py \
        [--out web/animations/mcp-agentic-architecture.mp4] [--fps 30] \
        [--chromium /usr/bin/chromium]

Requires ffmpeg on PATH and a Chromium (Playwright's bundled one or system).
"""
import argparse
import asyncio
import pathlib
import subprocess

from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "web" / "animations" / "mcp-agentic-architecture.html"


async def render(out: pathlib.Path, fps: int, chromium: str | None, width: int, height: int) -> None:
    async with async_playwright() as p:
        launch = {"args": ["--no-sandbox"]}
        if chromium:
            launch["executable_path"] = chromium
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.goto(PAGE.as_uri() + "?record=1", wait_until="domcontentloaded")
        await page.wait_for_selector("body[data-ready='1']", state="attached", timeout=15000)
        duration = await page.evaluate("__explainer.duration")
        frames = int(duration * fps) + 1
        print(f"Rendering {duration:.1f}s → {frames} frames at {fps} fps → {out}")

        ffmpeg = subprocess.Popen(
            ["ffmpeg", "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", str(fps),
             "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
            stdin=subprocess.PIPE,
        )
        for i in range(frames):
            await page.evaluate(f"void __explainer.seek({i / fps})")
            ffmpeg.stdin.write(await page.screenshot(type="png"))
            if i % (fps * 10) == 0:
                print(f"  {i / fps:5.1f}s")
        ffmpeg.stdin.close()
        ffmpeg.wait()
        await browser.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "web" / "animations" / "mcp-agentic-architecture.mp4"))
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--chromium", default=None, help="path to a Chromium binary (default: Playwright's)")
    a = ap.parse_args()
    asyncio.run(render(pathlib.Path(a.out), a.fps, a.chromium, a.width, a.height))


if __name__ == "__main__":
    main()
