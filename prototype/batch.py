"""PROTOTYPE - throwaway. Run the whole pipeline over several films, shortest first.

Per film: transcribe.py (skipped if words.json exists) -> align_subs.py (if a subtitle file
is given and not yet aligned) -> carve_proto.py --subs ... --render-height 720.
Logs go to renders/<stem>/pipeline.log; the key report lines are printed as each film ends.

Usage: .venv/Scripts/python prototype/batch.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

PY = sys.executable
FILMS = [  # (video, subtitles or None) - shorts first so results arrive early
    ("media/DuckandC1951.mp4", "media/DuckandC1951.asr.srt"),
    ("media/elephantsdream-720-h264-st-aac.mov", None),
    ("media/big_buck_bunny_480p_h264.mov", None),
    ("media/Sintel.2010.720p.mkv", None),
    ("media/Detour.mp4", "media/Detour.asr.srt"),
    ("media/his_girl_friday.mp4", "media/his_girl_friday.asr.srt"),
    ("media/NightOfTheLivingDead_PS3.mp4", "media/NightOfTheLivingDead_PS3.asr.srt"),
]
KEY = ("[cascade] speech", "[cascade] subtitles", "[cascade] title", "== keep", "   information",
       "   subtitle lines", "   kinds", "   join strategies", "[render] done", "[align] ", "[asr] ", "Traceback",
       "Error")


def run(cmd, log):
    t0 = time.time()
    with open(log, "a", encoding="utf-8") as lf:
        lf.write(f"\n$ {' '.join(map(str, cmd))}\n")
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace")
        for line in p.stdout:
            lf.write(line)
            if line.startswith(KEY) and not line.startswith("[asr]   "):
                print("   " + line.rstrip(), flush=True)
        p.wait()
    return p.returncode, time.time() - t0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # ASR text can hold any character
    for video, subs in FILMS:
        v = Path(video)
        if not v.exists():
            cands = sorted(v.parent.glob(v.stem.split("-")[0].split("_")[0] + "*.mkv")) if "sintel" in v.name else []
            if cands:
                v = cands[0]
            else:
                print(f"[batch] skip (missing): {video}", flush=True)
                continue
        out = Path("renders") / v.stem
        out.mkdir(parents=True, exist_ok=True)
        log = out / "pipeline.log"
        if (out / "pipeline.done").exists():
            print(f"[batch] already done: {v.name}", flush=True)
            continue
        print(f"\n[batch] === {v.name} ===", flush=True)
        if not (out / "words.json").exists():
            rc, s = run([PY, "-u", "prototype/transcribe.py", str(v)], log)
            print(f"[batch] transcribe rc={rc} {s/60:.1f} min", flush=True)
        if subs and Path(subs).exists():
            aligned = out / "subs_aligned.json"
            if not aligned.exists() or json.loads(aligned.read_text(encoding="utf-8")).get("source_srt") != subs:
                rc, s = run([PY, "-u", "prototype/align_subs.py", str(v), subs], log)
                print(f"[batch] align rc={rc} {s/60:.1f} min", flush=True)
        cmd = [PY, "-u", "prototype/carve_proto.py", str(v), "--render-height", "720"]
        if subs and Path(subs).exists():
            cmd += ["--subs", subs]
        rc, s = run(cmd, log)
        print(f"[batch] carve+render rc={rc} {s/60:.1f} min", flush=True)
        if rc == 0:
            (out / "pipeline.done").write_text(time.strftime("%Y-%m-%d %H:%M"), encoding="utf-8")
    print("\n[batch] all done", flush=True)


if __name__ == "__main__":
    main()
