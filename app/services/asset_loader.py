from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.models.card import ArcanaType, Card, SuitType
from app.models.deck import DeckMode

_ALLOWED_ARCANA: set[ArcanaType] = {"major", "minor"}
_ALLOWED_SUITS: set[SuitType] = {"batons", "coupes", "deniers", "epees"}
_REQUIRED_MANIFEST_KEYS = {"id", "name", "arcana", "suit", "rank", "image", "display_order"}


class AssetError(Exception):
    """Base exception for asset loading errors."""


class ManifestValidationError(AssetError):
    """Raised when the cards manifest has invalid content."""


@dataclass(slots=True)
class CardRepository:
    cards: tuple[Card, ...]
    _cards_by_id: dict[str, Card] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._cards_by_id = {card.id: card for card in self.cards}

    @property
    def cards_by_id(self) -> dict[str, Card]:
        return dict(self._cards_by_id)

    def by_id(self, card_id: str) -> Card:
        try:
            return self._cards_by_id[card_id]
        except KeyError as exc:
            raise KeyError(f"Carte inconnue: {card_id}") from exc

    def majors(self) -> tuple[Card, ...]:
        return tuple(card for card in self.cards if card.arcana == "major")

    def minors(self) -> tuple[Card, ...]:
        return tuple(card for card in self.cards if card.arcana == "minor")

    def cards_for_mode(self, mode: DeckMode) -> tuple[Card, ...]:
        if mode == DeckMode.MAJORS:
            cards = self.majors()
        elif mode == DeckMode.MINORS:
            cards = self.minors()
        elif mode == DeckMode.FULL:
            cards = self.cards
        else:
            raise ValueError(f"Mode inconnu: {mode}")

        if not cards:
            raise ManifestValidationError(f"Aucune carte disponible pour le mode {mode.value}.")
        return cards


def _read_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise AssetError(f"Manifeste introuvable: {manifest_path}")

    try:
        raw_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestValidationError(f"JSON invalide dans {manifest_path}: {exc}") from exc

    if not isinstance(raw_data, list):
        raise ManifestValidationError("Le manifeste doit être un tableau JSON.")
    return raw_data


def _parse_card(entry: dict[str, Any], assets_root: Path, index: int) -> Card:
    missing_keys = _REQUIRED_MANIFEST_KEYS - set(entry)
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ManifestValidationError(f"Entrée #{index}: clés manquantes: {missing}")

    card_id = str(entry["id"]).strip()
    name = str(entry["name"]).strip()
    arcana = str(entry["arcana"]).strip()
    suit = entry["suit"]
    rank = entry["rank"]
    display_order = entry["display_order"]

    if not card_id:
        raise ManifestValidationError(f"Entrée #{index}: id vide.")
    if not name:
        raise ManifestValidationError(f"Entrée #{index}: nom vide.")
    if arcana not in _ALLOWED_ARCANA:
        raise ManifestValidationError(f"Entrée #{index} ({card_id}): arcana invalide '{arcana}'.")
    if not isinstance(display_order, int):
        raise ManifestValidationError(f"Entrée #{index} ({card_id}): display_order doit être un entier.")

    if arcana == "major":
        if suit is not None:
            raise ManifestValidationError(f"Entrée #{index} ({card_id}): suit doit être null pour un majeur.")
    else:
        if suit not in _ALLOWED_SUITS:
            raise ManifestValidationError(f"Entrée #{index} ({card_id}): suit invalide '{suit}'.")

    image_rel_path = Path(str(entry["image"]))
    if image_rel_path.is_absolute():
        raise ManifestValidationError(f"Entrée #{index} ({card_id}): le chemin image doit être relatif.")
    image_path = assets_root / image_rel_path
    if not image_path.exists():
        raise AssetError(f"Image manquante pour '{card_id}': {image_path}")

    return Card(
        id=card_id,
        name=name,
        arcana=arcana,
        suit=suit,
        rank=str(rank) if rank is not None else None,
        image_path=image_path,
        display_order=display_order,
    )


def load_card_repository(assets_root: Path, manifest_path: Path) -> CardRepository:
    if not assets_root.exists():
        raise AssetError(f"Dossier assets introuvable: {assets_root}")

    manifest_entries = _read_manifest(manifest_path)
    cards: list[Card] = []
    ids_seen: set[str] = set()

    for idx, raw_entry in enumerate(manifest_entries, start=1):
        if not isinstance(raw_entry, dict):
            raise ManifestValidationError(f"Entrée #{idx}: type invalide (objet JSON attendu).")
        card = _parse_card(raw_entry, assets_root, idx)
        if card.id in ids_seen:
            raise ManifestValidationError(f"ID dupliqué dans le manifeste: {card.id}")
        ids_seen.add(card.id)
        cards.append(card)

    cards.sort(key=lambda item: item.display_order)
    return CardRepository(cards=tuple(cards))
