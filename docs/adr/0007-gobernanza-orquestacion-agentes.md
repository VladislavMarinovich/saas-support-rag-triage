# ADR-0007 — Gobernanza de orquestación de agentes y defensa de drift

- **Estado:** Aceptado
- **Fecha:** 2026-08-24
- **Owner:** Vladislav Marinovich · Marinovich Consulting SAS
- **Refs:** [Constitution](../../.specify/memory/constitution.md) — este ADR habilita la enmienda v1.0.0 → v1.1.0 (requisito de su sección "Cambios a la Constitución"). Jira POL-18. Método: MC SFE (Marinovich Consulting Spec-First Engineering); precedente en `fsp-consola` constitución v1.3.0 / CSOS-47.

## Contexto

Polaris v2 se construye con una tripulación de agentes: un orquestador que especifica y despacha, ejecutores efímeros que implementan, y un auditor. Ese reparto funcionó de hecho durante POL-10 y POL-11, pero **nunca tuvo rango de norma**: vivía en las convenciones de `tasks.md` y en la memoria del orquestador. La Constitución v1.0.0 no menciona orquestador, ejecutor ni auditor.

Dos hechos verificables obligan a formalizarlo.

**Hecho 1 — el handoff en memoria falló.** El 24-ago, al retomar el proyecto, la pregunta "¿por dónde quedamos?" se respondió desde la memoria del orquestador, no desde el repo. Cualquier sesión nueva sin esa memoria habría quedado ciega. El repo tenía los eventos (`timeline.jsonl`) y los aprendizajes (`hallazgos.md`), pero ningún artefacto decía **qué sigue**.

**Hecho 2 — la falta de un gate de radio de impacto costó una regresión medida.** En POL-11 se expandió la KB de 20 a 75 artículos (subtarea 11.3). Eso cambió el índice de chunks. El corpus de eval **referencia ese índice** por etiquetas (`expected_chunks`). Nadie enumeró qué apuntaba al índice antes de tocarlo, y el resultado fue **Recall@5 de 0.92 → 0.86** sobre las queries del baseline.

Lo agravante: `docs/features/eval.md` §2 **ya exigía** revisar las etiquetas al expandir la KB. La regla estaba escrita y se saltó. Es la confirmación empírica de que **un checklist saltable es una sugerencia, no un guardarraíl**: para atar a un agente autónomo, la verificación debe estar mecanizada.

## Decisión

Elevar a rango constitucional el modelo de gobernanza de MC SFE, adaptado a Polaris:

1. **Orquestación con separación de roles.** El orquestador no escribe código de implementación; prepara el prompt del ejecutor con guardarraíles y audita el resultado. La auditoría adversarial formal la hace un auditor renovado en sesión aparte. Un solo escritor por rama y **un solo escritor por archivo**.

2. **Autonomía en el medio, gate en las fronteras.** Autonomía plena del ejecutor en exploración e implementación. Gate duro con firma de Vlad en las fronteras de la verdad compartida. Para Polaris las fronteras son tres, y se declaran explícitamente en la Constitución: **(a)** re-estampar el baseline, **(b)** activar `LIVE=true` en cualquier entorno desplegado, **(c)** merge a `main`.

3. **Defensa de drift en dos cadencias.** Tier 1 por cambio (radio de impacto: enumerar qué referencia lo que se toca) y Tier 2 por hito (barrido global al cerrar una Historia). Tier 1 caza drift local; Tier 2 caza el drift emergente que ningún chequeo local ve.

4. **Tablero de orquestación en el repo** como punto de rehidratación: qué pasó, veredicto de auditoría, qué sigue.

## Consecuencias

**Positivas.** El handoff deja de depender de la memoria de una sesión. Las fronteras quedan nombradas, así que un ejecutor no puede cruzarlas por omisión — y la que tenemos enfrente (11.5 re-estampa el baseline) ya cae bajo firma. Y Polaris se vuelve la **segunda aplicación real de MC SFE**, lo que sostiene el earn-then-codify con dos batallas en vez de una.

**Aporte de vuelta al método.** Polaris instancia el Tier 1 de forma **métrica**, no estructural: la regla de no-regresión contra baseline (`eval.md` §7) es un detector de drift cuantitativo, mientras el Tier 1 de Consola es estructural (estampas de versión, cobertura enum→emisor). Mismo pilar, mecanismo distinto — evidencia de que la cadencia generaliza y su implementación depende del dominio.

Además, el guard `post_baseline` del runner de eval es "mecanizado, no acordate" ya funcionando: **se niega a correr** antes que emitir un número que mezcle poblaciones. Bloqueó de verdad la ejecución el 21-ago. Nació antes de esta enmienda, lo que refuerza que el patrón emerge del problema y no de la teoría.

**Costos y límites.** El gate en fronteras introduce esperas por firma humana — es el precio deliberado. Tier 2 es caro, por eso va por hito y no por cambio. Y el límite honesto se hereda de Consola: **Tier 1 caza rezago, no mentira** (un ejecutor que declara "verificado" sin verificar pasa el chequeo); la barrera final sigue siendo evidencia verificable más auditoría adversarial independiente.

## Alternativas consideradas

**Dejarlo como convención en `tasks.md`.** Rechazada: es lo que había, y falló dos veces documentadamente. Una convención no obliga a un ejecutor efímero que no la leyó.

**Copiar la constitución de `fsp-consola` completa.** Rechazada: su sección "Reglas de Dominio Invariantes" es de Consola (rollups, cierre, External_ID) y no aplica. Se transfieren los pilares universales de gobernanza, no el dominio.

**Mecanizar Tier 1 con un hook pre-commit ahora.** Diferida, no rechazada: es la forma correcta (Consola la construyó como `tests/test_anti_drift.py`), pero Polaris ya tiene un Tier 1 métrico vivo en el eval y el hook exigiría su propia subtarea con diseño. Queda declarado como deuda explícita con dueño: se evalúa al cerrar POL-11.
