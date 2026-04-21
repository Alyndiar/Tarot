from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.deck import DeckMode
from app.services.session_service import SessionService
from app.ui.widgets.card_view import CardView
from app.ui.widgets.history_panel import HistoryPanel


@dataclass(slots=True)
class WindowPreferences:
    width: int = 1200
    height: int = 760
    confirm_mode_change: bool = True


class MainWindow(QMainWindow):
    def __init__(self, session: SessionService, prefs: WindowPreferences | None = None) -> None:
        super().__init__()
        self._session = session
        self._prefs = prefs or WindowPreferences()

        self.setWindowTitle("TarotDealerMarseille")
        self.resize(self._prefs.width, self._prefs.height)
        self.setMinimumSize(980, 640)

        self._mode_combo = QComboBox()
        self._mode_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        for mode in DeckMode:
            self._mode_combo.addItem(mode.label_fr, userData=mode.value)

        self._draw_button = QPushButton("Tirer une carte")
        self._draw_button.setMinimumHeight(42)
        self._draw_button.setStyleSheet("font-size: 15px; font-weight: 600;")

        self._reshuffle_button = QPushButton("Remélanger")
        self._copy_name_button = QPushButton("Copier le nom")
        self._reverse_majors_checkbox = QCheckBox("Majeurs tête en bas")
        self._reverse_majors_checkbox.setChecked(self._session.allow_reversed_majors)

        self._mode_value = QLabel("")
        self._remaining_value = QLabel("")
        self._drawn_value = QLabel("")
        self._status_value = QLabel("")
        self._status_value.setWordWrap(True)
        self._status_value.setStyleSheet("color: #3b3b3b;")

        self._history_panel = HistoryPanel()
        self._card_view = CardView()
        self._card_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._build_ui()
        self._connect_signals()
        self._set_mode_combo(self._session.mode)
        self._refresh_view()

    def _build_ui(self) -> None:
        side_panel = QFrame()
        side_panel.setFrameShape(QFrame.Shape.StyledPanel)
        side_panel.setMinimumWidth(340)
        side_panel.setMaximumWidth(430)

        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(12, 12, 12, 12)
        side_layout.setSpacing(12)

        controls_grid = QGridLayout()
        controls_grid.setHorizontalSpacing(8)
        controls_grid.setVerticalSpacing(8)
        controls_grid.addWidget(QLabel("Mode"), 0, 0)
        controls_grid.addWidget(self._mode_combo, 0, 1)
        controls_grid.addWidget(QLabel("Mode courant"), 1, 0)
        controls_grid.addWidget(self._mode_value, 1, 1)
        controls_grid.addWidget(QLabel("Restantes"), 2, 0)
        controls_grid.addWidget(self._remaining_value, 2, 1)
        controls_grid.addWidget(QLabel("Tirées"), 3, 0)
        controls_grid.addWidget(self._drawn_value, 3, 1)
        controls_grid.addWidget(self._reverse_majors_checkbox, 4, 0, 1, 2)
        side_layout.addLayout(controls_grid)

        button_row = QHBoxLayout()
        button_row.addWidget(self._reshuffle_button)
        button_row.addWidget(self._copy_name_button)
        side_layout.addLayout(button_row)

        side_layout.addWidget(self._draw_button)
        side_layout.addWidget(self._status_value)

        side_layout.addWidget(QLabel("Historique de session"))
        side_layout.addWidget(self._history_panel, 1)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)
        main_layout.addWidget(side_panel)
        main_layout.addWidget(self._card_view, 1)

        root = QWidget()
        root.setLayout(main_layout)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self._draw_button.clicked.connect(self._on_draw_clicked)
        self._reshuffle_button.clicked.connect(self._on_reshuffle_clicked)
        self._copy_name_button.clicked.connect(self._on_copy_name_clicked)
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._reverse_majors_checkbox.toggled.connect(self._on_reverse_majors_toggled)

    def _set_mode_combo(self, mode: DeckMode) -> None:
        self._mode_combo.blockSignals(True)
        for index in range(self._mode_combo.count()):
            if self._mode_combo.itemData(index) == mode.value:
                self._mode_combo.setCurrentIndex(index)
                break
        self._mode_combo.blockSignals(False)

    def _on_mode_changed(self, index: int) -> None:
        raw_mode = self._mode_combo.itemData(index)
        if raw_mode is None:
            return
        try:
            mode = DeckMode.from_value(str(raw_mode))
        except ValueError:
            return
        if mode == self._session.mode:
            return

        if self._prefs.confirm_mode_change and self._session.drawn_count > 0:
            answer = QMessageBox.question(
                self,
                "Changer de mode",
                "Changer de mode démarre une nouvelle session et efface l'historique actuel.\nContinuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self._set_mode_combo(self._session.mode)
                return

        self._session.change_mode(mode)
        self._refresh_view()

    def _on_draw_clicked(self) -> None:
        draw = self._session.draw_card()
        if draw is None:
            self._status_value.setText("Le paquet est épuisé. Remélangez pour recommencer.")
        self._refresh_view()

    def _on_reshuffle_clicked(self) -> None:
        self._session.reshuffle()
        self._refresh_view()

    def _on_reverse_majors_toggled(self, checked: bool) -> None:
        self._session.set_allow_reversed_majors(checked)
        if checked:
            self._status_value.setText("Les majeurs peuvent maintenant sortir tête en bas.")
        else:
            self._status_value.setText("Les majeurs sortiront uniquement en orientation normale.")

    def _on_copy_name_clicked(self) -> None:
        draw = self._session.current_draw
        if draw is None:
            self._status_value.setText("Aucune carte à copier.")
            return
        card_label = draw.display_name
        clipboard = QApplication.clipboard()
        clipboard.setText(card_label)
        self._status_value.setText(f"Nom copié: {card_label}")

    def _refresh_view(self) -> None:
        current_draw = self._session.current_draw
        if current_draw is None:
            self._card_view.set_card(None)
        else:
            self._card_view.set_card(current_draw.card, is_reversed=current_draw.is_reversed)
        self._history_panel.set_history(self._session.history_draws)
        self._mode_value.setText(self._session.mode.label_fr)
        self._remaining_value.setText(f"{self._session.remaining_count} / {self._session.total_count}")
        self._drawn_value.setText(str(self._session.drawn_count))
        reverse_available = self._session.mode != DeckMode.MINORS
        self._reverse_majors_checkbox.setEnabled(reverse_available)
        if reverse_available:
            self._reverse_majors_checkbox.setToolTip("Autorise l'orientation tête en bas pour les arcanes majeurs.")
        else:
            self._reverse_majors_checkbox.setToolTip(
                "Aucun arcane majeur dans ce mode: option sans effet."
            )
        self._draw_button.setEnabled(not self._session.is_empty)
        if self._session.is_empty:
            self._status_value.setText("Le paquet est épuisé. Remélangez pour recommencer.")
        elif current_draw is None:
            self._status_value.setText("Session prête. Cliquez sur « Tirer une carte ».")
        elif current_draw.is_reversed:
            self._status_value.setText("Tirage effectué (carte majeure tête en bas).")
        else:
            self._status_value.setText("Tirage effectué.")
