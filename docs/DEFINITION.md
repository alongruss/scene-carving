# Liquid Retime: definition

> **Status:** agreed definition v0, 2026-11-10, the outcome of two grilling sessions and a prior-art scan.
> Decisions and their history: [DECISIONS.md](DECISIONS.md). Vocabulary: [GLOSSARY.md](GLOSSARY.md). Prior art: [research/](research/README.md).
> No code exists yet. This document defines *what* we are building, not *how* it is implemented.

## 1. One-line definition

**Liquid Retime carves time out of a finished film.** It removes scored seams of picture and audio, least noticeable and least important first. The result is shorter but keeps the director's rhythm, mood and plot, and nobody can see the edits. It is seam carving (liquid rescale) applied to the time axis.

## 2. Principles

1. **Carve only.** Every output frame and audio sample comes from the source. Nothing is generated, interpolated, looped, time-stretched or remixed. The one exception is short blends of original material at joins: audio crossfades, plus picture cross-dissolves at unavoidable same-camera joins.
2. **Intent-preserving.** The headline goal is the same film, faster, with the director's intent kept. Pauses, holds and pacing carry meaning, so they are compressed with care rather than flattened.
3. **Two-axis, multi-layer scoring.** Every seam has a **noticeability** score (the perceptual cost of the new join) and an **importance** score (plot plus mood). Both are built from multiple layers covering picture, dialogue, music and sync. Importance can veto a cheap removal.
4. **Self-calibrated per film.** All scores and weights are judged against *this* film's own statistics. There are no hand-written per-film rules. Human marks are the only per-film input.
5. **One nested removal order.** A single precomputed cascade orders every seam. Any target length is a prefix of that order, so every shorter version is contained in every longer one.
6. **Human authority.** People steer the result through marks (Protect, Importance level, Force cut) in a timeline UI.
7. **Local.** All models run on the user's own machine. Analysis may run overnight.

## 3. Pipeline

```
 source film ──► [1 ANALYSIS] ──► score map ──► [2 CASCADE] ──► removal order
  (offline, hours, local models)               (offline, after analysis;
                                                 re-run when marks/pace change)
                                                         │
                         human marks, pace knob ──►──────┤
                                                         ▼
                                         [3 TIMELINE UI]  (near-real-time)
                                          length slider = threshold on order
                                                         │
                                                         ▼
                                         [4 RENDER] ──► shortened file + removal report
```

### 3.1 Analysis (offline, can take hours)

Analysis reads the film once and produces the **score map**: time-aligned layers, each self-calibrated against the film norm.

| Group | Layers | Typical detectors (see [research](research/synthesis.md)) |
|---|---|---|
| **Structure** | shots and transitions, scenes, words, lines, speakers, fillers, pauses and gaps, music beats, downbeats and sections | shot-boundary and scene segmentation, VAD, ASR with word alignment, diarization, verbatim filler ASR, beat and downbeat tracking on a stem *separated for analysis only* |
| **Noticeability: visual** | join discontinuity (temporal forward energy, frame distance D(i,j)), subject motion vs. camera motion, predicted attention, event boundaries | frame and flow differences, motion classification, saliency |
| **Noticeability: audio** | join discontinuity in the mix: inside a word, inside a musical phrase, off-beat, mismatched room-tone statistics | alignment boundaries, downbeats, texture statistics |
| **Importance: plot** | plot relevance per span, turning points, interleaved side beats | local VLM captions plus transcript, scored by a local LLM |
| **Importance: mood** | mood curve (arousal and valence), music emotion | affect models on audio and picture |
| **Importance: duration as intent** | how unusually long a hold or pause is *for this film* | the film's own distributions |
| **Constraints** | sync-critical spans (on-screen speech, visible sound events), human marks | active speaker detection, event detection |
| **Rhythm reference** | shot-length sequence, ASL, 1/f slope, act proportions, pause classes and rank order | the film's own statistics |

### 3.2 Seams

A **seam** is a serial, continuous group of frames and/or audio of any length, from a single frame up to a whole scene. Seams are generated at every scale, scored, and allowed to **overlap**.

| Scale | Seam kinds |
|---|---|
| Micro | runs of static frames; single frames dropped during a camera move (only if unnoticeable); fillers ("umm"); pauses and gaps |
| Meso | shot heads and tails (holds before or after the action); jump-cut intervals inside a shot; lines or sentences |
| Macro | interleaved beats (e.g. a character calling their dog during an important conversation); whole shots; whole scenes |

A seam is one of two kinds:
- **joint**: picture and audio over the same interval;
- **decoupled**: a paired audio seam and picture seam of equal duration at different positions (see §5).

### 3.3 Cascade (offline, right after analysis)

The cascade repeatedly removes the cheapest remaining seam and records the order:

1. **Cost** of each candidate seam. It combines:
   - the noticeability of the join it would create;
   - the importance of the content it removes;
   - the spread penalty from nearby earlier removals;
   - the change it would cause to the rhythm signature.

   Hard-constraint violations make the cost infinite. Weights are self-calibrated per film. Lessons validated with the prototype:
   - **Mid-shot joins cost far more than trims at existing cuts.** A hard cut inside a same-camera shot, especially in a conversation, is very noticeable. So trimming a shot's or scene's start or end is preferred, and moving subjects near a join raise its cost further. This needs motion split into camera vs. subject motion.
   - **Titles and credits score near-zero story importance**, so they go first, entirely.
   - **Information comes first, and motion is not information.**
     - Cutting into a word is very expensive, and pauses inside a sentence are costly.
     - A whole sentence is a seam (padded into its surrounding pauses), and removing it costs its plot score.
     - In the prototype the plot score is an IDF stand-in for an LLM.
     - Subject motion only raises the cost of mid-shot joins, never the value of what is removed.
     - On *Tears of Steel* this kept 100% of the words at 30% length.
   - **Inside a kept sentence, only fillers and repeats may be cut** (um/uh/hmm, a set-off "you know", stutters and false starts).
     - Each filler unit is cut whole or not at all.
     - Filler cuts land inside speech, so they are ordered after silent trims.
   - **A visible join is one perceptual event.** Its cost must not be averaged away over a long seam, and extending an existing hole adds no new join.
2. **Remove** the cheapest seam and append it to the **removal order**.
3. **Cascade the update:**
   - overlapping seams shrink or disappear and are re-scored;
   - the new join's noticeability is computed;
   - neighbours receive the spread penalty;
   - the rhythm term is refreshed.
4. Repeat until nothing removable remains.

Because the order is nested, **any target length is a prefix**, and the slider can go all the way down. Plot is protected *by ordering*: plot-bearing seams have the highest importance, so they go last, and the score map shows the user exactly when plot starts to be lost.

The cascade is **re-run** (not the analysis) when human marks or the pace knob change.

### 3.4 Timeline UI (near-real-time)

- **Length slider:** thresholds the precomputed removal order. Moving it must feel instant, like liquid rescale.
- **Pace knob:** separate from length. It sets how far toward modern pacing to push. We don't yet know what is better, so it starts as a knob.
- **Score heatmaps:** every layer along the film, showing what is removed at the current length.
- **Human marks**, painted on the timeline:
  - **Protect:** never removed.
  - **Importance level:** raise or lower the importance of a span.
  - **Force cut:** removed regardless of score.
- **Preview** plays the original with the current skip list and cheap crossfades, without re-encoding.

### 3.5 Render

- Cuts at frame accuracy from the original media, with **short, cheap audio crossfades** at joins. Same-camera picture joins get a **short cross-dissolve** of original frames (about 6 frames). Both use handles from the removed material, so length and sync stay exact.
- **Heal strategies.** Every seam is tagged with how its join is healed, and the render applies the tag of each final join:
  - `trim-at-cut`: the join lands on an existing cut, so it is a plain cut.
  - `dissolve`: a short cross-dissolve of original frames.
  - `hard`: a mid-shot jump between near-identical frames, where a dissolve would only ghost.
  - `edge-trim`: the film's start or end.
  - ~~`patch`~~: a per-pixel switch-time graph cut between the same two handle streams ([research](research/patching-from-other-times.md)). **Rejected after a blind bake-off**: it was worst in 7 of 10 cuts, because the per-pixel switch shows as tearing. Better synthesis remains a future direction.
- **Standard review renders:** 90 / 75 / 60 / 30% of the original length.
- Outputs:
  - the **shortened video file**, for personal use;
  - a **removal report**: every removed seam with time range, kind, scale, scores and the reason it went.

  Other outputs may come later.
- Runs the **lip-sync validator** on rendered on-screen dialogue (hard fail; see §4).

## 4. Hard constraints

| Constraint | Meaning |
|---|---|
| **No synthesis** | No frame interpolation, morph cuts, generated or looped ambience, or inpainting. Only original frames and samples, which may be *blended* at a join: a short audio crossfade, or an approximately 6-frame cross-dissolve at an unavoidable same-camera picture join. |
| **No speed or pitch change of audio** | No time-scale modification. Speech always plays at its original speed. |
| **Carve the original mix** | Audio seams cut the mixed soundtrack as-is. Stem separation exists only inside analysis. |
| **Lip-sync never lost** | No A/V offset on sync-critical content. Validated with SyncNet-style measurement against EBU R37 (+40 ms / −60 ms). Exceeding it is a hard fail. |
| **No physics distortion** | Subject motion is never sped up. Frames may be dropped during *camera* moves only when that is unnoticeable. |
| **One clock per frame** | Each output frame is one whole source frame. No spatio-temporal (multi-clock) seams. |
| **Chronology kept** | No reordering of material. |

## 5. Decoupled cuts

A decoupled cut is the automatic version of an editor's J-cut or L-cut. An audio seam and a picture seam of **equal duration** are removed at **different positions**.

- Between the two positions, audio and picture are offset by that duration.
- So a decoupled cut is valid only if **nothing sync-critical lies between them**: no visible speech and no visible sound events.
- This lets the soundtrack be cut where the *mix* is cleanly cuttable (on a downbeat, in room tone) while the picture is cut where the *image* is cleanly cuttable (at a shot boundary, during a static hold).

## 6. Pauses, holds and spread

- **Pause floors, classes and rank order are learned from the film's own pause statistics.** Research norms (about 200 ms between speakers, about 250 ms within one speaker, trimodal pause classes, rank-order preservation) serve only as reference and fallback.
- **Dead air is more removable but is still a director's choice.** It is scored, never removed by rule.
- **Breathing room.** The frames right after speech or sound ends, and a shorter breath before it starts, are protected so lines don't get clipped. The length is learned from the film's pause statistics; the prototype's loudness stand-in found 0.62 s on *Tears of Steel*.
- **Duration as intent:** a hold that is unusually long *for this film* scores as emphasis.
- **Spread** is part of the cost, not a separate pass. It distributes removals so the *relative* timing of the film survives. Shortening one long pause while its neighbours stay intact can change a scene's meaning.
- **Scene band:** scenes compress by moderately different amounts. On top of that, plot-irrelevant parts and whole scenes can go when their scores allow.

## 7. Escalation (no modes)

There is no separate "extreme mode". As the target length drops, the cascade simply reaches more expensive seams:
- **micro:** fillers, slack frames, pauses;
- **meso:** holds, shot tails, jump cuts, lines;
- **macro:** interleaved side beats, shots, scenes.

At the far end the work resembles a film editor's, guided by the same scores.

## 8. Success criteria and evaluation

Success is four scores with no fixed priority, plus the hard constraints:

1. **Edits unnoticed:** viewers can't tell the film was altered.
2. **Watched to the end:** attention is held. This is subjective, so it is assessed, not optimized directly.
3. **Plot understood:** a viewer understands the same story.
4. **Mood preserved:** the film feels the same: awe, dread, stillness.

**Evaluation plan:** an automatic metrics suite plus occasional small blind tests.

| Aspect | Measure |
|---|---|
| Invisibility | Small blind 2AFC "which was edited?" tests reporting d′; a press-when-you-notice task |
| Sync | SyncNet / Synchformer offsets on on-screen dialogue (hard fail outside EBU R37) |
| Speech intactness | ViSQOL / STOI on retained segments and seam windows; DNSMOS overall |
| Plot | Local-LLM plot QA, original vs. retimed, with bias controls |
| Rhythm | KS distance on log shot lengths, ASL ratio, 1/f slope, act proportions, Spearman correlation of per-scene durations |
| Mood | Correlation of the mood (arousal) curve |

## 9. Test material

- **Public-domain features**, e.g. *His Girl Friday* (rapid dialogue) or *Night of the Living Dead*.
- **Blender open movies** (CC BY: *Sintel*, *Tears of Steel*, *Spring*, *Charge*), for seam and audio tests.
- ***2001: A Space Odyssey*** from a personal copy. This is the north-star benchmark; results are never shared.
- **Own footage.**

Media files never go into git (see `.gitignore`).

## 10. Environment

- **Development laptop:**
  - GTX 970M 6 GB (Maxwell, sm_52), i7-6700HQ, 32 GB RAM.
  - PyTorch is limited to **≤ 2.14 from the cu126 index**, fp32 on the GPU, driver branch 580.
  - Local LLMs/VLMs via llama.cpp or Ollama.
  - Expect a 2.5-hour film to take roughly 3–7 hours of analysis (estimate).
- **Later:** a modern GPU is not ruled out. The design must not depend on the laptop's limits.

## 11. Open questions

- **License:** GPL vs. permissive (to decide when code starts).
- **Tech stack:**
  - language for the analysis and cascade;
  - framework for the timeline UI;
  - frame-accurate preview decoding at near-real-time speed.
- **Cascade algorithm:**
  - pure greedy vs. local dynamic-programming refinement (e.g. hyperlapse-style frame selection inside a seam);
  - how overlap updates are computed efficiently;
  - recompute latency after marks.
- **Cost combination:** the exact functional form, and how self-calibration normalizes each layer.
- **Pace knob mapping:** which operators or targets it shifts, e.g. favouring trims within long shots so ASL drops, vs. removing whole units.
- **Models:** which local models to use for mood and plot, and how to score sync-critical *non-speech* events.
- **Camera-move frame dropping:** the threshold at which it becomes noticeable.
- **Crossfade length and shape** that stays cheap enough for live preview.
