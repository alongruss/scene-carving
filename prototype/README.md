# PROTOTYPE: carve-only feasibility (throwaway)

> This lives on the `prototype/carve-only` branch only. It is not production code. Validated decisions get folded into [docs/DEFINITION.md](../docs/DEFINITION.md) on `main`.

## Question

Can a film be shortened by carving **only original whole frames and mixed-audio intervals** (no synthesis, no speed or pitch change) without the seams being noticed? How far can it go before they show? Does a **nested, greedy, spread-aware cascade** feel right behind a liquid-rescale-style length slider?

## Run

```bash
py -m venv .venv && .venv/Scripts/python -m pip install numpy        # once
.venv/Scripts/python prototype/carve_proto.py media/tears_of_steel_720p.mov
```

- Output goes to `renders/<stem>/` (gitignored):
  - `viewer.html`: the slider preview, seam map, state panel and walkthroughs.
  - `<stem>_090.mp4`, `_075.mp4`, `_060.mp4`: real carved renders, frame-accurate with 10 ms crossfades.
  - `report.txt`: numbers per length.
- Open the viewer with `.venv/Scripts/python prototype/serve.py renders/<stem> 8765`, then go to http://localhost:8765/viewer.html. Double-clicking `viewer.html` in Chrome or Edge also works.
- Test clip: *Tears of Steel* (Blender Foundation, CC BY), 12:14, 24 fps, from https://download.blender.org/demo/movies/ToS/

## What the prototype does (deliberately small)

| Piece | Prototype version | Full design (DEFINITION.md) |
|---|---|---|
| Analysis | Signal only: 160 px grey frames, frame difference, histogram cuts, 16 kHz loudness and 40 ms edge spectra | Plus ASR/VAD, diarization, active-speaker detection, beats, plot/mood models |
| Scores | Per-film percentile ranks (self-calibrated) | Same idea, more layers |
| Seams | Windows of 3–96 frames, joint picture+audio only | Every scale up to whole scenes, plus decoupled cuts |
| Cost | join base + visual forward energy + audio join + fragment penalty + length × (content + spread), ranked per removed frame | TBD |
| Cascade | Lazy greedy over a heap; each removal re-scores the joins next to it and raises spread nearby | Same shape |
| Render | Frame-accurate decode→encode pipe; 10 ms equal-power crossfades using source handles, so A/V stay in sync | Same |

## Findings so far (2026-11-10)

1. **Fast enough.** Analysis takes 26 s and the cascade about 15 s for a 12-minute film on the GTX 970M laptop (CPU only). A 2.5-hour film would take minutes for the signal layers. The nested order makes any length instant: the viewer slider re-carves 17,620 frames live.
2. **Shot detection needed looser thresholds.** The first thresholds found 85 shots. Loosened, they find 161, checked on a contact sheet: real cuts, plus a VFX flash and animated credits. The gap matters, because a missed cut makes trims at existing cuts look like jump cuts, and a false cut makes real jumps look free.
3. **Without a per-join cost the cascade shatters the film.** It removed mostly 3–6-frame holds, about 47 joins per carved minute at 75%. A fixed `JOIN_BASE` halved that to about 24/min. *Every join is a risk, even one that scores "free."*
4. **Visual noticeability must be absolute forward energy, not relative to shot motion.** Measured relative to the shot's own motion, jump cuts in tracking shots (a character walking across Amsterdam bridges, 04:19–04:50) came out cheap, and 12 visible jumps survived at 75%.
5. **Cost-per-frame ranking hides visible joins.** A 1 s seam spreads one obvious jump across 24 frames. A visible join is *one perceptual event however much time it saves*. A steep penalty for the top 15% of discontinuities brought likely-visible jumps (frame distance D > 25) down as follows:

   | Keep | Before | After |
   |---|---|---|
   | 90% | 0 | 0 (max D 12, median 4.6) |
   | 75% | 12 | 8 |
   | 60% | 35 | 19 |

   The full design needs a cost term that cannot be amortized over seam length.
6. **The carving shape looks editor-like.** At 90% it removes mostly static holds (163) plus trims at existing cuts (51). By 75%, trims at existing cuts take over (202). Whole shots disappear only from 75% (2 at 75%, 11 at 60%).
7. **Spread works, but only moderately.** The largest share removed from any 10 s window was 32% at 90%, 57% at 75% and 73% at 60%.
8. **Renders are exact and in sync.** All three versions rendered in 214 s total, sharing one decode. Lengths are 11:00.5, 9:10.5 and 7:19.6 (90.0%, 75.0%, 59.9%), and audio and video stream lengths match within 10 ms. Joint seams and handle-based crossfades cause no drift.
9. **The rhythm signature degrades smoothly.**

   | Keep | Average shot length | KS distance (log shot length) |
   |---|---|---|
   | 100% | 4.56 s | — |
   | 90% | 4.10 s | 0.087 |
   | 75% | 3.46 s | 0.156 |
   | 60% | 2.95 s | 0.234 |

## Iteration 2: after watching (user feedback, 2026-11-10)

**User verdict on iteration 1:**
- The **end credits** (starting at 8:42 of the 90% render) threw the 90% version off. They are not story and should be cut completely.
- **Any hard cut in the middle of a shot from the same camera, especially in a conversation, is very noticeable.** The cuts in the bridge conversation scenes were rough.
- So: prefer **trimming the start or end of a shot or scene** over cutting in the middle, use **motion** to help scoring, and heal unavoidable same-camera cuts with a **short cross-dissolve** (decision: dissolve of original frames, not motion-interpolated morphs).

**Changes:**
- **Story-weight layer** (a stand-in for the plot layer). Dark-dominant blocks of 20 s or more near the film's ends are titles or credits, and their story weight is 0.05. That scales their content, spread and join costs. The detected block is 9:48–11:49; the post-credits scene at 11:49–12:05 stays story.
- **Mid-shot joins are expensive:** a base cost of 1.0, plus absolute forward energy, plus **subject motion** near the join, plus the visible-jump penalty. Joins that land on an existing cut cost 0.1.
- **Camera and subject motion are separated** by global phase correlation between consecutive frames. Subject motion is the residual after compensating for camera motion. It feeds both the content cost and the mid-shot join cost.
- **Join costs are only partly averaged out:** they are divided by the square root of the seam length instead of the full length.
- **Growing an existing hole costs no new join**, so holes grow instead of multiplying.
- **Whole shots** up to 10 s are candidate seams.
- **Renders:** every same-shot join becomes a **6-frame cross-dissolve** of original frames (handles on both sides, so length stays exact).

**Results:**

| Keep | Story kept | Credits kept | Joins per carved minute | Same-shot joins | Visible jumps | Trims at existing cuts | Average shot length |
|---|---|---|---|---|---|---|---|
| 90% | 100% | 38% | 1.5 | 9 (inside credits) | 3 (inside credits) | — | 4.56 → 4.36 s |
| 75% | 90% | 0% | 4.9 (was 24) | 1 (dissolved) | 0 (was 8) | 197 | → 4.02 s, KS 0.077 |
| 60% | 72% | 0% | 10.2 (was 36) | 4 (dissolved) | 0 (was 19) | 485 | → 3.41 s, KS 0.137 |

**What changed:** the carving now looks like what an editor does. Lose the credits first, then tighten every shot at its cut points, and almost never cut inside a shot. The largest share of story removed from any 10 s window is 50% at 75% and 71% at 60%.

**New risks to check by watching:**
- With up to 485 trims at existing cuts, does the action still make sense? Trims can cut off the start of an action, which risks the cut no longer matching on the action across it.
- The audio at those cut points.
- Whether 6 frames is the right dissolve length.

## Iteration 3: strategies, breathing room, 30% (user feedback, 2026-11-10)

**User feedback on iteration 2:**
- Tag seams with a removal/patch strategy.
- Some cuts are too abrupt, landing right when speech ends with no breathing room.
- Crossfades are better than the rough jump we had earlier, and better synthesis could improve this further in the future.
- Always create a 30% version.
- Research PatchMatch-style patching from other times: see `docs/research/patching-from-other-times.md` on `main`.

**Changes:**
- **Every seam is tagged with a heal strategy** (`STRATEGIES`): `trim-at-cut` (lands on an existing cut), `dissolve` (6-frame cross-dissolve of original frames), `hard` (a mid-shot jump between near-identical frames, rank below 0.5, so a dissolve would only ghost) or `edge-trim`.
  - The render applies the strategy of each final join. A `dissolve` with no room for handles falls back to `hard`.
  - The viewer shows the strategy for each seam, and the report counts strategies per join.
  - `patch` is reserved as a future strategy.
- **Breathing room, learned from the film.** Smoothed loudness with a film-level threshold marks where sound ends.
  - The length is this film's median short pause, clamped to 0.4–1.0 s. On *Tears of Steel* that's **0.62 s**.
  - Those frames after sound ends, plus half as many before it starts, cost 1.5 per frame. That covers 17% of frames.
  - This is a signal-only stand-in for speech offsets. It also triggers on music and effects endings, and misses speech that ends under continuous music.
- **Default lengths are 90/75/60/30%.**

**Results:**

| Keep | Length | Joins/min | trim-at-cut | dissolve | hard | Story breathing room eaten |
|---|---|---|---|---|---|---|
| 90% | 11:00.5 | 1.6 | 4 | 13 (in credits) | 1 | 0% |
| 75% | 9:10.5 | 4.7 | 36 | 3 | 4 | 0% |
| 60% | 7:20.4 | 12.1 | 71 | 12 | 6 | 0% |
| 30% | 3:39.9 | 31.9 | 84 | 24 | 9 | 4% |

At 30% only 36% of the story is kept: average shot length drops from 4.56 s to 1.84 s, 23 whole shots are dropped, and some 10 s windows are removed entirely. This is the extreme end. Rendering all four took 242 s.

## Iteration 4: protect information (user feedback on the 30% render, 2026-11-10)

**User feedback:**
- "Why would you rather cut important words from sentences than cut a man walking in 00:51–00:59?"
- The cut around 0:46 is hard for both audio and conversation.
- The bridge conversation starting at 1:38 is missing a lot of important words, especially near 1:52.
- So: add a plot score and a conversation score to better protect informative scenes.

**Diagnosis:** the content proxy was `0.5 × loudness rank + 0.5 × subject-motion rank`.
- The walking man (original 2:35–2:50) ranked 0.63 on subject motion, so he looked like information.
- The quiet bridge dialogue ranked only 0.15–0.4 on loudness, measured against this action film's music and explosions, so its words looked cheap.
- At 30% the bridge conversation kept only 37% of its frames.

**Changes:**
- **Local ASR:** `prototype/transcribe.py` runs faster-whisper `small.en` (int8, CPU) with VAD and word timestamps. It took 98 s for the 12-minute film and produced 253 words and 56 sentences (`renders/<stem>/words.json`).
- **Conversation score:**
  - Cutting *into* a word costs 8.0 per frame.
  - Pauses inside a sentence cost 2.0 per frame.
  - Breathing room now follows sentence ends, using the film's median gap between sentences: 0.79 s.
- **Plot score stand-in:** each **whole sentence** is a candidate seam, padded halfway into the pauses on either side.
  - Removing it costs `1.0 + 3.0 × importance` per frame.
  - Importance is the rank of the summed IDF of its content words within this film's transcript, so rare names and nouns score high and "yeah" or "okay" score low.
  - A local LLM would replace this later.
- **Motion is no longer information.** Non-speech content is `0.4 × loudness`. Subject motion only raises the cost of mid-shot joins.

**Results:** the information metric is now the headline.

| Keep | Word frames kept | Sentences intact | Joins/min |
|---|---|---|---|
| 90% | 100% | 56/56 | 1.3 |
| 75% | 100% | 56/56 | 3.7 |
| 60% | 100% | 56/56 | 8.3 |
| 30% | 100% | 56/56 | 18.0 (was 32) |

- Speech covers only 10% of *Tears of Steel*'s frames, so even 30% is reachable by carving non-speech.
- **Re-transcribing the actual 30% render gives 252 words, matching the original count. Every line is present.**
- Spot checks at 30%:

  | Spot | Original | Kept before | Kept now |
  |---|---|---|---|
  | Walking man | 2:35–2:51 | 53% | 22% |
  | Bridge conversation | 5:18–6:05 | 37% | 82% |
  | Around the old 0:46 cut | 1:54–2:30 | 12% | 24%, with its line kept |

**The new risk is the opposite extreme.** At 30% the film becomes nearly "all dialogue, minimal visuals". Purely visual story beats, such as action that matters to the plot, now have no importance signal. That needs the VLM plot layer.

## Bake-off verdict (user's blind picks, 2026-11-10)

The user marked a worst variant for 10 of the 11 cuts, but a best for only one.

| Variant | Worst | Best |
|---|---|---|
| patch6 | 5 | 0 |
| hard | 2 (incl. the bridge conversation) | 1 |
| patch12 | 1 | 0 |
| snap+patch6 | 1 | 0 |
| dissolve6 | 1 | 0 |
| snap+dissolve6 | **0** | 0 |

**The graph-cut `patch` lost: a patch variant was worst in 7 of 10 cuts.** The per-pixel switch shows as tearing or patchwork. That matches the logged metric: seam energy came out higher than dissolve ghosting on every join.

**Decision:**
- `dissolve` stays the heal for unavoidable same-camera cuts.
- `patch` is dropped.
- Snap isn't adopted: the evidence is thin, and it can move a cut into words.
- Better synthesis stays an open future direction.

## Iteration 5: fillers and repeats (decision #60)

**Question asked:** "What is the current strategy about cutting words that are not plot important?"

**Answer (as of iteration 4):**
- Individual words were never cut.
- Only whole sentences could go, priced by plot score.
- Uncaptured fillers counted as pauses.

**User decision:** cut **fillers and repeats only**; real words inside a kept sentence are never cut.

**Changes:**
- **Verbatim ASR.** A filler-laden `initial_prompt` makes Whisper keep "um" and "uh" and stutters.
- **Sentence splitting fix.** A trailing "..." is a false start, not a sentence end.
- **What counts as a filler:**
  - um / uh / er / hmm ...;
  - "you know" when set off by punctuation;
  - stutter repeats: an immediately repeated token, or a "word..." false start.
- **Filler units.** Adjacent filler words merge into one unit (gap ≤ 0.3 s). A unit is cut **whole or not at all**: a partial cut is priced like real words (8.0 per frame), while a whole unit costs 0.3 per frame plus its join. This fixed a bug where "you" was cut out of "you know".
- **Kind `filler`**, cut together with up to 3 frames of the pause on each side.

**Result on *Tears of Steel*:** the film is scripted, so there are few disfluencies.

| Unit | Detected | Removed |
|---|---|---|
| "Be..." stutter in "Be... be tender to her" | yes | whole, once the film is down to 25% |
| "you know" | yes | never, at least down to 20% |

At 30% all 58 sentences are intact and 100% of real-word frames are kept. Filler cuts land *inside* speech, so they're ordered after silent trims. That is correct for "least noticeable first", and they'll matter more in interviews or documentaries.

## Iteration 6: subtitles as the authority on what is said (decision #61)

**User idea:** scripts found online and subtitle files (possibly CC) can feed plot scoring.

**Test material:** Blender's official `TOS-en.srt` (76 lines, 4.7 KB), downloaded to `media/`.

**Finding: speech recognition misses a lot under music and effects.** Whisper heard only **52 of the 76 subtitle lines**. The 24 it missed include:
- the climax: "The world's changed, Celia…" / "…maybe we can too.";
- "Captain! We have to abort!";
- the ending: "There's a lesson to be learned from this." / "Could'a gone worse.".

Measured against the subtitles, iteration 5's 30% render **lost 16 lines and partly cut 16 more**. Its "100% of words kept" claim only covered the words Whisper heard.

**Change (`--subs file.srt`):**
- Every subtitle line becomes a protected unit.
  - If ASR heard it, its word timings set the span.
  - If not, the whole cue span is protected as speech.
- ASR speech outside every subtitle line stays protected as its own unit.
- The plot score's IDF is computed over the subtitle text.
- The report adds a **subtitle-line** metric: intact / partly cut / lost.

**Result:**

| Keep | Subtitle lines intact | Partly cut | Lost |
|---|---|---|---|
| 90% | 76 | 0 | 0 |
| 75% | 76 | 0 | 0 |
| 60% | 76 | 0 | 0 |
| 30% | **74** | **0** | 2 ("There she is.", "Now.") |

- At 30%, the only lines lost are those two, removed whole as the lowest-plot lines.
- Speech now covers 15% of frames (was 10%).

**Caveats:**
- SRT timing is coarse (often whole seconds), so unheard lines are protected over their full cue span.
- This SRT is plain dialogue, not SDH, so there are no sound-event cues yet.
- One cue includes on-screen text ("Fourty years later").
- **Screenplay** alignment (action lines → visual plot beats) is still to do.

## Iteration 7: subtitles anchored to the audio (decision #62)

**User:** "30 was wonderful. Because subtitle timing is coarse and might also differ in timing with some release versions, we need to anchor subtitles with whisper across the video."

**`prototype/align_subs.py`** runs after `transcribe.py` and adds no new downloads.
1. **Anchors.** A monotonic token alignment (`difflib`) of the subtitle text against the ASR words. Matched content words become anchor pairs.
2. **Transform.**
   - For each known framerate ratio (1, 25/23.976, 23.976/25, 24/25, 25/24, 24/23.976, 23.976/24), fit piecewise offsets: a new piece starts where residuals jump more than 1 s for 3 anchors (release edits).
   - Pick by inlier support, then by residual (ties within 0.05 s), then by the ratio closest to 1 and the fewest pieces.
3. **Per line**, in order of preference:
   - `asr`: the ASR word times.
   - `prompted`: Whisper re-run on the line's window with the line text as `initial_prompt`. The window is snapped to a 0.5 s grid for stability, and words count only where Silero VAD finds speech.
   - `asr+vad`: partly heard. Partial evidence never shrinks a line below its mapped span.
   - `vad`: speech found by Silero VAD only.
   - `mapped`: the transform-mapped cue span.

   Words stretched over silence are capped at 1 s.
4. **Output.** `subs_aligned.json`, `<stem>.aligned.srt` and a report. `carve_proto.py --subs x.srt` picks up the aligned file automatically. Precise lines protect their word frames; coarse lines protect their span.

**Result on *Tears of Steel*:**
- 92 anchors, scale 1.0, offset −0.14 s, median residual 0.22 s.
- Timing per line: **asr 35, prompted 18** (newly heard, including the climax and ending), asr+vad 5, vad 6, mapped 12.
- Lines moved by a median 0.18 s (max 1.3 s) and got a median 0.30 s shorter.

**Release self-test (`--selftest`):** the subtitles are distorted three ways and must re-align to the undistorted result.

| Distortion | Lines within ±0.25 s | Detail |
|---|---|---|
| +3 s offset | 100% | |
| PAL speed-up ×23.976/25 + 1.5 s | 100% | scale 1.04271 recovered |
| +4 s after 5:00 (inserted scene) | 99% | breakpoint found at 305.2 s |

The method counts are identical across all three distortions. Two bugs were found and fixed on the way:
- rounding buckets in the ratio choice picked 0.999 over 1.0;
- prompted windows were unstable to a few milliseconds of transform difference (fixed by grid-snapping).

**Cascade, matching release:**
- 30% keeps **75/76 lines intact, 0 partly cut**. "I know." is removed whole as the lowest plot score.
- Speech covers 16% of frames.
- Renders: 90/75/60/30% with exact lengths, A/V in sync, done in 223 s.

**Cascade, PAL-distorted subtitles** (up to 22 s off by the end): aligned back, they give an **identical carve** — 1198 seams, the same line metrics.

## Open (needs eyes and ears, not metrics)

- **Audio joins** are the expected first failure. Signal-only scoring has no beat or speech awareness: a 125 ms hiccup in music, or a clipped word, is invisible to these metrics. Listen to `_090`, `_075` and `_060`.
- At what keep % does *Tears of Steel* start to feel carved? Where exactly?
- Does the live slider feel like liquid rescale?

## Likely next steps (if the verdict is "promising")

- Speech-aware audio joins: VAD plus word boundaries, so seams never land inside a word.
- Beat- and downbeat-aware joins in music.
- **Decoupled cuts**, so picture can be cut at shot boundaries while audio is cut at quiet or beat points. This is probably the biggest gain for scenes with continuous music.
- A non-amortizable visible-join term in the cost.
- Duration as intent (holds that are long *for this film*) as protection.
