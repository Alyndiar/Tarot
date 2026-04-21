from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.models.card import Card


class CardView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._original_pixmap: QPixmap | None = None
        self._is_reversed = False

        self._image_label = QLabel("Aucune carte tirée")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(320, 520)
        self._image_label.setStyleSheet(
            "background-color: #f5f5f5; border: 1px solid #d0d0d0; border-radius: 8px;"
        )

        self._name_label = QLabel("")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #202020;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self._image_label, 1)
        layout.addWidget(self._name_label)

    def set_card(self, card: Card | None, *, is_reversed: bool = False) -> None:
        if card is None:
            self._name_label.setText("")
            self._image_label.setText("Aucune carte tirée")
            self._image_label.setPixmap(QPixmap())
            self._original_pixmap = None
            self._is_reversed = False
            return

        self._name_label.setText(card.name)
        self._is_reversed = is_reversed
        self._load_pixmap(card.image_path)
        self._rescale_pixmap()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._rescale_pixmap()

    def _load_pixmap(self, image_path: Path) -> None:
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self._original_pixmap = None
            self._image_label.setPixmap(QPixmap())
            self._image_label.setText(f"Image non lisible:\n{image_path.name}")
            return
        self._original_pixmap = pixmap
        self._image_label.setText("")

    def _rescale_pixmap(self) -> None:
        if self._original_pixmap is None:
            return
        source = self._original_pixmap
        if self._is_reversed:
            source = source.transformed(QTransform().rotate(180), Qt.TransformationMode.SmoothTransformation)
        target_size = self._image_label.size()
        scaled = source.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
