from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from pydantic import BaseModel, Field

class Audience(StrEnum):
    rd = "rd"
    sales = "sales"
    marketing = "marketing"
    executive = "executive"

class PatentRecord(BaseModel):
    patent_id: str = Field(..., description="Publication number or stable patent identifier.")
    title: str = ""
    abstract: str = ""
    claims: str = ""
    description: str = ""
    assignees: list[str] = Field(default_factory=list)
    inventors: list[str] = Field(default_factory=list)
    publication_date: str | None = None
    filing_date: str | None = None
    jurisdiction: str | None = None
    cpc_codes: list[str] = Field(default_factory=list)
    ipc_codes: list[str] = Field(default_factory=list)
    source_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class PatentChunk(BaseModel):
    chunk_id: str
    patent_id: str
    section: Literal["title", "abstract", "claim", "description", "metadata"]
    text: str
    token_estimate: int
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvidenceItem(BaseModel):
    patent_id: str
    section: str
    text: str
    score: float
    source_url: str | None = None

class ReportRequest(BaseModel):
    query: str
    audience: Audience = Audience.rd
    top_k: int = 5
    model: str | None = None

class ReportSection(BaseModel):
    heading: str
    content: str
    evidence_ids: list[str] = Field(default_factory=list)

class PatentReport(BaseModel):
    report_id: str
    query: str
    audience: Audience
    model: str
    generated_at: datetime
    executive_summary: str
    sections: list[ReportSection]
    evidence: list[EvidenceItem]
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvaluationExample(BaseModel):
    query: str
    audience: Audience
    expected_terms: list[str] = Field(default_factory=list)
    forbidden_terms: list[str] = Field(default_factory=list)
    expected_patent_ids: list[str] = Field(default_factory=list)

class EvaluationResult(BaseModel):
    query: str
    audience: Audience
    model: str
    evidence_coverage: float
    expected_term_recall: float
    forbidden_term_rate: float
    hallucination_risk: float
    latency_seconds: float
    notes: str
