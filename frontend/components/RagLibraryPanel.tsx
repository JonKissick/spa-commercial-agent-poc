import { useMemo, useState } from "react";
import { ANALYSIS_SECTIONS, APPROVAL_STATUSES, KNOWLEDGE_TYPES, QUALITY_LABELS } from "@/lib/knowledge";
import type { KnowledgeDocumentMetadata } from "@/lib/types";
import MissingKnowledgeSuggestions from "./MissingKnowledgeSuggestions";
import StatusBadge from "./StatusBadge";

interface RagLibraryPanelProps {
  knowledge: KnowledgeDocumentMetadata[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}

function SelectFilter({ value, onChange, options, label }: { value: string; onChange: (value: string) => void; options: string[]; label: string }) {
  return <label><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}><option value="">All</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>;
}

export default function RagLibraryPanel({ knowledge, isLoading, error, onRefresh }: RagLibraryPanelProps) {
  const [search, setSearch] = useState("");
  const [knowledgeType, setKnowledgeType] = useState("");
  const [approvalStatus, setApprovalStatus] = useState("");
  const [analysisSection, setAnalysisSection] = useState("");
  const [qualityLabel, setQualityLabel] = useState("");

  const filtered = useMemo(() => knowledge.filter((item) => {
    const haystack = [item.title, item.knowledge_type, item.approval_status, item.analysis_section, item.quality_label, item.tags?.join(" ")].join(" ").toLowerCase();
    return (!search || haystack.includes(search.toLowerCase())) && (!knowledgeType || item.knowledge_type === knowledgeType) && (!approvalStatus || item.approval_status === approvalStatus) && (!analysisSection || item.analysis_section === analysisSection) && (!qualityLabel || item.quality_label === qualityLabel);
  }), [knowledge, search, knowledgeType, approvalStatus, analysisSection, qualityLabel]);

  return <div className="panel-stack"><div className="split-grid"><section className="card"><div className="card-header compact"><div><h2>RAG Library</h2><p className="quiet">Metadata-only view of ingested local RAG knowledge.</p></div><button className="secondary-button" onClick={onRefresh} type="button">Refresh</button></div>{error && <p className="error-text standalone">{error}</p>}<div className="filters"><label><span>Search</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="pricing, optionality, checklist" /></label><SelectFilter label="Knowledge type" value={knowledgeType} onChange={setKnowledgeType} options={KNOWLEDGE_TYPES} /><SelectFilter label="Approval" value={approvalStatus} onChange={setApprovalStatus} options={APPROVAL_STATUSES} /><SelectFilter label="Section" value={analysisSection} onChange={setAnalysisSection} options={ANALYSIS_SECTIONS} /><SelectFilter label="Quality" value={qualityLabel} onChange={setQualityLabel} options={QUALITY_LABELS} /></div></section><MissingKnowledgeSuggestions knowledge={knowledge} /></div><section className="card wide"><div className="card-header compact"><h3>Knowledge Documents</h3><StatusBadge label={isLoading ? "Loading" : `${filtered.length} shown`} /></div><div className="table-wrap"><table><thead><tr><th>Title</th><th>Type</th><th>Approval</th><th>RAG</th><th>Commodity</th><th>Contract</th><th>Deal</th><th>Section</th><th>Quality</th><th>Tags</th><th>Warnings</th><th>Created</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.knowledge_id}><td>{item.title}</td><td>{item.knowledge_type}</td><td>{item.approval_status}</td><td>{item.approved_for_rag ? "yes" : "no"}</td><td>{item.commodity ?? "-"}</td><td>{item.contract_type ?? "-"}</td><td>{item.deal_type ?? "-"}</td><td>{item.analysis_section ?? "-"}</td><td>{item.quality_label ?? "-"}</td><td>{item.tags?.join(", ")}</td><td>{item.warnings?.join("; ") || "-"}</td><td>{item.created_at}</td></tr>)}</tbody></table></div>{!filtered.length && <p className="quiet">No knowledge documents match the current filters.</p>}</section></div>;
}
