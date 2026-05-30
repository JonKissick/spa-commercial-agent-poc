from enum import StrEnum

from pydantic import BaseModel, Field

from app.calculators.schemas import NpvCalculationResponse
from app.rag.schemas import RagContextBundle
from app.schemas import CommercialEvaluationResponse


class AgentMode(StrEnum):
    MOCK_BEDROCK_RAG = "mock_bedrock_rag"


class AgentGroundingStatus(StrEnum):
    DRAFT_REQUIRES_REVIEW = "draft_requires_review"


class BoardPaperDraftRequest(BaseModel):
    analysis: CommercialEvaluationResponse
    npv: NpvCalculationResponse | None = None
    rag_context: RagContextBundle | None = None
    audience: str = "board"


class BoardPaperDraftResponse(BaseModel):
    mode: AgentMode = AgentMode.MOCK_BEDROCK_RAG
    grounding_status: AgentGroundingStatus = AgentGroundingStatus.DRAFT_REQUIRES_REVIEW
    title: str
    executive_summary: str
    recommendation: str
    valuation_summary: list[str] = Field(default_factory=list)
    commercial_risks: list[str] = Field(default_factory=list)
    key_conditions: list[str] = Field(default_factory=list)
    human_review_required: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ManagementSlidePackRequest(BaseModel):
    analysis: CommercialEvaluationResponse
    npv: NpvCalculationResponse | None = None
    rag_context: RagContextBundle | None = None
    audience: str = "management"


class SlideDraft(BaseModel):
    slide_number: int
    title: str
    headline: str
    bullets: list[str] = Field(default_factory=list)
    speaker_notes: str
    citations: list[str] = Field(default_factory=list)


class ManagementSlidePackResponse(BaseModel):
    mode: AgentMode = AgentMode.MOCK_BEDROCK_RAG
    grounding_status: AgentGroundingStatus = AgentGroundingStatus.DRAFT_REQUIRES_REVIEW
    title: str
    slides: list[SlideDraft]
    human_review_required: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
