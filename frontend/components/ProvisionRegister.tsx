import type { ProvisionRegisterItem } from "@/lib/types";

interface ProvisionRegisterProps {
  items: ProvisionRegisterItem[];
}

export default function ProvisionRegister({ items }: ProvisionRegisterProps) {
  return (
    <article className="card wide">
      <div className="card-header">
        <h2>Provision Register</h2>
        <span className="badge">{items.length} items</span>
      </div>

      <div className="register-list">
        {items.map((item) => (
          <section className="register-item" key={item.id}>
            <div className="item-title">
              <strong>{item.id}</strong>
              <span className="badge">{item.category}</span>
              <span className="badge">{item.valuation_impact}</span>
              <span className="badge">{item.evidence_status}</span>
            </div>
            <p>{item.interpretation}</p>
            {item.assumption_required && (
              <div className="evidence-note">
                <strong>Assumption required</strong>: {item.assumption_required}
              </div>
            )}
          </section>
        ))}
      </div>
    </article>
  );
}
