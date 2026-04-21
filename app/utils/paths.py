from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def runtime_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return project_root()


def assets_dir() -> Path:
    return runtime_root() / "assets"


def manifest_path() -> Path:
    return assets_dir() / "cards_manifest.json"


def config_path() -> Path:
    return runtime_root() / "config" / "app_config.json"

