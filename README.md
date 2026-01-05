# Resume Critique Web App

A resume critique web app with extra steps.

## Features

- Deterministic job-specific rubric generation
- Resume evaluation against explicit criteria
- Progress tracking across resume versions
- Bounded LLM usage for extraction and explanations
- Supabase authentication and storage

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