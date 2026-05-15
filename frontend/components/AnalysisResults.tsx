import type {
  ClauseCoverageItem,
  CommercialEvaluationResponse,
  DealRecommendation,
  DocumentMetadata,
  MarketContextAssessment,
  OptionalityRegisterItem,
  PortfolioFitAssessment,
  ProvisionRegisterItem,
  ValuationInputItem,
  ValuationInputPack,
} from "@/lib/types";
import CommercialModelOutputs from "./CommercialModelOutputs";
import JsonBlock from "./JsonBlock";
import StatusBadge from "./StatusBadge";

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not identified";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function warningList(warnings?: string[]) {
  if (!warnings?.length) return null;
  return <ul className="warning-list">{warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>;
}

function DocumentMetadataCard({ metadata }: { metadata?: DocumentMetadata | null }) {
  if (!metadata) return null;
  return (
    <section className="card wide">
      <div className="card-header compact"><h3>Document Metadata</h3><StatusBadge label={metadata.storage_provider} /></div>
      <div className="data-grid">
        <div><span>Filename</span><strong>{metadata.original_filename}</strong></div>
        <div><span>Size</span><strong>{metadata.size_bytes.toLocaleString()} bytes</strong></div>
        <div><span>Checksum</span><strong className="mono">{metadata.checksum_sha256.slice(0, 18)}...</strong></div>
        <div><span>Encryption</span><strong>{metadata.encryption_status}</strong></div>
        <div><span>Retention</span><strong>{metadata.retention_policy}</strong></div>
        <div><span>Created</span><strong>{metadata.created_at}</strong></div>
      </div>
    </section>
  );
}

function RagContextCard({ result }: { result: CommercialEvaluationResponse }) {
  const summary = result.rag_context_summary;
  return (
    <section className="card wide">
      <div className="card-header compact">
        <div><h3>RAG Context Used</h3><p className="quiet">RAG guidance is not contract evidence.</p></div>
        <StatusBadge label={summary?.enabled ? "RAG enabled" : "No RAG context"} tone={summary?.items_used?.length ? "good" : "neutral"} />
      </div>
      {summary ? (
        <>
          <p className="callout">{summary.note}</p>
          {summary.warnings?.length ? warningList(summary.warnings) : null}
          <div className="register-list">
            {summary.items_used.map((item) => (
              <article className="register-item" key={item.chunk_id}>
                <div className="item-title"><strong>{item.title}</strong><StatusBadge label={item.knowledge_type} /><StatusBadge label={`score ${item.score}`} /></div>
                <p>{item.text_excerpt}</p>
                {warningList(item.warnings)}
              </article>
            ))}
          </div>
        </>
      ) : <p className="quiet">This response did not include RAG context. Enable RAG on the backend to use local guidance.</p>}
    </section>
  );
}

function ContractSummaryCard({ result }: { result: CommercialEvaluationResponse }) {
  const summary = result.contract_summary;
  return (
    <section className="card wide">
      <div className="card-header compact"><h3>Contract Summary</h3><StatusBadge label={summary.commodity ?? "commodity unknown"} /></div>
      <p>{summary.summary}</p>
      <div className="data-grid">
        <div><span>Seller</span><strong>{text(summary.seller)}</strong></div>
        <div><span>Buyer</span><strong>{text(summary.buyer)}</strong></div>
        <div><span>Term</span><strong>{text(summary.contract_term)}</strong></div>
        <div><span>Governing law</span><strong>{text(summary.governing_law)}</strong></div>
      </div>
      {summary.evidence?.length ? <JsonBlock value={summary.evidence} /> : null}
    </section>
  );
}

function ClauseCoverageTable({ items = [] }: { items?: ClauseCoverageItem[] }) {
  return (
    <section className="card wide">
      <div className="card-header compact"><h3>Clause Coverage</h3><StatusBadge label={`${items.length} categories`} /></div>
      <div className="table-wrap"><table><thead><tr><th>Category</th><th>Status</th><th>Evidence</th><th>Provisions</th><th>Warnings</th></tr></thead><tbody>{items.map((item) => (
        <tr key={item.category}><td>{item.label}</td><td><StatusBadge label={item.status} tone={item.status === "present" ? "good" : item.status === "weak_unclear" ? "warning" : "neutral"} /></td><td>{item.evidence_summary}</td><td>{item.provision_ids.join(", ") || "-"}</td><td>{item.warnings.join("; ") || "-"}</td></tr>
      ))}</tbody></table></div>
    </section>
  );
}

function ProvisionTable({ items }: { items: ProvisionRegisterItem[] }) {
  return (
    <section className="card wide"><div className="card-header compact"><h3>Provision Register</h3><StatusBadge label={`${items.length} items`} /></div>
      <div className="table-wrap"><table><thead><tr><th>ID</th><th>Category</th><th>Title</th><th>Meaning</th><th>Impact</th><th>Evidence</th><th>Warnings</th></tr></thead><tbody>{items.map((item) => (
        <tr key={item.id}><td>{item.id}</td><td>{item.category}</td><td>{item.title ?? "-"}</td><td>{item.commercial_meaning ?? item.interpretation ?? "-"}</td><td>{item.valuation_impact}</td><td>{item.evidence_status} / {item.confidence}</td><td>{item.warnings?.join("; ") || "-"}</td></tr>
      ))}</tbody></table></div>
    </section>
  );
}

function valuationEntries(pack: ValuationInputPack): [string, unknown][] {
  return Object.entries(pack).filter(([key]) => !["missing_analyst_assumptions", "missing_market_data", "missing_portfolio_data", "valuation_warnings", "evidence_status"].includes(key));
}

function ValuationPackCard({ pack }: { pack: ValuationInputPack }) {
  return (
    <section className="card wide"><div className="card-header compact"><h3>Valuation Input Pack</h3><StatusBadge label={pack.evidence_status ?? "inputs"} /></div>
      <div className="two-column-list">{valuationEntries(pack).map(([key, value]) => <div key={key}><span>{key}</span><JsonBlock value={value} /></div>)}</div>
      <div className="data-grid"><div><span>Analyst assumptions</span><ul>{pack.missing_analyst_assumptions?.map((x) => <li key={x}>{x}</li>)}</ul></div><div><span>Market data</span><ul>{pack.missing_market_data?.map((x) => <li key={x}>{x}</li>)}</ul></div><div><span>Portfolio data</span><ul>{pack.missing_portfolio_data?.map((x) => <li key={x}>{x}</li>)}</ul></div><div><span>Warnings</span><ul>{pack.valuation_warnings?.map((x) => <li key={x}>{x}</li>)}</ul></div></div>
    </section>
  );
}

function OptionalityTable({ items }: { items: OptionalityRegisterItem[] }) {
  return <section className="card wide"><div className="card-header compact"><h3>Optionality Register</h3><StatusBadge label={`${items.length} items`} /></div><div className="table-wrap"><table><thead><tr><th>ID</th><th>Option</th><th>Type</th><th>Method</th><th>Source</th><th>Evidence</th><th>Warnings</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.id}</td><td>{item.option_name}<p>{item.commercial_description}</p></td><td>{item.option_type ?? "-"}</td><td>{item.suggested_valuation_method ?? "-"}</td><td>{item.source_provision_ids?.join(", ") || "-"}</td><td>{item.evidence_status} / {item.confidence}</td><td>{item.warnings?.join("; ") || "-"}</td></tr>)}</tbody></table></div></section>;
}

function ContextCard({ title, assessment }: { title: string; assessment?: MarketContextAssessment | PortfolioFitAssessment }) {
  if (!assessment) return null;
  return <section className="card"><div className="card-header compact"><h3>{title}</h3><StatusBadge label={assessment.evidence_status} /></div><p>{assessment.summary}</p><JsonBlock value={assessment} /></section>;
}

function RecommendationCard({ recommendation }: { recommendation?: DealRecommendation }) {
  if (!recommendation) return null;
  return <section className="card"><div className="card-header compact"><h3>Recommendation Memo</h3><StatusBadge label={recommendation.recommendation} tone={recommendation.recommendation === "reject" ? "danger" : recommendation.recommendation === "insufficient_evidence" ? "warning" : "good"} /></div><p>{recommendation.memo}</p><h4>Conditions</h4><ul>{recommendation.key_conditions.map((item) => <li key={item}>{item}</li>)}</ul><h4>Risks</h4><ul>{recommendation.key_risks.map((item) => <li key={item}>{item}</li>)}</ul></section>;
}

export default function AnalysisResults({ result, onPrefillNpv }: { result: CommercialEvaluationResponse; onPrefillNpv?: () => void }) {
  const market = result.market_context_assessment ?? result.market_context;
  const portfolio = result.portfolio_fit_assessment ?? result.portfolio_fit;
  const recommendation = result.deal_recommendation ?? result.recommendation;

  return (
    <section className="results-stack" aria-label="Commercial evaluation results">
      <DocumentMetadataCard metadata={result.document_metadata} />
      <RagContextCard result={result} />
      <ContractSummaryCard result={result} />
      <ClauseCoverageTable items={result.clause_coverage} />
      <ProvisionTable items={result.provision_register} />
      <ValuationPackCard pack={result.valuation_input_pack} />
      <CommercialModelOutputs outputs={result.analysis_model_outputs} onPrefillNpv={onPrefillNpv} />
      <OptionalityTable items={result.optionality_register} />
      <div className="split-grid"><ContextCard title="Market Context" assessment={market} /><ContextCard title="Portfolio Fit" assessment={portfolio} /><RecommendationCard recommendation={recommendation} /></div>
      {result.limitations?.length ? <section className="card wide"><h3>Limitations</h3><ul>{result.limitations.map((item) => <li key={item}>{item}</li>)}</ul></section> : null}
    </section>
  );
}
