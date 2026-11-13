---
name: Mesa de Dictamen Dual-Pane
description: Sistema de diseño para evaluación y auditoría objetiva de CVs vs Vacantes
colors:
  bg-canvas: "#f4f3ef"
  bg-surface: "#ffffff"
  bg-subtle: "#f9f8f5"
  text-primary: "#151821"
  text-secondary: "#525866"
  text-muted: "#7e8695"
  accent-primary: "#1d4ed8"
  accent-hover: "#1e40af"
  border-subtle: "#e5e3dc"
  border-default: "#d8d5cb"
  badge-ok-bg: "#ecfdf5"
  badge-ok-text: "#047857"
  badge-warn-bg: "#fffbeb"
  badge-warn-text: "#b45309"
  badge-bad-bg: "#fff1f2"
  badge-bad-text: "#b91c1c"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
  body:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "0.875rem"
    lineHeight: 1.5
  tabular:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.85rem"
rounded:
  xs: "4px"
  sm: "6px"
  md: "8px"
  lg: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.accent-primary}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "8px 14px"
  badge-verdict:
    rounded: "{rounded.xs}"
    padding: "3px 8px"
---

## Overview

Sistema de diseño de alta densidad operativa (modo *Operate*) inspirado en actas de adjudicación documental sobre papel mineral cálido. Diseñado específicamente para que reclutadores y Hiring Managers realicen triage de tandas de CVs y auditoría profunda de evidencias textuales en una sola pantalla sin pérdidas de contexto.

## Colors

- **Fondo mineral (`#f4f3ef`):** Evita la fatiga visual de pantallas blanco puro en jornadas diurnas de revisión prolongada.
- **Paneles (`#ffffff`):** Superficies elevadas delimitadas por filetes de 1px (`#e5e3dc`) en lugar de sombras borrosas pesadas.
- **Tinta tipográfica (`#151821`):** Contraste superior a 7:1 (cumplimiento WCAG AAA) para lectura cómoda de párrafos densos y justificaciones de LLM.
- **Acento funcional (`#1d4ed8`):** Reservado estrictamente para llamadas a la acción primarias y estados seleccionados.
- **Semántica de veredictos:**
  - *Aceptable*: Verde bosque (`#047857` sobre `#ecfdf5`).
  - *Aceptable con reservas*: Ámbar dorado (`#b45309` sobre `#fffbeb`).
  - *No aceptable*: Carmesí alerta (`#b91c1c` sobre `#fff1f2`).

## Typography

- **Familia principal:** `Plus Jakarta Sans` para lectura de interfaz, formularios y resúmenes ejecutivos.
- **Cifras tabulares:** `JetBrains Mono` y `font-variant-numeric: tabular-nums` para rankings, puntajes `0-100`, duración en segundos y conteos de tokens, garantizando alineación visual columnar perfecta.
- **Escala:** Escala compacta con ratio de 1.15 a 1.2 entre niveles jerárquicos.

## Layout

- **Estructura en dos niveles:**
  1. **Banda superior de configuración (colapsable):** Contrato de la vacante (extracción/edición) y panel de carga por lotes (1 a 50 archivos).
  2. **Zona de trabajo Dual-Pane acoplada:**
     - **Panel izquierdo (42%):** Tabla de ranking con filtros rápidos por veredicto, búsqueda y alertas.
     - **Panel derecho (58%):** Folio de auditoría del candidato seleccionado (resumen, desglose ponderado, knock-outs con meses, matriz de habilidades con citas *verbatim* y módulo Human-in-the-Loop).

## Elevation & Depth

- Filetes y costuras de 1px (`#e5e3dc` y `#d8d5cb`) como delimitador estructural primario.
- Sombra muy sutil (`0 1px 2px rgba(21, 24, 33, 0.04)`) para anclar paneles sin crear ruido visual.

## Shapes

- Radios controlados entre `4px` (badges y citas) y `8px` (paneles principales). Se evitan bordes hiperredondeados ("pills" excesivas) que restan seriedad a un entorno de auditoría.

## Components

- **Citas Verbatim (`.evidence-quote`):** Bloques con filete vertical azul a la izquierda, tipografía itálica y fondo gris perla para identificar citas literales extraídas del CV.
- **Alerta de Seguridad (`.security-alert-box`):** Caja roja destacada que se activa solo cuando el agente detecta inyección de prompt o inconsistencia cronológica.
- **Desglose de Categorías:** Barras de progreso ponderadas que visualizan el aporte matemático de cada dimensión (experiencia 40%, must-have 35%, nice-to-have 15%, educación 10%).

## Do's and Don'ts

### Do's
- Mantener siempre sincronizada la selección de la tabla izquierda con el acta derecha.
- Citar textualmente entre comillas la evidencia del CV que justifica cada puntaje o cumplimiento.
- Destacar el veredicto con texto explícito junto al color (nunca depender únicamente del color para transmitir estado).

### Don'ts
- No utilizar modales bloqueantes para inspeccionar candidatos: el reclutador necesita mantener a la vista el ranking global.
- No utilizar tipografías display o decorativas en datos o etiquetas técnicas.
- No animar elementos sin propósito de estado: las transiciones deben ser de 150-200ms para mantener la fluidez operativa.
