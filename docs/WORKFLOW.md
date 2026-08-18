# Flujo de trabajo Git — Polaris

Este documento define cómo se trabaja en el repo `saas-support-rag-triage`. Es de lectura obligatoria antes de abrir el primer PR.

Modelo elegido: **GitHub Flow** (no Git Flow clásico). Simple, adecuado para 1-3 devs, escalable a más si llega el momento.

Ver también: `.specify/memory/constitution.md` (Principio VII — PHVA riguroso).

## 1. Ramas

Hay una sola rama de larga vida: `main`. Todo lo demás son ramas cortas creadas desde `main` y borradas después del merge.

### Nomenclatura obligatoria

```
feature/POL-XX-descripcion-corta      # nueva funcionalidad
fix/POL-XX-descripcion-corta          # corrección de bug
docs/POL-XX-descripcion-corta         # solo documentación
refactor/POL-XX-descripcion-corta     # refactor sin cambio funcional
chore/POL-XX-descripcion-corta        # tareas de mantenimiento (deps, config)
```

Reglas:

- Siempre incluir el issue key de Jira (`POL-XX`) en el nombre de la rama.
- Usar `kebab-case`, sin mayúsculas, sin espacios.
- Máximo 60 caracteres después del prefijo.
- Crear siempre desde `main` actualizada (`git pull` antes).
- Nunca ramificar desde otra rama feature (excepto para hotfix explícito).

Ejemplos correctos:

```
feature/POL-6-canonicalize-cache
feature/POL-7-hybrid-retriever
fix/POL-8-bq-insert-timeout
docs/POL-2-constitution-v1
chore/POL-10-eval-fixtures
```

## 2. Commits

Cada commit debe:

- Tener un solo propósito (una función, una config, un archivo).
- Estar en español (Constitution Principio XIII).
- Usar Conventional Commits en el título: `chore:`, `feat(scope):`, `fix(scope):`, `docs:`, `refactor(scope):`, `test:`.
- Incluir `Refs POL-XX` en el body al final.

Ejemplos correctos:

```
feat(worker): canonicalize query con Gemini Flash Lite

Implementa canonicalización pre-cache para maximizar hit rate.
Prompt tight (< 20 tokens output) para minimizar costo.

Refs POL-6
```

```
docs(constitution): 14 principios v1.0.0

Base filosófica del ciclo v2. Sync Impact Report incluido.

Refs POL-2
```

Ejemplos incorrectos:

```
fix stuff
wip
various changes
[POL-6] added cache
```

## 3. Push incremental

- Hacer push después de cada grupo lógico de commits, no solo al final.
- Nunca dejar trabajo local sin push por más de un día.
- `git push origin feature/POL-XX-desc` — siempre con nombre explícito de rama.

## 4. Apertura de PR

Un PR se abre cuando el trabajo está listo para revisión.

### Título del PR

```
[POL-XX] Descripción clara de qué hace este PR
```

### Descripción del PR

Usar la plantilla `.github/pull_request_template.md`.

## 5. Merge strategy

**Squash and merge.**

- Mantiene la historia de `main` lineal y limpia (1 commit por PR).
- Preserva los commits granulares dentro de la rama para debugging.
- Convención del squash title: mismo formato Conventional Commits.

Ejemplo del commit final en `main` tras squash:

```
feat(retrieval): hybrid BM25 + semantic + RRF (#12)

* build BM25 stemmer-less index desde chunks del KB
* export a worker/bm25_index.json bundled
* worker/hybrid_search.js con RRF k=60
* integración en flow principal

Refs POL-7
```

## 6. Después del merge

1. La rama local y remota se eliminan automáticamente (config del repo o manual).
2. El issue de Jira se transiciona a **Verificar** (o **Actuar** si el deploy también terminó).
3. Worklog en Jira registra las horas del bloque.
4. Si el PR afecta docs operativas, verificar que Confluence refleja el estado.

## 7. Protección de `main`

GitHub Free no soporta branch protection en repos privados. La convención es la ley:

- No push directo a `main`.
- Squash es el único merge permitido.
- La rama fuente se borra después del merge.

Cuando el proyecto tenga presupuesto para GitHub Pro ($4/mes), se activarán reglas técnicas de protección.

## 8. Ciclo PHVA aplicado al PR

Ver Constitution Principio VII.

- **Planear**: issue Jira creado + rama nombrada + spec (si aplica).
- **Hacer**: commits granulares en la rama.
- **Verificar**: tests + preview local + code review + **correr eval framework (Principio XII)**.
- **Actuar**: merge del PR + Jira transicionado + worklog + Confluence espejo si aplica.

## 9. Trazabilidad — checklist antes de cerrar cualquier issue

- [ ] Existió una rama con el patrón `<tipo>/POL-XX-...`.
- [ ] Los commits llevan `Refs POL-XX` en el body.
- [ ] El PR fue abierto, revisado, mergeado (no push directo).
- [ ] El PR referencia el issue de Jira en la descripción.
- [ ] Eval framework corrió y confirma que no hay regresión (para cambios de retrieval/prompt/modelo).
- [ ] El issue en Jira quedó en el estado correcto (Verificar o Actuar).

## 10. Contacto

Dudas o excepciones: Vlad Marinovich · <ops@marinovich.co>.
