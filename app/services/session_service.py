from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models.card import Card
from app.models.deck import Deck, DeckMode
from app.models.draw import DrawResult
from app.services.asset_loader import CardRepository


class SessionError(Exception):
    """Raised when a session save/load action fails."""


@dataclass(slots=True)
class SessionSnapshot:
    mode: DeckMode
    remaining_card_ids: list[str]
    drawn_card_ids: list[str]
    drawn_reversed_flags: list[bool]
    current_card_id: str | None
    current_is_reversed: bool


class SessionService:
    def __init__(
        self,
        repository: CardRepository,
        default_mode: DeckMode = DeckMode.MAJORS,
        *,
        allow_reversed_majors: bool = True,
    ) -> None:
        self._repository = repository
        self._mode = default_mode
        self._deck = Deck(self._repository.cards_for_mode(self._mode))
        self._allow_reversed_majors = allow_reversed_majors
        self._history: list[DrawResult] = []
        self._current_draw: DrawResult | None = None
        self._rng = random.Random()

    @property
    def mode(self) -> DeckMode:
        return self._mode

    @property
    def current_card(self) -> Card | None:
        if self._current_draw is None:
            return None
        return self._current_draw.card

    @property
    def current_draw(self) -> DrawResult | None:
        return self._current_draw

    @property
    def history(self) -> tuple[Card, ...]:
        return tuple(draw.card for draw in self._history)

    @property
    def history_draws(self) -> tuple[DrawResult, ...]:
        return tuple(self._history)

    @property
    def allow_reversed_majors(self) -> bool:
        return self._allow_reversed_majors

    @property
    def total_count(self) -> int:
        return self._deck.total_count()

    @property
    def remaining_count(self) -> int:
        return self._deck.remaining_count()

    @property
    def drawn_count(self) -> int:
        return self._deck.drawn_count()

    @property
    def is_empty(self) -> bool:
        return self._deck.is_empty()

    def draw_card(self) -> DrawResult | None:
        card = self._deck.draw_next()
        if card is None:
            self._current_draw = None
            return None

        is_reversed = (
            self._allow_reversed_majors
            and card.arcana == "major"
            and self._rng.choice((True, False))
        )
        draw = DrawResult(card=card, is_reversed=is_reversed)
        self._current_draw = draw
        self._history.append(draw)
        return draw

    def reshuffle(self) -> None:
        self._deck.reset()
        self._history = []
        self._current_draw = None

    def change_mode(self, mode: DeckMode) -> None:
        self._mode = mode
        self._deck = Deck(self._repository.cards_for_mode(mode))
        self._history = []
        self._current_draw = None

    def set_allow_reversed_majors(self, enabled: bool) -> None:
        self._allow_reversed_majors = enabled

    def export_snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
            mode=self._mode,
            remaining_card_ids=[card.id for card in self._deck.remaining_cards],
            drawn_card_ids=[draw.card.id for draw in self._history],
            drawn_reversed_flags=[draw.is_reversed for draw in self._history],
            current_card_id=self._current_draw.card.id if self._current_draw else None,
            current_is_reversed=self._current_draw.is_reversed if self._current_draw else False,
        )

    def save_session(self, session_path: Path) -> None:
        snapshot = self.export_snapshot()
        payload = {
            "mode": snapshot.mode.value,
            "remaining_card_ids": snapshot.remaining_card_ids,
            "drawn_card_ids": snapshot.drawn_card_ids,
            "drawn_reversed_flags": snapshot.drawn_reversed_flags,
            "current_card_id": snapshot.current_card_id,
            "current_is_reversed": snapshot.current_is_reversed,
        }
        try:
            session_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            raise SessionError(f"Impossible d'enregistrer la session: {session_path}") from exc

    def load_session(self, session_path: Path) -> None:
        if not session_path.exists():
            raise SessionError(f"Session introuvable: {session_path}")

        try:
            raw_data: dict[str, Any] = json.loads(session_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SessionError(f"Session invalide (JSON): {session_path}") from exc
        except OSError as exc:
            raise SessionError(f"Impossible de lire la session: {session_path}") from exc

        try:
            mode = DeckMode.from_value(str(raw_data["mode"]))
            remaining_ids = list(raw_data["remaining_card_ids"])
            drawn_ids = list(raw_data["drawn_card_ids"])
            drawn_reversed_flags_raw = raw_data.get("drawn_reversed_flags")
            current_card_id = raw_data.get("current_card_id")
            current_is_reversed = bool(raw_data.get("current_is_reversed", False))
        except (KeyError, TypeError, ValueError) as exc:
            raise SessionError("Session invalide: champs requis absents ou incorrects.") from exc

        if drawn_reversed_flags_raw is None:
            drawn_reversed_flags = [False for _ in drawn_ids]
        else:
            drawn_reversed_flags = [bool(flag) for flag in drawn_reversed_flags_raw]
        if len(drawn_reversed_flags) != len(drawn_ids):
            raise SessionError("Session invalide: drawn_reversed_flags incohérent.")

        deck_cards = self._repository.cards_for_mode(mode)
        deck = Deck(deck_cards, auto_shuffle=False)
        try:
            deck.set_state(remaining_ids=remaining_ids, drawn_ids=drawn_ids)
        except ValueError as exc:
            raise SessionError(f"Session invalide: {exc}") from exc

        self._mode = mode
        self._deck = deck
        self._history = []
        for card_id, is_reversed in zip(drawn_ids, drawn_reversed_flags, strict=True):
            self._history.append(DrawResult(card=self._repository.by_id(card_id), is_reversed=is_reversed))

        if current_card_id is None:
            self._current_draw = None
            return
        if current_card_id not in remaining_ids and current_card_id not in drawn_ids:
            raise SessionError("Session invalide: current_card_id absent de l'état du paquet.")
        self._current_draw = DrawResult(
            card=self._repository.by_id(current_card_id),
            is_reversed=current_is_reversed,
        )
