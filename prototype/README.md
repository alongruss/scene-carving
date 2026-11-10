# PROTOTYPE: carve-only feasibility (throwaway)

> This lives on the `prototype/carve-only` branch only. It is not production code. Validated decisions get folded into [docs/DEFINITION.md](../docs/DEFINITION.md) on `master`.

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
