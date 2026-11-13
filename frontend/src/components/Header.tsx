import React from 'react';
import { Activity, Download, History, RefreshCw } from 'lucide-react';
import { getExportCsvUrl } from '../services/api';

interface HeaderProps {
  apiOnline: boolean;
  onRefreshHealth: () => void;
  onOpenHistory: () => void;
  totalEvaluationsCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  apiOnline,
  onRefreshHealth,
  onOpenHistory,
  totalEvaluationsCount,
}) => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <Activity size={20} color="#3b82f6" />
        <div>
          <h1>Agente Comparador de CVs vs. Vacante</h1>
        </div>
        <span className="header-subtitle">
          Mesa de Dictamen Auditable · LangGraph + Gemini
        </span>
      </div>

      <div className="header-actions">
        <button
          type="button"
          onClick={onRefreshHealth}
          className="status-pill"
          title="Verificar conexión con backend"
          style={{ background: 'transparent', cursor: 'pointer' }}
        >
          <span className={`status-dot ${apiOnline ? 'online' : 'offline'}`} />
          <span>{apiOnline ? 'API Conectada' : 'API Desconectada'}</span>
          <RefreshCw size={12} style={{ marginLeft: 2 }} />
        </button>

        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={onOpenHistory}
          title="Ver historial de evaluaciones guardadas"
        >
          <History size={14} />
          <span>Historial ({totalEvaluationsCount})</span>
        </button>

        <a
          href={getExportCsvUrl()}
          download="evaluaciones_cv.csv"
          className="btn btn-primary btn-sm"
          title="Descargar reporte completo en formato CSV"
        >
          <Download size={14} />
          <span>Exportar CSV</span>
        </a>
      </div>
    </header>
  );
};
