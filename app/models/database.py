"""
Database models representing Supabase tables.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, UUID4


class Job(BaseModel):
    """Job posting model."""
    id: UUID4
    user_id: UUID4
    title: str
    company_name: str
    job_posting_text: str
    job_posting_hash: str
    created_at: datetime
    updated_at: datetime


class Rubric(BaseModel):
    """Job-specific rubric model."""
    id: UUID4
    job_id: UUID4
    user_id: UUID4
    base_rubric_id: str
    base_rubric_version: str
    ruleset_version: str
    dimension_overrides: Dict[str, Any]
    created_at: datetime


class ResumeVersion(BaseModel):
    """Resume version model."""
    id: UUID4
    job_id: UUID4
    user_id: UUID4
    version_label: str
    uploaded_at: datetime
    storage_path: str
    extracted_text: Optional[str] = None
    parse_meta: Optional[Dict[str, Any]] = None


class Evaluation(BaseModel):
    """Resume evaluation model."""
    id: UUID4
    resume_id: UUID4
    job_id: UUID4
    user_id: UUID4
    rubric_id: UUID4
    overall_score: float
    dimension_scores: Dict[str, Any]
    recommendations: Dict[str, Any]
    created_at: datetime
