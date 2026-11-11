# Prior art: video, retargeting and film editing

> Part of the [Scene Carving research survey](README.md) (scan of 2026-11-10).
> Scope: the visual, video and film-editing side of shortening a finished film while keeping one clock per frame, using no synthesized pixels, and preserving the director's rhythm.
>
> **Verification:** every URL came from a search result or a direct fetch. † means the DOI was also checked against Crossref (title, authors and venue matched). **UNVERIFIED** marks claims found only in secondary sources. The Adobe Morph Cut help page appears in search results but returned 403 when fetched.
>
> **Status for Scene Carving:** some items below are recorded for contrast only, because the [decisions](../DECISIONS.md) rule them out. Those are frame interpolation, morph cuts, multi-clock seams and subject speed-up. They are tagged *(contrast / not used)*.

---

## 1. Seam carving and its descendants

**Avidan & Shamir 2007** — "Seam carving for content-aware image resizing", *ACM TOG* 26(3), SIGGRAPH 2007.
- Links: https://doi.org/10.1145/1276377.1276390 † · project page https://faculty.runi.ac.il/arik/site/seam-carve.asp
- What it does: removes the lowest-energy 8-connected path using dynamic programming. Its "multi-size image" index map stores the order in which seams are removed, so any size can be produced instantly.
- **Borrow:** precompute one global *removal order* to get a multi-length film. Any runtime is then a threshold on that order, and the escalation from micro-trim to scene cut follows from it.

**Rubinstein, Shamir & Avidan 2008** — "Improved seam carving for video retargeting", *ACM TOG* 27(3).
- Links: https://doi.org/10.1145/1360612.1360615 · https://faculty.runi.ac.il/arik/site/seam-video.asp
- What it does: introduces **forward energy**, the cost of the new adjacencies a removal creates, and graph-cut seams through the space-time volume.
- **Borrow:** this is our *noticeability*. A temporal removal costs the discontinuity between the new neighbours (frame i−1 butted against frame j+1), not the energy of the removed material.

**Rubinstein, Shamir & Avidan 2009** — "Multi-operator media retargeting", *ACM TOG* 28(3).
- Link: https://doi.org/10.1145/1531326.1531329
- What it does: mixes crop, scale and seam carving, and uses dynamic programming to choose the operator sequence under one image-distance measure.
- **Borrow:** price micro-trim, tail trim, line lift, scene drop and camera-move frame drops on one perceptual scale.

**Shamir & Sorkine 2009** — "Visual media retargeting", *SIGGRAPH Asia Courses*.
- Link: https://doi.org/10.1145/1665817.1665828 †
- A survey course. It shows the field has been almost entirely *spatial* (aspect ratio), which is useful for positioning Scene Carving.

**Rubinstein, Gutierrez, Sorkine & Shamir 2010** — "A comparative study of image retargeting" (RetargetMe), *ACM TOG* 29(6).
- Links: https://doi.org/10.1145/1882261.1866186 † · https://people.csail.mit.edu/mrub/retargetme/
- What it found: in a paired-comparison user study of 8 methods, automatic metrics predicted human preference poorly.
- **Borrow:** use it as the evaluation template. Claiming the shortening goes unnoticed will require human studies.

## 2. Temporal retargeting and video condensation

**Rav-Acha, Pritch, Lischinski & Peleg 2005** — "Dynamosaics: Video mosaics with non-chronological time", *CVPR*.
- Links: https://doi.org/10.1109/CVPR.2005.137 · https://vision.huji.ac.il/dynmos
- What it does: sweeps "time fronts" through an aligned space-time volume using a 4D min-cut.
- *(contrast / not used)* This was the first time-domain carving, but each output frame mixes input times, which breaks *one clock per frame*.

**Pritch, Rav-Acha & Peleg 2008** — "Nonchronological video synopsis and indexing", *IEEE TPAMI* 30(11).
- Links: https://doi.org/10.1109/TPAMI.2008.29 · precursor "Making a long video short", *CVPR 2006*, https://doi.org/10.1109/CVPR.2006.179
- What it does: shifts "activity tubes" in time so that events from different times play together.
- *(contrast / not used)* It is built for surveillance and gives up chronology. The transferable idea is an activity-tube energy.

**Li, Ishwar & Konrad 2009** — "Video condensation by ribbon carving", *IEEE TIP* 18(11):2572–2583.
- Link: https://doi.org/10.1109/TIP.2009.2026677 †
- What it does: carves "ribbons", seams in (x or y, t), using an activity-aware cost, dynamic programming, and a sliding window for streams.
- **Closest prior "temporal seam carving".** Borrow the activity cost, the dynamic programming and the streaming window. Scene Carving restricts ribbons to *flat, full-frame* removal, the degenerate case of ribbon carving.

**Chen & Sen 2008** — "Video carving", *Eurographics Short Papers*.
- Links: https://doi.org/10.2312/egs.20081022 · PDF https://web.ece.ucsb.edu/~psen/Papers/EG08_VideoCarving.pdf
- What it does: carves 2D "sheets" out of the x-y-t volume with min-cut.
- *(contrast / not used)* Like ribbon carving, it mixes times within a frame.

**Lu, Cole, Dekel, Xie, Zisserman, Salesin, Freeman & Rubinstein 2020** — "Layered neural rendering for retiming people in video", *ACM TOG* 39(6), SIGGRAPH Asia.
- Link: https://arxiv.org/abs/2009.07833
- What it does: splits a video into per-person RGBA layers so each person can be sped up, slowed down or frozen.
- *(contrast / not used)* This is exactly the subject-time distortion Scene Carving forbids.

## 3. Content-aware fast-forward and adaptive playback speed

**Peker & Divakaran 2004** — "Adaptive fast playback-based video skimming using a compressed-domain visual complexity measure", *ICME*.
- Link: https://www.merl.com/publications/TR2004-060
- An earlier ICIP 2001 "constant pace" paper has DOI 10.1109/ICIP.2001.958139 according to one index (**UNVERIFIED**).
- What it does: a visual-complexity measure (motion plus texture) sets the maximum speed that stays within perceptual limits.
- **Borrow:** a perceptual-limit model to gate camera-move frame drops. *(contrast)* It also speeds up subjects.

**Petrovic, Jojic & Huang 2005** — "Adaptive video fast forward", *Multimedia Tools and Applications* 26(3):327–344.
- Link: https://doi.org/10.1007/s11042-005-0895-9 †
- What it does: sets speed from the likelihood of each frame under a generative model of a query clip. Importance is driven by a query, not by plot.

**Cheng, Luo, Chen & Chu 2009** — "SmartPlayer: User-centric video fast-forwarding", *CHI '09*, 789–798.
- Link: https://doi.org/10.1145/1518701.1518823
- What it does: adapts speed to semantic events and to learned user preference, and skips nothing.
- *(contrast)* It accelerates footage rather than removing it.

**Kopf, Cohen & Szeliski 2014** — "First-person hyper-lapse videos", *ACM TOG* 33(4):78.
- Links: https://doi.org/10.1145/2601097.2601195 † · https://www.microsoft.com/en-us/research/publication/first-person-hyperlapse-videos/
- What it does: reconstructs the scene in 3D and re-renders a smoothed camera path.
- *(contrast / not used)* It synthesizes pixels.

**Joshi, Kienzle, Toelle, Uyttendaele & Cohen 2015** — "Real-time hyperlapse creation via optimal frame selection", *ACM TOG* 34(4).
- Link: https://www.microsoft.com/en-us/research/publication/real-time-hyperlapse-creation-via-optimal-frame-selection/ (DOI 10.1145/2766954 via Scilit)
- What it does: dynamic programming over frame-to-frame transition costs, plus penalties for deviating from the target speed-up and for changing speed.
- **Most directly reusable algorithm.** Choosing which frames to keep becomes a shortest-path problem: the edge cost is forward energy, the speed-up term is the target length, and the acceleration penalty preserves rhythm.

**Poleg, Halperin, Arora & Peleg 2015** — "EgoSampling: Fast-forward and stereo for egocentric videos", *CVPR*.
- Link: https://arxiv.org/abs/1412.3596
- What it does: treats frame sampling as a shortest-path or energy-minimization problem solvable in polynomial time. It confirms the graph formulation.

**Silva, Ramos, Ferreira, Chamone, Campos & Nascimento 2018** — "A weighted sparse sampling and smoothing frame transition approach for semantic fast-forward first-person videos", *CVPR*.
- Link: https://arxiv.org/abs/1802.08722
- What it does: weights the sampling density by semantic scores and smooths the transitions.
- **Borrow:** importance-weighted keep-rates.

**Lan, Panda, Zhu & Roy-Chowdhury 2018** — "FFNet: Video fast-forwarding via reinforcement learning", *CVPR*.
- Link: https://arxiv.org/abs/1805.02792
- What it does: a reinforcement-learning agent decides online how far to skip. It optimizes coverage of important frames, not invisibility, so it is of low relevance.

## 4. Summarization, skimming and trailers

**Smith & Kanade 1997** — "Video skimming and characterization through the combination of image and language understanding techniques", *CVPR*.
- Link: https://doi.org/10.1109/CVPR.1997.609414 †
- What it does: produces skims at up to 20:1 from image cues plus transcript keywords. It is the earliest multi-layer skim.
- *(contrast)* It compresses extremely and tolerates choppiness.

**Ma, Lu, Zhang & Li 2002** — "A user attention model for video summarization", *ACM Multimedia*.
- Links: https://doi.org/10.1145/641007.641116 † · extended version *IEEE TMM* 2005, DOI 10.1109/TMM.2005.854410
- What it does: fuses visual, audio and linguistic attention into a single attention curve.
- **Direct precedent for the multi-layer score map**, but its notion of attention is salience, not plot.

**Gygli, Grabner, Riemenschneider & Van Gool 2014** — "Creating summaries from user videos" (SumMe), *ECCV*.
- Link: https://doi.org/10.1007/978-3-319-10584-0_33 †

**Song, Vallmitjana, Stent & Jaimes 2015** — "TVSum", *CVPR*.
- Link: https://openaccess.thecvf.com/content_cvpr_2015/html/Song_TVSum_Summarizing_Web_2015_CVPR_paper.html
- SumMe and TVSum are importance benchmarks built on short user and web videos. Their domain and compression level are wrong for us, so they serve only as sanity checks.

**Lee, Gong & Cho 2025** — "Video summarization with large language models" (LLMVS), *CVPR*.
- Link: https://arxiv.org/abs/2504.11199
- What it does: a multimodal LLM captions frames, an LLM scores importance from nearby captions, and global attention refines the scores.
- **Borrow:** a template for the importance layer using local models.

**Papalampidi, Keller & Lapata 2019** — "Movie plot analysis via turning point identification" (TRIPOD), *EMNLP*.
- Links: https://arxiv.org/abs/1908.10328 · follow-up "Movie summarization via sparse graph construction", *AAAI 2021*, https://arxiv.org/abs/2012.07536
- What it does: annotates turning points for 99 films, projects them onto screenplay scenes, and detects them with multimodal graphs.
- **Borrow:** turning points as plot anchors with very high importance, plus priors on act structure.

**Smith, Joshi, Huet, Hsu & Cota 2017** — "Harnessing A.I. for augmenting creativity: Application to movie trailer creation" (IBM / *Morgan*), *ACM MM*.
- Links: https://doi.org/10.1145/3123266.3127906 · PDF https://www.eurecom.fr/publication/5344/download/data-publi-5344.pdf
- What it does: audio-visual sentiment and scene analysis proposed 10 moments, and a human editor cut the trailer from them. A precedent for mood scoring.
- *(contrast)* It picks the top moments, whereas we remove the bottom ones.

**Argaw, Soldan, Pardo, Zhao, Caba Heilbron, Chung & Ghanem 2024** — "Towards automated movie trailer generation", *CVPR*.
- Link: https://arxiv.org/abs/2404.03477
- What it does: a Trailer Generation Transformer selects and *reorders* shots as a sequence-to-sequence task.
- *(contrast)* It reorders; Scene Carving keeps chronology.

**Bain, Nagrani, Brown & Zisserman 2020** — "Condensed Movies: Story based retrieval with contextual embeddings", *ACCV*.
- Link: https://arxiv.org/abs/2005.04208
- What it is: key scenes from more than 3,000 films, with descriptions.
- **Borrow:** a prior on which scenes people consider key, usable as positive examples for importance.

**Soldan et al. 2022** — "MAD: A scalable dataset for language grounding in videos from movie audio descriptions", *CVPR*.
- Link: https://arxiv.org/abs/2112.00431
- What it is: 384K audio-description sentences aligned to 1,200 hours of film.
- **Borrow:** audio-description-style captions as a dense narrative signal that a local LLM can score.

## 5. Computational editing and hiding cuts

**Berthouzoz, Li & Agrawala 2012** — "Tools for placing cuts and transitions in interview video", *ACM TOG* 31(4):67.
- Link: https://doi.org/10.1145/2185520.2185563
- What it does: places cuts from the transcript, scores how seamless each cut is from face and frame similarity, hides transitions with optical-flow interpolation, and inserts pauses where a cut cannot be hidden.
- **Core noticeability model for line lifts.** *(not used: the interpolation part — carve-only)* It also works only on a single talking head in raw footage.

**Leake, Davis, Truong & Agrawala 2017** — "Computational video editing for dialogue-driven scenes", *ACM TOG* 36(4).
- Links: https://doi.org/10.1145/3072959.3073653 · https://graphics.stanford.edu/papers/roughcut
- What it does: encodes film idioms (keep the speaker visible, avoid jump cuts, control pace) as HMM costs over multiple takes.
- **Borrow:** the idioms as soft constraints when lifting lines or beats. *(contrast)* It assembles a cut from raw takes, whereas we trim a locked master.

**Truong, Berthouzoz, Li & Agrawala 2016** — "QuickCut: An interactive tool for editing narrated video", *UIST*.
- Links: https://doi.org/10.1145/2984511.2984569 † · https://vis.berkeley.edu/papers/quickcut
- What it does: dynamic programming picks frame-accurate cut points that respect narration sync and film rules.
- **Borrow:** refine cut points after deciding what to remove.

**Adobe Premiere Pro Morph Cut (2015)**
- Link: https://helpx.adobe.com/premiere/desktop/add-video-effects/apply-video-transitions/apply-morph-cut-to-smoothen-jump-cuts.html (search-indexed; direct fetch returned 403)
- What it does: works best on a fixed, single-subject talking head. It fails with background motion, hand movement, or a lot of head motion.
- *(not used — synthesizes frames)* Adobe's list of failure cases is still a ready-made specification for an "unsafe join" classifier.

**Wang, Park, Zhou, Shechtman & Zhang 2024** — "Jump cut smoothing for talking heads", arXiv.
- Link: https://arxiv.org/abs/2401.04718
- What it does: interpolates facial keypoints and synthesizes frames with an image-translation network, handling head rotation better than FILM. *(not used — synthesis)*

**Reda et al. 2022** — "FILM: Frame interpolation for large motion", *ECCV*.
- Links: https://arxiv.org/abs/2202.04901 · https://film-net.github.io

**Huang et al. 2022** — "RIFE: Real-time intermediate flow estimation", *ECCV*.
- Link: https://arxiv.org/abs/2011.06294
- *(not used — synthesis)* FILM and RIFE invent motion, so they would conflict with "never synthesize frames".

**Schödl, Szeliski, Salesin & Essa 2000** — "Video textures", *SIGGRAPH*.
- Links: https://doi.org/10.1145/344779.345012 † · https://sites.cc.gatech.edu/gvu/perception/projects/videotexture/index.html
- What it does: builds a frame-distance matrix D(i,j), filtered to preserve dynamics, to find invisible loop points.
- **The cleanest noticeability primitive.** Used in reverse, any pair (i, j) with a low D is a jump nobody sees. We use it only to *score* joins, never to loop footage.

**Davis & Agrawala 2018** — "Visual rhythm and beat", *ACM TOG* 37(4).
- Link: https://doi.org/10.1145/3197517.3201371 †
- What it does: extracts "visual beats" from motion.
- **Borrow:** a measurable rhythm signal to preserve and to align cuts to. *(contrast)* The paper warps motion to fit music, which we forbid.

## 6. Shot and scene structure, speakers and lip-sync

**Souček & Lokoč 2020** — "TransNet V2", arXiv.
- Link: https://arxiv.org/abs/2008.04838

**PySceneDetect** (BSD-3)
- Link: https://www.scenedetect.com/
- Both detect cuts and gradual transitions, and both run locally. They define shot heads and tails, and fades.

**Rao et al. 2020** — "A local-to-global approach to multi-modal movie scene segmentation", *CVPR* (MovieScenes: 21K scenes, 150 films).
- Link: https://openaccess.thecvf.com/content_CVPR_2020/html/Rao_A_Local-to-Global_Approach_to_Multi-Modal_Movie_Scene_Segmentation_CVPR_2020_paper.html

**Huang et al. 2020** — "MovieNet", *ECCV*.
- Link: https://arxiv.org/abs/2007.10937
- Rao et al. and MovieNet give us the scene level of the seam hierarchy.

**Tao et al. 2021** — "Is someone speaking?" (TalkNet), *ACM MM*.
- Link: https://arxiv.org/abs/2107.06592

**Liao et al. 2023** — "A light weight model for active speaker detection" (Light-ASD, about 1M parameters), *CVPR*.
- Link: https://arxiv.org/abs/2303.04439
- TalkNet and Light-ASD tell us when an audio edit would be visible on someone's lips. That defines the **sync-critical** layer.

**Chung & Zisserman 2016** — "Out of time: automated lip sync in the wild" (SyncNet), *ACCV Workshops*.
- Link: https://doi.org/10.1007/978-3-319-54427-4_19 †
- What it does: measures the audio-video offset and a confidence score.
- **Use as the hard-fail validator:** every on-screen speaking segment near an edit must show no offset.

## 7. Perception and film theory

**Smith & Henderson 2008** — "Edit blindness", *Journal of Eye Movement Research* 2(2).
- Link: https://doi.org/10.16910/jemr.2.2.6
- What it found: about a quarter of same-scene cuts went undetected, and about a third when the cut coincided with a sudden onset of motion. Cuts that follow continuity rules are missed more often.
- **Borrow:** place removals at motion onsets and matched action, and use this detection protocol in user tests.

**Smith & Mital 2013** — "Attentional synchrony…", *Journal of Vision* 13(8):16.
- Link: https://doi.org/10.1167/13.8.16 †

**Mital, Smith, Hill & Henderson 2011** — *Cognitive Computation* 3(1).
- Link: https://doi.org/10.1007/s12559-010-9074-z
- What they found: motion and flicker predict where viewers' gaze clusters.
- **Borrow:** weight the cost of a discontinuity by predicted gaze. Discontinuities outside the attended region are cheap.

**Smith 2012** — "The attentional theory of cinematic continuity", *Projections* 6(1).
- Link: https://doi.org/10.3167/proj.2012.060102
- Explains match-on-action, shot/reverse-shot and the 180° rule in terms of attention. A theoretical basis for the cut-cost features.

**Magliano & Zacks 2011** — "The impact of continuity editing in narrative film on event segmentation", *Cognitive Science* 35(8).
- Link: https://doi.org/10.1111/j.1551-6709.2011.01202.x
- What it found: breaks in action drive perceived event boundaries much more than breaks in space or time.
- **Borrow:** removing time *between* events is cheap; removing it *inside* an action is expensive.

**Murch, *In the Blink of an Eye*** — Silman-James, 1992; 2nd ed. 2001.
- Link: https://en.wikipedia.org/wiki/In_the_Blink_of_an_Eye_(Murch_book)
- The **Rule of Six** weights a cut by emotion 51%, story 23%, rhythm 10%, eye-trace 7%, 2D screen plane 5% and 3D space 4% (percentages from secondary sources, **UNVERIFIED** against the book). Murch also argues for cutting on the blink.
- **Borrow:** emotion and story map to *importance*; rhythm, eye-trace and the two spatial terms map to *noticeability*.

**Cutting, DeLong & Nothelfer 2010** — "Attention and the evolution of Hollywood film", *Psychological Science*.
- Link: https://doi.org/10.1177/0956797610361679
- What it found: across 150 films from 1935 to 2005, sequences of shot lengths become increasingly 1/f-like.
- **Borrow:** a quantitative signature of the director's rhythm. Check that the shot-length spectrum survives the edit.

**Cutting et al. 2011** — "Quicker, faster, darker", *i-Perception* 2(6).
- Link: https://doi.org/10.1068/i0441aap †

**Cutting 2016** — "The evolution of pace in popular movies", *Cognitive Research: Principles and Implications*.
- Link: https://doi.org/10.1186/s41235-016-0029-0
- Both profile shot duration, motion and luminance across a film's runtime.
- **Borrow:** a constraint that preserves the pacing profile over runtime, plus era-aware priors.

**Cinemetrics**
- Link: https://cinemetrics.uchicago.edu/
- A crowd-sourced database of shot timings (ASL, MSL, full distributions). For *2001*, secondary sources report about 600 shots and an ASL of about 13 s (**UNVERIFIED** against the Cinemetrics record).

**Bordwell 2002** — "Intensified continuity", *Film Quarterly* 55(3).
- Link: https://doi.org/10.1525/fq.2002.55.3.16
- Modern films are cut tighter, so expect less slack to remove invisibly than in films from the 1960s.

**Pezzotta 2017** — "Slowness and time expansion in long takes: *2001*, *Barry Lyndon*, *Eyes Wide Shut*", *Cinergie* 12.
- Link: https://doi.org/10.6092/issn.2280-9481/7340
- Argues that *2001*'s long, near-silent takes stretch "expressed time" on purpose.
- **North-star warning:** low motion and no dialogue do *not* mean low importance.

---

## Terminology (video and editing)

- **Retargeting (spatial / temporal):** changing a medium's dimensions (frame size, or duration) while preserving its content.
- **Seam carving / liquid rescale:** repeatedly removing the lowest-energy connected path.
- **Backward energy:** the energy of the removed pixels.
- **Forward energy:** the energy of the new adjacencies the removal creates.
- **Seam ordering / multi-size media:** an index map that stores the removal order, so any target size can be produced.
- **Multi-operator retargeting:** an optimized sequence that mixes operators such as crop, scale and carve.
- **Video condensation:** shortening by removing low-activity space-time regions (ribbons, sheets).
- **Video synopsis:** non-chronological condensation that shifts activity tubes in time.
- **Adaptive fast-forward / constant-pace skimming:** playback speed that varies inversely with the information rate.
- **Hyperlapse / optimal frame selection:** choosing a subset of frames to hit a target speed-up while keeping motion smooth.
- **Semantic fast-forward:** frame sampling weighted by semantic relevance.
- **Video skim vs. keyframe storyboard:** a moving excerpt vs. a set of still frames.
- **Turning point (TP):** a plot event that marks a narrative act boundary.
- **Shot / scene / sequence / beat:** one continuous take; one continuous time and place; a group of scenes; the smallest dramatic unit.
- **Hard cut vs. gradual transition:** an instant change vs. a dissolve, fade or wipe.
- **Head / tail / handles:** a shot's start and end; extra frames beyond the in and out points.
- **Lift vs. extract (ripple delete):** removing material and leaving a gap, vs. removing it and closing the gap.
- **Lifting a line / tightening:** removing dialogue; trimming pauses inside a scene.
- **Jump cut:** a cut between two near-identical framings of the same subject, which reads as a skip in time.
- **Continuity editing / 180° rule / match on action:** conventions that hide cuts by keeping space, direction and action consistent.
- **J-cut / L-cut (split edit):** the audio leads or trails the picture cut.
- **Cutaway / insert:** a covering shot used to hide a cut in the main action.
- **Morph cut / hidden transition:** a synthesized blend that hides a jump cut. Not used by Scene Carving.
- **Time remapping / speed ramp:** changing the playback rate inside a clip.
- **Video texture:** an infinite or extended video made by jumping between similar frames.
- **Edit blindness:** viewers failing to notice a cut.
- **Attentional synchrony:** many viewers looking at the same place at the same time.
- **Event segmentation / event boundary:** how viewers divide activity into perceived events, and the points where one event ends and the next begins.
- **ASL / MSL / cutting rate:** average shot length; median shot length; cuts per minute.
- **Rule of Six:** Murch's ranked criteria for judging a cut.
- **Active speaker detection (ASD):** working out which on-screen face is speaking.
- **AV offset / lip-sync error:** how far the audio is shifted relative to mouth movement, in frames or milliseconds.
- **Intensified continuity:** Bordwell's term for the faster, tighter continuity style of post-1960s Hollywood.
- **Slow cinema / long take:** an aesthetic of extended, sparse duration.

## Gap analysis: what no existing work does

1. **Temporal carving that keeps one clock per frame.** Every time-domain carver (Dynamosaics, synopsis, ribbon carving, sheet carving) mixes input times within a frame and targets static-camera surveillance. None restricts itself to whole-frame removal from edited feature films with moving cameras.
2. **Removal instead of acceleration.** Fast-forward and hyperlapse methods change apparent speed, which distorts subject physics. None separates subject motion (never touched) from camera motion (frames dropped only below a perceptual threshold).
3. **Light compression with a perceptual guarantee.** Summarization targets about 5–20% of the runtime and accepts choppiness. Nothing targets keeping 70–95% with an explicit "unnoticed" objective, or evaluates with the edit-blindness and detection paradigm.
4. **Separate noticeability and importance axes.** Prior work merges salience and relevance into one score. Seam carving supplies forward energy and TRIPOD and LLM summarizers supply the narrative side, but nobody has combined them as two axes.
5. **Rhythm preservation as an objective.** No system checks that ASL, the shot-length distribution, the 1/f spectrum (Cutting) or visual beats (Davis & Agrawala) survive, or spreads cuts out to protect them.
6. **Working on a finished, mixed master.** Computational editors (Berthouzoz, Leake, QuickCut) assemble raw takes with a human in the loop. None re-edits a locked picture with mixed music and effects, where every cut also has to heal the sound.
7. **Escalation across scales.** No time-domain equivalent of seam ordering exists: an ordered removal list running from single frames through shot tails, pauses, lines and beats to whole scenes, so any runtime can be produced.
8. **Lip-sync as a hard constraint inside the optimizer.** Active speaker detection and SyncNet exist, but no editing system treats lip-sync as an inviolable constraint rather than an after-the-fact metric.
9. **Awareness of slow cinema.** Energies based on motion or dialogue would gut *2001* (Pezzotta's long takes). No method models deliberate duration and music-driven mood as importance.
