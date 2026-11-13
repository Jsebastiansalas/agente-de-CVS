import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Mail,
  Phone,
  MapPin,
  Copy,
  Check,
  CheckCircle,
  XCircle,
  HelpCircle,
  MessageSquare,
  Send,
  UserCheck,
} from 'lucide-react';
import { RankedCandidateItem, Verdict, FeedbackRecord } from '../types/api';
import { submitEvaluationFeedback, getFeedbackList } from '../services/api';

interface CandidateDetailAuditProps {
  selectedItem: RankedCandidateItem | null;
  onFeedbackSaved?: () => void;
}

export const CandidateDetailAudit: React.FC<CandidateDetailAuditProps> = ({
  selectedItem,
  onFeedbackSaved,
}) => {
  const [copiedPii, setCopiedPii] = useState(false);
  const [feedbackAgrees, setFeedbackAgrees] = useState<boolean>(true);
  const [humanVerdict, setHumanVerdict] = useState<Verdict>('ACEPTABLE');
  const [feedbackComment, setFeedbackComment] = useState('');
  const [savingFeedback, setSavingFeedback] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);
  const [feedbackHistory, setFeedbackHistory] = useState<FeedbackRecord[]>([]);

  useEffect(() => {
    if (selectedItem?.evaluation?.evaluation_id) {
      setFeedbackAgrees(true);
      setHumanVerdict(selectedItem.evaluation.verdict);
      setFeedbackComment('');
      setFeedbackSuccess(false);

      getFeedbackList(selectedItem.evaluation.evaluation_id)
        .then(setFeedbackHistory)
        .catch(() => setFeedbackHistory([]));
    }
  }, [selectedItem?.evaluation?.evaluation_id]);

  if (!selectedItem) {
    return (
      <div className="desk-panel" style={{ height: '100%', minHeight: 540 }}>
        <div className="empty-state" style={{ margin: 'auto' }}>
          <UserCheck size={44} color="#cbd5e1" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '1rem', color: '#475569', marginBottom: 6 }}>
            Acta de Dictamen Auditable
          </h3>
          <p style={{ maxWidth: 360, margin: '0 auto', fontSize: '0.82rem', color: '#64748b' }}>
            Selecciona a un candidato de la tabla de la izquierda para examinar sus evidencias textuales,
            desglose de puntajes y registrar dictamen humano.
          </p>
        </div>
      </div>
    );
  }

  const { evaluation, contact_pii, source_file } = selectedItem;

  const handleCopyPii = () => {
    const text = `Nombre: ${contact_pii.full_name || 'N/A'}\nEmail: ${contact_pii.email || 'N/A'}\nTeléfono: ${contact_pii.phone || 'N/A'}\nUbicación: ${contact_pii.location || 'N/A'}`;
    navigator.clipboard.writeText(text);
    setCopiedPii(true);
    setTimeout(() => setCopiedPii(false), 2000);
  };

  const handleSendFeedback = async () => {
    if (!evaluation.evaluation_id) return;
    setSavingFeedback(true);
    try {
      await submitEvaluationFeedback(evaluation.evaluation_id, {
        agrees_with_agent: feedbackAgrees,
        human_verdict: humanVerdict,
        comment: feedbackComment.trim(),
      });
      setFeedbackSuccess(true);
      const updatedList = await getFeedbackList(evaluation.evaluation_id);
      setFeedbackHistory(updatedList);
      if (onFeedbackSaved) onFeedbackSaved();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al guardar feedback');
    } finally {
      setSavingFeedback(false);
    }
  };

  return (
    <div className="desk-panel" style={{ height: '100%', minHeight: 540, overflowY: 'auto' }}>
      {/* Encabezado del Acta */}
      <div className="panel-header" style={{ alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: '1.05rem', color: '#0f172a' }}>
              {contact_pii.full_name || evaluation.candidate_id}
            </h2>
            <span
              className={`badge ${
                evaluation.verdict === 'ACEPTABLE'
                  ? 'badge-aceptable'
                  : evaluation.verdict === 'ACEPTABLE_CON_RESERVAS'
                  ? 'badge-con-reservas'
                  : 'badge-no-aceptable'
              }`}
              style={{ fontSize: '0.78rem' }}
            >
              {evaluation.verdict === 'ACEPTABLE'
                ? 'Aceptable'
                : evaluation.verdict === 'ACEPTABLE_CON_RESERVAS'
                ? 'Aceptable con Reservas'
                : 'No Aceptable'}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }} className="tabular">
            Archivo: {source_file} · ID Evaluación: {evaluation.evaluation_id}
          </span>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, justifyContent: 'flex-end' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 700, color: '#1d4ed8' }} className="tabular">
              {evaluation.overall_score.toFixed(1)}
            </span>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>/100</span>
          </div>
          <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase' }}>
            Puntaje Determinista
          </span>
        </div>
      </div>

      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Alerta de Seguridad (si aplica) */}
        {(evaluation.security_flags?.prompt_injection_detected ||
          evaluation.security_flags?.inconsistent_dates_warning) && (
          <div className="security-alert-box">
            <ShieldAlert size={18} style={{ flexShrink: 0, marginTop: 1 }} />
            <div>
              <strong>Alerta de Seguridad e Integridad en el CV:</strong>
              <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                {evaluation.security_flags.prompt_injection_detected && (
                  <li>Sospecha de inyección de prompt o instrucciones maliciosas en el documento.</li>
                )}
                {evaluation.security_flags.inconsistent_dates_warning && (
                  <li>Inconsistencias cronológicas o fechas solapadas detectadas en la experiencia.</li>
                )}
                {evaluation.security_flags.details?.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Tarjeta de Contacto PII (Anonimizada en evaluación, visible para contacto) */}
        <div
          style={{
            background: '#fafaf9',
            border: '1px solid #e7e5e4',
            borderRadius: 6,
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 12,
            fontSize: '0.8rem',
          }}
        >
          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', color: '#44403c' }}>
            {contact_pii.email && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <Mail size={13} color="#64748b" />
                <a href={`mailto:${contact_pii.email}`} style={{ color: '#1d4ed8', textDecoration: 'none' }}>
                  {contact_pii.email}
                </a>
              </span>
            )}
            {contact_pii.phone && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <Phone size={13} color="#64748b" />
                <span>{contact_pii.phone}</span>
              </span>
            )}
            {contact_pii.location && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <MapPin size={13} color="#64748b" />
                <span>{contact_pii.location}</span>
              </span>
            )}
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleCopyPii}
            style={{ fontSize: '0.74rem' }}
          >
            {copiedPii ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
            <span>{copiedPii ? 'Copiado' : 'Copiar PII'}</span>
          </button>
        </div>

        {/* Resumen Ejecutivo */}
        <div>
          <h4 style={{ fontSize: '0.84rem', color: '#334155', marginBottom: 6, textTransform: 'uppercase' }}>
            Resumen Ejecutivo
          </h4>
          <p
            style={{
              fontSize: '0.86rem',
              color: '#1e293b',
              lineHeight: 1.5,
              background: '#ffffff',
              padding: '10px 12px',
              borderRadius: 6,
              border: '1px solid #e2e8f0',
            }}
          >
            {evaluation.executive_summary}
          </p>
        </div>

        {/* Desglose Ponderado de Categorías */}
        <div>
          <h4 style={{ fontSize: '0.84rem', color: '#334155', marginBottom: 8, textTransform: 'uppercase' }}>
            Ponderación por Categorías (Scoring Determinista)
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[
              {
                label: 'Experiencia Relevante (40%)',
                data: evaluation.category_scores.relevant_experience,
              },
              {
                label: 'Habilidades Obligatorias (35%)',
                data: evaluation.category_scores.must_have_skills,
              },
              {
                label: 'Habilidades Deseables (15%)',
                data: evaluation.category_scores.nice_to_have_skills,
              },
              {
                label: 'Educación e Idiomas (10%)',
                data: evaluation.category_scores.education_and_languages,
              },
            ].map((cat, i) => (
              <div
                key={i}
                style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: 6,
                  padding: 8,
                  fontSize: '0.78rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, color: '#334155' }}>{cat.label}</span>
                  <span style={{ fontWeight: 700, color: '#1d4ed8' }} className="tabular">
                    {cat.data.score.toFixed(0)}/100 · (+{cat.data.weighted.toFixed(1)} pts)
                  </span>
                </div>
                <div className="score-bar-track">
                  <div
                    className="score-bar-fill"
                    style={{
                      width: `${Math.min(100, cat.data.score)}%`,
                      backgroundColor: cat.data.score >= 70 ? '#059669' : cat.data.score >= 40 ? '#d97706' : '#dc2626',
                    }}
                  />
                </div>
                <span style={{ display: 'block', fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>
                  {cat.data.justification}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Tabla de Requisitos Knock-Out */}
        <div>
          <h4 style={{ fontSize: '0.84rem', color: '#334155', marginBottom: 8, textTransform: 'uppercase' }}>
            Requisitos Excluyentes (Knock-Out)
          </h4>
          {evaluation.knockout_requirements.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Sin requisitos knock-out definidos.</p>
          ) : (
            <div style={{ border: '1px solid #e2e8f0', borderRadius: 6, overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                    <th style={{ padding: '8px 10px', width: '35%' }}>Requisito</th>
                    <th style={{ padding: '8px 10px', width: '20%' }}>Estado</th>
                    <th style={{ padding: '8px 10px' }}>Evidencia / Cita del CV</th>
                  </tr>
                </thead>
                <tbody>
                  {evaluation.knockout_requirements.map((kr, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px 10px', fontWeight: 600 }}>{kr.requirement}</td>
                      <td style={{ padding: '8px 10px' }}>
                        {kr.status === 'CUMPLIDO' ? (
                          <span className="badge badge-aceptable" style={{ fontSize: '0.7rem' }}>
                            <CheckCircle size={11} /> CUMPLIDO
                          </span>
                        ) : kr.status === 'NO_CUMPLIDO' ? (
                          <span className="badge badge-no-aceptable" style={{ fontSize: '0.7rem' }}>
                            <XCircle size={11} /> NO CUMPLIDO
                          </span>
                        ) : (
                          <span className="badge badge-con-reservas" style={{ fontSize: '0.7rem' }}>
                            <HelpCircle size={11} /> NO MENCIONADO
                          </span>
                        )}
                        {kr.calculated_months !== undefined && kr.calculated_months !== null && (
                          <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 2 }} className="tabular">
                            {kr.calculated_months} meses
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '8px 10px' }}>
                        {kr.evidence ? (
                          <div className="evidence-quote">"{kr.evidence}"</div>
                        ) : (
                          <span style={{ color: '#94a3b8', fontSize: '0.74rem' }}>Sin evidencia en CV</span>
                        )}
                        {kr.notes && (
                          <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'block' }}>
                            {kr.notes}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Matriz de Habilidades y Evidencias */}
        <div>
          <h4 style={{ fontSize: '0.84rem', color: '#334155', marginBottom: 8, textTransform: 'uppercase' }}>
            Matriz de Habilidades con Citas Verbatim
          </h4>
          <div style={{ border: '1px solid #e2e8f0', borderRadius: 6, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                  <th style={{ padding: '8px 10px', width: '22%' }}>Habilidad</th>
                  <th style={{ padding: '8px 10px', width: '15%' }}>Tipo</th>
                  <th style={{ padding: '8px 10px', width: '20%' }}>Nivel Coincidencia</th>
                  <th style={{ padding: '8px 10px' }}>Cita Textual y Justificación</th>
                </tr>
              </thead>
              <tbody>
                {evaluation.skills_matrix.map((sk, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '8px 10px', fontWeight: 600 }}>{sk.skill}</td>
                    <td style={{ padding: '8px 10px' }}>
                      <span
                        className="badge badge-neutral"
                        style={{
                          fontSize: '0.68rem',
                          background: sk.skill_type === 'MUST_HAVE' ? '#eff6ff' : '#f8fafc',
                          color: sk.skill_type === 'MUST_HAVE' ? '#1d4ed8' : '#475569',
                        }}
                      >
                        {sk.skill_type}
                      </span>
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          color:
                            sk.match_level === 'EXACTO'
                              ? '#047857'
                              : sk.match_level === 'PARCIAL_EQUIVALENTE'
                              ? '#b45309'
                              : '#64748b',
                        }}
                      >
                        {sk.match_level}
                      </span>
                      {sk.proven_in_work_experience && (
                        <div style={{ fontSize: '0.68rem', color: '#047857', fontWeight: 500 }}>
                          ✓ En cargo laboral
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      {sk.evidence && <div className="evidence-quote">"{sk.evidence}"</div>}
                      <span style={{ fontSize: '0.72rem', color: '#475569', display: 'block' }}>
                        {sk.explanation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Brechas y Preguntas de Entrevista */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 6, padding: 10 }}>
            <h5 style={{ fontSize: '0.78rem', color: '#92400e', marginBottom: 6, textTransform: 'uppercase' }}>
              Brechas Detectadas
            </h5>
            {evaluation.detected_gaps.length > 0 ? (
              <ul style={{ margin: '0 0 0 16px', padding: 0, fontSize: '0.78rem', color: '#78350f' }}>
                {evaluation.detected_gaps.map((gap, i) => (
                  <li key={i}>{gap}</li>
                ))}
              </ul>
            ) : (
              <span style={{ fontSize: '0.76rem', color: '#92400e' }}>Ninguna brecha mayor detectada.</span>
            )}
          </div>

          <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 6, padding: 10 }}>
            <h5 style={{ fontSize: '0.78rem', color: '#1e40af', marginBottom: 6, textTransform: 'uppercase' }}>
              Preguntas Sugeridas de Entrevista
            </h5>
            {evaluation.suggested_interview_questions.length > 0 ? (
              <ul style={{ margin: '0 0 0 16px', padding: 0, fontSize: '0.78rem', color: '#1e3a8a' }}>
                {evaluation.suggested_interview_questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            ) : (
              <span style={{ fontSize: '0.76rem', color: '#1e40af' }}>Sin preguntas adicionales sugeridas.</span>
            )}
          </div>
        </div>

        {/* Módulo Human-in-the-Loop: Feedback y Auditoría */}
        <div
          style={{
            background: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: 8,
            padding: 14,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <MessageSquare size={16} color="#1d4ed8" />
            <h4 style={{ fontSize: '0.86rem', color: '#0f172a' }}>
              Dictamen y Auditoría Humana (Human-in-the-Loop)
            </h4>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12 }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>¿De acuerdo con el agente?</span>
            <button
              type="button"
              className={`btn btn-sm ${feedbackAgrees ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => {
                setFeedbackAgrees(true);
                setHumanVerdict(evaluation.verdict);
              }}
            >
              Sí, conforme
            </button>
            <button
              type="button"
              className={`btn btn-sm ${!feedbackAgrees ? 'btn-danger' : 'btn-secondary'}`}
              onClick={() => setFeedbackAgrees(false)}
            >
              No, corregir veredicto
            </button>
          </div>

          {!feedbackAgrees && (
            <div className="form-group" style={{ maxWidth: 300 }}>
              <label className="form-label">Nuevo Veredicto Humano Asignado:</label>
              <select
                className="form-select"
                value={humanVerdict}
                onChange={(e) => setHumanVerdict(e.target.value as Verdict)}
              >
                <option value="ACEPTABLE">ACEPTABLE</option>
                <option value="ACEPTABLE_CON_RESERVAS">ACEPTABLE_CON_RESERVAS</option>
                <option value="NO_ACEPTABLE">NO_ACEPTABLE</option>
              </select>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Comentarios o Justificación de Auditoría:</label>
            <textarea
              className="form-textarea"
              rows={2}
              placeholder="Anota tus observaciones técnicas o motivo del cambio de veredicto..."
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={handleSendFeedback}
              disabled={savingFeedback}
            >
              <Send size={13} />
              <span>{savingFeedback ? 'Guardando dictamen...' : 'Registrar Dictamen'}</span>
            </button>

            {feedbackSuccess && (
              <span style={{ color: '#059669', fontSize: '0.76rem', fontWeight: 600 }}>
                ✓ Dictamen registrado en base de datos
              </span>
            )}
          </div>

          {/* Historial de feedbacks sobre este candidato */}
          {feedbackHistory.length > 0 && (
            <div style={{ marginTop: 14, borderTop: '1px solid #f1f5f9', paddingTop: 10 }}>
              <span style={{ fontSize: '0.74rem', fontWeight: 600, color: '#64748b' }}>
                HISTORIAL DE REVISIONES HUMANAS ({feedbackHistory.length}):
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
                {feedbackHistory.map((fb, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: '#f8fafc',
                      padding: '6px 10px',
                      borderRadius: 4,
                      fontSize: '0.74rem',
                      border: '1px solid #e2e8f0',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                      <strong>
                        {fb.agrees_with_agent ? 'De acuerdo con el agente' : `Corregido a: ${fb.human_verdict}`}
                      </strong>
                      <span style={{ color: '#94a3b8' }} className="tabular">
                        {fb.created_at}
                      </span>
                    </div>
                    {fb.comment && <div style={{ color: '#475569' }}>"{fb.comment}"</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
