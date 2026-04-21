from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from app.models.draw import DrawResult


class HistoryPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._list_widget = QListWidget()
        self._list_widget.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list_widget)

    def set_history(self, draws: tuple[DrawResult, ...]) -> None:
        self._list_widget.clear()
        if not draws:
            self._list_widget.addItem("Aucun tirage pour cette session.")
            return

        entries: list[str] = []
        for draw_index, draw in enumerate(draws, start=1):
            entries.append(f"#{draw_index} - {draw.display_name}")

        for text in reversed(entries):
            self._list_widget.addItem(QListWidgetItem(text))
