from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ArcanaType = Literal["major", "minor"]
SuitType = Literal["batons", "coupes", "deniers", "epees"]


@dataclass(frozen=True, slots=True)
class Card:
    id: str
    name: str
    arcana: ArcanaType
    suit: SuitType | None
    rank: str | None
    image_path: Path
    display_order: int

