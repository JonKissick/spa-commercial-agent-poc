import type { AnalysisModelOutputs } from "@/lib/types";
import JsonBlock from "./JsonBlock";
import StatusBadge from "./StatusBadge";

interface CommercialModelOutputsProps {
  outputs?: AnalysisModelOutputs | null;
}

function ListBlock({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <div>
      <span>{title}</span>
      <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
    </div>
  );
}

export default function CommercialModelOutputs({ outputs }: CommercialModelOutputsProps) {
  if (!outputs) return null;
  const deal = outputs.deal_structure;
  const readiness = outputs.npv_readiness;
  const landed = outputs.landed_value_or_netback;
  const scenario = outputs.scenario_model_requirements;
  const routing = outputs.optionality_model_routing;
  const portfolio = outputs.portfolio_impact_requirements;

  return (
    <section className="card wide commercial-model-section">
      <div className="card-header compact">
        <div>
          <h3>Commercial Model Outputs</h3>
          <p className="quiet">Model route and missing-input assessment only. No NPV has been calculated.</p>
        </div>
        <StatusBadge label={readiness.readiness} tone={readiness.can_calculate_npv_now ? "good" : "warning"} />
      </div>

      <div className="commercial-model-grid">
        <article>
          <div className="card-header compact"><h4>Deal Structure</h4><StatusBadge label={deal.delivery_basis} /></div>
          <div className="data-grid compact-grid">
            <div><span>Role</span><strong>{deal.contract_role}</strong></div>
            <div><span>Shipping</span><strong>{deal.shipping_responsibility}</strong></div>
            <div><span>Origin</span><strong>{deal.origin ?? deal.loading_port ?? "unclear"}</strong></div>
            <div><span>Destination</span><strong>{deal.destination ?? deal.discharge_port ?? "unclear"}</strong></div>
          </div>
          <JsonBlock value={{ title_transfer_point: deal.title_transfer_point, risk_transfer_point: deal.risk_transfer_point, warnings: deal.warnings }} />
        </article>

        <article>
          <div className="card-header compact"><h4>NPV Readiness</h4><StatusBadge label={readiness.can_calculate_npv_now ? "ready" : "not calculable"} tone="warning" /></div>
          <p>{readiness.reason_not_ready}</p>
          <div className="data-grid compact-grid">
            <ListBlock title="Available" items={readiness.available_contract_inputs} />
            <ListBlock title="Missing contract inputs" items={readiness.missing_contract_inputs} />
            <ListBlock title="Manual assumptions" items={readiness.required_manual_assumptions} />
            <ListBlock title="Logistics data" items={readiness.required_logistics_data} />
          </div>
        </article>

        <article>
          <div className="card-header compact"><h4>Landed Value / Netback</h4><StatusBadge label={landed.applicable_model} /></div>
          <p>{landed.economic_logic}</p>
          <p className="callout">{landed.value_formula_description}</p>
          <p>{landed.origin_destination_relevance}</p>
          <JsonBlock value={{ des_fob_notes: landed.des_fob_notes, required_logistics_inputs: landed.required_logistics_inputs, warnings: landed.warnings }} />
        </article>

        <article>
          <div className="card-header compact"><h4>Scenario Requirements</h4><StatusBadge label="inputs only" /></div>
          <div className="data-grid compact-grid">
            <ListBlock title="Base" items={scenario.base_case_inputs_required} />
            <ListBlock title="Upside" items={scenario.upside_case_inputs_required} />
            <ListBlock title="Downside" items={scenario.downside_case_inputs_required} />
            <ListBlock title="Stress" items={scenario.stress_case_inputs_required} />
            <ListBlock title="Sensitivities" items={scenario.key_sensitivities} />
            <ListBlock title="Break-even candidates" items={scenario.break_even_candidates} />
          </div>
        </article>

        <article>
          <div className="card-header compact"><h4>Optionality Routing</h4><StatusBadge label={`${routing.routed_options.length} routes`} /></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Option</th><th>Future model</th><th>Readiness</th><th>Source</th></tr></thead>
              <tbody>{routing.routed_options.map((item) => <tr key={`${item.option_type}-${item.source_optionality_ids.join("-")}`}><td>{item.option_type}</td><td>{item.suggested_model}</td><td>{item.readiness}</td><td>{item.source_optionality_ids.join(", ")}</td></tr>)}</tbody>
            </table>
          </div>
          <JsonBlock value={{ not_ready_reasons: routing.not_ready_reasons, required_market_data: routing.required_market_data }} />
        </article>

        <article>
          <div className="card-header compact"><h4>Portfolio Impact Requirements</h4><StatusBadge label={portfolio.portfolio_relevance} /></div>
          <div className="data-grid compact-grid">
            <ListBlock title="Required portfolio inputs" items={portfolio.required_portfolio_inputs} />
            <ListBlock title="Concentration risks" items={portfolio.potential_concentration_risks} />
            <ListBlock title="Hedge value" items={portfolio.potential_hedge_value} />
            <ListBlock title="Constraints" items={portfolio.liquidity_or_operational_constraints} />
          </div>
        </article>
      </div>

      {outputs.commercial_model_warnings.length > 0 && (
        <div className="callout warning">
          <strong>Commercial model warnings</strong>
          <ul>{outputs.commercial_model_warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
        </div>
      )}
    </section>
  );
}
