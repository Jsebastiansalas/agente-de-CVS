"""Anonimizador determinista de datos personales (PII) para mitigar sesgos (HU-1.3)."""

import re

from src.schemas.candidate import (
    CandidateContactPII,
    CandidateSchema,
    EducationEntry,
    WorkExperience,
)

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,4}(?!\w)"
)
DEMOGRAPHIC_PATTERN = re.compile(
    r"(?im)\b(?:edad|age|fecha de nacimiento|birth\s*date|dob|estado civil|"
    r"marital status|g[eé]nero|gender|sexo|sex|nacionalidad|nationality|"
    r"c[eé]dula|dni|pasaporte|passport|direcci[oó]n|address)\s*[:\-]\s*[^\n,;]+"
)
URL_PERSONAL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:linkedin\.com/in|github\.com|twitter\.com|x\.com)/[^\s,)]+",
    re.IGNORECASE,
)


def scrub_text_pii(text: str, *, contact_pii: CandidateContactPII | None = None) -> str:
    """Elimina correos, teléfonos, atributos demográficos y nombre completo de un texto."""
    cleaned = EMAIL_PATTERN.sub("[EMAIL_OCULTO]", text)
    cleaned = URL_PERSONAL_PATTERN.sub("[PERFIL_OCULTO]", cleaned)
    cleaned = PHONE_PATTERN.sub("[TELEFONO_OCULTO]", cleaned)
    cleaned = DEMOGRAPHIC_PATTERN.sub("[DATO_DEMOGRAFICO_OCULTO]", cleaned)

    if contact_pii:
        if contact_pii.email:
            cleaned = re.sub(
                re.escape(contact_pii.email),
                "[EMAIL_OCULTO]",
                cleaned,
                flags=re.IGNORECASE,
            )
        if contact_pii.phone:
            cleaned = re.sub(
                re.escape(contact_pii.phone),
                "[TELEFONO_OCULTO]",
                cleaned,
                flags=re.IGNORECASE,
            )
        if contact_pii.location:
            cleaned = re.sub(
                rf"\b{re.escape(contact_pii.location)}\b",
                "[UBICACION_OCULTA]",
                cleaned,
                flags=re.IGNORECASE,
            )
        if contact_pii.full_name:
            cleaned = re.sub(
                re.escape(contact_pii.full_name),
                "[CANDIDATO]",
                cleaned,
                flags=re.IGNORECASE,
            )
            for token in contact_pii.full_name.split():
                if len(token) >= 3:
                    cleaned = re.sub(
                        rf"\b{re.escape(token)}\b",
                        "[CANDIDATO]",
                        cleaned,
                        flags=re.IGNORECASE,
                    )

    return cleaned


def anonymize_candidate(
    candidate: CandidateSchema,
    contact_pii: CandidateContactPII | None = None,
) -> CandidateSchema:
    """Limpia recursivamente cualquier rastro de PII del perfil del candidato."""
    summary = (
        scrub_text_pii(candidate.summary, contact_pii=contact_pii)
        if candidate.summary
        else None
    )

    clean_exps = [
        WorkExperience(
            role=scrub_text_pii(exp.role, contact_pii=contact_pii),
            company=scrub_text_pii(exp.company, contact_pii=contact_pii),
            start_date=exp.start_date,
            end_date=exp.end_date,
            is_current=exp.is_current,
            calculated_months=exp.calculated_months,
            technologies=exp.technologies,
            achievements=[
                scrub_text_pii(ach, contact_pii=contact_pii) for ach in exp.achievements
            ],
        )
        for exp in candidate.work_experiences
    ]

    clean_edu = [
        EducationEntry(
            degree=scrub_text_pii(edu.degree, contact_pii=contact_pii),
            institution=scrub_text_pii(edu.institution, contact_pii=contact_pii),
            field_of_study=(
                scrub_text_pii(edu.field_of_study, contact_pii=contact_pii)
                if edu.field_of_study
                else None
            ),
            end_year=edu.end_year,
            is_completed=edu.is_completed,
        )
        for edu in candidate.education
    ]

    clean_certs = [
        scrub_text_pii(cert, contact_pii=contact_pii) for cert in candidate.certifications
    ]

    return candidate.model_copy(
        update={
            "summary": summary,
            "work_experiences": clean_exps,
            "education": clean_edu,
            "certifications": clean_certs,
        }
    )


def detect_residual_pii(
    candidate: CandidateSchema,
    contact_pii: CandidateContactPII | None = None,
) -> list[str]:
    """Verifica que el objeto CandidateSchema no conserve datos personales identificables."""
    serialized = candidate.model_dump_json()
    findings: list[str] = []

    if EMAIL_PATTERN.search(serialized):
        findings.append("Se detectó un correo electrónico residual.")
    if DEMOGRAPHIC_PATTERN.search(serialized):
        findings.append("Se detectó un dato demográfico residual (edad/género/estado civil).")
    if contact_pii and contact_pii.full_name:
        if re.search(re.escape(contact_pii.full_name), serialized, flags=re.IGNORECASE):
            findings.append("Se detectó el nombre completo residual en el perfil.")

    return findings
