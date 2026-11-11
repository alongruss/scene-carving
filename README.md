# Liquid Retime

**Seam carving for time.** Put a long film in and get a shorter one out. Liquid Retime carves away the least noticeable, least important seams of picture and audio, from a single "umm" or a static hold up to a whole side scene. The director's rhythm, mood and plot are kept intact, and nobody should see the edits.

It is inspired by liquid rescale and [seam carving](https://en.wikipedia.org/wiki/Seam_carving). The north-star test is *2001: A Space Odyssey*.

> **Status: definition + prototype phase.**
> - `main` holds the agreed definition, the decision log and the research.
> - A **throwaway prototype** on branch [`prototype/carve-only`](#try-the-prototype) runs the whole pipeline end to end on real films. What it validated is folded back into the docs here.
> - No production code yet; the license is undecided.

## How it works

1. **Analysis** runs offline, overnight is fine, using local models only. It builds a multi-layered **score map**, judged against each film's own statistics:
   - **Picture:** shot cuts; camera vs. subject motion; how visible a new join would be (temporal forward energy).
   - **Speech:** local speech recognition (Whisper) with word timings. Subtitle files are the authority on *what* is said, and they are **anchored to the audio**, so lines from any release land on this film's timeline.
   - **Importance:** a conversation score (words, sentences, fillers), a plot score, breathing room after lines, and a story weight that sends titles and credits first.
2. **Cascade** precomputes one **nested removal order** by repeatedly removing the cheapest scored seam. A seam can be anything from a few frames to whole sentences, shots or scenes. Seams overlap, so each removal re-scores its neighbours, and a spread term protects relative rhythm.
3. **Timeline UI** is a length slider that thresholds that order in near real time, as in liquid rescale. It also shows score heatmaps and takes human marks: Protect, Importance and Force cut. The prototype has a single-file slider viewer.
4. **Render** cuts frame-accurately from the original:
   - picture and audio stay in sync;
   - every audio join gets a short crossfade;
   - unavoidable same-camera cuts get a short dissolve;
   - each join is tagged with its heal strategy;
   - output is the shortened film plus a removal report.

## Rules at a glance

- **Carve, plus one gentle speed-up.** No generated or interpolated pixels, no pitch change, no looping or remixing. Every frame and sample comes from the source. There are two exceptions:
  - short blends of original material at joins (audio crossfades and picture dissolves);
  - a second device: one film-wide speed-up tied to the target length, with the pitch kept. It is 1.0× at 100%, 1.05× at 60% and 1.1× at 20%. Picture and sound change together, so lip-sync stays exact.
- **Information first.**
  - Words are never cut into. Inside a kept sentence, only fillers and stutters may go, whole or not at all.
  - Whole lines go only after everything cheaper, lowest plot score first.
  - Motion is not information. It only makes a cut more visible.
- **Credits go first, and cuts land at existing cuts.** A same-camera jump cut is a last resort and gets a dissolve.
- **Lip-sync never breaks** and **physics is never distorted** (no slow or fast motion).
- **Audio is cut from the original mix.** Separating it into stems is for analysis only.
- **No hand-written per-film rules.** Scores calibrate themselves to each film, and human marks are the only per-film input.
- **Local.** Everything runs on your own machine.

## What the prototype has shown

The full iteration log is `prototype/README.md` on branch `prototype/carve-only`.

- **Credits, then trims at existing cuts.** On *Tears of Steel*, the story is carved almost entirely by trimming shot heads and tails. Visible jumps dropped to 0 at 75% and 60%.
- **Healing jump cuts.** In a blind bake-off, a short **dissolve** beat both hard cuts and a graph-cut "patch". The patch was worst in 7 of 10 cuts.
- **Speech recognition misses lines under music**, so subtitles are the authority. Anchoring them to the audio recovered precise timing for the climax and the ending.
  - At 30% length, *Tears of Steel* keeps **75 of 76 subtitle lines intact, with none partly cut**.
  - Subtitles shifted, sped up for PAL, or containing an inserted scene re-align within ±0.25 s and give an identical carve.
- **Eight films, from no dialogue to wall-to-wall talk.**
  - *Sintel* keeps every spoken word down to 30%, and *Elephants Dream* keeps 99%.
  - *Night of the Living Dead* cuts into no sentence down to 60%, dropping only four short lines (such as "Good.") whole, and keeps 91% of its words at 30%.
  - *Detour* keeps every word at 90% and cuts into a single sentence at 75% and at 60%.
- **Lessons from dark films and machine captions** (decision #65):
  - Darkness alone is not credits.
  - Auto-generated captions don't mark sentences, so the speech recognizer's sentences stay the units.
- **Limit found:** a speech-dense film can't reach 30% by carving alone without losing speech. At 30%, *Duck and Cover* (71% speech) and *His Girl Friday* (67%) keep only about 40% of their words, dropped as whole sentences, least important first.

## Try the prototype

The prototype lives on branch `prototype/carve-only`. It needs Python 3.13 and ffmpeg. The Whisper `small.en` model (about 486 MB) downloads once into `cache/`.

```bash
git switch prototype/carve-only
```

```bash
py -m venv .venv && .venv/Scripts/python -m pip install numpy faster-whisper PyMaxflow
```

```bash
.venv/Scripts/python prototype/transcribe.py media/film.mp4
```

```bash
.venv/Scripts/python prototype/align_subs.py media/film.mp4 media/film.srt
```

```bash
.venv/Scripts/python prototype/carve_proto.py media/film.mp4 --subs media/film.srt --render-height 720
```

- `align_subs.py` is optional and only needed when you have a subtitle file.
- Output goes to `renders/<film>/`:
  - `<film>_090/075/060/030.mp4`;
  - `viewer.html`, the length slider and seam map;
  - `report.txt`.
- `prototype/batch.py` runs several films in a row.
- Films and renders never go into git: `media/`, `renders/` and `cache/` are ignored.

## Test films

All are legal to keep and share except *2001*, which stays private.

- **Blender open movies (CC BY):** *Tears of Steel* (with official subtitles), *Sintel*, *Elephants Dream*, *Big Buck Bunny*.
- **Public domain (archive.org):** *Duck and Cover* (1951), *Detour* (1945), *His Girl Friday* (1940), *Night of the Living Dead* (1968).

## Docs

| Doc | What's in it |
|---|---|
| [docs/VISION.md](docs/VISION.md) | Why this exists, the intent-preserving headline, the *2001* north star, goals and non-goals, success criteria, ethics. |
| [docs/DEFINITION.md](docs/DEFINITION.md) | The model: pipeline, score layers, seams and cascade, heal strategies, hard constraints, evaluation, open questions, future directions (incl. lengthening). |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Project vocabulary, plus borrowed academic and industry terms. |
| [docs/DECISIONS.md](docs/DECISIONS.md) | The decision log (#1–#64): every question, the options offered, the answers given, reversals and prototype verdicts. |
| [docs/research/](docs/research/README.md) | Prior-art survey (240+ source links), a [synthesis](docs/research/synthesis.md) of what we borrow and reject, and [patching from other times](docs/research/patching-from-other-times.md) (PatchMatch and seam healing). |

## Usage and rights

Liquid Retime is for retiming **your own copy for personal use**. Shareable demos use public-domain or CC-BY films only. See [docs/VISION.md](docs/VISION.md#ethics-and-law). The license is still to be decided.
