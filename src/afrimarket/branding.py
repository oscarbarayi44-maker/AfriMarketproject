"""Charte graphique AfriMarket — source unique de vérité pour les couleurs et
polices utilisées dans le dashboard Streamlit, le rapport PDF et le PowerPoint.

Palette calquée sur le logo (sac vert avec silhouette Afrique blanche,
texte "AfriMarket Online" en vert foncé). Si le fichier logo réel est déposé
dans assets/, LOGO_PATH le détecte automatiquement.
"""
from pathlib import Path

DARK_GREEN = "#14532D"    # titres, en-têtes, texte fort
BRAND_GREEN = "#2E8B57"   # accent principal (barres, boutons, liens)
LIGHT_GREEN = "#66BB6A"   # accent secondaire
PALE_GREEN = "#EAF5EC"    # fonds de bloc, alternance de lignes
WHITE = "#FFFFFF"
TEXT_DARK = "#1B241D"
GREY = "#5A6B5D"

CATEGORICAL_PALETTE = [BRAND_GREEN, DARK_GREEN, LIGHT_GREEN, "#8BC34A", "#4C7A5D", "#A5D6A7"]

FONT_FAMILY = "Calibri"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"


def find_logo() -> Path | None:
    if not ASSETS_DIR.exists():
        return None
    for ext in ("png", "jpg", "jpeg", "webp"):
        matches = sorted(ASSETS_DIR.glob(f"*.{ext}"))
        if matches:
            return matches[0]
    return None


LOGO_PATH = find_logo()
