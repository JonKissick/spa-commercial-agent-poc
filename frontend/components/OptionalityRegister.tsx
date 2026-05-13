import type { OptionalityRegisterItem } from "@/lib/types";

interface OptionalityRegisterProps {
  items: OptionalityRegisterItem[];
}

export default function OptionalityRegister({ items }: OptionalityRegisterProps) {
  return (
    <article className="card">
      <div className="card-header">
        <h2>Optionality Register</h2>
        <span className="badge">{items.length} options</span>
      </div>

      <div className="register-list">
        {items.map((item) => (
          <section className="register-item" key={item.id}>
            <div className="item-title">
              <strong>{item.option_name}</strong>
              <span className="badge">{item.evidence_status}</span>
            </div>
            <p>{item.commercial_description}</p>
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
