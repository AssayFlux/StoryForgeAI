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

## Termux verification

From the repository root:

```sh
python -m unittest discover -s tests -v
```

The registry tests use small synthetic GGUF-header fixtures, not real model
weights. Device verification must confirm migration, persistence, file
integrity checks and no unexpected file movement. No real GGUF model has yet
been loaded or used for inference.
