# Agente Evaluador de Hojas de Vida vs. Vacantes

Sistema agéntico en **Python + LangGraph + Google Gemini** que compara hojas de vida (`PDF`, `DOCX`, `TXT`) contra una vacante, valida requisitos excluyentes (*knock-out*), evalúa habilidades con citas de evidencia textual, calcula el puntaje de forma determinista y entrega un veredicto auditable (**Aceptable**, **Aceptable con Reservas**, **No Aceptable**).

## Requisitos e Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Edita .env con tu GEMINI_API_KEY
```

## Levantar API y Dashboard MVP

```powershell
.\.venv\Scripts\uvicorn.exe src.api.main:app --reload --port 8000
```

- Dashboard visual: `http://localhost:8000/`
- Documentación interactiva Swagger/OpenAPI: `http://localhost:8000/docs`

## Pruebas, Linting y Benchmark

```powershell
# Linter
.\.venv\Scripts\ruff.exe check .

# Suite de pruebas unitarias e integración
.\.venv\Scripts\pytest.exe -v

# Benchmark contra el Golden Dataset (30 CVs / 5 vacantes)
.\.venv\Scripts\python.exe -m evals.run_evals --concurrency 2 --consistency-sample 2
```
