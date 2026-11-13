"""Generador del Golden Dataset sintético y anonimizado (5 vacantes, 30 CVs, casos difíciles)."""

import json
from pathlib import Path

from docx import Document
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

DATASET_DIR = Path(__file__).resolve().parent / "golden_dataset"
VACANCIES_DIR = DATASET_DIR / "vacancies"
CVS_DIR = DATASET_DIR / "cvs"

VACANCIES: dict[str, str] = {
    "vac_01_backend_python.txt": """Vacante: Desarrollador Backend Senior (Python)
Seniority: Senior
Modalidad: Remoto / Híbrido

Requisitos Excluyentes (Knock-out):
- Mínimo 4 años de experiencia comprobable desarrollando backend con Python.
- Experiencia en producción con FastAPI o Django.
- Inglés nivel B2 o superior (lectura técnica y reuniones).

Habilidades Obligatorias (Must-have):
- Diseño de APIs RESTful y modelado en bases de datos relacionales (PostgreSQL).
- Contenerización con Docker y pruebas automatizadas (pytest).
- Integración continua (GitHub Actions o GitLab CI).

Habilidades Deseables (Nice-to-have):
- Orquestación con Kubernetes o AWS ECS.
- Colas de mensajes (RabbitMQ, Kafka o Celery + Redis).
- Arquitectura de microservicios.

Responsabilidades:
- Diseñar y mantener servicios backend de alto tráfico.
- Optimizar consultas SQL y garantizar cobertura de pruebas.
""",
    "vac_02_frontend_react.txt": """Vacante: Desarrollador Frontend Mid (React / TypeScript)
Seniority: Mid
Modalidad: Remoto

Requisitos Excluyentes (Knock-out):
- Mínimo 2 años de experiencia desarrollando aplicaciones web con React.
- Dominio práctico de TypeScript.

Habilidades Obligatorias (Must-have):
- HTML5, CSS3 moderno / Tailwind CSS.
- Consumo de APIs REST o GraphQL y manejo de estado (Redux Toolkit, Zustand o React Query).
- Testing de componentes con Jest, Vitest o Testing Library.

Habilidades Deseables (Nice-to-have):
- Next.js (App Router / SSR).
- Accesibilidad web (WCAG) y optimización Core Web Vitals.
- Inglés B1 o superior.

Responsabilidades:
- Construir interfaces responsivas y accesibles desde diseños en Figma.
- Colaborar con backend en la definición de contratos API.
""",
    "vac_03_data_engineer.txt": """Vacante: Ingeniero de Datos Senior (SQL / Spark / Cloud)
Seniority: Senior
Modalidad: Híbrido

Requisitos Excluyentes (Knock-out):
- Mínimo 4 años de experiencia en Ingeniería de Datos o ETL/ELT.
- SQL avanzado y Python para procesamiento de datos.
- Inglés B2 o superior.

Habilidades Obligatorias (Must-have):
- Procesamiento distribuido con Apache Spark / PySpark o transformación moderna con dbt.
- Experiencia en al menos una nube (AWS, GCP o Azure) y Data Warehouses (BigQuery, Snowflake o Redshift).
- Orquestación de pipelines con Apache Airflow o Dagster.

Habilidades Deseables (Nice-to-have):
- Infraestructura como código (Terraform).
- Streaming con Kafka o Pub/Sub.

Responsabilidades:
- Construir y monitorear pipelines batch y streaming escalables.
- Garantizar calidad y linaje de datos.
""",
    "vac_04_qa_automation.txt": """Vacante: QA Automation Engineer (Mid)
Seniority: Mid
Modalidad: Remoto

Requisitos Excluyentes (Knock-out):
- Mínimo 2 años de experiencia automatizando pruebas de software (E2E o API).
- Experiencia demostrable con Playwright, Cypress o Selenium.

Habilidades Obligatorias (Must-have):
- Programación de scripts de prueba en Python, TypeScript o JavaScript.
- Automatización de pruebas de APIs REST (Postman, Pytest+httpx o RestAssured).
- Integración de suites de pruebas en pipelines CI/CD.

Habilidades Deseables (Nice-to-have):
- Pruebas de carga/performance (k6 o JMeter).
- Conocimientos de SQL para validación de datos.
- Inglés B1 o superior.

Responsabilidades:
- Diseñar, automatizar y mantener suites de regresión E2E y API.
""",
    "vac_05_devops_sre.txt": """Vacante: DevOps / SRE Engineer (Mid-Senior)
Seniority: Mid-Senior
Modalidad: Remoto

Requisitos Excluyentes (Knock-out):
- Mínimo 3 años de experiencia en roles DevOps, SRE o Infraestructura Cloud.
- Experiencia en producción con AWS y Terraform (IaC).
- Inglés nivel B2 o superior.

Habilidades Obligatorias (Must-have):
- Administración de contenedores y orquestación con Kubernetes (EKS/GKE).
- Construcción de pipelines CI/CD (GitHub Actions, GitLab CI o Jenkins).
- Administración de Linux, redes y observabilidad (Prometheus, Grafana, Datadog).

Habilidades Deseables (Nice-to-have):
- Scripting en Python o Bash/Go.
- Certificación AWS Solutions Architect o CKA.

Responsabilidades:
- Automatizar aprovisionamiento de infraestructura y despliegues sin downtime.
- Mantener SLAs y responder a incidentes en producción.
""",
}

# Definición de 30 CVs sintéticos anonimizados (6 por vacante)
CV_CASES: list[dict] = [
    # --- VACANTE 1: Backend Python Senior ---
    {
        "case_id": "case_01",
        "vacancy_file": "vac_01_backend_python.txt",
        "cv_file": "cv_01_backend_acep_senior.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "5 años reales en Python + FastAPI + PostgreSQL + Docker + pytest + Inglés C1.",
        "content": """CANDIDATO ANÓNIMO 01
Perfil: Ingeniero de Software Backend con 5 años de experiencia diseñando APIs escalables en Python.

Experiencia Laboral:
1. Senior Python Developer | FinTech Andina (2023-02 - Actualidad)
- Lideró la arquitectura de microservicios con FastAPI, PostgreSQL y Celery + Redis.
- Implementó pipelines CI/CD en GitHub Actions y suites de pruebas con pytest (90% cobertura).
- Desplegó servicios contenerizados con Docker en AWS ECS.

2. Backend Developer | DataSoft Latam (2021-01 - 2023-01)
- Desarrolló APIs REST en Django y FastAPI conectadas a PostgreSQL.
- Optimizó consultas SQL reduciendo latencia promedio en 40%.

Educación:
- Ingeniería de Sistemas (2019).

Idiomas:
- Español: Nativo
- Inglés: C1 (IELTS 2023)
""",
    },
    {
        "case_id": "case_02",
        "vacancy_file": "vac_01_backend_python.txt",
        "cv_file": "cv_02_backend_acep_2col.pdf",
        "format": "two_column_pdf",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["two_column_pdf"],
        "reason": "CV en dos columnas; cumple 4.5+ años en Python/Django/PostgreSQL/Docker/CI e Inglés B2.",
        "left_col": [
            "CANDIDATO ANÓNIMO 02",
            "Senior Backend Engineer",
            "",
            "HABILIDADES",
            "- Python (5 años)",
            "- Django / DRF / FastAPI",
            "- PostgreSQL, Redis",
            "- Docker, Kubernetes",
            "- pytest, GitLab CI",
            "",
            "IDIOMAS",
            "- Español: Nativo",
            "- Inglés: B2 Certificado",
            "",
            "EDUCACIÓN",
            "Ingeniero Informático (2018)",
        ],
        "right_col": [
            "EXPERIENCIA LABORAL",
            "",
            "Backend Lead | CloudPay (2022-06 - Actualidad)",
            "- Diseño de APIs RESTful con FastAPI y PostgreSQL.",
            "- Despliegue en Kubernetes y pipelines GitLab CI.",
            "- Cobertura de pruebas automatizadas con pytest.",
            "",
            "Python Developer | RetailTech (2020-01 - 2022-05)",
            "- Desarrollo de módulos backend en Django.",
            "- Contenerización con Docker y RabbitMQ.",
        ],
    },
    {
        "case_id": "case_03",
        "vacancy_file": "vac_01_backend_python.txt",
        "cv_file": "cv_03_backend_reservas_equiv.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["equivalent_technologies", "missing_knockout_info"],
        "reason": "Tiene 4 años en Python/Flask+MySQL (tecnología equivalente a FastAPI/PostgreSQL) pero no menciona nivel de inglés.",
        "content": """CANDIDATO ANÓNIMO 03
Perfil: Desarrollador Backend Python con foco en sistemas transaccionales.

Experiencia Laboral:
1. Desarrollador Backend | PagosRápidos (2022-05 - Actualidad)
- Construcción de servicios REST con Flask y SQLAlchemy sobre MySQL.
- Uso diario de Docker, pytest y GitHub Actions.

2. Desarrollador Python | Agencia Digital (2021-06 - 2022-04)
- Desarrollo de endpoints internos en Python y bases de datos relacionales.

Educación:
- Tecnólogo en Desarrollo de Software (2020).
""",
    },
    {
        "case_id": "case_04",
        "vacancy_file": "vac_01_backend_python.txt",
        "cv_file": "cv_04_backend_reservas_overlap.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["overlapping_dates"],
        "reason": "Tiene trabajos traslapados (2023-2025 paralelo); meses reales ~38 meses (cerca de 4 años) con buen stack.",
        "content": """CANDIDATO ANÓNIMO 04
Perfil: Desarrollador Python / FastAPI.

Experiencia Laboral:
1. Consultor Backend Freelance | Varios Clientes (2023-06 - 2025-10)
- Desarrollo de APIs en FastAPI, PostgreSQL y Docker.

2. Backend Developer | TechCorp (2023-01 - Actualidad)
- Servicios REST en Django y FastAPI con PostgreSQL, pytest y GitLab CI.

Educación:
- Ingeniero de Software (2022).

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_05",
        "vacancy_file": "vac_01_backend_python.txt",
        "cv_file": "cv_05_backend_reject_junior.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "Solo 8 meses de experiencia laboral; incumple requisito excluyente de 4 años en Python.",
        "content": """CANDIDATO ANÓNIMO 05
Perfil: Desarrollador Junior recién egresado con conocimientos en Python.

Experiencia Laboral:
1. Practicante Backend | StartUp Uno (2025-02 - 2025-10)
- Apoyo en endpoints básicos con FastAPI y pruebas manuales.

Educación:
- Bootcamp Desarrollo Web (2024).

Idiomas:
- Inglés: A2
""",
    },
    {
        "case_id": "case_06",
        "vacancy_file": "vac_01_backend_python.txt",
        "cv_file": "cv_06_backend_reject_stack.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "6 años de experiencia pero en PHP/WordPress; no tiene experiencia en Python ni FastAPI/Django.",
        "content": """CANDIDATO ANÓNIMO 06
Perfil: Desarrollador Web Senior en PHP y WordPress.

Experiencia Laboral:
1. Senior PHP Developer | WebStudio (2020-01 - Actualidad)
- Desarrollo de sitios corporativos y e-commerce en WordPress, WooCommerce y Laravel.
- Administración de MySQL y cPanel.

Idiomas:
- Inglés: B2
""",
    },
    # --- VACANTE 2: Frontend Mid React / TypeScript ---
    {
        "case_id": "case_07",
        "vacancy_file": "vac_02_frontend_react.txt",
        "cv_file": "cv_07_frontend_acep_docx.docx",
        "format": "docx",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["docx_format"],
        "reason": "CV en DOCX; 3 años en React, TypeScript, Tailwind, React Query, Vitest y Next.js.",
        "content": """CANDIDATO ANÓNIMO 07
Perfil: Frontend Developer con 3 años de experiencia creando aplicaciones SPA y SSR.

Experiencia Laboral:
1. Frontend Engineer | ComercioPlus (2023-04 - Actualidad)
- Desarrollo de plataforma e-commerce con React 18, TypeScript, Next.js y Tailwind CSS.
- Manejo de estado servidor con React Query y pruebas unitarias con Vitest + Testing Library.

2. Junior Frontend Developer | PixelLab (2022-01 - 2023-03)
- Maquetación en HTML5/CSS3 y componentes reutilizables en React + Redux Toolkit.

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_08",
        "vacancy_file": "vac_02_frontend_react.txt",
        "cv_file": "cv_08_frontend_acep_std.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "3.5 años en React + TypeScript + Jest + GraphQL + CSS moderno.",
        "content": """CANDIDATO ANÓNIMO 08
Perfil: Ingeniero Frontend especializado en ecosistema React.

Experiencia Laboral:
1. Mid Frontend Developer | SaaS Cloud (2022-05 - Actualidad)
- Interfaces complejas con React, TypeScript, Zustand y GraphQL.
- Pruebas con Jest y React Testing Library; optimización de Core Web Vitals.

Idiomas:
- Inglés: B1
""",
    },
    {
        "case_id": "case_09",
        "vacancy_file": "vac_02_frontend_react.txt",
        "cv_file": "cv_09_frontend_reservas_scan.pdf",
        "format": "scanned_image_pdf",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["scanned_image_pdf"],
        "reason": "PDF escaneado sin capa de texto; 2.5 años en React/JS, pero TypeScript solo listado sin evidencia laboral y sin testing.",
        "lines": [
            "CANDIDATO ANONIMO 09",
            "Frontend Developer",
            "",
            "EXPERIENCIA LABORAL:",
            "Desarrollador Web | Agencia Creativa (2023-05 - Actualidad)",
            "- Construccion de interfaces en React y JavaScript ES6.",
            "- Consumo de APIs REST y estilos con CSS3 y Tailwind.",
            "",
            "HABILIDADES LISTADAS:",
            "React, JavaScript, TypeScript, HTML, CSS.",
            "",
            "IDIOMAS: Ingles A2",
        ],
    },
    {
        "case_id": "case_10",
        "vacancy_file": "vac_02_frontend_react.txt",
        "cv_file": "cv_10_frontend_reservas_angular.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["equivalent_technologies"],
        "reason": "3 años fuertes en Angular + TypeScript + RxJS, y solo 1 proyecto corto en React; alta transferibilidad.",
        "content": """CANDIDATO ANÓNIMO 10
Perfil: Frontend Developer con sólida experiencia en TypeScript.

Experiencia Laboral:
1. Frontend Developer | Banco Digital (2022-08 - Actualidad)
- Desarrollo de banca web en Angular 15, TypeScript, RxJS y pruebas con Jest.
- Migración de módulo de onboarding a React + TypeScript durante 4 meses.

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_11",
        "vacancy_file": "vac_02_frontend_react.txt",
        "cv_file": "cv_11_frontend_reject_noexp.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "Sin experiencia laboral formal en React ni TypeScript (solo proyectos académicos).",
        "content": """CANDIDATO ANÓNIMO 11
Perfil: Estudiante de último semestre buscando primera oportunidad laboral.

Experiencia:
- Proyecto universitario de carrito de compras en HTML, CSS y JavaScript vanilla (3 meses).

Educación:
- Ingeniería de Sistemas (en curso).
""",
    },
    {
        "case_id": "case_12",
        "vacancy_file": "vac_02_frontend_react.txt",
        "cv_file": "cv_12_frontend_reject_backend.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "Perfil DBA / PL-SQL sin experiencia en React ni desarrollo frontend.",
        "content": """CANDIDATO ANÓNIMO 12
Perfil: Administrador de Bases de Datos Oracle.

Experiencia Laboral:
1. DBA Oracle | Telecom (2019-01 - Actualidad)
- Administración de instancias Oracle, tuning SQL y respaldos RMAN.
""",
    },
    # --- VACANTE 3: Data Engineer Senior ---
    {
        "case_id": "case_13",
        "vacancy_file": "vac_03_data_engineer.txt",
        "cv_file": "cv_13_data_acep_senior.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "5 años en Data Engineering con PySpark, SQL, Airflow, Redshift/AWS e Inglés C1.",
        "content": """CANDIDATO ANÓNIMO 13
Perfil: Senior Data Engineer con 5 años construyendo plataformas analíticas en AWS.

Experiencia Laboral:
1. Senior Data Engineer | RetailAnalytics (2022-01 - Actualidad)
- Pipelines batch y streaming con PySpark, AWS Glue, Kafka y Apache Airflow.
- Modelado dimensional en Amazon Redshift y dbt; automatización con Terraform.

2. Data Engineer | Seguros Global (2020-06 - 2021-12)
- Procesos ETL en Python y SQL avanzado sobre PostgreSQL y S3.

Idiomas:
- Inglés: C1
""",
    },
    {
        "case_id": "case_14",
        "vacancy_file": "vac_03_data_engineer.txt",
        "cv_file": "cv_14_data_acep_gcp.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "4.5 años en GCP, BigQuery, dbt, Python, Airflow e Inglés B2.",
        "content": """CANDIDATO ANÓNIMO 14
Perfil: Ingeniero de Datos especializado en GCP.

Experiencia Laboral:
1. Data Engineer | MobilityApp (2021-04 - Actualidad)
- Orquestación de DAGs en Cloud Composer (Apache Airflow).
- Transformaciones ELT con dbt y SQL avanzado en BigQuery; ingesta con Python y Pub/Sub.

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_15",
        "vacancy_file": "vac_03_data_engineer.txt",
        "cv_file": "cv_15_data_reservas_bi.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["equivalent_technologies"],
        "reason": "4.5 años en BI/SQL/Python y Snowflake, pero sin experiencia comprobada en Spark ni Airflow (usó SSIS/Azure Data Factory).",
        "content": """CANDIDATO ANÓNIMO 15
Perfil: BI & Data Specialist.

Experiencia Laboral:
1. Especialista ETL / BI | Grupo Financiero (2021-03 - Actualidad)
- Pipelines ELT en Azure Data Factory y scripts Python hacia Snowflake.
- SQL avanzado para reportes ejecutivos y modelado estrella.

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_16",
        "vacancy_file": "vac_03_data_engineer.txt",
        "cv_file": "cv_16_data_reservas_noeng.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["missing_knockout_info"],
        "reason": "Cumple el stack técnico (4+ años PySpark, Airflow, AWS, SQL), pero no especifica nivel de inglés.",
        "content": """CANDIDATO ANÓNIMO 16
Perfil: Data Engineer.

Experiencia Laboral:
1. Data Engineer | Logística Express (2021-01 - Actualidad)
- Diseño de pipelines en PySpark y Apache Airflow sobre AWS EMR y Redshift.
- Modelado de datos con dbt y SQL.
""",
    },
    {
        "case_id": "case_17",
        "vacancy_file": "vac_03_data_engineer.txt",
        "cv_file": "cv_17_data_reject_analyst.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "Analista de datos enfocado en Excel y Power BI sin pipelines en Python/Spark/Airflow ni cloud.",
        "content": """CANDIDATO ANÓNIMO 17
Perfil: Analista de Datos / Reporting.

Experiencia Laboral:
1. Analista de Datos | Comercializadora Norte (2022-01 - Actualidad)
- Creación de tableros en Power BI y Excel avanzado (tablas dinámicas, macros).
- Consultas SQL básicas de extracción.
""",
    },
    {
        "case_id": "case_18",
        "vacancy_file": "vac_03_data_engineer.txt",
        "cv_file": "cv_18_data_reject_1yr.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "Solo 1 año de experiencia total; incumple el mínimo excluyente de 4 años.",
        "content": """CANDIDATO ANÓNIMO 18
Perfil: Junior Data Engineer.

Experiencia Laboral:
1. Junior Data Engineer | TechStart (2024-10 - 2025-10)
- Mantenimiento de scripts Python y consultas en BigQuery.

Idiomas:
- Inglés: B2
""",
    },
    # --- VACANTE 4: QA Automation Engineer ---
    {
        "case_id": "case_19",
        "vacancy_file": "vac_04_qa_automation.txt",
        "cv_file": "cv_19_qa_acep_playwright.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "3 años automatizando con Playwright + TypeScript + Postman + GitHub Actions + k6.",
        "content": """CANDIDATO ANÓNIMO 19
Perfil: QA Automation Engineer.

Experiencia Laboral:
1. QA Automation Engineer | EdTech Global (2022-09 - Actualidad)
- Creación desde cero de framework E2E con Playwright y TypeScript.
- Automatización de pruebas API con Postman/Newman integradas en GitHub Actions.
- Pruebas de carga con k6 y validaciones en PostgreSQL.

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_20",
        "vacancy_file": "vac_04_qa_automation.txt",
        "cv_file": "cv_20_qa_acep_selenium.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "2.5 años en Selenium + Python + Pytest + GitLab CI.",
        "content": """CANDIDATO ANÓNIMO 20
Perfil: QA Engineer especializado en automatización con Python.

Experiencia Laboral:
1. QA Automation | InsurTech (2023-03 - Actualidad)
- Suites de regresión web con Selenium WebDriver y Python (Pytest).
- Pruebas automatizadas de endpoints REST con pytest + httpx en GitLab CI.

Idiomas:
- Inglés: B1
""",
    },
    {
        "case_id": "case_21",
        "vacancy_file": "vac_04_qa_automation.txt",
        "cv_file": "cv_21_qa_reservas_manual.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["standard"],
        "reason": "3 años de QA Manual y apenas 1 año de automatización con Cypress (por debajo de 2 años en automatización).",
        "content": """CANDIDATO ANÓNIMO 21
Perfil: Analista QA en transición a automatización.

Experiencia Laboral:
1. QA Analyst | Banca Móvil (2022-01 - Actualidad)
- 2 años ejecutando pruebas funcionales manuales, casos de prueba en Jira y Postman manual.
- Último año (2024-10 - Actualidad) automatizando flujos críticos con Cypress y JavaScript.

Idiomas:
- Inglés: B1
""",
    },
    {
        "case_id": "case_22",
        "vacancy_file": "vac_04_qa_automation.txt",
        "cv_file": "cv_22_qa_reservas_java.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["equivalent_technologies"],
        "reason": "3 años automatizando con Selenium + Java + RestAssured (stack equivalente, aunque pide Python/TS/JS).",
        "content": """CANDIDATO ANÓNIMO 22
Perfil: QA Automation Engineer (Java).

Experiencia Laboral:
1. Automation Tester | Consulting Tech (2022-06 - Actualidad)
- Automatización UI con Selenium + Java (TestNG) y APIs con RestAssured.
- Integración continua en Jenkins.

Idiomas:
- Inglés: B1
""",
    },
    {
        "case_id": "case_23",
        "vacancy_file": "vac_04_qa_automation.txt",
        "cv_file": "cv_23_qa_reject_onlymanual.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "4 años de QA 100% manual sin programación ni herramientas de automatización.",
        "content": """CANDIDATO ANÓNIMO 23
Perfil: QA Tester Manual.

Experiencia Laboral:
1. Tester Manual | Software House (2021-01 - Actualidad)
- Ejecución manual de pruebas exploratorias y de regresión.
- Reporte de bugs en Jira y Trello.
""",
    },
    {
        "case_id": "case_24",
        "vacancy_file": "vac_04_qa_automation.txt",
        "cv_file": "cv_24_qa_reject_support.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "Experiencia exclusivamente en mesa de ayuda y soporte técnico N1.",
        "content": """CANDIDATO ANÓNIMO 24
Perfil: Técnico de Soporte TI.

Experiencia Laboral:
1. Soporte Técnico N1 | CallCenter SA (2021-05 - Actualidad)
- Atención de tickets de hardware, Windows y Office 365.
""",
    },
    # --- VACANTE 5: DevOps / SRE ---
    {
        "case_id": "case_25",
        "vacancy_file": "vac_05_devops_sre.txt",
        "cv_file": "cv_25_devops_acep_senior.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "4 años en AWS + Terraform + Kubernetes EKS + GitHub Actions + Prometheus/Grafana + Inglés B2.",
        "content": """CANDIDATO ANÓNIMO 25
Perfil: Site Reliability Engineer / DevOps.

Experiencia Laboral:
1. SRE / DevOps Engineer | CloudNative Co (2021-08 - Actualidad)
- Gestión de infraestructura en AWS con Terraform y módulos reutilizables.
- Administración de clústeres Kubernetes (EKS), Helm y GitHub Actions.
- Observabilidad con Prometheus, Grafana y alertas en PagerDuty; Linux y scripting en Python/Bash.

Certificaciones:
- AWS Certified Solutions Architect - Associate.

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_26",
        "vacancy_file": "vac_05_devops_sre.txt",
        "cv_file": "cv_26_devops_acep_gitlab.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "3.5 años en AWS, Terraform, Kubernetes, GitLab CI, Datadog e Inglés C1.",
        "content": """CANDIDATO ANÓNIMO 26
Perfil: DevOps Engineer.

Experiencia Laboral:
1. DevOps Engineer | PayTech (2022-03 - Actualidad)
- Infraestructura como código con Terraform en AWS (VPC, RDS, EKS).
- Pipelines CI/CD en GitLab CI; monitoreo y APM con Datadog en servidores Linux.

Idiomas:
- Inglés: C1
""",
    },
    {
        "case_id": "case_27",
        "vacancy_file": "vac_05_devops_sre.txt",
        "cv_file": "cv_27_devops_reservas_azure.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["equivalent_technologies"],
        "reason": "4 años fuertes en Terraform + Kubernetes (AKS) + CI/CD, pero en Azure/GCP en vez de AWS.",
        "content": """CANDIDATO ANÓNIMO 27
Perfil: Cloud & DevOps Engineer.

Experiencia Laboral:
1. DevOps Engineer | Enterprise Corp (2021-06 - Actualidad)
- Infraestructura con Terraform en Azure y GCP (AKS/GKE).
- Pipelines en GitHub Actions y monitoreo con Prometheus/Grafana sobre Linux.

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_28",
        "vacancy_file": "vac_05_devops_sre.txt",
        "cv_file": "cv_28_devops_reservas_noiac.txt",
        "format": "txt",
        "expected_verdict": "ACEPTABLE_CON_RESERVAS",
        "difficulty_tags": ["standard"],
        "reason": "3 años en AWS, Docker/ECS y CI/CD, pero Terraform solo en laboratorio y sin Kubernetes en producción.",
        "content": """CANDIDATO ANÓNIMO 28
Perfil: Cloud Operations Engineer.

Experiencia Laboral:
1. Cloud Engineer | MediaStream (2022-09 - Actualidad)
- Operación de servicios en AWS EC2 y AWS ECS, pipelines en Jenkins y monitoreo en CloudWatch.
- Prácticas internas con Terraform para entornos de prueba.

Idiomas:
- Inglés: B2
""",
    },
    {
        "case_id": "case_29",
        "vacancy_file": "vac_05_devops_sre.txt",
        "cv_file": "cv_29_devops_reject_onprem.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "Administrador de redes on-premise sin experiencia en AWS, Terraform, Kubernetes ni CI/CD.",
        "content": """CANDIDATO ANÓNIMO 29
Perfil: SysAdmin On-Premise.

Experiencia Laboral:
1. Administrador de Servidores | Industrias del Sur (2019-01 - Actualidad)
- Mantenimiento de servidores físicos Windows Server, Active Directory y VMware vSphere.
- Cableado estructurado y firewalls locales.
""",
    },
    {
        "case_id": "case_30",
        "vacancy_file": "vac_05_devops_sre.txt",
        "cv_file": "cv_30_devops_reject_english.txt",
        "format": "txt",
        "expected_verdict": "NO_ACEPTABLE",
        "difficulty_tags": ["standard"],
        "reason": "Solo 1 año de experiencia e inglés A1 (incumple 3 años mínimos e inglés B2 excluyente).",
        "content": """CANDIDATO ANÓNIMO 30
Perfil: Junior Cloud Support.

Experiencia Laboral:
1. Cloud Support Associate | Hosting Co (2024-10 - 2025-10)
- Soporte básico a instancias EC2 y S3 en AWS.

Idiomas:
- Inglés: A1
""",
    },
]


def _write_two_column_pdf(path: Path, left_col: list[str], right_col: list[str]) -> None:
    """Genera un PDF real de dos columnas usando ReportLab."""
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 10)

    y_left = height - 50
    for line in left_col:
        c.drawString(40, y_left, line)
        y_left -= 15

    y_right = height - 50
    for line in right_col:
        c.drawString(width / 2 + 10, y_right, line)
        y_right -= 15

    c.save()


def _write_scanned_image_pdf(path: Path, lines: list[str]) -> None:
    """Genera un PDF compuesto únicamente por una imagen renderizada (sin capa de texto)."""
    img = Image.new("RGB", (1240, 1754), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=24)

    y = 60
    for line in lines:
        draw.text((60, y), line, fill="black", font=font)
        y += 38

    temp_img = path.with_suffix(".png")
    img.save(temp_img)

    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    c.drawImage(str(temp_img), 0, 0, width=width, height=height)
    c.save()
    temp_img.unlink(missing_ok=True)


def _write_docx(path: Path, content: str) -> None:
    """Genera un archivo DOCX real con python-docx."""
    doc = Document()
    for line in content.strip().splitlines():
        doc.add_paragraph(line)
    doc.save(str(path))


def build_dataset() -> None:
    """Construye todas las vacantes, CVs y el archivo ground_truth.json."""
    VACANCIES_DIR.mkdir(parents=True, exist_ok=True)
    CVS_DIR.mkdir(parents=True, exist_ok=True)

    for filename, text in VACANCIES.items():
        (VACANCIES_DIR / filename).write_text(text.strip() + "\n", encoding="utf-8")

    ground_truth_cases = []
    for item in CV_CASES:
        cv_path = CVS_DIR / item["cv_file"]
        fmt = item["format"]
        if fmt == "txt":
            cv_path.write_text(item["content"].strip() + "\n", encoding="utf-8")
        elif fmt == "docx":
            _write_docx(cv_path, item["content"])
        elif fmt == "two_column_pdf":
            _write_two_column_pdf(cv_path, item["left_col"], item["right_col"])
        elif fmt == "scanned_image_pdf":
            _write_scanned_image_pdf(cv_path, item["lines"])
        else:
            raise ValueError(f"Formato no soportado: {fmt}")

        ground_truth_cases.append(
            {
                "case_id": item["case_id"],
                "vacancy_file": f"vacancies/{item['vacancy_file']}",
                "cv_file": f"cvs/{item['cv_file']}",
                "expected_verdict": item["expected_verdict"],
                "reason": item["reason"],
                "difficulty_tags": item["difficulty_tags"],
            }
        )

    gt_payload = {"version": "1.0.0", "cases": ground_truth_cases}
    (DATASET_DIR / "ground_truth.json").write_text(
        json.dumps(gt_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build_dataset()
    print(f"Golden Dataset generado en {DATASET_DIR}")
