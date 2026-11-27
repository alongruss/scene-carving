# Scene Carving – Liquid Retiming

**Seam carving for time.** Put a long film in and get a shorter one out. Nobody should see the edits.

- *Scene Carving* echoes [seam carving](https://en.wikipedia.org/wiki/Seam_carving), which shrinks an image by removing its least noticeable paths of pixels. Here the seams are stretches of time, picture and sound together, from a single "umm" or a static hold up to a whole side scene, removed least noticeable and least important first.
- *Liquid retiming*, the name for the operation, echoes *liquid rescale*, GIMP's seam-carving plugin. Here you drag a length slider and the cut updates in near real time.
- **Why not just press 1.5×?** A uniform speed-up rushes every line while the dead air still drags. Scene Carving cuts the dead air instead and keeps the director's rhythm, mood and plot. Speech stays close to its natural pace. Speed changes are gentle: one film-wide factor (1.05× at 60% length, 1.1× at 20%), and the same again on wordless camera moves and long takes.
- **North-star test:** [*2001: A Space Odyssey*](docs/VISION.md#north-star-2001-a-space-odyssey), a famously slow film. Its long, near-silent takes stretch time on purpose, and a score based on motion or dialogue would gut it. It is a private benchmark.

**Try it:** [the prototype](#try-the-prototype) · **Read more:** [the docs](#docs)

> **Status: definition + prototype phase.**
> - `main` holds the agreed definition, the decision log and the research.
> - A **throwaway prototype** on branch [`prototype/carve-only`](#try-the-prototype) runs the whole pipeline end to end on real films. What it validated is folded back into the docs here.
> - No production code yet.

## How it works

1. **Analysis** runs offline, overnight is fine, using local models only. It builds a multi-layered **score map**, judged against each film's own statistics:
   - **Picture:** shot cuts; camera vs. subject motion; how visible a new join would be (temporal forward energy).
   - **Speech:** speech recognition (Whisper) with word timings. Subtitle files are the authority on *what* is said, and they are **anchored to the audio**, so lines from any release land on this film's timeline.
   - **Importance:** a conversation score (words, sentences, fillers), a plot score, breathing room after lines, and a story weight that sends titles and credits first.
2. **Cascade** precomputes one **nested removal order** by repeatedly removing the cheapest scored seam. Seams overlap, so each removal re-scores its neighbours, and a spread term protects relative rhythm.
3. **Timeline UI** is the length slider: any length reads its cuts straight off that order. It also shows score heatmaps and takes human marks: Protect, Importance and Force cut. The prototype has a single-file slider viewer.
4. **Render** cuts frame-accurately from the original:
   - every audio join gets a 10 ms crossfade;
   - unavoidable same-camera joins get a ~6-frame **aligned dissolve**: each co-timed frame pair is warped into line before blending;
   - each join is tagged with its heal strategy;
   - output is the shortened film plus a removal report.

## Rules at a glance

- **Carve, plus gentle speed-ups.** No generated frames, no pitch change, no looping or remixing. Every frame and sample comes from the source. The exceptions:
  - short blends of original material at joins (audio crossfades and aligned dissolves);
  - a second device: one film-wide speed-up tied to the target length, with the pitch kept. Picture and sound change together;
  - the same factor again on edge-only shots without speech (below). Their effects, breathing and silence speed up with the picture. Speech is never sped up on its own, and music keeps its tempo.
- **Information first.**
  - Words are never cut into. Inside a kept sentence, only fillers and stutters may go, whole or not at all.
  - Whole lines go only after everything cheaper, lowest plot score first.
  - Motion is not information. It only makes a cut more visible.
- **Credits go first, and cuts prefer existing shot cuts.**
- **Keep the film's own cutting style.**
  - A film gets only as many jump cuts as it has itself. Past that, a jump cut is a last resort.
  - Camera moves, shots of one moving subject, and long static takes are **edge-only**: trimmed at the head and tail, never cut inside. Trimming costs more as a shot shrinks.
  - Of adjacent shots that show the same thing, the most informative stays.
- **Lip-sync never breaks.**
- **Audio is cut from the original mix.** Separating it into stems is for analysis only. Where the mix is only music, the music is carved at its own musical joins, apart from the picture.
- **No hand-written per-film rules.** Scores calibrate themselves to each film, and human marks are the only per-film input.
- **Local.** Everything runs on your own machine.

## What the prototype has shown

The full iteration log is `prototype/README.md` on branch `prototype/carve-only`. Current renders include the film-wide speed-up.

- **Trims at existing shot cuts.** On *Tears of Steel*, the story is carved almost entirely by trimming shot heads and tails.
- **Healing jump cuts.**
  - **First bake-off:** a short plain **dissolve** beat both hard cuts and a graph-cut "patch", which was worst in 7 of 10 cuts.
  - **Second bake-off** (24 joins in *Tears of Steel* and *Detour*, half with speech): dissolves whose frames are first **aligned along their motion** (optical flow or RIFE) won 13 of 17 best picks. The plain dissolve was picked worst as often as a hard cut (6 of 19). RIFE heals a join in about 0.3 s on a 2014 laptop GPU (GTX 970M).
- **Speech recognition misses lines under music.** Anchoring subtitles to the audio recovered precise timing for the climax and the ending.
  - At 30% length, *Tears of Steel* keeps **75 of 76 subtitle lines intact**. Only the one-word "Now." goes; before the style rules of #70–#76 it kept all 76.
  - Subtitles shifted, sped up for PAL, or containing an inserted scene re-align within ±0.25 s and give an identical carve.
- **Eight films, from no dialogue to wall-to-wall talk.**
  - *Sintel* keeps every spoken word at every length. *Elephants Dream* keeps 99% at 30%, with one sentence removed whole.
  - *Night of the Living Dead* cuts into no sentence down to 60%, dropping only four short lines (such as "Good.") whole, and keeps 95% of its words at 30%.
  - *Detour* keeps every word at 90% and cuts into a single sentence at 75% and at 60%.
- **Lessons from dark films and machine captions** (decision #65): darkness alone is not credits, and auto-generated captions don't mark sentences, so the speech recognizer's sentences stay the units.
- **Limit found:** a speech-dense film can't reach 30% without losing speech. At 30%, *Duck and Cover* (71% speech) keeps 44% of its words and *His Girl Friday* (67%) keeps 45%. Words go mostly as whole sentences, least important first.
- **The speed-up pays off at short lengths:** up to about 6 more percentage points of spoken words are kept at 20–30%. The lip-sync offset stays between 0 and −5 ms, and lengths come out exact.
- **Keeping *2001*'s own cutting style** (decisions #70–#76). Kubrick's cut has no jump cuts of its own, so its budget is zero.
  - At 30% the render has 65 silent jump cuts, down from 345. At 60% it has 19, down from 268.
  - Joins at 30% fell from 815 to 520, and every spoken word is still kept.
  - The EVA stretch the user flagged has no jump cuts at 60% and one at 30%.
  - Lip-sync stays within 20 ms over the whole film, with the extra speed and separately carved music.
- **Subtitles fitted to each render** (#77) land a median of under 50 ms from the speech heard in the render.

## Try the prototype

The prototype lives on branch `prototype/carve-only`. You need Python 3.13 and an ffmpeg build with the `rubberband` filter, which the default speed-up uses. The Whisper `small.en` model (about 486 MB) downloads once into `cache/`.

The commands use Windows paths. On macOS or Linux, use `python3` instead of `py`, and `.venv/bin/python` instead of `.venv/Scripts/python`.

```bash
git clone https://github.com/alongruss/scene-carving.git
```

```bash
cd scene-carving
```

```bash
git switch prototype/carve-only
```

```bash
py -m venv .venv
```

```bash
.venv/Scripts/python -m pip install numpy faster-whisper PyMaxflow opencv-python
```

Create `media/` and put your film (and its `.srt`, if you have one) in it.

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
- `carve_proto.py` options: `--speed-slope 0` carves only, with no speed-up; `--heal <name>` tries that heal first and falls back down the heal chain below if it can't run (for example `--heal dissolve` for the plain dissolve); `--classic` turns off the style rules of decisions #70–#76.
- Output goes to `renders/<film>/`:
  - `<film>_090/075/060/030.mp4`, at 90%, 75%, 60% and 30% of the original length;
  - `<film>_090/075/060/030.srt`, subtitles fitted to each render, which VLC and mpv load automatically;
  - `viewer.html`, the length slider and seam map;
  - `report.txt`.
- `prototype/subtitles.py media/film.mp4` writes the fitted subtitles again for renders that already exist.
- `prototype/batch.py` runs several films in a row.
- `prototype/bakeoff.py <film>` builds a blind heal bake-off page, for comparing heals without knowing which is which.
- Films and renders never go into git: `media/`, `renders/` and `cache/` are ignored.

**Optional GPU heal:** each dissolve is aligned with RIFE 4.26 on the GPU, else with DIS optical flow on the CPU; if neither can run, it stays a plain dissolve. For RIFE, install torch 2.14.1+cu126, the last build for Maxwell GPUs such as the GTX 970M; on newer GPUs any recent CUDA build of torch works. Plain PyPI on Windows gives a CPU-only build, so install from the CUDA index:

```bash
.venv/Scripts/python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cu126
```

Then get the RIFE 4.26 weights linked from [Practical-RIFE](https://github.com/hzwer/Practical-RIFE)'s README and place `IFNet_HDv3.py` and `flownet.pkl` in `cache/rife/v4.26/`.

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
| [docs/DECISIONS.md](docs/DECISIONS.md) | The decision log (#1–#77): every question, the options offered, the answers given, reversals and prototype verdicts. |
| [docs/research/](docs/research/README.md) | Prior-art survey (400+ source links), a [synthesis](docs/research/synthesis.md) of what we borrow and reject, [patching from other times](docs/research/patching-from-other-times.md) (PatchMatch and seam healing), and [frame infilling at joins](docs/research/frame-infilling-at-joins.md) (interpolation, morph cuts and generative in-betweening; warp-only heals adopted, generative frames excluded). |

## Usage and rights

Scene Carving is for retiming **your own copy for personal use**. Shareable demos use public-domain or CC-BY films only. See [docs/VISION.md](docs/VISION.md#ethics-and-law). The code and docs are under the [MIT License](LICENSE). That covers this repo only: the films you retime, and the models and tools it downloads (Whisper, RIFE weights, ffmpeg), keep their own terms.
