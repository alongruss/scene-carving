# Scene Carving: glossary

Project vocabulary comes first. Borrowed academic and industry terms follow, each linked to the research doc where it is explained. When a project term conflicts with common usage, the project term wins in all Scene Carving docs and code.

## Project terms

| Term | Definition | Avoid / notes |
|---|---|---|
| **Scene Carving** | The project: seam carving applied to a film's time axis, named to echo *seam carving*. Full title: *Scene Carving – Liquid Retiming*. Formerly *Liquid Retime* (decision #69). | — |
| **Liquid retiming** | The operation: shortening a film by carving seams of time, as *liquid rescale* shrinks an image by carving seams of pixels. | Not a speed change: the gentle film-wide speed-up is only a second device (#66). |
| **Retime** | To shorten a film by **carving** seams, helped by at most one gentle film-wide speed-up (the **second device**). It never involves synthesis. | Don't use it for "speed up" or "summarize". |
| **Second device** | The film-wide speed-up that runs alongside carving: speed = 1 + (1 − target) / 8, so 1.1× at 20%. It applies to picture and sound together and keeps the pitch (decision #66). Edge-only shots without speech may add the **extra speed** (#75). | Not a "speed mode": it is set by the target length. |
| **Carve / carve-only** | Removing original material. Carve-only is the principle that every output frame and sample exists in the source. | Not "edit", which is too broad. |
| **Seam** | A serial, continuous group of frames and/or audio of any length, from one frame up to a whole scene. Seams are scored and may overlap. | Not "cut". |
| **Seam scale** | **Micro:** static frames, single frames dropped during camera moves, fillers, pauses and gaps. **Meso:** shot heads and tails, jump-cut intervals, lines. **Macro:** interleaved beats, shots, scenes. | — |
| **Joint seam** | A seam that removes picture and audio over the same interval. | — |
| **Decoupled cut** | A paired audio seam and picture seam of **equal duration** at different positions. It is valid only if nothing **sync-critical** lies between them. This is the automatic form of a J/L-cut. | "Split edit" in editing jargon. |
| **Join** | The new adjacency created where a seam was removed. Its perceptual cost is the seam's **noticeability**. | — |
| **Cut (original)** | A shot boundary that already exists in the source film. | Don't call our removals "cuts" in docs. Use seam or join. |
| **Crossfade / dissolve** | A short, cheap blend across a join, using only original material. Audio gets a crossfade of about 10 ms. Unavoidable same-camera picture joins get a cross-dissolve of about 6 frames. It must stay cheap enough for near-real-time preview. | Not synthesis. Not a morph cut. |
| **Mid-shot join** | A join inside a single same-camera shot. It is costly (a jump cut), and costlier with moving subjects or in conversation. The opposite is a trim at an existing cut. | — |
| **Jump-cut budget** | How many mid-shot joins a film may get per output minute: its own rate of jump cuts (cuts whose two sides show the same setup). Past it, a jump cut is a last resort. Speech edits (whole sentences, fillers) don't count (decisions #70, #74). | — |
| **Edge-only shot** | A camera move (pan, tilt, dolly, zoom), a shot of one moving subject, or a static take at least as long as the film's median shot. It is trimmed only at its head and tail, with a cost that rises as it shrinks (decisions #71, #72). | — |
| **Look-alike shots** | Adjacent shots with no speech that show the same thing. Only the most informative stays: an event happens in it, it is the newest view, or its action is most complete (decision #73). | — |
| **Extra speed** | A second speed factor on edge-only shots without speech, on the same curve as the second device and stacked on it. Effects, breathing and silence speed up with the picture; music keeps its tempo (decision #75). | Never applied to speech. |
| **Music-only stretch** | Where the mix is essentially just music. There the music is carved at its own musical joins, apart from the picture, to the exact length the picture plays for (decision #76). | — |
| **Heal strategy** | The tag saying how a seam's join is healed: `trim-at-cut`, `dissolve`, `hard` or `edge-trim`. (`patch`, a per-pixel switch-time graph cut, was rejected after a blind bake-off.) | — |
| **Filler unit** | One or more adjacent fillers or stutter repeats ("um", "you know", "Be... be"). It is cut whole or not at all; the only speech that may be cut from inside a kept sentence. | — |
| **Breathing room** | Protected frames right after speech or sound ends, and before it starts. The length is learned from the film. | — |
| **Story weight** | A per-frame multiplier from the plot layer. Titles and credits are near 0. | — |
| **Score map** | The output of analysis: time-aligned, self-calibrated **layers** covering the whole film. | — |
| **Layer** | One time series in the score map, e.g. plot, mood, visual noticeability, audio noticeability, sync-critical, duration-as-intent, or the rhythm reference. | — |
| **Noticeability** | The perceptual cost of a seam's removal, evaluated at the join (temporal **forward energy**). It has visual and audio components. | Not "energy" alone, which is ambiguous. |
| **Importance** | The meaning lost by removing a seam's content: **plot** plus **mood**, informed by **duration as intent**. It can veto a removal that would otherwise be cheap. | Not "salience". |
| **Plot importance** | How much a span carries the story, with turning points highest. | — |
| **Mood curve** | The film's affect over time (arousal and valence, plus music emotion). Its shape should survive the retime. | — |
| **Duration as intent** | A hold or pause that is unusually long *relative to the rest of this film* counts as directorial emphasis. | — |
| **Film norm** | This film's own statistics: shot lengths, pause classes, motion levels, loudness. Every score is judged against it. | — |
| **Self-calibration** | Normalizing every layer and weight against the film norm. It is why there are **no per-film hand rules**. | Not "tuning". |
| **Sync-critical** | Content whose sound must stay aligned with the picture: visible speech (lips) and visible sound events. | — |
| **Cascade** | (1) The offline process that repeatedly removes the cheapest seam, updates the seams that overlap it, and re-scores its neighbours. (2) The effect of one removal on those overlapping and neighbouring seams. | — |
| **Removal order** | The nested order produced by the cascade. Any **target length** is a prefix of it. | — |
| **Nested** | The property that every shorter version is contained in every longer one. | — |
| **Spread** | The cost term that makes removals near earlier removals more expensive. It distributes carving so relative timing survives. | Not a separate pass. |
| **Rhythm signature** | The film's measurable pacing: the shot-length distribution and sequence (1/f), ASL, act proportions, pause classes and rank order. It is a soft objective and a reported metric. | — |
| **Pace knob** | A UI control, separate from target length, that sets how far toward modern pacing to push. | — |
| **Target length** | The requested runtime, i.e. the position of the length slider. | — |
| **Pause / gap / pause floor** | A pause is silence within one speaker. A gap is silence between speakers. The pause floor is the minimum duration, **learned from the film**. | — |
| **Filler** | A disfluency such as "umm" or "uh", the cheapest kind of speech seam. | — |
| **Interleaved beat** | A side moment woven into a scene that can be removed without harming plot or mood. Example: a character calls their dog during an important conversation. | — |
| **Human marks** | **Protect** (never removed), **Importance level** (raise or lower a span's importance), **Force cut** (removed regardless of score). | No "pin duration". |
| **Hard constraint** | A rule no cost can buy: no synthesis, no pitch change, no local speed change beyond the extra speed on edge-only shots without speech, carve the original mix, lip-sync never lost, no physics distortion, one clock per frame, chronology kept. | — |
| **One clock per frame** | Every output frame is one whole source frame. There are no spatio-temporal seams. | — |
| **Physics distortion** | Any local, visible change in the speed of subject motion. Forbidden beyond the gentle curve of the second device and the extra speed on edge-only shots (#75). | — |
| **Analysis / Cascade / Timeline UI / Render** | The four pipeline phases. Analysis runs offline (hours). The cascade runs offline after analysis and again when marks or the pace knob change. The UI is near real time. Render produces the file and the report. | — |
| **Removal report** | A render output listing every removed seam with its range, kind, scale, scores and reason. | — |
| **North star** | *2001: A Space Odyssey*, our hardest private benchmark. | — |

## Borrowed terms

### Retargeting and carving — [research/video-and-editing.md](research/video-and-editing.md)

- **Seam carving / liquid rescale:** removing the lowest-energy connected paths (Avidan & Shamir 2007).
- **Backward energy / forward energy:** the energy of the removed content vs. the energy of the new adjacencies a removal creates (Rubinstein et al. 2008). Our noticeability is temporal forward energy.
- **Seam ordering / multi-size media:** a stored removal order from which any size can be produced. Our nested removal order is its time-domain counterpart.
- **Multi-operator retargeting:** several operators on one cost scale.
- **Temporal retargeting / video condensation / ribbon carving:** shortening by carving space-time regions. We use only the flat, whole-frame case.
- **Video synopsis / Dynamosaics:** non-chronological, multi-clock condensation. Rejected.
- **Adaptive fast-forward / hyperlapse / optimal frame selection:** speed-based shortening. The frame-selection dynamic programming is a candidate solver; the acceleration itself is rejected.
- **Video texture, D(i,j):** a frame-distance matrix used to find invisible jumps. We use it only to score joins.

### Film editing and perception — [research/video-and-editing.md](research/video-and-editing.md)

- **Shot / scene / sequence / beat**, **head / tail / handles**, **lift vs. extract**, **lifting a line / tightening**.
- **Jump cut**, **J-cut / L-cut (split edit)**, **cutaway / insert**, **continuity editing / 180° rule / match on action**.
- **Morph cut**: a synthesized jump-cut repair. Not used.
- **Edit blindness**, **attentional synchrony**, **event segmentation / event boundary**.
- **Rule of Six** (Murch): emotion, story, rhythm, eye-trace, 2D plane and 3D space.
- **ASL / MSL / cutting rate**, **1/f fluctuation**, **intensified continuity**, **slow cinema / long take**.
- **Turning point (TP)**, **active speaker detection (ASD)**, **AV offset / lip-sync error**.

### Audio and speech — [research/audio-and-speech.md](research/audio-and-speech.md)

- **TSM (time-scale modification)**: used only for the film-wide second device, as one uniform stretch with the pitch kept (ffmpeg `rubberband` in the prototype).
- **OLA / WSOLA / PSOLA / phase vocoder**, **HPSS**, **formant preservation**, **key-frame map**: considered, and not used beyond that.
- **Room tone**, **ambience / atmos**, **audio texture**, **audio inpainting**: synthesis is not used; texture statistics may score joins.
- **DME stems / M&E**: separation is used for analysis only.
- **VAD**, **forced alignment**, **diarization**, **verbatim ASR**, **filler / disfluency**.
- **Pause / gap / overlap**, **turn-transition offset**, **prosodic boundary**.
- **Beat / downbeat / bar**.
- **SI-SDR**.

### Landscape, evaluation and law — [research/landscape.md](research/landscape.md)

- **EDL (CMX 3600)**, **OTIO**, **FCPXML**: interchange formats, for later.
- **Arousal / valence / affect curve**.
- **2AFC / d′**, **intrusive vs. non-intrusive metric**, **MOS-LQO**, **LLM-as-judge**.
- **Director's cut / final cut**, **pan-and-scan**, **colorization**, **moral rights (droit moral)**, **derivative work / fair use**, **playback-time filtering**, **§1201**.
- **Speed-watching / taipa**, **fast movies (ファスト映画)**.
- **Compute capability (sm_52)**, **GGUF / mmproj**.
