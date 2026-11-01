"""Local inference interfaces and backend adapters."""
from storyforge.runtime.interface import (
    GenerationError, GenerationRequest, GenerationResult, InferenceBackend,
    InferenceRuntimeError, ModelLoadError, ModelSpec, RuntimeUnavailableError,
)
from storyforge.runtime.llama_cpp import LlamaCppCliBackend

__all__ = [
    "GenerationError", "GenerationRequest", "GenerationResult",
    "InferenceBackend", "InferenceRuntimeError", "LlamaCppCliBackend",
    "ModelLoadError", "ModelSpec", "RuntimeUnavailableError",
]
