"""PROTOTYPE - throwaway code. Liquid Retime carve-only feasibility check.

QUESTION
    Can a film be shortened by carving ONLY original whole frames and
    mixed-audio intervals - no synthesis, no speed or pitch change - without
    the seams being noticed? How far can it go before the seams show? And
    does a nested, greedy, spread-aware cascade feel right behind a
    liquid-rescale-style length slider?

SCOPE (deliberately small)
    - Signal-only scoring: no ASR, VAD models or LLMs.
      * visual join cost  = temporal forward energy (frame distance at the
        new join, relative to the shot's own motion)
      * audio join cost   = spectral discontinuity relative to local natural
        continuity, weighted by loudness
      * content proxy     = loudness rank + motion rank of what is removed
      * spread            = removed fraction near the seam
      * fragment penalty  = discourages leaving a few flash frames behind
    - Joint seams only: picture and audio are removed over the same interval
      (no decoupled cuts yet). Audio joins get 10 ms equal-power crossfades.
    - Every score is a percentile rank within THIS film (self-calibration).

RUN
    .venv/Scripts/python prototype/carve_proto.py media/tears_of_steel_720p.mov
    Optional flags: --fractions 0.9 0.75 0.6   --no-render   --stop 0.2

OUTPUT  renders/<stem>/  (gitignored)
    viewer.html   open by double-click: slider preview, seam map, state panel
    proxy.mp4     small copy of the original, played by the viewer
    <stem>_090.mp4 ...   real carved renders (frame-accurate, crossfaded)
    report.txt    numbers per length
"""
import argparse
import heapq
import json
import subprocess
import time
import wave
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

# --- knobs (global, NOT per film) -------------------------------------------
SEAM_SIZES = (3, 6, 12, 24, 48, 96)  # candidate seam lengths in frames
SPREAD_WIN_S = 4.0                   # half-window for the spread term
LAMBDA_SPREAD = 1.5                  # spread weight (per removed frame)
MIN_FRAGMENT = 6                     # kept runs shorter than this = flash
FRAGMENT_PENALTY = 1.0
JOIN_BASE = 0.4                      # every join is a risk, even a "free" one
VISIBLE_JUMP_PENALTY = 4.0           # extra join cost at the most visible jumps
SMALL_W = 160                        # analysis frame width
XFADE_MS = 10
KIND_NAMES = ["hold", "jump", "at-cut", "shot-drop", "edge"]


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def probe(path):
    out = sh(["ffprobe", "-v", "error", "-select_streams", "v:0",
              "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
              "-of", "json", str(path)], capture_output=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = map(int, s["r_frame_rate"].split("/"))
    return {"w": s["width"], "h": s["height"], "fps": num / den,
            "n": int(s.get("nb_frames") or 0)}


def read_gray(path, W, H):
    raw = sh(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
              f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
             capture_output=True).stdout
    n = len(raw) // (W * H)
    return np.frombuffer(raw, np.uint8)[: n * W * H].reshape(n, H, W)


def read_audio(path, sr, ch):
    raw = sh(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", str(ch),
              "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32)
    return a.reshape(-1, ch) if ch > 1 else a


def rank_fn(ref):
    s = np.sort(np.asarray(ref, np.float64))
    return lambda x: np.searchsorted(s, x) / len(s)


def sliding_median(x, k):
    pad = np.pad(x, k, mode="edge")
    return np.median(sliding_window_view(pad, 2 * k + 1), axis=1)


# --- 1. ANALYSIS -------------------------------------------------------------
def analyze(path, info, cache):
    if cache.exists():
        print(f"[analysis] cached: {cache}")
        z = np.load(cache)
        return {k: z[k] for k in z.files}
    t0 = time.time()
    W = SMALL_W
    H = int(round(info["h"] * W / info["w"] / 2)) * 2
    g = read_gray(path, W, H)
    n = len(g)
    print(f"[analysis] {n} frames decoded at {W}x{H} ({time.time()-t0:.0f}s)")

    gi = g.astype(np.int16)
    d = np.zeros(n, np.float32)
    d[1:] = np.abs(gi[1:] - gi[:-1]).mean(axis=(1, 2))
    del gi
    hist = np.stack([np.bincount(f.ravel() >> 3, minlength=32) for f in g])
    hist = hist.astype(np.float32) / hist.sum(1, keepdims=True)
    hd = np.zeros(n, np.float32)
    hd[1:] = 0.5 * np.abs(hist[1:] - hist[:-1]).sum(1)
    locmed = sliding_median(d, 12)
    cut = (hd > 0.1) & (d / (locmed + 1) > 3)  # checked on a contact sheet: mostly real cuts
    cut[0] = True
    shot = np.cumsum(cut) - 1

    sr = 16000
    a = read_audio(path, sr, 1)
    spf = sr / info["fps"]
    starts = np.minimum((np.arange(n) * spf).astype(np.int64), len(a) - 1)
    ends = np.minimum(((np.arange(n) + 1) * spf).astype(np.int64), len(a))
    c2 = np.concatenate([[0.0], np.cumsum(a.astype(np.float64) ** 2)])

    def db(s, e):
        return 10 * np.log10((c2[e] - c2[s]) / np.maximum(e - s, 1) + 1e-10)

    rms_db = db(starts, ends)
    E = int(0.02 * sr)
    start_db = db(starts, np.minimum(starts + E, len(a)))
    end_db = db(np.maximum(ends - E, 0), ends)

    L = int(0.04 * sr)
    win = np.hanning(L).astype(np.float32)
    edges = np.unique(np.geomspace(2, L // 2 + 1, 25).astype(int))

    def spec_at(s0):
        idx = np.minimum(s0[:, None] + np.arange(L)[None, :], len(a) - 1)
        mag = np.abs(np.fft.rfft(a[idx] * win, axis=1)) ** 2
        return np.log10(np.add.reduceat(mag, edges[:-1], axis=1) + 1e-9).astype(np.float32)

    spec_start = spec_at(starts)
    spec_end = spec_at(np.maximum(ends - L, 0))
    nat = np.zeros(n, np.float32)
    nat[1:] = np.abs(spec_end[:-1] - spec_start[1:]).mean(1)
    nat_local = sliding_median(nat, 12).astype(np.float32)

    feats = dict(g=g, d=d, cut=cut, shot=shot, rms_db=rms_db.astype(np.float32),
                 start_db=start_db.astype(np.float32), end_db=end_db.astype(np.float32),
                 spec_start=spec_start, spec_end=spec_end, nat=nat, nat_local=nat_local)
    np.savez(cache, **feats)
    print(f"[analysis] done in {time.time()-t0:.0f}s, {int(cut.sum())} shots")
    return feats


# --- 2. CASCADE (the liftable core) ------------------------------------------
def cascade(F, fps, stop_fraction):
    """Greedy, lazy-re-evaluated seam removal. Returns the nested removal order."""
    g, d, shot = F["g"], F["d"], F["shot"]
    n = len(d)
    cut = F["cut"].astype(bool)

    natural_d = d[~cut]
    rank_d = rank_fn(natural_d)
    rank_l = rank_fn(F["rms_db"])
    rank_s = rank_fn(F["nat"][1:])
    n_shots = int(shot.max()) + 1
    shot_start = np.searchsorted(shot, np.arange(n_shots), "left")
    shot_end = np.searchsorted(shot, np.arange(n_shots), "right") - 1
    shot_med = np.array([np.median(d[s + 1:e + 1]) if e > s else 0.0
                         for s, e in zip(shot_start, shot_end)])
    shot_med_rank = rank_d(shot_med)
    motion_rank = rank_d(d)
    loud_rank = rank_l(F["rms_db"])
    content = 0.5 * loud_rank + 0.5 * motion_rank
    cpre = np.concatenate([[0.0], np.cumsum(content)])
    spec_start, spec_end = F["spec_start"], F["spec_end"]
    start_db, end_db, nat_local = F["start_db"], F["end_db"], F["nat_local"]

    removed = np.zeros(n, bool)
    prev_k = np.arange(-1, n - 1)
    next_k = np.arange(1, n + 1)
    shot_kept = (shot_end - shot_start + 1).astype(np.int64)
    SW = int(SPREAD_WIN_S * fps)

    def join_cost(p, q):
        if p < 0 or q >= n:
            return 0.0, 0.0
        if shot[p] != shot[q]:
            vj = 0.1
        else:
            # forward energy, absolute: how big is the new discontinuity within
            # this film's range of frame-to-frame change? (relative-to-shot-motion
            # under-priced jump cuts in tracking shots - see README findings)
            # A visible jump is one perceptual event however long the seam is,
            # so it must not be amortised away by cost-per-frame ranking: steep
            # penalty once the jump is in the top 15% of natural change.
            D = np.abs(g[p].astype(np.int16) - g[q]).mean()
            r = float(rank_d(D))
            vj = r * r + VISIBLE_JUMP_PENALTY * max(0.0, r - 0.85) / 0.15
        dist = float(np.abs(spec_end[p] - spec_start[q]).mean())
        spec = max(0.0, float(rank_s(dist)) - float(rank_s(nat_local[p])))
        loud = max(float(rank_l(end_db[p])), float(rank_l(start_db[q])))
        return vj, 0.6 * spec + 0.4 * loud * loud

    def fragments(a, b, p, q):
        f = 0
        for start, step in ((p, -1), (q, 1)):
            if start < 0 or start >= n:
                continue
            x, c = start, 0
            while 0 <= x < n and not removed[x] and shot[x] == shot[start] and c < MIN_FRAGMENT:
                c += 1
                x += step
            if c < MIN_FRAGMENT and 0 <= x < n and removed[x]:
                f += 1
        for s in range(shot[a], shot[b] + 1):
            rem = min(b, shot_end[s]) - max(a, shot_start[s]) + 1
            left = shot_kept[s] - rem
            if 0 < left < MIN_FRAGMENT:
                f += 1
        return f

    def evaluate(a, b):
        L = b - a + 1
        p, q = int(prev_k[a]), int(next_k[b])
        vj, aj = join_cost(p, q)
        C = (cpre[b + 1] - cpre[a]) / L
        x0, x1 = max(0, a - SW), min(n, b + 1 + SW)
        S = LAMBDA_SPREAD * (removed[x0:x1].sum() + L) / (x1 - x0)
        Fp = FRAGMENT_PENALTY * fragments(a, b, p, q)
        total = JOIN_BASE + vj + aj + Fp + L * (C + S)
        return total / L, (p, q, vj, aj, C, S, Fp)

    heap = []

    def push(a, b):
        if a < 0 or b >= n or removed[a:b + 1].any():
            return
        sc, _ = evaluate(a, b)
        heapq.heappush(heap, (sc, a, b))

    t0 = time.time()
    for w in SEAM_SIZES:
        for a in range(0, n - w + 1, max(1, w // 2)):
            push(a, a + w - 1)
    print(f"[cascade] {len(heap)} initial candidates ({time.time()-t0:.0f}s)")

    order, kept, target = [], n, int(stop_fraction * n)
    while heap and kept > target:
        sc, a, b = heapq.heappop(heap)
        if removed[a:b + 1].any():
            continue
        new, parts = evaluate(a, b)
        if heap and new > heap[0][0] + 1e-12:
            heapq.heappush(heap, (new, a, b))
            continue
        p, q, vj, aj, C, S, Fp = parts
        shots_hit = range(shot[a], shot[b] + 1)
        drop = any(shot_kept[s] - (min(b, shot_end[s]) - max(a, shot_start[s]) + 1) == 0
                   for s in shots_hit)
        if p < 0 or q >= n:
            kind = 4
        elif drop:
            kind = 3
        elif shot[p] != shot[q]:
            kind = 2
        else:
            kind = 0 if motion_rank[a:b + 1].mean() < 0.35 else 1
        for s in shots_hit:
            shot_kept[s] -= min(b, shot_end[s]) - max(a, shot_start[s]) + 1
        removed[a:b + 1] = True
        if p >= 0:
            next_k[p] = q
        if q < n:
            prev_k[q] = p
        kept -= b - a + 1
        order.append([a, b, kind, round(new, 4), round(vj, 3), round(aj, 3),
                      round(C, 3), round(S, 3), round(Fp, 1)])
        for w in SEAM_SIZES:
            if p >= 0:
                push(p - w + 1, p)
            if q < n:
                push(q, q + w - 1)
    print(f"[cascade] {len(order)} seams removed down to {kept/n:.0%} ({time.time()-t0:.0f}s)")
    return order, dict(motion_rank=motion_rank, loud_rank=loud_rank,
                       shot_start=shot_start, shot_end=shot_end)


def keep_mask(order, n, fraction):
    target = n - round(fraction * n)
    removed, cum = np.zeros(n, bool), 0
    for a, b, *_ in order:
        if cum >= target:
            break
        removed[a:b + 1] = True
        cum += b - a + 1
    return ~removed


def runs(mask):
    idx = np.flatnonzero(np.diff(np.concatenate([[0], mask.astype(np.int8), [0]])))
    return list(zip(idx[0::2], idx[1::2]))  # [start, end) in frames


# --- 3. REPORT ---------------------------------------------------------------
def report(order, F, aux, fps, fractions, path):
    n = len(F["d"])
    shot_len = aux["shot_end"] - aux["shot_start"] + 1
    lines = [f"frames={n} fps={fps} duration={n/fps/60:.2f} min shots={len(shot_len)} "
             f"ASL={np.mean(shot_len)/fps:.2f}s", ""]
    for fr in fractions:
        keep = keep_mask(order, n, fr)
        removed_idx = set(np.flatnonzero(~keep))
        active = [o for o in order if o[0] in removed_idx]
        kinds = {k: 0 for k in KIND_NAMES}
        for o in active:
            kinds[KIND_NAMES[o[2]]] += 1
        joins = len(runs(keep)) - 1
        kept_per_shot = np.array([keep[s:e + 1].sum() for s, e in zip(aux["shot_start"], aux["shot_end"])])
        alive = kept_per_shot[kept_per_shot > 0]
        a, b = np.log(shot_len), np.log(alive)
        grid = np.sort(np.concatenate([a, b]))
        ks = np.max(np.abs(np.searchsorted(np.sort(a), grid, "right") / len(a)
                           - np.searchsorted(np.sort(b), grid, "right") / len(b)))
        w = int(10 * fps)
        local = sliding_window_view((~keep).astype(np.float32), w).mean(1)
        lines += [f"== keep {fr:.0%}: {keep.sum()/fps/60:.2f} min, {len(active)} seams, {joins} joins "
                  f"({joins/(keep.sum()/fps/60):.1f}/min)",
                  "   kinds: " + ", ".join(f"{k}={v}" for k, v in kinds.items()),
                  f"   shots kept {len(alive)}/{len(shot_len)}, ASL {np.mean(shot_len)/fps:.2f}s -> "
                  f"{np.mean(alive)/fps:.2f}s, KS(log shot len)={ks:.3f}",
                  f"   local removal (10s windows): max {local.max():.0%}, std {local.std():.3f}",
                  "   most expensive active seams (score, orig time, kind, vj, aj, C, S, frag):"]
        for o in sorted(active, key=lambda o: -o[3])[:8]:
            t = o[0] / fps
            lines.append(f"     {o[3]:.3f}  {int(t//60):02d}:{t%60:05.2f}  len {o[1]-o[0]+1:3d}f  "
                         f"{KIND_NAMES[o[2]]:9s} vj={o[4]} aj={o[5]} C={o[6]} S={o[7]} F={o[8]}")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


# --- 4. RENDER ---------------------------------------------------------------
def render(src, info, order, n, fractions, outdir, stem):
    fps, W, H = info["fps"], info["w"], info["h"]
    sr = 48000
    spf = int(round(sr / fps))
    audio = read_audio(src, sr, 2)
    h = int(sr * XFADE_MS / 2000)
    ramp = np.linspace(0, np.pi / 2, 2 * h, dtype=np.float32)[:, None]
    fo, fi = np.cos(ramp), np.sin(ramp)
    masks, encs = {}, {}
    for fr in fractions:
        keep = keep_mask(order, n, fr)
        masks[fr] = keep
        pieces, joins, pos = [], [], 0
        for s, e in runs(keep):
            seg = audio[s * spf:e * spf]
            pieces.append(seg)
            pos += len(seg)
            joins.append((pos, s * spf, e * spf))
        out = np.concatenate(pieces).copy()
        for (j, _, end_prev), (_, start_next, _) in zip(joins[:-1], joins[1:]):
            if j - h < 0 or j + h > len(out) or end_prev + h > len(audio) or start_next - h < 0:
                continue
            out[j - h:j + h] = audio[end_prev - h:end_prev + h] * fo + audio[start_next - h:start_next + h] * fi
        wav = outdir / f"{stem}_{int(fr*100):03d}.wav"
        with wave.open(str(wav), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
        mp4 = outdir / f"{stem}_{int(fr*100):03d}.mp4"
        encs[fr] = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p",
             "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", str(wav),
             "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-shortest", str(mp4)],
            stdin=subprocess.PIPE)
    fb = W * H * 3 // 2
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), "-f", "rawvideo",
                            "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE)
    t0 = time.time()
    for i in range(n):
        buf = dec.stdout.read(fb)
        if len(buf) < fb:
            break
        for fr, enc in encs.items():
            if masks[fr][i]:
                enc.stdin.write(buf)
        if i % 2000 == 0:
            print(f"[render] frame {i}/{n} ({time.time()-t0:.0f}s)")
    for enc in encs.values():
        enc.stdin.close()
        enc.wait()
    dec.wait()
    for fr in fractions:
        (outdir / f"{stem}_{int(fr*100):03d}.wav").unlink()
    print(f"[render] done ({time.time()-t0:.0f}s)")


# --- 5. VIEWER ---------------------------------------------------------------
def viewer(order, F, aux, info, fractions, outdir, stem):
    proxy = outdir / "proxy.mp4"
    if not proxy.exists():
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(info["src"]), "-vf", "scale=640:-2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "27", "-g", "12",
            "-keyint_min", "12", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
            str(proxy)])
    data = {
        "stem": stem, "fps": info["fps"], "n": len(F["d"]),
        "motion": (aux["motion_rank"] * 99).astype(int).tolist(),
        "loud": (aux["loud_rank"] * 99).astype(int).tolist(),
        "cuts": np.flatnonzero(F["cut"]).tolist(),
        "order": order, "kinds": KIND_NAMES,
        "renders": [f"{stem}_{int(fr*100):03d}.mp4" for fr in fractions],
        "fractions": fractions,
    }
    tpl = (Path(__file__).parent / "viewer_template.html").read_text(encoding="utf-8")
    (outdir / "viewer.html").write_text(tpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":"))),
                                        encoding="utf-8")
    print(f"[viewer] {outdir / 'viewer.html'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--fractions", type=float, nargs="+", default=[0.9, 0.75, 0.6])
    ap.add_argument("--stop", type=float, default=0.2)
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()
    src = Path(args.src)
    stem = src.stem
    outdir = Path("renders") / stem
    outdir.mkdir(parents=True, exist_ok=True)
    info = probe(src)
    info["src"] = src
    F = analyze(src, info, outdir / "features.npz")
    order, aux = cascade(F, info["fps"], args.stop)
    (outdir / "order.json").write_text(json.dumps(order), encoding="utf-8")
    report(order, F, aux, info["fps"], args.fractions, outdir / "report.txt")
    viewer(order, F, aux, info, args.fractions, outdir, stem)
    if not args.no_render:
        render(src, info, order, len(F["d"]), args.fractions, outdir, stem)


if __name__ == "__main__":
    main()
