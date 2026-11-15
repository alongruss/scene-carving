"""PROTOTYPE - throwaway. Shot-level analysis for decisions #70-#76 (2001 review, 2026-11-14).

  * global motion per frame: DIS optical flow at analysis size, fitted with a similarity
    model (pan/tilt = tx, ty; zoom/dolly = s; roll = r); the residual is subject motion
  * shot kinds: camera move, moving subject, long static take (edge-only), else other
  * per-frame trim signals: movement carried, new picture content, event moments
  * native jump cuts (the film's own same-setup cuts) -> the jump-cut budget
  * look-alike neighbours: adjacent silent shots that show the same thing

Everything is either a physical measure at the analysis size (px per frame at 160 px
wide) or ranked within this film. Cached in renders/<stem>/shots.npz.
"""
import time

import cv2
import numpy as np

CAM_MOVE_PX = 0.25       # px/frame at 160 px wide: the camera is moving (pan, tilt, zoom, dolly)
SUBJ_MOVE_PX = 0.35      # mean residual px/frame on moving points: a subject is moving
SUBJ_AREA_MAX = 0.6      # residual motion on less than this share of the frame = one subject
KIND_SHARE = 0.5         # a shot is of a kind when this share of its frames shows it
KINDS = ["other", "camera move", "moving subject", "static"]   # edge-only: 1, 2, and 3 when long
LAYOUT = (40, 18)        # small layout for "same picture" comparisons


def _layouts(g):
    out = np.empty((len(g), LAYOUT[1], LAYOUT[0]), np.float32)
    for i, f in enumerate(g):
        out[i] = cv2.resize(f, LAYOUT, interpolation=cv2.INTER_AREA)
    return out


def global_motion(g, cut, step=4):
    """Per frame: similarity motion (tx, ty, s, r) of frame i-1 -> i, and residual stats."""
    n, H, W = g.shape
    ys, xs = np.mgrid[step // 2:H:step, step // 2:W:step]
    xc = (xs - W / 2).ravel().astype(np.float32)
    yc = (ys - H / 2).ravel().astype(np.float32)
    m = len(xc)
    A = np.zeros((2 * m, 4), np.float32)
    A[0::2, 0], A[0::2, 2], A[0::2, 3] = 1, xc, -yc
    A[1::2, 1], A[1::2, 2], A[1::2, 3] = 1, yc, xc
    border = ((xs < 12) | (xs >= W - 12) | (ys < 6) | (ys >= H - 6)).ravel()
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
    mot = np.zeros((n, 4), np.float32)
    subj = np.zeros(n, np.float32)      # mean residual on moving points
    area = np.zeros(n, np.float32)      # share of points with residual motion
    bord = np.zeros(n, np.float32)      # residual motion at the frame border (enter/leave)
    cen = np.zeros((n, 2), np.float32)  # centroid of residual motion (x, y in 0..1)
    t0 = time.time()
    for i in range(1, n):
        if cut[i]:
            continue
        f = dis.calc(g[i - 1], g[i], None)[step // 2::step, step // 2::step].reshape(-1)
        sol = np.linalg.lstsq(A, f, rcond=None)[0]
        res = f - A @ sol
        rmag = np.hypot(res[0::2], res[1::2])
        inl = rmag <= max(0.3, np.percentile(rmag, 60))      # refit on the majority (background)
        sol = np.linalg.lstsq(A[np.repeat(inl, 2)], f[np.repeat(inl, 2)], rcond=None)[0]
        res = f - A @ sol
        rmag = np.hypot(res[0::2], res[1::2])
        mov = rmag > 0.5
        mot[i] = sol
        area[i] = mov.mean()
        if mov.any():
            subj[i] = rmag[mov].mean()
            wgt = rmag * mov
            cen[i] = (float((xc * wgt).sum() / wgt.sum() / W + 0.5), float((yc * wgt).sum() / wgt.sum() / H + 0.5))
        bord[i] = rmag[border].mean()
        if i % 20000 == 0:
            print(f"[shots] motion {i}/{n} ({time.time()-t0:.0f}s)", flush=True)
    return mot, subj, area, bord, cen


def camera_speed(mot, W=160):
    """px/frame at the frame edge: pan/tilt plus zoom/dolly plus roll."""
    return np.hypot(mot[:, 0], mot[:, 1]) + (np.abs(mot[:, 2]) + np.abs(mot[:, 3])) * W / 2


def _within_shot_windows(x, shot_start, shot_end, half):
    """Mean of x over [i-half, i) and [i, i+half), clipped to the shot: (before, after)."""
    n = len(x)
    c = np.concatenate([np.zeros((1,) + x.shape[1:]), np.cumsum(x, axis=0)])
    idx = np.arange(n)
    sid = np.zeros(n, np.int64)
    for k, (s, e) in enumerate(zip(shot_start, shot_end)):
        sid[s:e + 1] = k
    lo = np.maximum(idx - half, shot_start[sid])
    hi = np.minimum(idx + half, shot_end[sid] + 1)
    before = (c[idx] - c[lo]) / np.maximum(idx - lo, 1)[:, None]
    after = (c[hi] - c[idx]) / np.maximum(hi - idx, 1)[:, None]
    return before, after


def analyze_shots(g, cut, shot, fps, cache):
    if cache.exists():
        z = np.load(cache)
        print(f"[shots] cached: {cache}")
        return {k: z[k] for k in z.files}
    t0 = time.time()
    n = len(g)
    lay = _layouts(g)
    mcache = cache.with_name(cache.stem + "_motion.npz")
    if mcache.exists():
        z = np.load(mcache)
        mot, subj, area, bord, cen = (z[k] for k in ("mot", "subj", "area", "bord", "cen"))
    else:
        mot, subj, area, bord, cen = global_motion(g, cut)
        np.savez(mcache, mot=mot, subj=subj, area=area, bord=bord, cen=cen)
    print(f"[shots] motion done ({time.time()-t0:.0f}s)", flush=True)
    n_shots = int(shot.max()) + 1
    s0 = np.searchsorted(shot, np.arange(n_shots), "left")
    s1 = np.searchsorted(shot, np.arange(n_shots), "right") - 1
    cam = camera_speed(mot)
    # new picture content: distance to the nearest frame of the same shot >= 1 s away
    uniq = np.zeros(n, np.float32)
    gap = int(round(fps))
    for a, b in zip(s0, s1):
        L = b - a + 1
        if L <= gap:
            continue
        X = lay[a:b + 1].reshape(L, -1).astype(np.float64)
        ref_idx = np.arange(0, L, 2)
        R = X[ref_idx]
        rr = (R ** 2).sum(1)
        for c0 in range(0, L, 1024):
            Q = X[c0:c0 + 1024]
            d2 = (Q ** 2).sum(1)[:, None] + rr[None, :] - 2 * Q @ R.T     # squared L2 via a matmul
            far = np.abs((c0 + np.arange(len(Q)))[:, None] - ref_idx[None, :]) >= gap
            d2[~far] = np.inf
            uniq[a + c0:a + c0 + len(Q)] = np.sqrt(np.maximum(d2.min(1), 0) / X.shape[1])
    uniq[~np.isfinite(uniq)] = 0
    # event moments: the motion pattern changes (starts, stops, turns, enters or leaves)
    feat = np.stack([mot[:, 0], mot[:, 1], mot[:, 2] * 80, mot[:, 3] * 80,
                     subj * (area > 0.01), area * 10, bord, cen[:, 0] * 10 * (area > 0.01)], 1).astype(np.float64)
    before, after = _within_shot_windows(feat, s0, s1, max(2, int(0.5 * fps)))
    event = np.abs(after - before).sum(1).astype(np.float32)
    # native jump cuts: a cut whose two sides show the same setup
    lay_d1 = np.abs(lay[gap:] - lay[:-gap]).mean(axis=(1, 2))
    same_shot = shot[gap:] == shot[:-gap]
    within = lay_d1[same_shot]
    cut_idx = np.flatnonzero(cut)[1:]
    cut_d = np.abs(lay[cut_idx] - lay[cut_idx - 1]).mean(axis=(1, 2))
    # shot descriptors for look-alikes: mean layout + 32-bin histogram
    hist = np.zeros((n_shots, 32), np.float32)
    mlay = np.zeros((n_shots,) + lay.shape[1:], np.float32)
    half_d = np.full(n_shots, np.nan, np.float32)
    for k, (a, b) in enumerate(zip(s0, s1)):
        mlay[k] = lay[a:b + 1].mean(0)
        hist[k] = np.bincount((g[a:b + 1:3] >> 3).ravel(), minlength=32)[:32]
        hist[k] /= max(hist[k].sum(), 1)
        if b - a + 1 >= 2 * fps:
            m_ = (a + b) // 2
            h1 = np.bincount((g[a:m_:3] >> 3).ravel(), minlength=32)[:32].astype(np.float32)
            h2 = np.bincount((g[m_:b + 1:3] >> 3).ravel(), minlength=32)[:32].astype(np.float32)
            half_d[k] = _desc_dist(lay[a:m_].mean(0), lay[m_:b + 1].mean(0), h1 / h1.sum(), h2 / h2.sum())
    out = dict(mot=mot, subj=subj, area=area, bord=bord, cen=cen, cam=cam.astype(np.float32),
               uniq=uniq, event=event, within_d1=within.astype(np.float32), cut_idx=cut_idx,
               cut_d=cut_d.astype(np.float32), hist=hist, mlay=mlay, half_d=half_d)
    np.savez(cache, **out)
    print(f"[shots] analysis done in {time.time()-t0:.0f}s", flush=True)
    return out


def _desc_dist(l1, l2, h1, h2):
    return 0.5 * float(np.abs(l1 - l2).mean()) / 64.0 + 0.5 * float(np.abs(h1 - h2).sum())


def shot_kinds(S, s0, s1, fps, story):
    """Motion kind per shot (index into KINDS) and whether it is edge-only: camera moves,
    one moving subject, and static takes at least as long as the film's median shot."""
    n_shots = len(s0)
    lens = s1 - s0 + 1
    in_story = np.array([story[a:b + 1].mean() > 0.5 for a, b in zip(s0, s1)])
    med_len = np.median(lens[in_story]) if in_story.any() else np.median(lens)
    kind = np.zeros(n_shots, np.int8)
    for k, (a, b) in enumerate(zip(s0, s1)):
        if not in_story[k] or b - a < 2:
            continue
        fr = slice(a + 1, b + 1)
        cam = (S["cam"][fr] > CAM_MOVE_PX).mean()
        sub = ((S["subj"][fr] > SUBJ_MOVE_PX) & (S["area"][fr] < SUBJ_AREA_MAX) & (S["area"][fr] > 0.005)).mean()
        still = ((S["cam"][fr] <= CAM_MOVE_PX) & (S["subj"][fr] * S["area"][fr] < 0.05)).mean()
        if cam >= KIND_SHARE:
            kind[k] = 1
        elif sub >= KIND_SHARE:
            kind[k] = 2
        elif still >= KIND_SHARE:
            kind[k] = 3
    edge_only = (kind == 1) | (kind == 2) | ((kind == 3) & (lens >= med_len))
    return kind, edge_only, in_story


def trim_signals(S, s0, s1, kind, edge_only, in_story, fps):
    """Per-frame trim cost signals in 0..1 (decision #72): movement carried (relative to the
    shot), new picture content and event moments (ranked within the film, events held +-1 s)."""
    n = len(S["cam"])
    m = S["cam"] + S["subj"] * S["area"]
    move = np.zeros(n, np.float32)
    new = np.zeros(n, np.float32)
    ev = np.zeros(n, np.float32)
    frames = np.concatenate([np.arange(a, b + 1) for k, (a, b) in enumerate(zip(s0, s1)) if in_story[k]] or [np.zeros(0, int)])
    r_new = _rank(S["uniq"][frames])
    r_ev = _rank(S["event"][frames])
    hold = max(1, int(fps))
    for k, (a, b) in enumerate(zip(s0, s1)):
        if not edge_only[k]:
            continue
        seg = m[a:b + 1]
        move[a:b + 1] = np.minimum(seg / (seg.mean() + 0.05), 3.0) / 3.0
        new[a:b + 1] = r_new(S["uniq"][a:b + 1])
        e = r_ev(S["event"][a:b + 1])
        # hold each event for +-1 s inside the shot (running max)
        pad = np.pad(e, hold, mode="edge")
        ev[a:b + 1] = np.lib.stride_tricks.sliding_window_view(pad, 2 * hold + 1).max(1)
    return move, new, ev


def native_jump_rate(S, story, fps):
    """The film's own jump cuts per story minute: cuts whose two sides look like one setup
    (no further apart than frames 1 s apart inside a shot usually are)."""
    thr = np.percentile(S["within_d1"], 50)
    ci = S["cut_idx"]
    in_story = story[ci]
    jumps = ci[(S["cut_d"] <= thr) & in_story]
    return len(jumps) / max(story.sum() / fps / 60, 1e-6), jumps, thr


def lookalikes(S, s0, s1, kind, story, has_speech, fps):
    """Groups of adjacent silent story shots showing the same thing, and the one to keep.

    Same thing = their descriptors differ no more than the two halves of a typical shot.
    Most informative = an event happens + a new view + the most complete action."""
    n_shots = len(s0)
    ok = np.array([story[a:b + 1].mean() > 0.5 and not has_speech[k] and b - a + 1 >= fps
                   for k, (a, b) in enumerate(zip(s0, s1))])
    hd = S["half_d"][np.isfinite(S["half_d"])]
    thr = float(np.percentile(hd, 75)) if len(hd) else 0.0
    pair = np.zeros(max(n_shots - 1, 0), bool)
    dist = np.full(max(n_shots - 1, 0), np.inf)
    for k in range(n_shots - 1):
        if ok[k] and ok[k + 1]:
            dist[k] = _desc_dist(S["mlay"][k], S["mlay"][k + 1], S["hist"][k], S["hist"][k + 1])
            pair[k] = dist[k] <= thr
    groups, k = [], 0
    while k < n_shots - 1:
        if pair[k]:
            j = k
            while j < n_shots - 1 and pair[j]:
                j += 1
            groups.append(list(range(k, j + 1)))
            k = j + 1
        else:
            k += 1
    ev_rank = _rank(S["event"][story])
    keep_of, drop = {}, np.zeros(n_shots, bool)
    for grp in groups:
        score = []
        for k in grp:
            a, b = s0[k], s1[k]
            ev = float(ev_rank(S["event"][a:b + 1].max()))
            others = [o for o in grp if o != k]
            view = np.mean([_desc_dist(S["mlay"][k], S["mlay"][o], S["hist"][k], S["hist"][o]) for o in others])
            moved = float((S["cam"][a + 1:b + 1] + S["subj"][a + 1:b + 1] * S["area"][a + 1:b + 1]).sum())
            score.append((ev, view, b - a + 1, moved))
        sc = np.array(score, np.float64)
        sc = sc / np.maximum(sc.max(0), 1e-9)          # each signal relative to the group
        total = sc[:, 0] + sc[:, 1] + 0.5 * (sc[:, 2] + sc[:, 3])
        best = grp[int(np.argmax(total))]
        for k in grp:
            keep_of[k] = best
            drop[k] = k != best
    return groups, drop, keep_of, thr


def _rank(ref):
    s = np.sort(np.asarray(ref, np.float64))
    return lambda x: np.searchsorted(s, x) / max(len(s), 1)
