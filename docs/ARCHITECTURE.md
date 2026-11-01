# Architecture

## Current foundation

StoryForge AI starts as a Python package with configuration and tests. The command-line production engine and graphical interface are deliberately deferred until the underlying modules exist.

## Architectural boundaries

The planned package areas are:

- `core`: shared types, validation, errors, and orchestration contracts.
- `ai/models`: model metadata, explicit model installation, and local inference adapters.
- `stories`: story structures, script generation, and revision workflows.
- `characters`: character profiles and continuity records.
- `scenes`: scene breakdowns, timing estimates, and visual descriptions.
- `voice`: offline TTS adapters, voice profiles, and narration segmentation.
- `visuals`: local asset catalogs, references, composition, and image effects.
- `audio`: music, ambience, effects, and mixing.
- `subtitles`: subtitle generation, timing, and export.
- `video`: FFmpeg orchestration and render validation.
- `projects`: project lifecycle and production state.
- `youtube`: metadata, thumbnails, Shorts adaptations, and optional publishing integration.
- `storage`: SQLite repositories and filesystem access.
- `utils`: small cross-cutting utilities that do not own domain behavior.

Modules must depend on documented interfaces rather than importing each other's internal implementation. Keep imports acyclic. Optional engines must fail with actionable diagnostics when their models or native dependencies are absent.

## Data and privacy

Project metadata will use SQLite and JSON where appropriate. Generated media and downloaded models stay in user-controlled local storage and are not committed to Git. Network access must be explicit, opt-in, and visible to the user. Core generation must not require a network connection after the required local resources are present.

## Resource management

The initial device target is Android 15, ARM64, and 8 GB RAM. The application must not assume desktop-class acceleration or load multiple large models concurrently. Long audio/video operations should be segmented, cancellable, and recoverable. Resolution, bitrate, context size, and generation limits must be configurable.

## Compatibility policy

A successful desktop test or CI run does not establish Android compatibility. Android verification requires testing on a real supported device and recording the device, Android version, Termux/Python versions, commands, and results in the compatibility documentation.
