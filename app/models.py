from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


class SearchResult(BaseModel):
    title: str = Field(..., min_length=1)
    url: HttpUrl
    snippet: str = Field(..., min_length=1)


class Fact(BaseModel):
    fact: str = Field(..., min_length=1)
    source_url: HttpUrl
    source_title: str = Field(..., min_length=1)
    fact_type: Literal["stat", "claim", "definition", "trend", "contradiction"]
    evidence_snippet: str = Field(..., min_length=1)
    confidence: Literal["high", "medium", "low"]


class Summary(BaseModel):
    context: str = ""
    insights: list[str] = Field(default_factory=list)
    implications: list[str] = Field(default_factory=list)
    contrarian_angle: str = ""


class ValidationIssue(BaseModel):
    step: str = Field(..., min_length=1)
    severity: Literal["low", "medium", "high"]
    message: str = Field(..., min_length=1)


class StepLog(BaseModel):
    step: str = Field(..., min_length=1)
    status: Literal["ok", "warning", "error"]
    started_at: str
    ended_at: str
    items_in: int = 0
    items_out: int = 0
    message: str = ""


class ValidationState(BaseModel):
    draft_ok: bool = False
    style_ok: bool = False
    issues: list[ValidationIssue] = Field(default_factory=list)


class PipelineOutput(BaseModel):
    run_id: str
    topic: str
    post: str
    image_prompts: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    summary: Summary = Field(default_factory=Summary)
    validation: ValidationState = Field(default_factory=ValidationState)
    errors: list[str] = Field(default_factory=list)