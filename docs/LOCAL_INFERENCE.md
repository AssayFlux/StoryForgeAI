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

## Termux verification (2026-11-01)

The user ran `python -m unittest discover -s tests -v` in the StoryForgeAI checkout: **34 tests passed**. They also checked the locally built `$HOME/src/llama.cpp/build/bin/llama-cli --help`; the output confirmed all flags used by `LlamaCppCliBackend`: `--system-prompt`, `--single-turn`, `--no-display-prompt`, `--no-show-timings`, `--simple-io`, `--n-predict`, `--top-p`, and `--threads`. Finally, constructing `LlamaCppCliBackend` with that explicit executable path returned `Available: True`.

This is real-device verification of the repository suite, CLI option compatibility, and executable discovery. It is **not** a model-load or inference test: no GGUF file was selected, no generated tokens were observed, and offline inference remains unverified.

## Contract

- `ModelSpec` identifies a model already stored locally.
- `GenerationRequest` carries a prompt and common sampling controls.
- `GenerationResult` carries generated text, a finish reason, and optional usage/timing metadata.
- `InferenceBackend` defines availability, model selection, generation, and unloading.
- A concrete backend must never silently use a remote service.

## Lifecycle

1. Check `backend.is_available()`.
2. Select a local model with `backend.load_model(model_spec)`.
3. Submit validated `GenerationRequest` values.
4. Persist the result through the application layer.
5. Call `backend.unload_model()` when the stage finishes or memory must be released.
