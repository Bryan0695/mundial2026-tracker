"""
Modulo de torneo - Mundial 2026
================================
Contiene:
  - La estructura real de los 12 grupos (A-L) con sus 48 equipos.
  - El calendario de partidos de fase de grupos.
  - La logica para calcular tablas de grupo desde los resultados.
  - El calculo de los 8 mejores terceros (criterios oficiales FIFA).
  - La construccion de los cruces de dieciseisavos.

Todo se calcula desde una lista de resultados, asi que las tablas se
arman solas conforme ingresas marcadores.
"""

from __future__ import annotations

# La estructura de grupos y los nombres en espanol viven en teams.py (fuente
# unica). Aqui solo se importan para no duplicar el universo de selecciones.
from teams import GROUPS, DISPLAY_ES, team_es

# Matriz oficial FIFA (Annex C): las 495 combinaciones de 8 grupos de terceros
# y a que partido va cada uno. Es la fuente de verdad de la asignacion.
import r32_matrix


def all_group_matches() -> list[dict]:
    """
    Genera los 6 partidos de cada grupo (todos contra todos), organizados
    por jornada. Sirve para mostrar el calendario completo y poder ingresar
    cada resultado rapido sin escribir los nombres a mano.
    """
    matches = []
    for letter, teams in GROUPS.items():
        pairs = [
            (teams[0], teams[1], 1), (teams[2], teams[3], 1),
            (teams[0], teams[2], 2), (teams[1], teams[3], 2),
            (teams[3], teams[0], 3), (teams[1], teams[2], 3),
        ]
        for h, a, jornada in pairs:
            matches.append({
                "group": letter,
                "jornada": jornada,
                "home": h, "away": a,
                "home_es": team_es(h), "away_es": team_es(a),
            })
    return matches


def group_of(team: str) -> str | None:
    """Devuelve la letra del grupo de un equipo."""
    for letter, teams in GROUPS.items():
        if team in teams:
            return letter
    return None


# --- Calculo de tablas de grupo --------------------------------------------

def _blank_row(team: str) -> dict:
    return {
        "team": team, "team_es": team_es(team),
        "pj": 0, "g": 0, "e": 0, "p": 0,
        "gf": 0, "gc": 0, "dg": 0, "pts": 0,
    }


def compute_standings(results: list[dict]) -> dict[str, list[dict]]:
    """
    Recibe la lista de resultados y devuelve las 12 tablas ordenadas.
    Cada resultado: {home, away, home_goals, away_goals}.
    """
    # Inicializa todas las filas en cero.
    rows: dict[str, dict] = {}
    for teams in GROUPS.values():
        for t in teams:
            rows[t] = _blank_row(t)

    # Aplica cada resultado a las filas correspondientes.
    for r in results:
        h, a = r["home"], r["away"]
        hg, ag = r["home_goals"], r["away_goals"]
        if h not in rows or a not in rows:
            continue  # partido de eliminatoria o equipo no reconocido
        if group_of(h) != group_of(a):
            continue  # solo cuentan partidos del mismo grupo

        for team, gf, gc in ((h, hg, ag), (a, ag, hg)):
            row = rows[team]
            row["pj"] += 1
            row["gf"] += gf
            row["gc"] += gc
            row["dg"] = row["gf"] - row["gc"]
            if gf > gc:
                row["g"] += 1
                row["pts"] += 3
            elif gf == gc:
                row["e"] += 1
                row["pts"] += 1
            else:
                row["p"] += 1

    # Ordena cada grupo: puntos, dif. de goles, goles a favor.
    standings: dict[str, list[dict]] = {}
    for letter, teams in GROUPS.items():
        group_rows = [rows[t] for t in teams]
        group_rows.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
        for i, row in enumerate(group_rows):
            row["pos"] = i + 1
        standings[letter] = group_rows

    return standings


# --- Mejores terceros (criterios oficiales FIFA) ---------------------------

def best_thirds(standings: dict[str, list[dict]]) -> dict:
    """
    Calcula los 8 mejores terceros de los 12 grupos.
    Orden: puntos -> diferencia de goles -> goles a favor.
    """
    thirds = []
    for letter, rows in standings.items():
        if len(rows) >= 3:
            third = dict(rows[2])
            third["group"] = letter
            thirds.append(third)

    thirds.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)

    for i, t in enumerate(thirds):
        t["third_rank"] = i + 1
        t["qualifies"] = i < 8  # los primeros 8 clasifican

    return {
        "all_thirds": thirds,
        "qualified": [t for t in thirds if t["qualifies"]],
        "eliminated": [t for t in thirds if not t["qualifies"]],
    }


# --- Construccion de dieciseisavos -----------------------------------------

# Estructura oficial FIFA 2026 de los 16avos (partidos 73-88), en orden.
# Cada entrada: (codigo, fuente_local, fuente_visitante). Las fuentes son:
#   "1X" -> 1ro del grupo X     "2X" -> 2do del grupo X
#   "3rd" -> uno de los 8 mejores terceros (el grupo permitido lo fija THIRD_SLOTS)
# Fuente: calendario/reglamento oficial FIFA (CONMEBOL/UEFA/etc.).
OFFICIAL_R32 = [
    ("P73", "2A", "2B"),    # 2A v 2B
    ("P74", "1E", "3rd"),   # 1E (Alemania) v 3ro
    ("P75", "1F", "2C"),    # 1F v 2C
    ("P76", "1C", "2F"),    # 1C v 2F
    ("P77", "1I", "3rd"),   # 1I v 3ro
    ("P78", "2E", "2I"),    # 2E v 2I
    ("P79", "1A", "3rd"),   # 1A (Mexico) v 3ro
    ("P80", "1L", "3rd"),   # 1L v 3ro
    ("P81", "1D", "3rd"),   # 1D (USA) v 3ro
    ("P82", "1G", "3rd"),   # 1G v 3ro
    ("P83", "2K", "2L"),    # 2K v 2L
    ("P84", "1H", "2J"),    # 1H v 2J
    ("P85", "1B", "3rd"),   # 1B (Suiza) v 3ro
    ("P86", "1J", "2H"),    # 1J (Argentina) v 2H
    ("P87", "1K", "3rd"),   # 1K v 3ro
    ("P88", "2D", "2G"),    # 2D v 2G
]

# Conjunto de grupos permitidos por partido segun la regla oficial FIFA: un
# partido que recibe tercero SOLO puede recibirlo de estos grupos. La matriz
# r32_matrix respeta estos conjuntos; aqui se conservan para validarlo en los
# tests (un tercero nunca debe caer en un slot fuera de su conjunto).
THIRD_SLOTS = {
    "P74": frozenset("ABCDF"),
    "P77": frozenset("CDFGH"),
    "P79": frozenset("CEFHI"),
    "P80": frozenset("EHIJK"),
    "P81": frozenset("BEFIJ"),
    "P82": frozenset("AEHIJ"),
    "P85": frozenset("EFGIJ"),
    "P87": frozenset("DEIJL"),
}


def round_of_32(standings: dict[str, list[dict]]) -> list[dict]:
    """
    Arma los 16 cruces de dieciseisavos con la estructura OFICIAL FIFA 2026
    (partidos 73-88). La asignacion de los 8 mejores terceros sale de la matriz
    oficial (Annex C) via r32_matrix.lookup: se toman los 8 grupos que aportan
    tercero y la matriz dicta que grupo va a cada partido. Si todavia no hay 8
    terceros definidos (o la combinacion no esta en la matriz), los slots de
    tercero quedan en "Por definir" sin romper los cruces de rival fijo.
    """
    def first(g):  return standings[g][0] if len(standings.get(g, [])) >= 1 else None
    def second(g): return standings[g][1] if len(standings.get(g, [])) >= 2 else None
    def third(g):  return standings[g][2] if g and len(standings.get(g, [])) >= 3 else None

    qualified_thirds = best_thirds(standings)["qualified"]
    third_groups = [t["group"] for t in qualified_thirds]
    # {codigo_partido: letra_grupo} segun Annex C, o None si no hay 8 terceros.
    slot_map = r32_matrix.lookup(third_groups)

    def resolve(code: str, src: str):
        if src == "3rd":
            if not slot_map:
                return None
            return third(slot_map.get(code))
        pos, group = src[0], src[1]
        return first(group) if pos == "1" else second(group)

    matches = []
    for code, home_src, away_src in OFFICIAL_R32:
        home = resolve(code, home_src)
        away = resolve(code, away_src)
        h_name = home["team"] if home else None
        a_name = away["team"] if away else None
        matches.append({
            "code": code,
            "home": h_name, "away": a_name,
            "home_es": team_es(h_name) if h_name else "Por definir",
            "away_es": team_es(a_name) if a_name else "Por definir",
            "label": code,
        })
    return matches


# ===========================================================================
# BRACKET ELIMINATORIO (16avos -> Final)
# ===========================================================================
# El bracket avanza solo: el ganador de cada llave pasa a la siguiente fase.
# Los resultados de eliminatoria se guardan aparte (con la fase como clave)
# para no mezclarlos con los partidos de grupo.

# Orden de las fases y cuantos partidos tiene cada una.
KO_ROUNDS = [
    ("r32", "Dieciseisavos", 16),
    ("r16", "Octavos", 8),
    ("qf", "Cuartos", 4),
    ("sf", "Semifinales", 2),
    ("final", "Final", 1),
]


def ko_match_id(round_key: str, index: int) -> str:
    """ID unico de un partido de eliminatoria, ej: 'r32_0', 'qf_3'."""
    return f"{round_key}_{index}"


def build_bracket(standings: dict, ko_results: dict) -> dict:
    """
    Construye el bracket completo con la estructura OFICIAL FIFA 2026.
    Los ganadores avanzan solos segun los emparejamientos oficiales
    (partidos 73-104 del calendario FIFA).

    ko_results: dict { match_code: {"home_goals":x, "away_goals":y,
                                    "pen_home":a, "pen_away":b (opcional)} }
    """
    # --- 16avos: siembra desde grupos (partidos 73-88) ---
    r32 = round_of_32(standings)

    def resolve(home, away, code):
        """Calcula ganador de un cruce dado su resultado guardado."""
        res = ko_results.get(code)
        winner = None
        score = None
        if res and home and away:
            hg, ag = res.get("home_goals"), res.get("away_goals")
            if hg is not None and ag is not None:
                score = f"{hg}-{ag}"
                if hg > ag:
                    winner = home
                elif ag > hg:
                    winner = away
                else:
                    ph, pa = res.get("pen_home"), res.get("pen_away")
                    if ph is not None and pa is not None:
                        winner = home if ph > pa else away
                        score = f"{hg}-{ag} (pen {ph}-{pa})"
        return winner, score

    # Mapa de codigo -> ganador, para encadenar rondas.
    win = {}

    # Procesa 16avos.
    r32_matches = []
    for m in r32:
        w, sc = resolve(m["home"], m["away"], m["code"])
        win[m["code"]] = w
        r32_matches.append({**m, "winner": w,
                            "winner_es": team_es(w) if w else None, "score": sc})

    # --- Octavos (partidos 89-96): emparejamientos oficiales ---
    # Cada uno: (codigo, ganador_de_X, ganador_de_Y)
    r16_def = [
        ("P89", "P74", "P77"), ("P90", "P73", "P75"),
        ("P91", "P76", "P78"), ("P92", "P79", "P80"),
        ("P93", "P83", "P84"), ("P94", "P81", "P82"),
        ("P95", "P86", "P88"), ("P96", "P85", "P87"),
    ]
    r16_matches = _build_ko_round(r16_def, win, ko_results, resolve)

    # --- Cuartos (partidos 97-100) ---
    qf_def = [
        ("P97", "P89", "P90"), ("P98", "P93", "P94"),
        ("P99", "P91", "P92"), ("P100", "P95", "P96"),
    ]
    qf_matches = _build_ko_round(qf_def, win, ko_results, resolve)

    # --- Semifinales (partidos 101-102) ---
    sf_def = [("P101", "P97", "P98"), ("P102", "P99", "P100")]
    sf_matches = _build_ko_round(sf_def, win, ko_results, resolve)

    # --- Tercer lugar (partido 103): perdedores de semis ---
    sf_losers = []
    for m in sf_matches:
        if m["winner"] and m["home"] and m["away"]:
            loser = m["away"] if m["winner"] == m["home"] else m["home"]
            sf_losers.append(loser)
    third_place = None
    if len(sf_losers) == 2:
        w, sc = resolve(sf_losers[0], sf_losers[1], "P103")
        third_place = {
            "code": "P103", "round_name": "Tercer lugar",
            "home": sf_losers[0], "away": sf_losers[1],
            "home_es": team_es(sf_losers[0]), "away_es": team_es(sf_losers[1]),
            "winner": w, "winner_es": team_es(w) if w else None, "score": sc,
        }

    # --- Final (partido 104) ---
    final_home = win.get("P101")
    final_away = win.get("P102")
    fw, fsc = resolve(final_home, final_away, "P104")
    final_match = {
        "code": "P104", "round_name": "Final",
        "home": final_home, "away": final_away,
        "home_es": team_es(final_home) if final_home else "Por definir",
        "away_es": team_es(final_away) if final_away else "Por definir",
        "winner": fw, "winner_es": team_es(fw) if fw else None, "score": fsc,
    }

    return {
        "rounds": {
            "r32": {"name": "Dieciseisavos", "matches": r32_matches},
            "r16": {"name": "Octavos", "matches": r16_matches},
            "qf": {"name": "Cuartos", "matches": qf_matches},
            "sf": {"name": "Semifinales", "matches": sf_matches},
            "final": {"name": "Final", "matches": [final_match]},
        },
        "third_place": third_place,
        "champion": fw,
        "champion_es": team_es(fw) if fw else None,
    }


def _build_ko_round(definitions, win, ko_results, resolve):
    """Helper: construye una ronda KO a partir de los ganadores previos."""
    matches = []
    for code, src_home, src_away in definitions:
        home = win.get(src_home)
        away = win.get(src_away)
        w, sc = resolve(home, away, code)
        win[code] = w
        matches.append({
            "code": code,
            "home": home, "away": away,
            "home_es": team_es(home) if home else "Por definir",
            "away_es": team_es(away) if away else "Por definir",
            "winner": w, "winner_es": team_es(w) if w else None,
            "score": sc, "label": code,
        })
    return matches
