# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Vite + React + TypeScript + CSS de sistema de diseño propio (sin librerías de componentes pesadas), compilado y servido por FastAPI (`/`) y empaquetado mediante build multi-stage en Docker. Backend existente en Python + FastAPI + LangGraph + Google Gemini + SQLite.

## Users

- **Reclutadores de RRHH y Hiring Managers:** usan la aplicación en jornadas de escritorio para cargar una vacante, evaluar lotes de Hojas de Vida (individuales o hasta 50 por tanda), comparar candidatos en un ranking auditable y decidir a quién convocar a entrevista.

## Product Purpose

Evaluar de forma objetiva, rápida y auditable Hojas de Vida frente a los requisitos de una vacante: verificar filtros excluyentes (*knock-out*), calificar habilidades con citas textuales de evidencia real del CV, calcular el puntaje con reglas deterministas y entregar un veredicto claro (**Aceptable**, **Aceptable con Reservas**, **No Aceptable**) junto con brechas detectadas y preguntas sugeridas de entrevista.

## Positioning

A diferencia de filtros opacos de palabras clave o resúmenes genéricos de LLM, cada evaluación separa la extracción de hechos verificables de un cálculo determinista de puntaje, exige citas textuales y cálculo de meses para requisitos *knock-out*, señala alertas de seguridad (posible *prompt injection* o fechas inconsistentes) y registra feedback humano (*Human-in-the-Loop*) para auditar decisiones.

## Operating Context

- **Flujo diario de evaluación:**
  1. Cargar o pegar el texto de una vacante (o subir archivo `.txt`, `.md`, `.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`, `.webp`) para extraer requisitos *knock-out*, habilidades obligatorias, deseables y experiencia mínima; ajustar parámetros si hace falta.
  2. Subir una o múltiples Hojas de Vida (1 a 50 archivos en lote, con control de concurrencia).
  3. Inspeccionar el ranking comparativo con filtros por veredicto y telemetría de ejecución (latencia, tokens, costo estimado, errores por archivo).
  4. Auditar al candidato seleccionado: resumen ejecutivo, datos de contacto (PII), alertas de seguridad, desglose ponderado por categoría, estado de requisitos *knock-out*, matriz de habilidades con citas textuales del CV, brechas detectadas y preguntas sugeridas de entrevista.
  5. Registrar dictamen humano (*De acuerdo* o corrección de veredicto con comentario) y exportar resultados en CSV.

## Capabilities and Constraints

- **Capacidades confirmadas en API (`/api/v1`):**
  - `GET /health`
  - `POST /api/v1/vacancies/parse`
  - `POST /api/v1/evaluations/single`
  - `POST /api/v1/evaluations/batch` (1–50 archivos, concurrencia 1–10)
  - `GET /api/v1/evaluations` (filtro por veredicto, límite configurable)
  - `GET /api/v1/evaluations/{evaluation_id}`
  - `POST /api/v1/evaluations/{evaluation_id}/feedback` & `GET .../feedback`
  - `GET /api/v1/evaluations/export/csv`
- **Formatos soportados para ingesta:** `.pdf`, `.docx`, `.txt`, `.md`, `.png`, `.jpg`, `.jpeg`, `.webp` (hasta 10 MB por archivo).
- **Idioma de la interfaz y copy:** español.
- **Compatibilidad requerida:** mantener el título/endpoint raíz `/` en FastAPI sirviendo la aplicación web y compatibilidad total con los contratos JSON actuales y Docker.

## Evidence on Hand

- Backend completo y probado (`tests/test_api.py` y suite completa de 52 tests).
- Golden dataset real de 30 CVs y 5 vacantes en `evals/golden_dataset/`.
- Implementación HTML MVP previa en `src/api/static/index.html`.
- No fabricar métricas de clientes, testimonios ni estadísticas ficticias de contratación en la interfaz.

## Product Principles

1. **Veredicto trazable, nunca caja negra:** cada puntaje y cumplimiento debe remontarse a citas textuales y reglas explícitas.
2. **Triage veloz con inspección profunda a un clic:** pasar de decenas de CVs a la evidencia crítica del candidato sin perder contexto del ranking.
3. **Resiliencia ante archivos imperfectos o cuotas de API:** mostrar errores por archivo sin perder el resto del lote y reflejar estados de carga, vacíos y validación con claridad.
4. **Control humano explícito:** facilitar la comparación entre el dictamen del agente y el criterio del reclutador o Hiring Manager.

## Accessibility & Inclusion

- Operación completa por teclado, foco visible claro, contraste legible para lectura prolongada de texto denso y citas de CV, y estados semánticos que no dependan exclusivamente del color (etiquetas textuales junto a indicadores de estado).
