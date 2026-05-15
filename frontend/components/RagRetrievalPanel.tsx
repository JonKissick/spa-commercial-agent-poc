import { useState } from "react";
import { ANALYSIS_SECTIONS, APPROVAL_STATUSES, KNOWLEDGE_TYPES, QUALITY_LABELS } from "@/lib/knowledge";
import { retrieveRag } from "@/lib/api";
import type { RetrievalResult } from "@/lib/types";
import JsonBlock from "./JsonBlock";
import StatusBadge from "./StatusBadge";

export default function RagRetrievalPanel() {
  const [query, setQuery] = useState("pricing formula model input");
  const [topK, setTopK] = useState(5);
  const [knowledgeType, setKnowledgeType] = useState("");
  const [commodity, setCommodity] = useState("lng");
  const [contractType, setContractType] = useState("spa");
  const [analysisSection, setAnalysisSection] = useState("");
  const [approvalStatus, setApprovalStatus] = useState("");
  const [qualityLabel, setQualityLabel] = useState("");
  const [results, setResults] = useState<RetrievalResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function submit() {
    const filters: Record<string, string> = {};
    if (knowledgeType) filters.knowledge_type = knowledgeType;
    if (commodity) filters.commodity = commodity;
    if (contractType) filters.contract_type = contractType;
    if (analysisSection) filters.analysis_section = analysisSection;
    if (approvalStatus) filters.approval_status = approvalStatus;
    if (qualityLabel) filters.quality_label = qualityLabel;
    setError(null);
    setIsLoading(true);
    try {
      setResults(await retrieveRag({ query, top_k: topK, filters }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retrieval failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return <div className="panel-stack"><section className="card wide"><div className="card-header compact"><div><h2>RAG Retrieval Test</h2><p className="quiet">Debug local keyword retrieval before relying on RAG-aware analysis.</p></div><StatusBadge label="keyword" /></div><div className="form-grid"><label className="full"><span>Query</span><input value={query} onChange={(event) => setQuery(event.target.value)} /></label><label><span>Top K</span><input type="number" min={1} max={20} value={topK} onChange={(event) => setTopK(Number(event.target.value))} /></label><label><span>Knowledge type</span><select value={knowledgeType} onChange={(event) => setKnowledgeType(event.target.value)}><option value="">Any</option>{KNOWLEDGE_TYPES.map((x) => <option key={x}>{x}</option>)}</select></label><label><span>Commodity</span><input value={commodity} onChange={(event) => setCommodity(event.target.value)} /></label><label><span>Contract type</span><input value={contractType} onChange={(event) => setContractType(event.target.value)} /></label><label><span>Analysis section</span><select value={analysisSection} onChange={(event) => setAnalysisSection(event.target.value)}><option value="">Any</option>{ANALYSIS_SECTIONS.map((x) => <option key={x}>{x}</option>)}</select></label><label><span>Approval status</span><select value={approvalStatus} onChange={(event) => setApprovalStatus(event.target.value)}><option value="">Any</option>{APPROVAL_STATUSES.map((x) => <option key={x}>{x}</option>)}</select></label><label><span>Quality label</span><select value={qualityLabel} onChange={(event) => setQualityLabel(event.target.value)}><option value="">Any</option>{QUALITY_LABELS.map((x) => <option key={x}>{x}</option>)}</select></label></div><button className="primary-button" disabled={isLoading || !query} onClick={submit} type="button">{isLoading ? "Retrieving..." : "Run Retrieval"}</button>{error && <p className="error-text standalone">{error}</p>}</section><section className="card wide"><div className="card-header compact"><h3>Retrieval Results</h3><StatusBadge label={`${results.length} results`} /></div><div className="register-list">{results.map((result) => <article className="register-item" key={result.chunk_id}><div className="item-title"><strong>{result.title}</strong><StatusBadge label={result.knowledge_type} /><StatusBadge label={`score ${result.score}`} /></div><p>{result.text}</p>{result.warnings.length > 0 && <ul className="warning-list">{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}<JsonBlock value={{ metadata: result.metadata }} /></article>)}</div>{!results.length && <p className="quiet">No retrieval results yet.</p>}</section></div>;
}
