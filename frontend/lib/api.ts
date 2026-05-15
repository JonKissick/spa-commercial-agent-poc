import type {
  CommercialEvaluationResponse,
  HealthResponse,
  IngestRagTextPayload,
  IngestionResult,
  NpvCalculationRequest,
  NpvCalculationResponse,
  KnowledgeDocumentMetadata,
  RetrievalResult,
  RetrieveRagPayload,
  SystemStatus,
  SeedPackResult,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export async function analyzeContract(file: File): Promise<CommercialEvaluationResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<CommercialEvaluationResponse>("/analyze", { method: "POST", body: formData });
}

export async function getRagKnowledge(): Promise<KnowledgeDocumentMetadata[]> {
  return requestJson<KnowledgeDocumentMetadata[]>("/rag/knowledge");
}

export async function ingestRagText(payload: IngestRagTextPayload): Promise<IngestionResult> {
  return requestJson<IngestionResult>("/rag/ingest-text", { method: "POST", body: JSON.stringify(payload) });
}

export async function retrieveRag(payload: RetrieveRagPayload): Promise<RetrievalResult[]> {
  return requestJson<RetrievalResult[]>("/rag/retrieve", { method: "POST", body: JSON.stringify(payload) });
}

export async function getSystemStatus(): Promise<SystemStatus> {
  return requestJson<SystemStatus>("/system/status");
}

export async function calculateNpv(payload: NpvCalculationRequest): Promise<NpvCalculationResponse> {
  return requestJson<NpvCalculationResponse>("/calculators/npv", { method: "POST", body: JSON.stringify(payload) });
}

export async function seedRagStarterPack(): Promise<SeedPackResult> {
  return requestJson<SeedPackResult>("/rag/seed", { method: "POST" });
}
