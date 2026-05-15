import type { CommercialEvaluationResponse, KnowledgeDocumentMetadata } from "@/lib/types";
import AnalysisResults from "./AnalysisResults";
import MissingKnowledgeSuggestions from "./MissingKnowledgeSuggestions";
import RagSummaryPanel from "./RagSummaryPanel";

interface AnalyzeContractPanelProps {
  file: File | null;
  result: CommercialEvaluationResponse | null;
  error: string | null;
  isLoading: boolean;
  knowledge: KnowledgeDocumentMetadata[];
  knowledgeError: string | null;
  knowledgeLoading: boolean;
  onFileChange: (file: File | null) => void;
  onAnalyze: () => void;
  onPrefillNpv: () => void;
}

export default function AnalyzeContractPanel({ file, result, error, isLoading, knowledge, knowledgeError, knowledgeLoading, onFileChange, onAnalyze, onPrefillNpv }: AnalyzeContractPanelProps) {
  return (
    <div className="panel-stack">
      <section className="card wide">
        <div className="card-header compact">
          <div><h2>Analyze Contract</h2><p className="quiet">Upload a text-based SPA PDF and run the commercial extraction pipeline.</p></div>
          <span className="status-badge">PDF only</span>
        </div>
        <div className="upload-row">
          <label className="file-input"><span>SPA PDF</span><input type="file" accept="application/pdf" onChange={(event) => onFileChange(event.target.files?.[0] ?? null)} /></label>
          <button className="primary-button" disabled={!file || isLoading} onClick={onAnalyze} type="button">{isLoading ? "Analyzing..." : "Run Analysis"}</button>
        </div>
        {file && <p className="quiet">Selected: {file.name}</p>}
        {error && <p className="error-text standalone">{error}</p>}
      </section>
      <div className="split-grid"><RagSummaryPanel knowledge={knowledge} isLoading={knowledgeLoading} error={knowledgeError} /><MissingKnowledgeSuggestions knowledge={knowledge} /></div>
      {isLoading && <div className="status-panel">Analyzing uploaded PDF...</div>}
      {result && <AnalysisResults result={result} onPrefillNpv={onPrefillNpv} />}
    </div>
  );
}
