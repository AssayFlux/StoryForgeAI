"""Local inference interfaces and backend adapters."""

from storyforge.runtime.interface import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    InferenceBackend,
    InferenceRuntimeError,
    ModelLoadError,
    ModelSpec,
    RuntimeUnavailableError,
)

__all__ = [
    "GenerationError",
    "GenerationRequest",
    "GenerationResult",
    "InferenceBackend",
    "InferenceRuntimeError",
    "ModelLoadError",
    "ModelSpec",
    "RuntimeUnavailableError",
]
