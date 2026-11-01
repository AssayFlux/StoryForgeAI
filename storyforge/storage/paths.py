"""Configurable, app-owned local data directories."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class DataPaths:
    """Resolved locations for StoryForge runtime data."""

    root: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "DataPaths":
        """Build paths from an explicit root without creating anything."""
        return cls(root=Path(root).expanduser().resolve())

    @classmethod
    def from_environment(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        home: str | Path | None = None,
        configured_root: str | Path | None = None,
    ) -> "DataPaths":
        """Resolve data root: environment override, config, XDG, then home."""
        env = os.environ if environ is None else environ
        override = env.get("STORYFORGE_HOME")
        if override:
            return cls.from_root(override)
        if configured_root is not None:
            return cls.from_root(configured_root)

        home_path = Path(home).expanduser() if home is not None else Path.home()
        xdg_data_home = env.get("XDG_DATA_HOME")
        base = (
            Path(xdg_data_home).expanduser()
            if xdg_data_home
            else home_path / ".local" / "share"
        )
        return cls.from_root(base / "storyforge-ai")

    @property
    def database(self) -> Path:
        return self.root / "storyforge.db"

    @property
    def projects(self) -> Path:
        return self.root / "projects"

    @property
    def models(self) -> Path:
        return self.root / "models"

    @property
    def assets(self) -> Path:
        return self.root / "assets"

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    @property
    def backups(self) -> Path:
        return self.root / "backups"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    def ensure(self) -> "DataPaths":
        """Create the app data directories; safe to call repeatedly."""
        for directory in (
            self.root,
            self.projects,
            self.models,
            self.assets,
            self.cache,
            self.backups,
            self.logs,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self
