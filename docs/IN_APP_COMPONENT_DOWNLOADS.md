# In-app downloads and component manager

**Product requirement:** When StoryForgeAI is delivered as an Android APK/AAB, users must be able to discover, download, verify, install, update and remove large optional AI models and supported resource packs from inside the app. Large weights and resource files must not be bundled into the base APK.

This is a required Phase 14 Android-app capability. It is a product specification, not a claim that the download manager or Android UI is implemented today.

## User experience

Add a **Downloads / Models & Components** area under the app's model/tools/settings options. Each catalog item should show:

- Human-readable name and purpose (for example: story LLM, offline TTS voice, image model, tokenizer, font pack, subtitle resource pack).
- Component type, supported app/runtime versions, Android ABI where relevant, and whether it is required for a selected feature or optional.
- Publisher, source/release page, license identifier/name, attribution and any usage restrictions.
- Exact download size, installed size estimate, required free-space estimate and version.
- Integrity/provenance information (expected SHA-256 and pinned immutable version/revision).
- Current state: not downloaded, queued, downloading, paused, verifying, ready/installed, update available, failed, incompatible or removed.
- A **Download** button when absent, **Pause/Resume** while downloading where supported, **Retry** after recoverable failure, **Update** when a newer approved version is available, and **Remove** when installed.
- Progress percentage and bytes transferred, speed and ETA when known; show clear storage/network/error messages.

The app must explain that downloading a model consumes data and storage. Ask for confirmation before a large transfer, show the exact size and destination, and let the user choose Wi-Fi-only behavior. Never silently download multi-hundred-megabyte or gigabyte components.

## Component catalog and database

SQLite remains the source of truth. Reuse the existing `models`, `model_files` and `model_licenses` tables for installed GGUF model identity, file path, size, checksum and license data. Add download/catalog migrations during the Android app / download-manager implementation; do not store large binary files as SQLite BLOBs.

Proposed normalized tables (final columns and constraints must be designed and tested when implemented):

### `component_catalog`

- `id` stable catalog identifier; `component_type` (llm, tts_voice, image_model, tokenizer, font_pack, resource_pack, runtime_asset).
- `name`, `description`, `publisher`, `version`, `platform_constraints_json`, `required_by_features_json`.
- `source_uri` and immutable `source_revision` / release identifier.
- `file_name`, `download_size_bytes`, `installed_size_bytes`, `sha256`, `format`.
- `license_id`, `license_name`, `attribution`, `license_uri`.
- `is_required`, `is_optional`, `is_enabled`, `created_at`, `updated_at`.

### `component_downloads`

- `id`, `catalog_component_id`, `version`, `status`, `source_uri`, `destination_path`, `temporary_path`.
- `bytes_downloaded`, `expected_size_bytes`, `expected_sha256`, `actual_sha256`.
- `etag` / last-modified validator where supplied, `supports_resume`, `retry_count`, `last_error_code`, `last_error_message`.
- `started_at`, `updated_at`, `completed_at`, `verified_at`.
- Use stable IDs and indexes for status, component and update ordering. Keep download history sufficient for recovery and diagnostics without retaining sensitive URL credentials.

### `installed_components`

- `id`, `catalog_component_id`, `version`, `install_path`, `installed_size_bytes`, `sha256`, `integrity_status`, `installed_at`, `last_verified_at`, `enabled`.
- For LLMs, link the installed component to the existing model registry record (for example with a nullable `model_id` foreign key) instead of duplicating model metadata.
- Enforce foreign keys, unique version/install identities where appropriate, transactional state transitions and schema migrations.

The catalog may be seeded from a reviewed, versioned manifest shipped with the app. The manifest contains metadata and URLs only—not model weights. The database stores the user's selected versions, download state, verification results and install locations. If the app is offline, the catalog and already-installed components remain visible and usable.

## Download and install safety

1. Before starting, validate platform/ABI/runtime compatibility, license metadata, available storage and the user's network policy. Reserve enough space for the temporary file plus final file and extraction overhead.
2. Download to an app-private temporary path. Never write partial files into the final install location.
3. Support HTTP range/resume only when the server's validators make resuming safe. If a validator is missing or changes, restart rather than concatenate potentially different versions.
4. Enforce expected maximum size; detect truncated, oversized, HTML/error-page and malformed downloads.
5. Verify exact byte size and SHA-256 against the pinned catalog metadata before installation. A mismatch must fail closed; never load or mark the component ready.
6. Atomically move/rename the verified file into its versioned install directory, then update SQLite in a transaction. Recover or clean orphan temporary files after process death.
7. Keep the previous working version until the replacement is fully verified and activated. Failed updates must not break a currently usable model.
8. Recheck integrity before first use and when a component is reported missing/modified. Show actionable errors and allow retry/removal.
9. Pause safely on cancellation, process death, low storage, network loss or Android background limits. Do not promise background completion unless the Android worker/service implementation and OS behavior are verified.
10. Never silently fall back to cloud inference. Downloading is a separate, user-triggered operation; inference and production remain local after installation.

## APK size and Android system components

- Base APK/AAB should contain the app, essential UI/business logic and the minimum compatible runtime needed to launch. Large GGUF weights, TTS voice data, image model weights, fonts and optional resource packs are downloaded on demand.
- Keep downloaded files in app-private storage by default; use scoped storage/document picker only for explicit user import/export. Do not require root or broad filesystem access.
- Treat native executable code and system libraries differently from data/model files. Prefer packaging compatible native libraries in the APK/AAB or using supported Play Feature Delivery for code modules. Do **not** implement a generic downloader that fetches executable code or arbitrary shared libraries and loads them dynamically; check current Android and distribution-store policies before any exception.
- Do not download or replace Android OS components, request root, or install privileged system packages. "System components" in the in-app catalog means supported app-owned runtimes/data/resources only. If a required dependency is an Android OS feature, detect its availability and provide a documented installation/update route through the platform's official settings/store.
- Runtime dependencies such as FFmpeg/native inference libraries need a separate packaging and licensing decision. Model/voice/resource payloads are data assets and are suitable candidates for opt-in in-app downloads when their licenses permit redistribution.

## Acceptance criteria for Phase 14

- The APK installs and opens without pre-downloading optional models.
- The catalog lists reviewed components with source, publisher, license, version, size, compatibility and checksum.
- Each eligible item has the correct download/update/remove action and clear current state.
- Large transfers require user confirmation; Wi-Fi-only preference is respected.
- Download progress, pause/resume (when supported), cancellation, retry and app-restart recovery are tested on Android.
- Low-storage, network-loss, corrupt file, checksum mismatch, incompatible ABI/version and revoked/changed source cases fail safely.
- Verified files are installed atomically and recorded in SQLite; model files are linked to the existing model registry.
- Removing an optional component updates the database and removes only the selected app-owned files after confirmation; never deletes user projects or unrelated files.
- A previously installed working version remains usable if an update fails.
- With networking disabled, installed components remain available and inference/production has no cloud fallback.
- APK size is measured and documented separately from optional download sizes.
- Android background behavior, lifecycle recovery, permissions and distribution-policy compliance are verified on the target OS.

## Implementation timing

This capability is specified now and must be carried forward. Do not interrupt the current Phase 3 real-inference acceptance work to build UI prematurely. During Phase 14, implement it as a dedicated component/download manager backed by SQLite, then connect its state to the Android model/tools options. Phase 3 should continue using the existing local model registry; when the downloader is implemented, a verified downloaded GGUF is handed to that registry after checksum verification.
