# Liquid Retime: decision log

> This log records two grilling sessions held on **2026-11-10**. The assistant asked the questions through a multiple-choice UI, and the user could always type a free-form answer instead.
> Answers in quotes are the user's own words. **Later answers override earlier ones.** Reversals are marked ⟲.
> The resulting definition is in [DEFINITION.md](DEFINITION.md).

## Grill 1: concept and mechanism (before research)

| # | Question | Options offered | Answer |
|---|---|---|---|
| 1 | What does uniform 1.5× playback ruin? | Rushed dialogue · Still too long · Feels artificial | **Rushed dialogue.** It rushes speech while dead air and holds still drag. |
| 2 | What are we making when shortening a deliberately slow film like *2001*? | Same film, faster · New cut, new audience · Viewer's own cut | "same film faster trying to save director intent" |
| 3 | Who decides which moments carry meaning? | Algorithm alone · Algorithm + human marks · Human approves edits | **Algorithm + human marks** |
| 4 | What does "energy" mean? | Noticeability · Importance · Both, kept separate | **Both, kept separate.** Importance can veto removals that are cheap on noticeability. |
| 5 | Pause rules (a 10 s and a 1 s silence) | Long shrinks more, order kept · Proportional everywhere · Per-scene share, free inside · Free, cost-driven | "something between proportional and per scene share" (refined in #9) |
| 6 | Which audio manipulations are OK? | Speed up speech slightly · Cut music at bar lines · Loop/synthesize ambience · Decouple audio from picture | All four. ⟲ Speech speed-up was dropped (#46) and loop/synthesis retracted (#41). Music cuts are bounded by carving the mix as-is (#47) and by "no special rules" (#37). Decoupling was kept, with a sync condition (#41). |
| 7 | What happens beyond retiming into content removal? | Just go · Warn and report · Hard ratio ceiling · Never remove content | **Just go** |
| 8 | Which outcomes count as success? | Never notices edits · Watches to the end · Passes a plot quiz · Same mood described | **All four** |
| 9 | Where does the proportional rule apply? | Per scene · Per pause type · Everything | "by score, and trying not to harm conversations and direction. we may remove more from dead air, but the dead air was also a director's choice. in extreme modes a whole sentence or scene might have a lower score and become a candidate for removal. multi layered audio-visual scoring is the key here" |
| 10 | How far may one scene's compression stray from the overall ratio? | Tight · Moderate · Loose | "I would say moderate but again we also have the option to remove whole parts and scenes that do not harm the plot. so we need to understand for temporal audio and video what is needed for the plot and mood" |
| 11 | Which success goal is given up last? | Edits unnoticed · Watches to end · Plot · Mood | "they are all important scores. holding attention is subjective" |
| 12 | What shape should extreme removal take? | Many small, spread out · Few large · Least noticeable first | "we try to be least noticeable - maybe someone saying "umm" is unimportant. as the scoring allows us we remove more. maybe some character is calling out to it's dog while an important conversation is taking place. that whole dog interaction might be cut if it is not relevant to the plot and mood. as we go into the extreme it becomes a job similar to a film editor." |
| 13 | Which picture manipulations are OK? | Speed up motion slightly · Drop frames when static · Trim shot heads/tails · Jump cuts inside a shot | "we should not distort physics" (so no motion speed-up), plus **drop frames when static**, **trim heads/tails**, **jump cuts inside a shot** |
| 14 | In the dog example, what is removed? | Interleaved moments · Overlapping sound layer · Both | **Interleaved moments** (saves time) |
| 15 | Which models are acceptable? | Cloud frontier · Local only · Either | **Local only** |
| 16 | What can a human mark? | Protect · Pin duration · Importance level · Force cut | **Protect, Importance level, Force cut** (no pinned durations) |
| 17 | Lip-sync vs. speech speed-up conflict | Off-screen speech only · No speech speed-up · Talking-shot exception | "a mix of all the options you wrote. losing lip sync is a hard fail" ⟲ Speech speed-up was later dropped entirely (#46). |
| 18 | Does "physics" cover camera motion? | Camera may speed up · Camera is physics too · Only if unnoticeable | **Only if unnoticeable.** Under carve-only, this means dropping frames during camera moves. |
| 19 | What should v1 achieve on *2001*? | ~120 min · ~100 min · ~75 min · Any length, all levels | **Any length, all levels** |
| 20 | Neighbour-bump (spread) idea | Keep it · Scene band is enough · Tunable knob | "this should mesh with all other scoring - the important goal is to spread cuts to maintain director's intent and unnoticeability. changing a long pause to a short pause without the spread might change the meaning of a scene" |
| 21 | Target machine | This laptop · Laptop now, upgrade later · Any local machine | **Laptop now, upgrade later** |
| 22 | Analysis time budget | Overnight · About real-time · Minutes | **Overnight is fine** |

## Grill 2: aims and differentiators (during and after research)

| # | Question | Options offered | Answer |
|---|---|---|---|
| 23 | What is Liquid Retime for you? | Personal experiment · Open-source tool · Research paper · Product | **Personal experiment + open-source tool** |
| 24 | Where are marks placed and results reviewed? | CLI + marks file · Own timeline UI · Existing NLE round-trip | **Own timeline UI** |
| 25 | Outputs besides the video? | Removal report · Editable timeline · Score heatmaps · Playback-time map | **Removal report**. "may want other later, don't know yet" |
| 26 | Should shorter versions be nested in longer ones? | Yes, nested · No, optimize per length · Nested by default | **Yes, nested** |
| 27 | Headline differentiator | Invisible, measured · Intent-preserving · Seam carving for time · Finished-film A/V editing | **Intent-preserving** |
| 28 | Main output, given the legal research | Map first, render locally · Rendered file only · Both, map primary | **Rendered file only** (personal use) |
| 29 | License | GPL-3.0 · MIT/Apache-2.0 · Decide later | **Decide later** |
| 30 | How do we judge a retime? | Metrics + small blind tests · Automatic metrics only · Your own eye | **Metrics + small blind tests** |
| 31 | Does original duration signal importance? | Yes · Relative to film norm · No | "relative to other parts of the specific film" |
| 32 | Should retimed *2001* stay slow or approach modern pace? | Still slow, just tighter · Approach modern pace · A pace knob | "we don't know what is better yet so it should be a knob at first" |
| 33 | Synthesized in-between frames? | Only if unnoticeable · Near-identical only · Never | **Never synthesize** |
| 34 | Rhythm signature handling | Objective + metric · Hard constraint · Metric only | **Objective + metric** |
| 35 | Pause floors and rank order | Defaults, tunable · Floors only · Learn from the film | **Learn from the film** |
| 36 | Development test material | Public-domain features · Blender open movies · *2001* (private) · Own footage | **All four** |
| 37 | Famous music (e.g. *The Blue Danube*) | Cut at form boundaries · High noticeability · Same as any music | "I don't want special rules I need to define per movie. the scoring solution should be a mix that is not manually decided" |
| 38 | Asymmetry: picture never synthesized, ambience may be? | Loop + synth ambience · Loop only · No synthesis at all | Loop + synth ambience. ⟲ **Retracted** in #41. |
| 39 | Where do the score-mix weights come from? | Self-calibrated per film · Learned from data · Global defaults · Calibrated + learned | **Self-calibrated per film** |
| 40 | Learn from alternate cuts (theatrical vs. extended)? | Validation ground truth · Training + validation · Not now | "no, we are not training an editor who can change the whole plot, we want to keep the plot untouched, there is nothing we can learn from this" |
| 41 | Plot floor: what if the requested length is below it? | Stop at plot floor · Go past, report it · Go past silently | "listen, you analyze a movie (might take some hours) and the result is a multi layered score map (plot, noticeability, mood mapping, audio-visual sync and more). this map is then used as the film is compressed by a user timeline UI in at near realtime (much like liquid rescale). I take back anything to do with sound synthesis. we only use this tool to carve from video and audio (allow decoupled cuts that do not affect sync). a "seam" entity in our case is a serial continuous group of frames and/or audio of any amount. could be very short, could be whole scene in extreme cases. so a seam could be a scored group of any lengths and they might overlap so that removal cascades" |
| 42 | Pitch-preserved speech speed-up under carve-only? | No, whole seams only · Yes, counts as micro-carving | "I don't understand this question" (re-asked as #46) |
| 43 | How are audio pieces joined? | Short crossfades · Zero-crossing hard cuts | "we can do short crossfades as long is it is not processing intense. it must work near-relatime" |
| 44 | How do audio seams relate to the mix? | Stems for analysis only · Carve stems, remix · Mix only, no separation | "I do not understand this" (re-asked as #47) |
| 45 | What happens when the slider reaches plot seams? | User decides on the map · Warn at the floor · Hard stop | "analysis is an offline process already finished by the time the user is in the UI allowing for compute of the carving cascade. slider can go all the way." |
| 46 | Keep slightly faster off-screen speech? (re-asked in plain language) | Drop it · Keep it | **Drop it.** Speech always plays at normal speed. |
| 47 | Cut the mixed soundtrack as-is, or split it into layers? (re-asked in plain language) | Cut the mix as-is · Split and cut layers | **Cut the mix as-is.** Stem separation is used only during analysis. |

## Prototype feedback: after watching the carve-only prototype (iteration 1)

The user watched 90%, 75% and 60% carvings of *Tears of Steel*, made by the throwaway prototype on branch `prototype/carve-only`.

| # | Observation or question | Answer / decision |
|---|---|---|
| 48 | End credits survived in the 90% version | "the whole credit section is throwing us off as it is not relevant to story and could be cut completely. note that credits like this are low energy to plot." Titles and credits score near-zero story importance and go first. |
| 49 | Same-camera cuts inside a shot | "any hard cut video that happens in the middle of the same scene with the same camera and also in a conversation is very noticeable. we should score in a way the prefers trimming scene start or end above jump cutting in the middle." |
| 50 | Scoring inputs | "we might also want to help score using motion vectors?" This means using motion, split into camera vs. subject motion, in the noticeability of a join. |
| 51 | Visual healing for unavoidable same-camera cuts (options: Short cross-dissolve · Motion-interpolated morph · Dissolve live, morph in render · No healing, just avoid) | **Short cross-dissolve**: about 6 frames blending original frames, the picture equivalent of the audio crossfade. ⟲ This amends #33: blending is allowed, but generating or interpolating pixels is still not. |

## Prototype feedback: after watching iteration 2

| # | Observation or question | Answer / decision |
|---|---|---|
| 52 | Seam handling | "we might want to tag seams with a removal/patch strategy". Every seam carries a **heal strategy** for its join: `trim-at-cut`, `dissolve`, `hard` (a mid-shot jump between near-identical frames) or `edge-trim`. `patch` is reserved. |
| 53 | Abrupt cuts after lines | "some cuts are a bit too abrupt like right when speech ends without "breathing room"". **Breathing room** after sound or speech ends, and a shorter breath before it starts, is protected. Its length is learned from the film's pause statistics (consistent with #35). |
| 54 | Healing quality | "crossfades are better then the rough jump we had earlier, we might improve even more in the future with better synthesis". Better healing is a future direction. The question "is PatchMatch a relevant analogue?" was researched: [research/patching-from-other-times.md](research/patching-from-other-times.md). |
| 55 | Review lengths | "always create a 30% version". The standard review renders are **90 / 75 / 60 / 30%**. |

## Prototype feedback: after watching the 30% render (iteration 3)

| # | Observation or question | Answer / decision |
|---|---|---|
| 56 | Words cut before a man walking | "why would you rather cut important words from sentences than cut a man walking … we need to plot score and conversation score to better protect informative scenes … let's better protect information." **Information comes first.** Speech is protected by a conversation score: cutting into a word is very expensive, whole sentences are seams priced by a plot score, and breathing room follows sentence ends. **Motion is not information**; it only makes joins more visible. |
| 57 | Local speech recognition | Approved download of faster-whisper with the `small.en` model (486 MB), running locally on CPU. |
| 58 | Healing method | "you can also do the bake-off". A blind bake-off of hard / dissolve / `patch` (graph-cut switch map) / best-pair snap over 11 story mid-shot joins was built. **Result pending the user's picks.** |

## Resolved tensions

- **"Keep the plot untouched" (#40) vs. "just go" (#7) and "slider can go all the way" (#45).** There is no plot floor. Plot is protected *by ordering*: plot-bearing seams carry the highest importance and are removed last. The timeline shows exactly when plot starts to be lost.
- **Proportional removal vs. "rushed dialogue" (#1, #5, #9).** Removal is score-driven, not proportional. Conversation rhythm is protected by learned pause floors and rank order (#35), and spread is part of the cost (#20).
- **"Just go" (#7) vs. director intent (#2).** There is no separate extreme mode. The same cascade simply reaches costlier seams, ending in editor-like decisions (#12).
- **Speech speed-up (#6, #17) vs. carve-only (#41).** Speech speed-up was dropped (#46).
- **Cutting music at bar lines (#6) vs. carving the mix (#47) and no special rules (#37).** Music may only be cut where the *whole mix* is cleanly cuttable. Downbeats inform noticeability, and famous pieces get no special case.

## Rejected or out of scope

| Item | Why |
|---|---|
| Any synthesis: frame interpolation, morph cuts, generated or looped ambience, inpainting | #33, #41: carve only. Blending original material at joins is allowed: audio crossfades (#43) and short picture dissolves (#51). |
| Audio time-scale modification, including off-screen speech speed-up | #41, #46 |
| Separating stems and remixing them in the output | #47 (separation is for analysis only) |
| Speeding up subject motion | #13: no physics distortion |
| Multi-clock (spatio-temporal) seams such as video synopsis or Dynamosaics | Breaks physics and one clock per frame (#13). See [research](research/video-and-editing.md). |
| Learning weights from alternate cuts | #40 |
| A playback-time retime map as the primary output | #28: rendered file only for now |
| Per-film hand-written rules (e.g. special handling for famous music) | #37, #39 |
| Cloud models | #15 |
| Pinned exact durations as a mark type | #16 |
| Research paper or product as goals (for now) | #23 |
