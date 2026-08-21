# Auditoría de chunks huérfanos — antes de expandir la KB (POL-11, subtarea 11.1)

**Propósito.** El discovery encontró que 13 de 52 chunks (25%) nunca aparecían en top-3 y recomendó un bloqueo blando: entender por qué antes de crecer a 60-100 artículos ([findings.md §2](discovery/findings.md)). Esta auditoría ejecuta ese diagnóstico con el eval framework de POL-10 como instrumento.

**Fecha:** 2026-08-21 · **Instrumento:** `src/eval/` config v1 (dense-only), corpus v1 (47 queries), índice del eval (52 chunks, hash `a0cd72dab0ef`) · **Costo:** USD 0 (cache caliente).

**Veredicto en una línea:** el "25% invisible" era **artefacto de medición**, no defecto de la KB — pero la auditoría destapó algo peor y accionable: el índice sobre el que se midió el baseline **pierde 18 secciones reales y contiene 2 chunks de puro boilerplate**, y eso degrada el baseline de forma medible.

---

## 1. Inventario canónico de huérfanos

Un chunk es huérfano si no aparece en **top-5 de ninguna** query del corpus. `kb_coverage_pct` = chunks vistos / chunks del índice (métrica de vigilancia de ADR-0004).

| Subconjunto de corpus | K | kb_coverage_pct | Huérfanos |
|---|---|---|---|
| discovery (30q) — **réplica del discovery** | 3 | **75.0 %** | **13** |
| discovery (30q) | 5 | 88.5 % | 6 |
| solo manuales (17q) | 5 | 80.8 % | 10 |
| **orgánico** (41q: todo menos las 6 dirigidas) | 5 | **96.2 %** | **2** |
| **corpus completo (47q)** | 5 | **98.1 %** | **1** |

**El instrumento está validado.** Replicando la medición exacta del discovery (30 queries, top-3) el eval devuelve 75.0 % y **los mismos 13 chunks** — con los ids canónicos, que corrigen dos typos de transcripción de `findings.md` §2 (`you're-entitled-to`, no `you-are-entitled`; `spam-/-promotions`, no `spam/promotions`). La diferencia entre 25 % y 1,9 % de huérfanos es **puramente metodológica**: 30→47 queries y top-3→top-5, no un cambio en la KB.

**Cifra honesta: 96.2 %, no 98.1 %.** Seis queries del corpus (`man-02`..`man-05`, `man-09`, `amb-02`) las escribí en 10.2 apuntando *deliberadamente* a chunks huérfanos. Usar esa cobertura como prueba de que no hay huérfanos sería circular. La medida limpia excluye esas 6: **96.2 %, 2 huérfanos**. La diferencia (2 chunks) es exactamente lo que las queries dirigidas rescataron — y ese rescate es legítimo como decisión de corpus, no como evidencia de salud de la KB.

### Huérfanos vigentes

| Chunk | Corpus completo | Corpus orgánico |
|---|---|---|
| `connectors-roadmap::paid-add-on-connectors` | **huérfano** (mejor rank 7, score 0.497) | huérfano |
| `security-privacy::isolation-&-access-control` | visible (rank 3 en `man-04`) | huérfano |

---

## 2. Los 13 huérfanos del discovery: causa y decisión

Causas del criterio de 11.1: **(A)** sesgo del corpus · **(B)** texto genérico que ninguna query natural activa · **(C)** brecha de vocabulario usuario↔chunk.

| Chunk | Estado hoy (mejor rank · score · query) | Causa | Decisión |
|---|---|---|---|
| `billing-plans::starter` | rank 1 · 0.717 · `man-07` | **A** | Aceptar y vigilar. Rescatado por query natural de plan; el discovery no preguntaba por planes. |
| `billing-plans::enterprise` | rank 1 · 0.696 · `man-02` | **A** | Aceptar y vigilar. |
| `billing-plans::growth` | rank 2 · 0.630 · `man-07` | **A + B parcial** | Aceptar y vigilar **con alerta**: su rank 1 absoluto (0.477) lo obtiene en `man-14`, una query fuera de dominio ("plan de marketing") — el token "plan" lo hace mini-imán de queries ambiguas. Si en 11.5 sube su dominancia, especificar el texto. |
| `connectors-connect-hubspot::what-happens-next` | rank 4 · 0.717 · `en-01` | **B** | Reescribir en 11.2/11.3: título deíctico ("what happens next") sin contenido propio recuperable; solo entra arrastrado por el artículo. Debe nombrar su tema (sync, latencia de datos). |
| `connectors-reauthorize-expired::how-to-reconnect` | rank 2 · 0.589 · `man-10` | **C + defecto de índice** | **Prioridad**: es el chunk esperado de 4 queries del corpus y las 2 que fallan Recall@5 (`typo-03`, `typo-04`) lo tienen fuera del top-5 — parcialmente porque el chunk-basura `::still-stuck?` del mismo artículo le roba el puesto (§3). Se resuelve al sanear el índice; sin vocabulario de jerga ("oauth", "token", "reautorizar") el gap persiste → candidato claro de BM25 (POL-7). |
| `connectors-roadmap::included-on-every-plan` | rank 2 · 0.624 · `man-03` | **A** | Aceptar y vigilar. |
| `connectors-roadmap::how-to-add-a-connector-you're-entitled-to` | rank 4 · 0.515 · `typo-02` | **B** | Reescribir: "a connector you're entitled to" es lenguaje de contrato, no del usuario; entra por proximidad al artículo, no por su tema. |
| `connectors-roadmap::paid-add-on-connectors` | **rank 7 · 0.497 · `es-03`** | **C, severa** | **Reescribir (el caso más duro).** Sigue huérfano *incluso con query dirigida*: `amb-02` ("does Polaris support TikTok Ads") no lo trae al top-5 aunque el chunk nombra TikTok Ads explícitamente. El embedding diluye los nombres propios de producto en prosa de pricing. Es el caso canónico de BM25 (POL-7) **y** de reescritura: los nombres de conector deben aparecer como entradas, no en una lista dentro de un párrafo. |
| `dashboards-build::prerequisites` | rank 4 · 0.607 · `es-07` | **A + B** | Aceptar y vigilar. Genérico ("prerequisites") pero se recupera por el cuerpo. |
| `reports-not-arriving::2.-check-your-spam-/-promotions-folder` | rank 1 · 0.597 · `man-12` | **A** | Aceptar y vigilar. Rescatado por query natural ES ("no llegan los correos"). |
| `reports-not-arriving::4.-check-data-freshness` | rank 1 · 0.601 · `ec-01` | **A** | Aceptar y vigilar. Ojo: su rank 1 lo obtiene en una query de código de error (`ec-01`) sin artículo — cuando POL-11 escriba `ER005`, este chunk debe cederle el puesto. Verificar en 11.5. |
| `security-privacy::data-in-transit-&-at-rest` | rank 1 · 0.741 · `man-04` | **A** | Aceptar y vigilar. El discovery simplemente no preguntaba por seguridad. |
| `security-privacy::isolation-&-access-control` | rank 3 · 0.671 · `man-04` | **A + C** | **Cubrir con query nueva en el corpus** (11.5): sigue huérfano en el corpus orgánico. Su vocabulario ("isolation", "multi-tenant") es de arquitectura; el usuario pregunta "¿otros clientes ven mis datos?". Agregar esa query — es cobertura real faltante, no maquillaje. |

**Resumen de decisiones:** 8 aceptar y vigilar (causa A, sesgo del corpus) · 4 reescribir (causa B/C) · 1 cubrir con query nueva.

**Conclusión sobre el bloqueo blando del discovery: se levanta.** La KB actual no es "25 % invisible": con un corpus representativo la cobertura es 96 %, y los huérfanos que quedan tienen causa identificada y dueño. La expansión de 11.2/11.3 puede proceder — con el checklist de §4 y con el saneamiento de §3 hecho o explícitamente diferido.

### Nota sobre el chunk imán (discovery §3)

`dashboards-not-loading::1.-check-your-internet-connection` sigue siendo el top-1 más frecuente: 4 veces, pero ahora sobre 47 queries. `chunk_dominance_top1_ratio` cae de **13.3 % → 8.5 %**, bajo el umbral de 10 % de ADR-0005. **Cuidado con leer eso como mejora**: el numerador no bajó (siguen siendo las mismas 4 queries genéricas), bajó el denominador. El imán no se arregló, se diluyó. La decisión de re-chunkear ese artículo sigue en pie para 11.3, y la métrica debe vigilarse en valor absoluto además de ratio.

---

## 3. Pérdida por el filtro `still stuck?` — es del instrumento, no de la KB

**Corrección de un hallazgo previo mío.** En `hallazgos.md` (10.2, #3) escribí que el filtro "se come la última sección real de varios artículos" y lo llamé "pérdida real de KB que POL-11 debe corregir". **Eso era incorrecto en su parte más importante**: la KB no pierde nada. Lo que pierde es el índice del *eval/discovery*.

| Objeto | Conteo | Estado |
|---|---|---|
| Artículos en `kb/` | 20 | — |
| Secciones H2 redactadas | **70** | íntegras |
| Índice de **producción** (`src/chunk_kb.py` → Mongo → `worker/kb_vectors.json`) | **90** = 70 secciones + 20 intros | **completo, cero pérdida** |
| Índice del **eval/discovery** (`src/eval/kb_index.py`) | **52** | **degradado** |

El chunker de producción strippea el footer del texto crudo *antes* de segmentar. El del discovery filtra por sección, así que descarta entera cualquier sección cuyo cuerpo contenga el footer — es decir, **la última sección de 18 de los 20 artículos**.

**Lo que el índice del eval no ve (18 secciones, todas con contenido real, 97–436 caracteres):**

`alerts-create::Tips` · `alerts-not-firing::4. Alert is paused or misconfigured` · `attribution-models::View your attribution` · `attribution-setup-utms::Step 3: Verify the connection` · `billing-change-plan::What happens after` · `billing-plans::How to check or upgrade your plan` · `connectors-connect-ga4::Troubleshooting` · `connectors-connect-hubspot::Troubleshooting` · `connectors-roadmap::Not sure which plan you're on?` · `connectors-sync-delays::What to do next` · `dashboards-build::Tips` · `dashboards-not-loading::5. Try a hard refresh` · `getting-started::5. Set up your north-star metric` · `northstar-define::Important` · `reports-schedule::Notes` · `security-privacy::Security concerns?` · `users-invite-roles::Key points` · `users-permission-denied::Role reference`

Ninguna está vacía. Varias son material de soporte de primera línea: los dos bloques de **Troubleshooting** de los conectores (436 y 364 caracteres, cubren "Authorization failed", "Property not showing", token OAuth expirado) y `users-permission-denied::Role reference`.

**Y al revés: 2 de los 52 chunks son puro boilerplate.** En los 2 artículos que ponen el footer bajo su propio `## Still stuck?`, ese heading se convirtió en chunk indexado:

| Chunk basura | Apariciones en top-5 | Peor caso |
|---|---|---|
| `reports-not-arriving::still-stuck?` | 7 | **top-1 en `man-13`** (0.690) |
| `connectors-reauthorize-expired::still-stuck?` | 4 | rank 2 en `es-09` (0.698) |

**Daño medido sobre el baseline:** 11 de 235 slots de contexto (4.7 %) y **11 de 47 queries (23 %) reciben un chunk que solo dice "contact support"**. Dos consecuencias trazables:

1. **Explica un fallo de answer_type**: en `man-13` el top-1 es un footer con score 0.690 — el umbral 0.50 no gatilla y el sistema respondería con falsa confianza sobre un "chunk" sin información.
2. **Explica parte de las fallas de Recall@5**: en `es-09` y `typo-04`, `connectors-reauthorize-expired::still-stuck?` ocupa un puesto del top-5 mientras la sección útil del mismo artículo (`how-to-reconnect`) queda en rank 4 o fuera. **El footer le roba el contexto a su propio artículo.**

**Decisión y alcance.** Sanear el índice del eval NO se hace en 11.1: toca la construcción del índice, y el scope freeze de esta subtarea lo prohíbe (además cambiaría el índice bajo un baseline recién publicado). Se propone así:

- **Dónde:** subtarea **11.4** (re-chunk + re-embed), que ya tiene mandato de tocar el pipeline, o un PR propio previo a 11.5 si POL-7 lo necesita antes.
- **Qué:** unificar el índice del eval con el criterio de producción (strippear el footer del texto crudo antes de segmentar) para recuperar las 18 secciones y eliminar los 2 chunks basura.
- **Consecuencia a aceptar explícitamente:** el baseline v1 publicado quedará medido sobre un índice distinto del posterior. Al sanear hay que **re-correr el baseline y re-etiquetar** las queries afectadas (`typo-03`, `typo-04`, `es-09`, `man-13`, y las que apunten a secciones recuperadas), documentando el cambio de versión del corpus. No es opcional: sin eso, los deltas de v2 comparan contra un índice que ya no existe.
- **Relación con la paridad JS/Python** (eval.md §4, diferida a POL-7): este saneamiento es el prerrequisito. Sin unificar el índice no hay paridad posible; con él, la brecha se reduce a los 20 chunks de intro.

---

## 4. Checklist anti-huérfano para 11.2 / 11.3

Reglas derivadas de la evidencia de §2, para que los artículos nuevos —incluido el catálogo de códigos `ER/PF/PL/RP/AL/DB/AG`— no nazcan huérfanos ni imanes.

**Encabezados (la causa B, "texto genérico", entra casi siempre por acá)**

1. **El H2 nombra su tema, no su posición en el documento.** Prohibidos como único texto del heading: `Tips`, `Notes`, `Important`, `Key points`, `What happens next`, `Prerequisites`, `Steps`, `Troubleshooting`. Reemplazar por el tema: "Troubleshooting GA4 authorization errors", "Report permissions and data freshness". Evidencia: `what-happens-next` y `how-to-add-a-connector-you're-entitled-to` solo entran arrastrados por el artículo.
2. **Nada de lenguaje de contrato.** "a connector you're entitled to" no es cómo pregunta nadie. Escribir como el usuario habla.

**Vocabulario (la causa C, "brecha usuario↔chunk")**

3. **Cada chunk contiene las palabras con que un usuario lo buscaría**, incluida la jerga: `OAuth`, `token`, `API key`, `reautorizar`, `rotar`, `SSO`, `expiró`. Evidencia: `how-to-reconnect` es el chunk correcto de 4 queries y las de jerga no lo alcanzan.
4. **Los nombres propios de producto van como entradas, no dentro de un párrafo.** Un chunk que menciona "TikTok Ads, Constant Contact y Klaviyo" en prosa de pricing no se recupera al preguntar por TikTok Ads (`paid-add-on-connectors`, huérfano incluso con query dirigida). Un conector o código por bloque, con el nombre en el heading.
5. **Códigos de error: el código exacto en el H2 y repetido en el cuerpo.** `## ER005 — Not synced with Google Ads`, y el token `ER005` otra vez en Symptom. El denso representa mal estos tokens (por eso son la apuesta de BM25/POL-7); repetirlos es lo único que da chance al retrieval denso mientras BM25 no exista.
6. **Escribir en el idioma del usuario objetivo y, si el tema es bilingüe, incluir el término en ambos** (ej. "reautorizar / reauthorize"): el corpus es 55 % ES y el baseline no muestra sesgo — no introducirlo ahora.

**Especificidad (evitar nuevos imanes)**

7. **Ningún chunk debe poder responder "cualquier problema".** El imán actual dice "check your internet connection… this might not be the issue" — texto que cuela en "help" y "no me funciona". Cada chunk debe declarar *para qué síntoma concreto* sirve, en su primera oración.
8. **Separar troubleshooting genérico de específico en artículos distintos**, para que el genérico no compita con todo.
9. **Sin footers boilerplate como sección propia.** Nunca un `## Still stuck?`: en el índice del eval eso produjo 2 chunks que solo dicen "contact support" y contaminan el 23 % de las queries. El cierre de soporte va como texto de cierre, no como heading.

**Verificación (obligatoria antes de cerrar 11.3)**

10. **Cada artículo nuevo llega con al menos una query al corpus**, escrita con el vocabulario del usuario y **no** copiada del texto del artículo (eso mide el eco, no el retrieval).
11. **Correr el eval después de redactar y revisar tres cosas**: `kb_coverage_pct` no baja del 96 % orgánico; ningún chunk nuevo supera 10 % de dominancia top-1 (y vigilar el conteo absoluto, no solo el ratio); Recall@5/MRR no degradan en las queries donde v1 acertaba (regla de no-regresión, eval.md §7).
12. **Un artículo cuyo chunk no aparece en top-5 de su propia query se reescribe, no se acepta.** Nace huérfano.

---

## 5. Cifras rancias de conteo de chunks

El hallazgo #4 del 21-ago pedía corregir "89 → 52" en cuatro documentos. **La corrección correcta es 89 → 90, no 52**, y va con la distinción de índices explícita: los cuatro lugares describen el índice de **producción** (Mongo `polaris.kb_chunks`, vectores bundled en el Worker, `src/vectorstore.py`), que hoy tiene **90** chunks —re-exportados en el commit `c78eeb8`—, no el índice de 52 del eval. Escribir 52 ahí habría introducido un error factual nuevo. Detalle y justificación del desvío en `bitacora/hallazgos.md` (11.1, #4).

---

## 6. Reproducir esta auditoría

```bash
uv run python -m src.eval.coverage            # kb_coverage_pct, huérfanos, imanes, chunks sin indexar
uv run python -m src.eval.coverage --corpus-subset organico --top-k 5
```

El módulo `src/eval/coverage.py` deja la medición reproducible para 11.5 (donde `kb_coverage_pct` debe recalcularse contra el 96.2 % orgánico de este documento) y para la vigilancia continua de ADR-0004/0005.
