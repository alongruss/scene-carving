"""PROTOTYPE - throwaway code. Scene Carving (liquid retiming) carve-only feasibility check.

QUESTION
    Can a film be shortened by carving ONLY original whole frames and
    mixed-audio intervals - no speed or pitch change - without the seams
    being noticed? How far can it go before they show? And does a nested,
    greedy, spread-aware cascade feel right behind a liquid-rescale-style
    length slider?

SCOPE (deliberately small)
    - Signal-only scoring (no ASR, VAD models or LLMs):
      * visual join cost  = absolute temporal forward energy at the new join;
        mid-shot joins cost far more than trims at existing cuts, and more
        again when subjects move (camera/subject split via phase correlation)
      * audio join cost   = spectral discontinuity vs local natural continuity,
        weighted by loudness
      * content proxy     = loudness rank + subject-motion rank
      * story weight      = stand-in for the plot layer: dark-dominant
        title/credit blocks score ~0 (a local VLM would do this for real)
      * spread, fragment penalty, per-join base cost
      * join costs only partially amortised over seam length (L**0.5)
    - Joint seams only (no decoupled cuts yet). Audio joins: 10 ms
      equal-power crossfades. Same-shot picture joins: 6-frame cross-dissolve
      of original frames (iteration 2, user decision 2026-11-10).
    - Every score is a percentile rank within THIS film (self-calibration).

RUN
    .venv/Scripts/python prototype/carve_proto.py media/tears_of_steel_720p.mov
    Optional flags: --fractions 0.9 0.75 0.6   --no-render   --stop 0.2

OUTPUT  renders/<stem>/  (gitignored)
    viewer.html, proxy.mp4, <stem>_090.mp4 ..., report.txt, order.json
"""
import argparse
import heapq
import json
import re
import subprocess
import time
import wave
from collections import Counter
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

# --- knobs (global, NOT per film) -------------------------------------------
SEAM_SIZES = (3, 6, 12, 24, 48, 96)  # candidate window seams, in frames
MAX_SHOT_SEAM_S = 10.0               # whole shots up to this length are seams too
SPREAD_WIN_S = 4.0                   # half-window for the spread term
LAMBDA_SPREAD = 1.5                  # spread weight (per removed frame)
MIN_FRAGMENT = 6                     # kept runs shorter than this = flash
FRAGMENT_PENALTY = 1.0
JOIN_BASE = 0.4                      # every join is a risk, even a "free" one
JOIN_AMORT = 0.5                     # join cost / L**JOIN_AMORT (not fully amortised)
AT_CUT_COST = 0.1                    # visual cost of a join that lands on a cut
SAME_SHOT_BASE = 1.0                 # mid-shot (same camera) joins are jarring
SUBJECT_W = 1.0                      # ... more so when subjects move near the join
VISIBLE_JUMP_PENALTY = 4.0           # extra cost at the most visible jumps
CREDITS_DARK = 0.42                  # dark-pixel share of a title/credit frame
CREDITS_MIN_S = 20.0                 # a title/credit block lasts at least this
CREDITS_STORY_W = 0.05               # story weight inside such a block
CREDITS_MAX_SPEECH = 0.15            # a dark block with more dialogue than this is story
CREDITS_CHAIN_S = 90.0               # credit blocks chain to the film's ends with gaps <= this
SUB_PUNCT_MIN = 0.15                 # punctuation per word: real subtitles ~0.4, machine captions <0.1
SENT_GAP_S = 2.0                     # a silence this long between words ends a sentence unit
SPEED_SLOPE = 0.125                  # film-wide speed = 1 + (1 - target) * this: 1.0x at 100%, 1.1x at 20% (#66)
SMALL_W = 160                        # analysis frame width
XFADE_MS = 10                        # audio crossfade
DISSOLVE_H = 3                       # picture dissolve = 2*H frames at same-shot joins
HARD_OK_RANK = 0.5                   # mid-shot jump this small needs no dissolve
BREATH_W = 1.5                       # per-frame cost of eating "breathing room"
DEFAULT_FRACTIONS = [0.9, 0.75, 0.6, 0.3]
# Information protection (iteration 4, needs renders/<stem>/words.json from transcribe.py)
WORD_W = 8.0                         # per frame: cutting INTO a word
MIDSENT_W = 2.0                      # per frame: pauses inside a sentence (rushes speech)
PLOT_BASE = 1.0                      # per frame: removing a WHOLE sentence ...
PLOT_W = 3.0                         # ... plus this x its plot score (0..1)
NONSPEECH_LOUD_W = 0.4               # non-speech content: loudness only (motion is not information)
FILLER_W = 0.3                       # per frame: fillers / stutter repeats are cheap (decision #60)
FILLER_PAD = 3                       # a filler seam may take this many frames of pause each side
FILLERS = {"um", "umm", "uh", "uhh", "uhm", "er", "erm", "ah", "hmm", "hm", "mm", "mhm", "eh"}
KIND_NAMES = ["hold", "jump", "at-cut", "shot-drop", "edge", "credits", "sentence", "filler"]
STOPWORDS = set("""a an the and or but if so of to in on at by for with from as is are was were be been
being am i you he she it we they me him her us them my your his its our their this that these those
there here what which who whom whose when where why how not no yes yeah okay ok oh uh um hmm hey well
just do does did done have has had will would can could should shall may might must let lets go going
gonna get got come came know think see look right now then than too very really all some any one two
up down out over into about again still also only even back""".split())
# How a seam's join is healed. Picture: trim-at-cut = lands on an existing cut
# (plain cut), dissolve = 2*H-frame cross-dissolve of original frames, hard =
# mid-shot jump so small it is left as is, edge-trim = film start/end.
# Audio always gets a 10 ms crossfade. Future candidate: "patch" (see
# docs/research/patching-from-other-times.md).
STRATEGIES = ["trim-at-cut", "dissolve", "hard", "edge-trim"]


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


def runs(mask):
    idx = np.flatnonzero(np.diff(np.concatenate([[0], mask.astype(np.int8), [0]])))
    return list(zip(idx[0::2], idx[1::2]))  # [start, end) in frames


# --- 1. ANALYSIS -------------------------------------------------------------
def motion_split(g, M=12):
    """Global (camera) shift per frame via phase correlation; residual = subject motion."""
    n, H, W = g.shape
    win = (np.hanning(H)[:, None] * np.hanning(W)[None, :]).astype(np.float32)
    cam = np.zeros((n, 2), np.int16)
    subj = np.zeros(n, np.float32)
    prev = None
    for c0 in range(0, n, 512):
        G = g[c0:c0 + 512].astype(np.float32)
        Fc = np.fft.rfft2((G - G.mean(axis=(1, 2), keepdims=True)) * win)
        for k in range(len(G)):
            i = c0 + k
            Fp = Fc[k - 1] if k > 0 else prev
            if Fp is None:
                continue
            R = Fc[k] * np.conj(Fp)
            r = np.fft.irfft2(R / (np.abs(R) + 1e-6), s=(H, W))
            dy, dx = np.unravel_index(np.argmax(r), r.shape)
            dy = int(np.clip(dy - H if dy > H // 2 else dy, -M, M))
            dx = int(np.clip(dx - W if dx > W // 2 else dx, -M, M))
            cam[i] = (dy, dx)
            shifted = np.roll(g[i - 1].astype(np.int16), (dy, dx), axis=(0, 1))
            subj[i] = np.abs(g[i].astype(np.int16) - shifted)[M:H - M, M:W - M].mean()
        prev = Fc[-1]
    return cam, subj


def analyze(path, info, cache):
    if cache.exists():
        z = np.load(cache)
        F = {k: z[k] for k in z.files}
        print(f"[analysis] cached: {cache}")
    else:
        F = base_features(path, info)
        np.savez(cache, **F)
    if "subj" not in F:
        t0 = time.time()
        F["cam"], F["subj"] = motion_split(F["g"])
        F["dark"] = (F["g"] < 40).mean(axis=(1, 2)).astype(np.float32)
        np.savez(cache, **F)
        print(f"[analysis] motion split + darkness in {time.time()-t0:.0f}s")
    return F


def base_features(path, info):
    t0 = time.time()
    W = SMALL_W
    H = int(round(info["h"] * W / info["w"] / 2)) * 2
    g = read_gray(path, W, H)
    n = len(g)
    print(f"[analysis] {n} frames decoded at {W}x{H} ({time.time()-t0:.0f}s)")

    d = np.zeros(n, np.float32)
    for c0 in range(1, n, 4096):  # chunked: a full int16 copy of a feature film is ~6 GB
        c1 = min(n, c0 + 4096)
        d[c0:c1] = np.abs(g[c0:c1].astype(np.int16) - g[c0 - 1:c1 - 1]).mean(axis=(1, 2))
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
    print(f"[analysis] done in {time.time()-t0:.0f}s, {int(cut.sum())} shots")
    return dict(g=g, d=d, cut=cut, shot=shot, rms_db=rms_db.astype(np.float32),
                start_db=start_db.astype(np.float32), end_db=end_db.astype(np.float32),
                spec_start=spec_start, spec_end=spec_end, nat=nat, nat_local=nat_local)


def make_rank_d(F):
    return rank_fn(F["d"][~F["cut"].astype(bool)])


def join_strategy(p, q, F, rank_d):
    """Index into STRATEGIES for the join between kept frames p and q."""
    n = len(F["d"])
    if p < 0 or q >= n:
        return 3
    if F["shot"][p] != F["shot"][q]:
        return 0
    D = np.abs(F["g"][p].astype(np.int16) - F["g"][q]).mean()
    return 2 if float(rank_d(D)) < HARD_OK_RANK else 1


def breathing_mask(rms_db, fps):
    """Frames right after sound stops (and just before it starts) - learned from this film.

    Signal-only stand-in for speech offsets: smoothed loudness with a film-level
    threshold. Breath length = the film's median short pause, clamped 0.4-1.0 s.
    """
    n = len(rms_db)
    sm = np.convolve(rms_db, np.ones(7) / 7, mode="same")
    active = sm > np.percentile(sm, 60)
    gaps = [e - s for s, e in runs(~active) if s > 0 and e < n and e - s < 3 * fps]
    breath = int(np.clip(np.median(gaps) if gaps else fps / 2, 0.4 * fps, 1.0 * fps))
    mask = np.zeros(n, bool)
    for s, e in runs(active):
        mask[e:e + breath] = True                       # breathing room after it ends
        mask[max(0, s - breath // 2):s] = True          # a breath before it starts
    return mask, breath


def speech_layers(words_path, n, fps, srt_path=None):
    """Conversation + plot-score stand-in from local ASR word timings.

    Returns word_mask (frames inside a word), sentences [(fs, fe, importance, text)],
    sent_mask (frames inside any sentence span) and a speech-based breathing-room
    mask. Importance = rarity (idf) of the sentence's content words within this
    film's transcript, ranked 0..1 - a stand-in for an LLM plot score.
    """
    segs = json.loads(Path(words_path).read_text(encoding="utf-8"))
    sents, cur = [], []
    for s in segs:
        for w in s["words"]:
            # a long silence ends a unit too (Whisper can scatter one segment's words over music)
            if cur and w["start"] - cur[-1]["end"] > SENT_GAP_S:
                sents.append(cur)
                cur = []
            cur.append(w)
            # "..." is a trailing-off / false start inside a sentence, not a sentence end
            if w["word"].rstrip('"\')').endswith((".", "?", "!")) and not w["word"].endswith(".."):
                sents.append(cur)
                cur = []
        if cur:
            sents.append(cur)
            cur = []
    tok = lambda w: "".join(ch for ch in w["word"].lower() if ch.isalnum() or ch == "'").strip("'")
    content = [{t for t in map(tok, s) if t and t not in STOPWORDS and len(t) > 1} for s in sents]
    df = {}
    for c in content:
        for t in c:
            df[t] = df.get(t, 0) + 1
    raw = np.array([sum(np.log((1 + len(sents)) / (1 + df[t])) + 1 for t in c) for c in content])
    imp = rank_fn(raw)(raw) if len(raw) else raw
    word_mask = np.zeros(n, bool)
    filler_mask = np.zeros(n, bool)
    sent_mask = np.zeros(n, bool)
    sentences, fillers = [], []
    for s, im in zip(sents, imp):
        toks = [tok(w) for w in s]
        for i, w in enumerate(s):
            raw_w = w["word"]
            # filler: um/uh/...; "you know" set off by punctuation; stutter = first of an
            # immediately repeated token or a trailing-ellipsis false start ("Be... be")
            is_filler = toks[i] in FILLERS
            if toks[i] == "you" and i + 1 < len(s) and toks[i + 1] == "know" and (
                    (i > 0 and s[i - 1]["word"].endswith(",")) or s[i + 1]["word"].endswith((",", ".", "?", "!"))):
                is_filler = True
            if toks[i] == "know" and i > 0 and toks[i - 1] == "you" and fillers and fillers[-1][2] == s[i - 1]["word"]:
                is_filler = True
            stutter = i + 1 < len(s) and toks[i] and (toks[i] == toks[i + 1] or raw_w.endswith(("...", "-", "—")))
            f0, f1 = int(w["start"] * fps), min(n, int(np.ceil(w["end"] * fps)))
            word_mask[f0:f1] = True
            if is_filler or stutter:
                filler_mask[f0:f1] = True
                fillers.append((f0, f1 - 1, raw_w, "filler" if is_filler else "repeat"))
        fs, fe = int(s[0]["start"] * fps), min(n - 1, int(np.ceil(s[-1]["end"] * fps)) - 1)
        sent_mask[fs:fe + 1] = True
        sentences.append((fs, fe, float(im), " ".join(w["word"] for w in s)))
    cues_out = []
    # Machine captions (rolling, back-to-back cues broken mid-sentence, almost no
    # punctuation) chain into minutes-long "lines" once aligned. For those, Whisper's
    # sentences stay the units and a caption line only adds speech Whisper never heard.
    sp_fs = np.array([int(s[0]["start"] * fps) for s in sents], np.int64)
    sp_fe = np.array([int(np.ceil(s[-1]["end"] * fps)) - 1 for s in sents], np.int64)
    heard_by_asr = lambda fs, fe: bool(((sp_fs <= fe) & (sp_fe >= fs)).any())
    punct_rate = lambda texts: (sum(len(re.findall(r"[.?!,]", t)) for t in texts)
                                / max(1, sum(len(t.split()) for t in texts)))
    structured = True
    if srt_path and str(srt_path).endswith(".json") and Path(srt_path).exists():
        # Subtitles anchored to the audio by align_subs.py (decision #62): precise lines
        # ("asr"/"prompted") protect their actual word frames; coarser lines protect
        # their whole aligned span.
        al = json.loads(Path(srt_path).read_text(encoding="utf-8"))
        structured = punct_rate([L["text"] for L in al["lines"]]) >= SUB_PUNCT_MIN
        words = [w for s in sents for w in s]
        mids = np.array([(w["start"] + w["end"]) / 2 for w in words]) if words else np.zeros(0)
        units, used = [], np.zeros(len(words), bool)
        for L in al["lines"]:
            fs, fe = int(L["start"] * fps), min(n - 1, int(np.ceil(L["end"] * fps)) - 1)
            cues_out.append((fs, fe, L["text"], L["method"]))
            # Machine captions: Whisper's own sentences cover what it heard, and a line it
            # missed counts only if Whisper hears it when told what to listen for ("prompted");
            # VAD alone is too weak to back machine-guessed text.
            if not structured and (L["method"] != "prompted" or heard_by_asr(fs, fe)):
                continue
            if L["method"] in ("asr", "prompted") and L["words"]:
                for w in L["words"]:
                    word_mask[int(w["start"] * fps):min(n, int(np.ceil(w["end"] * fps)))] = True
            else:
                word_mask[fs:fe + 1] = True
            if structured:                     # (an unheard caption line overlaps no ASR sentence)
                used |= (mids >= L["start"] - 0.3) & (mids <= L["end"] + 0.3)
            units.append([fs, fe, L["text"]])
    elif srt_path and Path(srt_path).exists():
        # Subtitles are the authority on WHAT is said (decision #61): every subtitle line
        # becomes a protected unit. Heard by ASR -> its word timings set the span; unheard
        # (speech under music/effects) -> the whole cue span is protected as speech.
        words = [w for s in sents for w in s]
        mids = np.array([(w["start"] + w["end"]) / 2 for w in words]) if words else np.zeros(0)
        units, used = [], np.zeros(len(words), bool)
        cues = parse_srt(srt_path)
        structured = punct_rate([t for _, _, t in cues]) >= SUB_PUNCT_MIN
        for cs, ce, text in cues:
            hit = np.flatnonzero((mids >= cs - 0.5) & (mids <= ce + 0.5))
            if len(hit):
                fs = int(min(words[i]["start"] for i in hit) * fps)
                fe = int(np.ceil(max(words[i]["end"] for i in hit) * fps)) - 1
            else:
                fs, fe = int(cs * fps), int(np.ceil(ce * fps)) - 1
            fe = min(n - 1, fe)
            cues_out.append((fs, fe, text, "asr" if len(hit) else "cue"))
            if not structured:
                continue                       # unaligned machine captions: Whisper alone sets the speech
            if len(hit):
                used[hit] = True
            else:
                word_mask[fs:fe + 1] = True
            units.append([fs, fe, text])
    if cues_out and not structured:
        print(f"[speech] subtitles look machine-made ({punct_rate([c[2] for c in cues_out]):.2f} punctuation "
              f"per word): Whisper sets the sentences; {len(units)} lines it caught only when prompted add protection")
    if cues_out:
        k = 0
        for s in sents:  # ASR speech outside every subtitle line stays protected, as its own unit
            idx = list(range(k, k + len(s)))
            k += len(s)
            if not used[idx].any():
                units.append([int(s[0]["start"] * fps), min(n - 1, int(np.ceil(s[-1]["end"] * fps)) - 1),
                              " ".join(w["word"] for w in s)])
        units.sort()
        merged, touch = [], int(0.25 * fps)
        for u in units:  # overlapping units merge into one
            if merged and u[0] <= merged[-1][1] and u[1] > merged[-1][1] and merged[-1][1] - u[0] < touch:
                merged.append([merged[-1][1] + 1, u[1], u[2]])   # merely touching: two units
                continue
            if merged and u[0] <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], u[1])
                merged[-1][2] += " " + u[2]
            else:
                merged.append(u)
        words_of = lambda t: {x for x in re.findall(r"[a-z']+", t.lower()) if x not in STOPWORDS and len(x) > 1}
        content = [words_of(u[2]) for u in merged]
        df = {}
        for c in content:
            for t in c:
                df[t] = df.get(t, 0) + 1
        raw = np.array([sum(np.log((1 + len(merged)) / (1 + df[t])) + 1 for t in c) for c in content])
        imp = rank_fn(raw)(raw)
        sent_mask[:] = False
        sentences = []
        for (fs, fe, text), im in zip(merged, imp):
            sent_mask[fs:fe + 1] = True
            sentences.append((fs, fe, float(im), text))
    gaps = [b[0] - a[1] for a, b in zip(sentences[:-1], sentences[1:]) if 0 < b[0] - a[1] < 3 * fps]
    breath = int(np.clip(np.median(gaps) if gaps else fps / 2, 0.4 * fps, 1.0 * fps))
    bmask = np.zeros(n, bool)
    for fs, fe, _, _ in sentences:
        bmask[fe + 1:fe + 1 + breath] = True
        bmask[max(0, fs - breath // 2):fs] = True
    bmask &= ~sent_mask
    # adjacent filler words form one unit ("you know"): cut whole or not at all
    units = []
    for f0, f1, w, k in fillers:
        if units and f0 - units[-1][1] <= int(0.3 * fps):
            u0, _, uw, uk = units[-1]
            units[-1] = (u0, f1, f"{uw} {w}", uk)
        else:
            units.append((f0, f1, w, k))
    return word_mask, sentences, sent_mask, bmask, breath, filler_mask, units, cues_out


def parse_srt(path):
    """[(start_s, end_s, text)] from an SRT file; strips tags and joins lines."""
    txt = Path(path).read_text(encoding="utf-8-sig", errors="replace").replace("\r", "")
    cues = []
    for blk in txt.strip().split("\n\n"):
        ls = [x for x in blk.strip().split("\n") if x.strip()]
        m = next((re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", x) for x in ls
                  if "-->" in x), None)
        if not m:
            continue
        t = [int(x) for x in m.groups()]
        s = t[0] * 3600 + t[1] * 60 + t[2] + t[3] / 1000
        e = t[4] * 3600 + t[5] * 60 + t[6] + t[7] / 1000
        text = " ".join(x for x in ls[ls.index(next(x for x in ls if "-->" in x)) + 1:])
        cues.append((s, e, re.sub(r"<[^>]+>|\{[^}]+\}", "", text).strip()))
    return cues


def credits_mask(dark, fps, speech=None):
    """Stand-in for the plot layer: title/credit blocks at the film's very ends.

    A block is long, dark-dominant and nearly free of dialogue, and it connects to the
    first or last frame through other such blocks with gaps of at most CREDITS_CHAIN_S.
    Darkness alone is not enough: noir and night films are dark throughout.
    """
    n = len(dark)
    sm = sliding_median(dark, int(fps)) > CREDITS_DARK
    cands = [(s, e) for s, e in runs(sm)
             if e - s >= CREDITS_MIN_S * fps and (s > 0.75 * n or e < 0.1 * n)]
    quiet = lambda s, e: speech is None or speech[s:e].mean() <= CREDITS_MAX_SPEECH
    G = int(CREDITS_CHAIN_S * fps)
    mask = np.zeros(n, bool)
    edge = 0                                   # opening titles, chained from the first frame
    for s, e in cands:
        if s - edge > G or not quiet(s, e):
            break
        mask[s:e], edge = True, e
    edge = n                                   # end credits, chained back from the last frame
    for s, e in reversed(cands):
        if edge - e > G or not quiet(s, e):
            break
        mask[s:e], edge = True, s
    return mask


# --- 2. CASCADE (the liftable core) ------------------------------------------
def cascade(F, fps, stop_fraction, words_path=None, srt_path=None):
    """Greedy, lazy-re-evaluated seam removal. Returns the nested removal order."""
    g, d, shot, subj = F["g"], F["d"], F["shot"], F["subj"]
    n = len(d)
    cut = F["cut"].astype(bool)

    rank_d = make_rank_d(F)
    rank_l = rank_fn(F["rms_db"])
    cues = []
    if words_path and Path(words_path).exists():
        word_mask, sentences, sent_mask, breath, breath_len, filler_mask, fillers, cues = \
            speech_layers(words_path, n, fps, srt_path)
        src = "speech+subtitles" if cues else "speech"
        print(f"[cascade] {src}: {len(sentences)} units, speech covers {word_mask.mean():.0%} of frames, "
              f"{len(fillers)} fillers/repeats: " + ", ".join(f"{w}({k[0]})" for _, _, w, k in fillers[:12]))
        if cues:
            from collections import Counter as _C
            print(f"[cascade] subtitles: {len(cues)} lines, timing by " +
                  ", ".join(f"{m}={c}" for m, c in _C(c[3] for c in cues).most_common()))
    else:
        breath, breath_len = breathing_mask(F["rms_db"], fps)
        word_mask, sentences, sent_mask, src = np.zeros(n, bool), [], np.zeros(n, bool), "loudness"
        filler_mask, fillers = np.zeros(n, bool), []
        print("[cascade] no words.json - information protection is loudness-only")
    bpre = np.concatenate([[0.0], np.cumsum(breath)])
    wdpre = np.concatenate([[0], np.cumsum(word_mask & ~filler_mask)])   # real words only
    flpre = np.concatenate([[0], np.cumsum(filler_mask)])
    u_fs = np.array([u[0] for u in fillers], np.int64)
    u_fe = np.array([u[1] for u in fillers], np.int64)

    def filler_cost(o0, o1):
        """Filler frames in [o0,o1]: cheap only where a whole filler unit is inside."""
        cost = 0.0
        for k in range(np.searchsorted(u_fe, o0), np.searchsorted(u_fs, o1, "right")):
            ov = flpre[min(o1, u_fe[k]) + 1] - flpre[max(o0, u_fs[k])]
            cost += (FILLER_W if o0 <= u_fs[k] and u_fe[k] <= o1 else WORD_W) * ov
        return cost
    s_fs = np.array([s[0] for s in sentences], np.int64)
    s_fe = np.array([s[1] for s in sentences], np.int64)
    s_rate = np.array([PLOT_BASE + PLOT_W * s[2] for s in sentences])
    print(f"[cascade] breathing room ({src}) {breath_len} frames ({breath_len/fps:.2f}s), "
          f"{breath.mean():.0%} of frames protected")
    rank_s = rank_fn(F["nat"][1:])
    subj_rank = rank_fn(subj[~cut])(subj)
    subj_rank[cut] = 0.0
    n_shots = int(shot.max()) + 1
    shot_start = np.searchsorted(shot, np.arange(n_shots), "left")
    shot_end = np.searchsorted(shot, np.arange(n_shots), "right") - 1
    loud_rank = rank_l(F["rms_db"])
    credits = credits_mask(F["dark"], fps, (word_mask & ~filler_mask) if len(sentences) else None)
    story = np.where(credits, CREDITS_STORY_W, 1.0)
    # Information = speech (charged per sentence below) + a little loudness for
    # music/effects. Motion is NOT information - it only makes joins visible.
    content = NONSPEECH_LOUD_W * loud_rank if len(sentences) else 0.5 * loud_rank + 0.5 * subj_rank
    cpre = np.concatenate([[0.0], np.cumsum(content * story)])
    wpre = np.concatenate([[0.0], np.cumsum(story)])
    spec_start, spec_end = F["spec_start"], F["spec_end"]
    start_db, end_db, nat_local = F["start_db"], F["end_db"], F["nat_local"]
    if credits.any():
        cr = runs(credits)
        print("[cascade] title/credit blocks: " + ", ".join(
            f"{s/fps//60:.0f}:{s/fps%60:04.1f}-{e/fps//60:.0f}:{e/fps%60:04.1f}" for s, e in cr))

    removed = np.zeros(n, bool)
    prev_k = np.arange(-1, n - 1)
    next_k = np.arange(1, n + 1)
    shot_kept = (shot_end - shot_start + 1).astype(np.int64)
    SW = int(SPREAD_WIN_S * fps)

    def join_cost(p, q):
        if p < 0 or q >= n:
            return 0.0, 0.0
        if shot[p] != shot[q]:
            vj = AT_CUT_COST
        else:
            # Absolute forward energy, steeply penalised when visible; a
            # same-camera cut is jarring in itself, more so with moving subjects.
            D = np.abs(g[p].astype(np.int16) - g[q]).mean()
            r = float(rank_d(D))
            moving = max(subj_rank[max(p - 2, 0):p + 1].max(), subj_rank[q:q + 3].max())
            vj = (SAME_SHOT_BASE + r * r + SUBJECT_W * float(moving)
                  + VISIBLE_JUMP_PENALTY * max(0.0, r - 0.85) / 0.15)
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

    def speech_cost(a, b):
        """Whole sentences cost their plot score; cutting INTO one costs per word frame."""
        cost, whole = 0.0, 0
        for k in range(np.searchsorted(s_fe, a), np.searchsorted(s_fs, b, "right")):
            fs, fe = s_fs[k], s_fe[k]
            o0, o1 = max(a, fs), min(b, fe)
            if o0 > o1:
                continue
            if a <= fs and fe <= b:
                cost += (fe - fs + 1) * s_rate[k]
                whole += 1
            else:
                wf = wdpre[o1 + 1] - wdpre[o0]
                ff = flpre[o1 + 1] - flpre[o0]
                cost += WORD_W * wf + filler_cost(o0, o1) + MIDSENT_W * ((o1 - o0 + 1) - wf - ff)
        return cost, whole

    def evaluate(a, b):
        L = b - a + 1
        p, q = int(prev_k[a]), int(next_k[b])
        vj, aj = join_cost(p, q)
        w_seam = (wpre[b + 1] - wpre[a]) / L
        w_join = max(story[p] if p >= 0 else 1.0, story[q] if q < n else 1.0)
        sp, whole = speech_cost(a, b)
        C = ((cpre[b + 1] - cpre[a]) + w_seam * (sp + BREATH_W * (bpre[b + 1] - bpre[a]))) / L
        x0, x1 = max(0, a - SW), min(n, b + 1 + SW)
        S = LAMBDA_SPREAD * w_seam * (removed[x0:x1].sum() + L) / (x1 - x0)
        Fp = FRAGMENT_PENALTY * fragments(a, b, p, q)
        # growing an existing hole moves a join instead of adding one
        grows = (a > 0 and removed[a - 1]) or (b + 1 < n and removed[b + 1])
        join = ((0.0 if grows else JOIN_BASE) + vj + aj + Fp) * w_join
        return join / L ** JOIN_AMORT + C + S, (p, q, vj, aj, C, S, Fp, w_seam, whole)

    heap = []

    def push(a, b):
        if a < 0 or b >= n or removed[a:b + 1].any():
            return
        sc, _ = evaluate(a, b)
        heapq.heappush(heap, (sc, a, b))

    # whole-sentence seams, padded halfway into the pauses on each side (max 1 s)
    pad_lo, pad_hi = [], []
    for k in range(len(sentences)):
        prev_end = s_fe[k - 1] if k > 0 else -1
        next_start = s_fs[k + 1] if k + 1 < len(sentences) else n
        pad_lo.append(max(prev_end + 1, s_fs[k] - min(int(fps), (s_fs[k] - prev_end) // 2)))
        pad_hi.append(min(next_start - 1, s_fe[k] + min(int(fps), (next_start - s_fe[k]) // 2)))

    def push_sentence(k):
        """Push sentence k with whatever of its padding is still kept."""
        fs, fe = int(s_fs[k]), int(s_fe[k])
        if removed[fs:fe + 1].any():
            return
        lo, hi = fs, fe
        while lo - 1 >= pad_lo[k] and not removed[lo - 1]:
            lo -= 1
        while hi + 1 <= pad_hi[k] and not removed[hi + 1]:
            hi += 1
        push(lo, hi)

    t0 = time.time()
    for w in SEAM_SIZES:
        for a in range(0, n - w + 1, max(1, w // 2)):
            push(a, a + w - 1)
    for s, e in zip(shot_start, shot_end):
        if e - s + 1 <= MAX_SHOT_SEAM_S * fps and e - s + 1 > SEAM_SIZES[-1]:
            push(int(s), int(e))
    for k in range(len(sentences)):
        push_sentence(k)
    for f0, f1, _, _ in fillers:  # the filler itself plus a little of the pause around it
        lo, hi = f0, f1
        while lo - 1 >= 0 and not word_mask[lo - 1] and f0 - lo < FILLER_PAD:
            lo -= 1
        while hi + 1 < n and not word_mask[hi + 1] and hi - f1 < FILLER_PAD:
            hi += 1
        push(lo, hi)
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
        p, q, vj, aj, C, S, Fp, w_seam, whole = parts
        shots_hit = range(shot[a], shot[b] + 1)
        drop = any(shot_kept[s] - (min(b, shot_end[s]) - max(a, shot_start[s]) + 1) == 0
                   for s in shots_hit)
        if w_seam < 0.5:
            kind = 5
        elif whole:
            kind = 6
        elif flpre[b + 1] > flpre[a] and wdpre[b + 1] == wdpre[a]:
            kind = 7
        elif p < 0 or q >= n:
            kind = 4
        elif drop:
            kind = 3
        elif shot[p] != shot[q]:
            kind = 2
        else:
            kind = 0 if subj_rank[a:b + 1].mean() < 0.35 else 1
        for s in shots_hit:
            shot_kept[s] -= min(b, shot_end[s]) - max(a, shot_start[s]) + 1
        removed[a:b + 1] = True
        if p >= 0:
            next_k[p] = q
        if q < n:
            prev_k[q] = p
        kept -= b - a + 1
        order.append([a, b, kind, round(new, 4), round(vj, 3), round(aj, 3),
                      round(C, 3), round(S, 3), round(Fp, 1), join_strategy(p, q, F, rank_d)])
        for w in SEAM_SIZES:
            if p >= 0:
                push(p - w + 1, p)
            if q < n:
                push(q, q + w - 1)
        if len(sentences):  # neighbouring sentences may have lost some padding
            for k in range(max(0, np.searchsorted(s_fe, a) - 1),
                           min(len(sentences), np.searchsorted(s_fs, b, "right") + 1)):
                push_sentence(k)
    print(f"[cascade] {len(order)} seams removed down to {kept/n:.0%} ({time.time()-t0:.0f}s)")
    return order, dict(subj_rank=subj_rank, loud_rank=loud_rank, credits=credits,
                       breath=breath, shot_start=shot_start, shot_end=shot_end,
                       word_mask=word_mask & ~filler_mask, sentences=sentences, fillers=fillers, cues=cues)


def speed_for(target, slope=SPEED_SLOPE):
    """The second device (decision #66): one film-wide speed-up that rises as the target
    length drops. Pitch is kept, every carved frame is shown, and lip-sync stays exact."""
    return 1.0 + (1.0 - target) * slope


def carve_for(target, slope=SPEED_SLOPE):
    """What carving keeps so that carving plus speed-up land exactly on the target.
    It rises with the target (for slope <= 1), so the nested removal order still holds."""
    return min(1.0, target * speed_for(target, slope))


def keep_mask(order, n, fraction):
    target = n - round(fraction * n)
    removed, cum = np.zeros(n, bool), 0
    for a, b, *_ in order:
        if cum >= target:
            break
        removed[a:b + 1] = True
        cum += b - a + 1
    return ~removed


def picture_plan(keep, F, rank_d, h=DISSOLVE_H):
    """Output frame list + per-join strategy counts; 'dissolve' joins become a 2h-frame
    heal window of original frames (handles keep length exact). A window frame is the tuple
    (A, B, alpha, p, q, t): the co-timed pair the plain dissolve blends, plus the join, so
    render() can hand the whole window to a heal from heals.py (decision #68)."""
    n = len(keep)
    rs = runs(keep)
    out, run_pos = [], []
    for s, e in rs:
        run_pos.append(len(out))
        out.extend(range(s, e))
    used = np.zeros(len(out), bool)
    dissolves = 0
    counts = Counter()
    for k in range(len(rs) - 1):
        (s0, e0), (s1, e1) = rs[k], rs[k + 1]
        p, q = e0 - 1, s1
        strat = join_strategy(p, q, F, rank_d)
        if strat == 1 and (e0 - s0 < h or e1 - s1 < h or p + h >= n or q - h < 0 or p - h < 0 or q + h >= n):
            strat = 2  # no room for handles: falls back to a hard join
        counts[STRATEGIES[strat]] += 1
        if strat != 1:
            continue
        j0 = run_pos[k + 1] - h
        if used[j0:j0 + 2 * h].any():
            counts["dissolve"] -= 1
            counts["hard"] += 1
            continue
        for j in range(2 * h):
            out[j0 + j] = (p - h + 1 + j, q - h + j, (j + 0.5) / (2 * h), p, q, j)
        used[j0:j0 + 2 * h] = True
        dissolves += 1
    return out, counts


# --- 3. REPORT ---------------------------------------------------------------
def report(order, F, aux, fps, fractions, path, slope=SPEED_SLOPE):
    n = len(F["d"])
    shot_len = aux["shot_end"] - aux["shot_start"] + 1
    lines = [f"frames={n} fps={fps} duration={n/fps/60:.2f} min shots={len(shot_len)} "
             f"ASL={np.mean(shot_len)/fps:.2f}s credits={aux['credits'].sum()/fps:.1f}s", ""]
    g, shot = F["g"], F["shot"]
    rank_d = make_rank_d(F)
    for fr in fractions:
        sp, kf = speed_for(fr, slope), carve_for(fr, slope)
        keep = keep_mask(order, n, kf)
        removed_idx = set(np.flatnonzero(~keep))
        active = [o for o in order if o[0] in removed_idx]
        kinds = {k: 0 for k in KIND_NAMES}
        for o in active:
            kinds[KIND_NAMES[o[2]]] += 1
        rs = runs(keep)
        joins = [(e0 - 1, s1) for (s0, e0), (s1, e1) in zip(rs[:-1], rs[1:])]
        same = [(p, q) for p, q in joins if shot[p] == shot[q]]
        D = [np.abs(g[p].astype(np.int16) - g[q]).mean() for p, q in same]
        _, strat_counts = picture_plan(keep, F, rank_d)
        story_kept = keep[~aux["credits"]].mean()
        kept_per_shot = np.array([keep[s:e + 1].sum() for s, e in zip(aux["shot_start"], aux["shot_end"])])
        alive = kept_per_shot[kept_per_shot > 0]
        a, b = np.log(shot_len), np.log(alive)
        grid = np.sort(np.concatenate([a, b]))
        ks = np.max(np.abs(np.searchsorted(np.sort(a), grid, "right") / len(a)
                           - np.searchsorted(np.sort(b), grid, "right") / len(b)))
        w = int(10 * fps)
        story_only = ~aux["credits"]
        local = sliding_window_view((~keep[story_only]).astype(np.float32), w).mean(1)
        wm, sents = aux["word_mask"], aux["sentences"]
        whole_kept = sum(keep[fs:fe + 1].all() for fs, fe, _, _ in sents)
        whole_gone = sum((~keep[fs:fe + 1]).all() for fs, fe, _, _ in sents)
        clipped = [t for fs, fe, _, t in sents if 0 < keep[fs:fe + 1].sum() < fe - fs + 1
                   and (~keep[fs:fe + 1] & wm[fs:fe + 1]).any()]
        fl = aux.get("fillers", [])
        fl_gone = [w for f0, f1, w, _ in fl if not keep[f0:f1 + 1].any()]
        info_line = (f"   information: real-word frames kept {keep[wm].mean() if wm.any() else 1:.0%}; sentences "
                     f"{whole_kept} intact / {len(clipped)} with real words cut / {whole_gone} removed whole; "
                     f"fillers/repeats removed {len(fl_gone)}/{len(fl)}" + (f" ({', '.join(fl_gone[:8])})" if fl_gone else ""))
        if aux.get("cues"):
            cl = [(keep[a:b + 1].mean(), t) for a, b, t, _ in aux["cues"]]
            lost = [t for k, t in cl if k < 0.2]
            info_line += (f"\n   subtitle lines: {sum(k >= 0.95 for k, _ in cl)} intact / "
                          f"{sum(0.2 <= k < 0.95 for k, _ in cl)} partly cut / {len(lost)} lost"
                          + (f" ({' | '.join(lost[:6])})" if lost else ""))
        out_min = keep.sum() / fps / sp / 60
        lines += [f"== keep {fr:.0%}: {out_min:.2f} min = carve to {kf:.1%} at {sp:.4f}x speed, "
                  f"{len(active)} seams, {len(joins)} joins "
                  f"({len(joins)/out_min:.1f}/min); story kept {story_kept:.0%}, "
                  f"credits kept {keep[aux['credits']].mean() if aux['credits'].any() else 0:.0%}",
                  info_line,
                  "   kinds: " + ", ".join(f"{k}={v}" for k, v in kinds.items()),
                  "   join strategies: " + ", ".join(f"{s}={strat_counts.get(s, 0)}" for s in STRATEGIES)
                  + f"; story breathing room eaten: "
                  f"{(~keep & aux['breath'] & story_only).sum() / max((aux['breath'] & story_only).sum(), 1):.0%}",
                  f"   same-shot joins {len(same)}, visible D>25: "
                  f"{sum(x > 25 for x in D)}, max D {max(D) if D else 0:.1f}",
                  f"   shots kept {len(alive)}/{len(shot_len)}, ASL {np.mean(shot_len)/fps:.2f}s -> "
                  f"{np.mean(alive)/fps:.2f}s, KS(log shot len)={ks:.3f}",
                  f"   local story removal (10s windows): max {local.max():.0%}, std {local.std():.3f}", ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


# --- 4. RENDER ---------------------------------------------------------------
def render(src, info, order, F, fractions, outdir, stem, render_height=None, slope=SPEED_SLOPE, heal=None):
    import heals as healmod
    n, rank_d = len(F["d"]), make_rank_d(F)
    heal_name = healmod.pick(heal)
    heal_fn = None if heal_name == "dissolve" else healmod.HEALS[heal_name]
    dh = DISSOLVE_H
    print(f"[render] same-shot joins healed by: {heal_name}" + (f" (asked for {heal})" if heal and heal != heal_name else ""))
    fps, W, H = info["fps"], info["w"], info["h"]
    W0, H0 = W, H
    if render_height and render_height < H:
        W, H = int(round(W * render_height / H)), render_height
    W, H = W // 2 * 2, H // 2 * 2  # yuv420p / libx264 need even sizes (e.g. 853x480, 720x405)
    vf = ["-vf", f"scale={W}:{H}"] if (W, H) != (W0, H0) else []
    sr = 48000
    fsamp = lambda f: int(round(f * sr / fps))  # noqa: E731  exact per frame (29.97/23.976 fps safe)
    audio = read_audio(src, sr, 2)
    h = int(sr * XFADE_MS / 2000)
    ramp = np.linspace(0, np.pi / 2, 2 * h, dtype=np.float32)[:, None]
    fo, fi = np.cos(ramp), np.sin(ramp)
    plans, encs = {}, {}
    for fr in fractions:
        sp = speed_for(fr, slope)
        keep = keep_mask(order, n, carve_for(fr, slope))
        plans[fr], counts = picture_plan(keep, F, rank_d)
        pieces, joins, pos = [], [], 0
        for s, e in runs(keep):
            seg = audio[fsamp(s):fsamp(e)]
            pieces.append(seg)
            pos += len(seg)
            joins.append((pos, fsamp(s), fsamp(e)))
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
        # Speed-up (decision #66): every carved frame is shown, just at fps*speed, and the
        # audio is time-stretched with its pitch kept (rubberband: exact length, ~2 ms offset).
        af = ["-af", f"rubberband=tempo={sp:.6f}:pitch=1"] if sp != 1 else []
        encs[fr] = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p",
             "-s", f"{W}x{H}", "-r", repr(fps * sp), "-i", "-", "-i", str(wav), *af,
             "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-shortest", str(mp4)],
            stdin=subprocess.PIPE)
        print(f"[render] target {fr:.0%}: carve to {keep.mean():.1%} at {sp:.4f}x; joins "
              + ", ".join(f"{k}={v}" for k, v in counts.items()))
    need = Counter()
    for plan in plans.values():
        for it in plan:
            if isinstance(it, tuple):
                need[it[0]] += 1
                need[it[1]] += 1
                if heal_fn and it[5] == 0:          # a heal also sees the untouched end frames
                    need[it[3] - dh] += 1
                    need[it[4] + dh] += 1
    cache, ptr = {}, {fr: 0 for fr in fractions}
    fb = W * H * 3 // 2
    if heal_fn:
        import cv2
        to_rgb = lambda f: cv2.cvtColor(cache[f].reshape(H * 3 // 2, W), cv2.COLOR_YUV2RGB_I420).astype(np.float32)
        to_yuv = lambda im: cv2.cvtColor(np.clip(im + 0.5, 0, 255).astype(np.uint8), cv2.COLOR_RGB2YUV_I420).tobytes()
    healed, heal_s, heal_n = {fr: {} for fr in fractions}, 0.0, 0

    def heal_window(p, q):
        a = [to_rgb(p - dh + 1 + t) for t in range(2 * dh)]
        b = [to_rgb(q - dh + t) for t in range(2 * dh)]
        frames, _ = heal_fn(a, b, to_rgb(p - dh), to_rgb(q + dh))
        for x in (p - dh, q + dh):
            need[x] -= 1
            if need[x] == 0:
                cache.pop(x, None)
        return [to_yuv(f) for f in frames]
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), *vf, "-f", "rawvideo",
                            "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE)
    t0 = time.time()
    for i in range(n):
        buf = dec.stdout.read(fb)
        if len(buf) < fb:
            break
        if need[i]:
            cache[i] = np.frombuffer(buf, np.uint8)
        for fr, enc in encs.items():
            plan, pt = plans[fr], ptr[fr]
            while pt < len(plan):
                it = plan[pt]
                if isinstance(it, tuple):
                    A, B, al, jp, jq, t = it
                    if heal_fn:
                        win = healed[fr]
                        if (jp, jq) not in win:
                            if jq + dh > i:              # the whole window must be decoded
                                break
                            t1 = time.time()
                            win[(jp, jq)] = heal_window(jp, jq)
                            heal_s, heal_n = heal_s + time.time() - t1, heal_n + 1
                        enc.stdin.write(win[(jp, jq)][t])
                        if t == 2 * dh - 1:
                            del win[(jp, jq)]
                    else:
                        if max(A, B) > i:
                            break
                        mix = cache[A].astype(np.float32) * (1 - al) + cache[B].astype(np.float32) * al
                        enc.stdin.write((mix + 0.5).astype(np.uint8).tobytes())
                    for x in (A, B):
                        need[x] -= 1
                        if need[x] == 0:
                            cache.pop(x, None)
                else:
                    if it > i:
                        break
                    enc.stdin.write(buf)
                pt += 1
            ptr[fr] = pt
        if i % 2000 == 0:
            print(f"[render] frame {i}/{n} ({time.time()-t0:.0f}s)")
    for enc in encs.values():
        enc.stdin.close()
        enc.wait()
    dec.wait()
    for fr in fractions:
        (outdir / f"{stem}_{int(fr*100):03d}.wav").unlink()
    if heal_n:
        print(f"[render] {heal_name}: {heal_n} joins in {heal_s:.0f}s ({heal_s / heal_n:.2f}s per join)")
    print(f"[render] done ({time.time()-t0:.0f}s)")


# --- 5. VIEWER ---------------------------------------------------------------
def viewer(order, F, aux, info, fractions, outdir, stem, slope=SPEED_SLOPE):
    proxy = outdir / "proxy.mp4"
    if not proxy.exists():
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(info["src"]), "-vf", "scale=640:-2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "27", "-g", "12",
            "-keyint_min", "12", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
            str(proxy)])
    data = {
        "stem": stem, "fps": info["fps"], "n": len(F["d"]),
        "motion": (aux["subj_rank"] * 99).astype(int).tolist(),
        "loud": (aux["loud_rank"] * 99).astype(int).tolist(),
        "cuts": np.flatnonzero(F["cut"]).tolist(),
        "credits": [[int(s), int(e)] for s, e in runs(aux["credits"])],
        "order": order, "kinds": KIND_NAMES, "strategies": STRATEGIES,
        "breath": [[int(s), int(e)] for s, e in runs(aux["breath"])],
        "renders": [f"{stem}_{int(fr*100):03d}.mp4" for fr in fractions],
        "fractions": fractions, "speed_slope": slope,
    }
    tpl = (Path(__file__).parent / "viewer_template.html").read_text(encoding="utf-8")
    (outdir / "viewer.html").write_text(tpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":"))),
                                        encoding="utf-8")
    print(f"[viewer] {outdir / 'viewer.html'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--fractions", type=float, nargs="+", default=DEFAULT_FRACTIONS)
    ap.add_argument("--stop", type=float, default=0.2)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--subs", help="subtitle file (SRT) - authoritative dialogue for the plot layer")
    ap.add_argument("--render-height", type=int, help="downscale renders to this height (e.g. 720)")
    ap.add_argument("--speed-slope", type=float, default=SPEED_SLOPE,
                    help="film-wide speed = 1 + (1 - target) * slope (default 0.125: 1.1x at 20%%; 0 = carve only)")
    ap.add_argument("--heal", help="heal for same-shot joins (heals.py); default: rifemorph, falling back to "
                                   "flowdissolve without PyTorch/GPU weights, then the plain dissolve")
    args = ap.parse_args()
    src = Path(args.src)
    stem = src.stem
    outdir = Path("renders") / stem
    outdir.mkdir(parents=True, exist_ok=True)
    info = probe(src)
    info["src"] = src
    F = analyze(src, info, outdir / "features.npz")
    subs = args.subs
    aligned = outdir / "subs_aligned.json"
    if subs and aligned.exists() and \
            Path(json.loads(aligned.read_text(encoding="utf-8")).get("source_srt", "")).resolve() == Path(subs).resolve():
        print(f"[main] using subtitles anchored to the audio: {aligned}")
        subs = aligned
    order, aux = cascade(F, info["fps"], args.stop, outdir / "words.json", subs)
    (outdir / "order.json").write_text(json.dumps(order), encoding="utf-8")
    report(order, F, aux, info["fps"], args.fractions, outdir / "report.txt", args.speed_slope)
    viewer(order, F, aux, info, args.fractions, outdir, stem, args.speed_slope)
    if not args.no_render:
        render(src, info, order, F, args.fractions, outdir, stem, args.render_height, args.speed_slope, args.heal)


if __name__ == "__main__":
    main()
