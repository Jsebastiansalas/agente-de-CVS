import React, { useState, useEffect } from 'react';
import { X, History, RefreshCw, FileText, ArrowRight } from 'lucide-react';
import { StoredEvaluation, RankedCandidateItem, Verdict } from '../types/api';
import { fetchStoredEvaluations } from '../services/api';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectStoredCandidate: (item: RankedCandidateItem) => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  onSelectStoredCandidate,
}) => {
  const [evaluations, setEvaluations] = useState<StoredEvaluation[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterVerdict, setFilterVerdict] = useState<Verdict | 'TODOS'>('TODOS');

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await fetchStoredEvaluations(filterVerdict, 50);
      setEvaluations(data);
    } catch (err) {
      console.error('Error al cargar historial', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen, filterVerdict]);

  if (!isOpen) return null;

  const handleInspect = (stored: StoredEvaluation, index: number) => {
    const item: RankedCandidateItem = {
      rank: index + 1,
      source_file: stored.source_file || stored.evaluation.candidate_id,
      evaluation: stored.evaluation,
      contact_pii: stored.contact_pii,
      duration_seconds: 0,
    };
    onSelectStoredCandidate(item);
    onClose();
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="panel-header" style={{ padding: '16px 20px' }}>
          <div className="panel-title">
            <History size={18} color="#1d4ed8" />
            <span>Historial de Evaluaciones Persistidas</span>
          </div>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={onClose}
            title="Cerrar panel"
          >
            <X size={18} />
          </button>
        </div>

        {/* Toolbar de filtros */}
        <div
          style={{
            padding: '10px 18px',
            background: '#f8fafc',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', gap: 6 }}>
            {(['TODOS', 'ACEPTABLE', 'ACEPTABLE_CON_RESERVAS', 'NO_ACEPTABLE'] as const).map((v) => (
              <button
                key={v}
                type="button"
                className={`btn btn-sm ${filterVerdict === v ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.7rem', padding: '2px 8px' }}
                onClick={() => setFilterVerdict(v)}
              >
                {v === 'TODOS' ? 'Todos' : v === 'ACEPTABLE' ? 'Aceptable' : v === 'ACEPTABLE_CON_RESERVAS' ? 'Reservas' : 'No Acept.'}
              </button>
            ))}
          </div>

          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={loadHistory}
            disabled={loading}
            title="Recargar historial"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Listado */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '14px 18px' }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div className="skeleton" style={{ height: 60 }} />
              <div className="skeleton" style={{ height: 60 }} />
              <div className="skeleton" style={{ height: 60 }} />
            </div>
          ) : evaluations.length === 0 ? (
            <div className="empty-state">
              <p>No hay evaluaciones guardadas con el filtro seleccionado.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {evaluations.map((item, idx) => {
                const { evaluation, contact_pii, source_file, created_at, latest_feedback } = item;
                const v = evaluation.verdict;
                return (
                  <div
                    key={evaluation.evaluation_id || idx}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: 8,
                      padding: 12,
                      background: '#fff',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6,
                      boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <FileText size={14} color="#3b82f6" />
                        <strong style={{ fontSize: '0.86rem', color: '#1e293b' }}>
                          {contact_pii.full_name || evaluation.candidate_id}
                        </strong>
                      </div>
                      <span
                        className={`badge ${
                          v === 'ACEPTABLE'
                            ? 'badge-aceptable'
                            : v === 'ACEPTABLE_CON_RESERVAS'
                            ? 'badge-con-reservas'
                            : 'badge-no-aceptable'
                        }`}
                        style={{ fontSize: '0.68rem' }}
                      >
                        {v}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.76rem', color: '#64748b' }}>
                      Vacante: <strong>{evaluation.vacancy_title}</strong> · Archivo: {source_file || 'N/A'}
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginTop: 4,
                        fontSize: '0.74rem',
                      }}
                    >
                      <span className="tabular" style={{ color: '#047857', fontWeight: 600 }}>
                        Score: {evaluation.overall_score.toFixed(1)}/100
                      </span>
                      <span style={{ color: '#94a3b8' }} className="tabular">
                        {created_at}
                      </span>
                    </div>

                    {latest_feedback && (
                      <div
                        style={{
                          fontSize: '0.72rem',
                          background: '#f8fafc',
                          padding: '4px 8px',
                          borderRadius: 4,
                          borderLeft: '2px solid #3b82f6',
                          color: '#475569',
                        }}
                      >
                        Dictamen humano: {latest_feedback.human_verdict} (
                        {latest_feedback.agrees_with_agent ? 'Conforme' : 'Corregido'})
                      </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '0.74rem', padding: '3px 8px' }}
                        onClick={() => handleInspect(item, idx)}
                      >
                        <span>Cargar en Mesa de Dictamen</span>
                        <ArrowRight size={12} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
