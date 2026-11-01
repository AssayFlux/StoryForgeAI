# Local inference

StoryForge exposes a backend-neutral inference contract in `storyforge.runtime`
and a local llama.cpp command-line adapter named `LlamaCppCliBackend`.

## llama.cpp CLI adapter

The adapter invokes an existing local `llama-cli` executable. It does not
install llama.cpp, download models, or access a remote service.

```python
from pathlib import Path
from storyforge.runtime import GenerationRequest, LlamaCppCliBackend, ModelSpec

backend = LlamaCppCliBackend(
    executable="llama-cli",  # or an explicit executable path
    threads=2,               # optional CPU thread limit
    timeout_seconds=600,
)
backend.load_model(ModelSpec("story-model", Path("~/models/story.gguf")))
result = backend.generate(
    GenerationRequest(
        prompt="Write a short opening scene.",
        max_tokens=128,
        temperature=0.7,
    )
)
print(result.text)
backend.unload_model()
```

### Behavior and limits

- The executable is resolved from `PATH` or an explicit executable path.
- Only an existing, non-empty GGUF file is accepted. No model download occurs.
- Commands are passed as an argument list to `subprocess.run`; no shell is used.
- llama.cpp loads the model afresh for each generation process. The adapter
  retains only its validated model reference between calls.
- Generation has a configurable timeout and captures stdout/stderr. Missing
  executables, process failures, timeouts, and empty output become typed errors.
- Stop sequences are applied to captured output. This trims returned text but
  does not interrupt token generation early.
- The adapter currently uses CLI output as plain text. Token counts and detailed
  performance metrics are not yet exposed.
- Automated tests mock the subprocess; actual model loading and inference still
  require a local GGUF file and device verification.

## Local model registry

The `storyforge.models.ModelRegistry` API records an already-present GGUF file.
It never downloads, copies, moves, deletes, or loads model weights. The path
remains where the user placed it; users must keep that file available.

Registration requires a model name and explicit license identifier/name.
Source name/URI and attribution can also be recorded. The registry validates
the GGUF magic and supported header version, records file size and a streaming
SHA-256 checksum (1 MiB chunks), and stores the metadata in SQLite schema v2.
The file itself is never stored in SQLite.

```python
from storyforge.models import ModelRegistry
from storyforge.storage import Database

registry = ModelRegistry(Database("storyforge.db"))
model = registry.register_local_model(
    "/storage/emulated/0/Download/story-model.gguf",
    name="Story model",
    license_id="LICENSE-ID",
    license_name="License name",
    source_name="Model publisher",
    source_uri="https://example.invalid/model-card",
    attribution="Required attribution, if any",
)
print(model["id"], model["sha256"], model["integrity_status"])
print(registry.check_integrity(model["id"])["integrity_status"])
```

Integrity checks classify a file as `valid`, `missing`, `modified`, or
`invalid`. Rechecking hashes the whole file, so it can take time for multi-GB
weights; it uses bounded memory. Registration is local-only and performs no
network request. A registered model is not automatically selected for
inference; model selection remains a separate explicit action.

## Phase 3 benchmark candidate (not downloaded)

The current benchmark candidate is documented in [MODEL_CANDIDATES.md](MODEL_CANDIDATES.md):

- Publisher repository: `Qwen/Qwen2.5-1.5B-Instruct-GGUF` (official Qwen account)
- Model: Qwen2.5-1.5B-Instruct, 1.54B parameters, Q4_K_M quantization
- Exact file: `qwen2.5-1.5b-instruct-q4_k_m.gguf`
- Pinned repository revision: `91cad51170dc346986eccefdc2dd33a9da36ead9`
- Exact file size: 1,117,320,736 bytes
- Expected SHA-256: `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`
- License: Apache-2.0

This is a test candidate, not an approved default model. The model weights must
live outside Git, for example under `$HOME/models`. Do not download until the
user explicitly approves. After approval, download from the pinned revision,
verify the full SHA-256 before registration, then register the existing file
with `ModelRegistry`. A matching filename alone is not sufficient provenance.

### Device benchmark protocol

1. Refresh `MemAvailable` and free space on the exact model destination filesystem.
2. Record Android version/API, device/SoC, battery percentage, temperature if
   available, llama.cpp version/commit, and CPU thread setting.
3. Use a bounded context of 2,048 tokens and at most 64 generated tokens for the
   first smoke test. Confirm the installed CLI supports the context-size flag
   before running; do not silently assume flags from a different llama.cpp build.
4. Measure cold startup/model-load time, prompt-processing throughput,
   generation throughput, and peak process RSS. Repeat a short run only after
   the first run completes safely; note thermal/battery changes.
5. Enable airplane mode and turn off Wi-Fi/mobile data before the inference
   run. Generate a short response with the local executable and local file.
   The adapter has no remote backend or cloud fallback; the test must still
   succeed with networking disabled.
6. Record raw output/timings and all settings in the benchmark report. Do not
   mark the task accepted until real generation, integrity verification,
   missing/incompatible-model errors, and low-memory behavior have been
   checked on the target device.

The last reported device snapshot (2026-11-01) showed 6,849,160 kB
`MemAvailable` and 195 GB free on the filesystem backing Termux paths. These
values are historical observations, not a runtime guarantee; refresh them
before the model is downloaded or loaded.

## Termux verification

From the repository root:

```sh
python -m unittest discover -s tests -v
```

The registry tests use small synthetic GGUF-header fixtures, not real model
weights. The user confirmed all 43 repository tests passed on Termux on
2026-11-01, accepting the registry's migration, persistence, validation and
integrity test coverage. No real GGUF model has yet been downloaded, loaded,
or used for inference.
