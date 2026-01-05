"""
Job endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Tuple
from supabase import Client
from app.core.auth import get_user_client
from app.schemas.schemas import JobCreate, JobResponse, JobUpdate
from app.services.job_service import JobProcessingService
from app.rubric.compiler import RubricCompiler
from app.core.config import settings
from datetime import datetime, timezone
import uuid


router = APIRouter(prefix="/jobs", tags=["jobs"])
job_service = JobProcessingService()
rubric_compiler = RubricCompiler()


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    user_data: Tuple[str, Client] = Depends(get_user_client)
):
    """Create a new job posting and generate rubric for that job posting."""
    user_id, supabase = user_data
    
    # Compile rubric from job posting
    rubric_result = rubric_compiler.compile_rubric(job_data.job_posting_text)
    
    # Create job record
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    job_record = {
        "id": job_id,
        "user_id": user_id,
        "title": job_data.title,
        "company_name": job_data.company_name,
        "job_posting_text": job_data.job_posting_text,
        "job_posting_hash": rubric_result["job_posting_hash"],
        "created_at": now,
        "updated_at": now
    }
    
    result = supabase.table("jobs").insert(job_record).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )
    
    # Create rubric record
    rubric_id = str(uuid.uuid4())
    rubric_record = {
        "id": rubric_id,
        "job_id": job_id,
        "user_id": user_id,
        "base_rubric_id": "canonical",
        "base_rubric_version": settings.BASE_RUBRIC_VERSION,
        "ruleset_version": settings.RULESET_VERSION,
        "dimension_overrides": rubric_result["dimension_configs"],
        "created_at": now
    }
    
    supabase.table("rubrics").insert(rubric_record).execute()
    
    return JobResponse(**result.data[0])


@router.get("", response_model=List[JobResponse])
async def list_jobs(user_data: Tuple[str, Client] = Depends(get_user_client)):
    """List all jobs for the current user."""
    user_id, supabase = user_data
    
    result = supabase.table("jobs").select("*").eq("user_id", user_id).execute()
    
    return [JobResponse(**job) for job in result.data]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user_data: Tuple[str, Client] = Depends(get_user_client)
):
    """Get a specific job."""
    user_id, supabase = user_data
    
    result = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return JobResponse(**result.data[0])


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    user_data: Tuple[str, Client] = Depends(get_user_client)
):
    """Update a job."""
    user_id, supabase = user_data
    
    # Verify job exists and belongs to user
    existing = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).execute()
    
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Build update data
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if job_update.title is not None:
        update_data["title"] = job_update.title
    
    if job_update.company_name is not None:
        update_data["company_name"] = job_update.company_name
    
    if job_update.job_posting_text is not None:
        update_data["job_posting_text"] = job_update.job_posting_text
        
        # Recompile rubric if job posting changed
        rubric_result = rubric_compiler.compile_rubric(job_update.job_posting_text)
        update_data["job_posting_hash"] = rubric_result["job_posting_hash"]
        
        # Update rubric
        supabase.table("rubrics").update({
            "dimension_overrides": rubric_result["dimension_configs"],
            "ruleset_version": settings.RULESET_VERSION
        }).eq("job_id", job_id).execute()
    
    result = supabase.table("jobs").update(update_data).eq("id", job_id).execute()
    
    return JobResponse(**result.data[0])


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    user_data: Tuple[str, Client] = Depends(get_user_client)
):
    """Delete a job."""
    user_id, supabase = user_data
    
    result = supabase.table("jobs").delete().eq("id", job_id).eq("user_id", user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return None
