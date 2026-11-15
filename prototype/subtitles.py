"""PROTOTYPE - throwaway. Subtitles fitted to each render (<stem>_090.srt next to <stem>_090.mp4).

The cascade knows exactly which source frames each render shows and for how long, so any
source-timed text can be moved onto the render's clock:
  * real subtitles (anchored to the audio by align_subs.py, decision #62): each line keeps
    its text; a line whose speech is mostly gone (< 20% kept, as in the report) is dropped
  * otherwise (no subtitles, or machine captions, decision #65): cues are rebuilt from the
    Whisper words the render still contains, so removed sentences and fillers vanish too
Players such as VLC and mpv load a .srt with the video's name automatically.

Usage (existing renders): .venv/Scripts/python prototype/subtitles.py media/film.mp4 [--subs media/film.srt]
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np

MAX_LINE = 42           # characters per line, two lines per cue
MAX_CUE_S = 6.0
GAP_S = 0.8             # a pause this long starts a new cue
MIN_SHOW_S = 0.8        # extend short cues up to this, without overlapping the next
LOST_BELOW = 0.2        # a subtitle line with less than this share of its span kept is dropped
PUNCT_MIN = 0.15        # same test as carve_proto.SUB_PUNCT_MIN: real subtitles are punctuated


def time_map(plan, durs, n):
    """Per source frame: output start time and display duration (-1 where not shown), plus
    the next / previous shown frame for snapping."""
    pos = np.full(n, -1.0)
    dur = np.zeros(n)
    t = 0.0
    for it, d in zip(plan, durs):
        f = (it[0] if it[2] < 0.5 else it[1]) if isinstance(it, tuple) else it
        if pos[f] < 0:
            pos[f], dur[f] = t, d
        t += d
    shown = pos >= 0
    idx = np.arange(n)
    nxt = np.minimum.accumulate(np.where(shown, idx, n)[::-1])[::-1]
    prv = np.maximum.accumulate(np.where(shown, idx, -1))
    return pos, dur, nxt, prv, t


def to_out(t_src, fps, m, forward):
    """Output time of a source time; snaps to the next (forward) or previous shown frame."""
    pos, dur, nxt, prv, total = m
    n = len(pos)
    f = min(max(int(t_src * fps), 0), n - 1)
    if pos[f] >= 0:
        return pos[f] + (t_src * fps - f) * dur[f]
    g = nxt[f] if forward else prv[f]
    if g < 0 or g >= n:
        return None
    return pos[g] if forward else pos[g] + dur[g]


def wrap(text):
    text = " ".join(text.split())
    if len(text) <= MAX_LINE:
        return text
    words, best = text.split(" "), None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = max(len(a), len(b))
        if best is None or score < best[0]:
            best = (score, a + "\n" + b)
    return best[1]


def stamp(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(cues, path):
    cues = sorted((a, b, t) for a, b, t in cues if t.strip())
    out = []
    for i, (a, b, t) in enumerate(cues):
        nxt = cues[i + 1][0] if i + 1 < len(cues) else None
        if nxt is not None and b > nxt - 0.04:              # one subtitle on screen at a time
            b = max(a + 0.3, nxt - 0.04)
        if b - a < MIN_SHOW_S:                               # long enough to read
            b = a + MIN_SHOW_S if nxt is None else max(b, min(a + MIN_SHOW_S, nxt - 0.04))
        out.append(f"{i + 1}\n{stamp(a)} --> {stamp(b)}\n{wrap(t)}\n")
    Path(path).write_text("\n".join(out), encoding="utf-8")
    return len(cues)


def source(outdir):
    """('subs', [(start_s, end_s, text)]) for real anchored subtitles, else ('asr', words)."""
    al = outdir / "subs_aligned.json"
    if al.exists():
        lines = json.loads(al.read_text(encoding="utf-8"))["lines"]
        texts = [L["text"] for L in lines]
        rate = sum(len(re.findall(r"[.?!,]", t)) for t in texts) / max(1, sum(len(t.split()) for t in texts))
        if rate >= PUNCT_MIN:
            return "subs", [(L["start"], L["end"], L["text"]) for L in lines]
    segs = json.loads((outdir / "words.json").read_text(encoding="utf-8"))
    return "asr", [w for s in segs for w in s["words"]]


def fit(kind, items, keep, fps, m):
    """Cues on the render's clock."""
    cues = []
    if kind == "subs":
        for s, e, text in items:
            f0, f1 = int(s * fps), min(len(keep) - 1, int(np.ceil(e * fps)))
            if f1 < f0 or keep[f0:f1 + 1].mean() < LOST_BELOW:
                continue
            a, b = to_out(s, fps, m, True), to_out(e, fps, m, False)
            if a is not None and b is not None:
                cues.append((a, max(a, b), text))           # zero-length lines get the minimum later
        return cues
    kept = []
    for w in items:
        c = int((w["start"] + w["end"]) / 2 * fps)
        if 0 <= c < len(keep) and keep[c]:
            a, b = to_out(w["start"], fps, m, True), to_out(w["end"], fps, m, False)
            if a is not None and b is not None:
                kept.append((a, max(b, a + 0.05), w["word"].strip()))
    cur = []
    for a, b, t in kept:
        if cur:
            text = " ".join(x[2] for x in cur)
            if (a - cur[-1][1] > GAP_S or b - cur[0][0] > MAX_CUE_S or len(text) + 1 + len(t) > 2 * MAX_LINE
                    or (re.search(r"[.?!]$", cur[-1][2]) and len(text) >= MAX_LINE // 2)):
                cues.append((cur[0][0], cur[-1][1], text))
                cur = []
        cur.append((a, b, t))
    if cur:
        cues.append((cur[0][0], cur[-1][1], " ".join(x[2] for x in cur)))
    return cues


def write_for_render(outdir, stem, fr, plan, durs, keep, fps):
    kind, items = source(outdir)
    m = time_map(plan, durs, len(keep))
    path = outdir / f"{stem}_{int(fr * 100):03d}.srt"
    cues = fit(kind, items, keep, fps, m)
    if not cues:                                  # nothing is said: no subtitle file
        path.unlink(missing_ok=True)
        return path, 0, kind
    return path, write_srt(cues, path), kind


def main():
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import carve_proto as cp
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--fractions", type=float, nargs="+", default=cp.DEFAULT_FRACTIONS)
    args = ap.parse_args()
    src = Path(args.src)
    stem = src.stem
    outdir = Path("renders") / stem
    info = cp.probe(src)
    fps = info["fps"]
    z = np.load(outdir / "features.npz")
    F = {k: z[k] for k in z.files}
    n = len(F["d"])
    order = json.loads((outdir / "order.json").read_text(encoding="utf-8"))
    xmask = np.zeros(n, bool)
    plan_npz = outdir / "plan.npz"
    classic = len(order[0]) < 11            # rendered before decisions #70-#76
    if plan_npz.exists() and not classic:
        xmask = np.load(plan_npz)["xmask"]
    elif not classic:
        xmask = cp.style_xmask(src, F, fps, outdir)
    rank_d = cp.make_rank_d(F)
    for fr in args.fractions:
        if classic:
            sp, xs = cp.speed_for(fr), 1.0
            keep = cp.keep_mask(order, n, cp.carve_for(fr))
        else:
            keep, sp, xs = cp.plan_for(order, n, fr, cp.SPEED_SLOPE, xmask)
        plan, _ = cp.picture_plan(keep, F, rank_d)
        durs = [1.0 / (fps * sp * (xs if xmask[it[0] if isinstance(it, tuple) else it] else 1.0)) for it in plan]
        path, k, kind = write_for_render(outdir, stem, fr, plan, durs, keep, fps)
        print(f"[subtitles] {path}: {k} cues from {'subtitles' if kind == 'subs' else 'speech recognition'}, "
              f"render clock {sum(durs) / 60:.2f} min")


if __name__ == "__main__":
    main()
