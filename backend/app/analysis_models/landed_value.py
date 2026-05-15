from app.analysis_models.schemas import ApplicableModel, ContractRole, DealStructureAssessment, DeliveryBasis, LandedValueOrNetbackAssessment


def select_landed_value_or_netback_model(deal_structure: DealStructureAssessment) -> LandedValueOrNetbackAssessment:
    role = deal_structure.contract_role
    basis = deal_structure.delivery_basis
    model = _model_for(role, basis)
    warnings: list[str] = []
    if model == ApplicableModel.UNCLEAR:
        warnings.append("Role or delivery basis is unclear, so landed value/netback model selection requires analyst confirmation.")

    logic = _logic(model)
    return LandedValueOrNetbackAssessment(
        applicable_model=model,
        economic_logic=logic,
        value_formula_description=_formula(model),
        required_price_inputs=["Contract price formula or fixed/manual price input", "Destination market value or origin netback reference", "Currency and FX assumptions"],
        required_volume_inputs=["Contract quantity", "Delivery schedule", "Tolerance and take-or-pay mechanics"],
        required_logistics_inputs=_logistics_inputs(basis),
        required_cost_inputs=["Supply acquisition cost", "Shipping/logistics costs as applicable", "Terminal/downstream costs as applicable", "Credit and operational risk adjustments"],
        required_tax_or_fee_inputs=["Taxes, duties, port fees, canal fees, change-in-law cost exposure where material"],
        origin_destination_relevance="Origin, loading port, destination, discharge port, and logistics responsibility determine whether the future model should compare landed cost, DES value, FOB value, or netback.",
        des_fob_notes=_des_fob_notes(basis),
        warnings=warnings,
    )


def _model_for(role: ContractRole, basis: DeliveryBasis) -> ApplicableModel:
    if role == ContractRole.BUYER and basis in {DeliveryBasis.FOB, DeliveryBasis.FREE_ON_BOARD}:
        return ApplicableModel.FOB_PURCHASE
    if role == ContractRole.BUYER and basis in {DeliveryBasis.DES, DeliveryBasis.EX_SHIP, DeliveryBasis.DELIVERED}:
        return ApplicableModel.DES_PURCHASE
    if role == ContractRole.SELLER and basis in {DeliveryBasis.FOB, DeliveryBasis.FREE_ON_BOARD}:
        return ApplicableModel.FOB_SALE
    if role == ContractRole.SELLER and basis in {DeliveryBasis.DES, DeliveryBasis.EX_SHIP, DeliveryBasis.DELIVERED}:
        return ApplicableModel.DES_SALE
    if role in {ContractRole.SWAP, ContractRole.PORTFOLIO_TRADE}:
        return ApplicableModel.NETBACK
    return ApplicableModel.UNCLEAR


def _logic(model: ApplicableModel) -> str:
    return {
        ApplicableModel.DES_PURCHASE: "Compare destination market value against DES contract price and buyer-side terminal/downstream/risk costs. No value is calculated in Stage 7A.",
        ApplicableModel.FOB_PURCHASE: "Compare destination market value against FOB contract price plus freight, boil-off, port/canal, regas/terminal, and other logistics costs. No value is calculated in Stage 7A.",
        ApplicableModel.DES_SALE: "Compare DES sale price against supply acquisition cost, shipping, boil-off, port/canal, and delivery costs. No value is calculated in Stage 7A.",
        ApplicableModel.FOB_SALE: "Compare FOB sale price against supply cost at loading point and relevant upstream/loading costs. No value is calculated in Stage 7A.",
        ApplicableModel.NETBACK: "Use netback or portfolio comparison logic once origin/destination spreads and logistics assumptions are supplied. No value is calculated in Stage 7A.",
        ApplicableModel.LANDED_COST: "Build landed cost from contract price plus logistics and terminal costs once all inputs are supplied. No value is calculated in Stage 7A.",
        ApplicableModel.UNCLEAR: "Model selection is unclear until contract role and delivery basis are confirmed. No value is calculated in Stage 7A.",
    }[model]


def _formula(model: ApplicableModel) -> str:
    return {
        ApplicableModel.DES_PURCHASE: "Destination market value minus DES contract price minus buyer-side terminal/downstream/risk costs.",
        ApplicableModel.FOB_PURCHASE: "Destination market value minus FOB contract price minus freight, boil-off, port/canal, regas/terminal, and other logistics costs.",
        ApplicableModel.DES_SALE: "DES sale price minus supply acquisition cost, shipping, boil-off, port/canal, and delivery costs.",
        ApplicableModel.FOB_SALE: "FOB sale price minus supply cost at loading point, liquefaction/tolling/feedgas/loading costs if relevant.",
        ApplicableModel.NETBACK: "Destination value minus logistics and handling costs to derive origin netback or portfolio-equivalent value.",
        ApplicableModel.LANDED_COST: "Contract price plus logistics, terminal, tax/fee, and risk adjustment inputs.",
        ApplicableModel.UNCLEAR: "Formula cannot be selected until role, delivery basis, origin, destination, and logistics responsibility are confirmed.",
    }[model]


def _logistics_inputs(basis: DeliveryBasis) -> list[str]:
    if basis in {DeliveryBasis.FOB, DeliveryBasis.FREE_ON_BOARD}:
        return ["origin/loading port", "destination/discharge market", "freight", "boil-off", "shipping duration", "port/canal costs", "regas/terminal costs"]
    if basis in {DeliveryBasis.DES, DeliveryBasis.EX_SHIP, DeliveryBasis.DELIVERED}:
        return ["destination/discharge point", "confirmation shipping is included", "terminal/downstream costs", "demurrage or operational exposure"]
    return ["confirmed delivery basis", "origin", "destination", "freight/logistics cost responsibility"]


def _des_fob_notes(basis: DeliveryBasis) -> list[str]:
    if basis in {DeliveryBasis.FOB, DeliveryBasis.FREE_ON_BOARD}:
        return ["FOB/free-on-board structure makes origin, loading port, freight, boil-off, and destination optionality central to later modelling."]
    if basis in {DeliveryBasis.DES, DeliveryBasis.EX_SHIP, DeliveryBasis.DELIVERED}:
        return ["DES/ex-ship/delivered structure makes destination value and buyer-side terminal/downstream cost assumptions central to later modelling."]
    return ["DES/FOB basis is unclear and must be confirmed before selecting landed value or netback logic."]
