"""Read-only detection of the Python runtime and host environment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path
import platform
import re
import sys


@dataclass(frozen=True)
class EnvironmentInfo:
    """A snapshot of runtime details useful for platform decisions."""

    is_android: bool
    is_termux: bool
    os_name: str
    architecture: str
    python_version: str
    android_api_level: int | None
    total_memory_bytes: int | None
    termux_prefix: str | None


def _normalise_architecture(machine: str) -> str:
    value = machine.strip().lower()
    if value in {"aarch64", "arm64"}:
        return "arm64"
    if value in {"x86_64", "amd64"}:
        return "x86_64"
    if value in {"i386", "i686", "x86"}:
        return "x86"
    return value or "unknown"


def _read_total_memory(meminfo_path: Path) -> int | None:
    """Return MemTotal from procfs, or None when procfs is unavailable."""
    try:
        with meminfo_path.open("r", encoding="ascii") as meminfo:
            for line in meminfo:
                match = re.match(r"^MemTotal:\s+(\d+)\s+kB\s*$", line)
                if match:
                    return int(match.group(1)) * 1024
    except (OSError, UnicodeError, ValueError):
        return None
    return None


def _read_android_api_level() -> int | None:
    getter = getattr(sys, "getandroidapilevel", None)
    if not callable(getter):
        return None
    try:
        level = getter()
        return int(level) if level is not None else None
    except (OSError, RuntimeError, TypeError, ValueError):
        return None


def detect_environment(
    *,
    environ: Mapping[str, str] | None = None,
    os_name: str | None = None,
    machine: str | None = None,
    python_version: str | None = None,
    android_api_level: int | None = None,
    meminfo_path: Path = Path("/proc/meminfo"),
) -> EnvironmentInfo:
    """Detect Android/Termux and basic hardware details without side effects.

    The function reads environment variables and, when available, procfs.
    It does not execute shell commands, install packages, or access the network.
    Optional arguments make the detection deterministic in tests.
    """
    env = os.environ if environ is None else environ
    prefix = env.get("PREFIX") or None
    termux_markers = (
        bool(env.get("TERMUX_VERSION")),
        bool(env.get("TERMUX_APP__DATA_DIR")),
        bool(prefix and "/com.termux/" in prefix),
    )
    is_termux = any(termux_markers)

    detected_os = platform.system() if os_name is None else os_name
    detected_machine = platform.machine() if machine is None else machine
    detected_python = sys.version.split()[0] if python_version is None else python_version

    if android_api_level is not None:
        api_level = int(android_api_level)
    elif os_name is None:
        api_level = _read_android_api_level()
    else:
        # An explicitly supplied OS makes this a simulated/test environment;
        # do not leak the host interpreter's Android API into that result.
        api_level = None

    is_android = bool(
        is_termux
        or api_level is not None
        or detected_os.strip().lower() == "android"
    )

    return EnvironmentInfo(
        is_android=is_android,
        is_termux=is_termux,
        os_name=detected_os,
        architecture=_normalise_architecture(detected_machine),
        python_version=detected_python,
        android_api_level=api_level,
        total_memory_bytes=_read_total_memory(Path(meminfo_path)),
        termux_prefix=prefix,
    )
