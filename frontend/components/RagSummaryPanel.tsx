import { countBy } from "@/lib/knowledge";
import type { KnowledgeDocumentMetadata } from "@/lib/types";
import StatusBadge from "./StatusBadge";

interface RagSummaryPanelProps {
  knowledge: KnowledgeDocumentMetadata[];
  isLoading?: boolean;
  error?: string | null;
}

function renderCounts(counts: Record<string, number>) {
  return Object.entries(counts).map(([key, count]) => (
    <span className="metric-chip" key={key}>
      {key}: {count}
    </span>
  ));
}

export default function RagSummaryPanel({ knowledge, isLoading = false, error = null }: RagSummaryPanelProps) {
  const byType = countBy(knowledge, "knowledge_type");
  const byApproval = countBy(knowledge, "approval_status");
  const recent = [...knowledge].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 4);

  return (
    <section className="card">
      <div className="card-header compact">
        <div>
          <h3>RAG Knowledge Summary</h3>
          <p className="quiet">Local guidance available to RAG-aware analysis.</p>
        </div>
        <StatusBadge label={isLoading ? "Loading" : `${knowledge.length} docs`} tone={knowledge.length ? "good" : "warning"} />
      </div>
      {error && <p className="error-text standalone">{error}</p>}
      {!knowledge.length && !isLoading && <p className="callout warning">No RAG knowledge is loaded yet. Analysis can still run, but RAG-aware guidance has nothing to retrieve.</p>}
      <div className="metric-row">{renderCounts(byType)}</div>
      <div className="metric-row">{renderCounts(byApproval)}</div>
      {recent.length > 0 && (
        <div className="mini-list">
          {recent.map((item) => (
            <div key={item.knowledge_id}>
              <strong>{item.title}</strong>
              <span>{item.knowledge_type} · {item.approval_status}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
