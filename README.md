# StoryForge AI

**An offline-first, Android-first YouTube story and video production studio.**

StoryForge AI is an open-source project intended to turn a topic or idea into a connected multimedia production: a story or script, characters, scenes, narration, visual assets, audio, subtitles, an assembled video, and publishing metadata.

The project is being developed incrementally. The initial engineering target is an Android 15, ARM64 smartphone with 8 GB RAM, using Termux without root access.

## Project principles

- **Offline-first:** core production must work without an internet connection after optional resources have been installed.
- **Local by default:** projects, settings, and generated media remain on the device.
- **No silent uploads:** user content is never sent to an external service without an explicit user action.
- **No mandatory paid services:** cloud APIs and subscriptions are not required.
- **Hardware-aware:** small quantized models, sequential workloads, cancellation, and recovery are preferred.
- **Modular:** engines have clear interfaces and can be developed and tested independently.
- **Honest compatibility claims:** desktop CI success is not Android verification.

## Planned technology direction

| Area | Preferred direction |
|---|---|
| Application and orchestration | Python |
| Android development environment | Termux, no root |
| Local language models | llama.cpp with quantized GGUF models |
| Speech | Verified offline neural TTS implementation |
| Video processing | Android-compatible FFmpeg |
| Project metadata | SQLite and JSON |
| Configuration | TOML |
| Tests | Python unittest initially; GitHub Actions CI |

These are engineering directions, not claims that every engine is already implemented or verified on Android. Model downloads and optional asset acquisition will be explicit and separately managed.

## Development status

This repository currently contains the project foundation, read-only environment detection, and an initial local storage/SQLite layer. No story generation, model inference, TTS, image generation, or video production engine is claimed as implemented.

Read [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) for the authoritative product vision, architecture, phase order, acceptance gates, and mandatory task workflow. See [docs/STATUS.md](docs/STATUS.md) for the current verified milestone and next task, [docs/LLAMA_CPP_EVALUATION.md](docs/LLAMA_CPP_EVALUATION.md) for the local runtime build-path assessment, and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for contribution and local test instructions.

## Getting started

The current development baseline provides package metadata, tests, and reusable storage primitives. It does not yet provide a production CLI or media-generation pipeline.

Requirements:
- Python 3.11 or newer.
- Git (for cloning and updating the source).

Clone and run the foundation tests:

```sh
git clone https://github.com/AssayFlux/StoryForgeAI.git
cd StoryForgeAI
python -m unittest discover -s tests -v
```

Install the package in editable mode when needed:

```sh
python -m pip install -e .
```

On Android, install Python and Git from the Termux package repositories first. See [docs/ANDROID_COMPATIBILITY.md](docs/ANDROID_COMPATIBILITY.md) and [docs/STORAGE.md](docs/STORAGE.md). Actual Android-device validation remains a separate acceptance requirement.

## Repository layout

```text
config/                 Default application configuration
docs/                   Architecture, development, compatibility, and status
storyforge/             Python application package
  core/                 Shared foundations and interfaces
  storage/              Local data paths and SQLite persistence
tests/                  Automated tests
scripts/                Developer and maintenance scripts
assets/                 Small, redistributable project assets
models/                 Local model storage (not committed)
projects/               Local user project storage (not committed)
.github/workflows/      Continuous integration
```

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
