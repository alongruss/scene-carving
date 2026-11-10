"""PROTOTYPE - throwaway. Anchor subtitle lines to the audio with Whisper (iteration 7, decision #62).

Subtitle timing is coarse (often whole seconds) and release-dependent: a constant
offset, PAL/NTSC framerate drift, or jumps where scenes were added or cut. This aligns
every subtitle line to THIS film's audio:

  1 anchors    monotonic token alignment (difflib) of subtitle text vs ASR words
  2 transform  robust t_audio = a*t_sub + b (a snapped to known framerate ratios),
               then piecewise offsets where residuals jump (release edits)
  3 refine     heard line   -> its ASR word times                        ("asr")
               unheard line -> Whisper re-run on the line's window with the
                               line text as prompt, gated by Silero VAD  ("prompted")
               partly heard -> ASR words + VAD speech in the window       ("asr+vad")
               else         -> VAD speech in the mapped window            ("vad")
               else         -> the mapped cue span                        ("mapped")
  4 output     renders/<stem>/subs_aligned.json, <stem>.aligned.srt, report

Usage:
  .venv/Scripts/python prototype/align_subs.py media/tears_of_steel_720p.mov media/TOS-en.srt
  .venv/Scripts/python prototype/align_subs.py media/tears_of_steel_720p.mov media/TOS-en.srt --selftest
"""
import argparse
import difflib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import carve_proto as cp  # noqa: E402
from transcribe import SR, load_audio16, load_model  # noqa: E402

RATIOS = [1.0, 25 / 23.976, 23.976 / 25, 24 / 25, 25 / 24, 24 / 23.976, 23.976 / 24]
INLIER_S = 0.8        # anchor counts as fitting the transform within this
JUMP_S = 1.0          # a sustained residual jump this big starts a new piece (release edit)
JUMP_RUN = 3          # ... over at least this many consecutive anchors
NEAR_S = 2.0          # a matched ASR word must lie this close to the line's mapped window
WIN_PAD_S = 1.0       # prompted re-run / VAD window padding around the mapped line
WIN_GRID_S = 0.5      # ... with boundaries snapped to this grid
ACCEPT_COVER = 0.6    # share of the line's tokens that must be recognised
MAX_WORD_S = 1.0      # a single word longer than this was stretched over silence
CONF = {"asr": 0.95, "prompted": 0.75, "asr+vad": 0.6, "vad": 0.5, "mapped": 0.3}


def toks(text):
    return [t.strip("'") for t in re.findall(r"[a-z0-9']+", text.lower()) if t.strip("'")]


def content(t):
    return len(t) >= 3 and t not in cp.STOPWORDS


def flat_words(words_json):
    return [w for s in json.loads(Path(words_json).read_text(encoding="utf-8")) for w in s["words"]]


def build_pairs(cues, words):
    """Monotonic token matches: (cue idx, word idx, est. subtitle time, audio time, token)."""
    S = []
    for ci, (s, e, text) in enumerate(cues):
        tt = toks(text)
        for k, t in enumerate(tt):
            S.append((t, ci, s + (e - s) * (k + 0.5) / len(tt)))
    A = [(t, wi) for wi, w in enumerate(words) if w["prob"] >= 0.5 for t in toks(w["word"])]
    sm = difflib.SequenceMatcher(None, [x[0] for x in S], [x[0] for x in A], autojunk=False)
    pairs = []
    for i, j, size in sm.get_matching_blocks():
        for k in range(size):
            t, ci, ts = S[i + k]
            w = words[A[j + k][1]]
            pairs.append((ci, A[j + k][1], ts, (w["start"] + w["end"]) / 2, t))
    return pairs


def piecewise(x, y, a):
    """Offsets for scale a, with a new piece wherever residuals jump for JUMP_RUN anchors."""
    o = np.argsort(x)
    xs, rs = x[o], (y - a * x)[o]
    segs = [[-1e9, []]]
    c = float(np.median(rs[:5]))                 # robust seed: first few anchors
    i = 0
    while i < len(xs):
        if abs(rs[i] - c) > JUMP_S:
            nxt = rs[i:i + JUMP_RUN]
            if len(nxt) == JUMP_RUN and np.all(np.abs(nxt - c) > JUMP_S) and np.ptp(nxt) < 2 * INLIER_S:
                segs.append([(xs[i - 1] + xs[i]) / 2 if i else -1e9, list(nxt)])
                c = float(np.median(nxt))
                i += JUMP_RUN
                continue
            i += 1                               # isolated outlier
            continue
        segs[-1][1].append(rs[i])
        c = float(np.median(segs[-1][1]))
        i += 1
    segments = [(s, float(np.median(v))) for s, v in segs if v]
    starts = np.array([s for s, _ in segments])
    offs = np.array([b for _, b in segments])
    mapper = lambda t: a * t + offs[np.clip(np.searchsorted(starts, t, "right") - 1, 0, None)]  # noqa: E731
    res = np.abs(y - np.array([mapper(t) for t in x]))
    return segments, mapper, res


def fit_transform(pairs):
    """Pick the framerate ratio by the FINAL piecewise fit (inliers, fewer pieces, residual)."""
    P = np.array([(ts, ta) for _, _, ts, ta, t in pairs if content(t)])
    if len(P) < 3:
        return 1.0, [(-1e9, 0.0)], (lambda t: t), {"anchors": len(P)}
    x, y = P[:, 0], P[:, 1]
    fits = []
    for a in RATIOS:
        segments, mapper, res = piecewise(x, y, a)
        fits.append(((res < INLIER_S).sum() - 2 * (len(segments) - 1), float(np.median(res)), a,
                     segments, mapper, res))
    top = max(f[0] for f in fits)
    good = [f for f in fits if f[0] >= top - 2]          # within 2 anchors of the best support
    floor = min(f[1] for f in good)
    tied = [f for f in good if f[1] <= floor + 0.05]     # within 0.05 s of the best residual
    # among ties: the simplest model - ratio closest to 1, then fewest pieces
    _, _, a, segments, mapper, res = min(tied, key=lambda f: (abs(np.log(f[2])), len(f[3])))
    return a, segments, mapper, {"anchors": int(len(P)), "median_residual_s": round(float(np.median(res)), 3),
                                 "inliers": int((res < INLIER_S).sum())}


def vad_regions(clip, w0):
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    opts = VadOptions(threshold=0.35, min_silence_duration_ms=200, speech_pad_ms=60)
    return [(r["start"] / SR + w0, r["end"] / SR + w0) for r in get_speech_timestamps(clip, opts)]


def cover(text_tokens, word_tokens):
    sm = difflib.SequenceMatcher(None, text_tokens, word_tokens, autojunk=False)
    return sum(b.size for b in sm.get_matching_blocks()) / max(1, len(text_tokens))


def matched_words(text_tokens, wlist):
    """(coverage, the contiguous run of words from first to last token match)."""
    idx = [wi for wi, w in enumerate(wlist) for _ in toks(w["word"])]
    sm = difflib.SequenceMatcher(None, text_tokens, [t for w in wlist for t in toks(w["word"])], autojunk=False)
    hits = [idx[b.b + k] for b in sm.get_matching_blocks() for k in range(b.size)]
    cov = sum(b.size for b in sm.get_matching_blocks()) / max(1, len(text_tokens))
    return cov, (wlist[min(hits):max(hits) + 1] if hits else [])


def align(srt_path, words_json, audio, model, log=print):
    cues = cp.parse_srt(srt_path)
    words = flat_words(words_json)
    dur = len(audio) / SR
    pairs = build_pairs(cues, words)
    a, segments, mapper, stats = fit_transform(pairs)
    log(f"[align] {len(cues)} lines, {stats['anchors']} anchors; scale {a:.5f}, pieces "
        + ", ".join(f"from {'start' if s < 0 else f'{s:.1f}s'} offset {b:+.2f}s" for s, b in segments)
        + f"; median residual {stats.get('median_residual_s')}s")
    by_cue = {}
    for ci, wi, ts, ta, t in pairs:
        s, e, _ = cues[ci]
        if mapper(s) - NEAR_S <= ta <= mapper(e) + NEAR_S:
            by_cue.setdefault(ci, set()).add(wi)
    lines = []
    for ci, (s, e, text) in enumerate(cues):
        ms, me = float(mapper(s)), float(mapper(e))
        tt = toks(text)
        hit = sorted(by_cue.get(ci, []))
        line_words, method, span = [], None, None
        if hit:
            line_words = words[hit[0]:hit[-1] + 1]
            cov = cover(tt, [x for w in line_words for x in toks(w["word"])])
            if cov >= ACCEPT_COVER:
                method, span = "asr", (line_words[0]["start"], line_words[-1]["end"])
        if method is None:
            # windows snap to a 0.5 s grid: a few-ms difference in the transform must not
            # change what Whisper is asked to listen to (stability across releases)
            w0 = max(0.0, np.floor((ms - WIN_PAD_S) / WIN_GRID_S) * WIN_GRID_S)
            w1 = min(dur, np.ceil((me + WIN_PAD_S) / WIN_GRID_S) * WIN_GRID_S)
            clip = audio[int(w0 * SR):int(w1 * SR)]
            vad = vad_regions(clip, w0) if len(clip) > SR // 10 else []
            segs, _ = model.transcribe(clip, language="en", word_timestamps=True, vad_filter=False,
                                       condition_on_previous_text=False, initial_prompt=text,
                                       beam_size=5, temperature=0.0)
            pw = [{"start": round(max(w.start, w.end - MAX_WORD_S) + w0, 3), "end": round(w.end + w0, 3),
                   "word": w.word.strip(), "prob": round(w.probability, 3)}
                  for sg in segs for w in (sg.words or [])]  # cap words stretched over a preceding silence
            # VAD gate: a prompted word only counts where there is actual speech
            pw = [w for w in pw if any(r0 - 0.15 <= (w["start"] + w["end"]) / 2 <= r1 + 0.15 for r0, r1 in vad)]
            pcov, pmatch = matched_words(tt, pw)
            if pmatch and pcov >= ACCEPT_COVER:
                # only the words that match the line, not everything said in the window
                method, line_words, span = "prompted", pmatch, (pmatch[0]["start"], pmatch[-1]["end"])
            else:
                near = [(r0, r1) for r0, r1 in vad if r1 >= ms - 0.25 and r0 <= me + 0.25]
                vad_cov = sum(min(r1, me) - max(r0, ms) for r0, r1 in near if min(r1, me) > max(r0, ms))
                if hit:
                    # partly heard: partial evidence never shrinks a line below its mapped span
                    method = "asr+vad"
                    lo = min([line_words[0]["start"], ms] + [r0 for r0, _ in near])
                    hi = max([line_words[-1]["end"], me] + [r1 for _, r1 in near])
                    span = (max(w0, lo), min(w1, hi))
                elif near:
                    method, line_words = "vad", []
                    span = (max(w0, near[0][0]), min(w1, near[-1][1]))
                    if vad_cov < 0.5 * (me - ms):  # VAD caught only part of the line
                        span = (min(span[0], ms), max(span[1], me))
                else:
                    method, line_words, span = "mapped", [], (ms, me)
        lines.append({"i": ci, "text": text, "sub_start": s, "sub_end": e, "start": round(span[0], 3),
                      "end": round(span[1], 3), "method": method, "conf": CONF[method],
                      "words": [dict(w) for w in line_words]})
    counts = {m: sum(l["method"] == m for l in lines) for m in CONF}
    log("[align] methods: " + ", ".join(f"{m}={c}" for m, c in counts.items()))
    return {"scale": a, "segments": segments, "stats": stats, "counts": counts, "lines": lines}


def write_srt(lines, path):
    fmt = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}"  # noqa: E731
    blocks = [f"{k + 1}\n{fmt(l['start'])} --> {fmt(l['end'])}\n{l['text']}\n" for k, l in enumerate(lines)]
    Path(path).write_text("\n".join(blocks), encoding="utf-8")


def selftest(src, srt, words_json, audio, model, outdir):
    """Distort the subtitle timing like other releases would, and check alignment recovers it."""
    base = {l["i"]: l for l in align(srt, words_json, audio, model, log=lambda *_: None)["lines"]}
    cues = cp.parse_srt(srt)
    cases = {"a: +3.0 s offset": lambda t: t + 3.0,
             "b: PAL speed-up x23.976/25 +1.5 s": lambda t: t * 23.976 / 25 + 1.5,
             "c: +4 s after 5:00 (inserted scene)": lambda t: t + (4.0 if t >= 300 else 0.0)}
    ok_all = True
    for name, f in cases.items():
        dpath = outdir / f"distorted_{name[0]}.srt"
        write_srt([{"start": f(s), "end": f(e), "text": t} for s, e, t in cues], dpath)
        res = align(dpath, words_json, audio, model, log=lambda *_: None)
        d = np.array([abs(l["start"] - base[l["i"]]["start"]) for l in res["lines"]])
        frac = float((d <= 0.25).mean())
        bps = [round(s, 1) for s, _ in res["segments"] if s > 0]
        ok = frac >= 0.9 and (name[0] != "c" or any(abs(bp - 300) < 15 for bp in bps))
        ok_all &= ok
        print(f"[selftest] {name}: {frac:.0%} of lines within ±0.25 s of baseline; scale {res['scale']:.5f}; "
              f"breakpoints {bps}; methods {res['counts']} -> {'PASS' if ok else 'FAIL'}", flush=True)
    return ok_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("srt")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", help="output JSON (default renders/<stem>/subs_aligned.json)")
    args = ap.parse_args()
    src = Path(args.src)
    outdir = Path("renders") / src.stem
    words_json = outdir / "words.json"
    t0 = time.time()
    audio = load_audio16(src)
    model = load_model()
    res = align(args.srt, words_json, audio, model)
    out = Path(args.out) if args.out else outdir / "subs_aligned.json"
    res["source_srt"] = str(args.srt)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    write_srt(res["lines"], outdir / f"{src.stem}.aligned.srt")
    moved = np.array([abs(l["start"] - l["sub_start"]) for l in res["lines"]])
    shrink = np.array([(l["sub_end"] - l["sub_start"]) - (l["end"] - l["start"]) for l in res["lines"]])
    print(f"[align] start moved median {np.median(moved):.2f}s (max {moved.max():.2f}s); "
          f"lines shorter by median {np.median(shrink):.2f}s -> {out} ({time.time()-t0:.0f}s)")
    for l in res["lines"]:
        if l["method"] != "asr":
            print(f"   {l['method']:8s} {l['sub_start']:7.2f}->{l['start']:7.2f}-{l['end']:7.2f}  {l['text']}")
    if args.selftest:
        print("[selftest] " + ("ALL PASS" if selftest(src, args.srt, words_json, audio, model, outdir) else "FAILURES"))


if __name__ == "__main__":
    main()
