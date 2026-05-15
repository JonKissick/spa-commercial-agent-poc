import { API_BASE_URL } from "@/lib/api";
import type { HealthResponse, KnowledgeDocumentMetadata, SystemStatus } from "@/lib/types";
import StatusBadge from "./StatusBadge";

interface SystemStatusPanelProps {
  health: HealthResponse | null;
  status: SystemStatus | null;
  knowledge: KnowledgeDocumentMetadata[];
  error: string | null;
  onRefresh: () => void;
}

export default function SystemStatusPanel({ health, status, knowledge, error, onRefresh }: SystemStatusPanelProps) {
  return <div className="panel-stack"><section className="card wide"><div className="card-header compact"><div><h2>System Status</h2><p className="quiet">Non-secret local POC configuration and availability.</p></div><button className="secondary-button" onClick={onRefresh} type="button">Refresh</button></div>{error && <p className="error-text standalone">{error}</p>}<div className="data-grid"><div><span>Backend health</span><strong>{health?.status ?? "unknown"}</strong></div><div><span>API base URL</span><strong>{API_BASE_URL}</strong></div><div><span>LLM provider</span><strong>{status?.llm_provider ?? "unknown"}</strong></div><div><span>Document store</span><strong>{status?.document_store_provider ?? "unknown"}</strong></div><div><span>RAG provider</span><strong>{status?.rag_provider ?? "unknown"}</strong></div><div><span>RAG enabled</span><strong>{status?.rag_enabled ? "yes" : "no"}</strong></div><div><span>Knowledge documents</span><strong>{knowledge.length}</strong></div><div><span>Mode</span><strong>{status?.local_dev_mode ? "local dev" : "unknown"}</strong></div></div>{status?.note && <p className="callout">{status.note}</p>}</section><section className="card wide"><div className="card-header compact"><h3>Caveats</h3><StatusBadge label="POC only" tone="warning" /></div><ul className="text-list"><li>Local POC only.</li><li>RAG endpoints are not production-secure without auth.</li><li>Local document storage is development-only.</li><li>RAG guidance is not contract evidence.</li><li>No final valuation, DCF, NPV, IRR, or option valuation is calculated.</li></ul></section></div>;
}
