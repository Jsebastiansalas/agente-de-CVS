import React, { useState } from 'react';
import { UploadCloud, FileText, Trash2, Play, Cpu, AlertTriangle, Layers } from 'lucide-react';
import { VacancySchema, BatchEvaluationResult } from '../types/api';
import { evaluateBatchCVs, evaluateSingleCV } from '../services/api';

interface BatchUploadPanelProps {
  currentVacancy: VacancySchema | null;
  rawVacancyFile: File | null;
  onEvaluationComplete: (result: BatchEvaluationResult) => void;
  isEvaluating: boolean;
  setIsEvaluating: (val: boolean) => void;
}

export const BatchUploadPanel: React.FC<BatchUploadPanelProps> = ({
  currentVacancy,
  rawVacancyFile,
  onEvaluationComplete,
  isEvaluating,
  setIsEvaluating,
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [concurrency, setConcurrency] = useState<number>(2);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFilesAdded = (incomingFiles: FileList | File[]) => {
    const validExtensions = ['.pdf', '.docx', '.txt', '.md', '.png', '.jpg', '.jpeg', '.webp'];
    const newFiles: File[] = [];

    Array.from(incomingFiles).forEach((f) => {
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      if (!validExtensions.includes(ext)) {
        setErrorMsg(`Extensión no permitida en "${f.name}". Formatos: ${validExtensions.join(', ')}`);
        return;
      }
      if (f.size > 10 * 1024 * 1024) {
        setErrorMsg(`"${f.name}" excede los 10 MB máximos.`);
        return;
      }
      newFiles.push(f);
    });

    setFiles((prev) => {
      const combined = [...prev, ...newFiles];
      if (combined.length > 50) {
        setErrorMsg('El límite máximo por lote es de 50 archivos.');
        return combined.slice(0, 50);
      }
      return combined;
    });
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    setFiles([]);
    setErrorMsg(null);
  };

  const handleRunEvaluation = async () => {
    if (files.length === 0) {
      setErrorMsg('Selecciona al menos un archivo de Hoja de Vida.');
      return;
    }
    if (!currentVacancy && !rawVacancyFile) {
      setErrorMsg('Debes ingresar o cargar primero el contrato de la vacante.');
      return;
    }

    setIsEvaluating(true);
    setErrorMsg(null);

    try {
      const vacancyPayload = currentVacancy
        ? { vacancyJson: JSON.stringify(currentVacancy) }
        : { vacancyFile: rawVacancyFile || undefined };

      if (files.length === 1) {
        // Modo individual mapeado al contrato de lote para consistencia en la UI
        const single = await evaluateSingleCV(files[0], vacancyPayload);
        const mappedBatch: BatchEvaluationResult = {
          vacancy: currentVacancy || {
            vacancy_id: 'vac_auto',
            title: single.evaluation.vacancy_title,
            seniority: 'NO_ESPECIFICADO',
            min_years_experience: 0,
            knockout_requirements: [],
            must_have_skills: [],
            nice_to_have_skills: [],
            required_languages: [],
            required_education: null,
            responsibilities: [],
          },
          ranked_candidates: [
            {
              rank: 1,
              source_file: single.source_file,
              evaluation: single.evaluation,
              contact_pii: single.contact_pii,
              duration_seconds: 0,
            },
          ],
          errors: [],
          total_duration_seconds: 0,
          usage_summary: {},
        };
        onEvaluationComplete(mappedBatch);
      } else {
        const batchRes = await evaluateBatchCVs(files, vacancyPayload, concurrency);
        onEvaluationComplete(batchRes);
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error inesperado durante la evaluación');
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="desk-panel">
      <div className="panel-header">
        <div className="panel-title">
          <UploadCloud size={16} color="#1d4ed8" />
          <span>2. Carga de CVs para Evaluación ({files.length}/50)</span>
        </div>
        {files.length > 0 && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={handleClearAll}
            disabled={isEvaluating}
            style={{ color: '#ef4444' }}
          >
            <Trash2 size={13} /> Limpiar todo
          </button>
        )}
      </div>

      <div className="panel-body">
        {/* Zona Drag & Drop */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files) handleFilesAdded(e.dataTransfer.files);
          }}
          style={{
            border: `2px dashed ${isDragging ? '#1d4ed8' : '#d8d5cb'}`,
            borderRadius: 8,
            padding: '18px 14px',
            textAlign: 'center',
            backgroundColor: isDragging ? '#eff6ff' : '#fbfbfa',
            cursor: 'pointer',
            transition: 'all 150ms ease',
          }}
          onClick={() => document.getElementById('cv-file-input')?.click()}
        >
          <UploadCloud size={28} color={isDragging ? '#1d4ed8' : '#64748b'} style={{ margin: '0 auto 6px' }} />
          <p style={{ fontSize: '0.86rem', fontWeight: 600, color: '#1e293b' }}>
            Arrastra aquí tus Hojas de Vida o haz clic para seleccionar
          </p>
          <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
            Formatos admitidos: PDF, DOCX, TXT, MD e Imágenes (PNG, JPG, WEBP) · Máx 10 MB c/u
          </span>
          <input
            id="cv-file-input"
            type="file"
            multiple
            style={{ display: 'none' }}
            accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp"
            onChange={(e) => {
              if (e.target.files) handleFilesAdded(e.target.files);
              e.target.value = '';
            }}
          />
        </div>

        {/* Lista de archivos en cola */}
        {files.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 6,
              }}
            >
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569' }}>
                ARCHIVOS EN COLA ({files.length})
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Cpu size={14} color="#64748b" />
                <label style={{ fontSize: '0.74rem', color: '#475569' }}>Concurrencia:</label>
                <select
                  value={concurrency}
                  onChange={(e) => setConcurrency(parseInt(e.target.value) || 1)}
                  disabled={isEvaluating}
                  style={{
                    padding: '2px 6px',
                    fontSize: '0.75rem',
                    borderRadius: 4,
                    border: '1px solid #cbd5e1',
                  }}
                >
                  {[1, 2, 3, 4, 5, 8, 10].map((num) => (
                    <option key={num} value={num}>
                      {num} {num === 1 ? 'hilo' : 'hilos'}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div
              style={{
                maxHeight: 110,
                overflowY: 'auto',
                border: '1px solid #e2e8f0',
                borderRadius: 6,
                background: '#fff',
                padding: '4px 8px',
              }}
            >
              {files.map((file, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '3px 0',
                    borderBottom: idx < files.length - 1 ? '1px solid #f1f5f9' : 'none',
                    fontSize: '0.76rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, overflow: 'hidden' }}>
                    <FileText size={13} color="#3b82f6" />
                    <span
                      style={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        maxWidth: 240,
                      }}
                    >
                      {file.name}
                    </span>
                    <span style={{ color: '#94a3b8' }} className="tabular">
                      ({(file.size / 1024).toFixed(0)} KB)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveFile(idx);
                    }}
                    disabled={isEvaluating}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      color: '#94a3b8',
                      padding: 2,
                    }}
                    title="Remover archivo"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="security-alert-box" style={{ marginTop: 10 }}>
            <AlertTriangle size={15} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Botón de Ejecutar */}
        <div style={{ marginTop: 14 }}>
          <button
            type="button"
            className="btn btn-primary"
            style={{ width: '100%', padding: '10px 14px', fontSize: '0.9rem' }}
            onClick={handleRunEvaluation}
            disabled={isEvaluating || files.length === 0}
          >
            {isEvaluating ? (
              <>
                <Layers size={16} className="animate-spin" />
                <span>Evaluando {files.length} Hojas de Vida con LangGraph...</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>Evaluar Lote ({files.length} CVs) con Gemini</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
