import React, { useState, useMemo } from 'react';
import { Search, ShieldAlert, Award, FileQuestion, Clock } from 'lucide-react';
import { RankedCandidateItem, Verdict } from '../types/api';

interface CandidateRankingTableProps {
  candidates: RankedCandidateItem[];
  selectedCandidateId: string | null;
  onSelectCandidate: (item: RankedCandidateItem) => void;
  isEvaluating: boolean;
}

export const CandidateRankingTable: React.FC<CandidateRankingTableProps> = ({
  candidates,
  selectedCandidateId,
  onSelectCandidate,
  isEvaluating,
}) => {
  const [filterVerdict, setFilterVerdict] = useState<Verdict | 'TODOS'>('TODOS');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredCandidates = useMemo(() => {
    return candidates.filter((c) => {
      // Filtro por veredicto
      if (filterVerdict !== 'TODOS' && c.evaluation.verdict !== filterVerdict) {
        return false;
      }
      // Filtro por búsqueda
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const name = c.contact_pii.full_name?.toLowerCase() || '';
        const file = c.source_file.toLowerCase();
        const candId = c.evaluation.candidate_id.toLowerCase();
        return name.includes(query) || file.includes(query) || candId.includes(query);
      }
      return true;
    });
  }, [candidates, filterVerdict, searchQuery]);

  const getVerdictBadgeClass = (v: Verdict) => {
    switch (v) {
      case 'ACEPTABLE':
        return 'badge-aceptable';
      case 'ACEPTABLE_CON_RESERVAS':
        return 'badge-con-reservas';
      case 'NO_ACEPTABLE':
        return 'badge-no-aceptable';
      default:
        return 'badge-neutral';
    }
  };

  const getScoreColorClass = (score: number) => {
    if (score >= 75) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
  };

  return (
    <div className="desk-panel" style={{ height: '100%', minHeight: 540 }}>
      <div className="panel-header">
        <div className="panel-title">
          <Award size={16} color="#1d4ed8" />
          <span>Ranking de Candidatos ({candidates.length})</span>
        </div>
        {candidates.length > 0 && (
          <span style={{ fontSize: '0.74rem', color: '#64748b' }} className="tabular">
            {filteredCandidates.length} mostrados
          </span>
        )}
      </div>

      <div style={{ padding: '12px 14px', borderBottom: '1px solid #e5e3dc', background: '#faf9f6' }}>
        {/* Barra de Búsqueda */}
        <div style={{ position: 'relative', marginBottom: 10 }}>
          <Search
            size={14}
            color="#94a3b8"
            style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }}
          />
          <input
            type="text"
            className="form-control"
            placeholder="Buscar por nombre, archivo o ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: 30, fontSize: '0.82rem' }}
          />
        </div>

        {/* Filtros por Veredicto */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {(['TODOS', 'ACEPTABLE', 'ACEPTABLE_CON_RESERVAS', 'NO_ACEPTABLE'] as const).map((v) => {
            const count =
              v === 'TODOS'
                ? candidates.length
                : candidates.filter((c) => c.evaluation.verdict === v).length;
            const active = filterVerdict === v;
            return (
              <button
                key={v}
                type="button"
                onClick={() => setFilterVerdict(v)}
                className={`btn btn-sm ${active ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.72rem', padding: '3px 8px' }}
              >
                <span>
                  {v === 'TODOS'
                    ? 'Todos'
                    : v === 'ACEPTABLE'
                    ? 'Aceptable'
                    : v === 'ACEPTABLE_CON_RESERVAS'
                    ? 'Con Reservas'
                    : 'No Aceptable'}
                </span>
                <span className="tabular" style={{ opacity: 0.85 }}>({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="ranking-table-wrapper" style={{ flex: 1 }}>
        {isEvaluating ? (
          <div style={{ padding: 20 }}>
            <div className="skeleton" style={{ height: 42, marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 42, marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 42, marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 42 }} />
          </div>
        ) : candidates.length === 0 ? (
          <div className="empty-state">
            <FileQuestion size={36} color="#94a3b8" style={{ margin: '0 auto 8px' }} />
            <p style={{ fontWeight: 600, color: '#475569' }}>Aún no se han evaluado candidatos</p>
            <span style={{ fontSize: '0.76rem', color: '#64748b' }}>
              Carga una vacante y uno o más CVs para generar el ranking determinista.
            </span>
          </div>
        ) : filteredCandidates.length === 0 ? (
          <div className="empty-state">
            <p>No hay candidatos que coincidan con los filtros aplicados.</p>
          </div>
        ) : (
          <table className="ranking-table">
            <thead>
              <tr>
                <th style={{ width: 44, textAlign: 'center' }}>#</th>
                <th>Candidato / Archivo</th>
                <th>Veredicto</th>
                <th style={{ width: 90 }}>Puntaje</th>
                <th style={{ width: 65, textAlign: 'right' }}>Tiempo</th>
              </tr>
            </thead>
            <tbody>
              {filteredCandidates.map((item) => {
                const isSelected =
                  selectedCandidateId === item.evaluation.candidate_id ||
                  selectedCandidateId === item.evaluation.evaluation_id;
                const hasSecurityAlert =
                  item.evaluation.security_flags?.prompt_injection_detected ||
                  item.evaluation.security_flags?.inconsistent_dates_warning;

                return (
                  <tr
                    key={item.evaluation.evaluation_id || item.evaluation.candidate_id}
                    className={`clickable ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectCandidate(item)}
                  >
                    <td style={{ textAlign: 'center', fontWeight: 700 }} className="tabular">
                      {item.rank}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontWeight: 600, color: '#1e293b' }}>
                          {item.contact_pii.full_name || item.evaluation.candidate_id}
                        </span>
                        {hasSecurityAlert && (
                          <span
                            title="Alerta de seguridad o inconsistencia de fechas detectada"
                            style={{ color: '#dc2626', display: 'inline-flex' }}
                          >
                            <ShieldAlert size={14} />
                          </span>
                        )}
                      </div>
                      <div
                        style={{
                          fontSize: '0.73rem',
                          color: '#64748b',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          maxWidth: 180,
                        }}
                      >
                        {item.source_file}
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${getVerdictBadgeClass(item.evaluation.verdict)}`}>
                        {item.evaluation.verdict === 'ACEPTABLE'
                          ? 'Aceptable'
                          : item.evaluation.verdict === 'ACEPTABLE_CON_RESERVAS'
                          ? 'Con Reservas'
                          : 'No Aceptable'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                        <strong
                          className="tabular"
                          style={{
                            fontSize: '0.94rem',
                            color:
                              item.evaluation.overall_score >= 75
                                ? '#047857'
                                : item.evaluation.overall_score >= 50
                                ? '#b45309'
                                : '#b91c1c',
                          }}
                        >
                          {item.evaluation.overall_score.toFixed(1)}
                        </strong>
                        <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>/100</span>
                      </div>
                      <div className="score-bar-track">
                        <div
                          className={`score-bar-fill ${getScoreColorClass(item.evaluation.overall_score)}`}
                          style={{ width: `${Math.min(100, item.evaluation.overall_score)}%` }}
                        />
                      </div>
                    </td>
                    <td style={{ textAlign: 'right', fontSize: '0.74rem', color: '#64748b' }} className="tabular">
                      {item.duration_seconds > 0 ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}>
                          <Clock size={11} />
                          {item.duration_seconds.toFixed(1)}s
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
