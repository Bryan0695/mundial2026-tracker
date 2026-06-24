"""
Motor de prediccion - Dixon-Coles + Elo
========================================
Este modulo es el cerebro estadistico del tracker. Implementa el mismo
enfoque que usan los predictores profesionales de torneos (estilo del
trabajo de Joachim Klemen y modelos tipo FiveThirtyEight):

  1. ELO         -> cada seleccion tiene un rating de fuerza global.
                    Sube si gana, baja si pierde. La magnitud depende
                    de contra quien jugo (ganarle a un fuerte vale mas).

  2. DIXON-COLES -> convierte la diferencia de fuerza en goles esperados
                    (lambda) para cada equipo, y usa la distribucion de
                    Poisson para sacar la probabilidad de cada marcador.
                    Dixon-Coles ademas corrige los resultados bajos
                    (0-0, 1-0, 0-1, 1-1) que Poisson puro subestima.

  3. ACTUALIZACION -> cuando entra un resultado real, se llama a
                      update_after_match() y los ratings Elo se ajustan.
                      La siguiente prediccion ya usa los nuevos ratings.

No requiere librerias pesadas: solo math de la libreria estandar.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# --- Parametros del modelo (ajustables) ------------------------------------

ELO_K = 40.0            # cuanto se mueve el rating por partido (torneo: 40-60)
ELO_HOME_ADV = 65.0     # ventaja de jugar "en casa" (sede local CONCACAF)
HOME_GOAL_BASE = 1.45   # goles esperados base del equipo local
AWAY_GOAL_BASE = 1.15   # goles esperados base del visitante
ELO_TO_GOALS = 0.0035   # factor que convierte diferencia Elo en goles
RHO = -0.13             # parametro de correccion Dixon-Coles para marcadores bajos
MAX_GOALS = 8           # tope de goles a considerar en la matriz de probabilidad


# Ratings Elo iniciales (junio 2026, aproximados al ranking FIFA real).
# Estos son el punto de partida; el modelo los va moviendo con cada resultado.
INITIAL_ELO: dict[str, float] = {
    "Argentina": 2105, "France": 2085, "Spain": 2075, "Brazil": 2065,
    "England": 2010, "Portugal": 1995, "Netherlands": 1990, "Germany": 1980,
    "Belgium": 1945, "Croatia": 1930, "Italy": 1925, "Morocco": 1915,
    "Colombia": 1900, "Uruguay": 1895, "Japan": 1860, "USA": 1850,
    "Mexico": 1845, "Switzerland": 1840, "Senegal": 1835, "Norway": 1830,
    "Ecuador": 1815, "Austria": 1810, "Egypt": 1800, "Ivory Coast": 1790,
    "Korea Republic": 1785, "Australia": 1775, "Canada": 1770, "Sweden": 1765,
    "Iran": 1760, "Paraguay": 1745, "Scotland": 1740,
    "Algeria": 1735, "Cape Verde": 1660, "Ghana": 1700, "Tunisia": 1695,
    "Saudi Arabia": 1670, "Qatar": 1665, "Bosnia and Herzegovina": 1710,
    "South Africa": 1655, "Czechia": 1745, "Panama": 1650, "Jordan": 1620,
    "New Zealand": 1610, "Uzbekistan": 1640, "Congo DR": 1685, "Iraq": 1630,
    "Curacao": 1560, "Haiti": 1545,
}

DEFAULT_ELO = 1700.0  # para cualquier seleccion no listada


# --- Estado del motor ------------------------------------------------------

@dataclass
class PredictionEngine:
    """Mantiene los ratings y produce/actualiza predicciones."""
    elo: dict[str, float] = field(default_factory=lambda: dict(INITIAL_ELO))

    def get_elo(self, team: str) -> float:
        return self.elo.get(team, DEFAULT_ELO)

    # -- Prediccion ANTES del partido --------------------------------------

    def predict(self, home: str, away: str, neutral: bool = True) -> dict:
        """
        Devuelve probabilidades 1X2, marcador mas probable y nivel de confianza.
        neutral=True cuando ninguno juega de local (la mayoria de partidos de Mundial).
        """
        eh = self.get_elo(home)
        ea = self.get_elo(away)

        # Ventaja de campo solo si NO es cancha neutral.
        home_adv = 0.0 if neutral else ELO_HOME_ADV
        diff = (eh + home_adv) - ea

        # Goles esperados (lambda) de cada equipo, derivados de la diferencia Elo.
        lambda_home = max(0.15, HOME_GOAL_BASE + diff * ELO_TO_GOALS)
        lambda_away = max(0.15, AWAY_GOAL_BASE - diff * ELO_TO_GOALS)

        # Matriz de probabilidad de cada marcador con correccion Dixon-Coles.
        p_home, p_draw, p_away, best_score, stats = self._score_matrix(lambda_home, lambda_away)

        confidence = self._confidence(p_home, p_draw, p_away)
        total_xg = round(lambda_home + lambda_away, 2)

        return {
            "home_team": home,
            "away_team": away,
            "prob_home_win": round(p_home * 100, 1),
            "prob_draw": round(p_draw * 100, 1),
            "prob_away_win": round(p_away * 100, 1),
            "most_likely_score": f"{best_score[0]}-{best_score[1]}",
            "expected_goals": {
                "home": round(lambda_home, 2),
                "away": round(lambda_away, 2),
                "total": total_xg,
            },
            "confidence": confidence,
            "elo": {"home": round(eh), "away": round(ea)},
            "goal_stats": stats,
        }

    def _score_matrix(self, lh: float, la: float):
        """
        Construye la matriz de Poisson + correccion Dixon-Coles y calcula
        de paso todas las estadisticas de goles (over/under, BTTS, clean sheets).
        """
        p_home = p_draw = p_away = 0.0
        best_p = -1.0
        best_score = (0, 0)

        # Acumuladores de estadisticas de goles.
        scores = []           # lista de (prob, i, j) para sacar top marcadores
        p_over15 = p_over25 = p_over35 = 0.0
        p_btts = 0.0          # ambos marcan
        p_home_cs = 0.0       # visitante no marca -> local clean sheet
        p_away_cs = 0.0       # local no marca -> visitante clean sheet

        for i in range(MAX_GOALS + 1):
            for j in range(MAX_GOALS + 1):
                p = _poisson(i, lh) * _poisson(j, la) * _dc_tau(i, j, lh, la, RHO)
                scores.append((p, i, j))
                if p > best_p:
                    best_p = p
                    best_score = (i, j)
                # 1X2
                if i > j:
                    p_home += p
                elif i == j:
                    p_draw += p
                else:
                    p_away += p
                # Estadisticas de goles
                total_goals = i + j
                if total_goals > 1.5: p_over15 += p
                if total_goals > 2.5: p_over25 += p
                if total_goals > 3.5: p_over35 += p
                if i > 0 and j > 0: p_btts += p       # ambos marcan
                if j == 0: p_home_cs += p             # local no recibe gol
                if i == 0: p_away_cs += p             # visitante no recibe gol

        total = p_home + p_draw + p_away
        # Top 3 marcadores mas probables.
        scores.sort(reverse=True)
        top_scores = [{"score": f"{i}-{j}", "prob": round(p / total * 100, 1)}
                      for p, i, j in scores[:3]]

        stats = {
            "over_1_5": round(p_over15 / total * 100, 1),
            "under_1_5": round((1 - p_over15 / total) * 100, 1),
            "over_2_5": round(p_over25 / total * 100, 1),
            "under_2_5": round((1 - p_over25 / total) * 100, 1),
            "over_3_5": round(p_over35 / total * 100, 1),
            "btts_yes": round(p_btts / total * 100, 1),
            "btts_no": round((1 - p_btts / total) * 100, 1),
            "clean_sheet_home": round(p_home_cs / total * 100, 1),
            "clean_sheet_away": round(p_away_cs / total * 100, 1),
            "top_scores": top_scores,
        }
        return p_home / total, p_draw / total, p_away / total, best_score, stats

    @staticmethod
    def _confidence(ph: float, pd: float, pa: float) -> str:
        """Nivel de confianza segun que tan clara es la favorita."""
        top = max(ph, pd, pa)
        if top >= 0.60:
            return "alta"
        if top >= 0.45:
            return "media"
        return "baja"

    # -- Actualizacion DESPUES del partido ---------------------------------

    def update_after_match(self, home: str, away: str,
                           home_goals: int, away_goals: int,
                           neutral: bool = True) -> dict:
        """
        Recalcula los ratings Elo tras un resultado real.
        Esto es lo que hace que el modelo 'aprenda' con cada partido.
        """
        eh = self.get_elo(home)
        ea = self.get_elo(away)

        home_adv = 0.0 if neutral else ELO_HOME_ADV

        # Resultado esperado (0 a 1) segun Elo, formula estandar.
        exp_home = 1.0 / (1.0 + 10 ** (-((eh + home_adv) - ea) / 400.0))
        exp_away = 1.0 - exp_home

        # Resultado real: 1 gana, 0.5 empate, 0 pierde.
        if home_goals > away_goals:
            score_home, score_away = 1.0, 0.0
        elif home_goals < away_goals:
            score_home, score_away = 0.0, 1.0
        else:
            score_home = score_away = 0.5

        # Multiplicador por diferencia de goles (ganar 4-0 mueve mas que 1-0).
        margin = abs(home_goals - away_goals)
        g_mult = math.log(margin + 1) + 1  # 0->1, 1->1.69, 3->2.39 ...

        new_eh = eh + ELO_K * g_mult * (score_home - exp_home)
        new_ea = ea + ELO_K * g_mult * (score_away - exp_away)

        self.elo[home] = round(new_eh, 1)
        self.elo[away] = round(new_ea, 1)

        return {
            "home": home, "away": away,
            "result": f"{home_goals}-{away_goals}",
            "elo_change": {
                home: round(new_eh - eh, 1),
                away: round(new_ea - ea, 1),
            },
            "new_elo": {home: round(new_eh), away: round(new_ea)},
        }

    def ranking(self) -> list[dict]:
        """Devuelve los equipos ordenados por rating Elo actual."""
        ordered = sorted(self.elo.items(), key=lambda kv: kv[1], reverse=True)
        return [{"team": t, "elo": round(e)} for t, e in ordered]


# --- Funciones matematicas auxiliares --------------------------------------

def _poisson(k: int, lam: float) -> float:
    """Probabilidad de exactamente k goles dado un promedio lam."""
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def _dc_tau(i: int, j: int, lh: float, la: float, rho: float) -> float:
    """
    Correccion Dixon-Coles para marcadores bajos.
    Poisson puro subestima 0-0/1-1 y sobreestima 1-0/0-1; tau corrige eso.
    """
    if i == 0 and j == 0:
        return 1 - lh * la * rho
    if i == 0 and j == 1:
        return 1 + lh * rho
    if i == 1 and j == 0:
        return 1 + la * rho
    if i == 1 and j == 1:
        return 1 - rho
    return 1.0


# --- Demo: corre este archivo directo para probarlo ------------------------

if __name__ == "__main__":
    engine = PredictionEngine()

    print("=== Prediccion ANTES del partido: Francia vs Iraq ===")
    pred = engine.predict("France", "Iraq")
    for k, v in pred.items():
        print(f"  {k}: {v}")

    print("\n=== Llega el resultado real: Francia 3-0 Iraq ===")
    upd = engine.update_after_match("France", "Iraq", 3, 0)
    print(f"  Cambio Elo: {upd['elo_change']}")

    print("\n=== Misma prediccion DESPUES (Francia ya subio un poco) ===")
    pred2 = engine.predict("France", "Norway")
    print(f"  Francia vs Noruega -> Francia {pred2['prob_home_win']}%, "
          f"empate {pred2['prob_draw']}%, Noruega {pred2['prob_away_win']}%")
    print(f"  Marcador probable: {pred2['most_likely_score']} "
          f"(confianza {pred2['confidence']})")
