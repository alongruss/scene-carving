# Liquid Retime: research survey

A prior-art scan for Liquid Retime: seam carving in the time domain for finished films. It covers academic work, products, culture, law, evaluation methods and test material.

## Contents

| Doc | Scope |
|---|---|
| [synthesis.md](synthesis.md) | **Start here.** What we borrow at each pipeline stage, what we rejected and why, and the combined gap that makes Liquid Retime new. |
| [video-and-editing.md](video-and-editing.md) | Seam carving lineage, temporal retargeting and video condensation, adaptive fast-forward and hyperlapse, summarization and trailers, computational editing and hiding cuts, shot/scene/speaker detection, perception and film theory. |
| [audio-and-speech.md](audio-and-speech.md) | Time-scale modification (reference only), non-uniform speech compression, pause and gap floors, silence and filler tools, music retargeting and beat tracking, cinematic stem separation (analysis only), the speech timing pipeline, A/V sync thresholds, GPU support on the development laptop. |
| [landscape.md](landscape.md) | Existing products, evidence on pacing and attention, ethics and law of altering films, narrative and affect understanding, local models on modest hardware, evaluation methods, legal test corpus, interchange formats. |
| [patching-from-other-times.md](patching-from-other-times.md) | Follow-up scan, also 2026-11-10: is PatchMatch an analogue? Healing jump cuts with existing pixels from other times: bidirectional similarity, shift-maps, graph-cut video transitions, video inpainting, and diffusion as contrast. Proposes the `patch` heal strategy. |

Each doc ends with a **terminology** list and a **gap analysis**. The project's own vocabulary lives in [../GLOSSARY.md](../GLOSSARY.md).

## Method

- **When:** 2026-11-10, after the first grilling session ([../DECISIONS.md](../DECISIONS.md)).
- **How:** three parallel research passes (video and editing, audio and speech, landscape) using web search and fetch, with an instruction never to invent URLs.
- **Afterwards:** the second grilling session made several choices that rule some researched approaches out. These are time-scale modification, stem remixing, audio synthesis, frame interpolation and multi-clock seams. They are kept in the docs and annotated *considered — not used*, so the reasoning remains visible.

## Verification legend

| Mark | Meaning |
|---|---|
| ✔ | URL fetched and content confirmed. |
| † | DOI also checked against Crossref (title, authors and venue matched). |
| (s) | URL taken from search results but not fetched, or the fetch was blocked (e.g. Adobe helpx returned 403). |
| **UNVERIFIED** | Claim or identifier could not be confirmed and came only from secondary sources. Treat with care. |
| No mark | URL confirmed by fetch or search, with no further metadata check. |

## Caveats

- Hardware and model facts (PyTorch Maxwell support, CTranslate2 precision rules, throughput estimates) date quickly. Re-check them before implementation.
- Throughput numbers for the GTX 970M are **arithmetic estimates**, not benchmarks.
- The legal notes are a summary for orientation, **not legal advice**. Liquid Retime currently renders files for personal use only. *2001: A Space Odyssey* is a private benchmark, and results from copyrighted films are not shared.
