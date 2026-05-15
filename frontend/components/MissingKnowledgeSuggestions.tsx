import type { KnowledgeDocumentMetadata } from "@/lib/types";
import { getMissingKnowledgeSuggestions } from "@/lib/knowledge";

interface MissingKnowledgeSuggestionsProps {
  knowledge: KnowledgeDocumentMetadata[];
}

export default function MissingKnowledgeSuggestions({ knowledge }: MissingKnowledgeSuggestionsProps) {
  const suggestions = getMissingKnowledgeSuggestions(knowledge);

  return (
    <section className="card">
      <div className="card-header compact">
        <h3>Missing Knowledge Suggestions</h3>
        <span className="muted-count">{suggestions.length} gaps</span>
      </div>
      {suggestions.length ? (
        <ul className="text-list">
          {suggestions.map((suggestion) => (
            <li key={suggestion}>{suggestion}</li>
          ))}
        </ul>
      ) : (
        <p className="quiet">Core knowledge coverage looks reasonable for this local POC.</p>
      )}
    </section>
  );
}
