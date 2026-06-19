# Mundial 2026 Predictor

Modelo probabilistico experimental para estimar probabilidades de partidos del Mundial 2026.

Este repositorio es el pipeline tecnico separado del sitio `edgarsierra.com`. Genera datos derivados y JSON validados que la Fase 2 podra copiar, importar o sincronizar hacia `edgarsierra.com/mundial-2026`.

## Que predice

- Probabilidad de victoria del equipo A
- Probabilidad de empate
- Probabilidad de victoria del equipo B
- Goles esperados
- Marcadores mas probables

## Que NO hace todavia

- No predice campeon
- No simula todo el torneo
- No calcula probabilidades de avanzar por grupo
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
python scripts/03_export_outputs.py
```

## Outputs

```txt
data/outputs/predictions_today.json
data/outputs/team_power_ranking.json
data/outputs/model_metadata.json
```

Estos JSON son el contrato de entrega hacia `edgarsierra.com`. La integracion con Astro se define en Fase 2; este repositorio solo genera y valida los archivos.

## Tests

```bash
pytest
```

## Principio

Este modelo no adivina el futuro. Estima probabilidades y se audita publicamente.
