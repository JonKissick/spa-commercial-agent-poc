import re

from app.analysis_models.schemas import Confidence, ContractRole, DealStructureAssessment, DeliveryBasis, EvidenceStatus, Responsibility
from app.analysis_models.utils import has_any, response_text, unique
from app.schemas import CommercialEvaluationResponse, ProvisionCategory


def assess_deal_structure(response: CommercialEvaluationResponse) -> DealStructureAssessment:
    text = response_text(response)
    source_ids = _source_ids(response)
    basis = _delivery_basis(text)
    role = _contract_role(text)
    warnings: list[str] = []

    if role == ContractRole.UNCLEAR:
        warnings.append("Contract role is unclear; buyer/seller/swap/portfolio role must be confirmed before model selection.")
    if basis == DeliveryBasis.UNCLEAR:
        warnings.append("Delivery basis is unclear; DES/FOB/delivered terms must be confirmed before logistics modelling.")

    shipping = Responsibility.UNCLEAR
    logistics = Responsibility.UNCLEAR
    if basis in {DeliveryBasis.DES, DeliveryBasis.EX_SHIP, DeliveryBasis.DELIVERED}:
        shipping = Responsibility.SELLER
        logistics = Responsibility.SELLER
        warnings.append("DES/delivered heuristic assumes seller bears shipping to destination unless the contract says otherwise.")
    elif basis in {DeliveryBasis.FOB, DeliveryBasis.FREE_ON_BOARD}:
        shipping = Responsibility.BUYER
        logistics = Responsibility.BUYER
        warnings.append("FOB heuristic assumes buyer bears shipping/logistics after loading unless the contract says otherwise.")

    confidence = Confidence.MEDIUM if role != ContractRole.UNCLEAR and basis != DeliveryBasis.UNCLEAR else Confidence.LOW
    evidence_status = EvidenceStatus.INFERRED_FROM_CONTRACT if confidence == Confidence.MEDIUM else EvidenceStatus.INSUFFICIENT_EVIDENCE

    return DealStructureAssessment(
        contract_role=role,
        delivery_basis=basis,
        commodity=response.contract_summary.commodity,
        origin=_extract_after(text, ["origin", "supply origin", "source"]),
        destination=_extract_after(text, ["destination", "delivery point", "discharge point"]),
        loading_port=_extract_after(text, ["loading port", "load port", "port of loading"]),
        discharge_port=_extract_after(text, ["discharge port", "port of discharge", "discharge terminal"]),
        title_transfer_point=_extract_after(text, ["title transfer", "title passes", "title shall pass"]),
        risk_transfer_point=_extract_after(text, ["risk transfer", "risk passes", "risk shall pass"]),
        shipping_responsibility=shipping,
        logistics_cost_responsibility=logistics,
        source_provision_ids=source_ids,
        evidence_status=evidence_status,
        confidence=confidence,
        warnings=unique(warnings),
    )


def _source_ids(response: CommercialEvaluationResponse) -> list[str]:
    categories = {ProvisionCategory.DELIVERY, ProvisionCategory.PRICING, ProvisionCategory.VOLUME, ProvisionCategory.TAKE_OR_PAY}
    return [provision.id for provision in response.provision_register if provision.category in categories]


def _delivery_basis(text: str) -> DeliveryBasis:
    if has_any(text, ["free on board", "free-on-board"]):
        return DeliveryBasis.FREE_ON_BOARD
    if re.search(r"\bfob\b", text):
        return DeliveryBasis.FOB
    if has_any(text, ["ex ship", "ex-ship"]):
        return DeliveryBasis.EX_SHIP
    if re.search(r"\bdes\b", text):
        return DeliveryBasis.DES
    if has_any(text, ["delivered", "delivery at destination", "delivered ex"]):
        return DeliveryBasis.DELIVERED
    return DeliveryBasis.UNCLEAR


def _contract_role(text: str) -> ContractRole:
    if has_any(text, ["swap", "exchange"]):
        return ContractRole.SWAP
    if has_any(text, ["tolling", "toll"]):
        return ContractRole.TOLLING
    if has_any(text, ["portfolio optimization", "portfolio trade"]):
        return ContractRole.PORTFOLIO_TRADE
    buyer_hits = len(re.findall(r"\bbuyer\b|purchase|purchaser", text))
    seller_hits = len(re.findall(r"\bseller\b|sale|supplier", text))
    if buyer_hits > seller_hits and buyer_hits > 0:
        return ContractRole.BUYER
    if seller_hits > buyer_hits and seller_hits > 0:
        return ContractRole.SELLER
    if buyer_hits and seller_hits:
        return ContractRole.BUYER
    return ContractRole.UNCLEAR


def _extract_after(text: str, labels: list[str]) -> str | None:
    for label in labels:
        pattern = re.escape(label) + r"\s*[:\-]?\s*([a-z0-9 ,/._-]{3,80})"
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip(" .,-")
            return value[:80] if value else None
    return None
