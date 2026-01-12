-- Drop tables if they exist (for reset)
DROP TABLE IF EXISTS evaluations CASCADE;
DROP TABLE IF EXISTS resume_versions CASCADE;
DROP TABLE IF EXISTS rubrics CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    job_posting_text TEXT NOT NULL,
    job_posting_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rubrics table
CREATE TABLE IF NOT EXISTS rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    base_rubric_id TEXT NOT NULL,
    base_rubric_version TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    dimension_overrides JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resume versions table
CREATE TABLE IF NOT EXISTS resume_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    storage_path TEXT NOT NULL,
    extracted_text TEXT,
    parse_meta JSONB
);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id UUID NOT NULL UNIQUE REFERENCES resume_versions(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    rubric_id UUID NOT NULL REFERENCES rubrics(id) ON DELETE CASCADE,
    overall_score DECIMAL(3,2) NOT NULL,
    dimension_scores JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can insert their own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can update their own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can delete their own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can view their own rubrics" ON rubrics;
DROP POLICY IF EXISTS "Users can insert their own rubrics" ON rubrics;
DROP POLICY IF EXISTS "Users can update their own rubrics" ON rubrics;
DROP POLICY IF EXISTS "Users can delete their own rubrics" ON rubrics;
DROP POLICY IF EXISTS "Users can view their own resume versions" ON resume_versions;
DROP POLICY IF EXISTS "Users can insert their own resume versions" ON resume_versions;
DROP POLICY IF EXISTS "Users can update their own resume versions" ON resume_versions;
DROP POLICY IF EXISTS "Users can delete their own resume versions" ON resume_versions;
DROP POLICY IF EXISTS "Users can view their own evaluations" ON evaluations;
DROP POLICY IF EXISTS "Users can insert their own evaluations" ON evaluations;
DROP POLICY IF EXISTS "Users can update their own evaluations" ON evaluations;
DROP POLICY IF EXISTS "Users can delete their own evaluations" ON evaluations;

-- RLS Policies for jobs
CREATE POLICY "Users can view their own jobs"
    ON jobs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own jobs"
    ON jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own jobs"
    ON jobs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own jobs"
    ON jobs FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for rubrics
CREATE POLICY "Users can view their own rubrics"
    ON rubrics FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own rubrics"
    ON rubrics FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own rubrics"
    ON rubrics FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own rubrics"
    ON rubrics FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for resume_versions
CREATE POLICY "Users can view their own resume versions"
    ON resume_versions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own resume versions"
    ON resume_versions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own resume versions"
    ON resume_versions FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own resume versions"
    ON resume_versions FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for evaluations
CREATE POLICY "Users can view their own evaluations"
    ON evaluations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own evaluations"
    ON evaluations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own evaluations"
    ON evaluations FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own evaluations"
    ON evaluations FOR DELETE
    USING (auth.uid() = user_id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_rubrics_job_id ON rubrics(job_id);
CREATE INDEX IF NOT EXISTS idx_resume_versions_job_id ON resume_versions(job_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_resume_id ON evaluations(resume_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_job_id ON evaluations(job_id);

-- Create storage bucket for resumes
INSERT INTO storage.buckets (id, name, public)
VALUES ('resumes', 'resumes', false)
ON CONFLICT (id) DO NOTHING;

-- Drop existing storage policy if exists
DROP POLICY IF EXISTS "Users can access their own resume files" ON storage.objects;

-- Storage RLS policy
CREATE POLICY "Users can access their own resume files"
    ON storage.objects FOR ALL
    USING (
        bucket_id = 'resumes' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );