# Local inference interface

StoryForge defines a backend-neutral contract in `storyforge.runtime`. The contract separates orchestration and story-generation code from the implementation used to execute a local model.

## Contract

- `ModelSpec` identifies a model already stored locally. Constructing it does not download, open, or validate the model file.
- `GenerationRequest` carries a prompt and common sampling controls, with validation at the boundary.
- `GenerationResult` carries generated text, a finish reason, and optional token/timing metadata.
- `InferenceBackend` defines availability, model loading, generation, and model unloading.
- `InferenceRuntimeError` and its specific subclasses distinguish unavailable runtimes, model-loading failures, and generation failures.

A concrete backend must not silently use a remote service. Missing executables, libraries, or model files must produce actionable local errors. Model installation/import and licensing metadata belong to later model-registry work, not this interface.

## Intended lifecycle

1. Ask the selected backend whether its local runtime is available.
2. Load a `ModelSpec` referring to an explicitly installed local model.
3. Submit one or more validated `GenerationRequest` values.
4. Persist the result through the application layer.
5. Unload the model when the stage finishes or memory must be released.

The interface does not prescribe subprocess invocation, llama.cpp flags, threading, context allocation, or Android-specific build details. Those belong in a future adapter and must be benchmarked on the target device.

## Current limitation

This commit defines and tests the contract only. It does not implement a llama.cpp adapter, perform inference, install dependencies, download model weights, or establish Android compatibility.
