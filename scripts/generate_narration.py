"""Generate an animation's voice-over track from a narration YAML, with local TTS.

Each cue is synthesised with Kokoro (open-weights, runs offline once the model
is cached) and placed at its `at` second on a silent track the length of the
animation, so the MP3 can play in sync with the GSAP timeline.

Usage (from repo root):
    uv run --python 3.12 --with kokoro --with soundfile --with 'misaki[en]' --with pip --with pyyaml \
        python scripts/generate_narration.py [data/narration/mcp-agentic-architecture.yaml]

Fails if a line runs into the next one: shorten the text or move its `at`.
Requires ffmpeg on PATH.
"""
import pathlib
import subprocess
import sys

import numpy as np
import soundfile as sf
import yaml
from kokoro import KPipeline

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "data" / "narration" / "mcp-agentic-architecture.yaml"
RATE = 24000
GAP = 0.05  # minimum silence between two lines, in seconds


def main() -> None:
    spec = yaml.safe_load(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT).read_text())
    cues = spec["cues"]
    pipeline = KPipeline(lang_code=spec["lang"], repo_id="hexgrad/Kokoro-82M")
    track = np.zeros(int(spec["duration"] * RATE), dtype=np.float32)

    overruns = 0
    for i, cue in enumerate(cues):
        parts = list(pipeline(cue["text"], voice=spec["voice"], speed=spec["speed"]))
        audio = np.concatenate([np.asarray(p.audio) for p in parts])
        start, end = cue["at"], cue["at"] + len(audio) / RATE
        limit = cues[i + 1]["at"] - GAP if i + 1 < len(cues) else spec["duration"]
        over = end > limit
        overruns += over
        print(f"{start:6.1f}-{end:6.1f}{'  OVERRUN' if over else ''}  {' '.join(p.phonemes for p in parts)}")
        first = int(start * RATE)
        track[first:first + len(audio)] += audio[: len(track) - first]

    if overruns:
        sys.exit(f"{overruns} line(s) overrun the next cue; nothing written.")

    out = ROOT / spec["output"]
    wav = out.with_suffix(".wav")
    sf.write(wav, track, RATE)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-ac", "1",
                    "-c:a", "libmp3lame", "-b:a", "64k", str(out)], check=True)
    wav.unlink()
    print(f"Wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
