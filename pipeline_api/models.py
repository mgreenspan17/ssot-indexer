from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProgressMetric(BaseModel):
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    percent: float = Field(ge=0.0, le=100.0)


class PipelineStatusResponse(BaseModel):
    filesystem_count: int = Field(ge=0)
    stage1_count: int = Field(ge=0)
    stage2_count: int = Field(ge=0)
    stage3_count: int = Field(ge=0)
    db_indexed_count: int = Field(ge=0)
    canonical_count: int = Field(ge=0)
    shortcut_count: int = Field(ge=0)
    scanner_progress: ProgressMetric
    processed_progress: ProgressMetric
    ingestion_progress: ProgressMetric


class PipelineErrorsResponse(BaseModel):
    errors: list[dict[str, Any]]


class PipelineSummaryResponse(BaseModel):
    pipeline: str | None = None
    status: str | None = None
    stages: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    checkpoint: str | None = None
    log: str | None = None
    completed_at: str | None = None


class CategoryCount(BaseModel):
    category: str | None
    count: int = Field(ge=0)


class PipelineCategoriesResponse(BaseModel):
    categories: list[CategoryCount]


class LiveStatusResponse(BaseModel):
    current_stage: int = Field(ge=0)
    stage_description: str
    stage_elapsed_seconds: float = Field(ge=0.0)
    pipeline_active: bool
    db_active: bool
    next_expected_event: str
    last_log_line: str
    filesystem_count: int = Field(ge=0)
    stage1_count: int = Field(ge=0)
    stage2_count: int = Field(ge=0)
    stage3_count: int = Field(ge=0)
    crawl_phase: bool
    crawl_progress: str
    crawl_message: str
