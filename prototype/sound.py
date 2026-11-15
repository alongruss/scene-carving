"""PROTOTYPE - throwaway. Sound types and separate music carving (decisions #75-#76).

  * sound type per frame, from the original mix (no stems): speech (ASR words), music
    (sustained tonal energy: the harmonic share of a median-filter harmonic/percussive
    split), effects/breathing (the rest), silence
  * music-only stretches: music with no speech and little else in the mix
  * carve_music(): shorten a music-only stretch at musical joins, independent of the
    picture's cuts: jumps between moments that sound alike, starting on onsets,
    equal-power crossfades; the removed total is exact to the sample
"""
import time

import numpy as np

SR = 16000
NFFT, HOP = 1024, 320                     # 64 ms window, 20 ms hop (50 analysis frames per second)
MUSIC_H = 0.62                            # harmonic share of the energy: tonal enough to be music
MUSIC_SMOOTH_S = 1.0                      # judged over this window
MUSIC_MIN_S = 4.0                         # shorter music-only runs are left to the joint cuts
SILENCE_DB = 12.0                         # within this many dB of the film's floor = silence
JUMP_CTX_S = 0.5                          # context compared on both sides of a musical jump
JUMP_MIN_S = 0.3                          # shortest musical jump
JUMP_MAX_S = 30.0                         # longest musical jump
JUMP_MARGIN_S = 0.6                       # keep jumps this far from the stretch ends
MUSIC_XFADE_S = 0.08                      # equal-power crossfade at a musical join


def _stft_mag(a):
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    x = torch.from_numpy(a.astype(np.float32)).to(dev)
    win = torch.hann_window(NFFT, device=dev)
    out = []
    step = HOP * 60000
    for c0 in range(0, len(x), step):
        seg = x[max(0, c0 - NFFT):c0 + step + NFFT]
        S = torch.stft(seg, NFFT, HOP, window=win, center=False, return_complex=True).abs()
        skip = (c0 - max(0, c0 - NFFT)) // HOP
        out.append(S[:, skip:skip + step // HOP].T.contiguous())
    return torch.cat(out), dev


def harmonic_share(a):
    """Per analysis frame: share of energy in the harmonic part (median over time beats
    median over frequency), 60 Hz - 6 kHz."""
    import torch
    S, dev = _stft_mag(a)                                  # (T, bins)
    f = np.fft.rfftfreq(NFFT, 1 / SR)
    band = torch.from_numpy((f >= 60) & (f <= 6000)).to(dev)
    S = S[:, band]
    T = S.shape[0]
    kt, kf = 17, 17                                         # ~340 ms in time, ~265 Hz in frequency
    hs = torch.empty(T, device=dev)
    en = torch.empty(T, device=dev)
    for c0 in range(0, T, 20000):
        lo, hi = max(0, c0 - kt), min(T, c0 + 20000 + kt)
        blk = S[lo:hi]
        Ht = torch.nn.functional.pad(blk.T[None], (kt // 2, kt // 2), mode="replicate")[0].unfold(1, kt, 1).median(-1).values.T
        Pf = torch.nn.functional.pad(blk[None], (kf // 2, kf // 2), mode="replicate")[0].unfold(1, kf, 1).median(-1).values
        Mh = Ht ** 2 / (Ht ** 2 + Pf ** 2 + 1e-12)
        e = (blk ** 2).sum(1)
        h = ((blk ** 2) * Mh).sum(1) / (e + 1e-12)
        a0 = c0 - lo
        n_ = min(20000, T - c0)
        hs[c0:c0 + n_] = h[a0:a0 + n_]
        en[c0:c0 + n_] = e[a0:a0 + n_]
    return hs.cpu().numpy(), en.cpu().numpy()


def sound_types(path, n_frames, fps, word_mask, rms_db, cache):
    """Per video frame: harmonic share, and the music-only mask."""
    if cache.exists():
        z = np.load(cache)
        print(f"[sound] cached: {cache}")
        h_f = z["h"]
    else:
        from carve_proto import read_audio
        t0 = time.time()
        a = read_audio(path, SR, 1)
        h, _ = harmonic_share(a)
        t_an = (np.arange(len(h)) * HOP + NFFT / 2) / SR
        fr = np.minimum((t_an * fps).astype(np.int64), n_frames - 1)
        h_f = np.bincount(fr, weights=h, minlength=n_frames) / np.maximum(np.bincount(fr, minlength=n_frames), 1)
        h_f = h_f.astype(np.float32)
        np.savez(cache, h=h_f)
        print(f"[sound] harmonic share in {time.time()-t0:.0f}s")
    k = max(1, int(MUSIC_SMOOTH_S * fps / 2))
    hs = np.convolve(h_f, np.ones(2 * k + 1) / (2 * k + 1), mode="same")
    floor = np.percentile(rms_db, 2)
    audible = np.convolve(rms_db > floor + SILENCE_DB, np.ones(2 * k + 1) / (2 * k + 1), mode="same") > 0.8
    near_speech = np.convolve(word_mask.astype(float), np.ones(2 * k + 1), mode="same") > 0
    music = (hs >= MUSIC_H) & audible & ~near_speech
    from carve_proto import runs
    mo = np.zeros(n_frames, bool)
    for s, e in runs(music):
        if e - s >= MUSIC_MIN_S * fps:
            mo[s:e] = True
    silent = ~audible
    return dict(h=h_f, h_smooth=hs.astype(np.float32), music_only=mo, silent=silent)


def _features(x, sr):
    """Log band energies (shape, 36 bands) and onset strength at 50 per second, from 48 kHz audio."""
    m = x.mean(1) if x.ndim == 2 else x
    step = sr // SR
    m = m[::step] if step > 1 else m                       # crude decimation is fine for features
    if len(m) < NFFT:
        return np.zeros((1, 36)), np.zeros(1)
    win = np.hanning(NFFT).astype(np.float32)
    idx = np.arange(0, len(m) - NFFT + 1, HOP)
    frames = np.stack([m[i:i + NFFT] for i in idx]) * win
    mag = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    f = np.fft.rfftfreq(NFFT, 1 / SR)
    edges = np.geomspace(60, 7000, 37)
    bands = np.stack([mag[:, (f >= lo) & (f < hi)].sum(1) for lo, hi in zip(edges[:-1], edges[1:])], 1)
    lb = np.log10(bands + 1e-9)
    onset = np.maximum(0, np.diff(lb, axis=0, prepend=lb[:1])).sum(1)
    shape = lb - lb.mean(1, keepdims=True)
    return np.concatenate([shape, 0.5 * lb.mean(1, keepdims=True)], 1), onset


def carve_music(x, sr, remove_samples):
    """Shorten stretch x (samples x channels, 48 kHz) by exactly remove_samples with musical
    jumps. Returns (y, jumps) where jumps = [(at_sample_in_x, removed_samples), ...], or
    (None, []) when no clean set of jumps exists (the caller then cuts with the picture)."""
    if remove_samples <= 0:
        return x, []
    if remove_samples > 0.85 * len(x) - 2 * JUMP_MARGIN_S * sr:
        return None, []
    fe, on = _features(x, sr)
    T = len(fe)
    fs = SR / HOP                                         # analysis frames per second
    ctx, margin = int(JUMP_CTX_S * fs), int(JUMP_MARGIN_S * fs)
    spa = sr / fs                                         # output samples per analysis frame
    need = remove_samples / spa
    # candidate join points: onsets (local maxima of onset strength above its median)
    pk = np.flatnonzero((on[1:-1] >= on[:-2]) & (on[1:-1] >= on[2:]) & (on[1:-1] > np.median(on))) + 1
    pk = pk[(pk >= margin + ctx) & (pk <= T - margin - ctx - 1)]
    if len(pk) < 2:
        pk = np.arange(margin + ctx, max(margin + ctx + 1, T - margin - ctx), 5)
    W = np.stack([fe[p - ctx:p + ctx].ravel() for p in pk]) if len(pk) else np.zeros((0, 1))
    lo, hi = int(JUMP_MIN_S * fs), int(JUMP_MAX_S * fs)
    cands = []
    for ii, i in enumerate(pk):
        jj = np.flatnonzero((pk - i >= lo) & (pk - i <= min(hi, need + 2)))
        if len(jj):
            cost = np.abs(W[jj] - W[ii]).mean(1)
            for j_, c in zip(jj, cost):
                cands.append((float(c), int(i), int(pk[j_])))
    cands.sort()
    chosen, left = [], need
    free = lambda i, j: all(j + ctx < u0 or i - ctx > u1 for u0, u1 in chosen)  # noqa: E731
    for c, i, j in cands:
        if left < lo / 2:
            break
        if j - i <= left + 0.5 and free(i, j):
            chosen.append((i, j))
            left -= j - i
    if left >= 0.5:                                       # top up with the jump closest in length
        best = None
        for c, i, j in cands:
            if free(i, j) and j - i <= left + 0.5:
                key = (abs((j - i) - left), c)
                if best is None or key < best[0]:
                    best = (key, i, j)
        if best is None:
            return None, []
        chosen.append((best[1], best[2]))
    if not chosen:                                        # too little to remove for a musical jump
        return None, []
    chosen.sort()
    # to samples; the remainder (under one analysis frame) goes to the longest jump
    js = [[int(round(i * spa)), int(round((j - i) * spa))] for i, j in chosen]
    k = int(np.argmax([r for _, r in js]))
    js[k][1] += remove_samples - sum(r for _, r in js)
    xf = int(MUSIC_XFADE_S * sr / 2)
    end = xf
    for at, rem in js:                                    # valid, ordered, non-overlapping
        if rem <= 0 or at - xf < end or at + rem + xf > len(x):
            return None, []
        end = at + rem + xf
    ramp = np.linspace(0, np.pi / 2, 2 * xf, dtype=np.float32)[:, None]
    fo, fi = np.cos(ramp), np.sin(ramp)
    pieces, pos = [], 0
    for at, rem in js:
        pieces.append(x[pos:at - xf])
        pieces.append(x[at - xf:at + xf] * fo + x[at + rem - xf:at + rem + xf] * fi)
        pos = at + rem + xf
    pieces.append(x[pos:])
    y = np.concatenate(pieces)
    return y, [(at, rem) for at, rem in js]
