"""SQLite persistence for StoryForge projects and generation jobs."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = 2


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    """Small standard-library SQLite data layer with versioned migrations."""

    def __init__(self, path: str | Path, *, timeout_seconds: float = 5.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self.path = Path(path).expanduser()
        self.timeout_seconds = timeout_seconds

    def _open(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout_seconds)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {int(self.timeout_seconds * 1000)}")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a transaction-scoped connection and always close it."""
        connection = self._open()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create the database and apply all migrations up to this version."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = self._open()
        try:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
        finally:
            connection.close()

        with self.connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT MAX(version) AS version FROM schema_migrations"
            ).fetchone()
            current_version = row["version"] or 0
            if current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema {current_version} is newer than supported "
                    f"version {SCHEMA_VERSION}"
                )
            if current_version < 1:
                self._migration_1(connection)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (1, _utc_now()),
                )
                current_version = 1
            if current_version < 2:
                self._migration_2(connection)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (2, _utc_now()),
                )

    @staticmethod
    def _migration_1(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'archived')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE generation_jobs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                job_type TEXT NOT NULL CHECK(length(trim(job_type)) > 0),
                status TEXT NOT NULL DEFAULT 'queued'
                    CHECK(status IN ('queued', 'running', 'paused', 'completed', 'failed', 'cancelled')),
                payload_json TEXT NOT NULL DEFAULT '{}',
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            "CREATE INDEX idx_generation_jobs_project_created "
            "ON generation_jobs(project_id, created_at)"
        )
        connection.execute(
            "CREATE INDEX idx_generation_jobs_status_created "
            "ON generation_jobs(status, created_at)"
        )

    @staticmethod
    def _migration_2(connection: sqlite3.Connection) -> None:
        """Add local model registry metadata; model weights remain ordinary files."""
        connection.execute(
            """
            CREATE TABLE models (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                format TEXT NOT NULL CHECK(format = 'gguf'),
                integrity_status TEXT NOT NULL DEFAULT 'valid'
                    CHECK(integrity_status IN ('valid', 'missing', 'modified', 'invalid')),
                integrity_checked_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE model_files (
                id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL UNIQUE,
                path TEXT NOT NULL UNIQUE,
                size_bytes INTEGER NOT NULL CHECK(size_bytes > 0),
                sha256 TEXT NOT NULL CHECK(length(sha256) = 64),
                registered_at TEXT NOT NULL,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE model_licenses (
                model_id TEXT PRIMARY KEY,
                license_id TEXT NOT NULL CHECK(length(trim(license_id)) > 0),
                license_name TEXT NOT NULL CHECK(length(trim(license_name)) > 0),
                source_uri TEXT,
                source_name TEXT,
                attribution TEXT,
                FOREIGN KEY(model_id) REFERENCES models(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute("CREATE INDEX idx_models_name ON models(name)")

    def integrity_check(self) -> list[str]:
        """Return SQLite integrity messages; ['ok'] indicates a healthy DB."""
        with self.connection() as connection:
            return [
                row[0] for row in connection.execute("PRAGMA integrity_check").fetchall()
            ]

    def create_project(self, name: str) -> dict[str, Any]:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Project name must not be empty")
        now = _utc_now()
        project_id = str(uuid4())
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO projects(id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (project_id, cleaned_name, now, now),
            )
        return self.get_project(project_id)  # type: ignore[return-value]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def list_projects(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM projects ORDER BY created_at DESC, id"
            ).fetchall()
        return [dict(row) for row in rows]

    def create_generation_job(
        self,
        project_id: str,
        job_type: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        cleaned_type = job_type.strip()
        if not cleaned_type:
            raise ValueError("Job type must not be empty")
        payload_json = json.dumps(
            dict(payload or {}),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        now = _utc_now()
        job_id = str(uuid4())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO generation_jobs(
                    id, project_id, job_type, payload_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job_id, project_id, cleaned_type, payload_json, now, now),
            )
        return self.get_generation_job(job_id)  # type: ignore[return-value]

    def get_generation_job(self, job_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM generation_jobs WHERE id = ?", (job_id,)
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result
