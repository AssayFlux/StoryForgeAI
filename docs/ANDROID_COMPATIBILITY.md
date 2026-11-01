# Android and Termux compatibility

## Target

- Android 15
- ARM64 (AArch64)
- 8 GB device RAM
- Termux, installed from a trusted distribution source
- No root access

## Current verification status

The initial repository foundation passed its four standard-library tests on a Termux device. The environment-detection module is being added and must be exercised on the same device before it is marked Android verified. This does not establish compatibility of future native engines.

## Environment detection

The read-only detector is available from `storyforge.core.environment`:

```python
from storyforge.core.environment import detect_environment

info = detect_environment()
print(info)
```

It reports Android/Termux detection, OS name, normalized CPU architecture, Python version, Android API level when exposed by the Python runtime, total physical memory when procfs provides it, and the Termux prefix.

Detection reads environment variables and `/proc/meminfo`. It does not execute shell commands, install packages, change settings, or access the network. Missing platform information is represented as `None` rather than treated as a fatal error.

## Engineering constraints

- Use Termux-supported packages and binaries; verify availability before documenting an install command as supported.
- Prefer CPU-first ARM64 inference. Treat acceleration as optional until demonstrated on the target device.
- Investigate llama.cpp Android/Termux build and runtime behavior before selecting model formats or build flags.
- Start with small quantized GGUF instruction models (approximately 1B–3B parameters), and measure memory, speed, heat, and battery use.
- Load one model at a time and provide explicit model selection and download controls.
- Do not assume desktop ComfyUI, large Stable Diffusion pipelines, or large video-generation models are practical on the target device.
- Use FFmpeg only after confirming the selected Termux package/build supports the required codecs and filters.
- Keep generated data in app-controlled local storage and plan for Android storage permissions and scoped-storage behavior.

## Device verification record

No full device verification record exists yet. When testing is performed, record:
- Device model and chipset (if known)
- Android version and architecture
- Termux source/version
- Python and relevant native package versions
- Exact commands executed
- Test output, failures, memory use, and thermal observations
