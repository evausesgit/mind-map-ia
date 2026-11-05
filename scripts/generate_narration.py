"""Generate an animation's voice-over track from a narration YAML.

Each cue is synthesised, then placed at its `at` second on a silent track the
length of the animation, so the MP3 can play in sync with the GSAP timeline.

Two engines, picked by the YAML's `engine` key:

- `kokoro` (default): open-weights, runs offline once the model is cached.
    uv run --python 3.12 --with kokoro --with soundfile --with 'misaki[en]' --with pip --with pyyaml \
        python scripts/generate_narration.py [data/narration/mcp-agentic-architecture.yaml]

- `gradium`: Gradium's hosted TTS (gradium.ai), native French voices. Needs
  GRADIUM_API_KEY in the environment. Uses about one credit per character.
    uv run --python 3.12 --with numpy --with soundfile --with pyyaml \
        python scripts/generate_narration.py data/narration/mcp-agentic-architecture-fr.yaml

Fails if a line runs into the next one: shorten the text or move its `at`.
Requires ffmpeg on PATH.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

import numpy as np
import soundfile as sf
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "data" / "narration" / "mcp-agentic-architecture.yaml"
RATE = 24000
GAP = 0.05  # minimum silence between two lines, in seconds
GRADIUM_URL = "https://api.gradium.ai/api/post/speech/tts"


def kokoro_engine(spec):
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code=spec["lang"], repo_id="hexgrad/Kokoro-82M")

    def say(text):
        parts = list(pipeline(text, voice=spec["voice"], speed=spec["speed"]))
        return np.concatenate([np.asarray(p.audio) for p in parts]), " ".join(p.phonemes for p in parts)

    return say


def gradium_engine(spec):
    key = os.environ.get("GRADIUM_API_KEY")
    if not key:
        sys.exit("GRADIUM_API_KEY is not set.")
    settings = {k: spec[k] for k in ("temp", "padding_bonus") if k in spec}
    # Unchanged lines are reused from the cache: no credits spent, same take.
    cache = pathlib.Path(os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache")) / "mmia-narration"
    cache.mkdir(parents=True, exist_ok=True)

    def say(text):
        body = {"text": text, "voice_id": spec["voice"], "output_format": "pcm_24000", "only_audio": True}
        if settings:
            body["json_config"] = settings
        hit = cache / (hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:24] + ".pcm")
        if not hit.exists():
            req = urllib.request.Request(GRADIUM_URL, data=json.dumps(body).encode(),
                                         headers={"x-api-key": key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                hit.write_bytes(resp.read())
        pcm = np.frombuffer(hit.read_bytes(), dtype="<i2")
        return pcm.astype(np.float32) / 32768, text

    return say


def main() -> None:
    spec = yaml.safe_load(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT).read_text())
    cues = spec["cues"]
    say = {"kokoro": kokoro_engine, "gradium": gradium_engine}[spec.get("engine", "kokoro")](spec)
    track = np.zeros(int(spec["duration"] * RATE), dtype=np.float32)

    overruns = 0
    for i, cue in enumerate(cues):
        audio, shown = say(cue["text"])
        start, end = cue["at"], cue["at"] + len(audio) / RATE
        limit = cues[i + 1]["at"] - GAP if i + 1 < len(cues) else spec["duration"]
        over = end > limit
        overruns += over
        print(f"{start:6.1f}-{end:6.1f}{'  OVERRUN' if over else ''}  {shown}")
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
