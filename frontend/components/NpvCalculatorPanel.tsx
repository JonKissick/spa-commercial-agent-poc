import { useEffect, useMemo, useState } from "react";
import { calculateNpv } from "@/lib/api";
import type { CommercialEvaluationResponse, NpvCalculationResponse, NpvContractRole, NpvDeliveryBasis, NpvScenarioName, ScenarioAssumptions, SensitivityTable, BreakEvenResult } from "@/lib/types";
import JsonBlock from "./JsonBlock";
import StatusBadge from "./StatusBadge";


interface NpvCalculatorPanelProps {
  latestAnalysis: CommercialEvaluationResponse | null;
  prefillSignal: number;
}

interface PrefillSuggestion {
  contractRole?: NpvContractRole;
  deliveryBasis?: NpvDeliveryBasis;
  currency?: string;
  unit: string;
  documentName?: string;
  notes: string[];
  warnings: string[];
}

const ALLOWED_ROLES: NpvContractRole[] = ["buyer", "seller"];
const ALLOWED_BASES: NpvDeliveryBasis[] = ["des", "fob", "ex_ship", "delivered", "free_on_board"];

const SCENARIOS: NpvScenarioName[] = ["base", "upside", "downside", "stress"];
const NUMERIC_FIELDS: { key: keyof ScenarioAssumptions; label: string }[] = [
  { key: "annual_volume", label: "Annual volume" },
  { key: "contract_price", label: "Contract price" },
  { key: "market_price", label: "Market price" },
  { key: "supply_cost", label: "Supply cost" },
  { key: "freight_cost", label: "Freight" },
  { key: "boil_off_cost", label: "Boil-off" },
  { key: "port_canal_cost", label: "Port/canal" },
  { key: "regas_terminal_cost", label: "Regas/terminal" },
  { key: "downstream_cost", label: "Downstream" },
  { key: "other_costs", label: "Other costs" },
  { key: "annual_fixed_costs", label: "Fixed costs" },
];

function initialScenario(name: NpvScenarioName, index: number): ScenarioAssumptions {
  const spread = [0, 1.5, -1, -2.5][index] ?? 0;
  return {
    scenario_name: name,
    annual_volume: 1000000,
    contract_price: 8,
    market_price: 10 + spread,
    supply_cost: 5,
    freight_cost: 0.8,
    boil_off_cost: 0.1,
    port_canal_cost: 0.05,
    regas_terminal_cost: 0.35,
    downstream_cost: 0.1,
    other_costs: 0,
    annual_fixed_costs: 0,
    notes: null,
  };
}


function firstCurrencyFromAnalysis(analysis: CommercialEvaluationResponse | null): string | undefined {
  const raw = analysis?.valuation_input_pack?.currency;
  if (!Array.isArray(raw)) return undefined;
  for (const item of raw) {
    if (typeof item === "object" && item !== null && "value" in item) {
      const value = String((item as { value?: unknown }).value ?? "").trim();
      if (/^[A-Z]{3}$/.test(value)) return value;
      const match = value.match(/\b[A-Z]{3}\b/);
      if (match) return match[0];
    }
  }
  return undefined;
}

function buildPrefillSuggestion(analysis: CommercialEvaluationResponse | null): PrefillSuggestion | null {
  if (!analysis) return null;
  const outputs = analysis.analysis_model_outputs;
  const deal = outputs?.deal_structure;
  const readiness = outputs?.npv_readiness;
  const landed = outputs?.landed_value_or_netback;
  const warnings: string[] = [];
  const notes: string[] = [];
  let contractRole: NpvContractRole | undefined;
  let deliveryBasis: NpvDeliveryBasis | undefined;

  if (deal?.contract_role && ALLOWED_ROLES.includes(deal.contract_role as NpvContractRole)) {
    contractRole = deal.contract_role as NpvContractRole;
    notes.push(`Role suggested from analysis: ${deal.contract_role}.`);
  } else {
    warnings.push("Contract role is unclear or not buyer/seller; choose buyer or seller manually.");
  }

  if (deal?.delivery_basis && ALLOWED_BASES.includes(deal.delivery_basis as NpvDeliveryBasis)) {
    deliveryBasis = deal.delivery_basis as NpvDeliveryBasis;
    notes.push(`Delivery basis suggested from analysis: ${deal.delivery_basis}.`);
  } else {
    warnings.push("Delivery basis is unclear; choose DES/FOB/delivered basis manually.");
  }

  if (deal?.confidence === "low") warnings.push("Deal structure confidence is low; review role, basis, origin, destination, and logistics responsibility before calculation.");
  if (readiness?.missing_contract_inputs?.length) notes.push(`Missing contract inputs: ${readiness.missing_contract_inputs.join(", ")}.`);
  if (readiness?.required_logistics_data?.length) notes.push(`Required logistics data: ${readiness.required_logistics_data.join(", ")}.`);
  if (landed?.applicable_model) notes.push(`Suggested future model: ${landed.applicable_model}.`);

  return {
    contractRole,
    deliveryBasis,
    currency: firstCurrencyFromAnalysis(analysis),
    unit: "MMBtu",
    documentName: analysis.document_metadata?.original_filename ?? undefined,
    notes,
    warnings,
  };
}

function formulaGuidance(role: NpvContractRole, basis: NpvDeliveryBasis): string {
  const isFob = basis === "fob" || basis === "free_on_board";
  const isDelivered = basis === "des" || basis === "ex_ship" || basis === "delivered";
  if (role === "buyer" && isFob) return "Buyer FOB: destination market value minus FOB price minus freight, boil-off, port/canal, regas/terminal, downstream, and other logistics costs.";
  if (role === "buyer" && isDelivered) return "Buyer DES/delivered: destination market value minus DES contract price minus terminal, downstream, and other buyer-side costs.";
  if (role === "seller" && isFob) return "Seller FOB: FOB sale price minus supply cost, loading/port costs, and other seller-side costs.";
  if (role === "seller" && isDelivered) return "Seller DES/delivered: DES sale price minus supply, shipping, boil-off, port/canal, terminal, downstream, and delivery costs.";
  return "Choose buyer/seller role and DES/FOB/delivered basis to see formula guidance.";
}

function numberOrNull(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseShiftList(value: string): number[] {
  return value.split(",").map((item) => Number(item.trim())).filter((item) => Number.isFinite(item));
}

function formatNullable(value?: number | null): string {
  return value === null || value === undefined ? "n/a" : value.toLocaleString();
}

function SensitivityTables({ tables, currency }: { tables?: SensitivityTable[]; currency: string }) {
  if (!tables?.length) return null;
  return (
    <section className="card wide">
      <div className="card-header compact"><h3>Sensitivity Tables</h3><StatusBadge label="one variable at a time" /></div>
      <div className="sensitivity-grid">
        {tables.map((table) => (
          <article className="sensitivity-card" key={`${table.scenario_name}-${table.variable}`}>
            <h4>{table.scenario_name} · {table.variable}</h4>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Shift</th><th>Resulting NPV</th><th>Unit margin</th><th>Note</th></tr></thead>
                <tbody>{table.points.map((point) => <tr key={`${point.variable}-${point.shift}-${point.note ?? ""}`}><td>{point.shift}</td><td>{point.resulting_npv.toLocaleString()} {currency}</td><td>{point.resulting_annual_unit_margin.toLocaleString()}</td><td>{point.note ?? "-"}</td></tr>)}</tbody>
              </table>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function BreakEvenTables({ results, unit }: { results?: BreakEvenResult[]; unit: string }) {
  if (!results?.length) return null;
  return (
    <section className="card wide">
      <div className="card-header compact"><h3>Break-even Analysis</h3><StatusBadge label="flat margin" /></div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Scenario</th><th>Market price</th><th>Contract price</th><th>Freight cost</th><th>Annual volume</th><th>Notes</th><th>Warnings</th></tr></thead>
          <tbody>{results.map((item) => <tr key={item.scenario_name}><td>{item.scenario_name}</td><td>{formatNullable(item.break_even_market_price)}</td><td>{formatNullable(item.break_even_contract_price)}</td><td>{formatNullable(item.break_even_freight_cost)}</td><td>{formatNullable(item.break_even_annual_volume)} {item.break_even_annual_volume == null ? "" : unit}</td><td>{item.notes.join("; ") || "-"}</td><td>{item.warnings.join("; ") || "-"}</td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}


export default function NpvCalculatorPanel({ latestAnalysis, prefillSignal }: NpvCalculatorPanelProps) {
  const [contractRole, setContractRole] = useState<NpvContractRole>("buyer");
  const [deliveryBasis, setDeliveryBasis] = useState<NpvDeliveryBasis>("fob");
  const [discountRate, setDiscountRate] = useState(0.1);
  const [contractYears, setContractYears] = useState(5);
  const [currency, setCurrency] = useState("USD");
  const [unit, setUnit] = useState("MMBtu");
  const [midyear, setMidyear] = useState(false);
  const [sensitivityEnabled, setSensitivityEnabled] = useState(true);
  const [marketPriceShifts, setMarketPriceShifts] = useState("-2,-1,0,1,2");
  const [contractPriceShifts, setContractPriceShifts] = useState("-2,-1,0,1,2");
  const [freightCostShifts, setFreightCostShifts] = useState("-0.5,0,0.5,1");
  const [discountRateShifts, setDiscountRateShifts] = useState("-0.02,-0.01,0,0.01,0.02");
  const [scenarios, setScenarios] = useState<ScenarioAssumptions[]>(SCENARIOS.map(initialScenario));
  const [result, setResult] = useState<NpvCalculationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [prefillNotes, setPrefillNotes] = useState<string[]>([]);
  const [prefillWarnings, setPrefillWarnings] = useState<string[]>([]);
  const prefillSuggestion = useMemo(() => buildPrefillSuggestion(latestAnalysis), [latestAnalysis]);



  function applyPrefill() {
    if (!prefillSuggestion) {
      setPrefillWarnings(["No latest analysis result is available to prefill from."]);
      return;
    }
    const applied: string[] = [];
    const warnings = [...prefillSuggestion.warnings];
    if (prefillSuggestion.contractRole) {
      setContractRole(prefillSuggestion.contractRole);
      applied.push(`Applied role: ${prefillSuggestion.contractRole}.`);
    }
    if (prefillSuggestion.deliveryBasis) {
      setDeliveryBasis(prefillSuggestion.deliveryBasis);
      applied.push(`Applied delivery basis: ${prefillSuggestion.deliveryBasis}.`);
    }
    if (prefillSuggestion.currency) {
      setCurrency(prefillSuggestion.currency);
      applied.push(`Applied currency: ${prefillSuggestion.currency}.`);
    }
    setUnit(prefillSuggestion.unit);
    const note = [
      `Prefill from ${prefillSuggestion.documentName ?? "latest analysis"}.`,
      ...applied,
      "Numeric assumptions were not prefilled; analyst must supply or confirm price, volume, market, freight, discount rate, and costs.",
    ].join(" ");
    setScenarios((current) => current.map((scenario) => ({ ...scenario, notes: note })));
    setPrefillNotes([...applied, ...prefillSuggestion.notes, "Scenario notes updated. Numeric assumptions remain manual and editable."]);
    setPrefillWarnings(warnings);
    setResult(null);
  }

  useEffect(() => {
    if (prefillSignal > 0) applyPrefill();
  // applyPrefill intentionally reads current suggestion and setters only when the signal changes.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillSignal]);

  function updateScenario(index: number, key: keyof ScenarioAssumptions, value: string) {
    setScenarios((current) => current.map((scenario, scenarioIndex) => {
      if (scenarioIndex !== index) return scenario;
      return { ...scenario, [key]: key === "notes" ? value : numberOrNull(value) };
    }));
  }

  async function submit() {
    setError(null);
    setIsLoading(true);
    try {
      setResult(await calculateNpv({
        contract_role: contractRole,
        delivery_basis: deliveryBasis,
        discount_rate: discountRate,
        contract_years: contractYears,
        currency,
        unit,
        include_midyear_discounting: midyear,
        sensitivity: {
          enabled: sensitivityEnabled,
          market_price_shifts: parseShiftList(marketPriceShifts),
          contract_price_shifts: parseShiftList(contractPriceShifts),
          freight_cost_shifts: parseShiftList(freightCostShifts),
          discount_rate_shifts: parseShiftList(discountRateShifts),
        },
        scenarios,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "NPV calculation failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="panel-stack">
      <section className="card wide">
        <div className="card-header compact">
          <div>
            <h2>NPV Calculator</h2>
            <p className="quiet">Manual scenario assumptions only. No live market data, RAG, AI, or optionality value is used.</p>
          </div>
          <StatusBadge label="preliminary" tone="warning" />
        </div>

        <section className="prefill-panel">
          <div className="card-header compact">
            <div>
              <h3>Prefill from latest analysis</h3>
              <p className="quiet">Prefill uses analysis output only to set structural assumptions. Pricing, volume, market price, freight, discount rate, and costs must be supplied or confirmed by the analyst before calculation.</p>
            </div>
            <button className="secondary-button" onClick={applyPrefill} type="button" disabled={!prefillSuggestion}>Apply prefill</button>
          </div>
          {prefillSuggestion ? (
            <div className="data-grid compact-grid">
              <div><span>Document</span><strong>{prefillSuggestion.documentName ?? "latest analysis"}</strong></div>
              <div><span>Detected role</span><strong>{prefillSuggestion.contractRole ?? "unclear"}</strong></div>
              <div><span>Detected basis</span><strong>{prefillSuggestion.deliveryBasis ?? "unclear"}</strong></div>
              <div><span>Landed/netback model</span><strong>{latestAnalysis?.analysis_model_outputs?.landed_value_or_netback.applicable_model ?? "not available"}</strong></div>
              <div><span>NPV readiness</span><strong>{latestAnalysis?.analysis_model_outputs?.npv_readiness.readiness ?? "not available"}</strong></div>
              <div><span>Required logistics</span><strong>{latestAnalysis?.analysis_model_outputs?.npv_readiness.required_logistics_data?.join(", ") || "not available"}</strong></div>
            </div>
          ) : <p className="callout warning">No analysis result is available yet. Run Analyze Contract first, then return here to apply structural prefill.</p>}
          {prefillNotes.length > 0 && <ul className="text-list">{prefillNotes.map((note) => <li key={note}>{note}</li>)}</ul>}
          {prefillWarnings.length > 0 && <ul className="warning-list">{prefillWarnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
        </section>

        <div className="callout"><strong>Formula guidance</strong><p>{formulaGuidance(contractRole, deliveryBasis)}</p></div>

        <div className="form-grid">
          <label><span>Contract role</span><select value={contractRole} onChange={(event) => setContractRole(event.target.value as NpvContractRole)}><option value="buyer">buyer</option><option value="seller">seller</option></select></label>
          <label><span>Delivery basis</span><select value={deliveryBasis} onChange={(event) => setDeliveryBasis(event.target.value as NpvDeliveryBasis)}><option value="fob">fob</option><option value="free_on_board">free_on_board</option><option value="des">des</option><option value="ex_ship">ex_ship</option><option value="delivered">delivered</option><option value="unclear">unclear</option></select></label>
          <label><span>Discount rate</span><input type="number" step="0.01" min="0" max="0.99" value={discountRate} onChange={(event) => setDiscountRate(Number(event.target.value))} /></label>
          <label><span>Contract years</span><input type="number" min="1" value={contractYears} onChange={(event) => setContractYears(Number(event.target.value))} /></label>
          <label><span>Currency</span><input value={currency} onChange={(event) => setCurrency(event.target.value)} /></label>
          <label><span>Unit</span><input value={unit} onChange={(event) => setUnit(event.target.value)} /></label>
          <label className="checkbox-row"><input type="checkbox" checked={midyear} onChange={(event) => setMidyear(event.target.checked)} /> include midyear discounting</label>
        </div>

        <section className="prefill-panel">
          <div className="card-header compact">
            <div><h3>Sensitivity Settings</h3><p className="quiet">One-variable-at-a-time sensitivities. Values are comma-separated shifts applied to manual scenario inputs.</p></div>
            <label className="checkbox-row"><input type="checkbox" checked={sensitivityEnabled} onChange={(event) => setSensitivityEnabled(event.target.checked)} /> enable sensitivities</label>
          </div>
          <div className="form-grid">
            <label><span>Market price shifts</span><input value={marketPriceShifts} onChange={(event) => setMarketPriceShifts(event.target.value)} /></label>
            <label><span>Contract price shifts</span><input value={contractPriceShifts} onChange={(event) => setContractPriceShifts(event.target.value)} /></label>
            <label><span>Freight cost shifts</span><input value={freightCostShifts} onChange={(event) => setFreightCostShifts(event.target.value)} /></label>
            <label><span>Discount rate shifts</span><input value={discountRateShifts} onChange={(event) => setDiscountRateShifts(event.target.value)} /></label>
          </div>
        </section>

        <div className="table-wrap npv-table">
          <table>
            <thead><tr><th>Scenario</th>{NUMERIC_FIELDS.map((field) => <th key={field.key}>{field.label}</th>)}<th>Notes</th></tr></thead>
            <tbody>{scenarios.map((scenario, index) => <tr key={scenario.scenario_name}><td><strong>{scenario.scenario_name}</strong></td>{NUMERIC_FIELDS.map((field) => <td key={field.key}><input type="number" step="0.01" value={scenario[field.key] == null ? "" : String(scenario[field.key])} onChange={(event) => updateScenario(index, field.key, event.target.value)} /></td>)}<td><input value={scenario.notes ?? ""} onChange={(event) => updateScenario(index, "notes", event.target.value)} /></td></tr>)}</tbody>
          </table>
        </div>

        <button className="primary-button" disabled={isLoading} onClick={submit} type="button">{isLoading ? "Calculating..." : "Calculate Scenario NPVs"}</button>
        {error && <p className="error-text standalone">{error}</p>}
      </section>

      {result && <section className="card wide">
        <div className="card-header compact"><h3>NPV Results</h3><StatusBadge label={result.calculation_status} tone={result.calculation_status === "calculated" ? "good" : "warning"} /></div>
        <div className="table-wrap"><table><thead><tr><th>Scenario</th><th>Annual unit margin</th><th>Annual cash flow</th><th>NPV</th><th>Undiscounted total</th><th>Formula</th><th>Warnings</th></tr></thead><tbody>{result.scenario_results.map((item) => <tr key={item.scenario_name}><td>{item.scenario_name}</td><td>{item.annual_unit_margin.toLocaleString()}</td><td>{item.annual_cash_flow.toLocaleString()} {result.currency}</td><td>{item.npv.toLocaleString()} {result.currency}</td><td>{item.undiscounted_total_cash_flow.toLocaleString()} {result.currency}</td><td>{item.formula_used}</td><td>{item.warnings.join("; ")}</td></tr>)}</tbody></table></div>
        <div className="split-grid"><section><h4>Key sensitivities</h4><ul>{result.key_sensitivities.map((item) => <li key={item}>{item}</li>)}</ul></section><section><h4>Break-even candidates</h4><ul>{result.break_even_candidates.map((item) => <li key={item}>{item}</li>)}</ul></section></div>
        <div className="callout warning"><strong>Limitations</strong><ul>{result.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>
        <JsonBlock value={result.scenario_results.map((item) => ({ scenario: item.scenario_name, break_even_candidates: item.break_even_candidates, included_costs: item.included_costs, excluded_costs: item.excluded_costs }))} />
      </section>}
      {result && <SensitivityTables tables={result.sensitivity_tables} currency={result.currency} />}
      {result && <BreakEvenTables results={result.break_even_results} unit={result.unit} />}
    </div>
  );
}
