# Liquid Retime: vision

## The bet

Media keeps getting faster. Across 180 popular films, the mean shot length fell from about **10.5 s in 1930–55 to about 4.3 s in 1990–2015** (Cutting 2016). Nearly half of Japanese adults surveyed in 2024 have watched video at double speed, and the share is higher among people in their twenties and thirties (Cross Marketing 2024). The research behind these figures is in [research/landscape.md](research/landscape.md#2-culture-and-evidence-on-pacing-and-attention).

Older, slower films risk losing whole generations of viewers. Today's fix is the player's **uniform 1.5× button**. It rushes the dialogue while the dead air still drags, and it compresses performances and music by the same amount as empty holds.

Liquid Retime offers a different fix: **liquid rescale for time.** Seam carving shrinks an image by removing its least noticeable pixel paths. Liquid Retime shortens a film by removing its least noticeable, least important **seams of time**, from a single "umm" or a static frame up to a whole side scene. It preserves what the director meant.

## The headline: intent-preserving

> "Same film, faster, trying to save the director's intent."

Pauses, holds and pacing are not slack by default. A pause is a pause for a purpose. Liquid Retime therefore:

- Keeps the **relative rhythm**. Removals are spread out, the film's shot-length signature, act proportions and pause rank order are preserved, and long holds still feel long *relative to the rest of the film*.
- Keeps the **mood**. The arousal and valence curve and the music's continuity survive.
- Keeps the **plot**. Plot-bearing material is the last thing to go.
- Keeps the **information**. Spoken words are never cut into. Lines (taken from subtitles when available, anchored to the film's audio) go whole, least plot-important first, and only after everything cheaper.
- Keeps it **invisible**. It carves only, never generates pixels or sound, never changes speed or pitch, and never breaks lip-sync. Joins are softened only by short blends of original material.

## North star: *2001: A Space Odyssey*

*2001* is the hardest case we know:
- It averages about 13 s per shot, roughly three times today's norm.
- It has sparse dialogue.
- It is driven by famous music.
- Its long, near-silent takes stretch time *on purpose* (Pezzotta 2017).

An energy based on motion or dialogue would gut it. If Liquid Retime can shorten *2001* while keeping its awe and stillness, it can shorten almost anything. Whether a retimed *2001* should stay contemplative or move toward modern pacing is an open question, so it is a **pace knob**.

*2001* is a private benchmark run on a personal copy, and its results are never shared.

## Goals

1. **Any target length** from one analysis, through a **nested removal order**. Every shorter version is contained in every longer one, so a length slider works in near real time, as in liquid rescale.
2. **Graceful escalation** from micro-trims (fillers, pauses, static frames) to holds, lines, interleaved side beats and whole scenes, with no separate "modes".
3. **Two-axis, multi-layer scores**: noticeability versus importance (plot and mood) across picture, dialogue, music and sync.
4. **Self-calibration**: each film is judged against its own statistics, with no hand-written per-film rules.
5. **Human authority** through Protect, Importance level and Force-cut marks in our own timeline UI.
6. **Fully local**, on modest hardware, as an overnight analysis.
7. **Honest output**: a rendered file plus a **removal report** of what went and why.
8. **Release-independent**: subtitles or a screenplay from any release anchor to *this* film's audio, despite offsets, PAL/NTSC drift or added and cut scenes.

## Non-goals

- Summaries, highlights, trailers or "fast movies". The output stays a whole work in its original order.
- Uniform or variable acceleration of subjects, and speech speed-up.
- Any generative or synthetic picture or sound. Short crossfades and dissolves of original material at joins are not generation.
- Changing the plot, or training an editor that "can change the whole plot".
- Cloud processing.
- Distributing altered copies of copyrighted films.

## Success looks like

A 20-year-old watches a 100-minute *2001*, and four things are true:
1. They **never notice** it was altered.
2. They **watch to the end**.
3. They could **pass a plot quiz** as well as a viewer of the original.
4. They describe its **mood** the same way.

These are four scores, not a ranking. [DEFINITION.md §8](DEFINITION.md#8-success-criteria-and-evaluation) lists the metrics and the small blind tests that check them.

## Ethics and law

Altering films has a long and contested history: colorization, pan-and-scan, moral rights, *CleanFlicks v. Soderbergh* (2006), the US Family Movie Act, and Japan's 2021–22 "fast movie" prosecutions. See [research/landscape.md §3](research/landscape.md#3-ethics-and-law-of-altering-films).

Liquid Retime is a **personal and open-source tool** that renders files for **personal use** from the user's own copy. Shareable demos use public-domain or CC-BY material only. The original is never modified.

## Who

For now, this is a personal experiment on its way to becoming an open-source tool. It is not a paper or a product yet.
- A throwaway prototype (branch `prototype/carve-only`) has tested the idea end to end on *Tears of Steel* and on public-domain and CC-BY films.
- What it validated lives in [DEFINITION.md](DEFINITION.md) and [DECISIONS.md](DECISIONS.md).
- The license will be decided when production code starts.

**Future direction:** lengthening films too ("liquid stretch", the way seam carving can also enlarge images). See [DEFINITION.md §12](DEFINITION.md#12-future-directions).
