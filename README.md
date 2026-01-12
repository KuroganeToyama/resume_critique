# Resume Critique Web App

A LLM-powered resume critique web app with clear rubrics.

## Features

- Deterministic job-specific rubric generation
- Resume evaluation against explicit criteria
- Progress tracking across resume versions
- Bounded LLM usage for extraction and explanations
- Supabase authentication and storage

## Repository Structure

```
app/
  main.py                   - FastAPI application entry point
  
  core/                     - Core utilities
    config.py               - Environment settings and configuration
    auth.py                 - JWT authentication and user dependencies
    supabase.py             - Supabase client initialization
  
  api/                      - API endpoints
    jobs.py                 - Job CRUD (create, list, get, update, delete)
    resumes.py              - Resume upload, evaluation, progress tracking
  
  rubric/                   - Rubric system (deterministic)
    dimensions.py           - Fixed 17 dimensions with signals and scoring scales
    compiler.py             - Job posting → rubric compilation (regex-based)
    vocabulary.py           - Keyword → tag dictionary for dimension activation
  
  services/                 - Business logic
    job_service.py          - Job processing utilities
    resume_service.py       - Text extraction (PDF/DOCX) and LLM structure extraction
    evaluation_engine.py    - Deterministic scoring engine (signal checks, penalties)
    llm_client.py           - OpenAI API wrapper with JSON validation
  
  schemas/                  - Pydantic models
    schemas.py              - Request/response models for all endpoints
  
  models/                   - Database models
    database.py             - Table schemas (jobs, rubrics, resume_versions, evaluations)
  
  templates/                - Jinja2 HTML templates
    base.html               - Base template with navigation and common styles
    login.html              - Authentication page (signup/login)
    dashboard.html          - Job list with create modal
    job_detail.html         - Job view with resume upload and progress chart
    resume_detail.html      - Evaluation results with scores and recommendations

scripts/
  setup_database.py         - SQL schema with RLS policies and cascade deletes

schema.sql                  - Same SQL schema but with better visibility

.env.example                - Environment variables template
requirements.txt            - Python dependencies
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/Scripts/activate # MacOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run database migrations:
```bash
python scripts/setup_database.py
```

5. Start the application:
```bash
python main.py
```

The app will be available at http://localhost:8000