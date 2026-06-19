# Mundial 2026 Predictor

Modelo probabilistico experimental para estimar probabilidades de partidos del Mundial 2026.

Este repositorio es el pipeline tecnico separado del sitio `edgarsierra.com`. Genera datos derivados y JSON validados que la Fase 2 podra copiar, importar o sincronizar hacia `edgarsierra.com/mundial-2026`.

## Que predice

- Probabilidad de victoria del equipo A
- Probabilidad de empate
- Probabilidad de victoria del equipo B
- Goles esperados
- Marcadores mas probables
- Probabilidad de avanzar desde fase de grupos
- Probabilidad de llegar a rondas posteriores
- Probabilidad experimental de campeon

## Que NO hace todavia

- No implementa todavia el bracket oficial completo de FIFA
- No automatiza resultados reales desde fuentes externas
- No incorpora lesiones automaticamente
- No garantiza marcador exacto
- No usa cuotas de apuestas

## Insumos

Copiar los Excel crudos a `data/raw/`:

```txt
data/raw/mundial_fifa_2026_partidos_hasta_18_jun_2026_estadisticas.xlsx
data/raw/Estadisticas_ultimos20_selecciones_Mundial2026_v5_48selecciones_FINAL.xlsx
```

Los archivos crudos no se publican en el frontend. Solo se publican derivados trazables.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Pipeline

```bash
python scripts/01_build_datasets.py
python scripts/02_generate_predictions.py
python scripts/03_run_simulation.py
python scripts/03_export_outputs.py
```

## Outputs

```txt
data/outputs/predictions_today.json
data/outputs/team_power_ranking.json
data/outputs/group_probabilities.json
data/outputs/round_probabilities.json
data/outputs/champion_odds.json
data/outputs/tournament_snapshot.json
data/outputs/model_metadata.json
```

Estos JSON son el contrato de entrega hacia `edgarsierra.com`. La integracion con Astro se define en Fase 2; este repositorio solo genera y valida los archivos.

## Simulacion de grupos

La simulacion de Fase 3 usa resultados reales ya cargados y predicciones pendientes para estimar escenarios de clasificacion por grupo. En esta version:

- clasifican 1. y 2. de cada grupo;
- clasifican los 8 mejores terceros;
- los desempates usan puntos, diferencia de goles, goles a favor y fallback estable por `team_id`;
- las eliminatorias usan un bracket aproximado con siembra estable;
- `champion_odds.json` es experimental y no debe leerse como certeza ni como cuota de apuestas.

## Tests

```bash
pytest
```

## Principio

Este modelo no adivina el futuro. Estima probabilidades y se audita publicamente.
