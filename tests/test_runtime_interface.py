"""Tests for backend-neutral local inference contracts."""

from pathlib import Path
import unittest

from storyforge.runtime import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    InferenceBackend,
    InferenceRuntimeError,
    ModelLoadError,
    ModelSpec,
    RuntimeUnavailableError,
)


class FakeBackend:
    backend_name = "fake-local"

    def is_available(self) -> bool:
        return True

    def load_model(self, model: ModelSpec) -> None:
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return GenerationResult(
            text=f"generated: {request.prompt}",
            backend=self.backend_name,
            finish_reason="stop",
            prompt_tokens=3,
            generated_tokens=4,
            duration_seconds=0.1,
        )

    def unload_model(self) -> None:
        self.model = None


class RuntimeInterfaceTests(unittest.TestCase):
    def test_model_spec_normalizes_path_without_requiring_model_file(self) -> None:
        model = ModelSpec("small-model", Path("~/models/model.gguf"))
        self.assertEqual(model.path, Path("~/models/model.gguf").expanduser())
        self.assertEqual(model.format, "gguf")

    def test_rejects_invalid_model_spec(self) -> None:
        with self.assertRaises(ValueError):
            ModelSpec(" ", Path("model.gguf"))
        with self.assertRaises(ValueError):
            ModelSpec("model", Path("model.gguf"), format=" ")

    def test_generation_request_defaults_and_validation(self) -> None:
        request = GenerationRequest("Write a short story")
        self.assertEqual(request.max_tokens, 256)
        self.assertEqual(request.temperature, 0.7)
        self.assertEqual(request.top_p, 0.95)
        with self.assertRaises(ValueError):
            GenerationRequest(" ")
        with self.assertRaises(ValueError):
            GenerationRequest("prompt", max_tokens=0)
        with self.assertRaises(ValueError):
            GenerationRequest("prompt", temperature=2.1)
        with self.assertRaises(ValueError):
            GenerationRequest("prompt", top_p=0)
        with self.assertRaises(ValueError):
            GenerationRequest("prompt", seed=-1)
        with self.assertRaises(ValueError):
            GenerationRequest("prompt", stop_sequences=("",))

    def test_generation_result_validates_usage_and_timing(self) -> None:
        result = GenerationResult("hello", "fake", "stop", 2, 3, 0.5)
        self.assertEqual(result.generated_tokens, 3)
        with self.assertRaises(ValueError):
            GenerationResult("hello", "fake", "stop", generated_tokens=-1)
        with self.assertRaises(ValueError):
            GenerationResult("hello", "fake", "stop", duration_seconds=-0.1)

    def test_fake_backend_satisfies_protocol_and_runs_lifecycle(self) -> None:
        backend = FakeBackend()
        self.assertIsInstance(backend, InferenceBackend)
        self.assertTrue(backend.is_available())
        backend.load_model(ModelSpec("test", Path("/tmp/test.gguf")))
        result = backend.generate(GenerationRequest("hello"))
        self.assertEqual(result.text, "generated: hello")
        self.assertEqual(result.backend, "fake-local")
        backend.unload_model()
        self.assertIsNone(backend.model)

    def test_runtime_errors_share_a_base_class(self) -> None:
        for error in (RuntimeUnavailableError, ModelLoadError, GenerationError):
            self.assertTrue(issubclass(error, InferenceRuntimeError))


if __name__ == "__main__":
    unittest.main()
