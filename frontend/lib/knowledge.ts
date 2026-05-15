import type { KnowledgeDocumentMetadata } from "./types";

export const KNOWLEDGE_TYPES = [
  "contract_reference",
  "internal_procedure",
  "valuation_methodology",
  "market_fundamentals",
  "portfolio_strategy",
  "good_analysis_example",
  "bad_analysis_example",
  "corrected_analysis_example",
  "reviewer_feedback",
  "taxonomy_guidance",
  "model_input_mapping_rule",
  "negotiation_playbook",
  "glossary",
  "risk_policy",
  "other",
];

export const APPROVAL_STATUSES = ["approved", "draft", "deprecated", "superseded"];
export const ANALYSIS_SECTIONS = ["pricing", "volume", "valuation_input_pack", "optionality", "risk", "recommendation"];
export const QUALITY_LABELS = ["good", "bad", "corrected", "reference"];

function textFor(item: KnowledgeDocumentMetadata): string {
  return [item.title, item.knowledge_type, item.analysis_section, item.quality_label, item.tags?.join(" ")]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function hasAny(items: KnowledgeDocumentMetadata[], predicate: (item: KnowledgeDocumentMetadata) => boolean): boolean {
  return items.some(predicate);
}

export function getMissingKnowledgeSuggestions(items: KnowledgeDocumentMetadata[]): string[] {
  const suggestions: string[] = [];

  if (!hasAny(items, (item) => ["valuation_methodology", "model_input_mapping_rule"].includes(item.knowledge_type) && /pricing|price|index/.test(textFor(item)))) {
    suggestions.push("Add LNG SPA pricing methodology or model-input mapping guidance.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "model_input_mapping_rule" && /volume|take.or.pay|take_or_pay|quantity/.test(textFor(item)))) {
    suggestions.push("Add volume and take-or-pay mapping guidance.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "valuation_methodology" && /optionality|flex|option/.test(textFor(item)))) {
    suggestions.push("Add optionality methodology for contractual flexibilities.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "portfolio_strategy")) {
    suggestions.push("Add portfolio strategy guidance.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "market_fundamentals")) {
    suggestions.push("Add market fundamentals guidance.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "good_analysis_example")) {
    suggestions.push("Add good analysis examples.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "bad_analysis_example")) {
    suggestions.push("Add bad analysis examples for critique and comparison.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "corrected_analysis_example")) {
    suggestions.push("Add corrected analysis examples.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "negotiation_playbook")) {
    suggestions.push("Add a trader recommendation or negotiation checklist.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "glossary")) {
    suggestions.push("Add a glossary for SPA, trading, and valuation terms.");
  }
  if (!hasAny(items, (item) => item.knowledge_type === "risk_policy")) {
    suggestions.push("Add risk policy guidance.");
  }

  return suggestions;
}

export function countBy(items: KnowledgeDocumentMetadata[], field: keyof KnowledgeDocumentMetadata): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const raw = item[field];
    const key = typeof raw === "string" && raw ? raw : "unspecified";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
}
