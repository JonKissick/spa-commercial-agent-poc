"use client";

import { useCallback, useEffect, useState } from "react";
import AnalyzeContractPanel from "@/components/AnalyzeContractPanel";
import NpvCalculatorPanel from "@/components/NpvCalculatorPanel";
import RagIngestPanel from "@/components/RagIngestPanel";
import RagLibraryPanel from "@/components/RagLibraryPanel";
import RagRetrievalPanel from "@/components/RagRetrievalPanel";
import SystemStatusPanel from "@/components/SystemStatusPanel";
import WorkbenchTabs, { type WorkbenchTab } from "@/components/WorkbenchTabs";
import { analyzeContract, getHealth, getRagKnowledge, getSystemStatus } from "@/lib/api";
import type { CommercialEvaluationResponse, HealthResponse, KnowledgeDocumentMetadata, SystemStatus } from "@/lib/types";

export default function Home() {
  const [activeTab, setActiveTab] = useState<WorkbenchTab>("analyze");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<CommercialEvaluationResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [knowledge, setKnowledge] = useState<KnowledgeDocumentMetadata[]>([]);
  const [knowledgeError, setKnowledgeError] = useState<string | null>(null);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [systemError, setSystemError] = useState<string | null>(null);

  const refreshKnowledge = useCallback(async () => {
    setKnowledgeLoading(true);
    setKnowledgeError(null);
    try {
      setKnowledge(await getRagKnowledge());
    } catch (err) {
      setKnowledgeError(err instanceof Error ? err.message : "Unable to load RAG knowledge.");
    } finally {
      setKnowledgeLoading(false);
    }
  }, []);

  const refreshSystem = useCallback(async () => {
    setSystemError(null);
    try {
      const [healthResponse, statusResponse] = await Promise.all([getHealth(), getSystemStatus()]);
      setHealth(healthResponse);
      setSystemStatus(statusResponse);
    } catch (err) {
      setSystemError(err instanceof Error ? err.message : "Unable to load system status.");
    }
  }, []);

  useEffect(() => {
    refreshKnowledge();
    refreshSystem();
  }, [refreshKnowledge, refreshSystem]);

  async function handleAnalyze() {
    if (!file) {
      setAnalysisError("Choose a PDF before running analysis.");
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      setResult(await analyzeContract(file));
      await refreshKnowledge();
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="intro workbench-hero">
        <p className="eyebrow">Commercial SPA review POC</p>
        <h1>SPA Commercial Evaluation Agent</h1>
        <p>
          A local workbench for PDF analysis, structured commercial outputs, RAG knowledge ingestion,
          retrieval testing, and non-secret system status.
        </p>
      </section>

      <WorkbenchTabs activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "analyze" && (
        <AnalyzeContractPanel
          file={file}
          result={result}
          error={analysisError}
          isLoading={isAnalyzing}
          knowledge={knowledge}
          knowledgeError={knowledgeError}
          knowledgeLoading={knowledgeLoading}
          onFileChange={setFile}
          onAnalyze={handleAnalyze}
        />
      )}

      {activeTab === "library" && (
        <RagLibraryPanel knowledge={knowledge} isLoading={knowledgeLoading} error={knowledgeError} onRefresh={refreshKnowledge} />
      )}

      {activeTab === "ingest" && <RagIngestPanel onIngested={refreshKnowledge} />}

      {activeTab === "retrieval" && <RagRetrievalPanel />}

      {activeTab === "npv" && <NpvCalculatorPanel />}

      {activeTab === "status" && (
        <SystemStatusPanel health={health} status={systemStatus} knowledge={knowledge} error={systemError} onRefresh={refreshSystem} />
      )}
    </main>
  );
}
