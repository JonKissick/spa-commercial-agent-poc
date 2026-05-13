import type { ContractSummary } from "@/lib/types";

interface ContractSummaryCardProps {
  summary: ContractSummary;
}

function valueOrPending(value?: string | null) {
  return value || "Not extracted in V1";
}

export default function ContractSummaryCard({ summary }: ContractSummaryCardProps) {
  return (
    <article className="card wide">
      <div className="card-header">
        <h2>Contract Summary</h2>
        <span className="badge">{summary.evidence[0]?.status ?? "pending"}</span>
      </div>
      <p>{summary.summary}</p>

      <div className="meta-grid">
        <div className="meta-item">
          <span className="meta-label">Seller</span>
          {valueOrPending(summary.seller)}
        </div>
        <div className="meta-item">
          <span className="meta-label">Buyer</span>
          {valueOrPending(summary.buyer)}
        </div>
        <div className="meta-item">
          <span className="meta-label">Commodity</span>
          {valueOrPending(summary.commodity)}
        </div>
        <div className="meta-item">
          <span className="meta-label">Governing law</span>
          {valueOrPending(summary.governing_law)}
        </div>
      </div>

      {summary.evidence.map((item) => (
        <div className="evidence-note" key={`${item.status}-${item.note}`}>
          <strong>{item.status}</strong>: {item.note}
          {item.source_excerpt && <p>{item.source_excerpt}</p>}
        </div>
      ))}
    </article>
  );
}
