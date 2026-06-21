# Mundial 2026 Predictor

Pipeline probabilístico para estimar partidos, simular escenarios y auditar predicciones del Mundial 2026.

Este repositorio alimenta el [Laboratorio Mundial 2026](https://edgarsierra.com/mundial-2026) en `edgarsierra.com`. El sitio no recalcula el modelo: consume copias versionadas de los JSON generados aquí.

## Qué hace

- Genera probabilidades 1X2 por partido.
- Estima goles esperados para cada selección.
- Calcula marcadores más probables desde una matriz Poisson.
- Simula fase de grupos y caminos por rondas.
- Exporta outputs JSON para el frontend.
- Audita predicciones congeladas contra resultados reales.
- Produce métricas como accuracy 1X2, Brier score, log loss y error de goles.

## Qué no hace

- No garantiza marcadores exactos.
- No usa cuotas de apuestas.
- No pretende ser una verdad absoluta.
- No incorpora lesiones o alineaciones automáticamente.
- No oculta errores del modelo.
- No publica los Excel crudos en el frontend.

## Arquitectura

```txt
data/raw/          Excel y documentos fuente locales
data/processed/    CSV derivados y trazables
data/frozen/       predicciones congeladas para auditoría
data/outputs/      contrato JSON consumido por edgarsierra.com
src/               lógica del pipeline
scripts/           comandos operativos
tests/             pruebas unitarias y validaciones
```

Los archivos crudos viven en `data/raw/` y no deben publicarse. El sitio solo consume outputs derivados y versionados.

## Insumos

Copiar los Excel crudos a:

```txt
data/raw/mundial_fifa_2026_partidos_hasta_18_jun_2026_estadisticas.xlsx
data/raw/Estadisticas_ultimos20_selecciones_Mundial2026_v5_48selecciones_FINAL.xlsx
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Pipeline

Ejecutar paso por paso:

```bash
python scripts/01_build_datasets.py
python scripts/02_generate_predictions.py
python scripts/03_run_simulation.py
python scripts/04_audit_results.py
python scripts/03_export_outputs.py
```

O correr todo en orden:

```bash
python scripts/update_all.py
```

En GitHub Actions, donde los Excel crudos no están versionados, se usa:

```bash
python scripts/update_all.py --skip-build
```

## Cargar resultados nuevos (uso diario)

Cuando un partido termina, se agrega una fila a `data/raw/resultados_nuevos.csv` (editable con Excel, guardando como CSV):

```txt
date,team_a_id,team_b_id,team_a_goals,team_b_goals,...,source_url
2026-06-19,USA,AUS,1,2,...,https://...
```

Columnas obligatorias: `date`, `team_a_id`, `team_b_id`, `team_a_goals`, `team_b_goals`. El resto (posesión, remates, xG, formaciones, fuente) es opcional; si se deja en blanco, el partido se ingiere igual, solo sin esas métricas.

Al correr `python scripts/update_all.py --skip-build` (o solo `python scripts/00_ingest_results.py`), el pipeline:

1. busca cada fila contra `data/processed/upcoming_matches.csv` por fecha y equipos, sin importar el orden en que se escriban;
2. mueve el partido a `data/processed/matches_current.csv` preservando la orientación `team_a`/`team_b` original, la misma que ya tiene su predicción congelada;
3. lo quita de `upcoming_matches.csv`, por lo que deja de aparecer como partido de hoy/próximo en `predictions_today.json`;
4. recalcula standings, simulación y auditoría usando el resultado real ya cargado;
5. deja en `resultados_nuevos.csv` únicamente las filas que no pudo emparejar, para corregirlas y volver a correr.

No es necesario editar a mano `group_standings_current.csv`, `match_results_real.csv` ni `tournament_schedule.csv`: se regeneran siempre a partir de `matches_current.csv`. Cada partido ingerido queda además registrado en `data/processed/results_ingest_log.csv` con fecha de ingesta.

## Outputs

```txt
data/outputs/predictions_today.json
data/outputs/team_power_ranking.json
data/outputs/group_probabilities.json
data/outputs/round_probabilities.json
data/outputs/champion_odds.json
data/outputs/model_audit.json
data/outputs/model_calibration.json
data/outputs/tournament_snapshot.json
data/outputs/model_metadata.json
```

Estos JSON son el contrato de entrega hacia `edgarsierra.com`. Por ahora la sincronización hacia el sitio es manual.

## Simulación

La simulación combina resultados reales cargados y predicciones pendientes para estimar escenarios del torneo. En esta versión:

- clasifican 1. y 2. de cada grupo;
- clasifican los 8 mejores terceros;
- los desempates usan puntos, diferencia de goles, goles a favor y fallback estable por `team_id`;
- las eliminatorias usan un bracket aproximado con siembra estable.

## Nota sobre `champion_odds.json`

`champion_odds.json` es experimental.

No debe leerse como ranking definitivo de campeón, cuota de apuestas ni promesa de título. La primera versión mostró sensibilidad al bracket aproximado y a la fuerza inicial aprendida por el modelo base.

La v2.0 pendiente debe incorporar un prior estructural externo, como ranking FIFA, Elo o power rankings públicos, para anclar mejor la fuerza global de selecciones antes de simular campeón.

## Auditoría

La auditoría cruza predicciones congeladas con resultados reales verificados. Si todavía no hay cruce entre ambos archivos, los JSON se exportan con `matches_audited = 0` y métricas nulas.

Métricas soportadas:

- accuracy 1X2;
- Brier score;
- log loss;
- hit rate de marcador exacto;
- sesgo y error absoluto de goles.

## Automatización

`.github/workflows/update-manual.yml` corre con botón (`workflow_dispatch`) y también automático dos veces al día (`cron: "0 6,18 * * *"`, hora UTC). En cada corrida:

1. corre `ruff` y `pytest`;
2. corre `python scripts/update_all.py --skip-build` (ingesta de `resultados_nuevos.csv` incluida);
3. commitea los cambios en `data/processed`, `data/outputs`, `data/frozen` y `data/raw/resultados_nuevos.csv` dentro de este mismo repo;
4. si existe el secret `SITE_SYNC_TOKEN`, abre un Pull Request en `edgarsierra-gt/edgarsierra.com` con los JSON nuevos copiados a `src/data/mundial-2026/`.

Sin `SITE_SYNC_TOKEN` configurado, el workflow sigue corriendo y commiteando normal en este repo; solo se omiten los pasos 4 en adelante.

### Configurar `SITE_SYNC_TOKEN` (una sola vez)

1. Crear un fine-grained personal access token en GitHub con acceso únicamente al repositorio `edgarsierra-gt/edgarsierra.com`, permisos `Contents: Read and write` y `Pull requests: Read and write`.
2. En `mundial-2026-predictor` → Settings → Secrets and variables → Actions, agregar un secret llamado `SITE_SYNC_TOKEN` con ese token.

Desde ahí, el flujo queda: llenar `resultados_nuevos.csv` → push (o esperar la corrida programada) → revisar y mergear el PR que aparece en `edgarsierra.com` → Vercel redeploya solo.

## Tests

```bash
python -m ruff check .
python -m pytest
```

## Relación con `edgarsierra.com`

Este repo es el backend técnico del laboratorio. `edgarsierra.com` es la capa pública que presenta predicciones, metodología, simulación y auditoría.

El flujo actual es:

```txt
mundial-2026-predictor/data/outputs/*.json
        ↓ copia manual versionada
edgarsierra.com/src/data/mundial-2026/*.json
        ↓ imports build-time en Astro
edgarsierra.com/mundial-2026
```

## Principio

Este modelo no adivina el futuro. Estima probabilidades y se audita públicamente.

## Autor

Edgar Sierra  
Head of BI & Data Science  
https://edgarsierra.com
