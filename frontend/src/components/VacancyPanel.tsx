import React, { useState } from 'react';
import { Briefcase, FileUp, Sparkles, CheckCircle2, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { VacancySchema, SeniorityLevel } from '../types/api';
import { parseVacancy } from '../services/api';

interface VacancyPanelProps {
  currentVacancy: VacancySchema | null;
  onVacancyLoaded: (vacancy: VacancySchema) => void;
  rawVacancyFile: File | null;
  onRawVacancyFileChange: (file: File | null) => void;
}

export const VacancyPanel: React.FC<VacancyPanelProps> = ({
  currentVacancy,
  onVacancyLoaded,
  rawVacancyFile,
  onRawVacancyFileChange,
}) => {
  const [vacancyText, setVacancyText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);
  const [isEditing, setIsEditing] = useState(false);

  // Campos editables
  const [editTitle, setEditTitle] = useState('');
  const [editSeniority, setEditSeniority] = useState<SeniorityLevel>('SENIOR');
  const [editYears, setEditYears] = useState<number>(3);
  const [editKnockouts, setEditKnockouts] = useState<string>('');
  const [editMustHaves, setEditMustHaves] = useState<string>('');
  const [editNiceHaves, setEditNiceHaves] = useState<string>('');

  const handleParse = async () => {
    if (!vacancyText.trim() && !rawVacancyFile) {
      setError('Ingresa el texto de la vacante o sube un archivo.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const parsed = await parseVacancy({
        text: vacancyText.trim() || undefined,
        file: rawVacancyFile || undefined,
      });
      onVacancyLoaded(parsed);
      populateEditFields(parsed);
      setIsEditing(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al procesar la vacante');
    } finally {
      setLoading(false);
    }
  };

  const populateEditFields = (v: VacancySchema) => {
    setEditTitle(v.title);
    setEditSeniority(v.seniority);
    setEditYears(v.min_years_experience);
    setEditKnockouts(v.knockout_requirements.join('\n'));
    setEditMustHaves(v.must_have_skills.join('\n'));
    setEditNiceHaves(v.nice_to_have_skills.join('\n'));
  };

  const handleSaveEdits = () => {
    if (!currentVacancy) return;
    const updated: VacancySchema = {
      ...currentVacancy,
      title: editTitle.trim() || currentVacancy.title,
      seniority: editSeniority,
      min_years_experience: Number(editYears) || 0,
      knockout_requirements: editKnockouts
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean),
      must_have_skills: editMustHaves
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean),
      nice_to_have_skills: editNiceHaves
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean),
    };
    onVacancyLoaded(updated);
    setIsEditing(false);
  };

  return (
    <div className="desk-panel">
      <div className="panel-header">
        <div className="panel-title">
          <Briefcase size={16} color="#1d4ed8" />
          <span>1. Contrato de la Vacante</span>
          {currentVacancy && (
            <span
              className="badge badge-aceptable tabular"
              style={{ fontSize: '0.72rem', textTransform: 'none' }}
            >
              <CheckCircle2 size={12} /> {currentVacancy.title} ({currentVacancy.seniority})
            </span>
          )}
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => setExpanded(!expanded)}
          title={expanded ? 'Colapsar panel' : 'Expandir panel'}
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {expanded && (
        <div className="panel-body">
          {!currentVacancy || isEditing ? (
            <div>
              <div className="form-group">
                <label className="form-label">
                  Pega la descripción de la vacante o sube su archivo (PDF, DOCX, TXT, MD, Imagen):
                </label>
                <textarea
                  className="form-textarea"
                  placeholder="Ej: Buscamos Desarrollador Backend Python Senior con 4+ años de experiencia en FastAPI, PostgreSQL y Docker..."
                  value={vacancyText}
                  onChange={(e) => setVacancyText(e.target.value)}
                  rows={4}
                />
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 12,
                  flexWrap: 'wrap',
                }}
              >
                <label
                  className="btn btn-secondary btn-sm"
                  style={{ cursor: 'pointer' }}
                >
                  <FileUp size={14} />
                  <span>
                    {rawVacancyFile ? rawVacancyFile.name : 'Subir archivo de vacante'}
                  </span>
                  <input
                    type="file"
                    style={{ display: 'none' }}
                    accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp"
                    onChange={(e) => {
                      const file = e.target.files?.[0] || null;
                      onRawVacancyFileChange(file);
                    }}
                  />
                </label>

                {rawVacancyFile && (
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => onRawVacancyFileChange(null)}
                    style={{ color: '#ef4444' }}
                  >
                    Quitar archivo
                  </button>
                )}

                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={handleParse}
                  disabled={loading}
                  style={{ marginLeft: 'auto' }}
                >
                  <Sparkles size={14} />
                  <span>{loading ? 'Extrayendo con IA...' : 'Extraer Requisitos con Gemini'}</span>
                </button>
              </div>

              {error && (
                <div className="security-alert-box" style={{ marginTop: 8 }}>
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}
            </div>
          ) : (
            <div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: 10,
                  marginBottom: 12,
                  fontSize: '0.82rem',
                }}
              >
                <div style={{ background: '#f8fafc', padding: 8, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                  <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem' }}>PUESTO</span>
                  <strong>{currentVacancy.title}</strong>
                </div>
                <div style={{ background: '#f8fafc', padding: 8, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                  <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem' }}>SENIORITY / EXP. MÍNIMA</span>
                  <strong className="tabular">{currentVacancy.seniority} · {currentVacancy.min_years_experience} años</strong>
                </div>
                <div style={{ background: '#f8fafc', padding: 8, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                  <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem' }}>KNOCK-OUT REQUERIDOS</span>
                  <strong className="tabular">{currentVacancy.knockout_requirements.length} filtros</strong>
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div>
                  <strong style={{ color: '#b91c1c' }}>Filtros Excluyentes (Knock-out): </strong>
                  {currentVacancy.knockout_requirements.length > 0 ? (
                    <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                      {currentVacancy.knockout_requirements.map((kr, idx) => (
                        <li key={idx} style={{ color: '#7f1d1d' }}>{kr}</li>
                      ))}
                    </ul>
                  ) : (
                    <span style={{ color: '#94a3b8' }}>Ninguno detectado</span>
                  )}
                </div>

                <div>
                  <strong style={{ color: '#1e40af' }}>Habilidades Obligatorias (Must-Have): </strong>
                  <span style={{ color: '#334155' }}>
                    {currentVacancy.must_have_skills.join(', ') || 'No especificadas'}
                  </span>
                </div>

                <div>
                  <strong style={{ color: '#047857' }}>Habilidades Deseables (Nice-to-Have): </strong>
                  <span style={{ color: '#334155' }}>
                    {currentVacancy.nice_to_have_skills.join(', ') || 'Ninguna'}
                  </span>
                </div>
              </div>

              <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    populateEditFields(currentVacancy);
                    setIsEditing(true);
                  }}
                >
                  Modificar Parámetros
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => {
                    setIsEditing(true);
                    setVacancyText('');
                    onRawVacancyFileChange(null);
                  }}
                >
                  Cargar otra Vacante
                </button>
              </div>
            </div>
          )}

          {isEditing && currentVacancy && (
            <div
              style={{
                marginTop: 14,
                padding: 12,
                background: '#f8fafc',
                borderRadius: 6,
                border: '1px solid #cbd5e1',
              }}
            >
              <h4 style={{ fontSize: '0.82rem', marginBottom: 10, color: '#1e293b' }}>
                Ajustar Requisitos de Rúbrica
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div className="form-group">
                  <label className="form-label">Título del Cargo</label>
                  <input
                    type="text"
                    className="form-control"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Años Mínimos de Experiencia</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    className="form-control"
                    value={editYears}
                    onChange={(e) => setEditYears(parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Filtros Knock-out (uno por línea)</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={editKnockouts}
                  onChange={(e) => setEditKnockouts(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Habilidades Obligatorias (Must-Have, una por línea)</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={editMustHaves}
                  onChange={(e) => setEditMustHaves(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Habilidades Deseables (Nice-to-Have, una por línea)</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={editNiceHaves}
                  onChange={(e) => setEditNiceHaves(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={handleSaveEdits}
                >
                  Guardar Ajustes
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setIsEditing(false)}
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
