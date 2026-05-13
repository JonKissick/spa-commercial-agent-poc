"use client";

import { useState } from "react";
import ContractSummaryCard from "@/components/ContractSummaryCard";
import OptionalityRegister from "@/components/OptionalityRegister";
import ProvisionRegister from "@/components/ProvisionRegister";
import RecommendationMemo from "@/components/RecommendationMemo";
import UploadPanel from "@/components/UploadPanel";
import ValuationInputPack from "@/components/ValuationInputPack";
import { analyzeContract } from "@/lib/api";
import type { CommercialEvaluationResponse } from "@/lib/types";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<CommercialEvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleAnalyze() {
    if (!file) {
      setError("Choose a PDF before running analysis.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await analyzeContract(file);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="intro">
        <p className="eyebrow">Commercial SPA review POC</p>
        <h1>SPA Commercial Evaluation Agent</h1>
        <p>
          Upload an SPA PDF to exercise the V1 pipeline shape: text extraction,
          placeholder analysis, and structured commercial outputs for review.
        </p>
      </section>

      <UploadPanel
        file={file}
        isLoading={isLoading}
        error={error}
        onFileChange={setFile}
        onAnalyze={handleAnalyze}
      />

      {isLoading && <div className="status-panel">Analyzing uploaded PDF...</div>}

      {result && (
        <section className="results-grid" aria-label="Commercial evaluation results">
          <ContractSummaryCard summary={result.contract_summary} />
          <ProvisionRegister items={result.provision_register} />
          <ValuationInputPack pack={result.valuation_input_pack} />
          <OptionalityRegister items={result.optionality_register} />
          <RecommendationMemo recommendation={result.recommendation} />
        </section>
      )}
    </main>
  );
}
