"""
Rubric endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import get_current_user
from app.core.supabase import supabase
from app.schemas.schemas import RubricResponse


router = APIRouter(prefix="/jobs", tags=["rubrics"])


@router.get("/{job_id}/rubric", response_model=RubricResponse)
async def get_rubric(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get the rubric for a specific job."""
    
    # Verify job exists and belongs to user
    job_result = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).execute()
    
    if not job_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get rubric
    rubric_result = supabase.table("rubrics").select("*").eq("job_id", job_id).execute()
    
    if not rubric_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric not found"
        )
    
    return RubricResponse(**rubric_result.data[0])
