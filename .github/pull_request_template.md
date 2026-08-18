## Qué hace este PR

<!-- 1-3 líneas describiendo el cambio -->

## Issue de Jira

<!-- Ej: [POL-6](https://marinovich-consulting.atlassian.net/browse/POL-6) -->

## Principios de la Constitution que aplica

<!-- Ej: Cumple VI (Cache antes de compute), IV (Cost cap), X (Latency SLO) -->

## Cambios incluidos

- <!-- archivo/módulo modificado: qué cambió y por qué -->

## Cómo validar

1. <!-- paso 1 -->
2. <!-- paso 2 -->

## Eval framework (Principio XII)

<!-- Comparación cuantitativa vs baseline. Si el cambio no toca retrieval/prompt/modelo, indicar "N/A". -->

- Baseline: recall@5 = X · precision@5 = Y · MRR = Z
- Este PR: recall@5 = X' · precision@5 = Y' · MRR = Z'
- Delta: +N pp / -N pp

## Checklist

- [ ] Criterios de aceptación del issue cubiertos
- [ ] Sin credenciales ni datos sensibles en el diff
- [ ] Tests pasan (o no aplica)
- [ ] Docs actualizados (o no aplica)
- [ ] Confluence sincronizado (o no aplica)
- [ ] Eval framework corrido (o marcado N/A)
- [ ] Sin regresión de p95 latencia (Principio X)
