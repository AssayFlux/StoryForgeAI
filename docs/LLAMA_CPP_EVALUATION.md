# llama.cpp / GGUF build-path evaluation

**Reviewed:** 2026-11-01  
**Scope:** ARM64 Android/Termux, no root, CPU-first local inference  
**Outcome:** Native Termux build feasibility is now verified on the user's Android 15/API 35 ARM64 device. Keep Android NDK cross-compilation as a later packaging/integration route. The upstream llama.cpp checkout/build remains outside the StoryForgeAI repository; no model was downloaded or loaded.

## Upstream-supported options

### Option A — Build natively inside Termux

The current upstream llama.cpp Android guide documents building inside Termux without root. It instructs users to install Git, CMake and `libandroid-spawn`, then follow the normal CMake build instructions. The guide recommends keeping GGUF files in Termux's private home directory for performance and warns that an unnecessarily large context can cause memory pressure; it gives 4096 as an example starting context, not a universal safe setting.

**Advantages**
- Uses the actual device's ARM64 compiler/runtime environment.
- Avoids maintaining a separate Android NDK installation on the phone.
- Best first proof that the device can compile and execute the CPU backend.

**Risks / constraints**
- Compilation itself can consume substantial RAM, storage, battery and thermal headroom.
- Build flags and package availability must be checked against the installed Termux repository and current upstream CMake options before running commands.
- A successful CLI test is not yet proof of a stable Python integration or Android application packaging.
- Build and inference must be benchmarked on this specific device; total physical RAM is not an application memory budget.

### Option B — Cross-compile with the Android NDK

The upstream Android guide also documents CMake cross-compilation for `arm64-v8a`. Its portable configuration currently specifies Android API 28 and disables options that are not suitable for that build path, including native-host CPU tuning and OpenMP. The resulting binaries require correct shared-library deployment and runtime library-path handling.

**Advantages**
- Reproducible toolchain can be maintained on a separate development computer.
- Better fit for a future native Android application or controlled binary packaging.

**Risks / constraints**
- Requires a compatible NDK and host build environment.
- The documented API 28 baseline must be reconciled with the device's actual Android API level before choosing it. StoryForge's detector previously reported API 24, which conflicts with assuming API 28 support.
- Cross-compilation alone does not prove that the binaries run correctly under Termux's userspace.

## Decision

1. Use **Option A (native Termux build)** for the initial device feasibility test. This has now succeeded: on 2026-11-01 the user built upstream llama.cpp in Termux with Clang 21.1.8 and CMake 4.4.5. The configure step detected aarch64/ARM and OpenMP; the resulting `llama-cli` ran both `--version` and `--help`.
2. Do not force a global `-march` setting. Keep the baseline portable and use upstream runtime CPU feature detection unless a device-specific benchmark justifies a separate build.
3. Defer NDK cross-compilation until Android app integration or packaging requires it and the actual OS/API baseline is confirmed.
4. Do not download a model yet. First prove that a minimal llama.cpp build works and record compiler/build configuration, binary version, disk use, peak memory if measurable, and a short CPU inference benchmark.

## Sources

- Upstream llama.cpp Android build guidance: https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md
- Upstream llama.cpp build guidance: https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md

These upstream documents are moving targets; re-check them at implementation time. ## Device verification record (2026-11-01)

- Device OS/API: Android 15 / API 35 (direct `getprop` checks recorded separately).
- Architecture: `aarch64`.
- Toolchain: Clang 21.1.8, CMake 4.4.5, Git 2.56.0; `libandroid-spawn` 0.3 installed.
- Upstream checkout: shallow clone of `ggml-org/llama.cpp`; configure completed with Release build, ARM CPU backend, OpenMP and OpenSSL detection.
- CLI version: `0.8.0-dev`, build 1, ggml commit `a91eab6`; built with Clang 21.1.8 for Android aarch64.
- Smoke checks: `./build/bin/llama-cli --version` and `./build/bin/llama-cli --help` both exited successfully (user-provided output).
- Not tested: loading a GGUF file, generating tokens, offline inference, sustained performance, thermal behavior, or memory peak.

This is a verified native build and CLI startup, not yet proof of model inference or Android app packaging.
