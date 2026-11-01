# Development status

The authoritative scope, phase order, acceptance gates, and task-execution rules are in [MASTER_PLAN.md](MASTER_PLAN.md). Every task must begin by checking that plan and this status file.

Status labels:
- **Planned** — accepted for the roadmap, not implemented.
- **In Development** — currently being implemented.
- **Implemented** — code exists; platform verification may still be pending.
- **Tested** — automated or documented tests passed in the stated environment.
- **Android Verified** — platform behavior tested successfully on a recorded Android device, with OS/version evidence.
- **Experimental** — available for evaluation, not a stable capability.
- **Blocked** — cannot proceed until a dependency or issue is resolved.

## Current milestone

| Area | Status | Evidence / notes |
|---|---|---|
| Repository foundation | Tested | Four foundation tests passed on the user's Termux device; repository foundation accepted |
| Termux environment detection | Tested | Five environment tests and all nine repository tests passed on the user's Termux device after commit `e0df272` |
| Device runtime observation | Tested | Detector reported Android, Termux, ARM64, Python 3.14.8, and 12,188,905,472 total memory bytes |
| Android OS/API verification | Android Verified | User directly confirmed `getprop` reports Android 15 / API 35 on 2026-11-01; earlier environment-detector API 24 result conflicts and must be investigated before relying on detector output |
| Local data paths and SQLite foundation | Tested; accepted | Phase 2, Task 2; user confirmed Termux verification passed on 2026-11-01; storage paths, SQLite schema v1, project/job persistence and integrity check |
| llama.cpp build-path evaluation | Completed (research/docs) | Phase 3, Task 1; upstream Termux and Android NDK paths compared in [LLAMA_CPP_EVALUATION.md](LLAMA_CPP_EVALUATION.md); no build performed |
| Local inference interface | Android Verified (user-confirmed) | Phase 3, Task 2; user confirmed the latest Termux verification was all good on 2026-11-01; backend-neutral model/request/result types, protocol and typed errors; concrete CLI adapter added later in Task 4 |
| Native llama.cpp build | Android Verified (CLI smoke test) | Phase 3, Task 3; user built upstream llama.cpp natively in Termux on ARM64 with Clang 21.1.8/CMake 4.4.5; `llama-cli --version` and `--help` succeeded; no model loaded and no inference test yet |
| llama.cpp CLI adapter | Android Verified; Task 4 accepted | User's Termux runs confirmed the initial 34-test adapter suite and, after the context-size addition, all 44 repository tests passed. Installed CLI help confirmed the `--ctx-size` option; explicit executable discovery returned `Available: True`. This verifies adapter tests and CLI option compatibility, not GGUF loading or inference. |
| Local model registry | Android Verified; Task 5 accepted | Phase 3, Task 5: SQLite schema v2; explicit local GGUF registration; license/source/attribution metadata; streaming SHA-256; on-demand missing/modified/invalid checks. User confirmed all 43 repository tests passed on Termux. No real model downloaded or loaded. |
| Phase 3 model candidate | Selected; download pending approval | Official Qwen Q4_K_M candidate, immutable repository revision, exact file size and publisher SHA-256 recorded in `MODEL_CANDIDATES.md`; model weights are not stored in Git. |
| Story generation | Planned | Phase 4 |
| Character and continuity engine | Planned | Phase 5 |
| Story analysis and scene planning | Planned | Phase 6 |
| Offline TTS | Planned | Phase 7; implementation subject to compatibility and license review |
| Audio production | Planned | Phase 8 |
| Visual asset management | Planned | Phase 9 |
| Image-based video and animation | Planned | Phase 10; keyframes, camera motion, layers, transitions and compositing are required |
| Subtitles and synchronization | Planned | Phase 11 |
| FFmpeg video assembly | Planned | Phase 12 |
| YouTube metadata and thumbnails | Planned | Phase 13 |
| Android mobile application | Planned | Phase 14; includes required in-app Downloads / Models & Components manager backed by SQLite; large model/resource payloads are opt-in downloads outside the APK. Specification: [IN_APP_COMPONENT_DOWNLOADS.md](IN_APP_COMPONENT_DOWNLOADS.md). |
| Performance, reliability and release | Planned | Phase 15 |
| Lightweight local image/video AI experiments | Planned | Phase 16; optional and benchmark-gated |

## Verification summary

- Foundation tests: 4 passed on the user's Termux device.
- Environment detection tests: 5 passed on the user's Termux device.
- Full suite: 9 tests passed on the user's Termux device after pulling `e0df272`.
- Storage implementation: user confirmed all Termux checks passed on 2026-11-01. The detailed command output was not included in the confirmation.
- Local inference interface: user confirmed the requested latest Termux verification was all good on 2026-11-01. The user did not paste command output, so individual test counts and device details are not independently recorded.
- Native llama.cpp build: user pasted successful Termux output on 2026-11-01. Upstream checkout built for Android aarch64 with Clang 21.1.8; `llama-cli --version` reported `0.8.0-dev` (build 1, ggml commit `a91eab6`) and `--help` printed CLI usage. This verifies native build and executable startup, not model loading or inference.
- Observed total memory: 12,188,905,472 bytes; this is total physical memory, not the application's safe memory budget.
- Direct device check: `getprop ro.build.version.release` = 15 and `getprop ro.build.version.sdk` = 35 (2026-11-01). This supersedes the earlier detector's API 24 report for OS identification; investigate the detector discrepancy separately.
- GitHub Actions CI: run #17 on commit `90607c0` completed successfully; all 43 tests passed on GitHub Actions with Python 3.12.
- llama.cpp adapter: Phase 3, Task 4; user pasted Termux results on 2026-11-01 confirming the initial 34-test adapter suite passed and, after the optional context-size change, all 44 repository tests passed. The installed `llama-cli --help` output confirms `--ctx-size`, and explicit executable discovery returned `Available: True`. This is device verification of tests, CLI option compatibility and executable discovery. No actual GGUF model load or text generation has been run.
- GitHub Actions run #20 for commit `d45e9fc` passed all 44 tests (Python CI); this includes validation of the new optional CLI context-size argument. Termux verification of this change is still pending.
- Model registry: user confirmed all 43 repository tests passed on Termux on 2026-11-01. Automated tests cover schema migration, registration, checksum/provenance persistence, invalid inputs, duplicate records, file tampering/missing files and SQLite integrity using synthetic GGUF fixtures. No actual model weights have been downloaded or loaded.
- Production capabilities: no story, model inference, TTS, image generation or video production engine is claimed as implemented.

## Next task

**Current task: Phase 3, Task 6 — benchmark the pinned Qwen GGUF candidate and verify real offline inference.** Candidate selection and provenance review are recorded in [MODEL_CANDIDATES.md](MODEL_CANDIDATES.md). The exact official file is pinned by repository revision and SHA-256. The user's earlier device check (2026-11-01) showed 6,849,160 kB available RAM and 195 GB free on the filesystem backing Termux paths; refresh both immediately before download and loading. No model has been downloaded or loaded. Explicit user approval is still required before download. After approval: acquire outside Git, verify SHA-256, run bounded-context inference offline, measure resource/performance behavior, and register the verified local file.


## Phase 3, Task 6 — candidate decision

- Selected benchmark candidate: Qwen2.5-1.5B-Instruct-GGUF, Q4_K_M, from the official Qwen publisher repository.
- Immutable source revision, exact filename, byte size, license, and expected SHA-256 are recorded in [MODEL_CANDIDATES.md](MODEL_CANDIDATES.md).
- Selection is a benchmark candidate only, not a production default. No model file has been downloaded, loaded, or benchmarked.
- The user's latest device measurements are a preflight snapshot, not a persistent safety guarantee. Recheck available memory and free space immediately before download and inference.
- Explicit user approval is required before downloading the approximately 1.12 GB model. Keep weights in `$HOME/models`, never in the Git repository.


## Product requirement recorded — in-app component downloads

On 2026-11-01 the user requested that, when the Android APK is built, its options include in-app download buttons for large AI models and supported system/resource components, with component/download state stored in the app database. This is now a required Phase 14 feature, specified in [IN_APP_COMPONENT_DOWNLOADS.md](IN_APP_COMPONENT_DOWNLOADS.md). It is a documented requirement only; no downloader UI, download service or new database tables are claimed implemented. Continue the current Phase 3 real-inference task in roadmap order; implement the catalog/download/install tables and Android UI in Phase 14. Large model/data files stay outside the APK and SQLite; only metadata/state is stored in SQLite. Arbitrary executable code and Android OS packages must not be downloaded dynamically by this manager.
