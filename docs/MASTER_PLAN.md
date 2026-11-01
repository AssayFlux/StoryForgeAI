# StoryForge AI — Master Product & Engineering Plan

**Plan status:** Active project baseline  
**Repository:** https://github.com/AssayFlux/StoryForgeAI  
**Primary product goal:** A fully offline-capable, Android-first mobile application for producing high-quality AI-assisted stories and finished YouTube-style videos, including coherent characters, scene design, narration, visual animation, sound, subtitles, editing, and export.

This document is the project's source of truth for scope, engineering priorities, phase order, acceptance gates, and the next task. Every development session must read this plan and `docs/STATUS.md` before proposing or making repository changes. Update both when an accepted milestone changes.

---

## 1. Product vision

Build a local-first creative production studio that takes a user's idea and guides it through a controllable, resumable pipeline:

**Idea / brief → story research and planning → script → story analysis → characters and continuity → scenes and shots → visual assets → animation and motion → narration and sound → subtitles → video edit and render → quality checks → publishing package.**

The final product is an Android mobile application. Termux is the initial development and validation environment, not the intended permanent user experience. The architecture must support a later Android interface and packaging path without tying core business logic to a terminal.

### Non-negotiable product principles

1. **Offline inference and production:** After the user has explicitly installed/downloaded the required models, runtimes, fonts, and assets, core story, analysis, voice, visual, editing, and export workflows must work without internet access.
2. **No cloud dependency:** No paid API, hosted inference, mandatory account, remote database, or cloud rendering is required. No automatic upload or silent network fallback.
3. **Mobile-first execution:** ARM64 Android, no root, limited memory, thermal headroom, battery, storage, and Android background-execution constraints are first-class design constraints.
4. **Modular engines:** Story, analysis, database, model runtime, TTS, image, animation, audio, subtitles, rendering, and UI have defined interfaces and can be tested or replaced independently.
5. **Sequential, resource-aware jobs:** Heavy tasks run in bounded stages, not all at once. Jobs can be queued, paused when safe, cancelled, resumed, retried, and recovered after process termination.
6. **Persistent project state:** User work is saved incrementally. A failed stage must not force regeneration of completed stages.
7. **Human control:** Generated changes are versioned; users can inspect, approve, reject, and regenerate. Analysis does not silently rewrite source content.
8. **Production quality through validation:** Exports must be checked for technical integrity and content consistency. A feature is not complete merely because a demo runs.
9. **Honest claims:** Desktop tests do not prove Android compatibility. A feature is not described as offline, high-quality, production-ready, or Android-supported until the relevant acceptance tests pass.
10. **Open and maintainable:** Prefer documented, redistributable components and model weights with licenses compatible with the intended distribution. Record licenses and attribution.

---

## 2. Target platform and operating envelope

### Initial engineering target

- Android ARM64 device; intended target class is Android 15 and approximately 8 GB RAM.
- Termux, no root, Python-based core during early development.
- Actual device output currently reports ARM64, Termux, Python 3.14.8, and about 12.19 GB total memory. Direct device checks on 2026-11-01 report Android 15 / API 35 (`getprop`); this supersedes the earlier environment-detector API 24 result for OS identification. Investigate the detector discrepancy before trusting its API-level field.
- Total physical RAM is not the same as memory available to StoryForge. Runtime budgets must use current available memory and leave room for Android and other processes.

### Runtime policy

- Detect device capabilities at runtime; do not hard-code one phone's RAM as available model memory.
- Start with small quantized language models (roughly 1B–3B parameters as candidates), benchmark before selecting defaults.
- Load one large model/engine at a time where possible; release resources between stages.
- Make context length, CPU threads, batch size, image resolution, frame rate, render preset, and concurrency configurable within safe limits.
- Prefer CPU-first ARM64 support. Treat GPU/NPU acceleration as optional until verified on the actual device.
- Check free disk space before downloads, generation, caching, and rendering.
- Provide low-memory and low-storage handling, progress reporting, cancellation, and resumability.
- Never promise desktop-class text-to-video generation on a phone.

---

## 3. Product architecture

### Layer A — Android application and user experience

The end product is a mobile app with project dashboard, editor, scene/shot timeline, model manager, job queue, preview, settings, and export screens. Early development can use a Termux CLI for validation, but core logic must remain UI-independent. Choose the final Android UI/packaging technology only after a small compatibility spike and explicit evaluation; do not prematurely bind the project to a framework.

### Layer B — orchestration and resource manager

- Pipeline planner with explicit stage dependencies.
- Persistent job queue and per-stage state machine.
- Resource manager for memory, CPU threads, storage, temperature signals when accessible, and safe concurrency.
- Cancellation and checkpoint semantics.
- Structured logs, error categories, retries, and crash recovery.
- Offline policy enforcement and network-disabled tests for inference/production paths.

### Layer C — domain engines

Independent modules with versioned input/output contracts:
- Project and asset management
- Story brief, outline, script, dialogue and revision
- Story analysis: structure, pacing, continuity, tone, age/safety preferences, and quality reports
- Character, location, world and continuity bible
- Scene breakdown, shot list, storyboard and visual prompt generation
- Local language-model runtime and model registry
- Offline text-to-speech and voice profiles
- Audio assembly, ambience, effects, mixing and loudness checks
- Image generation or local image workflows, asset import and curation
- Animation/motion and compositing
- Subtitle generation, timing, formatting and synchronization
- FFmpeg-based editing, transitions, encoding and export
- Thumbnail and YouTube metadata generation

### Layer D — persistence and local files

- SQLite is the source of truth for structured project state, relationships, jobs, model metadata, revisions, and asset records.
- JSON is used for versioned structured payloads and interchange where appropriate.
- Large media and model weights live as files, not SQLite blobs.
- Store relative paths, hashes, sizes, formats, provenance, and generation settings in the database.
- Use schema migrations, foreign keys, indexes, transactions, integrity checks, and tested backup/restore.
- Evaluate SQLite WAL mode for the actual access pattern; use one controlled writer/serialized write queue where needed.
- Keep project data in a configurable app-owned directory and design for Android storage permission/scoped-storage realities.

---

## 4. High-quality video and animation strategy

"Proper video and animation" is a core product requirement, not just a folder of still images. However, the implementation must be staged according to what mobile hardware can actually sustain.

### Required baseline: deterministic cinematic assembly

The first dependable video system must support:
- Multiple scenes and shots with explicit durations and ordering.
- Image sequences and imported/generated artwork.
- Camera motion such as pan, tilt, zoom, crop, and Ken Burns movement.
- Keyframed transforms, easing, fades, transitions, overlays, titles, and compositing.
- Layered foreground/background assets and parallax-style 2.5D motion where assets allow it.
- Narration, music, ambience and sound effects on a timeline.
- Subtitle timing and styling.
- Project preview proxies and staged/segment rendering.
- Reproducible FFmpeg export presets and technical validation.

This baseline can produce an actual edited video with motion and animation; it must not be represented as full generative text-to-video.

### Advanced visual generation: staged and optional

Investigate local image generation, frame interpolation, motion transfer, and compact video-generation models as separate capabilities. Benchmark model size, RAM/VRAM requirements, speed, heat, battery, output quality, licensing, and Android build feasibility. Advanced generative video remains experimental until proven on target hardware. The app must still create a complete video using the deterministic animation/editing pipeline when generative video is unavailable.

### Quality controls

- Character appearance references and scene continuity checks.
- Consistent aspect ratio, resolution, frame rate, and color handling.
- Audio/video synchronization and subtitle timing validation.
- Missing asset and broken-path checks.
- Render previews before full-quality export.
- User-selectable quality presets with clear time/storage estimates.
- Export integrity checks (container, streams, duration, dimensions, audio presence).

---

## 5. Data model and database plan

**Android in-app downloads are a required Phase 14 capability.** The app must provide an in-app Downloads / Models & Components area with explicit download/update/remove actions for large optional models and resource packs. Download state, catalog metadata, licenses and verified installation records belong in SQLite; binaries remain files. See [IN_APP_COMPONENT_DOWNLOADS.md](IN_APP_COMPONENT_DOWNLOADS.md) for the required UX, proposed schema, safety rules and acceptance criteria. Do not bundle large model weights into the APK, and do not dynamically download executable code as if it were model data.

SQLite schema will be introduced early, before substantial generation features depend on it. Initial entities should include:

- `projects`, `project_settings`
- `stories`, `story_versions`, `story_analysis`
- `characters`, `character_versions`, `locations`, `world_facts`
- `scenes`, `shots`, `storyboards`
- `assets`, `asset_usages`, `asset_provenance`
- `models`, `model_files`, `model_licenses`
- `component_catalog`, `component_downloads`, `installed_components` (Phase 14 migration; see [IN_APP_COMPONENT_DOWNLOADS.md](IN_APP_COMPONENT_DOWNLOADS.md))
- `generation_jobs`, `pipeline_steps`, `job_events`
- `voice_profiles`, `audio_tracks`, `subtitle_tracks`
- `timelines`, `render_jobs`, `exports`
- `app_settings`, `schema_migrations`

Use stable IDs, timestamps, explicit statuses, schema/version fields for JSON payloads, and foreign-key constraints. Avoid premature over-normalization; migrate as real workflows define the data. Store large binary assets on disk and maintain checksums in SQLite.

---

## 6. Development roadmap and acceptance gates

Work strictly in order. Each numbered phase is a milestone, not permission to skip acceptance criteria. Within a phase, implement one small task at a time. Do not start the next task until the current task is tested and accepted.

### Phase 1 — Repository foundation and Android compatibility baseline
**Status: Accepted.**
- Package structure, metadata, docs, CI baseline, tests, Android constraints.
- Acceptance: foundation tests pass; repository clean and synchronized.

### Phase 2 — Termux setup and environment detection
**Tasks 1–2 status: Accepted.**
- Task 1: read-only detection of Android/Termux, architecture, Python, API level, memory and Termux prefix — tested and accepted on device.
- Task 2: configurable local data paths and SQLite project/job persistence — user confirmed Termux verification passed on 2026-11-01.
- Direct device verification now confirms Android 15 / API 35 via `getprop` (2026-11-01). The earlier detector result of API 24 conflicts and should be debugged separately; do not use that detector field as proof of OS version until fixed.
- Acceptance: tests pass on device; missing platform information is non-fatal; no unexpected shell/network side effects; storage/database persistence and integrity checks pass.

### Phase 3 — Local AI runtime (llama.cpp / GGUF)
**Task 1: Build-path evaluation — completed.** Upstream Termux-native and Android NDK paths are compared in [LLAMA_CPP_EVALUATION.md](LLAMA_CPP_EVALUATION.md). No build or model was installed.
**Task 2: Backend-neutral inference interface — accepted after user-confirmed Termux verification (2026-11-01).** See [LOCAL_INFERENCE.md](LOCAL_INFERENCE.md). The contract is independent of llama.cpp process flags and native-library details. A concrete CLI backend was added later in Task 4; no model registry or actual GGUF inference has been verified yet.
**Tasks 1–3 completed:** build-path evaluation, backend-neutral inference interface, and native llama.cpp build feasibility. On 2026-11-01 the user built upstream llama.cpp natively in Termux on ARM64 using Clang 21.1.8 and CMake 4.4.5; `llama-cli --version` and `llama-cli --help` both ran successfully. The tested upstream checkout reports llama.cpp `0.8.0-dev`, build 1, ggml commit `a91eab6`. This verifies native compilation and CLI startup only; no GGUF model was loaded and no text inference has been tested.
**Task 4: llama.cpp CLI adapter — Termux verified and accepted (2026-11-01).** `LlamaCppCliBackend` lives in `storyforge/runtime/llama_cpp.py` and implements the existing backend-neutral protocol. It resolves an explicit/PATH executable, validates an existing non-empty GGUF file, invokes `llama-cli` with an argument list (no shell), supports bounded generation, sampling controls, optional thread limits and stop-text trimming, and maps runtime/process failures to typed errors. On the user's Termux device, the initial adapter suite passed all 34 tests; after adding the optional explicit context-size limit, the user confirmed all 44 repository tests passed. The installed llama.cpp help output confirmed the `--ctx-size` option, and explicit executable discovery returned `Available: True`. This accepts adapter integration, tests and CLI option compatibility only; no GGUF model has yet been loaded and no tokens generated. See [LOCAL_INFERENCE.md](LOCAL_INFERENCE.md).
**Task 5: Local model registry — Termux verified and accepted (2026-11-01).** SQLite schema v2 adds `models`, `model_files`, and `model_licenses`. `ModelRegistry.register_local_model` registers an existing local GGUF file without copying or moving it, requires explicit license metadata, validates the GGUF header, and records byte size plus streaming SHA-256. On-demand integrity checks distinguish `valid`, `missing`, `modified`, and `invalid`. The user confirmed all 43 repository tests passed on Termux, accepting the synthetic-fixture migration, persistence, validation and integrity coverage. No real model was downloaded or loaded. See [LOCAL_INFERENCE.md](LOCAL_INFERENCE.md).
**Task 6: Small-model selection and real offline inference — in progress.** A benchmark candidate has been selected and provenance pinned in [MODEL_CANDIDATES.md](MODEL_CANDIDATES.md): official Qwen/Qwen2.5-1.5B-Instruct-GGUF, Q4_K_M, exact file revision `91cad51170dc346986eccefdc2dd33a9da36ead9`, published SHA-256 and Apache-2.0 license. The user's device checks show adequate free storage and current available memory for a cautious test, but these readings must be refreshed immediately before download/load. The large GGUF remains outside Git and outside the StoryForge repository. Download is not authorized or started yet; obtain explicit user approval first. Then benchmark startup, peak RSS, prompt/prefill and generation throughput, temperature and battery observations at bounded context. Run real generation with network access disabled and verify no cloud fallback. Record exact model revision, file SHA-256, llama.cpp build, settings and measured results. Full Phase 3 acceptance also requires clean missing/incompatible-model errors and safe low-memory behavior.

### Phase 4 — Story engine
- Structured brief, outline, script, dialogue, revision and version history.
- Prompt templates and output schemas; bounded context and chunked processing.
- Acceptance: saved/reloaded projects, deterministic non-AI tests, local inference integration, user-approved revisions.

### Phase 5 — Character and continuity engine
- Character sheets, relationships, locations, world facts, reference descriptions and continuity ledger.
- Acceptance: continuity checks cite the conflicting story facts and never silently alter source material.

### Phase 6 — Story analysis and scene planning
- Story structure, pacing, tone, scene breakdown, shot list, storyboard and visual prompts.
- Analysis and generation remain separate.
- Acceptance: structured outputs validate against schemas and survive save/reload.

### Phase 7 — Offline TTS
- Evaluate available offline engines, voices, licenses, ARM64 compatibility and memory.
- Segment-based speech generation, pronunciation controls and voice consistency.
- Acceptance: speech generated without network; segments persist and can be regenerated independently.

### Phase 8 — Audio production
- Music/effects import, ambience, mixing, normalization and synchronization.
- Acceptance: reproducible audio render and technical checks.

### Phase 9 — Visual asset system
- Asset library, references, prompt metadata, local generation/import adapters and character consistency workflow.
- Acceptance: offline asset organization and complete provenance; any image model must pass device benchmarks before being enabled by default.

### Phase 10 — Image-based cinematic video and animation
- Storyboard-to-timeline, multiple shots, keyframes, camera moves, transitions, layers, 2.5D/parallax options, overlays and preview.
- Acceptance: a multi-scene animated video can be created from local assets entirely offline on the target device within documented resource limits.

### Phase 11 — Subtitles
- Subtitle generation/import, timing, styling, line breaking and synchronization.
- Acceptance: subtitle file and rendered output pass timing/format checks.

### Phase 12 — FFmpeg production and rendering
- Verify Termux FFmpeg build, codecs, filters and licensing; create render presets, proxies, segment rendering, resume and export validation.
- Acceptance: complete offline video export with verified streams, duration, dimensions, audio and subtitles.

### Phase 13 — YouTube package
- Titles, descriptions, chapters, tags, thumbnail composition and export bundle. No automatic publishing or upload by default.
- Acceptance: all metadata and thumbnail assets saved locally and editable.

### Phase 14 — Android mobile application
- Mobile project dashboard, editors, timeline, model manager, job queue, preview and settings.
- **Required in-app Downloads / Models & Components option:** provide user-triggered Download, Update and Remove actions for large optional GGUF models, offline TTS voices, image models and licensed resource packs. Show size, source, version, license, compatibility, checksum, storage requirements and progress; persist catalog/download/install state in SQLite; verify SHA-256 before atomic installation; support safe pause/resume/retry/recovery and Wi-Fi-only preference. Large weights/data stay outside the APK. See [IN_APP_COMPONENT_DOWNLOADS.md](IN_APP_COMPONENT_DOWNLOADS.md).
- Package native executable code/libraries in the APK/AAB or use approved platform delivery mechanisms; never create a generic downloader for arbitrary executable code or Android system packages.
- Select and validate app framework/packaging path; bridge to core engines without duplicating business logic.
- Acceptance: installable app on target Android version, local project workflows, permissions, lifecycle/recovery and offline operation verified; in-app component catalog/download manager passes the download, integrity, storage, recovery, database and offline acceptance checklist in [IN_APP_COMPONENT_DOWNLOADS.md](IN_APP_COMPONENT_DOWNLOADS.md).

### Phase 15 — Optimization, reliability and production release
- Profile memory, CPU, heat, battery, storage and render time.
- Improve resource scheduling, caching, cleanup, backups, crash recovery, accessibility and UX.
- Full test suite, device matrix where possible, documentation, versioning and reproducible release artifacts.
- Acceptance: release checklist passes on real target device; limitations documented; no unsupported compatibility or quality claims.

### Phase 16 — Optional lightweight AI experiments
- Evaluate small local image/video models, interpolation, motion tools or acceleration.
- Experiments must not destabilize the reliable production pipeline.
- Acceptance: each feature is separately benchmarked, licensed, opt-in and removable.

---

## 7. Task execution protocol (mandatory)

At the start of every development task:

1. Read this file, `docs/STATUS.md`, and the relevant source/tests/docs from the current repository branch.
2. Confirm the current branch/head and identify the exact next incomplete task.
3. State the task's purpose, scope, dependencies, and acceptance criteria.
4. Make only the changes required for that task. Do not bundle unrelated refactors or jump ahead.
5. Add or update tests and documentation with the implementation.
6. Run available automated checks. Clearly separate local/CI results from tests the user must run on Android.
7. Inspect the final diff and update `docs/STATUS.md` with evidence, limitations, and the next task.
8. Commit with a specific conventional commit message. Never claim a commit or push succeeded until confirmed.
9. Give exact Termux commands and the expected evidence for device verification.
10. Stop and wait for the user's results/acceptance before starting another task.

If a test fails, fix the current task only. Preserve accepted work. Never skip a phase because a later feature looks more exciting.

### Required response format for each task

- Current plan phase and exact task
- Repository state inspected
- What will change (and what will not)
- Acceptance criteria
- Implementation and tests
- Commit SHA/link, only after confirmed
- Exact user verification commands
- Current status and one next task

---

## 8. Definition of done for the overall product

StoryForge AI is not "production-ready" until all required product workflows operate as a coherent mobile application and the following are demonstrated on the target Android device:

- Install, launch, create, save, reopen, backup and restore projects.
- Run story generation and analysis with local models while network access is disabled.
- Maintain character, location and plot continuity across a multi-scene project.
- Generate offline narration and assemble audio.
- Produce a multi-scene video with real timeline structure, motion/keyframes/transitions and synchronized audio/subtitles.
- Render and validate a finished video using local tools.
- Pause/recover interrupted jobs without losing completed work.
- Operate within documented device resource limits and fail safely when resources are insufficient.
- Manage model files, licenses, storage and user data transparently.
- Pass automated tests and real-device acceptance checks.
- Provide clear setup, user, troubleshooting, privacy, licensing and release documentation.

A fully generative text-to-video model is not a prerequisite for the first complete production release. A reliable offline animation, compositing and editing system is required. Advanced generative video is an optional capability until a suitable model is proven on-device.

---

## 9. Current next action

Phase 1 and Phase 2 Tasks 1–2 are accepted. Phase 3 Task 1 (build-path evaluation) is documented. Phase 3 Task 2 (backend-neutral inference contract) is implemented and the user confirmed its Termux verification was all good on 2026-11-01. Direct `getprop` checks confirm Android 15/API 35; this supersedes the earlier API 24 detector reading, which remains a detector discrepancy to investigate. The confirmation did not include raw command output, so no additional test count or device details are asserted.

Phase 3, Tasks 1–3 are complete at the documented scope: the build-path evaluation, backend-neutral inference contract, and native Termux build/CLI smoke test. On 2026-11-01 the user confirmed that upstream llama.cpp built on the Android 15/API 35 ARM64 device with Clang 21.1.8 and CMake 4.4.5; `llama-cli --version` and `--help` both executed. No model was downloaded or loaded, so inference is not yet verified. The environment detector's earlier API 24 discrepancy remains open.
Phase 3, Task 4 is accepted after user-side Termux verification on 2026-11-01: all 34 repository tests passed; the installed `llama-cli --help` output contained every CLI option used by the adapter; and explicit executable discovery returned `Available: True`. This verifies the adapter's command compatibility and executable discovery on the device, not actual GGUF loading or text generation.
**Immediate next task: Phase 3, Task 6 — select and benchmark a small GGUF candidate, then verify real offline inference.** Task 5 is accepted after the user's Termux confirmation that all 43 tests pass. Before downloading anything, verify candidate licensing/provenance, current memory, and free space on the actual target filesystem; obtain explicit user approval. Keep inference fully local with network access disabled.

---

## 10. Change control

This plan is the default authority for implementation order and product scope. Changes are allowed when device tests, licensing, Android constraints, or better engineering evidence require them. Record any approved change in this document with its reason and update the status/next task. Do not silently change the product goal or skip required capabilities.
