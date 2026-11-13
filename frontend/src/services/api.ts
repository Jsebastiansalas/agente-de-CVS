import {
  VacancySchema,
  BatchEvaluationResult,
  SingleEvaluationResponse,
  StoredEvaluation,
  FeedbackRecord,
  Verdict,
} from '../types/api';

const BASE_URL = '';

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error(`Error en healthcheck: HTTP ${res.status}`);
  return res.json();
}

export async function parseVacancy(
  textOrFile: { text?: string; file?: File; overridesJson?: string }
): Promise<VacancySchema> {
  const formData = new FormData();
  if (textOrFile.file) {
    formData.append('file', textOrFile.file);
  }
  if (textOrFile.text) {
    formData.append('vacancy_text', textOrFile.text);
  }
  if (textOrFile.overridesJson) {
    formData.append('overrides_json', textOrFile.overridesJson);
  }

  const res = await fetch(`${BASE_URL}/api/v1/vacancies/parse`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Error al procesar la vacante');
  }

  return res.json();
}

export async function evaluateSingleCV(
  cvFile: File,
  vacancy: { vacancyJson?: string; vacancyText?: string; vacancyFile?: File }
): Promise<SingleEvaluationResponse> {
  const formData = new FormData();
  formData.append('file', cvFile);
  if (vacancy.vacancyJson) {
    formData.append('vacancy_json', vacancy.vacancyJson);
  } else if (vacancy.vacancyText) {
    formData.append('vacancy_text', vacancy.vacancyText);
  } else if (vacancy.vacancyFile) {
    formData.append('vacancy_file', vacancy.vacancyFile);
  }

  const res = await fetch(`${BASE_URL}/api/v1/evaluations/single`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Error al evaluar CV');
  }

  return res.json();
}

export async function evaluateBatchCVs(
  files: File[],
  vacancy: { vacancyJson?: string; vacancyText?: string; vacancyFile?: File },
  maxConcurrency = 3
): Promise<BatchEvaluationResult> {
  const formData = new FormData();
  files.forEach((f) => formData.append('files', f));

  if (vacancy.vacancyJson) {
    formData.append('vacancy_json', vacancy.vacancyJson);
  } else if (vacancy.vacancyText) {
    formData.append('vacancy_text', vacancy.vacancyText);
  } else if (vacancy.vacancyFile) {
    formData.append('vacancy_file', vacancy.vacancyFile);
  }

  formData.append('max_concurrency', maxConcurrency.toString());

  const res = await fetch(`${BASE_URL}/api/v1/evaluations/batch`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Error al evaluar lote de CVs');
  }

  return res.json();
}

export async function fetchStoredEvaluations(
  verdict?: Verdict | 'TODOS',
  limit = 50
): Promise<StoredEvaluation[]> {
  const params = new URLSearchParams();
  if (verdict && verdict !== 'TODOS') {
    params.append('verdict', verdict);
  }
  params.append('limit', limit.toString());

  const res = await fetch(`${BASE_URL}/api/v1/evaluations?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Error al obtener historial');
  }

  return res.json();
}

export async function submitEvaluationFeedback(
  evaluationId: string,
  payload: {
    agrees_with_agent: boolean;
    human_verdict: Verdict;
    comment: string;
  }
): Promise<FeedbackRecord> {
  const res = await fetch(`${BASE_URL}/api/v1/evaluations/${encodeURIComponent(evaluationId)}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Error al guardar feedback');
  }

  return res.json();
}

export async function getFeedbackList(evaluationId: string): Promise<FeedbackRecord[]> {
  const res = await fetch(
    `${BASE_URL}/api/v1/evaluations/${encodeURIComponent(evaluationId)}/feedback`
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Error al consultar historial de feedback');
  }
  return res.json();
}

export function getExportCsvUrl(verdict?: string): string {
  const params = new URLSearchParams();
  if (verdict && verdict !== 'TODOS') {
    params.append('verdict', verdict);
  }
  return `${BASE_URL}/api/v1/evaluations/export/csv?${params.toString()}`;
}
