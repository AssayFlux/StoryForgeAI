# Phase 3 model candidate — Qwen2.5 1.5B Q4_K_M

**Decision:** selected for the first target-device inference benchmark only. This is
not yet the default model and has not been downloaded or run on the device.

## Publisher and provenance

| Field | Pinned value |
|---|---|
| Publisher | Qwen (official publisher account) |
| Source repository | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF |
| Immutable repository revision | `91cad51170dc346986eccefdc2dd33a9da36ead9` |
| Exact file | `qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| File size | 1,117,320,736 bytes (about 1.12 GB decimal) |
| Quantization | Q4_K_M |
| Base/instruct model | Qwen2.5-1.5B-Instruct (1.54B parameters) |
| License shown by publisher | Apache-2.0 |
| Expected SHA-256 | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |
| Pinned file URL | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/91cad51170dc346986eccefdc2dd33a9da36ead9/qwen2.5-1.5b-instruct-q4_k_m.gguf |

The revision is immutable and includes the selected file. The SHA-256 and exact
byte size are taken from the publisher's Hugging Face Xet/LFS pointer metadata.
Verify the downloaded bytes independently before registering or loading them.
The model's Apache-2.0 license does not remove the need to retain its license
and attribution notices when redistributing it.

## Why this candidate

- Small enough to be a cautious first local-inference test (approximately 1.12 GB
  on disk), while using a 4-bit medium K-quantization rather than the most
  aggressive low-bit option.
- Official publisher repository, clear model card, GGUF packaging and
  llama.cpp usage documented by the publisher.
- The user's latest preflight snapshot reported 6.85 GB available RAM and
  195 GB free on the filesystem backing Termux paths. Those numbers are not a
  safe-memory guarantee and must be refreshed immediately before use.
- The target device's llama.cpp build is known to start, but compatibility with
  this actual model and real inference remain unverified.

## Download and placement policy

- **Approval required:** do not download until the user explicitly approves
  this exact candidate and its approximately 1.12 GB transfer.
- Keep weights outside the repository and upstream llama.cpp checkout, e.g.
  `$HOME/models/qwen2.5-1.5b-instruct-q4_k_m.gguf`.
- Do not commit model weights, Git LFS pointers, access tokens, or downloaded
  binary artifacts to StoryForgeAI.
- After approval, download from the pinned URL (not the moving `main` URL),
  calculate SHA-256 locally, and require an exact match before registry
  registration. If the hash differs, quarantine/delete the incomplete file and
  stop; do not load it.

## Initial benchmark envelope

- Context: 2,048 tokens.
- Maximum generated tokens: 64 for first smoke test.
- CPU threads: start conservatively (2); change only as a recorded experiment.
- Network: airplane mode with Wi-Fi/mobile data disabled for the actual
  inference test.
- Measure cold start/model load, prompt processing tokens/s, generation
  tokens/s, peak process RSS, wall time, battery percentage and temperature
  before/after when accessible.
- Record exact llama.cpp version/commit and command settings. A successful CLI
  startup alone is not a model-load or inference pass.

## Acceptance checklist

- [ ] User explicitly approves this exact model download.
- [ ] Pre-download free-space and MemAvailable checks refreshed.
- [ ] Downloaded file size equals 1,117,320,736 bytes.
- [ ] SHA-256 equals the pinned publisher value above.
- [ ] Model registers in SQLite with Apache-2.0 and official Qwen provenance.
- [ ] Model loads successfully with the user's Termux llama.cpp build.
- [ ] A real response is generated with network disabled and no remote fallback.
- [ ] Startup, prompt and generation throughput, peak RSS, battery/thermal
      observations and settings are recorded.
- [ ] Missing/corrupt/incompatible model and low-memory failure paths are safe.

Until all relevant checks pass, status remains **candidate selected; inference
not verified**.

## Publisher references

- Model repository and license: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
- Pinned repository revision: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/tree/91cad51170dc346986eccefdc2dd33a9da36ead9
- Exact file metadata and SHA-256: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/blob/91cad51170dc346986eccefdc2dd33a9da36ead9/qwen2.5-1.5b-instruct-q4_k_m.gguf
