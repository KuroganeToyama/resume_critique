# Resume Critique Web App

A LLM-powered resume critique web app with clear rubrics for any job type.

## Features

- **Universal Job Support**: Works for tech, healthcare, finance, sales, education, and more
- **Hybrid Rubric Generation**: LLM-powered job analysis with deterministic evaluation
- Resume evaluation against explicit criteria
- Progress tracking across resume versions
- Bounded LLM usage for extraction and explanations
- Supabase authentication and storage

## How It Works

### Rubric Generation (LLM-Powered)
```
Job Posting → LLM Analysis → Dimension Mapping → Custom Rubric
```

1. **Job Analysis**: LLM extracts role level, domain, requirements, and priorities
2. **Dimension Mapping**: LLM decides which dimensions matter and assigns weights
3. **Rubric Storage**: Configuration saved for consistent evaluation

### Resume Evaluation (Deterministic)
```
Resume Upload → Text Extraction → Structure Parsing → Signal Checks → Scores
```

1. **Text Extraction**: PyPDF2/python-docx extracts raw text
2. **Structure Parsing**: LLM identifies sections and bullets with metadata
3. **Signal Checks**: Deterministic checks (action verbs, metrics, tools, outcomes)
4. **Scoring**: Pass rates mapped to 1-5 scale with content penalties
5. **Recommendations**: Top priorities and quick wins generated

**Key Principle**: Same resume + same rubric = same score (deterministic)

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
  
  rubric/                   - Rubric system
    dimensions.py           - Fixed 17 dimensions with signals and scoring scales
    compiler.py             - Hybrid compiler (LLM + regex fallback)
    vocabulary.py           - Keyword → tag dictionary (for regex fallback)
  
  services/                 - Business logic
    job_service.py          - Job processing utilities
    resume_service.py       - Text extraction (PDF/DOCX) and LLM structure extraction
    evaluation_engine.py    - Deterministic scoring engine (signal checks, penalties)
    llm_client.py           - OpenAI API wrapper with JSON validation
  
  schemas/                  - Pydantic models
    schemas.py              - Request/response models (includes JobAnalysis, DimensionMapping)
  
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

## Architecture

### The 17 Dimensions

Fixed set of evaluation criteria across 4 categories:

**Core (4)**: Always applicable
- clarity, evidence, impact, structure

**Alignment (4)**: Job-specific matching
- skill_alignment, tooling_match, domain_relevance, level_appropriateness

**Risk (3)**: Quality indicators
- signal_density, consistency, security_awareness

**Contextual (6)**: Specialized aspects
- communication, leadership, data_rigor, research_quality, collaboration, innovation

### LLM Usage (Bounded)

**Rubric Generation (one-time per job)**:
- Job analysis: Extract requirements, domain, role level
- Dimension mapping: Decide which dimensions apply and their weights

**Resume Processing (one-time per upload)**:
- Structure extraction: Parse sections and bullets
- Optional rewrite suggestions (max 5)

**Evaluation Scoring**: No LLM (fully deterministic)

### Scoring Logic

**Signal Checks**: Each dimension has signals (e.g., "has_metrics", "clear_action_verbs")
- Run checks on every bullet
- Track failures

**Pass Rate**: `(total_checks - failures) / total_checks`

**Score Mapping** (stricter thresholds):
- 95%+ → 5.0
- 85%+ → 4.0
- 70%+ → 3.0
- 50%+ → 2.0
- <50% → 1.0

**Content Penalties**:
- No work experience → 1.0 for critical dimensions
- <3 bullets → 1.5
- <5 bullets → 30% penalty
- <8 bullets → 15% penalty

**Overall Score**: Weighted average of dimension scores

## Setup

### Local Development

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

### Docker Deployment

Self-host using Docker for production deployments.

#### Quick Start

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase and OpenAI credentials
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - App: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

#### Environment Variables

Required variables in `.env`:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key
LLM_MODEL=gpt-4-turbo-preview

# App
SECRET_KEY=your-secret-key-here
APP_ENV=production
```

#### Docker Commands

**Build**:
```bash
docker-compose build
```

**Start**:
```bash
docker-compose up -d
```

**Stop**:
```bash
docker-compose down
```

**View Logs**:
```bash
docker-compose logs -f web
```

**Restart**:
```bash
docker-compose restart
```

**Rebuild and Restart**:
```bash
docker-compose up -d --build
```

#### Monitoring

**Health Check**:
```bash
curl http://localhost:8000/health
```

**Container Status**:
```bash
docker-compose ps
```

**Resource Usage**:
```bash
docker stats resume-critique-web
```