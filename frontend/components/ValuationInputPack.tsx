import type { ValuationInputPack as ValuationInputPackType } from "@/lib/types";
import JsonBlock from "./JsonBlock";
interface ValuationInputPackProps { pack: ValuationInputPackType; }
function asList(value: unknown): string[] { return Array.isArray(value) ? value.map(String) : []; }
function InputList({ title, items }: { title: string; items: string[] }) { return <section><h3>{title}</h3><ul className="text-list">{items.map((item) => <li key={item}>{item}</li>)}</ul></section>; }
export default function ValuationInputPack({ pack }: ValuationInputPackProps) {
  return <article className="card"><div className="card-header"><h2>Valuation Input Pack</h2><span className="badge">{pack.evidence_status ?? "inputs"}</span></div><div className="register-list"><InputList title="Analyst assumptions" items={pack.missing_analyst_assumptions ?? asList(pack.required_analyst_assumptions)} /><InputList title="Market data" items={pack.missing_market_data ?? []} /><InputList title="Portfolio data" items={pack.missing_portfolio_data ?? []} /><InputList title="Warnings" items={pack.valuation_warnings ?? []} /></div><JsonBlock value={pack} /></article>;
}
