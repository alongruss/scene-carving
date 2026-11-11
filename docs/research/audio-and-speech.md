# Prior art: audio and speech

> Part of the [Scene Carving research survey](README.md) (scan of 2026-11-10).
> Scope: carving time out of a film's mixed soundtrack without harming speech, music or ambience, while keeping lip-sync.
>
> **Verification:** each URL was confirmed by fetching it or finding it in search results. **UNVERIFIED** marks anything not confirmed.
>
> **Corrections to our own starting assumptions:**
> - UnderScore is a UIST **2012** paper. The UIST 2014 Rubin & Agrawala paper is a different one.
> - The license of the TSM Toolbox is ambiguous: the page says MIT, the DAFx paper says GPL.
> - Demucs has been archived (read-only since 2025-01-01).
> - Auto-Editor is now written in Nim.
>
> **Status for Scene Carving: carve-only.** The [decisions](../DECISIONS.md) settled three things after this scan:
> - **No time-scale modification (TSM).** Speech is never sped up.
> - **No stem remixing.** Audio is carved from the original mix, and stem separation is used *for analysis only*.
> - **No audio synthesis, generation or looping.** Joins use short, cheap crossfades.
>
> Sections 1, 6 (remixing) and 8 (generation) are therefore kept as *considered — not used* reference. Sections 2–5, 7 and 9 feed the scoring and validation directly.

---

## 1. Time-scale modification (TSM) — *considered, not used (carve-only)*

| # | Reference | URL | License | Relevance |
|---|---|---|---|---|
| 1 | Verhelst & Roelands, "An overlap-add technique based on waveform similarity (WSOLA) for high quality time-scale modification of speech," ICASSP 1993, vol. 2, pp. 554–557 | ICASSP DOI **UNVERIFIED**. Companion Eurospeech 1993 paper: https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html | – | Shifts each frame to the point of best waveform similarity before overlap-adding. The standard baseline for slight speech speed-up. |
| 2 | Laroche & Dolson, "Improved phase vocoder time-scale modification of audio," IEEE TSAP 7(3):323–332, 1999 | https://doi.org/10.1109/89.759041 | – | Phase locking reduces the "phasy" sound. Suits music and ambience stretches, where WSOLA can double transients. |
| 3 | Driedger, Müller & Ewert, "Improving TSM of music signals using harmonic-percussive separation," IEEE SPL 21(1):105–109, 2014 | DOI 10.1109/LSP.2013.2294023. Demo: https://audiolabs-erlangen.com/resources/2014-SPL-HPTSM/ | – | Phase vocoder with long frames on the harmonic part, OLA with short frames on the percussive part. Preserves transients without detecting them. |
| 4 | Driedger & Müller, "A Review of Time-Scale Modification of Music Signals," Applied Sciences 6(2):57, 2016 | https://www.mdpi.com/2076-3417/6/2/57 | Open access | The standard survey of OLA, WSOLA, phase vocoder and HPS-TSM failure modes. |
| 5 | TSM Toolbox (MATLAB, DAFx-14) | https://audiolabs-erlangen.de/resources/MIR/TSMtoolbox | MIT per the page, but the paper says GPL, so check | Reference implementations, including a wrapper for élastique. |
| 6 | libtsm (Python port of the TSM Toolbox) | https://github.com/meinardmueller/libtsm | MIT | WSOLA, phase vocoder and HPS-TSM in Python under a permissive license. |
| 7 | Rubber Band Library v4.0 (R2 "Faster" / R3 "Finer" engines) | https://breakfastquay.com/rubberband/ · https://github.com/breakfastquay/rubberband | GPL-2.0-or-later or commercial | `setKeyFrameMap` maps source frames to output frames, giving score-driven non-uniform stretch. Also has `OptionFormantPreserved`. Offline only. |
| 8 | pyrubberband | https://github.com/bmcfee/pyrubberband | ISC | Python wrapper that calls the Rubber Band CLI through files. |
| 9 | SoundTouch | https://www.surina.net/soundtouch/ | LGPL-2.1 | Fast WSOLA-like tempo change with about 100 ms latency (per its README). Fine for previews, weaker than R3 on music. |
| 10 | zplane élastique SDK | https://licensing.zplane.de/licensing | Commercial (academic licence available) | The industry quality standard. Licensing it conflicts with a fully open local stack. |
| 11 | audiotsm | https://github.com/Muges/audiotsm | MIT | OLA, WSOLA and phase vocoder, with real-time streaming. Fixed speed only in the documentation. |
| 12 | PyTSMod (ISMIR 2020 LBD) | https://github.com/KAIST-MACLab/PyTSMod | GPL-3.0 | Time-varying stretch through anchor points for OLA, WSOLA and phase vocoder. TD-PSOLA is fixed-rate and needs an external pitch tracker. |
| 13 | Cohen, Kreuk & Keshet, "Speech Time-Scale Modification With GANs" (ScalerGAN), IEEE SPL 29:1067–1071, 2022 | DOI 10.1109/LSP.2022.3164361. PDF: https://keshet.net.technion.ac.il/files/2023/09/CohenKrKe22.pdf. Code (github.com/MLSpeech/scaler_gan) **UNVERIFIED** | Code license unknown | Neural speech TSM that beat 11 baselines in the authors' listening tests. |
| 14 | Wisnu et al., "STSM-FiLM," arXiv 2510.02672, 2025 | https://arxiv.org/abs/2510.02672 | No code found | Neural speech TSM conditioned on a continuous speed factor and trained on WSOLA targets. A sign the field is maturing. |
| 15 | Tarrat, "Adaptation of the Seam Carving Technique for Improving Audio Time-Scaling," MSc thesis, UPF, 2008 | https://zenodo.org/records/3744795 | – | **The closest direct "seam carving for audio" precedent:** spectrogram seams within rhythm segments. Audio only, no picture. |

Why TSM is not used: speeding up speech without changing pitch means rebuilding the waveform from overlapping slices. That counts as synthesis under our carve-only rule. On-screen speech also cannot be stretched without breaking lip-sync. TSM stays relevant as the *baseline we beat*, since every player's 1.5× mode uses it.

## 2. Non-uniform speech compression and comprehension

| # | Reference | URL | Relevance |
|---|---|---|---|
| 16 | Arons, "SpeechSkimmer," ACM TOCHI 4(1):3–38, 1997 | DOI 10.1145/244754.244758. PDF: https://www.media.mit.edu/speech/old/papers/1997/arons_ToCHI97_speechskimmer.pdf | Combines time compression, pause shortening and pitch-based emphasis detection into several skimming levels. It is our escalation ladder, audio only. |
| 17 | Covell, Withgott & Slaney, "MACH1: nonuniform time-scale modification of speech," ICASSP 1998, pp. 349–352 | DOI 10.1109/ICASSP.1998.674439 (via dblp). PDF: https://www.ee.columbia.edu/~dpwe/papers/CovWS98-mach1.pdf | Sets a local compression rate from emphasis and relative speaking rate, then applies SOLA. Comprehension was 5–31 points better than linear compression, and listeners preferred it 95% of the time. **The closest precedent for score-driven compression.** |
| 18 | Foulke & Sticht, "Review of research on the intelligibility and comprehension of accelerated speech," Psychological Bulletin 72(1):50–62, 1969 | DOI **UNVERIFIED** (10.1037/h0027575 resolves to APA but the title was not confirmed). Discussed in https://link.springer.com/article/10.3758/BF03208200 | Comprehension declines moderately from about 175 to 275 words per minute, then more steeply. |
| 19 | Murphy et al., "Learning in double time," Applied Cognitive Psychology 36(1):69–82, 2022 | DOI 10.1002/acp.3899. PDF: https://castel.psych.ucla.edu/wp-content/uploads/sites/111/2022/03/Applied-Cognitive-Psychology-2021-Murphy-Learning-in-double-time-The-effect-of-lecture-video-speed-on-immediate-and.pdf | Little comprehension loss up to 2× for lectures. In film the problem is noticing the edit, not comprehension. |

## 3. Pauses, gaps and the "rushed" floor

| # | Reference | URL | Relevance |
|---|---|---|---|
| 20 | Goldman-Eisler, *Psycholinguistics: Experiments in Spontaneous Speech*, Academic Press, 1968 | Book (no DOI). Record: https://bibbase.org/network/publication/goldmaneisler-psycholinguisticsexperimentsinspontaneousspeech-1968 | Pauses are about half of spontaneous speaking time. Silences under about **250 ms** count as articulatory, not cognitive. Suggests a floor for pauses within one speaker. |
| 21 | Stivers et al., "Universals and cultural variation in turn-taking in conversation," PNAS 106(26):10587–10592, 2009 | https://doi.org/10.1073/pnas.0903616106 | Across 10 languages speakers avoid overlap and minimize silence. Language means fall within about 250 ms of the cross-language mean. |
| 22 | Levinson & Torreira, "Timing in turn-taking…," Frontiers in Psychology 6:731, 2015 | https://www.frontiersin.org/articles/10.3389/fpsyg.2015.00731/full | Gaps between turns are about **200 ms**, a practical floor for gaps between speakers. |
| 23 | Heldner & Edlund, "Pauses, gaps and overlaps in conversations," Journal of Phonetics 38(4):555–568, 2010 | https://doi.org/10.1016/j.wocn.2010.08.002 | Defines pause (within a speaker), gap (between speakers) and overlap. A 500 ms threshold catches only about half of gaps, so the spread is wide. |
| 24 | Campione & Véronis, "A large-scale multilingual study of silent pause duration," Speech Prosody 2002, pp. 199–202 | https://mail.sprosig.org/sp2002/pdf/campione-veronis.pdf | Pause durations are **trimodal**. Compress within each class, not across classes. |
| 25 | Krivokapić, "Prosodic planning: effects of phrasal length and complexity on pause duration," Journal of Phonetics 35(2):162–179, 2007 | https://doi.org/10.1016/j.wocn.2006.04.001 | Pause length tracks prosodic and phrasal structure. Shrinking should **preserve rank order**, not flatten pauses to one length. |
| 26 | Roberts & Francis, "Identifying a temporal threshold of tolerance for silent gaps after requests," JASA 133(6):EL471–EL477, 2013 | https://doi.org/10.1121/1.4802900 | Long gaps after requests signal reluctance (the exact threshold, possibly about 700 ms, is **UNVERIFIED**). They carry meaning and deserve protection. |

**Inferred floor (research reference).** Gaps between speakers ≥ 200 ms. Pauses within a speaker at phrase boundaries ≥ about 250 ms. Compress pauses roughly in proportion to their length so rank order is kept. Mark long gaps after questions or requests as meaningful. Per the decisions, Scene Carving **learns its floors from each film's own pause statistics**, and these norms serve as reference and fallback.

## 4. Silence and filler removal tools

| # | Tool | URL | License | Relevance |
|---|---|---|---|---|
| 27 | Auto-Editor | https://github.com/WyattBlue/auto-editor | Unlicense (public domain) | Cuts by loudness or motion threshold with a 0.2 s default margin. Exports to Premiere, Resolve, FCP, Shotcut, Kdenlive and EDL. Cuts the whole mix with no sense of meaning. |
| 28 | carykh jumpcutter | https://github.com/carykh/jumpcutter | MIT (unmaintained) | Speeds up silent parts instead of cutting them, which is exactly the artifact we avoid. |
| 29 | unsilence | https://github.com/lagmoellertim/unsilence | MIT | Separate speeds for audible and silent parts (silent default 6×). Same limitations as jumpcutter. |
| 30 | Audacity Truncate Silence | https://manual.audacityteam.org/man/truncate_silence.html | GPL (Audacity) | Shortens every silence below a threshold to one fixed length, the uniform behaviour we rejected. |
| 31 | Descript "Shorten word gaps" / "Remove filler words" | https://help.descript.com/script-editing/shorten-word-gaps · https://help.descript.com/script-editing/filler-words | Proprietary SaaS (not local) | Transcript-based gap and filler removal with an "Avoid harsh cuts" option. Users call the gap tool "brute force". |
| 32 | Overcast Smart Speed | https://overcast.fm | Proprietary | "Dynamically shortens silences in talk shows." Audio only, with no picture constraint. |
| 33 | Wagner et al., "CrisperWhisper: Accurate Timestamps on Verbatim Speech Transcriptions," Interspeech 2024 | https://arxiv.org/abs/2408.16589 · https://github.com/nyrahealth/CrisperWhisper | Code MIT. Weights non-commercial | Verbatim ASR that outputs [um]/[uh] with tighter word timestamps. The best local filler detector found. |

## 5. Music retargeting and beat tracking

| # | Reference | URL | License | Relevance |
|---|---|---|---|---|
| 34 | Wenner et al., "Scalable Music: Automatic Music Retargeting and Synthesis," Computer Graphics Forum 32(2):345–354, 2013 | https://doi.org/10.1111/cgf.12054 | – | Spectral clustering plus a length-constrained dynamic-programming search over jumps, explicitly "inspired by seam carving". Supports joint video and audio editing. The idea of finding seamless jumps transfers to scoring music joins. |
| 35 | Rubin et al., "Content-based tools for editing audio stories," UIST 2013, pp. 113–122 | https://doi.org/10.1145/2501988.2501993. Library: https://github.com/ucbvislab/radiotool | ISC (radiotool) | Transcript-based speech editing that keeps breaths and pauses natural, plus music retargeting to fit the speech. |
| 36 | Rubin et al., "UnderScore: musical underlays for audio stories," **UIST 2012** | https://doi.org/10.1145/2380116.2380163 | – | Aligns music changes to emphasis points in the speech. The idea behind decoupled music edit points. |
| 37 | Rubin & Agrawala, "Generating emotionally relevant musical scores for audio stories," UIST 2014, pp. 439–448 | https://doi.org/10.1145/2642918.2647406 | – | Re-sequences existing music with dynamic programming to fit the emotion of the speech. |
| 38 | Adobe Audition / Premiere "Remix" | https://helpx.adobe.com/audition/using/creating-remix.html · https://blog.adobe.com/en/publish/2015/11/30/audition-deep-dive-remix-automatically-rearrange-any-song-to-fit-any-duration | Proprietary | Beat detection plus separation-based harmonic analysis to fit a target duration, with "Maximum Slack" and optional stretching to exact length. Works on isolated music clips only. |
| 39 | librosa (McFee et al., SciPy 2015) | https://librosa.org/doc/latest/index.html | ISC | Beat tracking, HPSS and phase-vocoder stretch. Useful glue code. |
| 40 | madmom | https://github.com/CPJKU/madmom | Code BSD. Models CC BY-NC-SA 4.0 | Classic RNN+DBN beat and downbeat tracker. The PyPI release is stale, so install from GitHub. |
| 41 | Foscarin, Schlüter & Widmer, "Beat this!," ISMIR 2024 | https://arxiv.org/abs/2407.21658 · https://github.com/CPJKU/beat_this | MIT (code + weights) | State of the art for beats and downbeats. Runs on CPU, with an 8 MB small model. **Use for downbeat-aware audio cut points.** |
| 42 | Heydari, Cwitkowitz & Duan, "BeatNet," ISMIR 2021 | https://arxiv.org/abs/2108.03576 · https://github.com/mjhydri/BeatNet | CC-BY-4.0 | Joint beat, downbeat and meter tracking, with an offline mode. |
| 43 | Kim & Nam, "All-In-One," WASPAA 2023 | https://github.com/mir-aidj/all-in-one | MIT | Beats, downbeats and labelled sections (verse, chorus). Needs NATTEN built from source on Windows. |

For Scene Carving: we never remix stems, so music can only be cut where *the whole mix* is cuttable. Beat and downbeat positions (computed on a separated music stem during analysis) feed the noticeability of audio joins in the mix.

## 6. Cinematic source separation into dialogue, music and effects — *analysis only*

| # | Reference | URL | License | Relevance |
|---|---|---|---|---|
| 44 | Petermann et al., "The Cocktail Fork Problem," ICASSP 2022, and the DnR dataset | https://arxiv.org/abs/2110.09958. Code: https://github.com/merlresearch/cocktail-fork-separation. Data: https://zenodo.org/record/6949108 | Code MIT with MRX checkpoints. DnR license not confirmed | Defines the speech / music / effects split. The lightweight MRX model outputs `speech.wav`, `music.wav` and `sfx.wav`. |
| 45 | Watcharasupat et al., "A Generalized Bandsplit Neural Network for Cinematic Audio Source Separation" (BandIt), IEEE OJSP 5:73–81, 2024 | https://arxiv.org/abs/2309.02539 · https://github.com/karnwatcharasupat/bandit | Apache-2.0. Checkpoints on Zenodo 10160698 | State of the art on DnR. Dialogue separation exceeds the ideal ratio mask. |
| 46 | Uhlich et al., "The Sound Demixing Challenge 2023 – Cinematic Demixing Track," TISMIR 7(1), 2024 | https://arxiv.org/abs/2308.06981 (DOI 10.5334/tismir.172) | – | Evaluated on real movie audio. Training on DnR only gave +1.8 dB over the baseline, and open training data gave +5.7 dB. Expect bleed on real films, which is fine for analysis. |
| 47 | Rouard, Massa & Défossez, "Hybrid Transformers for Music Source Separation" (HT-Demucs), 2022 | https://arxiv.org/abs/2211.08553 · https://github.com/facebookresearch/demucs | MIT (archived) | A second-stage split of the music stem. Needs ≥ 3 GB GPU memory with `--segment` (HT max 7.8 s). On CPU it runs at about 1.5× the track length. |

Per the decisions, separated stems **only feed the score map**: where speech is, where the music beats fall, where effects hit. They are never remixed into the output.

## 7. Speech pipeline with word-level timing

| # | Reference | URL | License | Relevance |
|---|---|---|---|---|
| 48 | Radford et al., Whisper, arXiv 2212.04356 | https://github.com/openai/whisper | MIT | Memory needs: medium about 5 GB, turbo about 6 GB, large about 10 GB. |
| 49 | faster-whisper (CTranslate2) | https://github.com/SYSTRAN/faster-whisper. Precision rules: https://opennmt.net/CTranslate2/quantization.html | MIT | Word timestamps and a Silero VAD filter. **On GPU, fp16 needs compute capability ≥ 7.0 and int8 needs 6.1 or ≥ 7.0, so the 970M (5.2) runs fp32 only.** int8 works on CPU. |
| 50 | Bain et al., WhisperX, Interspeech 2023 | https://arxiv.org/abs/2303.00747 · https://github.com/m-bain/whisperX | BSD-2-Clause | wav2vec2 forced alignment gives accurate word boundaries, which define the pause intervals. |
| 51 | Silero VAD | https://github.com/snakers4/silero-vad | MIT | About 2 MB, under 1 ms per chunk on a single CPU thread. |
| 52 | pyannote.audio + `speaker-diarization-community-1` | https://github.com/pyannote/pyannote-audio · https://huggingface.co/pyannote/speaker-diarization-community-1 | Code MIT. Weights CC-BY-4.0, gated | "Exclusive" diarization makes it easy to assign transcript words to speakers, which separates gaps from pauses. Speed is published only for an H100 (about 31 s per hour of audio). |

## 8. Ambience, textures and inpainting — *considered, not used (no synthesis)*

| # | Reference | URL | License | Relevance |
|---|---|---|---|---|
| 53 | Lu, Wenyin & Zhang, "Audio textures: theory and applications," IEEE TSAP 12(2):156–167, 2004 | DOI 10.1109/TSA.2003.819947 (from an index, not confirmed by the publisher). PDF: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/1-tsap_audiotexture.pdf | – | Extends short clips into long seamless streams and fills gaps under constraints. |
| 54 | McDermott & Simoncelli, "Sound texture perception via statistics of the auditory periphery," Neuron 71(5):926–940, 2011 | https://doi.org/10.1016/j.neuron.2011.06.032 | Open access | Textures are perceived through time-averaged statistics. **Still useful for scoring:** a join inside a stationary texture (room tone) is cheap when the statistics on both sides match. |
| 55 | Schwarz, "State of the Art in Sound Texture Synthesis," DAFx 2011 | https://hal.archives-ouvertes.fr/hal-01161296 | – | Survey of granular, concatenative and statistical methods, with a film focus. |
| 56 | Adler et al., "Audio Inpainting," IEEE TASLP 20(3):922–932, 2012 | https://doi.org/10.1109/TASL.2011.2168211 | – | Formal framework for filling short gaps. |
| 57 | Stable Audio Open 1.0, arXiv 2407.14358 | https://huggingface.co/stabilityai/stable-audio-open-1.0 | Stability AI Community License | Up to 47 s of 44.1 kHz stereo. Whether it fits in 6 GB is unknown. |
| 58 | Novack et al., "Fast Text-to-Audio Generation with Adversarial Post-Training" (Stable Audio Open Small), arXiv 2505.08175 | https://arxiv.org/abs/2505.08175 | Community License | 341M parameters, targeted at Arm CPUs. |
| 59 | Liu et al., AudioLDM, ICML 2023 | https://arxiv.org/abs/2301.12503 · https://github.com/haoheliu/AudioLDM | CC BY-NC-SA 4.0 | Has an inpainting pipeline. The recommended 8 GB GPU memory is more than the 970M has. |

## 9. A/V sync measurement and thresholds

| # | Reference | URL | License | Relevance |
|---|---|---|---|---|
| 60 | Chung & Zisserman, "Out of time: automated lip sync in the wild" (SyncNet), ACCV-W 2016 | https://doi.org/10.1007/978-3-319-54427-4_19 · https://github.com/joonson/syncnet_python | MIT | Gives AV offset and confidence, on CPU or GPU. **The automatic lip-sync validator after every edit.** |
| 61 | Iashin et al., "Synchformer," ICASSP 2024 | https://arxiv.org/abs/2401.16423 · https://github.com/v-iashin/Synchformer | MIT | A newer sync model with LRS3 and VGGSound checkpoints and 21 offset classes. |
| 62 | ITU-R BT.1359-1 (1998) | https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1359-1-199811-I!!PDF-E.pdf | – | Offset becomes detectable at about +45 ms (sound early) and −125 ms (sound late). It becomes unacceptable at about +90 / −185 ms. |
| 63 | EBU R37 (2007) | https://tech.ebu.ch/publications/r037 | – | A tighter end-to-end limit of +40 ms / −60 ms (numbers from secondary sources). **We use these as hard-fail limits.** |
| 64 | van Wassenhove, Grant & Poeppel, "Temporal window of integration in auditory-visual speech perception," Neuropsychologia, 2007 | https://doi.org/10.1016/j.neuropsychologia.2006.01.001 | – | Audio and lips fuse within a window of about 200 ms. Listeners are more tolerant when audio lags than when it leads. |

## Maxwell (sm_52) support status for the development laptop (GTX 970M 6 GB)

- **PyTorch.**
  - From 2.8, the CUDA 12.8+ wheels dropped Maxwell and Pascal: https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128
  - The cu126 wheels still include sm_50, which runs on sm_52.
  - **PyTorch 2.14 is the last release with any CUDA 12.x wheels.** 2.15 drops Maxwell, Pascal and Volta (notice dated 2026-09-04): https://dev-discuss.pytorch.org/t/notice-cuda-12-6-wheels-will-no-longer-be-published-from-pytorch-2-15-drops-maxwell-pascal-volta/3432
  - After 2.14, PyTorch must be built from source against CUDA 12.6 with `TORCH_CUDA_ARCH_LIST=5.0`.
- **CUDA 13 / drivers.** CUDA 13 dropped offline compilation for compute capability < 7.5: https://developer.nvidia.com/blog/navigating-gpu-architecture-support-a-guide-for-nvidia-cuda-developers/. The 580 driver branch is the last one for Maxwell.
- **Precision.** Plan on fp32 everywhere on the GPU.

## Recommended local *analysis* stack (as researched)

The scan recommended a stack that also covered TSM and remixing. Here it is filtered to what remains valid under carve-only:

- **Runtime:** Python with **PyTorch ≤ 2.14 from the cu126 index**. Avoid the cu128 and cu13x wheels. Stay on the 580 driver branch. Use FFmpeg for I/O.
- **Stems (analysis only):** MRX from cocktail-fork (MIT, light) or BandIt (Apache-2.0) to locate dialogue, music and effects. Optionally HT-Demucs on the music stem.
- **Speech timing:**
  - Silero VAD on CPU.
  - faster-whisper `compute_type=float32` with medium, turbo or distil-large-v3. These should fit in 6 GB at fp32 (estimate); large-v3 at fp32 does not. Alternatively, CPU int8 overnight.
  - WhisperX alignment.
  - CrisperWhisper for fillers (weights are non-commercial).
  - pyannote community-1 for diarization. Check that its PyTorch pin works with ≤ 2.14.
- **Music:** Beat This! for beats and downbeats on CPU. Optionally All-In-One for sections (needs NATTEN built from source on Windows).
- **Sync check:** SyncNet on every on-screen dialogue shot after rendering, failing outside **+40 / −60 ms** (EBU). Synchformer as a second opinion.
- *Not used:* Rubber Band, libtsm, ambience generators (carve-only).

## Terminology (audio and speech)

- **TSM (time-scale modification):** changing duration without changing pitch. *Not used.*
- **OLA / SOLA / WSOLA:** overlap-add of windowed frames. SOLA and WSOLA align frames by waveform similarity first.
- **PSOLA / TD-PSOLA:** overlap-add synchronized to pitch periods. Needs pitch marks and suits clean speech.
- **Phase vocoder:** STFT-based TSM. Its artifact is "phasiness", reduced by phase locking.
- **Transient preservation:** keeping attacks (consonants, drum hits) from smearing or doubling.
- **HPSS:** harmonic-percussive source separation.
- **Key-frame map / time map:** a piecewise mapping from source time to output time.
- **Formant preservation:** keeping the spectral envelope fixed so voices don't sound "chipmunky".
- **Room tone:** the recorded "silence" of a location.
- **Ambience / atmos:** the continuous background bed of a scene.
- **DME stems:** dialogue, music and effects as separate mixes. **M&E** is music plus effects.
- **J-cut / L-cut (split edit):** the audio cut happens before (J) or after (L) the picture cut.
- **VAD:** voice activity detection. **Forced alignment:** timing known transcript words against the audio. **Diarization:** working out who spoke when.
- **Verbatim ASR:** ASR that keeps disfluencies. **Filler / disfluency:** "um", "uh", restarts.
- **Pause / gap / overlap:** silence within one speaker; silence between speakers; simultaneous talk. **Turn-transition offset:** the time between one speaker ending and the next starting.
- **Prosodic boundary:** a phrase edge marked by pause, lengthening and pitch reset.
- **Beat / downbeat / bar:** the pulse; the first beat of a bar; one metrical unit. Downbeats are the safe music cut points.
- **Audio texture:** a statistically stationary sound such as rain or room tone. **Audio inpainting:** filling missing audio.
- **SI-SDR:** scale-invariant signal-to-distortion ratio, the standard separation metric.
- **AV offset / lip-sync error:** the audio-picture time difference. Positive means audio arrives early.

## Gap analysis: what no existing audio tool does

1. **A joint A/V problem.** Silence cutters (27–30) cut picture and audio together on a loudness threshold. Speech compressors (16, 17, 31, 32) are audio only. None knows when lips are on screen.
2. **A model of what pauses mean.** Every tool uses one target length or uniform compression. None uses floors learned from the material, preserves rank order, or protects meaningful gaps (17 and 25 hint at this).
3. **Music awareness inside a finished mix.** Remix, Scalable Music and radiotool expect clean music files. None picks cut points in a mixed soundtrack by downbeat and musical continuity together with picture cuts.
4. **Escalation across levels.** Nothing goes from micro-trims to removing lines and scenes under one shared cost.
5. **Sync validation after editing.** SyncNet and Synchformer exist, but no editor uses them as an automatic pass/fail check against ITU or EBU limits.
6. **Decoupled cuts with a sync guarantee.** Editors do J/L cuts by hand. No tool plans split audio and picture cut points automatically under a "nothing sync-critical in between" constraint.
