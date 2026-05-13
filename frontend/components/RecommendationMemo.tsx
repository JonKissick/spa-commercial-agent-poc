import type { DealRecommendation } from "@/lib/types";

interface RecommendationMemoProps {
  recommendation: DealRecommendation;
}

export default function RecommendationMemo({ recommendation }: RecommendationMemoProps) {
  return (
    <article className="card wide">
      <div className="card-header">
        <h2>Recommendation Memo</h2>
        <span className="badge">{recommendation.recommendation}</span>
      </div>

      <p>{recommendation.memo}</p>

      <div className="meta-grid">
        <section>
          <h3>Conditions</h3>
          <ul className="text-list">
            {recommendation.key_conditions.map((condition) => (
              <li key={condition}>{condition}</li>
            ))}
          </ul>
        </section>
        <section>
          <h3>Risks</h3>
          <ul className="text-list">
            {recommendation.key_risks.map((risk) => (
              <li key={risk}>{risk}</li>
            ))}
          </ul>
        </section>
      </div>

      <div className="evidence-note">
        <strong>Evidence status</strong>: {recommendation.evidence_status}
      </div>
    </article>
  );
}
