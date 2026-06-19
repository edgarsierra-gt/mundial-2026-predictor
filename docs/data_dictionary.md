# Data Dictionary

## Processed datasets

- `teams.csv`: catalogo maestro de selecciones, codigos, slugs y grupo.
- `matches_current.csv`: una fila por partido del Mundial actual.
- `team_match_current.csv`: una fila por seleccion-partido del Mundial actual.
- `team_history.csv`: ultimos 20 partidos por seleccion, normalizados.
- `team_features.csv`: features agregadas de ataque, defensa, forma y calidad de datos.
- `upcoming_matches.csv`: partidos programados que se pueden modelar.
- `predictions_frozen.csv`: predicciones pre-partido versionadas.

## Public JSON contract

- `predictions_today.json`: predicciones 1X2, goles esperados y top marcadores.
- `team_power_ranking.json`: ranking inicial de fuerza, no probabilidad de campeon.
- `model_metadata.json`: version, parametros, fuentes y limitaciones.

