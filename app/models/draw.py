from __future__ import annotations

from dataclasses import dataclass

from .card import Card


@dataclass(frozen=True, slots=True)
class DrawResult:
    card: Card
    is_reversed: bool = False

    @property
    def display_name(self) -> str:
        if self.is_reversed:
            return f"{self.card.name} (inversée)"
        return self.card.name

