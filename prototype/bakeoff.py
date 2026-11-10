"""PROTOTYPE - throwaway. Blind bake-off: how to heal a mid-shot (same-camera) join.

Variants per join, same 3 s of output around the cut:
  hard        plain jump cut
  dissolve6   6-frame cross-dissolve of the two handle streams (current render)
  patch6      per-pixel switch-time map (graph cut, alpha-expansion) over a 6-frame window:
              every output pixel shows the A-side until its own switch frame, then the
              B-side - a dissolve whose alpha is 0/1 per pixel (Kwatra et al. 2003 s.7A)
  patch12     same, 12-frame window
  snap+dissolve6 / snap+patch6   first shift the seam by k in [-6, 6] frames to the
              most similar frame pair (best-pair snap), then heal

Run after carve_proto.py:
  .venv/Scripts/python prototype/bakeoff.py media/tears_of_steel_720p.mov
Output: renders/<stem>/bakeoff/index.html (+ clips). Open via serve.py: /bakeoff/index.html
See docs/research/patching-from-other-times.md for the reasoning.
"""
import json
import random
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np
from maxflow import fastmin

sys.path.insert(0, str(Path(__file__).parent))
import carve_proto as cp  # noqa: E402

CLIP_W = 640
MAP_W = 256
CTX = 36          # output frames before / after the join (3 s total at 24 fps)
SNAP = 6
LAMBDA = 3.0      # smoothness of the switch-time map (grey levels per frame of difference)
FRACTIONS = [0.9, 0.75, 0.6, 0.3, 0.2]
VARIANTS = ["hard", "dissolve6", "patch6", "patch12", "snap+dissolve6", "snap+patch6"]


def decode(src, f0, count, fps, W):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{f0 / fps:.4f}", "-i", str(src),
                          "-vf", f"scale={W}:-2", "-frames:v", str(count), "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    H = len(raw) // (count * W * 3)
    return np.frombuffer(raw, np.uint8)[: count * H * W * 3].reshape(count, H, W, 3)


def box(x, r):
    """Box blur over the last two axes (H, W)."""
    k = 2 * r + 1
    p = np.pad(x, [(0, 0)] * (x.ndim - 2) + [(r, r), (r, r)], mode="edge")
    c = p.cumsum(-1).cumsum(-2)
    c = np.pad(c, [(0, 0)] * (x.ndim - 2) + [(1, 0), (1, 0)])
    return (c[..., k:, k:] - c[..., :-k, k:] - c[..., k:, :-k] + c[..., :-k, :-k]) / (k * k)


def switch_map(Aseq, Bseq, K):
    """Aseq[t] = A_{t-1} for t=0..K, Bseq[t] = B_t for t=0..K (grey, map res). Labels s=0..K."""
    Dt = np.stack([np.abs(Aseq[s] - Bseq[s]) for s in range(K + 1)])     # jump seen if switching at s
    Dt = box(Dt, 2)
    V = LAMBDA * np.abs(np.arange(K + 1)[:, None] - np.arange(K + 1)[None, :]).astype(np.float64)
    t0 = time.time()
    lab = fastmin.aexpansion_grid(np.ascontiguousarray(Dt.transpose(1, 2, 0), dtype=np.float64), V)
    energy = float(np.take_along_axis(Dt, lab[None].astype(np.int64), 0).mean())
    return lab.astype(np.float32), energy, time.time() - t0


def upsample(m, H, W):
    ys = (np.arange(H) + 0.5) * m.shape[0] / H - 0.5
    xs = (np.arange(W) + 0.5) * m.shape[1] / W - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, m.shape[0] - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, m.shape[1] - 1)
    y1, x1 = np.minimum(y0 + 1, m.shape[0] - 1), np.minimum(x0 + 1, m.shape[1] - 1)
    wy, wx = np.clip(ys - y0, 0, 1)[:, None], np.clip(xs - x0, 0, 1)[None, :]
    return (m[y0][:, x0] * (1 - wy) * (1 - wx) + m[y1][:, x0] * wy * (1 - wx)
            + m[y0][:, x1] * (1 - wy) * wx + m[y1][:, x1] * wy * wx)


def build(src, fps, p, q, variant, cacheA, cacheB, offA, offB):
    """Return (frames, info) for one variant. cacheA[i] = source frame offA+i, same for B."""
    A = lambda f: cacheA[f - offA].astype(np.float32)
    B = lambda f: cacheB[f - offB].astype(np.float32)
    info = {}
    if variant.startswith("snap+"):
        g = cp_feats["g"]
        best = min(range(-SNAP, SNAP + 1),
                   key=lambda k: np.abs(g[p + k].astype(np.int16) - g[q + k]).mean())
        p, q = p + best, q + best
        info["snap"] = best
        variant = variant[5:]
    K = 0 if variant == "hard" else int("".join(ch for ch in variant if ch.isdigit()))
    h = K // 2
    pre = [A(f) for f in range(p - CTX + 1, p - h + 1)]
    post = [B(f) for f in range(q + h, q + CTX)]
    heal = []
    if variant.startswith("dissolve"):
        heal = [A(p - h + 1 + t) * (1 - (t + 0.5) / K) + B(q - h + t) * ((t + 0.5) / K) for t in range(K)]
    elif variant.startswith("patch"):
        grey = lambda img: img.mean(-1)
        Hc, Wc = cacheA.shape[1:3]
        mh = int(round(Hc * MAP_W / Wc))
        small = lambda img: upsample(grey(img), mh, MAP_W)
        Aseq = [small(A(p - h + t)) for t in range(K + 1)]          # A_{t-1}
        Bseq = [small(B(q - h + t)) for t in range(K + 1)]          # B_t
        lab, energy, secs = switch_map(Aseq, Bseq, K)
        ghost = float(np.mean([np.abs(Aseq[t + 1] - Bseq[t]).mean() for t in range(K)]) / 2)
        sf = box(upsample(lab, Hc, Wc)[None], 2)[0]
        for t in range(K):
            alpha = np.clip(t - sf + 1, 0, 1)[..., None]
            heal.append(A(p - h + 1 + t) * (1 - alpha) + B(q - h + t) * alpha)
        info.update(energy=round(energy, 2), ghost=round(ghost, 2), solve_s=round(secs, 2))
    frames = pre + heal + post
    info.update(p=int(p), q=int(q), D=round(float(np.abs(cp_feats["g"][p].astype(np.int16)
                                                         - cp_feats["g"][q]).mean()), 1))
    return [np.clip(f + 0.5, 0, 255).astype(np.uint8) for f in frames], info, p, q


def audio_clip(audio, spf, p, q, h_xf):
    a = audio[(p - CTX + 1) * spf:(p + 1) * spf]
    b = audio[q * spf:(q + CTX) * spf]
    out = np.concatenate([a, b]).copy()
    j = len(a)
    ramp = np.linspace(0, np.pi / 2, 2 * h_xf, dtype=np.float32)[:, None]
    out[j - h_xf:j + h_xf] = (audio[(p + 1) * spf - h_xf:(p + 1) * spf + h_xf] * np.cos(ramp)
                              + audio[q * spf - h_xf:q * spf + h_xf] * np.sin(ramp))
    return out


def main():
    global cp_feats
    src = Path(sys.argv[1])
    outdir = Path("renders") / src.stem
    bdir = outdir / "bakeoff"
    bdir.mkdir(exist_ok=True)
    info = cp.probe(src)
    fps = info["fps"]
    z = np.load(outdir / "features.npz")
    cp_feats = {k: z[k] for k in z.files}
    n = len(cp_feats["d"])
    order = json.loads((outdir / "order.json").read_text())
    credits = cp.credits_mask(cp_feats["dark"], fps)
    shot = cp_feats["shot"]
    joins = {}
    for fr in FRACTIONS:
        rs = cp.runs(cp.keep_mask(order, n, fr))
        for (s0, e0), (s1, e1) in zip(rs[:-1], rs[1:]):
            p, q = e0 - 1, s1
            if shot[p] == shot[q] and not credits[p] and not credits[q] \
                    and p - CTX - SNAP > 0 and q + CTX + SNAP < n:
                joins.setdefault((p, q), fr)
    joins = sorted(joins.items())
    print(f"[bakeoff] {len(joins)} distinct story mid-shot joins across {FRACTIONS}")
    sr = 48000
    spf = int(round(sr / fps))
    audio = cp.read_audio(src, sr, 2)
    rng = random.Random(7)
    cards = []
    for ji, ((p, q), fr) in enumerate(joins):
        offA, offB = p - CTX - SNAP, q - 12 - SNAP
        cacheA = decode(src, offA, CTX + 12 + 2 * SNAP + 2, fps, CLIP_W)
        cacheB = decode(src, offB, CTX + 12 + 2 * SNAP + 2, fps, CLIP_W)
        labels = list("ABCDEF")
        rng.shuffle(labels)
        card = {"join": ji, "orig": f"{p/fps//60:.0f}:{p/fps%60:05.2f}", "skip_s": round((q - p - 1) / fps, 2),
                "first_at": f"{fr:.0%}", "variants": []}
        for v, lab in zip(VARIANTS, labels):
            frames, vinfo, pp, qq = build(src, fps, p, q, v, cacheA, cacheB, offA, offB)
            wav = bdir / "tmp.wav"
            with wave.open(str(wav), "wb") as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes((np.clip(audio_clip(audio, spf, pp, qq, 240), -1, 1) * 32767)
                               .astype(np.int16).tobytes())
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
        print(f"[bakeoff] join {ji} at {card['orig']} (skip {card['skip_s']}s): " + ", ".join(
            f"{x['variant']}" + (f" E={x['energy']}/ghost={x['ghost']} {x['solve_s']}s" if 'energy' in x else "")
            for x in sorted(card['variants'], key=lambda x: VARIANTS.index(x['variant']))))
    (bdir / "tmp.wav").unlink(missing_ok=True)
    tpl = (Path(__file__).parent / "bakeoff_template.html").read_text(encoding="utf-8")
    (bdir / "index.html").write_text(tpl.replace("/*DATA*/null", json.dumps(cards)), encoding="utf-8")
    print(f"[bakeoff] {bdir / 'index.html'}")


if __name__ == "__main__":
    main()
