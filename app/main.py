"""
Main FastAPI application.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.api import jobs, rubrics, resumes
from app.core.config import settings


app = FastAPI(
    title="Resume Critique App",
    description="Deterministic resume critique with rubric-based evaluation",
    version="1.0.0"
)

# Mount static files
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(jobs.router, prefix="/api")
app.include_router(rubrics.router, prefix="/api")
app.include_router(resumes.router, prefix="/api")
app.include_router(resumes.router_resumes, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Landing page - redirect to login."""
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login/Signup page."""
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "supabase_url": settings.SUPABASE_URL,
            "supabase_key": settings.SUPABASE_KEY
        }
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page - list of jobs."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: str):
    """Job detail page."""
    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job_id": job_id}
    )


@app.get("/resumes/{resume_id}", response_class=HTMLResponse)
async def resume_detail(request: Request, resume_id: str):
    """Resume detail page."""
    return templates.TemplateResponse(
        "resume_detail.html",
        {"request": request, "resume_id": resume_id}
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }
