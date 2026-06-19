# Methodology Notes

Fase 1 implementa un modelo base trazable:

1. Normaliza selecciones con `team_id` estable.
2. Calcula forma reciente desde los ultimos 20 partidos.
3. Aplica ponderacion por recencia y tipo de partido.
4. Deriva indices de ataque y defensa.
5. Convierte lambdas de goles esperados en matriz de marcadores Poisson.
6. Agrega probabilidades 1X2 y top marcadores.
7. Congela predicciones con `model_version`, timestamp y hash de inputs.

Fuera de alcance:

- Probabilidades de campeon.
- Probabilidades de avanzar por grupo.
- Simulacion Monte Carlo.
- API publica.
- Integracion directa con Astro.

