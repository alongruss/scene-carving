# Landscape: products, culture, law, semantics, evaluation, test material

> Part of the [Liquid Retime research survey](README.md) (scan of 2026-11-10).
> **Legend:** ✔ = fetched and content confirmed. (s) = URL taken from search results, either not fetched or fetch blocked (Adobe helpx returns 403). UNVERIFIED = could not confirm. **This is not legal advice.**
>
> **Status for Liquid Retime:** the [decisions](../DECISIONS.md) chose a **rendered file for personal use** as the output, not a distributable playback-time map. The legal findings in §3 explain why *2001* stays a private benchmark and why results made from copyrighted films are not shared.

---

## 1. Existing products and tools

| Tool / URL | What it actually does | What it lacks vs. Liquid Retime |
|---|---|---|
| **Auto-Editor** ✔ https://github.com/WyattBlue/auto-editor | CLI written in Nim, released into the public domain (Unlicense). Cuts by audio loudness and/or motion thresholds. Exports Premiere, Resolve, FCP, Shotcut and Kdenlive projects, plus CMX 3600 EDL. | No semantics: it treats silence as unimportant. Its exporters are a reference implementation. |
| **Descript: Shorten word gaps** ✔ https://help.descript.com/hc/en-us/articles/10164807277453-Shorten-word-gaps · **Remove filler words** (s) https://help.descript.com/hc/en-us/articles/10164806394509-Remove-filler-words | Gaps longer than a threshold are cut to a target length (e.g. 200 ms). Filler removal has an "avoid harsh cuts" option. Uses cloud AI credits. | Speech only, with a fixed gap rule. Ignores dramatic pauses, music and picture. |
| **TimeBolt** ✔ https://www.timebolt.io/ | Removes silence, filler words and bad takes. Transcription runs locally. Has Premiere, FCP and Resolve workflows. | Built for talking-head and podcast footage. |
| **Recut** ✔ https://getrecut.com/ | Detects silence and builds a cut list. Exports XML to Premiere, Resolve, FCP, ScreenFlow and CapCut without touching the source. | Same limitations as above. Its non-destructive XML is a good pattern. |
| **Gling** ✔ https://www.gling.ai/ | Removes bad takes, silences and fillers for YouTubers. Exports to NLEs, MP4 and SRT. | Works on raw creator footage, not finished films. |
| **CapCut** ✔ https://www.capcut.com/tools/filler-words | Removes fillers and "trims unnecessary pauses while preserving your rhythm". Third-party sources say auto silence removal is desktop/Pro only. | Cloud-based, speech only. |
| **Premiere text-based editing** (s) https://helpx.adobe.com/premiere-pro/using/video/text-based-editing-video.html | Transcript-driven. Highlights pauses and fillers, then deletes them with Extract (ripple) or Lift. A guide warns it may not respect dramatic pauses ([RedShark](https://www.redsharknews.com/how-to-delete-pauses-and-filler-words-with-text-based-editing) (s)). | Manual and speech-centric. |
| **Scene Edit Detection** (s) https://helpx.adobe.com/premiere-pro/using/scene-edit-detection.html | Finds existing cut points and adds cuts or markers. | Structure only, no scoring. |
| **Morph Cut** (s) https://blog.adobe.com/en/publish/2015/06/18/morph-cut-tips-tricks-for-best-results | Uses face tracking and interpolation to hide interview jump cuts. Works best with static backgrounds. | Repairs a single seam and fails on action. Uses synthesis, so it is not used under carve-only. |
| **Remix** ✔ https://larryjordan.com/articles/remix-comes-to-adobe-premiere-pro-v22-2/ | Re-edits music to a target length within ±5 s, avoiding cuts that break the beat or melody. Not recommended for lyrics. | Music only, with no narrative logic. The closest analogue to *music-aware* cutting. |
| **Generative Extend** ✔ https://blog.adobe.com/en/publish/2024/10/14/generative-extend-in-premiere-pro | The **inverse**: generates extra frames and ambient audio. Won't extend dialogue or music. The beta was limited to 1080p at 12–30 fps. A reported 2 s video limit is UNVERIFIED. | Lengthens rather than shortens, and synthesizes. |
| **DaVinci Resolve** ✔ https://www.blackmagicdesign.com/products/davinciresolve/whatsnew | Version 21. IntelliScript "compares the script text to the original transcribed audio" to assemble cuts. Speed Warp is a Neural Engine optical-flow retime ([Frame.io](https://blog.frame.io/2021/09/27/davinci-resolve-ai-tools/) (s)). Per forums and tutorials, Fairlight gained silence removal in 20.2; which edition has it is UNVERIFIED. | Assembles from a script; doesn't condense finished films. |
| **OpusClip** ✔ https://www.opus.pro/ | Turns long videos into viral shorts. Reviews describe a 0–100 "virality score" (s). | Optimizes for virality, not for keeping the work whole. |
| **Netflix speed** ✔ 2019 test https://www.tubefilter.com/2019/10/29/judd-apatow-aaron-paul-netflix-speed-tests/ · 2020 rollout https://9to5google.com/2020/07/31/netflix-playback-speed-android-rollout/ | 0.5–1.5× with pitch correction. Resets for each title. Launched on mobile first. | Uniform: performances and music are compressed equally. |
| **YouTube** (s) https://www.howtogeek.com/702364/how-to-speed-up-youtubes-playback-speed-or-slow-it-down/ | 0.25–2×, uniform. | Same as Netflix. |
| **Overcast Smart Speed** ✔ https://overcast.fm/ | Trims pauses in talk audio "without distortion". The UI is a toggle plus a time-saved counter. A critic found it removes more than silence ([Cridland](https://james.cridland.net/blog/2024/why-overcast-is-more-than-a-podcast-player/) (s)). | Audio only. Its "invisible + time-saved counter" UX is worth copying. |
| **CinemaGazer** (Kurihara) ✔ https://arxiv.org/abs/1110.0864 | Research system with "two-level fast-forwarding": very fast where there is no speech, readable speed where subtitles are on screen. | Changes speed instead of removing material, and has no mood model. The **closest research ancestor**. |

## 2. Culture and evidence on pacing and attention

- **Cutting, DeLong & Nothelfer (2010)**, *Psychological Science* 21(3), DOI 10.1177/0956797610361679 ✔ https://www.psychologicalscience.org/journals/psychological-science/0956797610361679/
  - Across 150 films from 1935–2005, shot lengths became more correlated with their neighbours and approached a 1/f pattern.
  - **Implication:** preserve the *sequence structure* of shot lengths, not just their mean.
- **Cutting (2016), "The evolution of pace in popular movies"** ✔ https://pmc.ncbi.nlm.nih.gov/articles/PMC5256470/
  - 180 films. Mean shot length was about 10.5 s in 1930–55 and about 4.3 s in 1990–2015.
- **Cutting (2016), "Narrative theory and the dynamics of popular movies"** ✔ https://pmc.ncbi.nlm.nih.gov/articles/PMC5133278/
  - Films divide into four acts of about 25% each. A new scene or subscene starts about every 55 s. About 75% of opening shots have music.
  - Act proportions are something we can measure and preserve.
- **Cinemetrics** ✔ https://cinemetrics.uchicago.edu/
  - A shot-length measurement tool and database (Tsivian and Civjans).
  - A search snippet gives *2001* an ASL of about 13.2 s and Pezzotta cites 13.6 s. Both are UNVERIFIED on the page, which is rendered with JavaScript. Either way that is about 3× today's mean.
- **Pezzotta (2017), "Slowness and Time Expansion in Long Takes"** ✔ https://cinergie.unibo.it/article/view/7340
  - *2001*'s slowness is an *associative* narrative form: the slowness carries the mood.
- **Japanese "fast movies" (ファスト映画)**
  - Arrests ✔ https://coda-cj.jp/en/news/572/ : three people arrested on 23 June 2021 for uploading summaries of about 10 minutes that revealed the endings.
  - Civil ruling ✔ https://coda-cj.jp/en/news/177/ : Tokyo District Court, 17 Nov 2022, ¥500 million in damages.
- **Cross Marketing survey (March 2024)** ✔ https://www.cross-m.co.jp/en/report/trend-eye/20240306baisoku
  - n = 1,100, ages 20–69. 47.0% have watched at double speed, up 12.6 points in three years. The share is over 40–60% among people in their 20s and 30s.
- **Toyoshi Inada, *映画を早送りで観る人たち* (2022)** (s) https://realsound.jp/book/2022/05/post-1028956.html
  - Popularized "taipa" (time performance) and the Gen Z culture of skipping.
- **YouGov (April 2022, US)** ✔ https://yougov.com/en-us/articles/42726-american-tv-preferences-yougov-poll
  - 11% have watched TV faster than normal, 23% are interested, 55% are not.
- **Murphy et al. (2022)**, *Applied Cognitive Psychology* 36(1), DOI 10.1002/acp.3899 (s) https://www.sciencedaily.com/releases/2022/01/220111153637.htm
  - Lecture comprehension shows little cost up to 2× and declines beyond that. This was lectures, not films, and mood was not measured.
- **Gloria Mark** ✔ https://www.universityofcalifornia.edu/news/how-sharpen-your-attention-and-meet-your-goals-2024
  - Average time on one screen fell from about 2.5 min (2003 study) to 47 s (2016–20).
  - This measures task-switching among information workers, not attention to cinema. **Cite with care.**
- **Neta Alexander, "The Right to Speed-Watch"** (s) https://events.umich.edu/event/116008
  - Frames speed-watching as an accessibility practice rather than mere impatience.

## 3. Ethics and law of altering films

- **Colorization.**
  - CSMonitor 1987 ✔ https://csmonitor.com/1987/0514/acolor.html : Woody Allen called colorization "sinful". Gephardt's bill to bar altering films without the consent of the director and screenwriter did not pass.
  - The National Film Preservation Act of 1988 required a disclaimer label on colorized films on the National Film Registry (s) https://www.ebsco.com/research-starters/film/colorization-black-and-white-films
- **Pan-and-scan** ✔ https://en.wikipedia.org/wiki/Pan_and_scan
  - Sydney Pollack sued a Danish broadcaster in 1991. The court called the pan-and-scan version a "mutilation" but still ruled for the broadcaster.
  - Woody Allen refused to allow a pan-and-scan version of *Manhattan*.
- **Moral rights.**
  - Berne Convention Art. 6bis ✔ https://www.wipo.int/wipolex/en/text/283698 : the author has the right to object to "any distortion, mutilation or other modification" prejudicial to their honor or reputation.
  - *Huston v. Turner*, Cass. 1re civ., 28 May 1991 (s) https://www.doctrine.fr/d/CASS/1991/CASSPC9B4D7FA207BAD6791E4 : French moral rights applied despite US contracts.
  - Zinnemann/Italy (DGA) ✔ https://www.dga.org/news/guild-news/2005/december-2005/zinnemann-ruling-a-victory-for-artists-rights : broadcasting a colorized *The Seventh Cross* violated the director's moral rights. Per the DGA, "the integrity of the work is entitled to protection".
- ***CleanFlicks v. Soderbergh***, 433 F. Supp. 2d 1236 (D. Colo., 6 July 2006) (s) https://leagle.com/decision/20061669433fsupp2d123611552
  - Making and selling edited copies infringed the reproduction and distribution rights. Not fair use; an injunction was issued.
- **Family Movie Act, 17 U.S.C. §110(11)** ✔ https://www.law.cornell.edu/uscode/text/17/110
  - Exempts making *limited portions* of a film imperceptible during private home viewing of an *authorized copy*, and the technology that does it, provided no fixed copy of the altered version is made.
  - "Making imperceptible" excludes adding content over or in place of existing content.
- ***Disney v. VidAngel*** (9th Cir. 2017) (s) https://law.justia.com/cases/federal/appellate-courts/ca9/16-56843/16-56843-2017-08-24.html
  - The Family Movie Act requires an authorized copy. Decrypting discs brings §1201 liability.
- **§1201 exemptions**, 37 CFR 201.40 (s) https://www.law.cornell.edu/cfr/text/37/201.40
  - Cover short portions for criticism, comment or education only.
- **ClearPlay** https://web.clearplay.com/
  - The page fetched empty, so its playback-time filtering model is UNVERIFIED there.

**Implications found by the research:**
- Distributing altered files is high-risk: CleanFlicks, and Japan's ¥500 M fast-movie judgement.
- Playback-time skipping of an authorized copy is the protected US model.
- Ripping *2001* from disc is not covered (VidAngel).
- Honest labelling ("Retimed: X of Y min") and one-click revert answer the moral-rights and Apatow/Bird objections.

**Decision taken:** Liquid Retime renders files for **personal use**. *2001* is a private benchmark whose results are never shared. Shareable demos use public-domain or CC-BY material only.

## 4. Narrative and affect understanding (for importance and mood scoring)

- **MovieNet** ✔ https://arxiv.org/abs/2007.10937 : 1,100 movies, 42K scene boundaries, 92K cinematic-style tags. Scene segmentation.
- **MovieGraphs** ✔ https://arxiv.org/abs/1712.06761 : timestamped graphs of people, emotions, relationships, interactions and reasons. Character and relationship importance.
- **MovieQA** ✔ https://arxiv.org/abs/1512.02902 : 14,944 questions over 408 movies.
- **TVQA** ✔ https://arxiv.org/abs/1809.01696 : 152,545 QA pairs over 460 h. Together with MovieQA, a template for plot-retention QA.
- **LVU** ✔ https://arxiv.org/abs/2106.11310 : long-form video benchmark (CVPR 2021).
- **MAD** ✔ https://arxiv.org/abs/2112.00431 : 384K audio-description sentences over 1,200 h. Audio description is a dense narrative signal showing which visual events matter.
- **Condensed Movies** ✔ https://arxiv.org/abs/2005.04208 : key-scene clips from more than 3K films, usable as "must survive" labels.
- **TRIPOD** ✔ https://arxiv.org/abs/1908.10328 · data ✔ https://github.com/ppapalampidi/TRIPOD : 99 screenplays with turning-point labels. Turning points carry top plot importance.
- **Papalampidi et al.**
  - AAAI 2021 ✔ https://arxiv.org/abs/2012.07536 : sparse scene graphs used to find turning-point scenes.
  - ACL 2020 ✔ https://arxiv.org/abs/2004.12727 : latent narrative structure for screenplay summarization.
- **Hanjalic & Xu (2005)**, IEEE TMM 7(1) (s) https://repository.tudelft.nl/file/File_77c07032-a108-415e-9668-d2d3082fb943?preview=1 : arousal and valence curves from low-level features. **A candidate for the mood layer.**
- **LIRIS-ACCEDE** (s) https://hal.archives-ouvertes.fr/hal-01375518 : 9,800 Creative Commons excerpts from 160 films with crowdsourced pairwise affect ranks. The dataset site, liris-accede.ec-lyon.fr, refused the connection.
- **DEAM** ✔ https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0173392 : 1,802 songs with arousal and valence annotated at 2 Hz.
- **Essentia models** ✔ https://essentia.upf.edu/models.html : local arousal/valence regressors and mood classifiers (CC BY-NC-SA 4.0).

## 5. Local models on the GTX 970M (Maxwell, compute capability 5.2)

**Hardware and platform support**
- GTX 970M: 1,280 cores, 192-bit bus at about 120 GB/s, 6 GB (s) https://www.pugetsystems.com/parts/Video-Card/NVIDIA-MXM-Geforce-GTX-970M-6GB-for-Puget-M-and-D-series-10745
- **PyTorch** ✔ https://dev-discuss.pytorch.org/t/notice-cuda-12-6-wheels-will-no-longer-be-published-from-pytorch-2-15-drops-maxwell-pascal-volta/3432 (dated 4 Sept 2026): **2.14 is the last prebuilt wheel that runs on Maxwell** (cu126). From 2.15 onward, build from source with a CUDA 12.x toolkit.
- **NVIDIA** ✔ https://developer.nvidia.com/blog/navigating-gpu-architecture-support-a-guide-for-nvidia-cuda-developers : CUDA 13 cannot compile for compute capability below 7.5. The 580 driver branch is the last for this GPU and is supported until about mid-2028. Stay on CUDA 12.9.
- **Ollama** ✔ https://docs.ollama.com/gpu : supports compute capability 5.0 and up. Capabilities 5.0–6.2 need driver 570 or newer.
- **llama.cpp multimodal** ✔ https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md : supports Qwen2.5-VL 3B/7B, Gemma 3 4B, SmolVLM2, InternVL 2.5/3 and Moondream2. Build with `-DCMAKE_CUDA_ARCHITECTURES=52` ✔ https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md

**Models**
- **Qwen3-VL** ✔ https://github.com/QwenLM/Qwen3-VL : 2B/4B/8B/32B dense plus 30B-A3B and 235B-A22B MoE (Oct 2025). Apache-2.0, 256K context, timestamp alignment, 2 fps video sampling by default.
  - Official GGUF ✔ https://huggingface.co/Qwen/Qwen3-VL-2B-Thinking-GGUF : the 2B model is 1.11 GB at Q4_K_M, used with an mmproj file.
- **SmolVLM2** ✔ https://huggingface.co/blog/smolvlm2 : 256M / 500M / 2.2B, with video support.
- **Moondream2** ✔ https://huggingface.co/vikhyatk/moondream2 : 2B, Apache-2.0. Captioning, querying, detection and pointing.

**Transcription**
- **faster-whisper** ✔ https://github.com/SYSTRAN/faster-whisper
- **CTranslate2** ✔ https://opennmt.net/CTranslate2/quantization.html : fp16 needs compute capability 7.0+ and int8 needs 6.1 or 7.0+, so **the 970M falls back to fp32**. Run Whisper int8 on CPU, or use whisper.cpp.

**Reference point:** a GTX 1050 (Pascal, about 112 GB/s) runs a 7B Q4_0 model at 207 t/s prompt processing and 16.6 t/s generation ✔ https://www.mgroeber.de/benchmarking-llamacpp-on-legacy-hardware-2.html

**Throughput estimate for a 2.5-hour film.** These are estimates from bandwidth and compute arithmetic, not measurements; confirm with `llama-bench`.

| Stage | Assumption | Estimate |
|---|---|---|
| Whisper small/medium, int8 on CPU, with VAD | i7-6700HQ runs about 3–5× realtime | 0.5–1 h (much less for *2001*, which has sparse dialogue) |
| Keyframes | 1 per shot plus 1 per 10 s of long shots: 1,500–2,500 (about 600–1,200 for *2001*) | — |
| Qwen3-VL-2B Q4 captions and scores | ~0.5 s vision encoding, ~1 s prefill, ~50 tokens at ~40 t/s | ~3 s per frame → 1–2 h |
| Qwen3-VL-4B / Qwen3-4B | About 2× slower | 2–4 h |
| 8B Q4 text LLM for scene scoring | 12–15 t/s generation. Only ~1 GB VRAM left for the KV cache (~8K context), so sliding windows over ~300 scenes | 1–2 h |
| Option: 30B-A3B MoE split between CPU and GPU | 32 GB RAM, ~3B active parameters | ~6–10 t/s (UNVERIFIED) |
| **Total** | | **~3–7 h, an overnight batch** |

## 6. Evaluation methods

- **2AFC / spot the edit.** Present the original and retimed version of each scene and ask "which was edited?". Report d′, where chance is 50%. Add a task where viewers press a key whenever they notice a cut.
  - Smith & Henderson (2008), "Edit Blindness" (s) https://www.mdpi.com/1995-8692/2/2/11 : cuts that follow continuity rules are missed more often. About ¼ of same-scene cuts went unnoticed, rising to ⅓ at motion onsets. Use this as a prior for where to place seams.
- **Speech quality metrics.**
  - PESQ ✔ https://www.itu.int/rec/T-REC-P.862 : withdrawn 5 Jan 2024; ITU points to P.863.
  - ViSQOL ✔ https://github.com/google/visqol : speech mode at 16 kHz, audio mode at 48 kHz, Apache-2.0.
  - STOI/ESTOI ✔ https://github.com/mpariente/pystoi : intrusive, MIT.
  - DNSMOS ✔ https://arxiv.org/abs/2010.15258 : non-intrusive.
  - Intrusive metrics need a time-aligned reference. Score each retained segment, plus a window around each seam, against its source span via the edit list. Use DNSMOS on the full output.
- **A/V sync.**
  - SyncNet ✔ https://www.robots.ox.ac.uk/~vgg/software/lipsync/ : measure lip-sync offset on dialogue shots before and after.
  - ITU-R BT.1359 ✔ https://www.itu.int/rec/R-REC-BT.1359 : the often-cited +45/−125 ms detectability thresholds are UNVERIFIED on that page.
- **LLM-judged plot QA.**
  - Generate questions from the original's subtitles, screenplay or audio description. Answer them from the retimed version's transcript, AD and captions, then compare accuracy against the original.
  - Zheng et al. ✔ https://arxiv.org/abs/2306.05685 : LLM judges show position, verbosity and self-enhancement biases. Use multiple choice, swap answer order, and use a judge from a different model family. Validate the judge on a small human sample.
- **Pacing similarity.**
  - KS or Wasserstein distance on log shot durations.
  - Ratio of retimed to original ASL.
  - Lag-1 autocorrelation and 1/f slope (Cutting 2010).
  - Act-proportion preservation (Cutting 2016).
  - Spearman or Kendall correlation between original and retimed per-scene durations.
  - Correlation of the arousal curves.
- **Summarization metrics and their criticism.**
  - Otani et al. (CVPR 2019) ✔ https://arxiv.org/abs/1903.11328 : random summaries match the state of the art under the standard protocol, and segmentation dominates the score. The paper proposes rank-correlation analysis instead.
  - TVSum ✔ https://github.com/yalesong/tvsum : 50 videos, 2 s shots, 20 raters.
  - **Avoid F1 against reference summaries; prefer rank correlation of importance scores.**

## 7. Legal test material

- **Blender open movies.**
  - Index ✔ https://studio.blender.org/films/
  - Terms ✔ https://studio.blender.org/terms-and-conditions/ : content is "Creative Commons Attribution 4.0" unless noted otherwise. Music licensing is UNVERIFIED (the "Remixing Music" page returns 404).
  - Sintel (2010, 14:48, CC BY) ✔ https://en.wikipedia.org/wiki/Sintel . Subtitles in 40 languages ✔ https://durian.blender.org/
  - Tears of Steel (2012, CC BY) ✔ https://mango.blender.org/ : the actors keep their likeness rights. 4K EXR source available.
  - Spring (2019) and Charge (2022, about 3 min) are also CC BY.
  - They are short, so good for seam and audio tests but not for scene-level removal.
- **US public-domain features** ✔ https://en.wikipedia.org/wiki/List_of_films_in_the_public_domain_in_the_United_States . Check your jurisdiction.

  | Film | Why public domain | Caveat |
  |---|---|---|
  | *Night of the Living Dead* (1968) | Released without a copyright notice | The Criterion restoration is copyrighted |
  | *Charade* (1963) | Defective notice | The score and story are still copyrighted; Archive.org post ✔ https://blog.archive.org/2024/03/28/charade-public-domain-movie-screening-at-the-internet-archive/ |
  | *His Girl Friday* (1940) | Not renewed | The underlying play expired in 2024 |
  | *Detour* (1945) | Not renewed | — |
  | *The General* (1926) | Pre-1931 | — |

- **Prelinger Archives** ✔ https://archive.org/details/prelinger : about 6,000 distinct ephemeral films. The rights statement is on a linked panix.com page that was not fetched.
- **Why *2001* is personal-use only:**
  - Listings show © 1968 Turner Entertainment, now Warner Bros. (s).
  - The US term runs to about 2063 (our calculation).
  - Ripping the disc implicates §1201, and distributing results falls under CleanFlicks.
  - It is also the hardest test: about 601 shots (Film Comment snippet, UNVERIFIED), an ASL of about 13 s, and sparse dialogue, so importance must come from vision and music.

## 8. Interchange formats (for later; v1 renders a file)

- **OpenTimelineIO** ✔ https://github.com/AcademySoftwareFoundation/OpenTimelineIO
  - Apache-2.0, Academy Software Foundation. Adapters for CMX 3600, FCP XML and AAF.
  - Schema ✔ https://opentimelineio.readthedocs.io/en/latest/tutorials/otio-serialized-schema-only-fields.html : includes **LinearTimeWarp / FreezeFrame (`time_scalar`)** and **Marker** (`marked_range`, `color`, `comment`, `metadata`). Most objects carry `metadata`.
  - Could later store Protect, Importance and Force cut as markers with namespaced metadata, and the cut list as Clips and Gaps.
- **CMX3600 adapter** ✔ https://github.com/OpenTimelineIO/otio-cmx3600-adapter
  - Supports linear speed effects and markers. No multiple video tracks, no nesting, no "fancy" speed effects. The lowest-common-denominator export.
- **FCPXML** ✔ https://fcp.cafe/developers/fcpxml/
  - Time is expressed as rational seconds. Apple's archived DTD (s) https://developer.apple.com/library/archive/documentation/Miscellaneous/Conceptual/LegacyDTDsFinalCutPro/FCPXMLDTDv1.4/FCPXMLDTDv1.4.html shows `timeMap` for retiming. Details of the current version are UNVERIFIED.

---

## Terminology (landscape)

- **EDL (CMX 3600):** a text list of source and record timecodes for each event.
- **OTIO:** an open timeline interchange format and API.
- **FCPXML:** Final Cut Pro's XML timeline format.
- **Retime map:** a per-segment list of keep, skip or speed. In this research, applied at playback time; not our v1 output.
- **ASL / MSL:** average and median shot length.
- **1/f fluctuation:** a shot-length power spectrum that falls off inversely with frequency.
- **Act / turning point:** the large narrative units and the pivots between them.
- **Continuity editing:** cutting rules that hide cuts (match on action, eyeline, 180° rule).
- **Edit blindness:** failing to notice cuts.
- **Jump cut:** a discontinuous cut within one shot. **J/L-cut:** audio leads or trails the picture cut.
- **Room tone:** ambient background used to fill seams. Liquid Retime never fills seams; carve-only.
- **Director's cut / final cut:** the director's version / the contractual right to decide the released version.
- **Pan-and-scan / letterboxing:** cropping vs. matting widescreen for 4:3.
- **Colorization:** adding colour to black-and-white films.
- **Moral rights (droit moral):** inalienable rights of attribution and integrity.
- **Derivative work / fair use:** US copyright concepts at issue in CleanFlicks.
- **Playback-time filtering:** skipping content during private viewing (Family Movie Act §110(11)).
- **§1201:** the US anti-circumvention rule.
- **Speed-watching / 倍速視聴 / taipa:** watching at more than 1×, framed as "time performance".
- **Fast movies (ファスト映画):** unauthorized condensations of about 10 minutes.
- **Arousal / valence:** the intensity and the pleasantness of affect. **Affect curve:** arousal and valence plotted over time.
- **2AFC / d′:** two-alternative forced choice, and its sensitivity index.
- **Intrusive vs. non-intrusive metric:** one that needs a clean reference vs. one that doesn't.
- **MOS-LQO:** an objective estimate of the mean opinion score.
- **LLM-as-judge:** using an LLM to grade answers.
- **Compute capability (sm_52):** NVIDIA's architecture version number; Maxwell is 5.x.
- **GGUF / mmproj:** llama.cpp's weight format, and its vision-projector file.

## Differentiator analysis (as found by the scan)

Every product above falls into one of these buckets:
- Uniform speed (Netflix, YouTube).
- Removing speech gaps from raw footage (Auto-Editor, Descript, TimeBolt, Recut, Gling, CapCut, Premiere, Resolve, Overcast).
- Clipping for virality (OpusClip).
- Repairing or extending a single seam (Morph Cut, Generative Extend, Remix).
- Research summaries a few minutes long (Papalampidi, CinemaGazer).

Nothing targets *finished narrative features as whole works*. What Liquid Retime could uniquely offer:

1. **Any runtime, with graceful escalation:** micro-trims, then holds, then lines, then interleaved beats, then scenes, always taking the least noticeable and least important seam first.
2. **Mood preservation as an explicit term:**
   - arousal and valence curves;
   - music-aware cut points;
   - a pacing signature (ASL ratio, 1/f slope, act proportions).
   For *2001*, slowness can be *compressed* rather than removed (Pezzotta).
3. **Invisibility as the objective.** Seams are placed according to continuity and edit-blindness evidence (motion onsets, cuts on action) and validated by 2AFC d′. No competitor measures whether its edits are noticed.
4. **Importance grounded in narrative:** turning points (TRIPOD), character and relationship graphs (MovieGraphs), and audio-description density (MAD), rather than loudness thresholds.
5. **Human authority** through Protect, Importance and Force-cut marks.
6. **Legal and ethical awareness:** honest labelling, originals untouched, and copyrighted results kept private.
7. **Fully local on a 2015 laptop:** an overnight batch with no cloud upload, unlike Descript, CapCut or OpusClip.
8. **A built-in evaluation suite:** edit detection, plot-QA retention, speech and sync metrics, and pacing similarity, avoiding the summarization-metric pitfalls Otani et al. identified.
