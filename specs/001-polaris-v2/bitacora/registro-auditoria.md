# Registro de auditoría — Polaris v2

> ✍️ **Escribe: el AUDITOR adversarial** (sesión aparte y renovada). El orquestador y los ejecutores **no editan este archivo** — su registro es [`tablero.md`](tablero.md) y [`hallazgos.md`](hallazgos.md). Un escritor por archivo (Constitución v1.1.0).

Veredictos de las auditorías adversariales formales de cada Historia (subtareas 6.9, 7.8, 8.11, 9.10, 10.10, 11.6 de [`tasks.md`](../tasks.md)). El orquestador hace la **primera pasada**; el veredicto que habilita el merge lo da el auditor independiente — quien escribió el spec no juzga su propio spec.

**Formato de entrada:** `## [fecha] POL-X.Y — veredicto`, seguido de: qué se verificó **midiendo** (no leyendo), críticos abiertos, menores, y veredicto explícito (aprobado / aprobado con reservas / rechazado con motivo).

**Regla del auditor:** verificar reproduciendo la medición, no aceptando la prosa del ejecutor ni la del orquestador. Un hallazgo sin evidencia numérica o sin diff no es un hallazgo.

---

## Auditorías pendientes

| Subtarea | Historia | Alcance | Estado |
|---|---|---|---|
| **11.6** | POL-11 | PR completo de KB expansion: 11.1 → 11.5 (audit de huérfanos, spec, 55 artículos, saneamiento del índice, re-estampado del baseline) | ⧗ pendiente — se despacha al cerrar 11.5 |

**Nota histórica honesta:** POL-10.A se mergeó (PR #6) con **solo la primera pasada del orquestador**, sin auditoría independiente. La regla de auditor separado se acordó el 21-ago, después de ese merge, y se elevó a norma constitucional el 24-ago (v1.1.0). El baseline que produjo esa ventana se re-estampa en 11.5 y **entra en el alcance de la auditoría 11.6** — así el instrumento de medición del proyecto termina con veredicto independiente.
