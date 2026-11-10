# Patching from other times: healing temporal seams with existing pixels

> Part of the [Liquid Retime research survey](README.md) (scan of 2026-11-10).
> Scope: is PatchMatch the right analogue for Liquid Retime, and what is the state of the art in hiding a temporal seam (a jump cut) by borrowing frames or patches from other times instead of cross-dissolving?
>
> **Verification:** ✔ URL fetched and content confirmed. † DOI checked against Crossref (title, authors and venue matched). (s) taken from search results only, or the fetch was blocked. **UNVERIFIED**: could not be confirmed. Runtimes quoted from papers are on the authors' hardware. *Est.* marks an arithmetic estimate for the GTX 970M (sm_52, fp32 only, 6 GB) and i7-6700HQ.
>
> **Status:** carve-only still holds. The one exception is the ~6-frame dissolve at an unavoidable mid-shot join. Items that generate pixels are tagged *(contrast / not used)*.

---

## 0. The problem in patch terms

A mid-shot join butts frame i−1 against frame j+1. The dissolve mixes two co-timed handle streams over K frames: the **A-side** a_t (running on past i−1) and the **B-side** b_t (leading into j+1). Each technique below decides which existing pixels each output pixel shows:

- one frame (a hard cut, or a better pair);
- one global alpha (the dissolve);
- a per-pixel switch time between a_t and b_t (graph-cut transitions);
- averaged, displaced patches (voting, morphing);
- pixels from any time, carried along motion (video completion).

Only the first three use nothing but a_t and b_t.

## 1. PatchMatch

**Barnes, Shechtman, Finkelstein & Goldman 2009** — "PatchMatch: a randomized correspondence algorithm for structural image editing", *ACM TOG* 28(3).
- Links: https://doi.org/10.1145/1531326.1531330 † · https://gfx.cs.princeton.edu/pubs/Barnes_2009_PAR/ ✔
- What it does: computes an approximate **nearest-neighbour field (NNF)**, the offset from each patch in A to its best match in B. It uses random initialisation, propagation of good offsets to neighbours, and random search at shrinking radii; 4–5 iterations suffice. This made Simakov-style retargeting, completion and reshuffling interactive.
- Laptop: Table 1 gives 0.68 s at 0.1 MP and 2.65 s at 0.35 MP on a 2009 CPU, 20–100× faster than kd-trees, with O(M) memory. A GPU variant was ~7× faster. *Est.:* tens of ms per frame pair at the prototype's 160 px, 1–3 s at 720p. The reference code is MATLAB mex under an Adobe non-commercial licence.
- Maps to: **(a)** a join cost and a join classifier (see the Recommendation). It is the search engine inside patch-based heals, not a heal itself. The NNF is analysis only, so it does not affect carve-only.
- Follow-up: Generalized PatchMatch (*ECCV 2010*, https://doi.org/10.1007/978-3-642-15558-1_3 † · https://gfx.cs.princeton.edu/pubs/Barnes_2010_TGP/ ✔) adds k-NN, rotations, scales and arbitrary descriptors, which could ignore grading drift across a join.

**Adobe Content-Aware Fill.**
- Links: Barnes's thesis abstract says PatchMatch shipped in Photoshop CS5 as content-aware fill, https://www.cs.princeton.edu/research/techreps/885 ✔. Weizmann credits its space-time completion too, https://www.wisdom.weizmann.ac.il/~vision/VideoCompletion.html (s). The After Effects video version fills a mask from surrounding frames by estimating the motion behind it, https://helpx.adobe.com/after-effects/desktop/remove-objects-from-your-videos/content-aware-fill.html (s, 403 on fetch).
- Maps to: shows that borrowing from other frames works in production, but only for *spatial holes*.

## 2. Bidirectional similarity and patch-built transitions

**Simakov, Caspi, Shechtman & Irani 2008** — "Summarizing visual data using bidirectional similarity", *CVPR*.
- Links: https://doi.org/10.1109/CVPR.2008.4587842 † · project https://www.wisdom.weizmann.ac.il/~vision/VisualSummary.html (s) · PDF https://legacy-sites.tlt.harvard.edu/~cs278/papers/simakov.pdf ✔
- What it does: defines a distance with two terms. **Completeness** means every source patch has a match in the target. **Coherence** means every target patch came from the source. It synthesises the target iteratively: match patches both ways, then set each pixel to the weighted average of the colours its matched patches vote for.
- **For video, exactly:** with 7×7×5 space-time patches, a ballet clip was summarised to **half its length**, movements still at original speed. Output frames are *re-synthesised* from voted patches, so one frame mixes source times. Temporal cropping used completeness alone to pick the best window. Halving a 250×200 *image* took 5 min in MATLAB.
- Maps to: **(a)** coherence as a join cost (cheap when every space-time patch across the join exists in the source). **(c)** completeness as a **visual-uniqueness** importance feature (a stretch is cheap when its patches survive elsewhere).
- Carve-only: the summariser is *(contrast / not used)*: multi-clock and averaged.

**Shechtman, Rav-Acha, Irani & Seitz 2010** — "Regenerative morphing", *CVPR*.
- Links: https://doi.org/10.1109/CVPR.2010.5540159 † · https://grail.cs.washington.edu/projects/regenmorph (s) · PDF https://grail.cs.washington.edu/projects/regenmorph/regenmorph.cvpr10.pdf ✔
- What it does: builds every in-between frame from small pieces of the two end images. Each frame is made bidirectionally similar to its neighbours and to both sources. It needs no correspondences and ghosts less than a blend.
- Limitations the authors state: some jitter is unavoidable to keep frames sharp, lighting changes are handled poorly, and moving people needed manual correspondences.
- Laptop: no timing published. *Est.:* seconds to a minute per 720p frame on CPU, so render only.
- Maps to: **(b)** the most literal "PatchMatch heal": K in-betweens built only from A and B patches.
- Carve-only: borderline. Voting averages displaced patches into new arrangements. It belongs to the "better synthesis later" slot.

## 3. Shift-maps: a source time per pixel

**Pritch, Kav-Venaki & Peleg 2009** — "Shift-map image editing", *ICCV*.
- Links: https://doi.org/10.1109/ICCV.2009.5459159 † · PDF https://www.cs.huji.ac.il/~peleg/papers/iccv09-shiftmap.pdf ✔
- What it does: labels each output pixel with the shift to its source pixel, solved by multi-label graph cut. With several inputs the label becomes (tx, ty, image index). A hierarchical solve edits 1 MP in a few seconds.
- Maps to: **(b)/(c)** the cleanest formalism for a patch heal. Label each pixel in the window with the source frame it copies. Pixels are copied, never averaged.
- Video follow-up: Hu & Rajan, "Hybrid shift map for video retargeting", *CVPR 2010*, https://mlanthology.org/cvpr/2010/hu2010cvpr-hybrid/ (s).

**Granados, Kim, Tompkin, Kautz & Theobalt 2012** — "Background inpainting for videos with dynamic objects and a free-moving camera", *ECCV*.
- Links: https://doi.org/10.1007/978-3-642-33718-5_49 † · https://vcai.mpi-inf.mpg.de/projects/vidbginp/index.html ✔
- What it does: aligns frames with per-pixel homographies, then picks one source frame per pixel and fuses in the gradient domain. Huang et al. 2016 call this a spatio-temporal shift-map. It takes hours: Newson et al. report 11 h and 90 h for two HD clips.
- Maps to: **(b)** per-pixel source selection survives camera motion only after alignment, and alignment resamples pixels. That makes it a later option.

**Rüegg, Wang, Smolic & Gross 2013** — "DuctTake: spatiotemporal video compositing", *CGF*.
- Links: https://doi.org/10.1111/cgf.12025 † · https://arxiv.org/abs/2101.04772 ✔
- What it does: joins several takes of one scene along motion-compensated 3D graph-cut seams, interactively on HD.
- Maps to: **(b)** the production precedent for stitching two time ranges of a shot along a seam instead of blending.

## 4. Video completion and inpainting

These fill a *spatial hole* from other frames. A jump cut has no hole, so they mainly show what borrowing costs and where it stops being copying.

**Patch-based completion**
- **Wexler, Shechtman & Irani**, *CVPR 2004* (https://doi.org/10.1109/CVPR.2004.1315022 †) and *TPAMI 2007* (https://doi.org/10.1109/TPAMI.2007.60 †). Fills holes with space-time patches under a global coherence objective.
- **Newson et al. 2014**, "Video inpainting of complex scenes", *SIAM J. Imaging Sci.* (https://doi.org/10.1137/140954933 † · https://arxiv.org/abs/1503.05528 ✔ · MATLAB https://sites.google.com/site/alasdairnewson/research/video_inpainting ✔). Rebuilds Wexler on **3D PatchMatch**: the search drops from 985 s to 50 s, and a 1120×754×200 clip takes 44 min.
- **Huang, Kang, Ahuja & Kopf 2016**, *ACM TOG* (https://doi.org/10.1145/2980179.2982398 † · PDF https://microsoft.com/en-us/research/wp-content/uploads/2017/01/SigAsia_2016_VideoCompletion.pdf ✔). Solves flow and colour jointly, taking ~3 h for 854×480×90 frames on a quad-core 2.8 GHz i7.
- Maps to: **(a)** space-time PatchMatch is affordable offline. Otherwise it is the wrong problem.

**Learned flow-guided inpainting** *(contrast / not used)*
- **FGVC** (Gao et al., *ECCV 2020*): https://arxiv.org/abs/2009.01835 ✔ · https://doi.org/10.1007/978-3-030-58610-2_42 † · https://github.com/vt-vl-lab/FGVC ✔ (MIT). Propagates pixels along completed flow, including from distant frames. Pixels no frame saw come from an image-inpainting network.
- **E2FGVI** (Li et al., *CVPR 2022*): https://arxiv.org/abs/2204.02663 ✔ · https://doi.org/10.1109/CVPR52688.2022.01704 † · https://github.com/MCG-NKU/E2FGVI ✔ (CC BY-NC). 0.12 s per frame at 432×240 on a Titan XP; needs mmcv-full.
- **ProPainter** (Zhou et al., *ICCV 2023*): https://arxiv.org/abs/2309.03897 ✔ · https://doi.org/10.1109/ICCV51070.2023.00961 † · https://github.com/sczhou/ProPainter ✔ (non-commercial). Its README lists fp32 memory of 3 GB at 320×240 and 28 GB at 1280×720 (50 frames).
- Laptop (*est.*): ProPainter fits only at about 320×240; E2FGVI runs about 4–5× slower than on the Titan XP. There is no fast fp16 on Maxwell.
- Carve-only: propagation is copying, but hallucination is not.

**Diffusion inpainting and in-betweening, 2024–2025** *(contrast / not used)*
- **DiffuEraser** (https://arxiv.org/abs/2501.10018 · https://github.com/lixiaowen-xw/DiffuEraser ✔): needs 12 GB at 640×360.
- **VideoPainter** (https://arxiv.org/abs/2503.05639 ✔): 44.7 GB in MiniMax-Remover's comparison table (s).
- **MiniMax-Remover** (https://arxiv.org/abs/2505.24873 ✔): 8.2 GB at 360p on an A800 (s).
- **Generative Inbetweening** (Wang et al., *ICLR 2025*, https://arxiv.org/abs/2408.15239 ✔): generates the frames between two keyframes, which is the generative way to heal a jump cut.
- Laptop: none fits 6 GB fp32 (*est.*). All of them generate pixels.

## 5. Transitions between non-adjacent frames

**Schödl, Szeliski, Salesin & Essa 2000** — "Video textures", *SIGGRAPH* (see [video-and-editing.md](video-and-editing.md) §5).
- Links: https://doi.org/10.1145/344779.345012 † · https://sites.cc.gatech.edu/gvu/perception/projects/videotexture/index.html ✔
- What it does: jumps from i to j where a dynamics-filtered D(i,j) is low, and hides the jump by crossfade or morph (s). Kwatra et al. note that these transitions look intermittently blurred, which is the dissolve's weakness.
- Maps to: **(a)** this is the prototype's D. It adds **best-pair snap**: search ±k frames around both seam edges for the lowest-D pair.

**Kwatra, Schödl, Essa, Turk & Bobick 2003** — "Graphcut textures: image and video synthesis using graph cuts", *ACM TOG* 22(3):277–286.
- Links: https://doi.org/10.1145/882262.882264 † · https://cpl.cc.gatech.edu/projects/graphcuttextures ✔ · PDF https://faculty.cc.gatech.edu/~turk/my_papers/graph_cuts.pdf ✔
- What it does (§7A): takes a video-texture jump and cuts a minimum-cost seam *surface* through a 60-frame space-time window around it. In the paper's terms, this sets the transition time per pixel rather than per frame. Frames outside the window are untouched, and seams are feathered or blended with multiresolution splines.
- Laptop (*est.*): under 1 s per join on CPU for a graph cut at 320×180×K.
- Maps to: **(b)** **this is the patch heal.** Each pixel shows the A-side or the B-side at the same output time and switches once, where the two sides agree best.
- Carve-only: yes in substance. It is a dissolve whose alpha is 0 or 1 per pixel, drawn from the same two handle frames, plus a few feathered pixels.
- Same family: Agarwala et al. 2005, "Panoramic video textures" (https://doi.org/10.1145/1073204.1073268 †), solves per-pixel time offsets by graph cut.

**Liao, Joshi & Hoppe 2013** — "Automated video looping with progressive dynamism"; **Liao, Finch & Hoppe 2015** — "Fast computation of seamless video loops". Both in *ACM TOG*.
- Links: https://doi.org/10.1145/2461912.2461950 † · https://hhoppe.com/proj/videoloops/ ✔ · https://doi.org/10.1145/2816795.2818061 † · https://hhoppe.com/proj/fastloops/ ✔
- What it does: gives each pixel its own loop start time and period, solved by α-expansion graph cuts over spatial and temporal consistency.
- Runtime: 2013 needed 8–10 min for 5 s at 960×540, with HD made by upsampling the labels. 2015 needs ~7 s for 5 s of Full HD, using masked and coarse-grid graph cuts, label pruning and coarse Poisson blending.
- Maps to: **(b)** the engineering recipe for the patch heal: low-resolution labels, upsampled, then gradient-domain blending.

**Berthouzoz, Li & Agrawala 2012** — hidden transitions for interview video.
- Links: https://doi.org/10.1145/2185520.2185563 · Agrawala's slides https://magrawala.github.io/cs448v-sp20/assets/slides/Lec14.pdf ✔
- What it does: finds the shortest path through a hierarchical graph of raw-footage frames (face-landmark and HOG distances), then optical-flow-interpolates between the path frames. The number of in-betweens comes from D(i,j).
- Maps to: **(b)** **bridge frames**. Keeping a few in-order frames from the removed span that step from A's pose to B's is carve-only. It is a non-contiguous removal, so the existing "drop frames only if unnoticeable" rule governs it, and it must stay off visible speaking lips. The flow part is not used.

**Others**
- Cinemagraph tools pick a frozen or looping time per region: Tompkin et al. 2011 (https://doi.org/10.1109/CVMP.2011.16 †), Bai et al. 2012 (https://doi.org/10.1145/2185520.2185562 †), Cliplets 2012 (https://doi.org/10.1145/2380116.2380149 †). Low relevance.
- Hirai 2017, "Seamless video scene transition using hierarchical graph cuts" (https://doi.org/10.1145/3145690.3145703 †). Abstract not seen, so the content is **UNVERIFIED**.
- Wang et al. 2024, jump-cut smoothing (https://arxiv.org/abs/2401.04718) synthesises in-betweens *(not used)*.
- No 2024–2026 work was found that heals jump cuts by copying patches. Recent work is generative.

---

## Terminology

- **NNF:** for each patch, the offset of its best match in another image.
- **Bidirectional similarity:** completeness (nothing lost) plus coherence (nothing new).
- **Patch voting:** averaging overlapping matched patches. This creates new pixel values.
- **Shift-map:** a per-pixel label naming the source location and frame to copy.
- **α-expansion graph cut:** min-cut optimisation of pixel labels with a smoothness cost.
- **Switch-time map:** the frame at which each pixel changes from the A-side to the B-side.
- **Flow-guided propagation vs. hallucination:** copying pixels along motion vs. generating the rest.
- **Heal window, A-side, B-side:** the K frames around a join, and the two handle streams they draw on.
- **Patch heal, best-pair snap, bridge frames, jump-cut index:** proposed here; see the Recommendation.

## Mapping table

| Technique | (a) Scoring | (b) Healing | (c) Strategy | Laptop | Carve-only? |
|---|---|---|---|---|---|
| PatchMatch / GPM | NNF cost, jump-cut index | Engine only | — | ms at 160 px (*est.*) | Yes (analysis) |
| Simakov BDS | Coherence, uniqueness | — | Summarisation (rejected) | Offline, low-res | No (output) |
| Regenerative morphing | — | Patch-built in-betweens | Future `morph` | Render only | Borderline |
| Shift-map, Granados, DuctTake | — | Per-pixel source frame | Formalism for `patch` | Seconds to hours | Yes, unwarped |
| Wexler, Newson, Huang | Offline feasibility | Holes only | — | Minutes to hours | Wrong problem |
| FGVC, E2FGVI, ProPainter | — | Holes only | — | ≤ 320×240 | No |
| Diffusion inpainting / in-betweening | — | Generative heal | Future synthesis | No | No |
| Video textures | D(i,j), snap | Crossfade | Pre-step | In prototype | Yes |
| Graphcut textures §7A, panoramic VT | Seam energy | Switch-time map | **`patch`** | < 1 s per join (*est.*) | Yes (heal window) |
| Liao 2013/2015 | — | Low-res labels + Poisson | `patch` engineering | Seconds | Yes |
| Berthouzoz | D-timed | Frame path (+ flow) | `bridge` | Cheap | Yes, without flow |

## Recommendation

**Is PatchMatch the right analogue? As a tool, not as the analogue.** PatchMatch answers "does this patch exist elsewhere?" quickly. Its retargeting is the *other* branch from seam carving: content is re-synthesised by voting rather than removed, and in video that becomes multi-clock. The analogue for healing a temporal seam with existing pixels is the **graph-cut video transition** (Kwatra §7A, Liao, shift-maps). Seam carving's forward energy prices the new adjacency; a graph-cut transition minimises that adjacency pixel by pixel inside the heal window.

**Use PatchMatch for scoring, as a jump-cut index.** Compute the NNF between i−1 and j+1 at 160 px.
- High D with a low patch distance means the same content, displaced: the jump cut the user found jarring.
- High D with a high patch distance means new content. It reads as a cut and dissolves well.
- The offset field separates a camera jump (global) from subject motion (local).

Run it only on shortlisted mid-shot joins, because there are millions of candidate joins (*est.*).

**`patch` (the reserved strategy):**
- **Window:** the same K frames and handles as `dissolve`, so length and A/V sync do not change. Audio keeps its crossfade.
- **Solve:** a switch-time map s(x) ∈ {0…K} by α-expansion at ~320×180.
  - Temporal cost: |a_s(x) − b_s(x)|.
  - Spatial cost: Kwatra's seam cost between neighbours that switch at different times.
  - Constraint: face and person masks switch as one unit, so there are no composite faces.
- **Render:** a_t(x) while t < s(x), otherwise b_t(x). Feather the map by 2–3 px; Poisson blending can follow later.
- **Variant:** patch for the background plus a *local* dissolve inside the region that differs. Conversation jump cuts usually differ mainly in the face.
- **Choose `patch` when** the join is mid-shot, the camera residual from the existing phase correlation is about 0, the a_t/b_t difference is spatially sparse, and the graph-cut energy is well below the dissolve's ghosting energy (mean |a_t − b_t| at mid-alpha).
- **Otherwise:**
  - `trim-at-cut` always comes first.
  - `hard` for near-identical frames.
  - `dissolve` when the camera moves or the change is global (light, framing).
  - **Best-pair snap** runs before any strategy.
- **Decision needed:** word the dissolve exception as "inside a heal window, each output pixel weights the two co-timed handle frames". `patch` then fits inside it.

**Preview vs. render:**
- **Near-real-time preview:** `hard`, `dissolve` and a *precomputed* `patch` cost the same, a per-pixel choice between two decoded frames. A map is ~58 KB per join.
- **Overnight:** the jump-cut index, plus switch-time maps for every mid-shot join that is final at any slider length.
- **Render only:** full-resolution refinement, Poisson blending, regenerative morphs.
- **Not used:** inpainting and diffusion.

**Next experiment: a patch vs. dissolve bake-off on *Tears of Steel*.**
1. Collect every `dissolve` or `hard` join in the 90/75/60/30% renders (~70, fewer distinct).
2. Render 3 s clips for each: hard, 6-frame dissolve, `patch` with K=6, `patch` with K=12, and `patch` with a local dissolve. Render each again after best-pair snap (±6 frames).
3. Use numpy plus PyMaxflow's α-expansion (https://github.com/pmneila/PyMaxflow ✔). Compute costs on grey 320×180 frames and render in colour.
4. Log per join: graph-cut energy, ghost energy, D, the jump-cut index, and solve time.
5. Rank the variants blind in the viewer. Adopt `patch` if it beats the dissolve on most static-camera joins without composite faces, and fit the selection rule to the logged energies.
