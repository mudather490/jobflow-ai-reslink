-- ====================================================================
-- JobFlow.ai & ResLink Studio - Complete Supabase Master Schema
-- ====================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Profiles Table (User Account, Resume Data & Contact Settings)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE,
    full_name TEXT NOT NULL,
    headline TEXT,
    phone_number TEXT,
    location TEXT,
    linkedin TEXT,
    github TEXT,
    portfolio TEXT,
    summary TEXT,
    skills TEXT[] DEFAULT '{}',
    categorized_skills JSONB DEFAULT '{}'::jsonb,
    experience JSONB DEFAULT '[]'::jsonb,
    projects JSONB DEFAULT '[]'::jsonb,
    education JSONB DEFAULT '[]'::jsonb,
    certifications JSONB DEFAULT '[]'::jsonb,
    additional_background TEXT,
    target_role TEXT,
    subscription_tier TEXT DEFAULT 'starter', -- starter, pro, executive
    role TEXT DEFAULT 'user', -- user, admin, owner
    is_admin BOOLEAN DEFAULT false,
    gumroad_license_key TEXT,
    email_alerts_enabled BOOLEAN DEFAULT true,
    whatsapp_alerts_enabled BOOLEAN DEFAULT true,
    telegram_alerts_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. ResLinks Table (Video Pitch Studio & Public Recruiter Hub)
CREATE TABLE IF NOT EXISTS public.reslinks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    slug TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    tagline TEXT,
    location TEXT,
    summary_bio TEXT,
    video_url TEXT,
    video_duration NUMERIC DEFAULT 60.0,
    theme TEXT DEFAULT 'glassmorphic_dark',
    selected_cv_template TEXT DEFAULT 'modern', -- modern, harvard_consulting, corporate_elite, tech_specialist
    target_job_title TEXT,
    target_company TEXT,
    senior_contact TEXT,
    pitch_script TEXT,
    linkedin_outreach_note TEXT,
    competency_badges TEXT[] DEFAULT '{}',
    cta_settings JSONB DEFAULT '{"calendly_url": "https://calendly.com", "enable_booking": true, "enable_cv_download": true}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Real-time Recruiter Analytics & Event Telemetry
CREATE TABLE IF NOT EXISTS public.reslink_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reslink_slug TEXT NOT NULL,
    event_type TEXT NOT NULL, -- page_view, video_play, cv_download, calendly_click
    device TEXT DEFAULT 'desktop',
    referrer TEXT,
    watch_seconds NUMERIC DEFAULT 0,
    ip_hash TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Saved & Discovered Jobs Tracker
CREATE TABLE IF NOT EXISTS public.saved_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    job_id TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    posted_date TEXT,
    job_url TEXT NOT NULL,
    salary TEXT,
    match_score NUMERIC DEFAULT 85,
    status TEXT DEFAULT 'discovered', -- discovered, tailored, applied, archived
    tailored_pdf_url TEXT,
    tailored_docx_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Applications & Notifications Audit Table
CREATE TABLE IF NOT EXISTS public.applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    job_id TEXT NOT NULL,
    application_id TEXT NOT NULL UNIQUE,
    tailored_pdf_url TEXT,
    tailored_docx_url TEXT,
    status TEXT DEFAULT 'applied',
    notification_dispatched BOOLEAN DEFAULT false,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. Questionnaire Memory Bank (Autonomous Auto-Apply Q&A)
CREATE TABLE IF NOT EXISTS public.questionnaire_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    confidence NUMERIC DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. High-Performance Lookups Indexes
CREATE INDEX IF NOT EXISTS idx_reslinks_slug ON public.reslinks(slug);
CREATE INDEX IF NOT EXISTS idx_reslink_analytics_slug ON public.reslink_analytics(reslink_slug);
CREATE INDEX IF NOT EXISTS idx_reslink_analytics_event ON public.reslink_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_status ON public.saved_jobs(status);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON public.applications(job_id);

-- 9. Row Level Security (RLS) Configuration
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reslinks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reslink_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questionnaire_memory ENABLE ROW LEVEL SECURITY;

-- Allow public read of candidate public links
CREATE POLICY "Allow public read of reslinks by slug" 
ON public.reslinks FOR SELECT USING (true);

-- Allow public tracking of analytics events
CREATE POLICY "Allow public insert of analytics telemetry" 
ON public.reslink_analytics FOR INSERT WITH CHECK (true);

-- Service role / backend full access policies
CREATE POLICY "Service full access on profiles" ON public.profiles FOR ALL USING (true);
CREATE POLICY "Service full access on reslinks" ON public.reslinks FOR ALL USING (true);
CREATE POLICY "Service full access on analytics" ON public.reslink_analytics FOR ALL USING (true);
CREATE POLICY "Service full access on saved_jobs" ON public.saved_jobs FOR ALL USING (true);
CREATE POLICY "Service full access on applications" ON public.applications FOR ALL USING (true);
CREATE POLICY "Service full access on questionnaire" ON public.questionnaire_memory FOR ALL USING (true);

-- 10. Seed Master Owner & Executive Admin Account
INSERT INTO public.profiles (
    email,
    full_name,
    headline,
    location,
    target_role,
    subscription_tier,
    role,
    is_admin
) VALUES (
    'mudatherkbyer@gmail.com',
    'Mudather Mohammed',
    'Junior AI Engineer | Machine Learning Engineer',
    'Worldwide Remote',
    'Junior AI Engineer / Machine Learning Engineer',
    'executive',
    'owner',
    true
) ON CONFLICT (email) DO UPDATE SET
    subscription_tier = 'executive',
    role = 'owner',
    is_admin = true;

