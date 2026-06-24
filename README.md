# ⚽ Mundial 2026 — Tracker & Motor de Predicción

Sistema full-stack para seguir la Copa del Mundo FIFA 2026 con predicciones
estadísticas que se actualizan con cada resultado real.

## ¿Qué hace?

- **Calendario completo** de los 104 partidos (72 de grupos + 32 de eliminatoria)
  con fechas, sedes y banderas.
- **Motor de predicción Dixon-Coles + Elo**: calcula probabilidades 1X2,
  marcador probable, y estadísticas de goles (Over/Under, Ambos Marcan,
  Clean Sheets) para cada partido.
- **Tablas de grupos** que se arman solas con cada resultado.
- **Mejores terceros** según criterios oficiales FIFA.
- **Bracket eliminatorio** (16avos → final) con avance automático del ganador.
- **Ranking Elo** que se mueve con cada partido.

El modelo aprende: cuando ingresas un resultado real, los ratings Elo se
recalculan y las siguientes predicciones se ajustan.

## Arquitectura

```
panel.html  ──fetch──►  FastAPI (main.py)  ──►  prediction.py  (motor Dixon-Coles + Elo)
 navegador               backend                  tournament.py  (grupos, terceros, bracket)
                                                   calendar_data.py (calendario oficial)
```

## Cómo correrlo

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. (Opcional) crear .env con tu API key de api-football.com
#    Solo necesario si quieres datos en vivo. En modo manual no hace falta.
#    API_FOOTBALL_KEY=tu_key

# 3. Levantar el backend
python -m uvicorn main:app --reload --port 8000

# 4. Abrir panel.html en el navegador
```

El backend queda en http://localhost:8000 (documentación en /docs).

## Uso

1. En la pestaña **Calendario**, ingresa el marcador real de cada partido.
2. Las **tablas**, **terceros** y **16avos** se recalculan solos.
3. En **Bracket KO** ingresas las eliminatorias; el ganador avanza solo.
4. En **Predicciones** ves el pronóstico de cada partido con estadísticas de goles.

Todo se guarda en `resultados.json` y persiste al reiniciar.

## Endpoints principales

| Endpoint               | Qué hace                                    |
|------------------------|---------------------------------------------|
| `/api/calendar`        | 72 partidos de grupos con fecha y sede      |
| `/api/all-predictions` | Predicción + stats de goles de cada partido |
| `/api/group-standings` | Las 12 tablas de grupos                     |
| `/api/best-thirds`     | Tabla de mejores terceros                   |
| `/api/bracket`         | Bracket eliminatorio completo               |
| `/api/update-result`   | Registrar resultado de grupo                |
| `/api/ko-result`       | Registrar resultado de eliminatoria         |
| `/api/ranking`         | Ranking Elo actual                          |
| `/docs`                | Documentación interactiva (Swagger)         |

## El motor de predicción

`prediction.py` implementa **Dixon-Coles (1997) + Elo**, el método estándar de
los predictores estadísticos de fútbol:

- **Elo**: rating de fuerza por selección. Sube al ganar, baja al perder; la
  magnitud depende del rival y de la diferencia de goles.
- **Dixon-Coles**: convierte la diferencia de fuerza en goles esperados (λ) y usa
  Poisson para la probabilidad de cada marcador, con corrección para los
  resultados bajos (0-0, 1-0, 1-1).

De la matriz de marcadores se derivan: Over/Under 1.5/2.5/3.5, Ambos Marcan,
Clean Sheets y los marcadores más probables.

## Stack

- **Backend**: Python, FastAPI, uvicorn
- **Frontend**: HTML/CSS/JS vanilla, flag-icons
- **Persistencia**: JSON en disco

## Notas

- Los parámetros del modelo (`ELO_K`, `RHO`, goles base) están al inicio de
  `prediction.py` para calibrarlos.
- El proyecto funciona en modo manual (ingresas resultados) sin necesidad de
  API externa de pago.