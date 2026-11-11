# Frame infilling at joins: interpolation, morph cuts and generative in-betweening

> Part of the [Scene Carving research survey](README.md) (scan of 2026-11-11).
> Scope: which temporal frame-infilling techniques could compete with the 6-frame `dissolve` at same-shot (mid-shot) joins, and which of them run on the development laptop (GTX 970M, sm_52, 6 GB, fp32 only; i7-6700HQ; 32 GB RAM; Windows 11; PyTorch ≤ 2.14 from the cu126 wheels, see [landscape.md](landscape.md) §5).
> It builds on [patching-from-other-times.md](patching-from-other-times.md) (patch heals, video inpainting, transitions between non-adjacent frames) and [video-and-editing.md](video-and-editing.md) §5 (Berthouzoz 2012, Morph Cut, FILM, RIFE, jump-cut smoothing). Those entries are extended here, not repeated.
>
> **Verification:** ✔ URL fetched and content confirmed. (s) taken from search results only, or the fetch was blocked. **UNVERIFIED**: could not be confirmed. *API* means the licence or file list was read from the GitHub or Hugging Face API on 2026-11-11. ‡ means read on this laptop on 2026-11-11 (read-only queries; no model was downloaded or run). *Est.* marks an arithmetic estimate for the GTX 970M or the i7-6700HQ. Runtimes quoted from papers are on the authors' hardware.
>
> **Status:** decisions #33 ("Never synthesize"), #41 (carve only) and #51 (short dissolves of original material) still hold. This note does not change them. Each technique is tagged with the decision it would touch. The choice is the user's.

---

## 0. The problem in infilling terms

**The current heal, exactly.** A join butts frame p (last kept frame before the gap) against frame q (first kept frame after it). `picture_plan` in `prototype/carve_proto.py` (`DISSOLVE_H = 3`) replaces K = 2h = 6 output frames around the join. Output frame t (t = 0…5) is

  (1 − α_t)·a_t + α_t·b_t, with a_t = frame p−2+t, b_t = frame q−3+t, α_t = (t + 0.5)/6.

The **A-side** a_t runs 3 frames past p into removed material. The **B-side** b_t starts 3 frames before q. The six output positions already existed, so length is exact.

**A property worth keeping: the stronger layer is in sync.** The audio is cut at the same join, with a 10 ms crossfade. Output frames 0–2 play over the audio of frames p−2…p, and their stronger layer (α < 0.5) is exactly frames p−2…p. Frames 3–5 play over the audio of q…q+2, and their stronger layer is q…q+2. So the dominant picture is always co-timed with the sound. The weaker layer shows a mouth from up to 3 frames (125 ms) away, at no more than 42% opacity. *(This is my reading of the code, not a measurement.)*

**What the dissolve does badly.** If the subject moved between p and q, both poses show at once: a ghost. The blind bake-off still preferred it. The `patch` heal was worst in 7 of 10 cuts, and `dissolve6` was worst only once (`prototype/README.md`, section "Bake-off verdict"; [DECISIONS.md](../DECISIONS.md) #59).

**Infilling means replacing those K frames with something better.** The options differ in what each output pixel is:

| Level | Each output pixel is… | Examples | New content? |
|---|---|---|---|
| 0 | one original pixel | `hard` | No |
| 1 | a blend of two original pixels at the same place | `dissolve` (#51) | No new positions; mixed values |
| 2 | a blend of two original pixels, each first moved along a motion field (**warped**) | motion-compensated dissolve, ffmpeg `minterpolate`, Practical-RIFE 4.x | No new colours, but pixels sit where they never sat; holes get stretched or doubled pixels |
| 3 | level 2 plus a learned correction, or a network that paints the frame | RIFE (paper model), FILM, IFRNet, AMT, EMA-VFI | Partly new values |
| 4 | decoded by a generative model from noise and the two keyframes | LDMVFI, SVD-based in-betweening, Wan FLF2V, LTX-Video | New pixels; the model may invent content |

#33 forbids "synthesized in-between frames". #51 allows blending but says "generating or interpolating pixels is still not" allowed. **Level 2 is the boundary case:** it invents no colours, but each frame as a whole never existed.

**Two ways to place the K frames:**
- **Co-timed morph.** Keep the dissolve's pairs (a_t, b_t) and its α_t, but first align the two frames geometrically. Each layer keeps its own motion, including its own mouth. Only the pose difference between A and B is bridged.
- **Endpoint interpolation.** Freeze two end frames, p−h (the last untouched frame before the window) and q+h (the first untouched one after it). Generate K frames at times τ_k = k/(K+1), k = 1…K. This is what frame-interpolation models and Morph-Cut-style tools do. All motion inside the window is made up, and the mouth morphs between two still shapes.

**Why the gap matters.** Frame-interpolation models are trained on consecutive frames, for example Vimeo-90K triplets or the X4K1000FPS dataset (4K at 1000 fps) ✔ https://github.com/JihyongOh/XVFI. Our p and q can be seconds apart. Then no correct in-between exists: a gesture that went up and down becomes a slide, and a turned head becomes a morph. Endpoint interpolation also squeezes seconds of real displacement into 250 ms, which is a speed-up of subject motion. Decision #13 ("we should not distort physics") rules that out for anything but small pose shifts. Small pose shifts are also where every vendor says these tools work (§2).

## 1. Flow-based video frame interpolation (VFI)

**Shared notes**
- **What they do.** All models here estimate **optical flow** (where each pixel moved) and **warp** both inputs toward time τ. They differ in how they find large displacements and in whether a network then paints a correction.
- **Runs on the 970M?** PyTorch models that use only standard operations (convolutions, `grid_sample`) should run in fp32 on the cu126 wheels (*est.*). Models that need CuPy kernels, compiled CUDA extensions or Linux-only kernels are flagged.
- **Speed scaling (*est.*).** The RTX 3090 has 10,496 CUDA cores at a 1.70 GHz boost ✔ https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3090-3090ti/, about 36 TFLOPS fp32. The 970M has 1,280 cores ([landscape.md](landscape.md) §5) at about 1 GHz, about 2.5 TFLOPS. I assume the 970M is 8–15× slower than a 3090 and about 5× slower than a 2080 Ti on these fp32 networks. Per-join times below are the paper latency × that factor × K, for 1280×720. They could be off by 2× either way.
- **Benchmarks.** SNU-FILM "extreme" and X-TEST / Xiph 4K are the large-motion test sets. On SNU-FILM extreme every model scores only about 24–26 dB PSNR ✔ (VFIMamba Table 2, https://arxiv.org/html/2407.02315; AMT Table, https://arxiv.org/html/2304.09790v1). No benchmark spans seconds at 24 fps.

**Super SloMo** (Jiang et al., *CVPR 2018*)
- Links: https://arxiv.org/abs/1712.00080 ✔. The arXiv page links no official code ✔.
- What it does: a U-Net estimates flow both ways, combines it linearly for any τ, refines it and predicts **visibility maps** that hide occluded pixels. It then warps and fuses the inputs ✔.
- Maps to: a historical baseline that assumes straight-line motion. Not a candidate.

**DAIN** (Bao et al., *CVPR 2019*)
- Links: https://arxiv.org/abs/1904.00830 · https://github.com/baowenbo/DAIN ✔ (MIT, *API*).
- What it does: uses depth so that nearer objects win occlusions.
- Laptop: needs two custom CUDA extensions written against PyTorch 1.0's ATen API. The README lists compute_50/52 among its supported flags ✔. Building them against PyTorch 2.x on Windows will probably fail (*est.*).
- Maps to: superseded and hard to build. Not a candidate.

**RIFE and Practical-RIFE** (Huang et al., *ECCV 2022*)
- Links: https://arxiv.org/abs/2011.06294 · https://github.com/hzwer/ECCV2022-RIFE ✔ (MIT) · https://github.com/hzwer/Practical-RIFE ✔ (MIT; the model files are under the same licence).
- What it does: a small network (IFNet) estimates the flows from time τ to both inputs directly, plus a per-pixel **fusion mask**. It needs no pre-trained flow model and accepts any τ.
- **Output differs by version.**
  - The ECCV paper model adds a learned residual from a U-Net: `merged[2] = torch.clamp(merged[2] + res, 0, 1)` ✔ https://raw.githubusercontent.com/hzwer/ECCV2022-RIFE/main/model/IFNet.py. That is level 3.
  - Practical-RIFE 4.26 ends with `return warped_img0 * mask + warped_img1 * (1 - mask)` and adds nothing ✔. That is level 2: each output pixel is a weighted mix of two warped original pixels. Source: a third-party MIT copy of the 4.26 model code, https://raw.githubusercontent.com/HolyWu/vs-rife/master/vsrife/IFNet_HDv3_v4_26.py. The official code ships with the weights ("put *.py and flownet.pkl on train_log/", Practical-RIFE README ✔).
  - The warp is bilinear `grid_sample` with border padding ✔ https://raw.githubusercontent.com/hzwer/Practical-RIFE/main/model/warplayer.py. Edges therefore smear rather than show black.
- Versions: the newest are 4.26 (2024-09-21) and 4.25.lite (2024-10-20). The README recommends 4.25 for most scenes ✔. Commits up to 2026-08 change code only, with no new model (*API*).
- Laptop:
  - Standard operations only. Python ≤ 3.11 ✔. `requirements.txt` pins numpy ≤ 1.23.5 (*API*), while the prototype's `.venv` has numpy 2.5 and no PyTorch ‡. So it needs its own environment or a subprocess.
  - The RIFE paper says about 3 GB of GPU memory suffices for 1080p (s), so 720p should fit in 6 GB.
  - **Vulkan port, no CUDA or PyTorch needed:** rife-ncnn-vulkan (MIT, Windows binary, `-s` sets τ) ✔ https://github.com/nihui/rife-ncnn-vulkan ships models up to v4.6. The fork https://github.com/TNTwise/rife-ncnn-vulkan (MIT) ships v4.25 and v4.26 (*API*). The 970M reports Vulkan 1.4.303 on driver 577.00 ‡.
- Time: 29 ms per 720p frame on an RTX 3090 for the paper model (AMT Table 1 ✔). That gives 0.25–0.45 s per frame on the 970M, **about 2–3 s per join at K = 6 and 3–6 s at K = 12** (*est.*). It costs 0.20 TFLOPs per 720p frame ✔ (VFIMamba Table 2), about 1–3 s per frame on the i7 CPU (*est.*). The 4.2x models have more flow blocks than the paper model, so they may be somewhat slower (*est.*).
- Quality: the authors make no large-motion claims. RIFE sits at the low end of VFIMamba's tables: 25.27 dB on SNU-FILM extreme (IFRNet-L 25.26, VFIMamba 25.79) and 30.13 dB on X-TEST 4K, where only XVFI scores lower ✔. Expected failures (*est.*): smeared pixels where background is uncovered, ghosting where the mask is unsure, and melting limbs on large motion. It invents no content.
- Maps to: **(b) heal.** It is fast enough to precompute every mid-shot join overnight, and it works both for endpoint interpolation and as a co-timed morph.

**IFRNet** (Kong et al., *CVPR 2022*)
- Links: https://arxiv.org/abs/2205.14620 · https://github.com/ltkong218/IFRNet ✔ (MIT) · https://github.com/nihui/ifrnet-ncnn-vulkan ✔ (MIT, any τ).
- What it does: refines the flow and an intermediate feature map together in one encoder–decoder. The decoder outputs the frame, which puts it at level 3 (*est.* from the design; the exact output head is **UNVERIFIED**).
- Time: IFRNet-L takes 80 ms per 720p frame on a 3090 ✔, so **4–7 s per join at K = 6 and 8–15 s at K = 12** (*est.*). SNU-FILM extreme: 25.26–25.27 dB ✔.

**FILM** (Reda et al., *ECCV 2022*)
- Links: https://arxiv.org/abs/2202.04901 ✔ · https://github.com/google-research/frame-interpolation ✔ (Apache-2.0; TensorFlow 2; "not an officially supported Google product"; archived and read-only since 2025-10-14) · unofficial PyTorch port https://github.com/dajes/frame-interpolation-pytorch ✔ (Apache-2.0, weights converted from the TF model).
- What it does: a feature pyramid whose weights are shared across scales, so the same flow estimator handles large motion at coarse levels. A synthesis network then paints the frame (level 3). It predicts only the midpoint, so several frames come from recursion ✔ https://research.google/blog/large-motion-frame-interpolation/.
- **Closest published scenario to ours.** Google's post targets near-duplicate photos taken "several seconds" apart, with motion up to about 100 px ✔.
- Laptop:
  - The official code needs TensorFlow ≤ 2.10, the last release with GPU support on native Windows ✔ https://www.tensorflow.org/install/pip. TensorFlow's packages include architecture 5.0, which covers 5.2 (same page ✔). The PyTorch port avoids this.
  - The paper reports 0.393 s and about 4.5 GB peak at 720p (s, from a search snippet; GPU not confirmed). So 6 GB is tight, but `--block_height/--block_width` tiling exists ✔.
  - Recursion gives 2ⁿ−1 frames, so K = 7 or 15 rather than 6 or 12. That is **about 20–40 s for 7 frames and 45–90 s for 15** (*est.*).
- Quality: strong on large motion. But on talking heads that turn, Wang et al. show FILM causing "severe facial distortion" ✔ https://jeanne-wang.github.io/jumpcutsmoothing/.

**AMT** (Li et al., *CVPR 2023*)
- Links: https://arxiv.org/abs/2304.09790 ✔ · https://github.com/MCG-NKU/AMT ✔. Licence: **CC BY-NC 4.0** (non-commercial; commercial use needs permission).
- What it does: builds all-pairs correlation volumes, like RAFT, and predicts several flow fields per pixel to handle ambiguous motion.
- Laptop: correlation cost is "quadratic to the image resolution" (authors ✔), so whether 720p fits in 6 GB is uncertain. Latency per 720p frame on a 3090 ✔: AMT-S 51 ms, AMT-L 116 ms, AMT-G 250 ms. For AMT-G that is **12–24 s per join at K = 6 and 25–50 s at K = 12** (*est.*).
- Quality: up to 25.43 dB on SNU-FILM extreme, and the best Xiph 4K score in its table (34.63 dB) ✔.

**EMA-VFI** (Zhang et al., *CVPR 2023*)
- Links: https://arxiv.org/abs/2303.00440 · https://github.com/MCG-NJU/EMA-VFI ✔ (Apache-2.0; the licences of RIFE, IFRNet and the other works it builds on also apply).
- What it does: inter-frame attention extracts motion and appearance together. Variants support any τ.
- Laptop: PyTorch with timm, no custom operations ✔. The base model takes 211 ms per 720p frame on a 3090 ✔, so **10–20 s per join at K = 6 and 20–40 s at K = 12** (*est.*). The small model costs about the same as RIFE (0.20 TFLOPs ✔).
- Quality: 25.59–25.69 dB on SNU-FILM extreme ✔.

**UPR-Net** (Jin et al., *CVPR 2023*; *IJCV* 2025)
- Links: https://arxiv.org/abs/2211.03456 · https://github.com/srcn-ivl/UPR-Net ✔. Licence: **CC BY-NC-ND 4.0** (*API*, LICENSE file), so no modified redistribution.
- What it does: a lightweight pyramid network (1.7M parameters ✔) with forward warping by softmax splatting. The authors say iterative synthesis "can significantly improve the robustness" on large motion ✔.
- Laptop: tested with PyTorch 1.6, CUDA 10.2 and CuPy ✔. Whether CuPy kernels run on sm_52 with a cu126 stack is **UNVERIFIED**.

**XVFI** (Sim, Oh & Kim, *ICCV 2021*)
- Links: https://arxiv.org/abs/2103.16206 · https://github.com/JihyongOh/XVFI ✔. Licence: research and education only ✔.
- What it does: recursive multi-scale flow. The number of scales can be raised for larger motion ✔.
- Time: 165 ms at 1024² on a 2080 Ti ✔, about **10 s per join at K = 12** (*est.*). Quality: 30.12 dB on X-TEST 4K and 24.17 dB on SNU-FILM extreme ✔, below the newer models.

**SGM-VFI** (Liu et al., *CVPR 2024*)
- Links: https://arxiv.org/abs/2404.06913 ✔ · https://github.com/MCG-NJU/SGM-VFI ✔. The README says Apache-2.0, but the repository has no LICENSE file (*API*).
- What it does: estimates flow locally, finds where that flow is flawed, then fixes it with sparse **global matching** (GMFlow) ✔. It is built for large motion.
- Laptop: torch 1.13.1+cu117 and CuPy 12.3.0 in its requirements (*API*). It takes 73.6 ms at 512² and 942.9 ms at 1024² on a 2080 Ti ✔, so **25–35 s per join at K = 6 and 50–70 s at K = 12** (*est.*). The global feature extractor is the bottleneck ✔.
- Quality: best on the authors' own large-motion subsets (X-Test-L-2K 30.99 dB). Global matching adds about 0.4–0.7 dB over local flow alone ✔.

**VFIMamba** (Zhang et al., *NeurIPS 2024*)
- Links: https://arxiv.org/abs/2407.02315 ✔ · https://github.com/MCG-NJU/VFIMamba ✔ (Apache-2.0).
- What it does: state-space (Mamba) blocks model inter-frame dependencies at a cost linear in sequence length.
- Laptop: **blocked.** It needs the mamba_ssm and causal_conv1d CUDA kernels ✔, and Mamba lists Linux as its only OS ✔ https://github.com/state-spaces/mamba. Support for sm_52 is not stated. Time if it ran: 310.9 ms at 1024² on a 2080 Ti ✔.
- Quality: best in its own tables: 32.15 dB on X-TEST 4K and 25.79 dB on SNU-FILM extreme ✔.

**GIMM-VFI** (Guo, Li & Loy, *NeurIPS 2024*) and **BiM-VFI** (Seo, Oh & Kim, *CVPR 2025*)
- GIMM-VFI: https://arxiv.org/abs/2407.08680 · https://github.com/GSeanCDAT/GIMM-VFI ✔ (S-Lab License 1.0, non-commercial ✔). It learns an implicit motion field for any τ, on top of RAFT or FlowFormer. It used 7.9 GB for 2K input at 0.5 scale on a V100 ✔, so 720p probably needs downscaling on 6 GB (*est.*). It also needs CuPy.
- BiM-VFI: https://arxiv.org/abs/2412.11365 · https://github.com/KAIST-VICLab/BiM-VFI ✔ (research and education only). A bidirectional motion field for non-uniform motion (speeding up, curving). Uses torch 2.4.1 and CuPy ✔. No runtime given.

**2025–2026 frontier**
- **EDEN** (*CVPR 2025*): a diffusion transformer for large-motion interpolation. No code link ✔ https://arxiv.org/abs/2503.15831.
- **MoMo** (*AAAI 2025*): diffusion over optical flow instead of pixels ✔ https://arxiv.org/abs/2406.17256.
- **LDF-VFI** (arXiv, January 2026): an autoregressive diffusion transformer over the whole sequence. It claims gains "especially in scenes with large motion" ✔ https://arxiv.org/abs/2601.14959 · code https://github.com/xypeng9903/LDF-VFI (Apache-2.0, *API*).
- Listed in the AceVFI survey index but not opened (s) https://github.com/CMLab-Korea/Awesome-Video-Frame-Interpolation: bidirectional autoregressive diffusion for large complex motion (*CVPR 2026*), real-time VFI with one-step diffusion (*ICLR 2026*), LC-Mamba (*CVPR 2025*), Hierarchical Flow Diffusion (*CVPR 2025*), TLB-VFI (*ICCV 2025*).
- **Trend (assessment):** since 2025, large-motion interpolation has moved to diffusion (level 4). Progress in flow-only models is incremental.

## 2. Morph-cut-style transitions for talking heads

**Berthouzoz, Li & Agrawala 2012** (already in [video-and-editing.md](video-and-editing.md) §5 and [patching-from-other-times.md](patching-from-other-times.md) §5)
- New here: the abstract says the tools flag frames where the speaker is **quiet and still** as good cut points. Hidden transitions come from a hierarchical graph algorithm, with their timing set by a data-driven technique ✔ https://history.siggraph.org/?p=110546.
- Lesson: cut placement comes first. The flow interpolation is only the last step, applied after an easy frame pair has been found.
- The paper PDF (vis.berkeley.edu) failed with an expired certificate, so the details of its flow method remain **UNVERIFIED** beyond Agrawala's slides.

**Adobe Premiere Pro Morph Cut** (2015)
- Sources: the official Adobe blog post by James Strawn, 2015-06-18 ✔ https://blog.adobe.com/en/publish/2015/06/18/morph-cut-tips-tricks-for-best-results. The help pages return 403 (s): https://helpx.adobe.com/premiere/desktop/add-video-effects/apply-video-transitions/apply-morph-cut-to-smoothen-jump-cuts.html and https://helpx.adobe.com/ph_en/premiere-pro/kb/morph-cut.html.
- What it does: the search-indexed help describes face tracking combined with optical-flow interpolation (s). Analysis starts when the transition is dropped and reruns whenever it is trimmed ✔.
- Stated ideal footage ✔: a single-subject talking head, a fixed shot (minimal camera movement may be fine), and a static background, "includes avoiding subtle lighting changes".
- Stated limits ✔: "blotchy results" with a lot of background, hand or body movement; face detection struggles with tight framing or profiles; it "will always have some inherent limitations"; analysis is slow on large media and on GPUs with little memory.
- **Lip-sync advice** ✔: start and end the morph "toward the peaks of the last/first words" to avoid lip-sync problems. Pick short, logical gaps with similar head placement, and use the waveform to find natural pauses.
- Maps to: Adobe's own rules make a ready-made join classifier: talking head, still camera, still background, similar head pose, join inside a pause.

**Apple Final Cut Pro "Flow"** ✔ https://support.apple.com/guide/final-cut-pro/ver46d0179ac/mac
- It "seamlessly merges jump cuts to remove pauses or mistakes in on-camera interviews". Its duration is **fixed at 6 frames**; other durations give "unexpected results". On generators it falls back to a standard dissolve.
- Note: Apple's fixed length matches our K = 6.

**DaVinci Resolve "Smooth Cut"** (s) Resolve 18.6 manual mirror https://www.steakunderwater.com/VFXPedia/__man/Resolve18-6/DaVinciResolve18_Manual_files/part753.htm (404 on fetch)
- Smooth Cuts of 2–6 frames work best. Forum users report it works only when the person's start and end orientations are very similar (s) https://forum.blackmagicdesign.com/viewtopic.php?p=1048979.

**Boris FX Continuum "Jump Cut Fixer ML"** ✔ https://borisfx.com/blog/how-boris-fx-helps-make-jump-cuts/
- A commercial plugin using optical flow and machine learning, aimed at moderate-motion talking heads. Stated problems include a hand disappearing, odd blending, and cuts that still stand out.

**Open alternatives.** No open-source morph-cut equivalent was found (search, 2026-11-11). The nearest are running a VFI model across the cut (RIFE front ends such as Flowframes and SVP, listed in the RIFE README ✔) or the classical flow-dissolve in §4.

**Research methods for talking heads**
- **Wang, Park, Zhou, Shechtman & Zhang 2024**, "Jump cut smoothing for talking heads" (in [video-and-editing.md](video-and-editing.md) §5). New here ✔ https://jeanne-wang.github.io/jumpcutsmoothing/: FILM is its only baseline; no code is released; audio and lip sync are not discussed. Frames are synthesised from DensePose keypoints and face landmarks with an image-translation network ✔ https://arxiv.org/abs/2401.04718. Level 4.
- **Deng et al. 2025–2026**, "Beyond Boundary Frames: Talking-Head Inbetweening via Context-Aware Motion Modeling" ✔ https://arxiv.org/abs/2512.03590. A diffusion method that uses the surrounding clips and **injects speech-driven facial motion from the audio**. It was tested on the HDTF and Hallo3 talking-head sets. No code. It is the only method found that conditions the in-betweens on the speech playing over them. Level 4.
- KeyFace (*CVPR 2025*), audio-driven facial animation by keyframe interpolation (s) https://arxiv.org/abs/2503.01715. Not opened.

## 3. Generative keyframe in-betweening

**Shared hardware facts**
- **No fast half precision on sm_52.** NVIDIA says FP16 *computation* in cuFFT needs compute capability 5.3 or later. FP16 has long been supported as a *storage* format, and `cublasSgemmEx` computes in FP32 on FP16 inputs ✔ https://developer.nvidia.com/blog/mixed-precision-programming-cuda-8. So fp16 weights could halve memory but give no speed-up (*est.*). Whether every PyTorch operation accepts fp16 on sm_52 is **UNVERIFIED**. There is no bf16.
- **No FlashAttention.** FlashAttention-2 supports only Ampere, Ada and Hopper, in fp16 or bf16 ✔ https://github.com/Dao-AILab/flash-attention. PyTorch's attention then uses its plain math kernels (*est.*).
- **Memory.** A model of 1.5–2B parameters takes 6–8 GB in fp32, which is more than the card. It must be **offloaded**: layers stay in the 32 GB of RAM and move to the GPU when needed. Diffusers supports this ✔ (`enable_model_cpu_offload`, group offloading). **GGUF quantisation** (ComfyUI-GGUF, Apache-2.0 ✔ https://github.com/city96/ComfyUI-GGUF) lets large transformers run "on low-end GPUs". Weights are still expanded to fp32 for compute here (*est.*).
- **Speed scaling (*est.*).** Published times are on data-centre GPUs with fp16/bf16 tensor cores. The 970M in fp32 is roughly 30–100× slower than those.
- **CPU.** The i7-6700HQ peaks at about 0.2–0.4 TFLOPS fp32 (4 cores, AVX2 FMA), about 5–10× slower than the 970M (*est.*).

**LDMVFI** (Danier, Zhang & Bull, *AAAI 2024*)
- Links: https://arxiv.org/abs/2303.09508 ✔ · https://github.com/danier97/LDMVFI ✔ (MIT; adapted from CompVis latent-diffusion; includes a CuPy module).
- What it does: latent diffusion conditioned on the two neighbouring frames.
- Cost: 439M parameters, 200 DDIM steps, **8.48 s per 480p frame on an RTX 3090** ✔. On the 970M that is about 1–2 min per 480p frame and 2.5–5 min per 720p frame, so **15–30 min per join at K = 6 and 30–60 min at K = 12** (*est.*). Fewer steps would cut time roughly in proportion, at an unknown cost in quality.
- Quality: the best perceptual score (LPIPS 0.123) on SNU-FILM extreme in its own table ✔. That measures how real frames look, not how faithful they are.

**SVD-based in-betweening**
- The shared base, Stable Video Diffusion img2vid-xt, makes 25 frames at 576×1024 in about 180 s on an A100 80GB at default settings ✔ https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt. Its card warns: "Faces and people in general may not be generated properly" ✔.
  - Licence: the Stability community licence, free under $1M annual revenue ✔ https://stability.ai/license. That page does not name SVD in its visible list, so SVD's coverage is (s).
  - Diffusers' tricks bring SVD-XT below 8 GB of VRAM, in fp16 ✔ https://huggingface.co/docs/diffusers/main/en/using-diffusers/svd. That is still not 6 GB in fp32.
- **Generative Inbetweening** (Wang et al., *ICLR 2025*) ✔ https://arxiv.org/abs/2408.15239. It fine-tunes a backward-in-time copy of the model and fuses forward and backward denoising. Code https://github.com/jeanne-wang/svd_keyframe_interpolation ✔ (Apache-2.0): 1024×576, 25 frames, run on an A100.
- **TRF**, "Explorative Inbetweening of Time and Space" (Feng et al., *ECCV 2024*) ✔ https://arxiv.org/abs/2403.14611 · https://time-reversal.github.io ✔. Training-free **Time Reversal Fusion** of the forward and backward paths. Code https://github.com/HavenFeng/time_reversal ✔ is for non-commercial research only.
- **ViBiDSampler** (Yang, Kwon & Ye, *ICLR 2025*) ✔ https://arxiv.org/abs/2410.05651. Samples forward and backward in sequence: **25 frames at 1024×576 in 195 s on one RTX 3090** ✔. Code https://github.com/vibidsampler/vibid (MIT, *API*).
- **FCVG** (Zhu et al., *CVPR 2025*) ✔ https://github.com/Tian-one/FCVG. Makes the path explicit with frame-wise conditions: line matches (GlueStick) and poses (DWPose). Built on SVD-XT 1.1 and ControlNeXt, at 576×1024. No licence file (*API*).
- **Framer** (*ICLR 2025*) ✔ https://github.com/aim-uofa/Framer. SVD plus end-frame conditioning and point trajectories. An "autopilot" mode needs no user input. 512×320. Licence: BSD 2-clause for academic use; commercial use by contact ✔.
- Laptop, whole family: offload only. About **1–3 h per 25-frame sample at 1024×576 and 15–50 min at 512×320** (*est.*). The bidirectional methods run the network twice per step; this is included in the estimate.

**DynamiCrafter interpolation and ToonCrafter**
- **DynamiCrafter** (Xing et al., *ECCV 2024*) ✔ https://github.com/Doubiiu/DynamiCrafter. Code Apache-2.0; no weights licence is stated ✔. The `DynamiCrafter512_interp` model runs at 320×512 and takes **12.8 GB and 20 s on an A100** (50 DDIM steps) ✔. On the 970M: about **10–40 min** per clip with offload (*est.*).
- **ToonCrafter** (*SIGGRAPH Asia 2024*) ✔ https://github.com/ToonCrafter/ToonCrafter (Apache-2.0). About 24 GB and 24 s on an A100; the community reports about 10 GB. Built for cartoons, not live action.

**Wan2.1 FLF2V-14B** (first-last-frame-to-video, April 2025) ✔ https://github.com/Wan-Video/Wan2.1
- Licence: Apache-2.0. A 14B model, 720P only ✔.
- **Will not run on sm_52 as shipped.** Self-attention calls `flash_attention`, which asserts FlashAttention-2 when FlashAttention-3 is missing and asserts fp16/bf16 inputs ✔ https://raw.githubusercontent.com/Wan-Video/Wan2.1/main/wan/modules/attention.py · https://raw.githubusercontent.com/Wan-Video/Wan2.1/main/wan/modules/model.py.
- The diffusers port has a `last_image` argument ✔. Diffusers says its 14B text-to-video example with group offloading "requires ~13GB of VRAM", in bf16 ✔ https://huggingface.co/docs/diffusers/api/pipelines/wan.
- Wan2.2 lists no first-last-frame model, and its TI2V-5B needs at least 24 GB ✔ https://github.com/Wan-Video/Wan2.2.
- Laptop: 14B in fp32 is 56 GB, more than the 32 GB of RAM, so it could only run quantised. My arithmetic gives **days** for one 81-frame 720p clip at about 1 TFLOPS effective (*est.*). Not feasible.

**CogVideoX keyframe interpolation**
- **CogvideX-Interpolation** ✔ https://github.com/feizc/CogvideX-Interpolation: a modified CogVideoX pipeline that takes `first_image` and `last_image`, at 49 frames and 50 steps, with CPU offload and VAE tiling. No licence file (*API*).
- **CogVideoX-5B** ✔ https://github.com/zai-org/CogVideo: about 180 s per 50 steps on an A100. It needs "from 5GB" in BF16 with diffusers' optimisations, measured on Ampere and newer; FP8 needs an H100. Licences: the 5B model uses the CogVideoX LICENSE; the 2B model is Apache-2.0.
- Laptop: about **5–10 h per join** in fp32 with offload (*est.*).

**LTX-Video keyframe conditioning** (Lightricks) ✔ https://github.com/Lightricks/LTX-Video
- Licences: code Apache-2.0. The repository is marked legacy in favour of LTX-2.5 ✔.
  - The weights use the **LTXV Open Weights License** ✔ https://huggingface.co/Lightricks/LTX-Video/raw/main/LTX-Video-Open-Weights-License-0.X.txt. It is free, including for commercial use, below $10M annual revenue. Its use restrictions must be passed on to downstream users.
- What it does: conditions on images *or short video segments* placed at any frame index, each with a strength ✔. Frame counts must be 8n+1 and sizes divisible by 32 ✔.
- Models: 2B and 13B; a `ltxv-2b-0.9.8-distilled` checkpoint exists (*API*). Distilled models use 4–10 steps with guidance 1.0 ✔ https://huggingface.co/docs/diffusers/main/en/api/pipelines/ltx_video.
- Speed: the VAE compresses 1:192 (32×32×8 pixels per token) ✔ https://arxiv.org/abs/2501.00103. The paper claims 5 s of 768×512 video in 2 s on an H100 ✔. The FP8 kernels are optional and need Ada or newer ✔. Diffusers' example needs about 10 GB (bf16 with fp8 casting) ✔.
- Laptop (*est.*, very uncertain):
  - A 17-frame window at 768×512 is only about 1,150 latent tokens. With the 2B distilled model at 8 steps, that is about 10¹⁴ FLOPs, or **roughly 1–10 min per join**.
  - Its weights are 8 GB in fp32, so it needs offload or fp16 storage.
  - It is the **only generative model within overnight reach**.
- Risks (*est.*):
  - The heavy compression softens faces and texture, and the in-betweens may drift in identity.
  - Mouths are invented, since the model gets no audio.
  - A plus: it can be conditioned on a few A frames before the window and a few B frames after it, rather than two stills. That gives it the surrounding motion.

## 4. Classical, non-learned options

These options estimate motion and move original pixels. No model invents content. Uncovered areas are filled by stretching edges or by falling back to the other frame.

**Flow estimators**
- **DIS** (Kroeger et al., arXiv 2016) ✔ https://arxiv.org/abs/1603.03590. Runs at "300Hz up to 600Hz on a single CPU core" at its fastest setting ✔. Available as OpenCV's `DISOpticalFlow` with ULTRAFAST, FAST and MEDIUM presets ✔ https://raw.githubusercontent.com/opencv/opencv/4.x/modules/video/include/opencv2/video/tracking.hpp. OpenCV is Apache-2.0 (*API*). About 0.05–0.3 s per 720p pair on the i7 at MEDIUM (*est.*).
- **Farnebäck** (2003): OpenCV's `calcOpticalFlowFarneback` ✔ (same header). It fits local polynomials and is weak on large displacements (*est.*).
- **RAFT** (Teed & Deng, *ECCV 2020*) ✔ https://github.com/princeton-vl/RAFT (BSD-3); also in torchvision (BSD-3, *API*). Learned, but as a flow estimator it creates no pixels. It builds all-pairs correlation volumes; the optional `alt_cuda_corr` uses "significantly less GPU memory" but is slower ✔. About 1–3 s per 720p pair on the 970M (*est.*).

**Motion-compensated dissolve (flow-guided morph)**
- Classic image morphing warps both images toward a shared intermediate shape, then cross-dissolves. Mahajan et al. 2009, "Moving gradients" (*SIGGRAPH*), moves gradients along per-pixel paths, finds occlusions from path lengths and rebuilds the frame by Poisson reconstruction (s) https://cdfg.mit.edu/pdf/journal/2009-mahajan-moving-gradients-a-path-based-method-for-plausible-image.pdf.
- **Proposed here as `flow-dissolve`:**
  1. For each output frame t, compute the flow F between a_t and b_t.
  2. Warp a_t by α_t·F and b_t by −(1−α_t)·F, so both meet in the same in-between shape.
  3. Blend with the dissolve's α_t.
  4. Where a forward–backward flow check fails, use the plain dissolve.
- Properties: length is exact (the same K positions); the stronger layer stays co-timed with the audio (§0); no colours are invented. Failure modes (*est.*): rubber-sheet bending of limbs and edge smear. Where flow is unreliable it degrades to today's dissolve, not to garbage.

**ffmpeg `minterpolate`** ✔ source https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavfilter/vf_minterpolate.c (LGPL-2.1+)
- What it does: block motion estimation (EPZS by default, 16×16 blocks, search range 32) with bilateral or bidirectional vectors, then overlapped block motion compensation (`obmc`, or adaptive `aobmc`) ✔.
- **Trap:** scene-change detection is on by default (`scd=fdiff`, threshold 10). When it fires, the filter simply duplicates the nearer frame ✔. A big jump cut would therefore come out as a hard cut unless `scd=none` is set. Where no reference pixel is usable, it blends both frames at zero motion ✔.
- Laptop: seconds per join on the CPU (*est.*). Expected quality: blocky halos around non-rigid motion (*est.*).

## 5. Research on hiding jump cuts

- **Only three research lines target the jump cut itself:** Berthouzoz 2012 (choose quiet, still frame pairs, then flow-interpolate), Wang et al. 2024 (generative, keypoint-driven) and Deng et al. 2025–26 (generative, audio-driven). The vendor tools (Morph Cut, Flow, Smooth Cut, Jump Cut Fixer ML) cover the same ground.
- **All of them target a single talking head in interview footage.** Every vendor lists the same failures: head turns, hands, background motion and lighting change.
- **Lip sync:** Adobe advises placing the morph at word peaks or natural pauses. Only Deng et al. condition on speech. No method was found that *checks* lip sync across the healed window.
- **Generative transitions between scenes**, such as "Versatile Transition Generation with Image-to-Video Diffusion" (*ICCV 2025*) (s) https://arxiv.org/abs/2508.01698, aim at visible creative transitions, not invisible joins.
- **Nothing was found on joins in finished, mixed films with moving cameras.** The earlier finding, that no 2024–2026 method heals jump cuts by copying ([patching-from-other-times.md](patching-from-other-times.md) §5), still holds.

## 6. Comparison

Times are per join at 1280×720 on the 970M, for K = 6 / K = 12, and all are *est.* "Large-motion quality" summarises the benchmarks and the stated limits above.

| Method | Family | Source | Licence | Runs on 970M? | Est. time per join | Large-motion quality | Conflicts with #33/#41 |
|---|---|---|---|---|---|---|---|
| `dissolve` (current) | blend, level 1 | `carve_proto.py` | own | Yes | ms | Ghosts the pose change | None (#51) |
| flow-dissolve, DIS | classical warp, co-timed, level 2 | OpenCV DIS | Apache-2.0 | Yes, CPU | 1–3 s / 2–5 s | Falls back to the dissolve where flow fails | Wording of #51 ("interpolating pixels"); not new frames |
| flow-dissolve, RAFT | learned flow + warp, level 2 | RAFT / torchvision | BSD-3 | Yes, fp32 | 15–40 s / 30–80 s | Better flow at large displacement | As above |
| ffmpeg `minterpolate` | block motion, endpoint, level 2 | FFmpeg | LGPL-2.1+ | Yes, CPU | seconds | Blocky; hard cut unless `scd=none` | #33 |
| Super SloMo | VFI | arXiv 1712.00080 | no official code | — | — | Straight-line motion only | #33 |
| DAIN | VFI + depth | baowenbo/DAIN | MIT | Build unlikely | — | Superseded | #33 |
| **Practical-RIFE 4.26** | VFI, warp-only output, level 2 | hzwer/Practical-RIFE | MIT | **Yes** (PyTorch cu126, or ncnn-Vulkan) | **2–3 s / 3–6 s** | Low-end scores; smears | #33 (in-betweens of warped originals) |
| IFRNet-L | VFI, level 3 | ltkong218/IFRNet | MIT | Yes | 4–7 s / 8–15 s | Moderate | #33 |
| FILM | VFI, level 3 | google-research | Apache-2.0 | Likely (~4.5 GB at 720p (s)) | 20–40 s (7) / 45–90 s (15) | Strong; distorts turning faces | #33 |
| AMT-G | VFI, level 3 | MCG-NKU/AMT | CC BY-NC 4.0 | Likely; memory uncertain | 12–24 s / 25–50 s | Good | #33 |
| EMA-VFI | VFI, level 3 | MCG-NJU/EMA-VFI | Apache-2.0 | Yes | 10–20 s / 20–40 s | Good | #33 |
| UPR-Net | VFI, splatting | srcn-ivl/UPR-Net | CC BY-NC-ND 4.0 | Uncertain (CuPy) | unknown | Robust (claimed) | #33 |
| XVFI | VFI, multi-scale | JihyongOh/XVFI | research only | Yes | ~5 s / ~10 s | Below newer models | #33 |
| SGM-VFI | VFI + global matching | MCG-NJU/SGM-VFI | Apache-2.0 (README only) | Likely (CuPy) | 25–35 s / 50–70 s | Best large-motion design that runs | #33 |
| VFIMamba | VFI, state-space | MCG-NJU/VFIMamba | Apache-2.0 | **No** (Linux-only kernels) | — | Best benchmark scores | #33 |
| GIMM-VFI / BiM-VFI | VFI | see §1 | non-commercial / research only | Uncertain (CuPy, memory) | unknown | Arbitrary τ / non-uniform motion | #33 |
| Jump-cut smoothing (Wang 2024) | generative, keypoints | arXiv 2401.04718 | no code | No | — | Handles head turns (claimed) | #33, #41 |
| Talking-head in-betweening (Deng 2025) | generative, audio-driven | arXiv 2512.03590 | no code | No | — | — | #33, #41 |
| LDMVFI | latent diffusion VFI | danier97/LDMVFI | MIT | Yes, slowly | 15–30 min / 30–60 min | Best perceptual score in its table | #33, #41 |
| SVD family (GI, TRF, ViBiD, FCVG, Framer) | video diffusion | see §3 | Apache / MIT / NC / none, plus SVD licence | Offload only | 15–50 min (512×320) to 1–3 h (1024×576) | Plausible; faces unreliable | #33, #41 |
| DynamiCrafter-interp | video diffusion | Doubiiu/DynamiCrafter | Apache-2.0 code; weights unstated | Offload only | 10–40 min | — | #33, #41 |
| ToonCrafter | video diffusion | ToonCrafter | Apache-2.0 | Offload only | — | Cartoons only | #33, #41 |
| Wan2.1 FLF2V-14B | video diffusion | Wan-Video/Wan2.1 | Apache-2.0 | **No** (FlashAttention-2, bf16, 56 GB fp32) | days | Strongest prior | #33, #41 |
| CogVideoX-Interpolation | video diffusion | feizc | none; CogVideoX licence | Offload only | 5–10 h | — | #33, #41 |
| LTX-Video 2B distilled | video diffusion, multi-keyframe | Lightricks/LTX-Video | Apache-2.0 code; LTXV Open Weights | Probably (fp32 + offload) | 1–10 min | Unknown; lossy VAE | #33, #41 |
| Morph Cut / Flow / Smooth Cut / Jump Cut Fixer ML | commercial tools | vendor docs | proprietary | Not usable in our pipeline | — | Talking heads only | #33 |

---

## Terminology

- **VFI (video frame interpolation):** making frames between two given frames.
- **Optical flow:** a per-pixel motion field from one frame to another.
- **Intermediate flow:** flow from the in-between time τ to each input. RIFE estimates it directly.
- **Backward warping:** each output pixel looks up where it came from (`grid_sample`). **Forward warping / splatting:** each input pixel is pushed to where it goes, and collisions are resolved (softmax splatting).
- **Occlusion / disocclusion:** content that becomes hidden / content that becomes visible. Disoccluded pixels exist in only one input, or in neither.
- **Fusion mask:** a per-pixel weight that chooses between the two warped inputs.
- **Residual:** a learned correction added on top of the warped blend. It makes new pixel values.
- **Ghosting:** a double image from blending two misaligned frames.
- **Co-timed pair:** the A-side and B-side handle frames that the dissolve blends at the same output frame.
- **Endpoint interpolation:** in-betweens generated from two frozen end frames.
- **Co-timed morph / flow-dissolve:** the dissolve with each pair aligned by flow before blending. Proposed here.
- **Forward–backward consistency:** flow A→B followed by flow B→A should return to the start. Where it does not, the flow is unreliable.
- **Keyframe in-betweening / bounded generation:** generating a clip whose first and last frames are given.
- **Time reversal fusion:** fusing a denoising path that starts from the first frame with one that runs backward from the last.
- **Latent diffusion / VAE compression:** generating in a compressed space and decoding to pixels. 1:192 means each latent value stands for 192 pixel values.
- **DDIM steps / distillation:** denoising iterations; a distilled model needs fewer of them.
- **Offload:** keeping model weights in system RAM and moving them to the GPU when needed.
- **GGUF quantisation:** storing weights in 4–8 bits and expanding them at compute time.
- **fp16 storage vs. compute:** storing numbers in 16 bits vs. doing arithmetic in 16 bits. sm_52 can store fp16 but has no fast fp16 arithmetic.
- **SNU-FILM extreme, X-TEST, Xiph 4K:** large-motion interpolation benchmarks. **PSNR** measures pixel fidelity (higher is better); **LPIPS** measures perceptual difference (lower is better).

## Mapping table

| Technique | Heal role | Joins it suits | Lip-sync risk | Exact length by | Preview vs. render | Laptop | Decision touched |
|---|---|---|---|---|---|---|---|
| `dissolve` (current) | Blend co-timed handles | All mid-shot joins | Low: the stronger layer is co-timed | Same K positions | Both | Trivial | None |
| flow-dissolve (DIS or RAFT) | Align, then blend co-timed handles | Small to medium pose change, still camera; also during speech | Low: each layer keeps its own mouth; two mouths overlap near the middle | Same K positions and pairs | Precompute overnight; or preview a plain dissolve | CPU seconds / GPU tens of seconds | #51 wording |
| RIFE co-timed morph | Same as flow-dissolve, with learned flow and mask | As above | Low to medium: the learned mask may favour one side's mouth | Same K positions and pairs | Precompute | GPU seconds | #51 wording; #33 if read broadly |
| RIFE / IFRNet / EMA-VFI endpoint interpolation | Replace K frames with in-betweens of p−h and q+h | Small pose change **inside a pause** (mouth at rest at both ends) | **High during speech:** 250 ms of mouth morphing between two still shapes under running audio | K in-betweens at τ = k/(K+1) | Precompute | GPU seconds to a minute | #33; #13 when motion is large |
| FILM / SGM-VFI / AMT endpoint interpolation | As above, built for large motion | Larger pose change, no speech | High during speech | As above | Precompute (slow) | 0.5–1.5 min per join | #33; #13 |
| ffmpeg `minterpolate` | Block-based endpoint interpolation | Cheap baseline only | High during speech | As above (`scd=none`) | Render | CPU seconds | #33 |
| LTX-Video 2B keyframes | Generate K frames from A and B segments | Experiments only | High: mouths invented, no audio input | Generate 8n+1 frames; keep the middle K | Render only | Minutes per join (est.) | #33, #41 |
| SVD family, Wan, CogVideoX | Generative in-betweening | — | High | As above | — | Hours to days | #33, #41 |
| Morph Cut rules (Adobe, Apple) | **Join classifier**, not a heal | Decides which joins are safe to morph | Their advice: join at word peaks or pauses | — | Analysis | — | None |
| Flow between p and q | **Scoring**: flow magnitude and consistency as join-noticeability features (#50) | All joins | — | — | Analysis | CPU | None |

## Recommendation

**What the research says**
- **The closest competitor to the dissolve is the dissolve itself, aligned.** A flow-dissolve keeps the two things that make today's heal safe: exact length, and a stronger layer that is in sync with the sound. When flow fails, it degrades to the current dissolve.
- **Endpoint interpolation is what Morph Cut, Flow and Smooth Cut do.** Every vendor limits it to small head moves on still backgrounds, with the join placed in a pause. Over a gap of several seconds, it also compresses real motion into 250 ms, which touches #13.
- **Generative in-betweening is out of reach on this laptop, except perhaps LTX-Video 2B.** It invents the mouths, so it is the opposite of #33. Only one talking-head method conditions on speech (Deng et al.), and it has no code.

**Shortlist for a blind bake-off against `dissolve6`**
1. **`flowdissolve6`** — DIS flow (OpenCV) between each co-timed pair, a symmetric warp, the dissolve's α, and a fallback to the plain dissolve where the forward–backward check fails. *Reason:* the smallest step beyond #51; CPU only; keeps the in-sync layer.
2. **`rife6`** — Practical-RIFE 4.25 or 4.26 endpoint interpolation between frames p−h and q+h at τ = k/7. *Reason:* the morph-cut approach with warp-only output, at seconds per join on the 970M.
3. **`rifemorph6`** (optional) — RIFE on the co-timed pairs at τ = α_t. *Reason:* separates the effect of aligning the dissolve from the effect of flow quality (learned vs. DIS).

**Not shortlisted**
- **LTX-Video 2B:** the only feasible generative option. It needs a separate feasibility spike and a decision on #33 first.
- **FILM, SGM-VFI, AMT:** slower. Worth trying only if `rife6` wins on small jumps but fails on larger ones.
- **`minterpolate`:** has the scene-change trap and block artefacts. Usable as a cheap sanity baseline.
- **Everything else in §3:** too slow, or blocked on sm_52.

**How a variant plugs into `prototype/bakeoff.py`** (read, not edited)
- **Register it.** Add the name to `VARIANTS` (line 38). Labels come from `labels = list("ABCDEF")` zipped with `VARIANTS` (lines 163–168). `zip` silently drops any variant beyond six. So either retire the rejected `patch*` and `snap+*` variants, for example `["hard", "dissolve6", "flowdissolve6", "rife6", "rifemorph6"]`, or extend the labels *and* the template's "six different ways … A–F" text in `bakeoff_template.html`.
- **Window size.** `build()` reads K from the digits in the name (`K = … int(digits)`) and sets h = K // 2. `pre` ends at A(p−h) and `post` starts at B(q+h). A new branch beside `dissolve` and `patch` must append exactly K frames to `heal`. Then length and timing match the other variants automatically.
  - Co-timed variants use the same pairs as the dissolve: `A(p - h + 1 + t)`, `B(q - h + t)` and `alpha = (t + 0.5) / K`.
  - Endpoint variants use `A(p - h)` and `B(q + h)` with τ = (t + 1)/(K + 1).
  - The caches cover p−42…p+19 and q−18…q+43, so every frame needed for K ≤ 12 is already decoded.
- **The "snap+" prefix works unchanged.** `snap+flowdissolve6` would shift the pair first.
- **Resolution.** Clips are decoded at `CLIP_W = 640`, about a quarter of 720p's pixels. Bake-off solve times will be roughly 4× lower than the 720p estimates above (*est.*).
- **Audio.** `audio_clip()` is identical for every non-snap variant, so the blind test isolates the picture.
- **Logging.** Return `solve_s`, the mean flow magnitude and the forward–backward error through `info`. It is printed and shown after Reveal, like the patch's `energy` and `ghost`.
- **Loading.** Load any model once, as a global like `cp_feats`, not once per join.
- **Joins.** The earlier bake-off used 11 *Tears of Steel* joins (#58). Lip-sync risk shows up only on joins with visible speech. Add joins from a public-domain dialogue film (#63; *Detour* was used in #65), and record "speech at join" from `words.json` on each card, so the results can be split.
- **Installs (need the user's approval):**
  - `flowdissolve6`: `opencv-python` (Apache-2.0). The `.venv` has numpy and PyMaxflow but no OpenCV or PyTorch ‡.
  - `rife6` / `rifemorph6`, either:
    - PyTorch ≤ 2.14 from the cu126 index, plus the 4.25/4.26 weights from the Practical-RIFE Google Drive links, in its own environment because of the numpy pin; or
    - the rife-ncnn-vulkan binary (TNTwise fork for 4.26), called as a subprocess on PNG pairs with `-s τ`. This needs no PyTorch.

**If a candidate wins (sketch, not a decision)**
- A heal tag beside `dissolve`, for example `flow-dissolve` or `interpolate`, chosen per join from:
  - speech activity at the join (`words.json`; filler cuts land inside speech);
  - the camera residual already computed by phase correlation;
  - flow magnitude and forward–backward consistency between p and q.
- Endpoint interpolation, if allowed at all, would be restricted to joins with no speech in the window.
- Run the SyncNet hard-fail check ([video-and-editing.md](video-and-editing.md) §6) on every healed speech join.

**Preview vs. render**
- Near-real-time preview cannot run flow or VFI live. Either precompute heal frames overnight for every mid-shot join that is final at some slider length, or preview with the plain dissolve and use the new heal only in the render.
- At a few seconds per join, even 1,000 joins take about 1–2 h (*est.*). How many distinct joins a full slider sweep produces is **UNVERIFIED**.

**Decisions this would need (the user's call; listed without preference)**
- **A.** Keep #33 and #51 as written. Flow is used only for scoring. Nothing on the shortlist ships.
- **B.** Read #51 as "a blend of the two co-timed handle frames, which may first be aligned by warping". This admits `flowdissolve` and `rifemorph`. Endpoint interpolation stays out.
- **C.** Also allow warp-only endpoint interpolation (no learned residual, no generative model) at joins without speech. This revisits #33, and #13 for large motion.
- **D.** Allow generative in-betweening in the render. This reverses #33 and #41.
