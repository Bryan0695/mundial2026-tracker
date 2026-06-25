"""
Tests del dominio - Mundial 2026
================================
Cubre la logica pura (prediction.py y tournament.py), que es deterministica
y facil de testear. Ejecutar con:  pytest test_dominio.py -v

Instala pytest primero:  pip install pytest
"""

import prediction
import tournament
import teams


# --- Tests del motor de prediccion -----------------------------------------

def test_probabilidades_suman_100():
    """Las probabilidades 1X2 deben sumar ~100%."""
    e = prediction.PredictionEngine()
    p = e.predict("Brazil", "Argentina")
    total = p["prob_home_win"] + p["prob_draw"] + p["prob_away_win"]
    assert abs(total - 100.0) < 0.5, f"Suman {total}, no ~100"


def test_favorito_tiene_mas_probabilidad():
    """Un equipo mucho mas fuerte debe ser claro favorito."""
    e = prediction.PredictionEngine()
    p = e.predict("Germany", "Curacao")  # Alemania >> Curazao
    assert p["prob_home_win"] > p["prob_away_win"]
    assert p["prob_home_win"] > 50


def test_elo_sube_al_ganar():
    """Ganar debe subir el rating Elo."""
    e = prediction.PredictionEngine()
    elo_antes = e.get_elo("Ecuador")
    e.update_after_match("Ecuador", "Curacao", 3, 0)
    assert e.get_elo("Ecuador") > elo_antes


def test_elo_sube_mas_al_ganar_a_fuerte():
    """Ganarle a un rival fuerte debe subir mas que a uno debil."""
    e1 = prediction.PredictionEngine()
    e1.update_after_match("Ecuador", "Curacao", 1, 0)  # vs debil
    sube_vs_debil = e1.get_elo("Ecuador") - 1815

    e2 = prediction.PredictionEngine()
    e2.update_after_match("Ecuador", "Argentina", 1, 0)  # vs fuerte
    sube_vs_fuerte = e2.get_elo("Ecuador") - 1815

    assert sube_vs_fuerte > sube_vs_debil


def test_goal_stats_presentes():
    """La prediccion debe incluir las estadisticas de goles."""
    e = prediction.PredictionEngine()
    gs = e.predict("Spain", "Saudi Arabia")["goal_stats"]
    assert "over_2_5" in gs and "btts_yes" in gs
    assert 0 <= gs["over_2_5"] <= 100
    # over + under 2.5 deben sumar ~100
    assert abs(gs["over_2_5"] + gs["under_2_5"] - 100) < 0.5


def test_no_hay_clave_elo_duplicada():
    """INITIAL_ELO no debe tener equipos repetidos (F-013)."""
    # Si hubiera duplicados, el dict los colapsa; comparamos contra la fuente.
    import ast
    src = open("prediction.py", encoding="utf-8").read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
            str_keys = [k for k in keys if isinstance(k, str)]
            if "Ecuador" in str_keys and "Germany" in str_keys:
                assert len(str_keys) == len(set(str_keys)), "Hay claves duplicadas"
                break


# --- Tests de las reglas del torneo ----------------------------------------

def test_compute_standings_puntos():
    """Una victoria da 3 puntos al ganador, 0 al perdedor."""
    results = [{"home": "Mexico", "away": "South Africa",
                "home_goals": 2, "away_goals": 0}]
    st = tournament.compute_standings(results)
    mex = next(r for r in st["A"] if r["team"] == "Mexico")
    rsa = next(r for r in st["A"] if r["team"] == "South Africa")
    assert mex["pts"] == 3 and mex["pj"] == 1
    assert rsa["pts"] == 0 and rsa["pj"] == 1


def test_empate_da_un_punto():
    """Un empate da 1 punto a cada equipo."""
    results = [{"home": "Brazil", "away": "Morocco",
                "home_goals": 1, "away_goals": 1}]
    st = tournament.compute_standings(results)
    bra = next(r for r in st["C"] if r["team"] == "Brazil")
    mar = next(r for r in st["C"] if r["team"] == "Morocco")
    assert bra["pts"] == 1 and mar["pts"] == 1


def test_no_doble_conteo():
    """
    Un mismo partido en la lista solo debe contar una vez si se usa upsert.
    (Verifica que compute_standings es correcto con datos limpios.)
    """
    results = [{"home": "France", "away": "Iraq",
                "home_goals": 3, "away_goals": 0}]
    st = tournament.compute_standings(results)
    fra = next(r for r in st["I"] if r["team"] == "France")
    assert fra["pj"] == 1 and fra["pts"] == 3


def test_best_thirds_selecciona_8():
    """Con los 12 grupos completos, best_thirds debe marcar 8 clasificados."""
    # Genera resultados ficticios: en cada grupo el equipo 0 gana todo.
    results = []
    for teams in tournament.GROUPS.values():
        results += [
            {"home": teams[0], "away": teams[1], "home_goals": 2, "away_goals": 0},
            {"home": teams[2], "away": teams[3], "home_goals": 1, "away_goals": 0},
            {"home": teams[0], "away": teams[2], "home_goals": 2, "away_goals": 0},
            {"home": teams[1], "away": teams[3], "home_goals": 1, "away_goals": 0},
            {"home": teams[3], "away": teams[0], "home_goals": 0, "away_goals": 3},
            {"home": teams[1], "away": teams[2], "home_goals": 2, "away_goals": 1},
        ]
    st = tournament.compute_standings(results)
    thirds = tournament.best_thirds(st)
    qualified = [t for t in thirds["all_thirds"] if t["qualifies"]]
    assert len(qualified) == 8


def test_bracket_propaga_ganador():
    """El ganador de un cruce de 16avos debe avanzar a octavos."""
    results = []
    for teams in tournament.GROUPS.values():
        results += [
            {"home": teams[0], "away": teams[1], "home_goals": 2, "away_goals": 0},
            {"home": teams[2], "away": teams[3], "home_goals": 1, "away_goals": 0},
            {"home": teams[0], "away": teams[2], "home_goals": 2, "away_goals": 0},
            {"home": teams[1], "away": teams[3], "home_goals": 1, "away_goals": 0},
            {"home": teams[3], "away": teams[0], "home_goals": 0, "away_goals": 3},
            {"home": teams[1], "away": teams[2], "home_goals": 2, "away_goals": 1},
        ]
    st = tournament.compute_standings(results)
    # Resuelve un partido de 16avos (P73) y verifica que el ganador aparece en octavos.
    b = tournament.build_bracket(st, {"P73": {"home_goals": 2, "away_goals": 0}})
    p73 = next(m for m in b["rounds"]["r32"]["matches"] if m["code"] == "P73")
    assert p73["winner"] == p73["home"]  # gano el local
    # El ganador de P73 alimenta P90 (segun estructura oficial).
    p90 = next(m for m in b["rounds"]["r16"]["matches"] if m["code"] == "P90")
    assert p73["winner"] in (p90["home"], p90["away"])


# --- Tests de la fuente unica de equipos (teams.py) ------------------------

def test_teams_son_48():
    """El universo de selecciones del Mundial tiene exactamente 48 equipos."""
    assert len(teams.TEAMS) == 48


def test_no_hay_equipos_duplicados():
    """No debe haber nombres (name) repetidos en TEAMS."""
    names = [t.name for t in teams.TEAMS]
    assert len(names) == len(set(names)), "Hay equipos duplicados en TEAMS"


def test_grupos_completos():
    """GROUPS derivado tiene 12 grupos (A-L), cada uno con 4 equipos."""
    assert sorted(teams.GROUPS.keys()) == list("ABCDEFGHIJKL")
    for letter, equipos in teams.GROUPS.items():
        assert len(equipos) == 4, f"El grupo {letter} no tiene 4 equipos"


def test_todos_tienen_iso_y_es():
    """Cada equipo debe tener iso, es y emoji no vacios."""
    for t in teams.TEAMS:
        assert t.iso, f"{t.name} sin iso"
        assert t.es, f"{t.name} sin nombre en espanol"
        assert t.emoji, f"{t.name} sin emoji"


def test_groups_derivado_coincide():
    """teams.GROUPS debe coincidir con tournament.GROUPS (re-export sincronizado)."""
    assert teams.GROUPS == tournament.GROUPS


def test_as_dataset_forma():
    """as_dataset() devuelve 48 entradas con claves es/iso/emoji/group (sin name)."""
    ds = teams.as_dataset()
    assert len(ds) == 48
    for name, info in ds.items():
        assert set(info.keys()) == {"es", "iso", "emoji", "group"}
        assert "name" not in info  # la clave del dict ya es el nombre


def test_iso_codes_validos():
    """Los iso son minusculas de 2 letras, salvo gb-eng y gb-sct."""
    excepciones = {"gb-eng", "gb-sct"}
    for t in teams.TEAMS:
        if t.iso in excepciones:
            continue
        assert t.iso.islower(), f"{t.name}: iso {t.iso!r} no esta en minusculas"
        assert len(t.iso) == 2, f"{t.name}: iso {t.iso!r} no es de 2 letras"
