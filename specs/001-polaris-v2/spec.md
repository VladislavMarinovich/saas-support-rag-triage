<!-- Spec funcional Polaris v2 — POL-3. Estado: DRAFT. Fuente de verdad: este archivo. Confluence espeja al cierre de POL-3. -->

# Polaris v2 — Especificación funcional

**Versión:** DRAFT (POL-3 en curso)
**Autor:** Vladislav Marinovich · Marinovich Consulting SAS
**Refs:** Constitution v1.0.0 (`.specify/memory/constitution.md`), Epic POL-1.

Este documento describe QUÉ hace Polaris v2 y por qué. No describe cómo — eso vive en el Plan técnico (POL-4).

## 1. Contexto y problema

Polaris v1 es un demo funcional de RAG grounded sobre KB de producto, corriendo en Cloudflare Workers con Vertex AI (embeddings `text-embedding-005` y generación `gemini-2.5-flash-lite`). Responde preguntas de soporte citando fuentes de la KB actual (20 artículos, 89 chunks estructurales por sección H2) y clasifica el ticket antes de generar respuesta.

Cuatro carencias limitan a v1 como flagship de portafolio y como producto real:

**Sin memoria de queries repetidas.** Cada request paga la cadena completa de embed + retrieval + generación, incluso cuando la misma pregunta (o su reformulación) llegó minutos antes. En soporte SaaS, la proporción de queries duplicadas con distinto fraseo es sustancial y se está pagando cada una desde cero.

**Retrieval solo denso.** v1 recupera por similitud semántica únicamente. Las preguntas de usuario tienen errores tipográficos, jerga de producto y nombres exactos de features que un índice denso puro representa peor que un índice léxico. No hay fallback ni fusión.

**Cero observabilidad estructurada.** No se registra costo por request, latencia por componente, intent detectado, chunks recuperados ni cache hit/miss. Sin ese sustrato, cualquier discusión sobre "¿mejoró?" es opinión, no dato — lo que contradice Principio XII (eval-driven).

**Multilingual por accidente.** El modelo de embeddings soporta múltiples idiomas de forma nativa, pero el sistema no lo trata como caso de primera clase: la KB, el prompt y la cadena asumen tácitamente el mismo idioma en query y contenido. No hay contrato explícito ni verificación.

v2 aborda estas cuatro carencias como un solo ciclo cerrado — canonicalización + cache antes de compute, retrieval híbrido, telemetría de primera clase, y multilingual explícito — con un eval framework que respalda cada afirmación de mejora con números contra un baseline.

## 2. Usuarios y jobs-to-be-done

_A completar en commit siguiente._

## 3. Alcance funcional v2

_A completar en commit siguiente._

## 4. Criterios de aceptación

_A completar en commit siguiente._

## 5. Fuera de alcance (v2.1+)

_A completar en commit siguiente._

## 6. Métricas post-launch

_A completar en commit siguiente._

## 7. Riesgos y mitigaciones

_A completar en commit siguiente._
