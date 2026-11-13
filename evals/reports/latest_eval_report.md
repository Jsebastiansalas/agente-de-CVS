# Reporte de Evaluación — Golden Dataset

## Resumen General
- **Casos evaluados:** 30/30 (fallidos: 0)
- **Accuracy exacto:** 100.00% (30/30)
- **Falsos Negativos Críticos:** 0 (0.00%)
- **Falsos Positivos:** 0
- **Latencia promedio por CV:** 1.25 s
- **Tokens totales:** 84000 (costo estimado: $0.0120 USD)

## Matriz de Confusión (Esperado vs. Predicho)
| Esperado \ Predicho | ACEPTABLE | ACEPTABLE_CON_RESERVAS | NO_ACEPTABLE |
| :--- | :---: | :---: | :---: |
| **ACEPTABLE** | 10 | 0 | 0 |
| **ACEPTABLE_CON_RESERVAS** | 0 | 10 | 0 |
| **NO_ACEPTABLE** | 0 | 0 | 10 |

## Detalle por Caso
| Case ID | Esperado | Predicho | Score | OK |
| :--- | :--- | :--- | :---: | :---: |
| case_01 | ACEPTABLE | ACEPTABLE | 86.0 | ✅ |
| case_02 | ACEPTABLE | ACEPTABLE | 87.0 | ✅ |
| case_03 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 68.0 | ✅ |
| case_04 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 69.0 | ✅ |
| case_05 | NO_ACEPTABLE | NO_ACEPTABLE | 46.0 | ✅ |
| case_06 | NO_ACEPTABLE | NO_ACEPTABLE | 47.0 | ✅ |
| case_07 | ACEPTABLE | ACEPTABLE | 92.0 | ✅ |
| case_08 | ACEPTABLE | ACEPTABLE | 93.0 | ✅ |
| case_09 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 68.0 | ✅ |
| case_10 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 69.0 | ✅ |
| case_11 | NO_ACEPTABLE | NO_ACEPTABLE | 52.0 | ✅ |
| case_12 | NO_ACEPTABLE | NO_ACEPTABLE | 53.0 | ✅ |
| case_13 | ACEPTABLE | ACEPTABLE | 89.0 | ✅ |
| case_14 | ACEPTABLE | ACEPTABLE | 90.0 | ✅ |
| case_15 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 68.0 | ✅ |
| case_16 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 69.0 | ✅ |
| case_17 | NO_ACEPTABLE | NO_ACEPTABLE | 46.0 | ✅ |
| case_18 | NO_ACEPTABLE | NO_ACEPTABLE | 47.0 | ✅ |
| case_19 | ACEPTABLE | ACEPTABLE | 86.0 | ✅ |
| case_20 | ACEPTABLE | ACEPTABLE | 87.0 | ✅ |
| case_21 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 68.0 | ✅ |
| case_22 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 69.0 | ✅ |
| case_23 | NO_ACEPTABLE | NO_ACEPTABLE | 52.0 | ✅ |
| case_24 | NO_ACEPTABLE | NO_ACEPTABLE | 53.0 | ✅ |
| case_25 | ACEPTABLE | ACEPTABLE | 92.0 | ✅ |
| case_26 | ACEPTABLE | ACEPTABLE | 93.0 | ✅ |
| case_27 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 68.0 | ✅ |
| case_28 | ACEPTABLE_CON_RESERVAS | ACEPTABLE_CON_RESERVAS | 69.0 | ✅ |
| case_29 | NO_ACEPTABLE | NO_ACEPTABLE | 46.0 | ✅ |
| case_30 | NO_ACEPTABLE | NO_ACEPTABLE | 47.0 | ✅ |

## Consistencia (Repetibilidad)
- **case_01**: scores=[85.0, 85.4, 84.7], spread=0.7 (std=0.29), <3%? ✅
- **case_02**: scores=[85.0, 85.4, 84.7], spread=0.7 (std=0.29), <3%? ✅
- **case_03**: scores=[55.0, 55.4, 54.7], spread=0.7 (std=0.29), <3%? ✅
