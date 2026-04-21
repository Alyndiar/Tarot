from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.models.deck import DeckMode
from app.services.asset_loader import AssetError, load_card_repository
from app.services.session_service import SessionService
from app.ui.main_window import MainWindow, WindowPreferences
from app.utils import paths


@dataclass(slots=True)
class AppConfig:
    default_mode: DeckMode = DeckMode.MAJORS
    confirm_mode_change: bool = True
    allow_reversed_majors: bool = True
    window_width: int = 1200
    window_height: int = 760


def _load_config(config_file: Path) -> AppConfig:
    if not config_file.exists():
        return AppConfig()

    try:
        raw = json.loads(config_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AppConfig()

    default_mode_value = str(raw.get("default_mode", DeckMode.MAJORS.value))
    try:
        default_mode = DeckMode.from_value(default_mode_value)
    except ValueError:
        default_mode = DeckMode.MAJORS

    window_cfg = raw.get("window", {})
    if not isinstance(window_cfg, dict):
        window_cfg = {}

    def _safe_int(value: object, fallback: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    return AppConfig(
        default_mode=default_mode,
        confirm_mode_change=bool(raw.get("confirm_mode_change", True)),
        allow_reversed_majors=bool(raw.get("allow_reversed_majors", True)),
        window_width=_safe_int(window_cfg.get("width", 1200), 1200),
        window_height=_safe_int(window_cfg.get("height", 760), 760),
    )


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("TarotDealerMarseille")

    config = _load_config(paths.config_path())

    try:
        repository = load_card_repository(paths.assets_dir(), paths.manifest_path())
    except AssetError as exc:
        QMessageBox.critical(
            None,
            "Erreur de chargement des assets",
            (
                "Impossible de démarrer l'application.\n\n"
                f"{exc}\n\n"
                "Vérifiez le manifeste et le dossier assets."
            ),
        )
        return 1

    session = SessionService(
        repository,
        default_mode=config.default_mode,
        allow_reversed_majors=config.allow_reversed_majors,
    )
    window = MainWindow(
        session,
        prefs=WindowPreferences(
            width=config.window_width,
            height=config.window_height,
            confirm_mode_change=config.confirm_mode_change,
        ),
    )
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
