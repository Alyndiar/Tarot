from __future__ import annotations

import random
from enum import Enum
from typing import Iterable, Sequence

from .card import Card


class DeckMode(str, Enum):
    MAJORS = "majors"
    MINORS = "minors"
    FULL = "full"

    @property
    def label_fr(self) -> str:
        labels = {
            DeckMode.MAJORS: "Majeurs seulement",
            DeckMode.MINORS: "Mineurs seulement",
            DeckMode.FULL: "Jeu complet",
        }
        return labels[self]

    @classmethod
    def from_value(cls, value: str) -> "DeckMode":
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Mode inconnu: {value}") from exc


class Deck:
    def __init__(
        self,
        cards: Sequence[Card],
        *,
        rng: random.Random | None = None,
        auto_shuffle: bool = True,
    ) -> None:
        if not cards:
            raise ValueError("Un paquet ne peut pas être vide.")
        self._all_cards = list(cards)
        self._cards_by_id = {card.id: card for card in self._all_cards}
        self._rng = rng or random.Random()
        self._remaining_cards: list[Card] = []
        self._drawn_cards: list[Card] = []
        if auto_shuffle:
            self.reset()

    @property
    def all_cards(self) -> tuple[Card, ...]:
        return tuple(self._all_cards)

    @property
    def remaining_cards(self) -> tuple[Card, ...]:
        return tuple(self._remaining_cards)

    @property
    def drawn_cards(self) -> tuple[Card, ...]:
        return tuple(self._drawn_cards)

    def shuffle(self) -> None:
        self._rng.shuffle(self._remaining_cards)

    def draw_next(self) -> Card | None:
        if self.is_empty():
            return None
        card = self._remaining_cards.pop()
        self._drawn_cards.append(card)
        return card

    def reset(self) -> None:
        self._remaining_cards = list(self._all_cards)
        self._drawn_cards = []
        self.shuffle()

    def set_state(self, *, remaining_ids: Iterable[str], drawn_ids: Iterable[str]) -> None:
        remaining_list = list(remaining_ids)
        drawn_list = list(drawn_ids)
        known_ids = set(self._cards_by_id)
        remaining_set = set(remaining_list)
        drawn_set = set(drawn_list)

        if remaining_set & drawn_set:
            raise ValueError("L'état de session est invalide: cartes dupliquées.")
        if (remaining_set | drawn_set) != known_ids:
            raise ValueError("L'état de session ne correspond pas au mode courant.")
        if len(remaining_list) + len(drawn_list) != len(self._all_cards):
            raise ValueError("L'état de session contient un nombre incorrect de cartes.")

        try:
            self._remaining_cards = [self._cards_by_id[card_id] for card_id in remaining_list]
            self._drawn_cards = [self._cards_by_id[card_id] for card_id in drawn_list]
        except KeyError as exc:
            raise ValueError(f"Carte inconnue dans l'état de session: {exc}") from exc

    def remaining_count(self) -> int:
        return len(self._remaining_cards)

    def drawn_count(self) -> int:
        return len(self._drawn_cards)

    def total_count(self) -> int:
        return len(self._all_cards)

    def is_empty(self) -> bool:
        return self.remaining_count() == 0

