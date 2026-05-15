import { useState } from "react";
import { ANALYSIS_SECTIONS, APPROVAL_STATUSES, KNOWLEDGE_TYPES, QUALITY_LABELS } from "@/lib/knowledge";
import { ingestRagText } from "@/lib/api";
import type { IngestionResult } from "@/lib/types";
import StatusBadge from "./StatusBadge";

const EXAMPLES = {
  pricing: {
    title: "Good Pricing Analysis Rule",
    text: "For SPA pricing, map index, premium or discount, escalation, currency, review dates, and missing market curve requirements. Do not calculate NPV or fair value.",
    knowledge_type: "model_input_mapping_rule",
    analysis_section: "pricing",
  },
  optionality: {
    title: "Good Optionality Analysis Rule",
    text: "Identify destination, volume, make-up, carry-forward, and termination flexibility only when supported by contract text. Suggest a method and required data, but do not calculate option value.",
    knowledge_type: "valuation_methodology",
    analysis_section: "optionality",
  },
  recommendation: {
    title: "Trader-Ready Recommendation Checklist",
    text: "Recommendation memos should separate extracted facts, inferred commercial implications, missing assumptions, key risks, and negotiation conditions.",
    knowledge_type: "negotiation_playbook",
    analysis_section: "recommendation",
  },
  valuationPolicy: {
    title: "No Unsupported Valuation Claims Policy",
    text: "Do not state NPV, IRR, option value, fair value, expected profit, margin, trade P&L, or final valuation unless a validated model has been run outside this extraction workflow.",
    knowledge_type: "risk_policy",
    analysis_section: "risk",
  },
};

interface RagIngestPanelProps {
  onIngested: () => void;
}

export default function RagIngestPanel({ onIngested }: RagIngestPanelProps) {
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [knowledgeType, setKnowledgeType] = useState("model_input_mapping_rule");
  const [approvalStatus, setApprovalStatus] = useState("approved");
  const [approvedForRag, setApprovedForRag] = useState(true);
  const [owner, setOwner] = useState("commercial");
  const [confidentiality, setConfidentiality] = useState("internal");
  const [commodity, setCommodity] = useState("lng");
  const [contractType, setContractType] = useState("spa");
  const [dealType, setDealType] = useState("term");
  const [analysisSection, setAnalysisSection] = useState("valuation_input_pack");
  const [qualityLabel, setQualityLabel] = useState("good");
  const [tags, setTags] = useState("pricing, model-inputs");
  const [version, setVersion] = useState("v1");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [result, setResult] = useState<IngestionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  function quickFill(example: keyof typeof EXAMPLES) {
    const item = EXAMPLES[example];
    setTitle(item.title);
    setText(item.text);
    setKnowledgeType(item.knowledge_type);
    setAnalysisSection(item.analysis_section);
  }

  async function submit() {
    setError(null);
    setResult(null);
    setIsLoading(true);
    try {
      const response = await ingestRagText({
        text,
        metadata: {
          title,
          knowledge_type: knowledgeType,
          approval_status: approvalStatus,
          approved_for_rag: approvedForRag,
          owner,
          confidentiality,
          commodity,
          contract_type: contractType,
          deal_type: dealType,
          analysis_section: analysisSection,
          quality_label: qualityLabel,
          tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
          version,
          effective_date: effectiveDate || null,
        },
      });
      setResult(response);
      onIngested();
    } catch (err) {
      setError(err instanceof Error ? err.message : "RAG ingestion failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return <section className="card wide"><div className="card-header compact"><div><h2>RAG Ingest</h2><p className="quiet">Add local methodology, examples, feedback, glossary, and playbook text.</p></div><StatusBadge label="local index" /></div><div className="quick-actions"><button onClick={() => quickFill("pricing")} type="button">Good pricing analysis rule</button><button onClick={() => quickFill("optionality")} type="button">Good optionality analysis rule</button><button onClick={() => quickFill("recommendation")} type="button">Trader checklist</button><button onClick={() => quickFill("valuationPolicy")} type="button">No valuation claims policy</button></div><div className="form-grid"><label className="full"><span>Knowledge text</span><textarea value={text} onChange={(event) => setText(event.target.value)} rows={8} /></label><label><span>Title</span><input value={title} onChange={(event) => setTitle(event.target.value)} /></label><label><span>Knowledge type</span><select value={knowledgeType} onChange={(event) => setKnowledgeType(event.target.value)}>{KNOWLEDGE_TYPES.map((x) => <option key={x}>{x}</option>)}</select></label><label><span>Approval status</span><select value={approvalStatus} onChange={(event) => setApprovalStatus(event.target.value)}>{APPROVAL_STATUSES.map((x) => <option key={x}>{x}</option>)}</select></label><label className="checkbox-row"><input type="checkbox" checked={approvedForRag} onChange={(event) => setApprovedForRag(event.target.checked)} /> approved for RAG</label><label><span>Owner</span><input value={owner} onChange={(event) => setOwner(event.target.value)} /></label><label><span>Confidentiality</span><input value={confidentiality} onChange={(event) => setConfidentiality(event.target.value)} /></label><label><span>Commodity</span><input value={commodity} onChange={(event) => setCommodity(event.target.value)} /></label><label><span>Contract type</span><input value={contractType} onChange={(event) => setContractType(event.target.value)} /></label><label><span>Deal type</span><input value={dealType} onChange={(event) => setDealType(event.target.value)} /></label><label><span>Analysis section</span><select value={analysisSection} onChange={(event) => setAnalysisSection(event.target.value)}>{ANALYSIS_SECTIONS.map((x) => <option key={x}>{x}</option>)}</select></label><label><span>Quality label</span><select value={qualityLabel} onChange={(event) => setQualityLabel(event.target.value)}>{QUALITY_LABELS.map((x) => <option key={x}>{x}</option>)}</select></label><label><span>Tags</span><input value={tags} onChange={(event) => setTags(event.target.value)} /></label><label><span>Version</span><input value={version} onChange={(event) => setVersion(event.target.value)} /></label><label><span>Effective date</span><input value={effectiveDate} onChange={(event) => setEffectiveDate(event.target.value)} placeholder="YYYY-MM-DD" /></label></div><button className="primary-button" disabled={isLoading || !text || !title} onClick={submit} type="button">{isLoading ? "Ingesting..." : "Ingest Knowledge"}</button>{error && <p className="error-text standalone">{error}</p>}{result && <div className="success-box"><strong>Ingested {result.title}</strong><p>Knowledge ID: {result.knowledge_id}</p><p>Chunks created: {result.chunks_created}</p>{result.warnings.length > 0 && <ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}</div>}</section>;
}
