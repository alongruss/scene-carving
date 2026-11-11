"""PROTOTYPE - throwaway. Pluggable heals for same-shot joins (decision #67).

A heal replaces the K output frames around a mid-shot join with K new frames, so the
output length and the audio sync stay exact. Every heal has the same signature:

    frames, info = heal(a, b, a_end, b_end)

  a[t], b[t]    the co-timed handle pairs, t = 0..K-1: a[t] = A(p-h+1+t), b[t] = B(q-h+t).
                The plain dissolve blends exactly these with alpha_t = (t + 0.5) / K, so the
                stronger layer of every output frame is the one in sync with the audio.
  a_end, b_end  the untouched frames just outside the window: A(p-h) and B(q+h).
  frames        K float32 HxWx3 arrays in 0..255.   info: a small dict for the report.

Heals with ENDPOINT = True replace the window with in-betweens of a_end and b_end, so
they invent the motion inside it. Decision #67 allows them only where no one speaks in the
window. All heals here are warp-only (each output pixel is a weighted mix of original
pixels, moved along a flow field): no learned residual, no generative model.

Add a heal by writing a function with this signature and registering it in HEALS.
See docs/research/frame-infilling-at-joins.md.
"""
import importlib.util
import sys
import time
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RIFE_DIR = ROOT / "cache" / "rife" / "v4.26"       # IFNet_HDv3.py + flownet.pkl (Practical-RIFE 4.26)
FB_TOL = 1.5                                       # px: forward-backward flow error tolerance
FALLBACK_FRAC = 0.35                               # flow inconsistent over more of the frame: plain dissolve
GRAIN_SIGMA = 1.2                                  # px: blur before flow so film grain doesn't steer it
TEXTURE_MIN = 20.0                                 # Sobel magnitude: only textured pixels judge the flow


def _alphas(K):
    return [(t + 0.5) / K for t in range(K)]


def _taus(K):
    return [(t + 1) / (K + 1) for t in range(K)]


# --- dissolve (decision #51) ---------------------------------------------------------------
def dissolve(a, b, a_end, b_end):
    return [x * (1 - al) + y * al for x, y, al in zip(a, b, _alphas(len(a)))], {}


# --- optical flow helpers (OpenCV DIS) -----------------------------------------------------
def _cv():
    import cv2
    return cv2


def _grey(img):
    # a light blur keeps film grain from steering the flow
    return _cv().GaussianBlur(np.clip(img.mean(-1), 0, 255).astype(np.uint8), (0, 0), GRAIN_SIGMA)


def _flows(x, y):
    """DIS flow x->y and y->x (pixels), the share of textured pixels whose flow fails the
    forward-backward check, and the pixel grid."""
    cv2 = _cv()
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    gx, gy = _grey(x), _grey(y)
    f_xy = dis.calc(gx, gy, None)
    f_yx = dis.calc(gy, gx, None)
    H, W = gx.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    back = cv2.remap(f_yx, xx + f_xy[..., 0], yy + f_xy[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    err = np.linalg.norm(f_xy + back, axis=-1)
    # Inconsistent pixels are mostly occlusions (handled by visibility in _project), so only a
    # frame-wide failure of the flow sends a heal back to the plain dissolve. Flat areas are
    # ignored: their flow is arbitrary, and warping them shows nothing.
    grad = np.hypot(cv2.Sobel(gx, cv2.CV_32F, 1, 0), cv2.Sobel(gx, cv2.CV_32F, 0, 1))
    textured = grad > max(TEXTURE_MIN, float(np.percentile(grad, 50)))
    fails = err > FB_TOL + 0.05 * np.linalg.norm(f_xy, axis=-1)
    bad = float(fails[textured].mean()) if textured.any() else 0.0
    return f_xy, f_yx, bad, (xx, yy)


def _warp(img, flow, grid):
    cv2 = _cv()
    xx, yy = grid
    return cv2.remap(img, xx + flow[..., 0], yy + flow[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def _project(f, s, grid):
    """Forward-project flow f (frame -> other frame) to fraction s of the way: returns the
    flow from that in-between time back to the frame, and where the frame is visible there.
    Colliding pixels keep the larger motion (a moving subject covers a still background)."""
    cv2 = _cv()
    xx, yy = grid
    H, W = xx.shape
    mag = np.linalg.norm(f, axis=-1).ravel()
    order = np.argsort(mag, kind="stable")                       # small first; the largest motion wins
    tx = np.rint(xx.ravel() + s * f[..., 0].ravel())[order].astype(np.int64)
    ty = np.rint(yy.ravel() + s * f[..., 1].ravel())[order].astype(np.int64)
    ok = (tx >= 0) & (tx < W) & (ty >= 0) & (ty < H)
    out, cnt = np.zeros((H, W, 2), np.float32), np.zeros((H, W), np.float32)
    out[ty[ok], tx[ok]] = -s * f.reshape(-1, 2)[order][ok]
    cnt[ty[ok], tx[ok]] = 1
    num = cv2.boxFilter(out * cnt[..., None], -1, (3, 3), normalize=False)   # close rounding holes
    den = cv2.boxFilter(cnt, -1, (3, 3), normalize=False)
    filled = np.where(cnt[..., None] > 0, out, num / np.maximum(den, 1e-6)[..., None])
    return filled.astype(np.float32), (den > 0).astype(np.float32)


def _between(x, y, f_xy, f_yx, t, grid):
    """Warp-only in-between at time t (0 = x, 1 = y), by flow projection with visibility."""
    f_tx, vis_x = _project(f_xy, t, grid)
    f_ty, vis_y = _project(f_yx, 1 - t, grid)
    wx, wy = (1 - t) * vis_x, t * vis_y
    tot = wx + wy
    wx, wy = np.where(tot > 0, wx / np.maximum(tot, 1e-6), 1 - t), np.where(tot > 0, wy / np.maximum(tot, 1e-6), t)
    return _warp(x, f_tx, grid) * wx[..., None] + _warp(y, f_ty, grid) * wy[..., None]


def flowdissolve(a, b, a_end, b_end):
    """The dissolve, with each co-timed pair first aligned by DIS flow. A frame whose flow
    fails its forward-backward check broadly shows the plain dissolve instead."""
    t0, out, mags, bads = time.time(), [], [], []
    for x, y, al in zip(a, b, _alphas(len(a))):
        f_xy, f_yx, bad, grid = _flows(x, y)
        fall = bad > FALLBACK_FRAC
        out.append(x * (1 - al) + y * al if fall else _between(x, y, f_xy, f_yx, al, grid))
        mags.append(float(np.linalg.norm(f_xy, axis=-1).mean()))
        bads.append(fall)
    return out, {"flow_px": round(np.mean(mags), 1), "fallback": round(np.mean(bads), 2),
                 "solve_s": round(time.time() - t0, 2)}


def flowinterp(a, b, a_end, b_end):
    """Warp-only in-betweens of the two end frames (DIS flow). If the flow fails broadly, the
    co-timed dissolve shows instead."""
    t0 = time.time()
    f_xy, f_yx, bad, grid = _flows(a_end, b_end)
    fall = bad > FALLBACK_FRAC
    if fall:
        out = [x * (1 - al) + y * al for x, y, al in zip(a, b, _alphas(len(a)))]
    else:
        out = [_between(a_end, b_end, f_xy, f_yx, tau, grid) for tau in _taus(len(a))]
    return out, {"flow_px": round(float(np.linalg.norm(f_xy, axis=-1).mean()), 1),
                 "fallback": float(fall), "solve_s": round(time.time() - t0, 2)}


flowinterp.ENDPOINT = True


# --- RIFE (Practical-RIFE 4.26: warp-and-blend output, no residual) ------------------------
_rife = {}


def _rife_model():
    if "net" in _rife:
        return _rife["net"], _rife["dev"]
    import torch
    import torch.nn.functional as F
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    grids = {}

    def warp(inp, flow):  # bilinear backward warp, border padding (as Practical-RIFE's warplayer)
        k = (str(flow.device), tuple(flow.shape))
        if k not in grids:
            n, _, h, w = flow.shape
            gx = torch.linspace(-1.0, 1.0, w, device=flow.device).view(1, 1, 1, w).expand(n, -1, h, -1)
            gy = torch.linspace(-1.0, 1.0, h, device=flow.device).view(1, 1, h, 1).expand(n, -1, -1, w)
            grids[k] = torch.cat([gx, gy], 1)
        fl = torch.cat([flow[:, 0:1] / ((inp.shape[3] - 1.0) / 2.0), flow[:, 1:2] / ((inp.shape[2] - 1.0) / 2.0)], 1)
        return F.grid_sample(inp, (grids[k] + fl).permute(0, 2, 3, 1), mode="bilinear",
                             padding_mode="border", align_corners=True)

    # IFNet_HDv3.py imports `from model.warplayer import warp`; provide it without the repo.
    pkg, mod = types.ModuleType("model"), types.ModuleType("model.warplayer")
    mod.warp = warp
    pkg.warplayer = mod
    sys.modules.setdefault("model", pkg)
    sys.modules["model.warplayer"] = mod
    spec = importlib.util.spec_from_file_location("rife_ifnet_v426", RIFE_DIR / "IFNet_HDv3.py")
    ifnet = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ifnet)
    net = ifnet.IFNet()
    state = torch.load(RIFE_DIR / "flownet.pkl", map_location="cpu", weights_only=True)
    net.load_state_dict({k.replace("module.", ""): v for k, v in state.items()}, strict=False)
    net.eval().to(dev)
    _rife.update(net=net, dev=dev)
    return net, dev


def _rife_between(x, y, t):
    import torch
    import torch.nn.functional as F
    net, dev = _rife_model()
    H, W = x.shape[:2]
    ph, pw = -(-H // 128) * 128, -(-W // 128) * 128
    # RIFE was trained on BGR frames (cv2), ours are RGB: flip in and out
    to = lambda im: F.pad(torch.from_numpy(np.ascontiguousarray(im[..., ::-1].transpose(2, 0, 1)))[None].to(dev)
                          / 255.0, (0, pw - W, 0, ph - H))
    with torch.no_grad():
        _, _, merged = net(torch.cat((to(x), to(y)), 1), t, [16, 8, 4, 2, 1])
    return merged[-1][0, :, :H, :W].permute(1, 2, 0).cpu().numpy()[..., ::-1] * 255.0


def rifemorph(a, b, a_end, b_end):
    """The dissolve, with each co-timed pair merged by RIFE at time alpha_t (warp + mask)."""
    t0 = time.time()
    out = [_rife_between(x, y, al) for x, y, al in zip(a, b, _alphas(len(a)))]
    return out, {"solve_s": round(time.time() - t0, 2), "device": str(_rife["dev"])}


def rife(a, b, a_end, b_end):
    """Warp-only RIFE in-betweens of the two end frames."""
    t0 = time.time()
    out = [_rife_between(a_end, b_end, tau) for tau in _taus(len(a))]
    return out, {"solve_s": round(time.time() - t0, 2), "device": str(_rife["dev"])}


rife.ENDPOINT = True

HEALS = {"dissolve": dissolve, "flowdissolve": flowdissolve, "flowinterp": flowinterp,
         "rifemorph": rifemorph, "rife": rife}


def is_endpoint(name):
    return getattr(HEALS[name], "ENDPOINT", False)
