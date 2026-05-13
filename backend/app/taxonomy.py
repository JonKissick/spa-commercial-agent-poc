from app.schemas import ProvisionCategory, ValuationImpact


SPA_TAXONOMY: dict[ProvisionCategory, dict[str, object]] = {
    ProvisionCategory.PRICING: {
        "label": "Pricing",
        "description": "Contract price formula, fixed price, index linkage, escalation, currency, and payment price basis.",
        "what_to_look_for": "Price formula, index references, premiums, discounts, FX, escalation, floors, caps, review dates, and invoice price mechanics.",
        "common_signals": ["price", "pricing", "index", "formula", "premium", "discount", "escalation", "currency", "invoice"],
        "commercial_importance": "Pricing is usually a direct cash-flow driver and key input to any later DCF or margin analysis.",
        "typical_valuation_impacts": [ValuationImpact.DCF, ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.UNCLEAR],
    },
    ProvisionCategory.VOLUME: {
        "label": "Volume",
        "description": "Contract quantity, annual contract quantity, cargo sizes, tolerances, minimum and maximum quantities.",
        "what_to_look_for": "ACQ, DCQ, cargo quantity, nomination quantity, tolerance, minimum quantity, maximum quantity, supply obligation, offtake obligation.",
        "common_signals": ["quantity", "volume", "ACQ", "DCQ", "cargo", "tonnes", "barrels", "MMBtu", "tolerance"],
        "commercial_importance": "Volume defines exposure size, revenue basis, operational commitments, and model scale.",
        "typical_valuation_impacts": [ValuationImpact.DCF, ValuationImpact.PORTFOLIO, ValuationImpact.RISK_ADJUSTMENT],
    },
    ProvisionCategory.TAKE_OR_PAY: {
        "label": "Take-or-pay",
        "description": "Minimum payment or offtake obligation regardless of physical take.",
        "what_to_look_for": "Take-or-pay, ship-or-pay, minimum bill, deficiency payment, annual minimum quantity, payment despite failure to take.",
        "common_signals": ["take-or-pay", "ship-or-pay", "minimum bill", "deficiency", "failure to take", "minimum quantity"],
        "commercial_importance": "Creates downside protection for seller and fixed obligation risk for buyer.",
        "typical_valuation_impacts": [ValuationImpact.DCF, ValuationImpact.RISK_ADJUSTMENT],
    },
    ProvisionCategory.DELIVERY: {
        "label": "Delivery",
        "description": "Delivery location, timing, title/risk transfer, Incoterms, scheduling, and logistics obligations.",
        "what_to_look_for": "Delivery point, loading port, discharge port, title transfer, risk transfer, Incoterms, delivery window, laycan, scheduling.",
        "common_signals": ["delivery", "deliver", "title", "risk", "FOB", "CIF", "DES", "DAP", "loading", "discharge", "laycan"],
        "commercial_importance": "Delivery terms determine logistics cost, operational feasibility, and exposure to disruptions.",
        "typical_valuation_impacts": [ValuationImpact.DCF, ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.PORTFOLIO],
    },
    ProvisionCategory.DESTINATION_FLEXIBILITY: {
        "label": "Destination flexibility",
        "description": "Rights or restrictions to divert, redirect, resell, or nominate alternate destinations.",
        "what_to_look_for": "Destination restriction, diversion rights, resale restrictions, alternate discharge port, buyer destination nomination.",
        "common_signals": ["destination", "diversion", "redirect", "resale", "alternate port", "discharge port", "onward sale"],
        "commercial_importance": "Can create spread capture and market optimization value, but only if rights are contractually supported.",
        "typical_valuation_impacts": [ValuationImpact.OPTIONALITY, ValuationImpact.PORTFOLIO, ValuationImpact.RISK_ADJUSTMENT],
    },
    ProvisionCategory.VOLUME_FLEXIBILITY: {
        "label": "Volume flexibility",
        "description": "Rights to vary nomination quantities, cargo counts, tolerances, upward/downward flexibility, or swing.",
        "what_to_look_for": "Swing rights, tolerance bands, upward/downward quantity flexibility, nomination adjustments, buyer/seller quantity options.",
        "common_signals": ["flexibility", "swing", "tolerance", "nomination", "increase", "decrease", "upward", "downward"],
        "commercial_importance": "May create operational and commercial optionality, or expose one party to imbalance risk.",
        "typical_valuation_impacts": [ValuationImpact.OPTIONALITY, ValuationImpact.DCF, ValuationImpact.PORTFOLIO],
    },
    ProvisionCategory.MAKE_UP: {
        "label": "Make-up",
        "description": "Rights to recover paid-for but untaken quantities in later periods.",
        "what_to_look_for": "Make-up gas, make-up quantity, carry-forward, deficiency recovery, expiration of make-up rights.",
        "common_signals": ["make-up", "make up", "carry-forward", "deficiency quantity", "recover", "untaken"],
        "commercial_importance": "Can materially change the economics of take-or-pay and future delivery optionality.",
        "typical_valuation_impacts": [ValuationImpact.OPTIONALITY, ValuationImpact.DCF],
    },
    ProvisionCategory.PRICE_REVIEW: {
        "label": "Price review",
        "description": "Periodic or event-driven rights to reopen, renegotiate, reset, or arbitrate pricing.",
        "what_to_look_for": "Review date, price reopening, market review, hardship, expert determination, arbitration of price, trigger event.",
        "common_signals": ["price review", "review date", "reopener", "market price", "expert", "arbitration", "hardship"],
        "commercial_importance": "Can cap or reopen long-term economics and introduce negotiation or dispute risk.",
        "typical_valuation_impacts": [ValuationImpact.OPTIONALITY, ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.DCF],
    },
    ProvisionCategory.FORCE_MAJEURE: {
        "label": "Force majeure",
        "description": "Excuse, suspension, mitigation, and termination mechanics for events outside party control.",
        "what_to_look_for": "Force majeure events, notice, mitigation, suspension, excluded events, prolonged force majeure termination rights.",
        "common_signals": ["force majeure", "FM", "beyond control", "suspension", "mitigate", "notice", "prolonged"],
        "commercial_importance": "Allocates disruption risk and affects deliverability, penalties, and termination exposure.",
        "typical_valuation_impacts": [ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.DCF],
    },
    ProvisionCategory.TERMINATION: {
        "label": "Termination",
        "description": "Rights to terminate for default, insolvency, prolonged force majeure, convenience, or change events.",
        "what_to_look_for": "Termination event, default, insolvency, cure period, early termination, termination payment, convenience termination.",
        "common_signals": ["terminate", "termination", "default", "cure period", "insolvency", "early termination", "termination payment"],
        "commercial_importance": "Defines exit rights, downside loss protection, and stranded obligation risk.",
        "typical_valuation_impacts": [ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.OPTIONALITY, ValuationImpact.DCF],
    },
    ProvisionCategory.CREDIT: {
        "label": "Credit",
        "description": "Credit support, payment security, parent guarantees, letters of credit, collateral, and credit triggers.",
        "what_to_look_for": "Letter of credit, parent guarantee, collateral, security, credit rating, margining, payment default, assurance.",
        "common_signals": ["credit", "letter of credit", "LC", "guarantee", "collateral", "security", "assurance", "rating"],
        "commercial_importance": "Affects counterparty exposure, payment risk, and conditions to proceed.",
        "typical_valuation_impacts": [ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.PORTFOLIO],
    },
    ProvisionCategory.QUALITY: {
        "label": "Quality",
        "description": "Product specifications, quality tolerances, measurement, rejection, and off-spec remedies.",
        "what_to_look_for": "Specifications, sulphur, API gravity, heating value, quality certificate, off-spec, rejection, measurement.",
        "common_signals": ["quality", "specification", "off-spec", "certificate", "measurement", "API", "sulphur", "heating value"],
        "commercial_importance": "Quality affects price, deliverability, operations, rejection risk, and blending value.",
        "typical_valuation_impacts": [ValuationImpact.DCF, ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.PORTFOLIO],
    },
    ProvisionCategory.TAX: {
        "label": "Tax",
        "description": "Tax allocation, withholding, duties, VAT/GST, gross-up, and changes to tax burden.",
        "what_to_look_for": "Taxes, duties, VAT, GST, withholding, gross-up, customs, levies, tax indemnity.",
        "common_signals": ["tax", "VAT", "GST", "withholding", "gross-up", "duties", "customs", "levy"],
        "commercial_importance": "Tax allocation affects netback, cash flows, and change-in-law exposure.",
        "typical_valuation_impacts": [ValuationImpact.DCF, ValuationImpact.RISK_ADJUSTMENT],
    },
    ProvisionCategory.CHANGE_IN_LAW: {
        "label": "Change in law",
        "description": "Allocation of regulatory, sanctions, legal, or compliance changes after signing.",
        "what_to_look_for": "Change in law, sanctions, regulations, compliance change, new law, regulatory costs, illegality.",
        "common_signals": ["change in law", "new law", "regulation", "sanctions", "illegality", "compliance", "regulatory"],
        "commercial_importance": "Can shift costs, suspend obligations, or create renegotiation/termination rights.",
        "typical_valuation_impacts": [ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.DCF, ValuationImpact.OPTIONALITY],
    },
    ProvisionCategory.PENALTIES: {
        "label": "Penalties and liquidated damages",
        "description": "Late delivery charges, failure-to-take charges, shortfall remedies, demurrage, and liquidated damages.",
        "what_to_look_for": "Penalty, liquidated damages, LDs, demurrage, shortfall charge, late delivery charge, failure to deliver.",
        "common_signals": ["penalty", "liquidated damages", "LD", "demurrage", "shortfall", "late delivery", "failure to deliver"],
        "commercial_importance": "Creates downside risk, operational discipline, and potential risk-adjusted value impact.",
        "typical_valuation_impacts": [ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.DCF],
    },
    ProvisionCategory.OPERATIONAL_CONSTRAINTS: {
        "label": "Operational constraints",
        "description": "Operational conditions, facility constraints, scheduling limits, vessel requirements, and capacity restrictions.",
        "what_to_look_for": "Facility availability, vessel requirements, scheduling limits, capacity, maintenance, nominations deadline, operating procedures.",
        "common_signals": ["operational", "facility", "capacity", "maintenance", "vessel", "scheduling", "nomination deadline", "procedures"],
        "commercial_importance": "Constrains deliverability and may reduce the practical value of contractual flexibility.",
        "typical_valuation_impacts": [ValuationImpact.PORTFOLIO, ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.DCF],
    },
    ProvisionCategory.ASSIGNMENT_CHANGE_OF_CONTROL: {
        "label": "Assignment and change of control",
        "description": "Assignment rights, consent requirements, affiliate transfers, and change-of-control restrictions.",
        "what_to_look_for": "Assignment, transfer, affiliate, consent, change of control, novation, successor, permitted transferee.",
        "common_signals": ["assignment", "assign", "transfer", "affiliate", "consent", "change of control", "novation"],
        "commercial_importance": "Affects portfolio management, exit strategy, counterparty identity, and credit exposure.",
        "typical_valuation_impacts": [ValuationImpact.PORTFOLIO, ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.OPTIONALITY],
    },
    ProvisionCategory.OTHER: {
        "label": "Other commercial terms",
        "description": "Commercially material provisions that do not fit the canonical categories.",
        "what_to_look_for": "Unusual economics, bespoke rights, side letters, special conditions, or other material obligations.",
        "common_signals": ["special condition", "side letter", "bespoke", "commercial", "material", "other"],
        "commercial_importance": "Captures material terms that may affect economics or risk but sit outside the standard taxonomy.",
        "typical_valuation_impacts": [ValuationImpact.UNCLEAR, ValuationImpact.RISK_ADJUSTMENT, ValuationImpact.NONE],
    },
}


def taxonomy_categories() -> list[ProvisionCategory]:
    return list(SPA_TAXONOMY.keys())


def format_taxonomy_for_prompt() -> str:
    lines: list[str] = []
    for category, item in SPA_TAXONOMY.items():
        impacts = ", ".join(str(impact.value) for impact in item["typical_valuation_impacts"])
        signals = ", ".join(str(signal) for signal in item["common_signals"])
        lines.append(
            f"- {category.value} ({item['label']}): {item['description']} Look for: {item['what_to_look_for']} Signals: {signals}. Why it matters: {item['commercial_importance']} Typical valuation impacts: {impacts}."
        )
    return "\n".join(lines)
