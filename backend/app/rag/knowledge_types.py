from enum import StrEnum


class KnowledgeType(StrEnum):
    CONTRACT_REFERENCE = "contract_reference"
    INTERNAL_PROCEDURE = "internal_procedure"
    VALUATION_METHODOLOGY = "valuation_methodology"
    MARKET_FUNDAMENTALS = "market_fundamentals"
    PORTFOLIO_STRATEGY = "portfolio_strategy"
    GOOD_ANALYSIS_EXAMPLE = "good_analysis_example"
    BAD_ANALYSIS_EXAMPLE = "bad_analysis_example"
    CORRECTED_ANALYSIS_EXAMPLE = "corrected_analysis_example"
    REVIEWER_FEEDBACK = "reviewer_feedback"
    TAXONOMY_GUIDANCE = "taxonomy_guidance"
    MODEL_INPUT_MAPPING_RULE = "model_input_mapping_rule"
    NEGOTIATION_PLAYBOOK = "negotiation_playbook"
    GLOSSARY = "glossary"
    RISK_POLICY = "risk_policy"
    OTHER = "other"


KNOWLEDGE_TYPE_REGISTRY: dict[KnowledgeType, dict[str, object]] = {
    KnowledgeType.CONTRACT_REFERENCE: {
        "label": "Contract reference",
        "description": "Reference clauses or contract extracts for comparison and drafting context.",
        "intended_use": "Compare clause structure and terminology; do not treat as governing for the uploaded SPA.",
        "allowed_in_analysis_context": True,
        "caution": "Use only as reference context; the uploaded contract remains the source of truth.",
    },
    KnowledgeType.INTERNAL_PROCEDURE: {
        "label": "Internal procedure",
        "description": "Approved internal process guidance for commercial review workflow.",
        "intended_use": "Guide review steps, required checks, and escalation process.",
        "allowed_in_analysis_context": True,
        "caution": "Check approval status and effective date before relying on procedure.",
    },
    KnowledgeType.VALUATION_METHODOLOGY: {
        "label": "Valuation methodology",
        "description": "Method notes for DCF, risk adjustment, optionality framing, and model input mapping.",
        "intended_use": "Inform later analyst valuation setup without calculating value in the agent.",
        "allowed_in_analysis_context": True,
        "caution": "Methodology does not replace analyst model governance.",
    },
    KnowledgeType.MARKET_FUNDAMENTALS: {
        "label": "Market fundamentals",
        "description": "Market structure, drivers, curves, liquidity, and commodity context notes.",
        "intended_use": "Identify market data needs and assumptions.",
        "allowed_in_analysis_context": True,
        "caution": "May become stale; check effective date and source owner.",
    },
    KnowledgeType.PORTFOLIO_STRATEGY: {
        "label": "Portfolio strategy",
        "description": "Portfolio constraints, concentration themes, strategic fit, and exposure guidance.",
        "intended_use": "Frame portfolio data requirements and fit questions.",
        "allowed_in_analysis_context": True,
        "caution": "Do not infer current book positions unless supplied.",
    },
    KnowledgeType.GOOD_ANALYSIS_EXAMPLE: {
        "label": "Good analysis example",
        "description": "Examples of high-quality commercial analysis and memo style.",
        "intended_use": "Use as positive style and reasoning guidance.",
        "allowed_in_analysis_context": True,
        "caution": "Example facts should not be copied into new analysis.",
    },
    KnowledgeType.BAD_ANALYSIS_EXAMPLE: {
        "label": "Bad analysis example",
        "description": "Examples of flawed analysis, weak evidence use, or bad reasoning.",
        "intended_use": "Use for critique and comparison only.",
        "allowed_in_analysis_context": True,
        "caution": "Do not treat as positive guidance or reproduce conclusions.",
    },
    KnowledgeType.CORRECTED_ANALYSIS_EXAMPLE: {
        "label": "Corrected analysis example",
        "description": "Before/after examples showing reviewer corrections.",
        "intended_use": "Learn correction patterns and evidence discipline.",
        "allowed_in_analysis_context": True,
        "caution": "Separate corrected logic from source facts.",
    },
    KnowledgeType.REVIEWER_FEEDBACK: {
        "label": "Reviewer feedback",
        "description": "Reviewer comments and recurring critique themes.",
        "intended_use": "Highlight common quality issues and required checks.",
        "allowed_in_analysis_context": True,
        "caution": "Feedback may be context-specific; verify applicability.",
    },
    KnowledgeType.TAXONOMY_GUIDANCE: {
        "label": "Taxonomy guidance",
        "description": "Guidance on provision categories, evidence status, and classification rules.",
        "intended_use": "Support consistent clause classification.",
        "allowed_in_analysis_context": True,
        "caution": "Taxonomy guidance should not invent missing provisions.",
    },
    KnowledgeType.MODEL_INPUT_MAPPING_RULE: {
        "label": "Model input mapping rule",
        "description": "Rules for translating provisions into valuation input candidates.",
        "intended_use": "Support valuation input pack consistency.",
        "allowed_in_analysis_context": True,
        "caution": "Mapping rules do not calculate valuation outputs.",
    },
    KnowledgeType.NEGOTIATION_PLAYBOOK: {
        "label": "Negotiation playbook",
        "description": "Commercial negotiation levers, fallback positions, and risk allocation themes.",
        "intended_use": "Inform issues lists and negotiation questions.",
        "allowed_in_analysis_context": True,
        "caution": "Must be adapted to deal context and approvals.",
    },
    KnowledgeType.GLOSSARY: {
        "label": "Glossary",
        "description": "Definitions of commercial, legal, market, and valuation terms.",
        "intended_use": "Use for definitions and terminology clarification.",
        "allowed_in_analysis_context": True,
        "caution": "Use for definitions, not commercial conclusions.",
    },
    KnowledgeType.RISK_POLICY: {
        "label": "Risk policy",
        "description": "Risk appetite, approvals, controls, and compliance guidance.",
        "intended_use": "Flag risk review requirements and control questions.",
        "allowed_in_analysis_context": True,
        "caution": "Check approval status; policy interpretation may require risk team input.",
    },
    KnowledgeType.OTHER: {
        "label": "Other",
        "description": "Other approved reference material.",
        "intended_use": "Use only according to metadata and reviewer judgement.",
        "allowed_in_analysis_context": False,
        "caution": "Prefer a more specific knowledge type where possible.",
    },
}


def all_knowledge_types() -> list[KnowledgeType]:
    return list(KNOWLEDGE_TYPE_REGISTRY.keys())
