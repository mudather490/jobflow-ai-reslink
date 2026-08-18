-- ====================================================================
-- JobFlow.ai & ResLink Studio - Complete Supabase Master Schema
-- ====================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Profiles Table (User Account, Resume Data, Questionnaire & Contact Settings)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
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
    resume_profile JSONB DEFAULT '{}'::jsonb,
    resume_filename TEXT,
    notification_settings JSONB DEFAULT '{"email": "", "whatsapp": "", "telegram": ""}'::jsonb,
    memory_bank JSONB DEFAULT '[]'::jsonb,
    candidate_quick_profile JSONB DEFAULT '{}'::jsonb,
    selected_template TEXT DEFAULT 'modern',
    subscription_tier TEXT DEFAULT 'free', -- free, pro, executive, owner
    subscription_status TEXT DEFAULT 'active', -- active, free, past_due, canceled
    role TEXT DEFAULT 'user', -- user, admin, owner
    is_admin BOOLEAN DEFAULT false,
    gumroad_license_key TEXT,
    license_key TEXT,
    gumroad_subscription_id TEXT,
    email_alerts_enabled BOOLEAN DEFAULT true,
    whatsapp_alerts_enabled BOOLEAN DEFAULT true,
    telegram_alerts_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Idempotent Column Additions (for updating existing database instances)
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS resume_profile JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS resume_filename TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS notification_settings JSONB DEFAULT '{"email": "", "whatsapp": "", "telegram": ""}'::jsonb;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS memory_bank JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS candidate_quick_profile JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS selected_template TEXT DEFAULT 'modern';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS subscription_tier TEXT DEFAULT 'free';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'active';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS gumroad_license_key TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS license_key TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS gumroad_subscription_id TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS email_alerts_enabled BOOLEAN DEFAULT true;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS whatsapp_alerts_enabled BOOLEAN DEFAULT true;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS telegram_alerts_enabled BOOLEAN DEFAULT true;

-- 3. ResLinks Table (Video Pitch Studio & Public Recruiter Hub)
CREATE TABLE IF NOT EXISTS public.reslinks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    user_email TEXT,
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

ALTER TABLE public.reslinks ADD COLUMN IF NOT EXISTS user_email TEXT;

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
    user_email TEXT,
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

ALTER TABLE public.saved_jobs ADD COLUMN IF NOT EXISTS user_email TEXT;

-- 6. Applications & Notifications Audit Table
CREATE TABLE IF NOT EXISTS public.applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    user_email TEXT,
    job_id TEXT NOT NULL,
    application_id TEXT NOT NULL UNIQUE,
    job_title TEXT,
    company TEXT,
    location TEXT,
    job_url TEXT,
    ats_match_score NUMERIC DEFAULT 85,
    tailored_pdf_url TEXT,
    tailored_docx_url TEXT,
    template_used TEXT DEFAULT 'modern',
    candidate_name TEXT,
    candidate_email TEXT,
    candidate_phone TEXT,
    status TEXT DEFAULT 'applied',
    notification_dispatched BOOLEAN DEFAULT false,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS user_email TEXT;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS job_title TEXT;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS company TEXT;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS location TEXT;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS job_url TEXT;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS ats_match_score NUMERIC DEFAULT 85;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS template_used TEXT DEFAULT 'modern';
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS candidate_name TEXT;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS candidate_email TEXT;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS candidate_phone TEXT;

-- 7. Questionnaire Memory Bank (Global / Base Templates)
CREATE TABLE IF NOT EXISTS public.questionnaire_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_email TEXT,
    question_id TEXT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    confidence NUMERIC DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. High-Performance Lookups Indexes
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_reslinks_slug ON public.reslinks(slug);
CREATE INDEX IF NOT EXISTS idx_reslinks_user_email ON public.reslinks(user_email);
CREATE INDEX IF NOT EXISTS idx_reslink_analytics_slug ON public.reslink_analytics(reslink_slug);
CREATE INDEX IF NOT EXISTS idx_reslink_analytics_event ON public.reslink_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_status ON public.saved_jobs(status);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_email ON public.saved_jobs(user_email);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON public.applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_email ON public.applications(user_email);

-- 9. Row Level Security (RLS) Configuration
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reslinks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reslink_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questionnaire_memory ENABLE ROW LEVEL SECURITY;

-- Allow public read of candidate public links
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow public read of reslinks by slug') THEN
        CREATE POLICY "Allow public read of reslinks by slug" ON public.reslinks FOR SELECT USING (true);
    END IF;
END $$;

-- Allow public tracking of analytics events
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow public insert of analytics telemetry') THEN
        CREATE POLICY "Allow public insert of analytics telemetry" ON public.reslink_analytics FOR INSERT WITH CHECK (true);
    END IF;
END $$;

-- Service role / backend full access policies
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Service full access on profiles') THEN
        CREATE POLICY "Service full access on profiles" ON public.profiles FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Service full access on reslinks') THEN
        CREATE POLICY "Service full access on reslinks" ON public.reslinks FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Service full access on analytics') THEN
        CREATE POLICY "Service full access on analytics" ON public.reslink_analytics FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Service full access on saved_jobs') THEN
        CREATE POLICY "Service full access on saved_jobs" ON public.saved_jobs FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Service full access on applications') THEN
        CREATE POLICY "Service full access on applications" ON public.applications FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Service full access on questionnaire') THEN
        CREATE POLICY "Service full access on questionnaire" ON public.questionnaire_memory FOR ALL USING (true);
    END IF;
END $$;

-- 10. Seed Master Owner & Executive Admin Account
INSERT INTO public.profiles (
    email,
    full_name,
    headline,
    phone_number,
    location,
    linkedin,
    github,
    summary,
    skills,
    target_role,
    subscription_tier,
    subscription_status,
    role,
    is_admin,
    selected_template,
    notification_settings,
    memory_bank
) VALUES (
    'mudatherkbyer@gmail.com',
    'Mudather Mohammed',
    'Junior AI Engineer | Machine Learning Engineer',
    '+211 920 123 456',
    'Worldwide Remote',
    'https://www.linkedin.com/in/mudather-mohammed',
    'https://github.com/mudather',
    'Junior AI Engineer and Machine Learning Engineer specializing in autonomous multi-agent pipelines, LLM systems, computer vision, and scalable Python/FastAPI architectures.',
    ARRAY['Python', 'Machine Learning', 'FastAPI', 'PyTorch', 'LLM Pipelines', 'Multi-Agent Systems', 'Docker', 'PostgreSQL', 'Supabase', 'Git', 'REST APIs', 'Vector Databases', 'NLP', 'Pandas', 'Scikit-Learn'],
    'Junior AI Engineer / Machine Learning Engineer',
    'executive',
    'active',
    'owner',
    true,
    'corporate_elite',
    '{"email": "mudatherkbyer@gmail.com", "whatsapp": "+211 920 123 456", "telegram": "@mudather_ai"}'::jsonb,
    '[
        {"id": "first_name", "category": "contact", "question": "First name?", "answer": "Mudather"},
        {"id": "last_name", "category": "contact", "question": "Last name?", "answer": "Mohammed"},
        {"id": "phone_country_code", "category": "contact", "question": "Phone country code?", "answer": "South Sudan (+211)"},
        {"id": "mobile_phone", "category": "contact", "question": "Mobile phone number?", "answer": "+211 920 123 456"},
        {"id": "email_address", "category": "contact", "question": "Email address?", "answer": "mudatherkbyer@gmail.com"},
        {"id": "street_address", "category": "location", "question": "Address (Street / Line 1)?", "answer": "Airport Road, Sector 4"},
        {"id": "city", "category": "location", "question": "City?", "answer": "Juba"},
        {"id": "state", "category": "location", "question": "State / Province / Region?", "answer": "Central Equatoria"},
        {"id": "work_auth_us", "category": "work_auth", "question": "Are you legally authorized to work in your target country / United States?", "answer": "Yes"},
        {"id": "visa_sponsorship", "category": "work_auth", "question": "Will you now or in the future require visa sponsorship for employment?", "answer": "No"}
    ]'::jsonb
) ON CONFLICT (email) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    headline = EXCLUDED.headline,
    subscription_tier = 'executive',
    subscription_status = 'active',
    role = 'owner',
    is_admin = true,
    updated_at = timezone('utc'::text, now());
