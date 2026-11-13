# Agente Evaluador de Hojas de Vida vs. Vacantes

Sistema agéntico en **Python + LangGraph + Google Gemini** que compara hojas de vida (`PDF`, `DOCX`, `TXT`, `MD` e imágenes `PNG/JPG/WEBP`) contra una vacante, valida requisitos excluyentes (*knock-out*), evalúa habilidades con citas de evidencia textual, calcula el puntaje de forma determinista y entrega un veredicto auditable (**Aceptable**, **Aceptable con Reservas**, **No Aceptable**).

## Requisitos e Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Edita .env con tu GEMINI_API_KEY
```

## Levantar API y Dashboard React

```powershell
# 1. Compilar bundle de React (emite en src/api/static)
cd frontend
npm install
npm run build
cd ..

# 2. Iniciar servidor FastAPI
.\.venv\Scripts\uvicorn.exe src.api.main:app --reload --port 8000
```

- Dashboard interactivo (Mesa de Dictamen Dual-Pane en React): `http://localhost:8000/`
- Servidor de desarrollo Vite con Hot Module Replacement (HMR):
  ```powershell
  cd frontend
  npm run dev
  # Abre http://localhost:5173/ con proxy automático hacia http://127.0.0.1:8000
  ```
- Documentación interactiva Swagger/OpenAPI: `http://localhost:8000/docs`

## Ejecutar con Docker y Docker Compose

Asegúrate de tener tu archivo `.env` configurado con `GEMINI_API_KEY` (nunca se copia dentro de la imagen, se inyecta en tiempo de ejecución).

```powershell
# Construir y levantar el servicio (Dashboard + API en puerto 8000, DB persistida en ./data)
docker compose up --build -d

# Ver logs
docker compose logs -f

# Ejecutar CLI dentro del contenedor montando una carpeta local de documentos
docker compose run --rm -v "${PWD}\evals\golden_dataset:/docs:ro" cv-agent python -m src.cli --vacancy /docs/vacancies/vac_01_backend_python.txt --cv /docs/cvs/cv_02_backend_acep_2col.pdf
```

## Evaluar archivos directamente por CLI

```powershell
# Un CV contra archivo de vacante
.\.venv\Scripts\python.exe -m src.cli --vacancy ruta\vacante.pdf --cv ruta\hoja_de_vida.pdf

# Múltiples CVs (PDF, DOCX, imagen)
.\.venv\Scripts\python.exe -m src.cli --vacancy ruta\vacante.txt --cv cv1.pdf cv2.docx cv3.png
```

## Pruebas, Linting y Benchmark

```powershell
# Linter
.\.venv\Scripts\ruff.exe check .

# Suite de pruebas unitarias e integración
.\.venv\Scripts\pytest.exe -v

# Benchmark contra el Golden Dataset (30 CVs / 5 vacantes)
.\.venv\Scripts\python.exe -m evals.run_evals --concurrency 2 --consistency-sample 2
```
