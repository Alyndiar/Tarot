# TarotDealerMarseille

Application desktop Windows locale (PySide6) pour tirer des cartes du Tarot de Marseille, une carte à la fois, sans interprétation ésotérique.

## Fonctionnalités

- Modes de paquet:
  - `Majeurs seulement` (22)
  - `Mineurs seulement` (56)
  - `Jeu complet` (78)
- Tirage strictement sans remplacement jusqu'à épuisement.
- Affichage de la carte tirée (image + nom).
- Compteurs de session:
  - mode courant
  - restantes / total
  - tirées
- Historique de session (plus récent en haut).
- Remélange / nouvelle session sur le mode courant.
- Tirage des arcanes majeurs en orientation normale ou tête en bas (option activable).
- Option `Copier le nom` de la carte courante.
- Fonctionnement totalement hors ligne (assets locaux).

## Prérequis

- Windows 11 (cible principale)
- Python 3.12+

## Installation

### Option conda (recommandée)

```powershell
conda create -n Tarot python=3.12 -y
conda activate Tarot
pip install -r requirements.txt
```

### Option venv (si conda indisponible)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement

```powershell
python run.py
```

## Structure du projet

```text
TarotDealerMarseille/
├─ app/
│  ├─ main.py
│  ├─ models/
│  │  ├─ card.py
│  │  └─ deck.py
│  ├─ services/
│  │  ├─ asset_loader.py
│  │  └─ session_service.py
│  ├─ ui/
│  │  ├─ main_window.py
│  │  └─ widgets/
│  │     ├─ card_view.py
│  │     └─ history_panel.py
│  └─ utils/
│     └─ paths.py
├─ assets/
│  ├─ cards/
│  │  └─ cbd_tarot_marseille/
│  │     ├─ majors/
│  │     └─ minors/
│  ├─ cards_manifest.json
│  ├─ backs/
│  └─ credits/
│     └─ SOURCES.md
├─ config/
│  └─ app_config.json
├─ run.py
├─ requirements.txt
└─ build_windows.ps1
```

## Assets et manifeste JSON

Le manifeste est dans [assets/cards_manifest.json](/W:/Dany/Tarot/assets/cards_manifest.json).

Chaque carte contient:

- `id`
- `name`
- `arcana` (`major` ou `minor`)
- `suit` (`null` pour majeurs; sinon `batons|coupes|deniers|epees`)
- `rank`
- `image` (chemin relatif au dossier `assets`)
- `display_order`

Exemple:

```json
{
  "id": "major_00",
  "name": "Le Mat",
  "arcana": "major",
  "suit": null,
  "rank": "0",
  "image": "cards/cbd_tarot_marseille/majors/a22.jpg",
  "display_order": 0
}
```
Structure actuelle du set CBD intégré:

- majeurs: `assets/cards/cbd_tarot_marseille/majors/a01.jpg` à `a22.jpg`
- mineurs: `assets/cards/cbd_tarot_marseille/minors/{batons|coupes|deniers|epees}/{b|c|d|e}01.jpg` à `14.jpg`

Vous pouvez remplacer le set plus tard en conservant cette structure ou en modifiant le manifeste.

Le code ne télécharge aucun asset et ne dépend d'aucune API web.

## Configuration

Le fichier [config/app_config.json](/W:/Dany/Tarot/config/app_config.json) permet de régler:

- `default_mode`: `majors`, `minors` ou `full`
- `confirm_mode_change`: confirmation lors du changement de mode
- `allow_reversed_majors`: autorise les majeurs tête en bas

## Build Windows (optionnel)

Script fourni: [build_windows.ps1](/W:/Dany/Tarot/build_windows.ps1)

```powershell
.\build_windows.ps1
```

Le script:

- utilise conda si disponible (sinon venv),
- installe `PyInstaller`,
- génère un exécutable Windows (`TarotDealerMarseille`) avec assets/config embarqués.

## Notes de licence

- Le code de l'application est indépendant des assets.
- Les images de cartes peuvent suivre une licence différente du code.
- Vérifiez et documentez systématiquement la source exacte des images utilisées.
