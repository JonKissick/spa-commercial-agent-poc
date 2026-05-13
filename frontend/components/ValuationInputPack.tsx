import type { ValuationInputPack as ValuationInputPackType } from "@/lib/types";

interface ValuationInputPackProps {
  pack: ValuationInputPackType;
}

function InputList({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h3>{title}</h3>
      <ul className="text-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export default function ValuationInputPack({ pack }: ValuationInputPackProps) {
  return (
    <article className="card">
      <div className="card-header">
        <h2>Valuation Input Pack</h2>
        <span className="badge">{pack.evidence_status}</span>
      </div>

      <div className="register-list">
        <InputList title="Pricing" items={pack.pricing_inputs} />
        <InputList title="Volume" items={pack.volume_inputs} />
        <InputList title="Timing" items={pack.timing_inputs} />
        <InputList title="Risk" items={pack.risk_inputs} />
        <InputList title="Analyst assumptions" items={pack.required_analyst_assumptions} />
      </div>
    </article>
  );
}
