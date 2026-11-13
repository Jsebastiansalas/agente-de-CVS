import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { VacancyPanel } from './components/VacancyPanel';
import { BatchUploadPanel } from './components/BatchUploadPanel';
import { CandidateRankingTable } from './components/CandidateRankingTable';
import { CandidateDetailAudit } from './components/CandidateDetailAudit';
import { HistoryDrawer } from './components/HistoryDrawer';
import {
  VacancySchema,
  RankedCandidateItem,
  BatchEvaluationResult,
  UsageSummary,
} from './types/api';
import { checkHealth, fetchStoredEvaluations } from './services/api';
import { AlertCircle, Clock, Zap, DollarSign } from 'lucide-react';
import './styles/app.css';

export const App: React.FC = () => {
  const [apiOnline, setApiOnline] = useState<boolean>(true);
  const [currentVacancy, setCurrentVacancy] = useState<VacancySchema | null>(null);
  const [rawVacancyFile, setRawVacancyFile] = useState<File | null>(null);
  const [candidates, setCandidates] = useState<RankedCandidateItem[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<RankedCandidateItem | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [historyOpen, setHistoryOpen] = useState<boolean>(false);
  const [historyCount, setHistoryCount] = useState<number>(0);
  const [lastUsageSummary, setLastUsageSummary] = useState<UsageSummary | null>(null);
  const [batchErrors, setBatchErrors] = useState<Array<{ source_file: string; error: string }>>([]);
  const [lastDuration, setLastDuration] = useState<number | null>(null);

  const refreshHealth = useCallback(async () => {
    try {
      await checkHealth();
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    }
  }, []);

  const loadHistoryStats = useCallback(async () => {
    try {
      const items = await fetchStoredEvaluations(undefined, 100);
      setHistoryCount(items.length);
    } catch {
      // silencioso
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    loadHistoryStats();
    const timer = setInterval(refreshHealth, 20000);
    return () => clearInterval(timer);
  }, [refreshHealth, loadHistoryStats]);

  const handleEvaluationComplete = (result: BatchEvaluationResult) => {
    if (result.vacancy) {
      setCurrentVacancy(result.vacancy);
    }
    setCandidates(result.ranked_candidates);
    setBatchErrors(result.errors || []);
    setLastDuration(result.total_duration_seconds);
    setLastUsageSummary(result.usage_summary || null);

    if (result.ranked_candidates.length > 0) {
      setSelectedCandidate(result.ranked_candidates[0]);
    }
    loadHistoryStats();
  };

  const handleSelectStoredCandidate = (item: RankedCandidateItem) => {
    // Si no está en la lista actual, lo agregamos o lo seleccionamos directamente
    setSelectedCandidate(item);
    setCandidates((prev) => {
      const exists = prev.some(
        (c) => c.evaluation.evaluation_id === item.evaluation.evaluation_id
      );
      if (!exists) {
        return [item, ...prev];
      }
      return prev;
    });
  };

  return (
    <div className="app-shell">
      <Header
        apiOnline={apiOnline}
        onRefreshHealth={refreshHealth}
        onOpenHistory={() => setHistoryOpen(true)}
        totalEvaluationsCount={historyCount}
      />

      <main className="main-workspace">
        {/* Banda Superior: Vacante + Carga por lotes */}
        <section className="top-desk-band">
          <VacancyPanel
            currentVacancy={currentVacancy}
            onVacancyLoaded={(v) => setCurrentVacancy(v)}
            rawVacancyFile={rawVacancyFile}
            onRawVacancyFileChange={setRawVacancyFile}
          />
          <BatchUploadPanel
            currentVacancy={currentVacancy}
            rawVacancyFile={rawVacancyFile}
            onEvaluationComplete={handleEvaluationComplete}
            isEvaluating={isEvaluating}
            setIsEvaluating={setIsEvaluating}
          />
        </section>

        {/* Telemetría y errores de lote */}
        {(lastUsageSummary || (lastDuration !== null && lastDuration > 0) || batchErrors.length > 0) && (
          <div
            style={{
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: 8,
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 12,
              fontSize: '0.8rem',
            }}
          >
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
              {lastDuration !== null && lastDuration > 0 && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#334155' }}>
                  <Clock size={14} color="#64748b" />
                  <strong>Duración total:</strong> {lastDuration.toFixed(1)}s
                </span>
              )}
              {lastUsageSummary?.total_calls !== undefined && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#334155' }}>
                  <Zap size={14} color="#3b82f6" />
                  <strong>Llamadas LLM:</strong> {lastUsageSummary.total_calls}
                </span>
              )}
              {lastUsageSummary?.total_tokens !== undefined && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#334155' }}>
                  <strong>Tokens totales:</strong>{' '}
                  <span className="tabular">{lastUsageSummary.total_tokens.toLocaleString()}</span>
                </span>
              )}
              {lastUsageSummary?.total_estimated_cost_usd !== undefined && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#334155' }}>
                  <DollarSign size={14} color="#059669" />
                  <strong>Costo est.:</strong> ${lastUsageSummary.total_estimated_cost_usd.toFixed(4)} USD
                </span>
              )}
            </div>

            {batchErrors.length > 0 && (
              <div style={{ color: '#dc2626', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <AlertCircle size={15} />
                <span>{batchErrors.length} error(es) en archivos no procesados</span>
              </div>
            )}
          </div>
        )}

        {/* Zona Central Dual-Pane: 42% Ranking / 58% Dictamen */}
        <section className="dual-pane-container">
          <CandidateRankingTable
            candidates={candidates}
            selectedCandidateId={
              selectedCandidate?.evaluation.evaluation_id ||
              selectedCandidate?.evaluation.candidate_id ||
              null
            }
            onSelectCandidate={(item) => setSelectedCandidate(item)}
            isEvaluating={isEvaluating}
          />
          <CandidateDetailAudit
            selectedItem={selectedCandidate}
            onFeedbackSaved={loadHistoryStats}
          />
        </section>
      </main>

      {/* Cajón lateral deslizable de historial */}
      <HistoryDrawer
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelectStoredCandidate={handleSelectStoredCandidate}
      />
    </div>
  );
};
