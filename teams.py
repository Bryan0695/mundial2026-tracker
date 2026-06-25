"""
Fuente unica de equipos - Mundial 2026
======================================
Este modulo es la UNICA definicion del universo de selecciones del torneo.
Antes esta informacion estaba repetida en varios sitios (DISPLAY_ES en
tournament.py, FLAGS + ISO_CODES en calendar_data.py, y const ISO + FLAGS
en panel.html). Ahora todo nace aqui y el resto IMPORTA de este modulo.

Cada equipo tiene UNA estructura con:
  - name   : nombre en ingles (la CLAVE; debe coincidir con el motor Elo y el calendario)
  - es     : nombre bonito en espanol para mostrar
  - iso    : codigo para flag-icons (clase CSS "fi fi-XX")
  - emoji  : bandera como emoji unicode
  - group  : letra del grupo (A-L)

Los 48 equipos estan en ORDEN DE SIEMBRA por grupo (pot order). Ese orden
importa: lo usan all_group_matches() y los cruces de dieciseisavos.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Team:
    name: str   # ingles (clave)
    es: str     # espanol (display)
    iso: str    # flag-icons (fi fi-XX)
    emoji: str  # bandera emoji
    group: str  # grupo A-L


# Universo completo en orden de siembra por grupo (A..L, 4 equipos cada uno).
TEAMS: list[Team] = [
    # Grupo A
    Team("Mexico", "Mexico", "mx", "🇲🇽", "A"),
    Team("Korea Republic", "Corea Rep.", "kr", "🇰🇷", "A"),
    Team("Czechia", "R. Checa", "cz", "🇨🇿", "A"),
    Team("South Africa", "Sudafrica", "za", "🇿🇦", "A"),
    # Grupo B
    Team("Canada", "Canada", "ca", "🇨🇦", "B"),
    Team("Switzerland", "Suiza", "ch", "🇨🇭", "B"),
    Team("Bosnia and Herzegovina", "Bosnia", "ba", "🇧🇦", "B"),
    Team("Qatar", "Qatar", "qa", "🇶🇦", "B"),
    # Grupo C
    Team("Brazil", "Brasil", "br", "🇧🇷", "C"),
    Team("Morocco", "Marruecos", "ma", "🇲🇦", "C"),
    Team("Scotland", "Escocia", "gb-sct", "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "C"),
    Team("Haiti", "Haiti", "ht", "🇭🇹", "C"),
    # Grupo D
    Team("USA", "USA", "us", "🇺🇸", "D"),
    Team("Australia", "Australia", "au", "🇦🇺", "D"),
    Team("Paraguay", "Paraguay", "py", "🇵🇾", "D"),
    Team("Turkiye", "Turquia", "tr", "🇹🇷", "D"),
    # Grupo E
    Team("Germany", "Alemania", "de", "🇩🇪", "E"),
    Team("Ivory Coast", "C. Marfil", "ci", "🇨🇮", "E"),
    Team("Ecuador", "Ecuador", "ec", "🇪🇨", "E"),
    Team("Curacao", "Curazao", "cw", "🇨🇼", "E"),
    # Grupo F
    Team("Netherlands", "P. Bajos", "nl", "🇳🇱", "F"),
    Team("Japan", "Japon", "jp", "🇯🇵", "F"),
    Team("Sweden", "Suecia", "se", "🇸🇪", "F"),
    Team("Tunisia", "Tunez", "tn", "🇹🇳", "F"),
    # Grupo G
    Team("Egypt", "Egipto", "eg", "🇪🇬", "G"),
    Team("Iran", "Iran", "ir", "🇮🇷", "G"),
    Team("Belgium", "Belgica", "be", "🇧🇪", "G"),
    Team("New Zealand", "N. Zelanda", "nz", "🇳🇿", "G"),
    # Grupo H
    Team("Spain", "Espana", "es", "🇪🇸", "H"),
    Team("Uruguay", "Uruguay", "uy", "🇺🇾", "H"),
    Team("Cape Verde", "Cabo Verde", "cv", "🇨🇻", "H"),
    Team("Saudi Arabia", "A. Saudita", "sa", "🇸🇦", "H"),
    # Grupo I
    Team("France", "Francia", "fr", "🇫🇷", "I"),
    Team("Norway", "Noruega", "no", "🇳🇴", "I"),
    Team("Senegal", "Senegal", "sn", "🇸🇳", "I"),
    Team("Iraq", "Iraq", "iq", "🇮🇶", "I"),
    # Grupo J
    Team("Argentina", "Argentina", "ar", "🇦🇷", "J"),
    Team("Austria", "Austria", "at", "🇦🇹", "J"),
    Team("Algeria", "Argelia", "dz", "🇩🇿", "J"),
    Team("Jordan", "Jordania", "jo", "🇯🇴", "J"),
    # Grupo K
    Team("Colombia", "Colombia", "co", "🇨🇴", "K"),
    Team("Portugal", "Portugal", "pt", "🇵🇹", "K"),
    Team("Congo DR", "Congo RD", "cd", "🇨🇩", "K"),
    Team("Uzbekistan", "Uzbekistan", "uz", "🇺🇿", "K"),
    # Grupo L
    Team("England", "Inglaterra", "gb-eng", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "L"),
    Team("Ghana", "Ghana", "gh", "🇬🇭", "L"),
    Team("Croatia", "Croacia", "hr", "🇭🇷", "L"),
    Team("Panama", "Panama", "pa", "🇵🇦", "L"),
]


# --- Indices derivados (no editar a mano: nacen de TEAMS) -------------------

BY_NAME: dict[str, Team] = {t.name: t for t in TEAMS}

# Grupos como {letra: [equipos en orden de siembra]}. Como TEAMS ya viene en
# orden por grupo, el dict conserva el orden correcto.
GROUPS: dict[str, list[str]] = {}
for _t in TEAMS:
    GROUPS.setdefault(_t.group, []).append(_t.name)

# Diccionarios de compatibilidad para quien todavia los espera por nombre.
DISPLAY_ES: dict[str, str] = {t.name: t.es for t in TEAMS}
ISO_CODES: dict[str, str] = {t.name: t.iso for t in TEAMS}
FLAGS: dict[str, str] = {t.name: t.emoji for t in TEAMS}


# --- Helpers ----------------------------------------------------------------

def team_es(name: str) -> str:
    """Nombre en espanol; si no se conoce el equipo, devuelve el nombre tal cual."""
    t = BY_NAME.get(name)
    return t.es if t else name


def iso(name: str) -> str:
    """Codigo ISO para flag-icons; cadena vacia si no se conoce."""
    t = BY_NAME.get(name)
    return t.iso if t else ""


def flag(name: str) -> str:
    """Bandera emoji; balon generico si no se conoce el equipo."""
    t = BY_NAME.get(name)
    return t.emoji if t else "⚽"


def as_dataset() -> dict[str, dict]:
    """
    Dataset serializable para el endpoint /api/teams. Devuelve
    { "Mexico": {"es": ..., "iso": ..., "emoji": ..., "group": ...}, ... }
    en orden de siembra para que el frontend construya su lookup desde aqui.
    """
    out: dict[str, dict] = {}
    for t in TEAMS:
        d = asdict(t)
        d.pop("name")  # la clave ya es el nombre
        out[t.name] = d
    return out
