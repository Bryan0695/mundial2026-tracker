"""
Mundial 2026 Tracker - Backend Proxy (FastAPI)
================================================
Este backend actua como intermediario seguro entre el HTML (frontend)
y la API de futbol real (API-Football / api-sports.io).

Por que existe:
  - Protege tu API key (vive solo en el servidor, nunca en el navegador)
  - Resuelve el problema de CORS
  - Cachea respuestas para no agotar tu cuota de la API
  - Normaliza los datos al formato que tu HTML espera

Como correrlo:
  1. pip install fastapi uvicorn httpx python-dotenv
  2. Crea un archivo .env con tu key:  API_FOOTBALL_KEY=tu_key_aqui
  3. uvicorn main:app --reload --port 8000
  4. Abre http://localhost:8000/docs para ver la API interactiva
"""

import json
import logging
import os
import tempfile
import threading
import time
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from prediction import PredictionEngine
import tournament
import calendar_data
import teams

load_dotenv()

# Logging basico (F-011): deja traza en consola en vez de tragar errores.
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mundial2026")

# Lock global para escrituras de fichero (F-004): evita corrupcion si dos
# peticiones intentan guardar a la vez.
_io_lock = threading.Lock()

# Archivo donde se guardan los resultados ingresados manualmente.
RESULTS_FILE = "resultados.json"
KO_FILE = "ko_resultados.json"  # resultados de eliminatoria (16avos->final)

# Universo de equipos validos (F-007): nombres conocidos por grupos + motor.
KNOWN_TEAMS = set(tournament.DISPLAY_ES.keys())
for _g in tournament.GROUPS.values():
    KNOWN_TEAMS.update(_g)

# Motor de prediccion: una sola instancia viva mientras corre el servidor.
engine = PredictionEngine()


def _atomic_write(path: str, data) -> None:
    """
    Escritura atomica con lock (F-004): escribe a un temporal y hace rename.
    Si algo falla a mitad, el fichero original queda intacto.
    """
    with _io_lock:
        fd, tmp = tempfile.mkstemp(dir=".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)  # rename atomico
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise


def _read_json(path: str, default):
    """Lee un JSON; si esta corrupto, lo respalda a .bak y devuelve default (F-015)."""
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Fichero %s corrupto (%s); respaldando a .bak", path, e)
        try:
            os.replace(path, path + ".bak")
        except OSError:
            pass
        return default


def _is_final(r: dict) -> bool:
    """
    Un resultado cuenta como finalizado salvo que sea explicitamente "live".
    Retrocompatibilidad: los resultados viejos (sin campo "status") se asumen
    finalizados, asi el resultados.json antiguo sigue funcionando igual.
    """
    return r.get("status", "final") == "final"


def _result_index(saved: list) -> dict:
    """
    Indice de partidos con marcador: {(home, away): registro_completo}.
    Incluye tanto los parciales en vivo como los finalizados; quien necesite
    distinguir mira el campo "status" del registro (via _is_final). Se usa en
    el calendario y en las predicciones para no duplicar la construccion.
    """
    return {(r["home"], r["away"]): r for r in saved}


def _feed_elo(eng: PredictionEngine, results: list) -> None:
    """
    Alimenta el motor Elo con una lista de resultados de grupo, replicando
    SOLO los finalizados. Los marcadores en vivo NO mueven el Elo (un partido
    en curso no debe alterar ratings ni predicciones hasta que termine).
    """
    for r in results:
        if _is_final(r):
            eng.update_after_match(r["home"], r["away"],
                                   r["home_goals"], r["away_goals"])


def _save_results(results: list):
    """Guarda la lista de resultados de grupo en disco (atomico)."""
    _atomic_write(RESULTS_FILE, results)


def _save_ko_results(ko: dict):
    """Guarda los resultados de eliminatoria en disco (atomico)."""
    _atomic_write(KO_FILE, ko)


def _rebuild_engine() -> None:
    """
    Reconstruye los ratings Elo desde cero replicando los resultados FINALIZADOS:
    primero los de grupo, luego los de eliminatoria en orden de ronda (F-003, F-005).
    Esto evita el doble conteo (al corregir un marcador) y la deriva de Elo
    (los KO ahora si se replican al reiniciar). Los marcadores en vivo (status
    "live") se ignoran aqui: cuentan en las tablas, pero no en el Elo.
    """
    global engine
    engine = PredictionEngine()
    # 1) Resultados de grupo: SOLO los finalizados (los live no mueven el Elo).
    _feed_elo(engine, saved_results)
    # 2) Resultados de eliminatoria, en el orden correcto de las rondas.
    standings = tournament.compute_standings(saved_results)
    bracket = tournament.build_bracket(standings, ko_results)
    for rd in bracket["rounds"].values():
        for m in rd["matches"]:
            res = ko_results.get(m["code"])
            if res and m["home"] and m["away"]:
                engine.update_after_match(m["home"], m["away"],
                                          res["home_goals"], res["away_goals"])
    # Tercer lugar.
    if bracket.get("third_place"):
        tp = bracket["third_place"]
        res = ko_results.get(tp["code"])
        if res and tp["home"] and tp["away"]:
            engine.update_after_match(tp["home"], tp["away"],
                                      res["home_goals"], res["away_goals"])


# Carga inicial de datos desde disco.
saved_results: list = _read_json(RESULTS_FILE, [])
ko_results: dict = _read_json(KO_FILE, {})
# Reconstruye el motor con grupos + KO (F-005).
_rebuild_engine()

# --- Configuracion ---------------------------------------------------------

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")  # token para proteger mutaciones (F-001)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:8000")
API_HOST = "v3.football.api-sports.io"
API_BASE = f"https://{API_HOST}"

# ID de la Copa del Mundo 2026 en API-Football.
# OJO: verifica este ID en tu panel de API-Football, puede cambiar.
WORLD_CUP_LEAGUE_ID = 1
SEASON = 2026

# Cache simple en memoria: { url: (timestamp, datos) }
# Evita llamar a la API en cada request. La API tiene limite de llamadas/dia.
_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 60  # datos en vivo: 60s. Sube a 300 si no necesitas tiempo real.


app = FastAPI(title="Mundial 2026 Tracker API", version="1.0")

# CORS (F-006): restringe a origenes conocidos en vez de "*".
# Permite localhost y el archivo abierto directamente (origin "null").
_allowed_origins = [FRONTEND_ORIGIN, "http://localhost:8000",
                    "http://127.0.0.1:8000", "null"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --- Autenticacion de mutaciones (F-001) -----------------------------------

def require_token(x_admin_token: str = Header("")):
    """
    Protege los endpoints que modifican datos. Si ADMIN_TOKEN esta definido
    en el .env, las mutaciones exigen la cabecera X-Admin-Token correcta.
    Si NO esta definido (uso personal local), no exige nada: asi no rompe
    tu flujo actual hasta que decidas activar la proteccion.
    """
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="No autorizado")


def validate_teams(*teams: str):
    """Valida que los equipos existan en el universo conocido (F-007)."""
    for t in teams:
        if t not in KNOWN_TEAMS:
            raise HTTPException(status_code=422,
                                detail=f"Equipo no reconocido: {t}")


# --- Helper: llamada cacheada a la API real --------------------------------

async def _fetch_from_api(endpoint: str, params: dict) -> dict:
    """Llama a API-Football con la key, usando cache para ahorrar cuota."""
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Falta API_FOOTBALL_KEY. Crea un archivo .env con tu key.",
        )

    cache_key = f"{endpoint}?{sorted(params.items())}"
    now = time.time()

    # Si esta en cache y no expiro, devuelvelo sin llamar a la API.
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return data

    headers = {"x-apisports-key": API_KEY}
    url = f"{API_BASE}/{endpoint}"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        logger.warning("API %s: %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Error consultando la API de futbol")

    data = resp.json()
    _cache[cache_key] = (now, data)
    return data


# --- Endpoints que consume tu HTML -----------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "msg": "Mundial 2026 Tracker API. Ver /docs"}


@app.get("/health")
def health():
    """Healthcheck dedicado (F-011): util para monitoreo y como ping del front."""
    return {
        "status": "ok",
        "resultados_grupo": len(saved_results),
        "resultados_ko": len(ko_results),
        "auth_activa": bool(ADMIN_TOKEN),
    }


@app.get("/api/fixtures")
async def get_fixtures(date: str | None = None):
    """
    Partidos del Mundial. Si pasas ?date=2026-06-22 trae los de ese dia.
    Devuelve el formato simplificado que tu HTML necesita.
    """
    params = {"league": WORLD_CUP_LEAGUE_ID, "season": SEASON}
    if date:
        params["date"] = date

    raw = await _fetch_from_api("fixtures", params)
    return {"matches": [_simplify_fixture(f) for f in raw.get("response", [])]}


@app.get("/api/standings")
async def get_standings():
    """Tabla de posiciones de los 12 grupos."""
    params = {"league": WORLD_CUP_LEAGUE_ID, "season": SEASON}
    raw = await _fetch_from_api("standings", params)
    return {"raw": raw.get("response", [])}


@app.get("/api/topscorers")
async def get_topscorers():
    """Tabla de goleadores."""
    params = {"league": WORLD_CUP_LEAGUE_ID, "season": SEASON}
    raw = await _fetch_from_api("players/topscorers", params)
    scorers = []
    for p in raw.get("response", []):
        player = p.get("player", {})
        stats = (p.get("statistics") or [{}])[0]
        scorers.append({
            "name": player.get("name"),
            "team": stats.get("team", {}).get("name"),
            "goals": (stats.get("goals") or {}).get("total", 0),
        })
    return {"scorers": scorers}


# --- Normalizacion: de la API real al formato de tu HTML -------------------

def _simplify_fixture(f: dict) -> dict:
    """Convierte el objeto gigante de la API en lo minimo que el HTML usa."""
    fixture = f.get("fixture", {})
    teams = f.get("teams", {})
    goals = f.get("goals", {})
    status = fixture.get("status", {}).get("short", "")

    # Mapea estados de la API a los tuyos: live / final / scheduled
    if status in ("1H", "2H", "HT", "ET", "LIVE"):
        estado = "live"
    elif status in ("FT", "AET", "PEN"):
        estado = "final"
    else:
        estado = "scheduled"

    return {
        "id": fixture.get("id"),
        "date": fixture.get("date"),
        "status": estado,
        "home": {
            "name": teams.get("home", {}).get("name"),
            "logo": teams.get("home", {}).get("logo"),
            "score": goals.get("home"),
        },
        "away": {
            "name": teams.get("away", {}).get("name"),
            "logo": teams.get("away", {}).get("logo"),
            "score": goals.get("away"),
        },
    }


# --- Endpoints de PREDICCION (motor Dixon-Coles + Elo) ---------------------

@app.get("/api/predict")
def predict_match(home: str, away: str, neutral: bool = True):
    """
    Prediccion ANTES del partido.
    Ej: /api/predict?home=France&away=Iraq
    Devuelve probabilidades 1X2, marcador probable y confianza.
    """
    return engine.predict(home, away, neutral=neutral)


@app.post("/api/update-result", dependencies=[Depends(require_token)])
def update_result(home: str, away: str, home_goals: int, away_goals: int,
                  neutral: bool = True, status: str = "final"):
    """
    Registra (o corrige) un resultado de grupo. Usa UPSERT por (home, away):
    si el partido ya existia, lo reemplaza en vez de duplicarlo (F-003).
    Luego reconstruye los ratings Elo desde cero para no acumular (F-003/F-005).

    status:
      - "final" (default): marcador definitivo. Mueve el Elo y las predicciones.
      - "live": marcador en vivo. Cuenta en las tablas de grupo pero NO en el
        Elo. Llamar varias veces con "live" actualiza el mismo partido (upsert),
        no lo duplica; al pasar a "final" el Elo ya si lo replica.
    """
    validate_teams(home, away)  # F-007: rechaza equipos desconocidos
    if status not in ("live", "final"):
        raise HTTPException(status_code=422,
                            detail="status debe ser 'live' o 'final'")

    entry = {"home": home, "away": away,
             "home_goals": home_goals, "away_goals": away_goals,
             "status": status, "ts": time.time()}
    # Upsert: busca si ya existe ese partido.
    idx = next((i for i, r in enumerate(saved_results)
                if r["home"] == home and r["away"] == away), None)
    if idx is None:
        saved_results.append(entry)
    else:
        saved_results[idx] = entry
        logger.info("Resultado actualizado (%s): %s %s-%s %s",
                    status, home, home_goals, away_goals, away)

    _save_results(saved_results)
    _rebuild_engine()  # reconstruye Elo sin doble conteo (ignora los live)
    return {"status": "guardado", "match_status": status,
            "upsert": "update" if idx is not None else "insert"}


@app.get("/api/results")
def list_results():
    """Lista todos los resultados ingresados manualmente."""
    return {"results": saved_results, "total": len(saved_results)}


@app.post("/api/reset", dependencies=[Depends(require_token)])
def reset_all():
    """
    Borra todos los resultados y reinicia los ratings Elo a los valores iniciales.
    Util si te equivocaste e ingresaste algo mal.
    """
    global saved_results, ko_results
    saved_results = []
    ko_results = {}
    _save_results(saved_results)
    _save_ko_results(ko_results)
    _rebuild_engine()
    return {"status": "reiniciado", "msg": "Ratings, grupos y eliminatorias borrados"}


# --- Endpoints de TORNEO (tablas, terceros, dieciseisavos) -----------------

@app.get("/api/teams")
def get_teams():
    """
    Fuente unica de equipos: nombre en espanol, ISO de bandera, emoji y grupo.
    El frontend lo consume al cargar para construir su lookup de banderas y
    nombres, en vez de hardcodearlo (elimina la duplicacion en panel.html).
    """
    return {"teams": teams.as_dataset()}


@app.get("/api/groups")
def get_groups():
    """Estructura de los 12 grupos (para mostrar el calendario)."""
    return {"groups": tournament.GROUPS, "display_es": tournament.DISPLAY_ES}


@app.get("/api/group-standings")
def group_standings():
    """Las 12 tablas de grupo, calculadas desde los resultados ingresados."""
    standings = tournament.compute_standings(saved_results)
    return {"standings": standings}


@app.get("/api/best-thirds")
def best_thirds_endpoint():
    """Tabla de los mejores terceros (los 8 que clasifican)."""
    standings = tournament.compute_standings(saved_results)
    return tournament.best_thirds(standings)


@app.get("/api/round-of-32")
def round_of_32_endpoint():
    """Cruces de dieciseisavos segun la clasificacion actual."""
    standings = tournament.compute_standings(saved_results)
    matches = tournament.round_of_32(standings)
    return {"matches": matches}


@app.get("/api/calendar")
def get_calendar():
    """Calendario oficial: 72 partidos con fecha, sede, banderas y jornada real."""
    results = _result_index(saved_results)
    matches = []
    for m in calendar_data.OFFICIAL_CALENDAR:
        key = (m["home"], m["away"])
        row = {
            "date": m["date"],
            "jornada": m["jor"],
            "group": m["group"],
            "venue": m["venue"],
            "home": m["home"], "away": m["away"],
            "home_es": tournament.team_es(m["home"]),
            "away_es": tournament.team_es(m["away"]),
            "home_flag": calendar_data.flag(m["home"]),
            "away_flag": calendar_data.flag(m["away"]),
        }
        rec = results.get(key)
        if rec is None:
            row["status"] = "pending"
            row["played"] = False
        else:
            st = "final" if _is_final(rec) else "live"
            row["status"] = st
            # "played" se mantiene con su semantica antigua (True = finalizado)
            # para no romper a quien ya lo consumiera; el marcador en vivo se
            # distingue por status="live".
            row["played"] = st == "final"
            row["home_goals"] = rec["home_goals"]
            row["away_goals"] = rec["away_goals"]
        matches.append(row)
    return {"calendar": matches}


# --- Endpoints del BRACKET ELIMINATORIO (16avos -> Final) ------------------

@app.get("/api/bracket")
def get_bracket():
    """
    Devuelve el bracket completo: 16avos, octavos, cuartos, semis, final,
    tercer lugar y campeon. Los ganadores avanzan solos a la siguiente fase.
    """
    standings = tournament.compute_standings(saved_results)
    bracket = tournament.build_bracket(standings, ko_results)
    return bracket


@app.post("/api/ko-result", dependencies=[Depends(require_token)])
def save_ko_result(code: str, home_goals: int, away_goals: int,
                   pen_home: int | None = None, pen_away: int | None = None):
    """
    Registra (o corrige) el resultado de un partido de eliminatoria por su
    codigo FIFA. Si fue empate, pasa pen_home y pen_away para los penales.
    El ganador avanza automaticamente a la siguiente fase. Como ko_results es
    un dict por codigo, ya es upsert natural (corregir no duplica).
    """
    entry = {"home_goals": home_goals, "away_goals": away_goals}
    if pen_home is not None and pen_away is not None:
        entry["pen_home"] = pen_home
        entry["pen_away"] = pen_away
    ko_results[code] = entry
    _save_ko_results(ko_results)

    # Reconstruye Elo desde cero con grupos + KO (evita doble conteo, F-003/F-005).
    _rebuild_engine()
    standings = tournament.compute_standings(saved_results)
    bracket = tournament.build_bracket(standings, ko_results)
    return {"status": "guardado", "code": code, "bracket": bracket}


@app.post("/api/reset-ko", dependencies=[Depends(require_token)])
def reset_ko():
    """Borra solo los resultados de eliminatoria (mantiene los de grupo)."""
    global ko_results
    ko_results = {}
    _save_ko_results(ko_results)
    _rebuild_engine()  # recalcula Elo solo con resultados de grupo
    return {"status": "eliminatorias reiniciadas"}


@app.get("/api/all-predictions")
def all_predictions(only_upcoming: bool = True):
    """
    Predicciones de TODOS los partidos del calendario, con fecha y banderas.
    only_upcoming=True: solo los que aun no se han jugado.
    Los ya jugados incluyen su resultado real.
    """
    results = _result_index(saved_results)
    out = []
    for m in calendar_data.OFFICIAL_CALENDAR:
        key = (m["home"], m["away"])
        rec = results.get(key)
        # Solo los FINALIZADOS cuentan como "jugados" para las predicciones:
        # un partido en vivo sigue mostrando su prediccion (el Elo lo ignora).
        is_played = rec is not None and _is_final(rec)
        if only_upcoming and is_played:
            continue
        pred = engine.predict(m["home"], m["away"])
        row = {
            "date": m["date"], "jornada": m["jor"], "group": m["group"],
            "venue": m["venue"],
            "home": m["home"], "away": m["away"],
            "home_es": tournament.team_es(m["home"]),
            "away_es": tournament.team_es(m["away"]),
            "home_flag": calendar_data.flag(m["home"]),
            "away_flag": calendar_data.flag(m["away"]),
            "prob_home": pred["prob_home_win"],
            "prob_draw": pred["prob_draw"],
            "prob_away": pred["prob_away_win"],
            "score": pred["most_likely_score"],
            "confidence": pred["confidence"],
            "xg_home": pred["expected_goals"]["home"],
            "xg_away": pred["expected_goals"]["away"],
            "xg_total": pred["expected_goals"]["total"],
            "goal_stats": pred["goal_stats"],
            "played": is_played,
        }
        if is_played:
            row["real_home"], row["real_away"] = rec["home_goals"], rec["away_goals"]
        out.append(row)
    return {"predictions": out, "total": len(out)}


@app.get("/api/ranking")
def get_ranking():
    """Ranking actual de selecciones por rating Elo (se mueve con cada partido)."""
    return {"ranking": engine.ranking()}


@app.post("/api/sync-results")
async def sync_results():
    """
    Trae los partidos FINALIZADOS de la API real y actualiza los ratings
    automaticamente con cada resultado. Esto es la actualizacion 'en vivo':
    llama esto periodicamente (o tras cada jornada) y el modelo se pone al dia.
    """
    params = {"league": WORLD_CUP_LEAGUE_ID, "season": SEASON, "status": "FT"}
    raw = await _fetch_from_api("fixtures", params)

    updated = []
    for f in raw.get("response", []):
        simple = _simplify_fixture(f)
        if simple["status"] != "final":
            continue
        hg, ag = simple["home"]["score"], simple["away"]["score"]
        if hg is None or ag is None:
            continue
        result = engine.update_after_match(
            simple["home"]["name"], simple["away"]["name"], hg, ag
        )
        updated.append(result)

    return {"synced": len(updated), "updates": updated}


# Sirve el HTML del tracker desde el mismo backend (opcional pero comodo).
# Pon tu mundial2026_tracker.html dentro de una carpeta "static/".
if os.path.isdir("static"):
    app.mount("/app", StaticFiles(directory="static", html=True), name="static")
