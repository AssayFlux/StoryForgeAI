"""Subprocess adapter for the local llama.cpp command-line runner.

The adapter invokes a user-installed `llama-cli` executable. It never downloads
models, invokes a shell, or falls back to a remote inference service.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable

from storyforge.runtime.interface import (
    GenerationError, GenerationRequest, GenerationResult,
    ModelLoadError, ModelSpec, RuntimeUnavailableError,
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class LlamaCppCliBackend:
    """Run GGUF inference through a local llama.cpp `llama-cli`.

    llama.cpp loads the model afresh for each generation process. The adapter
    retains only a validated model reference between calls.
    """

    def __init__(
        self,
        executable: str | Path = "llama-cli",
        *,
        threads: int | None = None,
        timeout_seconds: float = 600.0,
        runner: CommandRunner = subprocess.run,
    ) -> None:
        executable_text = str(executable).strip()
        if not executable_text:
            raise ValueError("executable must not be empty")
        if threads is not None and threads < 1:
            raise ValueError("threads must be at least 1")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._executable = executable_text
        self._threads = threads
        self._timeout_seconds = timeout_seconds
        self._runner = runner
        self._model: ModelSpec | None = None

    @property
    def backend_name(self) -> str:
        return "llama.cpp-cli"

    @property
    def loaded_model(self) -> ModelSpec | None:
        """Return the currently selected model reference, if any."""
        return self._model

    def _resolve_executable(self) -> str | None:
        candidate = Path(self._executable).expanduser()
        if candidate.is_absolute() or candidate.parent != Path("."):
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate.resolve())
            return None
        return shutil.which(self._executable)

    def is_available(self) -> bool:
        return self._resolve_executable() is not None

    def load_model(self, model: ModelSpec) -> None:
        """Select an existing, non-empty GGUF file for subsequent inference."""
        if model.format.lower() != "gguf":
            raise ModelLoadError(
                f"Unsupported model format {model.format!r}; this backend requires GGUF"
            )
        path = model.path.expanduser()
        try:
            if not path.is_file():
                raise ModelLoadError(f"GGUF model file does not exist: {path}")
            if path.stat().st_size <= 0:
                raise ModelLoadError(f"GGUF model file is empty: {path}")
        except OSError as exc:
            raise ModelLoadError(f"Cannot access GGUF model file {path}: {exc}") from exc
        if not self.is_available():
            raise RuntimeUnavailableError(
                f"Cannot find executable {self._executable!r}; install/build llama.cpp "
                "and configure the llama-cli executable path"
            )
        self._model = ModelSpec(
            model_id=model.model_id,
            path=path.resolve(),
            format="gguf",
            metadata=dict(model.metadata),
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate text using one bounded llama-cli subprocess."""
        if self._model is None:
            raise ModelLoadError("No GGUF model selected; call load_model() first")
        executable = self._resolve_executable()
        if executable is None:
            raise RuntimeUnavailableError(
                f"llama.cpp executable {self._executable!r} is no longer available"
            )
        command: list[str] = [
            executable,
            "--model", str(self._model.path),
            "--prompt", request.prompt,
            "--n-predict", str(request.max_tokens),
            "--temp", str(request.temperature),
            "--top-p", str(request.top_p),
            "--no-display-prompt",
            "--no-show-timings",
            "--simple-io",
            "--single-turn",
        ]
        if request.system_prompt:
            command.extend(["--system-prompt", request.system_prompt])
        if request.seed is not None:
            command.extend(["--seed", str(request.seed)])
        if self._threads is not None:
            command.extend(["--threads", str(self._threads)])

        started = time.monotonic()
        try:
            completed = self._runner(
                command,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
                timeout=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise GenerationError(
                f"llama.cpp generation exceeded {self._timeout_seconds:g} seconds"
            ) from exc
        except FileNotFoundError as exc:
            raise RuntimeUnavailableError(
                f"llama.cpp executable could not be started: {executable}"
            ) from exc
        except OSError as exc:
            raise RuntimeUnavailableError(f"Cannot start llama.cpp: {exc}") from exc

        duration = max(0.0, time.monotonic() - started)
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            if len(detail) > 2000:
                detail = detail[-2000:]
            message = f"llama.cpp exited with status {completed.returncode}"
            if detail:
                message = f"{message}: {detail}"
            raise GenerationError(message)

        output = (completed.stdout or "").strip()
        if not output:
            detail = (completed.stderr or "").strip()
            suffix = f": {detail[-1000:]}" if detail else ""
            raise GenerationError(f"llama.cpp returned no generated text{suffix}")

        # Reverse-prompt is interactive on some builds. Trim captured output
        # instead so generation never waits for further terminal input.
        stop_positions = [
            output.find(sequence)
            for sequence in request.stop_sequences
            if output.find(sequence) >= 0
        ]
        if stop_positions:
            output = output[: min(stop_positions)].rstrip()

        return GenerationResult(
            text=output,
            backend=self.backend_name,
            finish_reason="stop" if stop_positions else "completed",
            duration_seconds=duration,
            metadata={
                "executable": executable,
                "model_id": self._model.model_id,
                "exit_code": completed.returncode,
            },
        )

    def unload_model(self) -> None:
        """Forget the selected model; any generation process has already exited."""
        self._model = None
