# Research synthesis: what Liquid Retime borrows, rejects and adds

> This summary pulls together the three research scans and maps them onto the agreed model in [DEFINITION.md](../DEFINITION.md).
> Sources and links are in [video-and-editing.md](video-and-editing.md) (V), [audio-and-speech.md](audio-and-speech.md) (A) and [landscape.md](landscape.md) (L).

## 1. Borrowed ideas, by pipeline stage

### Analysis: building the multi-layered score map

| Layer / need | Borrowed from | How we use it |
|---|---|---|
| Shot and scene structure | TransNet V2, PySceneDetect; MovieNet, Rao et al. 2020 (V §6) | Seam boundaries at every scale: shot heads and tails, shots, scenes. |
| Speech timing | Silero VAD, faster-whisper, WhisperX alignment, pyannote diarization (A §7) | Word boundaries give us pauses, gaps between speakers, lines and speakers. |
| Fillers | CrisperWhisper verbatim ASR (A §4) | "umm" and "uh" become the smallest, cheapest seams. |
| Sync-criticality | TalkNet / Light-ASD active speaker detection (V §6) | Marks where lips are visible, which decides where audio and picture may not drift apart. |
| Music structure | Beat This!, madmom, BeatNet, All-In-One (A §5), run on a stem separated *for analysis only* (A §6) | Downbeat and section positions feed the noticeability of audio joins in the mix. |
| Join noticeability (visual) | Forward energy (Rubinstein 2008); video-texture distance D(i,j) (Schödl 2000); hyperlapse transition cost (Joshi 2015) (V §1, §3, §5) | The cost of a seam is the discontinuity of the *new join*, not the content removed. |
| Where cuts hide | Edit blindness (Smith & Henderson 2008); attentional synchrony; event segmentation (Magliano & Zacks 2011); Murch's Rule of Six (V §7) | Cheap: cuts at motion onsets, between events, and outside the gaze region. Expensive: cuts inside an action. |
| Join noticeability (audio) | Stationary-texture statistics (McDermott & Simoncelli 2011); downbeats; prosodic boundaries (Krivokapić 2007) (A §3, §5, §8) | Cheap: joins inside matching room tone and at downbeats. Expensive: joins inside a word or a musical phrase. |
| Pause meaning | Mach1 emphasis-driven compression; pause classes (Campione & Véronis); turn-taking gaps (Stivers, Levinson & Torreira); meaningful gaps after requests (Roberts & Francis) (A §2–3) | Pause classes, rank order and floors are **learned from the film's own statistics**, with research norms as a fallback. |
| Plot importance | TRIPOD turning points; LLMVS-style caption-then-score; MAD-style audio-description captions; Condensed Movies key scenes; MovieGraphs (V §4, L §4) | Local VLM/LLM captions plus transcript give a plot score per seam. Turning points score highest. |
| Mood | Hanjalic & Xu arousal and valence curves; LIRIS-ACCEDE; DEAM; Essentia (L §4) | A mood curve whose shape must survive the cut. |
| Rhythm signature | Cutting 2010/2016: 1/f shot-length structure and act proportions; Cinemetrics ASL; Davis & Agrawala visual beats (V §7, L §2) | A soft objective during the cascade, and a reported metric. |
| Duration as intent | Pezzotta 2017 on *2001*'s long takes; Bordwell's intensified continuity (V §7) | A hold counts as emphasis when it is unusually long **for this film**. |

### Cascade: building the nested removal order

| Need | Borrowed from | How we use it |
|---|---|---|
| Any-length, nested result | Multi-size seam ordering (Avidan & Shamir 2007) (V §1) | One precomputed removal order. Any target length is a threshold on it. |
| Mixed operators on one scale | Multi-operator retargeting (Rubinstein 2009) (V §1) | Frame drops, head and tail trims, jump cuts, pause, filler and line removal, and beat or scene drops are all priced in one cost. |
| Temporal seams | Ribbon carving (Li, Ishwar & Konrad 2009), restricted to flat full-frame removal (V §2) | Temporal seam carving that keeps one clock per frame. |
| Optimization | Hyperlapse dynamic programming with speed and acceleration penalties (Joshi 2015); EgoSampling shortest path (V §3) | Candidate solvers for local seam selection. Greedy vs. dynamic programming is an open question. |
| Spread | The user's idea of raising neighbours' cost after a removal, plus the rhythm metrics | After each removal, overlapping seams and nearby seams are re-scored, which keeps a single region from being gutted. |
| Cut-point refinement | QuickCut, Berthouzoz 2012, Leake 2017 idioms (V §5) | Once a seam is chosen, snap its edges to the least noticeable exact frame or sample. |

### Timeline UI and render

| Need | Borrowed from | How we use it |
|---|---|---|
| Liquid-rescale slider | Avidan & Shamir's multi-size images | The slider thresholds the precomputed order in near real time. |
| Honest "time saved" UX | Overcast Smart Speed (L §1) | Show original length, retimed length and what was removed. |
| Decoupled cuts | J/L-cut practice; UnderScore's decoupled music edit points (A §5) | Audio and picture lose the same time at different positions, but only where nothing sync-critical lies in between. |
| Join smoothing | Short crossfades (standard practice) | Cheap, a few milliseconds, safe for near real time. No time-scale modification and no synthesis. |
| Validation | SyncNet, Synchformer; EBU R37 (+40/−60 ms), ITU-R BT.1359 (A §9) | Hard-fail lip-sync check on rendered on-screen dialogue. |

### Evaluation

| Need | Borrowed from |
|---|---|
| Invisibility | 2AFC spot-the-edit and d′ (L §6); the RetargetMe user-study template (V §1) |
| Speech intactness | ViSQOL, STOI, DNSMOS on retained segments and seam windows (L §6) |
| Plot retention | LLM-judged plot QA with bias controls (Zheng 2023); MovieQA/TVQA formats (L §4, §6) |
| Rhythm and mood | KS on log shot lengths, ASL ratio, 1/f slope, act proportions, per-scene Spearman, arousal-curve correlation (L §6) |
| What to avoid | F1 against reference summaries (Otani 2019) |

## 2. Considered and rejected (see [DECISIONS.md](../DECISIONS.md))

| Approach | Example work | Why it is not used |
|---|---|---|
| Multi-clock / spatio-temporal seams | Dynamosaics, video synopsis, ribbon or sheet carving in full generality, layered neural retiming | They break physics and one clock per frame. |
| Speed-up and acceleration of subjects | Adaptive fast-forward, hyperlapse rendering, SmartPlayer, CinemaGazer, jumpcutter | They distort physics. Only frame drops during camera moves survive, and only if unnoticeable. |
| Synthesized frames | Morph Cut, FILM, RIFE, jump-cut smoothing, hyperlapse re-rendering, Generative Extend | Never synthesize. |
| Time-scale modification of audio | WSOLA, phase vocoder, HPS-TSM, Rubber Band, neural TSM | Carve-only. Speech speed-up was dropped. |
| Stem remixing | Cutting dialogue, music and effects at different points and recombining them | It leaves separation artifacts in the output. Stems are for analysis only. |
| Ambience synthesis or looping | Audio textures, inpainting, Stable Audio, AudioLDM | Carve-only (this reverses an earlier "allow"). |
| Learning from alternate cuts | Theatrical vs. extended cuts | "We are not training an editor who can change the whole plot." |
| Distributable playback-time maps | Family Movie Act / ClearPlay model | v1 renders a file for personal use. The legal analysis is kept for the record. |
| Reordering shots, trailers, highlight selection | Trailer generation, OpusClip, summarization benchmarks | Chronology is preserved, and the goal is a whole work, not highlights. |

## 3. Combined gap: why Liquid Retime is new

No existing work or product does all of the following at once:

1. **Temporal seam carving with one clock per frame** on finished, edited, mixed feature films. Prior temporal carvers mix times and target surveillance footage.
2. **Removal only, never acceleration or synthesis.** Every frame and every audio sample in the output exists in the source.
3. **Two-axis, multi-layer scoring.** Noticeability (forward energy of the join) and importance (plot plus mood) are kept separate across picture, dialogue, music and sync layers.
4. **Self-calibration to the film itself.** Pause floors, what "long" means for a hold, and the rhythm reference all come from this film, with no hand-written per-film rules.
5. **One nested removal order spanning every scale**, from a few frames to whole scenes, rendered from a near-real-time slider.
6. **Intent preservation as the headline objective.** Rhythm signature, pause rank and mood curve are optimized *and* measured.
7. **Lip-sync as a hard constraint inside the optimizer**, with decoupled audio and picture cuts planned automatically.
8. **Fully local**, on modest hardware, as an overnight analysis.
