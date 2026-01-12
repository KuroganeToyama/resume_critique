"""
Pydantic schemas for API requests and responses.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, UUID4


# Job Schemas
class JobCreate(BaseModel):
    """Schema for creating a job."""
    title: str
    company_name: str
    job_posting_text: str


class JobResponse(BaseModel):
    """Schema for job response."""
    id: UUID4
    user_id: UUID4
    title: str
    company_name: str
    job_posting_text: str
    job_posting_hash: str
    created_at: datetime
    updated_at: datetime


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    title: Optional[str] = None
    company_name: Optional[str] = None
    job_posting_text: Optional[str] = None


# Rubric Schemas
class RubricResponse(BaseModel):
    """Schema for rubric response."""
    id: UUID4
    job_id: UUID4
    base_rubric_version: str
    ruleset_version: str
    dimension_overrides: Dict[str, Any]
    created_at: datetime


class DimensionConfig(BaseModel):
    """Configuration for a single rubric dimension."""
    name: str
    weight: float
    enabled: bool
    signals: List[str]
    scoring_scale: Dict[int, str]
    feedback_templates: List[str]


# Resume Schemas
class ResumeUpload(BaseModel):
    """Schema for resume upload."""
    version_label: str


class ResumeResponse(BaseModel):
    """Schema for resume response."""
    id: UUID4
    job_id: UUID4
    user_id: UUID4
    version_label: str
    uploaded_at: datetime
    storage_path: str
    extracted_text: Optional[str] = None


# Evaluation Schemas
class EvaluationResponse(BaseModel):
    """Schema for evaluation response."""
    id: UUID4
    resume_id: UUID4
    job_id: UUID4
    rubric_id: UUID4
    overall_score: float
    dimension_scores: Dict[str, Any]
    recommendations: Dict[str, Any]
    created_at: datetime


class ProgressEntry(BaseModel):
    """Schema for progress tracking."""
    version_label: str
    uploaded_at: datetime
    overall_score: float
    dimension_scores: Dict[str, float]


class ProgressResponse(BaseModel):
    """Schema for progress response."""
    job_id: UUID4
    versions: List[ProgressEntry]


# LLM Contract Schemas
class JobSectionSplit(BaseModel):
    """LLM contract for job posting section split."""
    required: str
    preferred: str
    responsibilities: str
    other: str


class TagEvidence(BaseModel):
    """Evidence for a detected tag."""
    quote: str


class JobTag(BaseModel):
    """LLM contract for job tag detection."""
    tag: str
    section: str
    evidence: List[TagEvidence]


class JobTagsResponse(BaseModel):
    """LLM response for job tags."""
    tags: List[JobTag]


class ResumeBullet(BaseModel):
    """Extracted resume bullet."""
    bullet_index: int
    text: str
    has_metric: bool
    tools: List[str]


class ResumeExtraction(BaseModel):
    """LLM contract for resume extraction."""
    sections: Dict[str, List[ResumeBullet]]


class RewriteSuggestion(BaseModel):
    """LLM contract for rewrite suggestion."""
    bullet_index: int
    original: str
    rewrite: str
    why: str


class RewriteSuggestionsResponse(BaseModel):
    """LLM response for rewrite suggestions."""
    suggestions: List[RewriteSuggestion]


class JobAnalysis(BaseModel):
    """LLM analysis of job posting."""
    role_level: str  # "junior", "mid", "senior", "lead"
    domain: str  # "technology", "healthcare", "finance", "sales", etc.
    job_function: str  # "engineering", "nursing", "accounting", "marketing"
    key_requirements: List[str]  # Main requirements from job
    required_skills: List[str]  # Critical skills needed
    preferred_skills: List[str]  # Nice-to-have skills
    evaluation_priorities: Dict[str, str]  # dimension_name -> "high"/"medium"/"low"


class DimensionWeight(BaseModel):
    """Weight configuration for a dimension."""
    enabled: bool
    weight: float
    reasoning: str  # Why this dimension matters for this job


class DimensionMapping(BaseModel):
    """LLM mapping of job requirements to dimensions."""
    dimensions: Dict[str, DimensionWeight]  # dimension_name -> weight config
