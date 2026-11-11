"""PROTOTYPE - throwaway. Blind bake-off: how to heal a mid-shot (same-camera) join.

Variants per join, same 3 s of output around the cut (heals live in heals.py, decision #67):
  hard            plain jump cut
  dissolve6       6-frame cross-dissolve of the co-timed handle pairs (current render)
  flowdissolve6   the same pairs, aligned by DIS optical flow before blending
  rifemorph6      the same pairs, merged by RIFE 4.26 (warp + mask) at the dissolve's alpha
  flowinterp6     warp-only in-betweens of the two end frames (DIS)    } only at joins with
  rife6           warp-only in-betweens of the two end frames (RIFE)   } no speech (#67)

The earlier patch/snap variants were rejected (decision #59) and are gone.

Run after carve_proto.py:
  .venv/Scripts/python prototype/bakeoff.py media/tears_of_steel_720p.mov
Output: renders/<stem>/bakeoff/index.html (+ clips). Open via serve.py: /bakeoff/index.html
Add --page-only to rebuild just the page from the existing clips (after a template change).
See docs/research/frame-infilling-at-joins.md for the reasoning.
"""
import json
import random
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import carve_proto as cp  # noqa: E402
import heals  # noqa: E402

CLIP_W = 640
CTX = 36          # output frames before / after the join (3 s total at 24 fps)
MAX_JOINS = 12    # per film: half with speech at the join, half without, spread over jump size
SPEECH_PAD = 2    # frames of margin around a word when deciding "speech at the join"
FRACTIONS = [0.9, 0.75, 0.6, 0.3, 0.2]
VARIANTS = ["hard", "dissolve6", "flowdissolve6", "rifemorph6", "flowinterp6", "rife6"]


def decode(src, f0, count, fps, W):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{f0 / fps:.4f}", "-i", str(src),
                          "-vf", f"scale={W}:-2", "-frames:v", str(count), "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    H = len(raw) // (count * W * 3)
    return np.frombuffer(raw, np.uint8)[: count * H * W * 3].reshape(count, H, W, 3)


def split(variant):
    name = "".join(ch for ch in variant if not ch.isdigit())
    digits = "".join(ch for ch in variant if ch.isdigit())
    return name, int(digits) if digits else 0


def build(p, q, variant, cacheA, cacheB, offA, offB):
    """Return (frames, info) for one variant. cacheA[i] = source frame offA+i, same for B."""
    A = lambda f: cacheA[f - offA].astype(np.float32)
    B = lambda f: cacheB[f - offB].astype(np.float32)
    name, K = split(variant)
    h = K // 2
    pre = [A(f) for f in range(p - CTX + 1, p - h + 1)]
    post = [B(f) for f in range(q + h, q + CTX)]
    heal, info = [], {}
    if name != "hard":
        a = [A(p - h + 1 + t) for t in range(K)]
        b = [B(q - h + t) for t in range(K)]
        heal, info = heals.HEALS[name](a, b, A(p - h), B(q + h))
    frames = pre + heal + post
    return [np.clip(f + 0.5, 0, 255).astype(np.uint8) for f in frames], info


def audio_clip(audio, spf, p, q, h_xf):
    a = audio[(p - CTX + 1) * spf:(p + 1) * spf]
    b = audio[q * spf:(q + CTX) * spf]
    out = np.concatenate([a, b]).copy()
    j = len(a)
    ramp = np.linspace(0, np.pi / 2, 2 * h_xf, dtype=np.float32)[:, None]
    out[j - h_xf:j + h_xf] = (audio[(p + 1) * spf - h_xf:(p + 1) * spf + h_xf] * np.cos(ramp)
                              + audio[q * spf - h_xf:q * spf + h_xf] * np.sin(ramp))
    return out


def word_frames(words_json, n, fps):
    m = np.zeros(n, bool)
    if Path(words_json).exists():
        for seg in json.loads(Path(words_json).read_text(encoding="utf-8")):
            for w in seg["words"]:
                m[max(0, int(w["start"] * fps) - SPEECH_PAD):min(n, int(np.ceil(w["end"] * fps)) + SPEECH_PAD)] = True
    return m


def pick(cands, k):
    """Up to k joins spread evenly over the visual jump size D."""
    cands = sorted(cands, key=lambda c: c[2])
    if len(cands) <= k:
        return cands
    return [cands[int(round(i * (len(cands) - 1) / (k - 1)))] for i in range(k)]


def write_page(bdir, cards):
    tpl = (Path(__file__).parent / "bakeoff_template.html").read_text(encoding="utf-8")
    (bdir / "index.html").write_text(tpl.replace("/*DATA*/null", json.dumps(cards)), encoding="utf-8")
    print(f"[bakeoff] {bdir / 'index.html'}")


def main():
    src = Path(sys.argv[1])
    outdir = Path("renders") / src.stem
    bdir = outdir / "bakeoff"
    if "--page-only" in sys.argv:              # template changed: rebuild the page, keep the clips
        html = (bdir / "index.html").read_text(encoding="utf-8")
        start = html.index("const CARDS = ") + len("const CARDS = ")
        cards, _ = json.JSONDecoder().raw_decode(html[start:])
        write_page(bdir, cards)
        return
    bdir.mkdir(exist_ok=True)
    for old in bdir.glob("j*_*.mp4"):          # clips from an earlier bake-off
        old.unlink()
    fps = cp.probe(src)["fps"]
    z = np.load(outdir / "features.npz")
    feats = {k: z[k] for k in z.files}
    n = len(feats["d"])
    order = json.loads((outdir / "order.json").read_text())
    speech = word_frames(outdir / "words.json", n, fps)
    credits = cp.credits_mask(feats["dark"], fps, speech)
    shot, g = feats["shot"], feats["g"]
    h = max(split(v)[1] for v in VARIANTS) // 2
    joins = {}
    for fr in FRACTIONS:
        rs = cp.runs(cp.keep_mask(order, n, cp.carve_for(fr)))
        for (s0, e0), (s1, e1) in zip(rs[:-1], rs[1:]):
            p, q = e0 - 1, s1
            if shot[p] == shot[q] and not credits[p] and not credits[q] and p - CTX - 12 > 0 and q + CTX + 12 < n:
                joins.setdefault((p, q), fr)
    cands = []
    for (p, q), fr in joins.items():
        talk = bool(speech[p - h + 1:p + 1].any() or speech[q:q + h].any())
        D = float(np.abs(g[p].astype(np.int16) - g[q]).mean())
        cands.append(((p, q), fr, D, talk))
    chosen = pick([c for c in cands if c[3]], MAX_JOINS // 2) + pick([c for c in cands if not c[3]], MAX_JOINS // 2)
    chosen.sort(key=lambda c: c[0])
    print(f"[bakeoff] {len(cands)} distinct story mid-shot joins ({sum(c[3] for c in cands)} with speech); "
          f"testing {len(chosen)}")
    sr = 48000
    spf = int(round(sr / fps))
    audio = cp.read_audio(src, sr, 2)
    rng = random.Random(7)
    cards = []
    for ji, ((p, q), fr, D, talk) in enumerate(chosen):
        offA, offB = p - CTX - 12, q - 24
        cacheA = decode(src, offA, CTX + 26, fps, CLIP_W)
        cacheB = decode(src, offB, CTX + 26, fps, CLIP_W)
        variants = [v for v in VARIANTS if v == "hard" or not (talk and heals.is_endpoint(split(v)[0]))]
        labels = list("ABCDEF"[:len(variants)])
        rng.shuffle(labels)
        card = {"join": ji, "orig": f"{p/fps//60:.0f}:{p/fps%60:05.2f}", "skip_s": round((q - p - 1) / fps, 2),
                "first_at": f"{fr:.0%}", "speech": talk, "D": round(D, 1), "variants": []}
        wav = bdir / "tmp.wav"
        with wave.open(str(wav), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes((np.clip(audio_clip(audio, spf, p, q, 240), -1, 1) * 32767).astype(np.int16).tobytes())
        for v, lab in zip(variants, labels):
            frames, vinfo = build(p, q, v, cacheA, cacheB, offA, offB)
            name = f"j{ji:02d}_{lab}.mp4"
            Hc, Wc = frames[0].shape[:2]
            enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                    "-s", f"{Wc}x{Hc}", "-r", str(fps), "-i", "-", "-i", str(wav),
                                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                                    "-c:a", "aac", "-shortest", str(bdir / name)], stdin=subprocess.PIPE)
            for f in frames:
                enc.stdin.write(f.tobytes())
            enc.stdin.close()
            enc.wait()
            card["variants"].append({"label": lab, "variant": v, "file": name, **vinfo})
        card["variants"].sort(key=lambda x: x["label"])
        cards.append(card)
        print(f"[bakeoff] join {ji} at {card['orig']} (skip {card['skip_s']}s, D={card['D']}, "
              f"{'speech' if talk else 'no speech'}): " + ", ".join(
                  x["variant"] + (f" {x['solve_s']}s" if "solve_s" in x else "")
                  + (f" flow {x['flow_px']}px fb {x['fallback']}" if "flow_px" in x else "")
                  for x in sorted(card["variants"], key=lambda x: VARIANTS.index(x["variant"]))))
    (bdir / "tmp.wav").unlink(missing_ok=True)
    write_page(bdir, cards)


if __name__ == "__main__":
    main()
