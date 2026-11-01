"""Backend-neutral contracts for local language-model inference.

This module intentionally contains no llama.cpp process or native-library code.
Concrete backends implement :class:`InferenceBackend`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable


class InferenceRuntimeError(RuntimeError):
    """Base exception for local inference failures."""


class RuntimeUnavailableError(InferenceRuntimeError):
    """Raised when the selected local inference backend cannot run."""


class ModelLoadError(InferenceRuntimeError):
    """Raised when a local model cannot be loaded."""


class GenerationError(InferenceRuntimeError):
    """Raised when inference fails after a model has been loaded."""


@dataclass(frozen=True)
class ModelSpec:
    """A reference to a model already present on local storage."""

    model_id: str
    path: Path
    format: str = "gguf"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id must not be empty")
        if not str(self.path).strip():
            raise ValueError("model path must not be empty")
        if not self.format.strip():
            raise ValueError("model format must not be empty")
        object.__setattr__(self, "path", Path(self.path).expanduser())


@dataclass(frozen=True)
class GenerationRequest:
    """Validated, backend-independent text generation parameters."""

    prompt: str
    max_tokens: int = 256
    system_prompt: str | None = None
    temperature: float = 0.7
    top_p: float = 0.95
    seed: int | None = None
    stop_sequences: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")
        if not 0.0 < self.top_p <= 1.0:
            raise ValueError("top_p must be greater than 0 and at most 1")
        if self.seed is not None and self.seed < 0:
            raise ValueError("seed must be non-negative")
        if any(not sequence for sequence in self.stop_sequences):
            raise ValueError("stop sequences must not contain empty strings")


@dataclass(frozen=True)
class GenerationResult:
    """Text returned by a backend, with optional usage and timing metadata."""

    text: str
    backend: str
    finish_reason: str
    prompt_tokens: int | None = None
    generated_tokens: int | None = None
    duration_seconds: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.backend.strip():
            raise ValueError("backend must not be empty")
        if not self.finish_reason.strip():
            raise ValueError("finish_reason must not be empty")
        for name in ("prompt_tokens", "generated_tokens"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")


@runtime_checkable
class InferenceBackend(Protocol):
    """Lifecycle contract implemented by each local inference backend."""

    @property
    def backend_name(self) -> str:
        """Stable human-readable backend identifier."""
        ...

    def is_available(self) -> bool:
        """Return whether this backend's required runtime is available."""
        ...

    def load_model(self, model: ModelSpec) -> None:
        """Load a model from local storage; raise ModelLoadError on failure."""
        ...

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate text using the loaded model; raise GenerationError on failure."""
        ...

    def unload_model(self) -> None:
        """Release model resources; safe to call after a successful load."""
        ...
