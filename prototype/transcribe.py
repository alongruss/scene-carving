"""PROTOTYPE - throwaway. Local speech recognition with word timings (faster-whisper, CPU).

Usage: .venv/Scripts/python prototype/transcribe.py media/tears_of_steel_720p.mov
Writes renders/<stem>/words.json: [{start, end, text, words: [{start, end, word, prob}]}]
The model (Systran/faster-whisper-small.en, ~486 MB) is cached under cache/whisper (gitignored).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

# Whisper normally drops disfluencies; a filler-laden prompt makes it transcribe
# "um", "uh" and stutters verbatim, so they can become cheap seams (decision #60).
VERBATIM_PROMPT = "Umm, let me think like, hmm... Okay, uh, here's what I'm, I'm, like, thinking."
SR = 16000


def load_model():
    from faster_whisper import WhisperModel
    return WhisperModel("small.en", device="cpu", compute_type="int8", download_root="cache/whisper")


def load_audio16(src):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def main():
    src = Path(sys.argv[1])
    out = Path("renders") / src.stem / "words.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    audio = load_audio16(src)
    t0 = time.time()
    model = load_model()
    print(f"[asr] model ready ({time.time()-t0:.0f}s)", flush=True)
    segments, info = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=True,
                                      condition_on_previous_text=False, beam_size=5,
                                      initial_prompt=VERBATIM_PROMPT)
    result = []
    for s in segments:
        result.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                       "words": [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip(),
                                  "prob": round(w.probability, 3)} for w in (s.words or [])]})
        print(f"[asr] {s.start:7.2f}-{s.end:7.2f} {s.text.strip()}", flush=True)
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"[asr] {len(result)} segments, {sum(len(s['words']) for s in result)} words -> {out} "
          f"({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
