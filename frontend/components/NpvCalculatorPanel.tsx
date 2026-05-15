import { useState } from "react";
import { calculateNpv } from "@/lib/api";
import type { NpvCalculationResponse, NpvContractRole, NpvDeliveryBasis, NpvScenarioName, ScenarioAssumptions } from "@/lib/types";
import JsonBlock from "./JsonBlock";
import StatusBadge from "./StatusBadge";

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

function numberOrNull(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export default function NpvCalculatorPanel() {
  const [contractRole, setContractRole] = useState<NpvContractRole>("buyer");
  const [deliveryBasis, setDeliveryBasis] = useState<NpvDeliveryBasis>("fob");
  const [discountRate, setDiscountRate] = useState(0.1);
  const [contractYears, setContractYears] = useState(5);
  const [currency, setCurrency] = useState("USD");
  const [unit, setUnit] = useState("MMBtu");
  const [midyear, setMidyear] = useState(false);
  const [scenarios, setScenarios] = useState<ScenarioAssumptions[]>(SCENARIOS.map(initialScenario));
  const [result, setResult] = useState<NpvCalculationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

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

        <div className="form-grid">
          <label><span>Contract role</span><select value={contractRole} onChange={(event) => setContractRole(event.target.value as NpvContractRole)}><option value="buyer">buyer</option><option value="seller">seller</option></select></label>
          <label><span>Delivery basis</span><select value={deliveryBasis} onChange={(event) => setDeliveryBasis(event.target.value as NpvDeliveryBasis)}><option value="fob">fob</option><option value="free_on_board">free_on_board</option><option value="des">des</option><option value="ex_ship">ex_ship</option><option value="delivered">delivered</option><option value="unclear">unclear</option></select></label>
          <label><span>Discount rate</span><input type="number" step="0.01" min="0" max="0.99" value={discountRate} onChange={(event) => setDiscountRate(Number(event.target.value))} /></label>
          <label><span>Contract years</span><input type="number" min="1" value={contractYears} onChange={(event) => setContractYears(Number(event.target.value))} /></label>
          <label><span>Currency</span><input value={currency} onChange={(event) => setCurrency(event.target.value)} /></label>
          <label><span>Unit</span><input value={unit} onChange={(event) => setUnit(event.target.value)} /></label>
          <label className="checkbox-row"><input type="checkbox" checked={midyear} onChange={(event) => setMidyear(event.target.checked)} /> include midyear discounting</label>
        </div>

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
    </div>
  );
}
