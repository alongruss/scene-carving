# Liquid Retime

**Seam carving for time.** Put a long film in and get a shorter one out. Liquid Retime carves away the least noticeable, least important seams of picture and audio, from a single "umm" up to a whole side scene. The director's rhythm, mood and plot are kept intact, and nobody can see the edits.

Inspired by liquid rescale and [seam carving](https://en.wikipedia.org/wiki/Seam_carving). The north-star test is *2001: A Space Odyssey*.

> **Status: research and definition phase.** There is no code yet.

## How it will work

1. **Analysis** (offline, overnight is fine, local models only) builds a multi-layered **score map**: plot, mood, noticeability, audio-visual sync and rhythm, each judged against the film's own statistics.
2. **Cascade** precomputes one **nested removal order** by repeatedly removing the cheapest scored seam. Seams overlap, so each removal updates the seams around it.
3. **Timeline UI** works like liquid rescale. A length slider thresholds the order in near real time. You also get a pace knob, score heatmaps, and Protect / Importance / Force-cut marks.
4. **Render** produces the shortened file plus a removal report.

## Rules at a glance

- **Carve only.** Liquid Retime never synthesizes, interpolates, loops, time-stretches or remixes. Every output frame and sample exists in the source.
- **Lip-sync never breaks** and **physics is never distorted**.
- **Audio is cut from the original mix.** Decoupled audio and picture cuts are allowed only where nothing sync-critical lies between them.
- **No hand-written per-film rules.** Scores calibrate themselves to each film, and human marks are the only per-film input.

## Docs

| Doc | What's in it |
|---|---|
| [docs/VISION.md](docs/VISION.md) | Why this exists, the intent-preserving headline, the *2001* north star, goals and non-goals, success criteria, ethics. |
| [docs/DEFINITION.md](docs/DEFINITION.md) | The agreed model: pipeline, seams and cascade, score layers, hard constraints, decoupled cuts, evaluation, open questions. |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Project vocabulary, plus borrowed academic and industry terms. |
| [docs/DECISIONS.md](docs/DECISIONS.md) | The grilling log: every decision, the options offered, the answers given and the reversals. |
| [docs/research/](docs/research/README.md) | A prior-art survey (240 unique source links), and a [synthesis](docs/research/synthesis.md) of what we borrow and what we reject. |

## Usage and rights

Liquid Retime is meant for retiming **your own copy for personal use**. Shareable demos use public-domain or CC-BY films only. See [docs/VISION.md](docs/VISION.md#ethics-and-law). The license is still to be decided.
