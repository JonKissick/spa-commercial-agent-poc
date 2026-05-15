from app.schemas import CommercialEvaluationResponse, ValuationInputItem


def item_text(item: ValuationInputItem) -> str:
    value = item.value
    if isinstance(value, list):
        value_text = " ".join(str(part) for part in value)
    elif isinstance(value, dict):
        value_text = " ".join(f"{key} {val}" for key, val in value.items())
    else:
        value_text = str(value or "")
    return " ".join([item.name, value_text, " ".join(item.warnings)]).strip()


def response_text(response: CommercialEvaluationResponse) -> str:
    parts: list[str] = [
        response.contract_summary.summary,
        str(response.contract_summary.commodity or ""),
        str(response.contract_summary.seller or ""),
        str(response.contract_summary.buyer or ""),
        str(response.contract_summary.contract_term or ""),
    ]
    for provision in response.provision_register:
        parts.extend([
            provision.title,
            provision.category.value,
            provision.clause_reference or "",
            provision.extracted_text or "",
            provision.commercial_meaning,
            provision.model_input or "",
        ])
    pack = response.valuation_input_pack
    for field in [
        "price_basis",
        "pricing_formula",
        "price_index",
        "currency",
        "volume_obligation",
        "annual_contract_quantity",
        "delivery_point",
        "delivery_terms",
        "duration",
        "destination_flexibility",
        "volume_flexibility",
        "tax_or_change_in_law_exposure",
        "operational_constraints",
        "termination_economics",
    ]:
        for item in getattr(pack, field):
            parts.append(item_text(item))
    return "\n".join(part for part in parts if part).lower()


def unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output


def has_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)
