"""Explicit, offline-only registration of local GGUF model files."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import stat
from typing import Any
from uuid import uuid4

from storyforge.storage.database import Database


_CHUNK_SIZE = 1024 * 1024
_GGUF_MAGIC = b"GGUF"
_SUPPORTED_GGUF_VERSIONS = {1, 2, 3}


class ModelRegistryError(ValueError):
    """Raised when a local model cannot be safely registered or inspected."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _validate_gguf_header(path: Path) -> None:
    try:
        with path.open("rb") as model_file:
            header = model_file.read(8)
    except OSError as exc:
        raise ModelRegistryError(f"Cannot read model file: {exc}") from exc
    if len(header) != 8 or header[:4] != _GGUF_MAGIC:
        raise ModelRegistryError("File does not have a valid GGUF header")
    version = int.from_bytes(header[4:8], byteorder="little", signed=False)
    if version not in _SUPPORTED_GGUF_VERSIONS:
        raise ModelRegistryError(f"Unsupported GGUF version: {version}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as model_file:
            for chunk in iter(lambda: model_file.read(_CHUNK_SIZE), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ModelRegistryError(f"Cannot hash model file: {exc}") from exc
    return digest.hexdigest()


class ModelRegistry:
    """Persist model metadata while leaving model weights at their source path.

    Registration never copies, moves, deletes, downloads, or loads model weights.
    The caller must explicitly select a model for inference in a separate step.
    """

    def __init__(self, database: Database) -> None:
        self.database = database

    def register_local_model(
        self,
        path: str | Path,
        *,
        name: str,
        license_id: str,
        license_name: str,
        source_uri: str | None = None,
        source_name: str | None = None,
        attribution: str | None = None,
        model_id: str | None = None,
    ) -> dict[str, Any]:
        """Register an existing GGUF file and capture its size and SHA-256."""
        cleaned_name = name.strip()
        cleaned_license_id = license_id.strip()
        cleaned_license_name = license_name.strip()
        if not cleaned_name:
            raise ModelRegistryError("Model name must not be empty")
        if not cleaned_license_id or not cleaned_license_name:
            raise ModelRegistryError("License ID and license name are required")
        model_path = Path(path).expanduser()
        try:
            resolved_path = model_path.resolve(strict=True)
            file_stat = resolved_path.stat()
        except (OSError, RuntimeError) as exc:
            raise ModelRegistryError(f"Model file does not exist: {model_path}") from exc
        if not stat.S_ISREG(file_stat.st_mode):
            raise ModelRegistryError("Model path must point to a regular file")
        if file_stat.st_size <= 0:
            raise ModelRegistryError("Model file must not be empty")
        _validate_gguf_header(resolved_path)
        checksum = _sha256_file(resolved_path)
        # Detect a file being replaced or resized while its checksum is read.
        try:
            after_stat = resolved_path.stat()
        except OSError as exc:
            raise ModelRegistryError("Model file disappeared during registration") from exc
        if after_stat.st_size != file_stat.st_size or after_stat.st_mtime_ns != file_stat.st_mtime_ns:
            raise ModelRegistryError("Model file changed while it was being registered")

        identifier = model_id or str(uuid4())
        if not identifier.strip():
            raise ModelRegistryError("Model ID must not be empty")
        now = _utc_now()
        self.database.initialize()
        try:
            with self.database.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO models(
                        id, name, format, integrity_status, created_at, updated_at
                    ) VALUES (?, ?, 'gguf', 'valid', ?, ?)
                    """,
                    (identifier, cleaned_name, now, now),
                )
                connection.execute(
                    """
                    INSERT INTO model_files(
                        id, model_id, path, size_bytes, sha256, registered_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (str(uuid4()), identifier, str(resolved_path), file_stat.st_size, checksum, now),
                )
                connection.execute(
                    """
                    INSERT INTO model_licenses(
                        model_id, license_id, license_name, source_uri, source_name, attribution
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        identifier, cleaned_license_id, cleaned_license_name,
                        source_uri.strip() if source_uri and source_uri.strip() else None,
                        source_name.strip() if source_name and source_name.strip() else None,
                        attribution.strip() if attribution and attribution.strip() else None,
                    ),
                )
        except Exception as exc:
            # Preserve the underlying database exception for callers that need
            # to distinguish duplicate IDs/paths from other persistence errors.
            raise ModelRegistryError(f"Could not register model: {exc}") from exc
        return self.get_model(identifier)  # type: ignore[return-value]

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        self.database.initialize()
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT m.id, m.name, m.format, m.integrity_status,
                       m.integrity_checked_at, m.created_at, m.updated_at,
                       f.path, f.size_bytes, f.sha256, f.registered_at,
                       l.license_id, l.license_name, l.source_uri, l.source_name,
                       l.attribution
                FROM models AS m
                JOIN model_files AS f ON f.model_id = m.id
                JOIN model_licenses AS l ON l.model_id = m.id
                WHERE m.id = ?
                """,
                (model_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def list_models(self) -> list[dict[str, Any]]:
        self.database.initialize()
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT m.id, m.name, m.format, m.integrity_status,
                       f.path, f.size_bytes, f.sha256, l.license_id, l.license_name
                FROM models AS m
                JOIN model_files AS f ON f.model_id = m.id
                JOIN model_licenses AS l ON l.model_id = m.id
                ORDER BY m.created_at, m.id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def check_integrity(self, model_id: str) -> dict[str, Any]:
        """Recheck presence, GGUF header, size and SHA-256 for a registered model."""
        model = self.get_model(model_id)
        if model is None:
            raise ModelRegistryError(f"Unknown model ID: {model_id}")
        path = Path(model["path"])
        status = "valid"
        try:
            file_stat = path.stat()
            if not stat.S_ISREG(file_stat.st_mode):
                status = "invalid"
            elif file_stat.st_size <= 0:
                status = "invalid"
            else:
                try:
                    _validate_gguf_header(path)
                except ModelRegistryError:
                    status = "invalid"
                else:
                    checksum = _sha256_file(path)
                    if file_stat.st_size != model["size_bytes"] or checksum != model["sha256"]:
                        status = "modified"
        except FileNotFoundError:
            status = "missing"
        except OSError:
            status = "invalid"

        checked_at = _utc_now()
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE models
                SET integrity_status = ?, integrity_checked_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, checked_at, checked_at, model_id),
            )
        return self.get_model(model_id)  # type: ignore[return-value]
