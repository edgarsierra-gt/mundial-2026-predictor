# Data Dictionary

## Processed datasets

- `teams.csv`: catalogo maestro de selecciones, codigos, slugs y grupo.
- `matches_current.csv`: una fila por partido del Mundial actual.
- `team_match_current.csv`: una fila por seleccion-partido del Mundial actual.
- `team_history.csv`: ultimos 20 partidos por seleccion, normalizados.
- `team_features.csv`: features agregadas de ataque, defensa, forma y calidad de datos.
- `upcoming_matches.csv`: partidos programados que se pueden modelar.
- `predictions_frozen.csv`: predicciones pre-partido versionadas.
- `tournament_schedule.csv`: calendario estructurado de partidos completados y programados.
- `group_standings_current.csv`: tabla actual por grupo con puntos, goles y ranking.
- `match_results_real.csv`: resultados reales normalizados para auditoria posterior.

## Public JSON contract

- `predictions_today.json`: predicciones 1X2, goles esperados y top marcadores.
- `team_power_ranking.json`: ranking inicial de fuerza, no probabilidad de campeon.
- `group_probabilities.json`: probabilidad de ganar grupo, quedar segundo, clasificar como tercero, avanzar o quedar eliminado.
- `round_probabilities.json`: probabilidad de alcanzar R32, R16, cuartos, semifinal, final y campeonato.
- `champion_odds.json`: ranking experimental de probabilidad de campeon bajo bracket aproximado.
- `tournament_snapshot.json`: snapshot tecnico de estado actual y alcance de simulacion.
- `model_metadata.json`: version, parametros, fuentes y limitaciones.
