"""
Resume endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List
from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.schemas.schemas import (
    ResumeResponse,
    EvaluationResponse,
    ProgressResponse,
    ProgressEntry
)
from app.services.resume_service import ResumeProcessingService
from app.services.evaluation_engine import EvaluationEngine
from datetime import datetime, timezone
import uuid


router = APIRouter(prefix="/jobs", tags=["resumes"])
resume_service = ResumeProcessingService()
evaluation_engine = EvaluationEngine()


@router.post("/{job_id}/resumes", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    job_id: str,
    version_label: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload a resume for a job."""
    
    # Verify job exists and belongs to user
    job_result = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).execute()
    
    if not job_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Extract text from file
    try:
        resume_text = resume_service.extract_text_from_file(file_content, file.filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Generate resume ID
    resume_id = str(uuid.uuid4())
    
    # Upload file to Supabase Storage
    storage_path = f"{user_id}/{job_id}/{resume_id}/{file.filename}"
    
    try:
        supabase.storage.from_("resumes").upload(
            storage_path,
            file_content,
            file_options={"content-type": file.content_type}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    # Extract resume structure
    resume_extraction = resume_service.extract_structure(resume_text)
    
    # Create resume record
    now = datetime.now(timezone.utc).isoformat()
    resume_record = {
        "id": resume_id,
        "job_id": job_id,
        "user_id": user_id,
        "version_label": version_label,
        "uploaded_at": now,
        "storage_path": storage_path,
        "extracted_text": resume_text,
        "parse_meta": {"sections": list(resume_extraction.sections.keys())}
    }
    
    result = supabase.table("resume_versions").insert(resume_record).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create resume record"
        )
    
    # Get rubric for evaluation
    rubric_result = supabase.table("rubrics").select("*").eq("job_id", job_id).execute()
    
    if not rubric_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric not found"
        )
    
    rubric = rubric_result.data[0]
    
    # Evaluate resume
    evaluation_result = evaluation_engine.evaluate(
        resume_extraction,
        {
            "dimension_configs": rubric["dimension_overrides"]
        }
    )
    
    # Create evaluation record
    evaluation_id = str(uuid.uuid4())
    evaluation_record = {
        "id": evaluation_id,
        "resume_id": resume_id,
        "job_id": job_id,
        "user_id": user_id,
        "rubric_id": rubric["id"],
        "overall_score": evaluation_result["overall_score"],
        "dimension_scores": evaluation_result["dimension_scores"],
        "recommendations": evaluation_result["recommendations"],
        "created_at": now
    }
    
    supabase.table("evaluations").insert(evaluation_record).execute()
    
    return ResumeResponse(**result.data[0])


@router.get("/{job_id}/resumes", response_model=List[ResumeResponse])
async def list_resumes(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """List all resume versions for a job."""
    
    # Verify job exists
    job_result = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).execute()
    
    if not job_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    result = supabase.table("resume_versions").select("*").eq("job_id", job_id).execute()
    
    return [ResumeResponse(**resume) for resume in result.data]


@router.get("/{job_id}/progress", response_model=ProgressResponse)
async def get_progress(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get progress tracking across resume versions."""
    
    # Verify job exists
    job_result = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).execute()
    
    if not job_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get all resumes for this job
    resumes = supabase.table("resume_versions").select("*").eq("job_id", job_id).order("uploaded_at").execute()
    
    if not resumes.data:
        return ProgressResponse(job_id=job_id, versions=[])
    
    # Get evaluations for these resumes
    resume_ids = [r["id"] for r in resumes.data]
    evaluations = supabase.table("evaluations").select("*").in_("resume_id", resume_ids).execute()
    
    # Build progress entries
    eval_map = {e["resume_id"]: e for e in evaluations.data}
    
    progress_entries = []
    for resume in resumes.data:
        evaluation = eval_map.get(resume["id"])
        if evaluation:
            # Extract dimension scores (just the numeric score)
            dim_scores = {
                dim_name: dim_data["score"]
                for dim_name, dim_data in evaluation["dimension_scores"].items()
            }
            
            progress_entries.append(ProgressEntry(
                version_label=resume["version_label"],
                uploaded_at=resume["uploaded_at"],
                overall_score=evaluation["overall_score"],
                dimension_scores=dim_scores
            ))
    
    return ProgressResponse(job_id=job_id, versions=progress_entries)


# Get specific resume
router_resumes = APIRouter(prefix="/resumes", tags=["resumes"])


@router_resumes.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific resume version."""
    
    result = supabase.table("resume_versions").select("*").eq("id", resume_id).eq("user_id", user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return ResumeResponse(**result.data[0])


@router_resumes.get("/{resume_id}/evaluation", response_model=EvaluationResponse)
async def get_evaluation(
    resume_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get evaluation for a specific resume."""
    
    # Verify resume belongs to user
    resume_result = supabase.table("resume_versions").select("*").eq("id", resume_id).eq("user_id", user_id).execute()
    
    if not resume_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Get evaluation
    eval_result = supabase.table("evaluations").select("*").eq("resume_id", resume_id).execute()
    
    if not eval_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    return EvaluationResponse(**eval_result.data[0])


@router_resumes.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a resume version and its file from storage."""
    
    # Get resume to verify ownership and get storage path
    resume_result = supabase.table("resume_versions").select("*").eq("id", resume_id).eq("user_id", user_id).execute()
    
    if not resume_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    resume = resume_result.data[0]
    
    # Delete file from storage if it exists
    if resume.get("storage_path"):
        try:
            supabase.storage.from_("resumes").remove([resume["storage_path"]])
        except Exception as e:
            # Log error but continue with database deletion
            print(f"Warning: Failed to delete file from storage: {e}")
    
    # Delete from database (CASCADE will delete evaluation too)
    result = supabase.table("resume_versions").delete().eq("id", resume_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return None
