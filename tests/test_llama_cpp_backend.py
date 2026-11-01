"""Tests for the llama.cpp CLI adapter without requiring a model/runtime."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from storyforge.runtime import (
    GenerationError, GenerationRequest, ModelLoadError, ModelSpec,
    RuntimeUnavailableError,
)
from storyforge.runtime.llama_cpp import LlamaCppCliBackend


class LlamaCppCliBackendTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.executable = self.root / "llama-cli"
        self.executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.executable.chmod(0o755)
        self.model_path = self.root / "tiny.gguf"
        self.model_path.write_bytes(b"GGUF test fixture")
        self.calls = []

    def tearDown(self):
        self.temp_dir.cleanup()

    def fake_runner(self, command, **kwargs):
        self.calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "A short generated story.", "")

    def make_backend(self, runner=None, **kwargs):
        return LlamaCppCliBackend(
            self.executable, runner=runner or self.fake_runner, **kwargs
        )

    def load(self, backend):
        backend.load_model(ModelSpec("tiny", self.model_path))

    def test_backend_is_available_and_has_stable_name(self):
        backend = self.make_backend()
        self.assertTrue(backend.is_available())
        self.assertEqual(backend.backend_name, "llama.cpp-cli")

    def test_missing_or_empty_model_is_rejected(self):
        backend = self.make_backend()
        with self.assertRaises(ModelLoadError):
            backend.load_model(ModelSpec("missing", self.root / "missing.gguf"))
        empty = self.root / "empty.gguf"
        empty.touch()
        with self.assertRaises(ModelLoadError):
            backend.load_model(ModelSpec("empty", empty))

    def test_unsupported_format_is_rejected(self):
        backend = self.make_backend()
        with self.assertRaises(ModelLoadError):
            backend.load_model(ModelSpec("model", self.model_path, format="safetensors"))

    def test_missing_executable_is_reported(self):
        backend = LlamaCppCliBackend(self.root / "not-installed")
        self.assertFalse(backend.is_available())
        with self.assertRaises(RuntimeUnavailableError):
            backend.load_model(ModelSpec("tiny", self.model_path))

    def test_generate_requires_selected_model(self):
        backend = self.make_backend()
        with self.assertRaises(ModelLoadError):
            backend.generate(GenerationRequest("hello"))

    def test_generate_builds_argument_list_and_returns_result(self):
        backend = self.make_backend(threads=2)
        self.load(backend)
        request = GenerationRequest(
            "Write a story; do not interpret shell syntax: $(id)",
            max_tokens=48, system_prompt="You are a storyteller.",
            temperature=0.4, top_p=0.8, seed=17,
        )
        result = backend.generate(request)
        command, options = self.calls[0]
        self.assertEqual(command[0], str(self.executable.resolve()))
        self.assertIn(request.prompt, command)
        self.assertIn(request.system_prompt, command)
        self.assertIn("--single-turn", command)
        self.assertIn("48", command)
        self.assertIn("17", command)
        self.assertIn("2", command)
        self.assertEqual(options["stdin"], subprocess.DEVNULL)
        self.assertEqual(result.text, "A short generated story.")
        self.assertEqual(result.backend, "llama.cpp-cli")
        self.assertEqual(result.finish_reason, "completed")
        self.assertEqual(result.metadata["model_id"], "tiny")

    def test_stop_sequences_are_applied_to_captured_text(self):
        backend = self.make_backend()
        self.load(backend)
        backend._runner = lambda command, **kwargs: subprocess.CompletedProcess(
            command, 0, "Beginning<END>discarded", ""
        )
        result = backend.generate(GenerationRequest("hello", stop_sequences=("<END>",)))
        self.assertEqual(result.text, "Beginning")
        self.assertEqual(result.finish_reason, "stop")

    def test_nonzero_exit_becomes_generation_error(self):
        backend = self.make_backend(
            runner=lambda command, **kwargs: subprocess.CompletedProcess(
                command, 2, "", "model failed"
            )
        )
        self.load(backend)
        with self.assertRaisesRegex(GenerationError, "model failed"):
            backend.generate(GenerationRequest("hello"))

    def test_timeout_becomes_generation_error(self):
        def timeout(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        backend = self.make_backend(runner=timeout, timeout_seconds=3)
        self.load(backend)
        with self.assertRaisesRegex(GenerationError, "3 seconds"):
            backend.generate(GenerationRequest("hello"))

    def test_unload_is_idempotent(self):
        backend = self.make_backend()
        self.load(backend)
        backend.unload_model()
        backend.unload_model()
        self.assertIsNone(backend.loaded_model)


if __name__ == "__main__":
    unittest.main()
