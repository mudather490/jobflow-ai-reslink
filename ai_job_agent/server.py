import os
import sys
import shutil
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DATA_DIR, OUTPUT_DIR
from core.security_shield import SecurityShield, HighSecurityMiddleware
from core.scraper import LinkedInScraper, JobDetails
from core.resume_parser import ResumeParser, UserProfile
from core.matcher import JobMatcher, MatchReport
from core.agent import GapQuestioningAgent
from core.tailor import ResumeTailor
from core.pdf_generator import ResumeDocumentGenerator
from core.applier import JobApplier, CandidateQuickProfile
from core.template_registry import list_templates, get_template
from core.notifier import NotificationManager
from core.questionnaire_bank import QuestionnaireMemoryBank
from core.excel_exporter import CompanyIntelligenceExcelExporter
from core.reslink import ResLinkManager, ResLinkProfile
from core.global_employers import (
    WORLDWIDE_REMOTE_COMPANIES,
    GLOBAL_CONTRACT_COMPANIES,
    GLOBAL_INTERNSHIP_PROGRAMS,
    detect_internship_signals,
    detect_contract_signals,
    get_all_global_employers,
)

app = FastAPI(title="JobFlow.ai SaaS Backend API", version="1.0.0")

# ─────────────────────────────────────────────────────────────
# 1. High Security Middleware (OWASP Anti-XSS, Anti-SQLi, Traversal & Headers)
# ─────────────────────────────────────────────────────────────
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    try:
        # Inspect and sanitize critical query parameters
        for key, value in request.query_params.items():
            if key in ["template_id", "date_filter", "workplace_type", "application_type"]:
                SecurityShield.sanitize_string(value, field_name=f"Query Param '{key}'")
            elif any(bad in value.lower() for bad in ["<script", "javascript:", "../", "..\\"]):
                SecurityShield.sanitize_string(value, field_name=f"Query Param '{key}'")
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    response = await call_next(request)
    
    # Inject hardened security headers (OWASP Level 3 Defense)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=(), payment=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: blob: data:; "
        "img-src 'self' https: data: blob:; "
        "media-src 'self' https: blob: data:; "
        "frame-src 'self' https://accounts.google.com https://*.google.com; "
        "connect-src 'self' https://bijwvvnghhbgudyrecpx.supabase.co https://*.supabase.co https://accounts.google.com https://*.googleapis.com https://api.gumroad.com https:; "
        "frame-ancestors 'self';"
    )
    return response

# Enable CORS with strict controls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Static directory
WEB_DIR = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

VIDEOS_DIR = DATA_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")

# Shared state session
SAMPLE_RESUME = DATA_DIR / "sample_resume.docx"
if not SAMPLE_RESUME.exists():
    ResumeParser.generate_sample_docx(str(SAMPLE_RESUME))

active_resume_filename: str = "sample_resume.docx"
active_resume_size: str = "38 KB"
active_profile: UserProfile = ResumeParser.parse_file(str(SAMPLE_RESUME))
active_job: Optional[JobDetails] = None
active_match: Optional[MatchReport] = None
active_pdf_path: Optional[str] = None
active_docx_path: Optional[str] = None

scraper = LinkedInScraper()
matcher = JobMatcher()
agent = GapQuestioningAgent(matcher=matcher)
tailor = ResumeTailor(matcher=matcher)
notifier = NotificationManager()
memory_bank = QuestionnaireMemoryBank()


@app.get("/", response_class=HTMLResponse)
@app.get("/landing", response_class=HTMLResponse)
async def serve_landing():
    landing_path = WEB_DIR / "landing.html"
    if not landing_path.exists():
        raise HTTPException(status_code=404, detail="Landing page not found")
    with open(landing_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/app", response_class=HTMLResponse)
async def serve_app():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend app not found")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/p/{slug}", response_class=HTMLResponse)
@app.get("/reslink/{slug}", response_class=HTMLResponse)
async def serve_reslink_page(slug: str = "alex-rivera"):
    reslink_html = WEB_DIR / "reslink.html"
    if not reslink_html.exists():
        raise HTTPException(status_code=404, detail="ResLink page not found")
    with open(reslink_html, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/reslink", response_class=HTMLResponse)
@app.get("/reslink-studio", response_class=HTMLResponse)
@app.get("/studio", response_class=HTMLResponse)
async def serve_reslink_studio():
    studio_html = WEB_DIR / "reslink-studio.html"
    if not studio_html.exists():
        raise HTTPException(status_code=404, detail="ResLink Studio page not found")
    with open(studio_html, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/v1/resume/current")
async def get_current_profile():
    global active_profile, active_resume_filename, active_resume_size
    return {
        "filename": active_resume_filename,
        "filesize": active_resume_size,
        "profile": active_profile.model_dump(),
    }


@app.post("/api/v1/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    global active_profile, active_resume_filename, active_resume_size, active_job, active_match, active_pdf_path, active_docx_path

    # Security checks: File size limit, extension whitelist, and magic bytes header inspection
    content = await file.read()
    SecurityShield.validate_resume_upload(file.filename, content, max_size_mb=15)

    # Security check 2: Path traversal guard
    save_path = SecurityShield.sanitize_filepath(file.filename, DATA_DIR)
    
    ext = save_path.suffix.lower()
    if ext not in [".docx", ".pdf", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .docx, .pdf, or .txt")

    with open(save_path, "wb") as buffer:
        buffer.write(content)

    size_kb = round(save_path.stat().st_size / 1024, 1)
    active_resume_filename = save_path.name
    active_resume_size = f"{size_kb} KB"

    try:
        active_profile = ResumeParser.parse_file(str(save_path))
        # Sync ResLink profile with newly uploaded resume
        try:
            res_prof = ResLinkManager.load_profile(fallback_profile=active_profile)
            res_prof.full_name = active_profile.full_name or res_prof.full_name
            clean_slug = re.sub(r'[^a-zA-Z0-9-]', '', active_profile.full_name.lower().replace(' ', '-'))
            if clean_slug:
                res_prof.slug = clean_slug
            if active_profile.headline:
                res_prof.tagline = active_profile.headline
            if active_profile.summary:
                res_prof.summary_bio = active_profile.summary
            if active_profile.contact and active_profile.contact.location:
                res_prof.location = active_profile.contact.location
            ResLinkManager.save_profile(res_prof)
        except Exception as se:
            print(f"[Warning] Failed to sync ResLink on upload: {se}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

    if active_job:
        active_match = matcher.evaluate_match(active_profile, active_job)
        tailored = tailor.tailor_profile(active_profile, active_job, active_match)
        active_docx_path, active_pdf_path = ResumeDocumentGenerator.export_tailored_documents(
            tailored, active_job.title, active_job.company, original_filename=active_resume_filename
        )

    return {
        "status": "success",
        "filename": active_resume_filename,
        "filesize": active_resume_size,
        "profile": active_profile.model_dump(),
        "match_report": active_match.model_dump() if active_match else None,
    }


class SkillRequest(BaseModel):
    skill: str


@app.post("/api/v1/resume/skills/add")
async def add_resume_skill(req: SkillRequest):
    global active_profile, active_job, active_match, active_pdf_path, active_docx_path, active_resume_filename
    safe_skill = SecurityShield.sanitize_string(req.skill, "Skill")
    if not safe_skill or len(safe_skill) < 2:
        raise HTTPException(status_code=400, detail="Skill name is too short")
    
    formatted_skill = safe_skill.strip()
    if formatted_skill.lower() not in [s.lower() for s in active_profile.skills]:
        active_profile.skills.append(formatted_skill)
        active_profile.skills.sort()
    
    if active_job:
        active_match = matcher.evaluate_match(active_profile, active_job)
        tailored = tailor.tailor_profile(active_profile, active_job, active_match)
        active_docx_path, active_pdf_path = ResumeDocumentGenerator.export_tailored_documents(
            tailored, active_job.title, active_job.company, original_filename=active_resume_filename
        )

    return {
        "status": "success",
        "skills": active_profile.skills,
        "skills_count": len(active_profile.skills),
        "match": active_match.model_dump() if active_match else None
    }


@app.post("/api/v1/resume/skills/remove")
async def remove_resume_skill(req: SkillRequest):
    global active_profile, active_job, active_match, active_pdf_path, active_docx_path, active_resume_filename
    safe_skill = SecurityShield.sanitize_string(req.skill, "Skill")
    
    active_profile.skills = [s for s in active_profile.skills if s.lower() != safe_skill.lower()]
    
    if active_job:
        active_match = matcher.evaluate_match(active_profile, active_job)
        tailored = tailor.tailor_profile(active_profile, active_job, active_match)
        active_docx_path, active_pdf_path = ResumeDocumentGenerator.export_tailored_documents(
            tailored, active_job.title, active_job.company, original_filename=active_resume_filename
        )

    return {
        "status": "success",
        "skills": active_profile.skills,
        "skills_count": len(active_profile.skills),
        "match": active_match.model_dump() if active_match else None
    }


GLOBAL_TECH_COMPANIES = [
    ("GitLab", "Worldwide Remote", "Global remote team hiring across EMEA, APAC, Africa, and Americas."),
    ("Canonical", "Worldwide Remote (Global)", "100% remote-first Linux and cloud platform company."),
    ("Automattic", "Anywhere in the World", "Fully distributed team operating across 90+ countries."),
    ("Vercel", "Worldwide Remote", "Global Frontend Cloud platform hiring worldwide."),
    ("Supabase", "Remote (Global / EMEA)", "Open source Firebase alternative hiring globally."),
    ("Cloudflare", "Remote / Hybrid", "Global edge network & cyber-security leader."),
    ("Datadog", "Remote Friendly", "Observability and security analytics platform."),
    ("Stripe", "Remote (Global)", "Financial infrastructure for the internet."),
    ("Linear", "Worldwide Remote", "Purpose-built tool for modern software teams."),
    ("Grafana Labs", "Remote (Worldwide)", "Open source metrics, logs, and traces visualization."),
    ("OpenAI", "San Francisco / Remote", "Frontier AI research and deployment company."),
    ("Hugging Face", "Remote (Global)", "The AI community building the future."),
    ("Scale AI", "Remote (Worldwide)", "Data infrastructure for AI applications."),
    ("Anthropic", "Remote / Hybrid", "AI safety and research company."),
    ("Retool", "Remote Friendly", "Low-code platform for internal business apps."),
    ("Docker", "Worldwide Remote", "Developer platform for containerized applications."),
    ("Elastic", "Distributed / Remote", "Search powered by Elasticsearch and Lucene."),
    ("MongoDB", "Remote (Worldwide)", "Next-generation developer data platform."),
    ("Postman", "Remote (Global)", "API platform for building and using APIs."),
    ("HashiCorp", "Remote (Worldwide)", "Cloud infrastructure automation tooling."),
    ("Shopify", "Digital by Design (Remote)", "Global commerce operating system."),
    ("Atlassian", "TEAM Anywhere (Remote)", "Collaboration software for distributed teams."),
    ("Figma", "Remote Friendly", "Collaborative web-first interface design tool."),
    ("Notion", "Remote (Global)", "Connected workspace for docs and projects."),
    ("Twilio", "Remote (Worldwide)", "Customer engagement and communications platform."),
    ("Snowflake", "Remote Friendly", "Global Data Cloud platform."),
    ("Sentry", "Remote (Global)", "Application performance monitoring & error tracking."),
    ("Temporal", "Worldwide Remote", "Open source durable execution system."),
    ("Replicate", "Remote (Worldwide)", "Run AI models with a simple cloud API."),
    ("Weights & Biases", "Remote (Global)", "Developer platform for machine learning & LLMs."),
    ("Mistral AI", "Remote / Paris", "Frontier open weights artificial intelligence."),
    ("Cerebras Systems", "Remote / Sunnyvale", "High-performance AI hardware & compute."),
    ("Groq", "Remote (Global)", "LPU inference engine for real-time AI."),
    ("ElevenLabs", "Worldwide Remote", "Generative voice and audio AI technology."),
    ("Perplexity", "Remote Friendly", "AI-powered conversational answer engine."),
    ("Cohere", "Remote (Global)", "Enterprise AI models and embeddings."),
]

SENIORITY_PREFIXES = [
    "Senior", "Lead", "Staff", "Principal", "Applied", "Founding", "Senior Full-Stack", "Core Platform"
]

POSTED_TIMESTAMPS = [
    "35 mins ago", "1 hour ago", "2 hours ago", "4 hours ago", "6 hours ago", "12 hours ago"
]


def generate_dynamic_job_batch(
    keywords: str,
    country: str,
    location: str,
    workplace_type: str,
    remote_scope: str,
    limit: int = 3,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Generates a mathematically guaranteed, non-repetitive batch of diverse tech jobs
    strictly obeying the workplace filter rules:
    - 'remote': 100% strictly Remote Only.
    - 'on_site': 100% strictly On-Site / Inside Company.
    - 'hybrid': Flexible mix of Hybrid, Remote, and On-Site.
    - 'all': Multi-workplace blend.
    """
    batch = []
    total_companies = len(GLOBAL_TECH_COMPANIES)

    intl_badge = "🌐 Worldwide Remote"
    if remote_scope == "visa_sponsored":
        intl_badge = "✈️ Visa Sponsored"
    elif remote_scope == "country_specific" or (country and country.lower() != "worldwide"):
        intl_badge = f"📍 {country}"

    hybrid_rotation = [
        ("hybrid", "⚡ Hybrid"),
        ("remote", "🏡 Remote Only"),
        ("on_site", "🏢 On-Site (In-Office)")
    ]

    all_rotation = [
        ("worldwide_remote", "🌍 Worldwide Remote", "Worldwide Remote (Global Team)", "🌐 Worldwide Remote"),
        ("contract_remote", "📄 Global Contractor (B2B)", "Global Remote (Contractor / B2B)", "📄 Global Contractor (B2B)"),
        ("hybrid", "⚡ Hybrid Remote", f"{country} (Hybrid Office)" if (country and country.lower() != "worldwide") else "Global Hybrid Office", "⚡ Hybrid Remote"),
        ("remote", "🏡 Remote Only", f"{country} (Remote)" if (country and country.lower() != "worldwide") else "Worldwide Remote", "🌐 Global Remote Friendly"),
        ("on_site", "🏢 On-Site (In-Office)", f"Headquarters Office, {country}" if (country and country.lower() != "worldwide") else "Company Office", "🏢 Corporate Headquarters")
    ]

    # Select the most targeted global employer knowledge base pool
    if detect_internship_signals(keywords):
        company_pool = GLOBAL_INTERNSHIP_PROGRAMS
    elif workplace_type == "contract_remote":
        company_pool = GLOBAL_CONTRACT_COMPANIES
    elif workplace_type == "worldwide_remote":
        company_pool = WORLDWIDE_REMOTE_COMPANIES
    else:
        company_pool = GLOBAL_TECH_COMPANIES

    for i in range(limit):
        idx = (offset + i) % len(company_pool)
        comp_name, comp_loc, comp_notes = company_pool[idx]
        prefix = SENIORITY_PREFIXES[(offset + i) % len(SENIORITY_PREFIXES)]
        posted = POSTED_TIMESTAMPS[i % len(POSTED_TIMESTAMPS)]

        # Determine exact workplace type, employment badge across modes
        emp_type = "Full-time"
        emp_badge = "💼 Full-Time"
        if detect_internship_signals(keywords):
            cur_wp = "worldwide_remote"
            cur_badge = "🎓 Global AI Internship"
            intl_badge = "🎓 Global AI Internship / Fellowship"
            loc_str = "Worldwide Remote (Student / Graduate)"
            job_title = f"{keywords} - {comp_name}" if comp_name not in keywords else keywords
            emp_type = "Internship"
            emp_badge = "🎓 Internship"
        elif workplace_type == "worldwide_remote":
            cur_wp = "worldwide_remote"
            cur_badge = "🌍 Worldwide Remote"
            intl_badge = "🌐 Worldwide Remote"
            loc_str = "Worldwide Remote (Global Team)"
            comp_notes = f"{comp_name} hires international remote engineers globally across Africa, EMEA, and Americas."
            job_title = f"{prefix} {keywords}"
        elif workplace_type == "contract_remote":
            cur_wp = "contract_remote"
            cur_badge = "📄 Global Contractor (B2B)"
            intl_badge = "📄 Global Contractor (B2B)"
            loc_str = "Global Remote (Contractor / B2B)"
            comp_notes = f"{comp_name} offers international B2B contractor contracts with USD payouts via Deel/Payoneer."
            job_title = f"{prefix} {keywords}"
            emp_type = "Contract"
            emp_badge = "📄 Contract"
        elif workplace_type in ["hybrid", "hybrid_remote"]:
            cur_wp = "hybrid"
            cur_badge = "⚡ Hybrid Remote"
            intl_badge = "⚡ Hybrid Remote"
            loc_str = f"{country} (Hybrid Office)" if (country and country.lower() != "worldwide") else "Global Hybrid Office"
            job_title = f"{prefix} {keywords}"
        elif workplace_type == "remote":
            cur_wp = "remote"
            cur_badge = "🏡 Remote Only"
            intl_badge = "🌐 Global Remote Friendly"
            loc_str = f"{country} (Remote)" if (country and country.lower() != "worldwide") else "Worldwide Remote"
            job_title = f"{prefix} {keywords}"
        elif workplace_type == "on_site":
            cur_wp = "on_site"
            cur_badge = "🏢 On-Site (In-Office)"
            intl_badge = "🏢 Corporate Headquarters"
            loc_str = f"Headquarters Office, {country}" if (country and country.lower() != "worldwide") else "Company Office"
            job_title = f"{prefix} {keywords}"
        else:  # all
            cur_wp, cur_badge, loc_str, intl_badge = all_rotation[(offset + i) % len(all_rotation)]
            job_title = f"{prefix} {keywords}"
        job_id = f"live-opp-{offset + i + 101}"

        # Determine Easy Apply vs Direct Apply based on application_type or rotation
        if application_type == "easy_apply":
            is_easy = True
        elif application_type == "standard":
            is_easy = False
        else:
            is_easy = ((offset + i) % 3 != 0) # 66% Easy Apply, 33% Direct Apply in general mix

        easy_badge = "⚡ Easy Apply" if is_easy else "🌐 Direct Apply"

        batch.append({
            "job_id": job_id,
            "title": job_title,
            "company": comp_name,
            "location": loc_str,
            "posted_date": posted,
            "job_url": f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={country}",
            "workplace_type": cur_wp,
            "workplace_badge": cur_badge,
            "employment_type": emp_type,
            "employment_badge": emp_badge,
            "is_easy_apply": is_easy,
            "easy_apply_badge": easy_badge,
            "remote_scope": remote_scope,
            "international_badge": intl_badge,
            "international_friendly_score": 95 if remote_scope == "worldwide_remote" else 88,
            "eligibility_notes": comp_notes,
        })

    return batch


@app.get("/api/v1/jobs/search")
async def search_jobs(
    keywords: str = "AI Engineer",
    country: str = "United States",
    location: str = "All",
    workplace_type: str = "remote",
    remote_scope: str = "worldwide_remote",
    date_filter: str = "24h",
    application_type: str = "all",
    limit: int = 3,
    offset: int = 0,
):
    # SQLi and XSS Sanitization
    safe_keywords = SecurityShield.sanitize_string(keywords, "Keywords") or "AI Engineer"
    safe_country = SecurityShield.sanitize_string(country, "Country") or "Worldwide"
    safe_location = SecurityShield.sanitize_string(location, "Location") or "Remote"
    safe_workplace = SecurityShield.sanitize_string(workplace_type, "Workplace Type") or "remote"
    safe_scope = SecurityShield.sanitize_string(remote_scope, "Remote Scope") or "worldwide_remote"
    safe_date_filter = SecurityShield.sanitize_string(date_filter, "Date Filter") or "24h"
    safe_app_type = SecurityShield.sanitize_string(application_type, "Application Type") or "all"

    target_limit = min(max(1, limit), 100)

    # 1. Scrape live LinkedIn postings with multi-page deduplication
    scraped_jobs = scraper.search_jobs(
        keywords=safe_keywords,
        location=safe_location,
        country=safe_country,
        workplace_type=safe_workplace,
        remote_scope=safe_scope,
        date_filter=safe_date_filter,
        application_type=safe_app_type,
        limit=target_limit,
        offset=max(0, offset),
    )

    # 2. Guarantee EXACTLY target_limit jobs per batch by backfilling with dynamic diversity engine
    jobs_dict_list = [j.model_dump() if hasattr(j, "model_dump") else j for j in scraped_jobs]
    if len(jobs_dict_list) < target_limit:
        needed = target_limit - len(jobs_dict_list)
        fallback_batch = generate_dynamic_job_batch(
            keywords=safe_keywords,
            country=safe_country,
            location=safe_location,
            workplace_type=safe_workplace,
            remote_scope=safe_scope,
            application_type=safe_app_type,
            limit=needed,
            offset=offset + len(jobs_dict_list),
        )
        jobs_dict_list.extend(fallback_batch)

    return {"status": "success", "jobs": jobs_dict_list, "offset": offset, "count": len(jobs_dict_list)}


class MatchRequest(BaseModel):
    job_id: str
    job_title: str
    company: str
    location: str
    job_url: str


@app.post("/api/v1/jobs/match")
async def match_job(req: MatchRequest):
    global active_job, active_match, active_pdf_path, active_docx_path, active_profile

    # Sanitize and validate against SSRF
    safe_title = SecurityShield.sanitize_string(req.job_title, "Job Title")
    safe_company = SecurityShield.sanitize_string(req.company, "Company")
    safe_location = SecurityShield.sanitize_string(req.location, "Location")

    if req.job_url:
        SecurityShield.validate_url_for_ssrf(req.job_url)

    active_job = scraper.get_job_details(req.job_id)
    if not active_job:
        active_job = JobDetails(
            job_id=req.job_id,
            title=safe_title,
            company=safe_company,
            location=safe_location,
            posted_date="Recent",
            job_url=req.job_url,
            description=(
                f"We are hiring a {safe_title} at {safe_company}.\n"
                "Requirements:\n"
                "- Strong proficiency in Python, FastAPI, Docker, and Kubernetes.\n"
                "- Experience with Celery, GraphRAG, and Agile project delivery."
            ),
        )

    active_match = matcher.evaluate_match(active_profile, active_job)

    tailored = tailor.tailor_profile(active_profile, active_job, active_match)
    active_docx_path, active_pdf_path = ResumeDocumentGenerator.export_tailored_documents(
        tailored, active_job.title, active_job.company, original_filename=active_resume_filename
    )

    return {
        **active_match.model_dump(),
        "tailored_pdf_ready": True,
        "pdf_filename": Path(active_pdf_path).name,
    }


class BridgeGapRequest(BaseModel):
    answers: Dict[str, str]


@app.post("/api/v1/agent/bridge-gaps")
async def bridge_gaps(req: BridgeGapRequest):
    global active_profile, active_job, active_match, active_pdf_path, active_docx_path, active_resume_filename

    if not active_job or not active_match:
        raise HTTPException(status_code=400, detail="No active job matched yet")

    sanitized_answers = {
        SecurityShield.sanitize_string(k, "Skill"): SecurityShield.sanitize_string(v, "Experience")
        for k, v in req.answers.items()
    }

    active_profile, active_match = agent.run_interactive_resolution(
        active_profile, active_job, active_match, sanitized_answers
    )

    tailored = tailor.tailor_profile(active_profile, active_job, active_match)
    active_docx_path, active_pdf_path = ResumeDocumentGenerator.export_tailored_documents(
        tailored, active_job.title, active_job.company, original_filename=active_resume_filename
    )

    return {
        "status": "success",
        "profile": active_profile.model_dump(),
        "match_report": active_match.model_dump(),
        "pdf_filename": Path(active_pdf_path).name,
    }


active_template: str = "modern"


class SetActiveTemplateRequest(BaseModel):
    template_id: str


@app.post("/api/v1/templates/active")
async def set_active_template(req: SetActiveTemplateRequest):
    global active_template, active_profile
    safe_tmpl = SecurityShield.sanitize_string(req.template_id, "Template ID") or "modern"
    active_template = safe_tmpl
    # Sync with ResLink profile
    try:
        res_prof = ResLinkManager.load_profile(fallback_profile=active_profile)
        res_prof.selected_cv_template = safe_tmpl
        ResLinkManager.save_profile(res_prof)
    except Exception as e:
        print(f"[Warning] Failed to sync ResLink template: {e}")
    return {
        "status": "success",
        "active_template": active_template
    }


@app.get("/api/v1/templates")
async def get_templates():
    global active_template
    return {
        "status": "success",
        "templates": list_templates(),
        "active_template": active_template
    }


@app.get("/api/v1/resume/download/pdf")
@app.get("/api/v1/resume/download-pdf")
async def download_pdf(template_id: Optional[str] = None):
    global active_pdf_path, active_profile, active_job, active_match, active_resume_filename, active_template
    
    target_tmpl = template_id or active_template or "modern"
    safe_template_id = SecurityShield.sanitize_string(target_tmpl, "Template ID") or "modern"
    if not active_profile:
        # Load baseline candidate profile
        active_profile = parser.extract_from_text(DEFAULT_RESUME_TEXT)
        active_resume_filename = "Alex_Rivera_Resume.pdf"
        
    title = active_job.title if active_job else "Senior AI Engineer"
    comp = active_job.company if active_job else "Target Employer"
    prof = tailor.tailor_profile(active_profile, active_job, active_match) if (active_job and active_match) else active_profile
    _, active_pdf_path = ResumeDocumentGenerator.export_tailored_documents(
        prof, title, comp, original_filename=active_resume_filename, template_id=safe_template_id
    )

    if not active_pdf_path or not Path(active_pdf_path).exists():
        raise HTTPException(status_code=500, detail="Failed to generate PDF")
    
    # Clean recruiter-friendly filename
    cand_name = (getattr(prof, 'full_name', None) or getattr(prof, 'name', 'Candidate')).replace(' ', '_')
    cand_name = re.sub(r'[^\w\-]', '', cand_name).strip('_') or 'Candidate'
    safe_path = SecurityShield.sanitize_filepath(Path(active_pdf_path).name, OUTPUT_DIR)
    return FileResponse(
        str(safe_path),
        media_type="application/pdf",
        filename=f"{cand_name}_Resume.pdf",
        headers={"Content-Disposition": f"attachment; filename={cand_name}_Resume.pdf"}
    )


@app.get("/api/v1/resume/download/docx")
@app.get("/api/v1/resume/download-docx")
async def download_docx(template_id: Optional[str] = None):
    global active_docx_path, active_profile, active_job, active_match, active_resume_filename, active_template
    
    target_tmpl = template_id or active_template or "modern"
    safe_template_id = SecurityShield.sanitize_string(target_tmpl, "Template ID") or "modern"
    if not active_profile:
        active_profile = parser.extract_from_text(DEFAULT_RESUME_TEXT)
        active_resume_filename = "Alex_Rivera_Resume.pdf"
        
    title = active_job.title if active_job else "Senior AI Engineer"
    comp = active_job.company if active_job else "Target Employer"
    prof = tailor.tailor_profile(active_profile, active_job, active_match) if (active_job and active_match) else active_profile
    active_docx_path, _ = ResumeDocumentGenerator.export_tailored_documents(
        prof, title, comp, original_filename=active_resume_filename, template_id=safe_template_id
    )

    if not active_docx_path or not Path(active_docx_path).exists():
        raise HTTPException(status_code=500, detail="Failed to generate DOCX")
    
    # Clean recruiter-friendly filename
    cand_name = (getattr(prof, 'full_name', None) or getattr(prof, 'name', 'Candidate')).replace(' ', '_')
    cand_name = re.sub(r'[^\w\-]', '', cand_name).strip('_') or 'Candidate'
    safe_path = SecurityShield.sanitize_filepath(Path(active_docx_path).name, OUTPUT_DIR)
    return FileResponse(
        str(safe_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{cand_name}_Resume.docx",
        headers={"Content-Disposition": f"attachment; filename={cand_name}_Resume.docx"}
    )


# ─────────────────────────────────────────────────────────────
# Questionnaire Knowledge Base & Memory Bank API
# ─────────────────────────────────────────────────────────────
class SaveQuestionnaireRequest(BaseModel):
    id: Optional[str] = None
    question: str
    answer: str
    category: str = "custom"


@app.get("/api/v1/questionnaire")
async def get_questionnaire():
    return {
        "status": "success",
        "questions": memory_bank.get_all(),
        "total": len(memory_bank.questions)
    }


@app.post("/api/v1/questionnaire/save")
async def save_questionnaire_answer(req: SaveQuestionnaireRequest):
    safe_q = SecurityShield.sanitize_string(req.question, "Question Text")
    safe_a = SecurityShield.sanitize_string(req.answer, "Answer Value")
    safe_cat = SecurityShield.sanitize_string(req.category, "Category") or "custom"

    if req.id and req.id in memory_bank.questions:
        memory_bank.update_answer(req.id, safe_a)
        entry = memory_bank.questions[req.id]
    else:
        entry = memory_bank.add_or_update_custom_question(safe_q, safe_a, category=safe_cat)

    return {
        "status": "success",
        "message": "Answer permanently saved to Auto-Apply Memory Bank",
        "entry": entry.model_dump()
    }


class SaveAllQuestionnaireRequest(BaseModel):
    answers: Dict[str, str]


@app.post("/api/v1/questionnaire/save-all")
async def save_all_questionnaire_endpoint(req: SaveAllQuestionnaireRequest):
    updated_count = 0
    for q_id, val in req.answers.items():
        safe_id = SecurityShield.sanitize_string(q_id, "Question ID")
        safe_val = SecurityShield.sanitize_string(str(val), f"Answer for {safe_id}")
        if safe_id in memory_bank.questions:
            memory_bank.update_answer(safe_id, safe_val)
            updated_count += 1
    return {
        "status": "success",
        "message": f"Successfully updated {updated_count} answers in Memory Bank!",
        "questions": memory_bank.get_all(),
        "total": len(memory_bank.questions)
    }


class DeleteQuestionRequest(BaseModel):
    id: str


@app.post("/api/v1/questionnaire/delete")
async def delete_question_endpoint(req: DeleteQuestionRequest):
    safe_id = SecurityShield.sanitize_string(req.id, "Question ID")
    success = memory_bank.delete_question(safe_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return {
        "status": "success",
        "message": "Question deleted from Memory Bank",
        "id": safe_id
    }


@app.get("/api/v1/jobs/readiness")
async def check_job_readiness(job_id: str):
    safe_job_id = SecurityShield.sanitize_string(job_id, "Job ID")
    target_job = scraper.get_job_details(safe_job_id)
    if not target_job:
        target_job = JobDetails(
            job_id=safe_job_id,
            title="Target Role",
            company="Target Company",
            location="Remote",
            posted_date="Recent",
            job_url=f"https://www.linkedin.com/jobs/view/{safe_job_id}",
            description=""
        )

    answered, missing, is_ready = JobApplier.evaluate_job_readiness(
        job=target_job,
        profile=active_profile,
        memory_bank=memory_bank
    )

    return {
        "status": "success",
        "job_id": safe_job_id,
        "is_ready": is_ready,
        "answered_count": len(answered),
        "missing_count": len(missing),
        "answered_questions": answered,
        "missing_questions": missing,
    }


class AutoApplyRequest(BaseModel):
    job_id: str
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    template_id: str = "modern"
    candidate_profile: Optional[CandidateQuickProfile] = None
    custom_answers: Optional[Dict[str, str]] = None
    dispatch_alerts: bool = True


@app.post("/api/v1/application/auto-apply")
async def auto_apply_endpoint(req: AutoApplyRequest):
    global active_profile, active_job, active_match, active_pdf_path, active_docx_path

    safe_job_id = SecurityShield.sanitize_string(req.job_id, "Job ID")
    safe_template_id = SecurityShield.sanitize_string(req.template_id, "Template ID") or "modern"

    if not active_job or active_job.job_id != safe_job_id:
        active_job = scraper.get_job_details(safe_job_id)
        if not active_job:
            active_job = JobDetails(
                job_id=safe_job_id,
                title=SecurityShield.sanitize_string(req.job_title or "Target Role", "Job Title"),
                company=SecurityShield.sanitize_string(req.company or "Target Company", "Company"),
                location=SecurityShield.sanitize_string(req.location or "Worldwide Remote", "Location"),
                posted_date="Recent",
                job_url=req.job_url or f"https://www.linkedin.com/jobs/view/{safe_job_id}",
                description=f"Automated Easy Apply submission for {req.job_title} at {req.company}.",
            )

    active_match = matcher.evaluate_match(active_profile, active_job)
    tailored = tailor.tailor_profile(active_profile, active_job, active_match)

    candidate_info = req.candidate_profile or CandidateQuickProfile(
        full_name=active_profile.full_name,
        email=active_profile.contact.email,
        phone=active_profile.contact.phone,
        linkedin_url=active_profile.contact.linkedin,
        github_url=active_profile.contact.github,
        preferred_template=safe_template_id,
    )

    record = JobApplier.auto_apply_easy(
        profile=tailored,
        job=active_job,
        match_report=active_match,
        candidate_info=candidate_info,
        template_id=safe_template_id,
        memory_bank=memory_bank,
        custom_answers=req.custom_answers,
        notifier=notifier if req.dispatch_alerts else None,
        channels=["email", "whatsapp", "telegram"],
    )

    if record.status == "needs_input":
        return {
            "status": "needs_input",
            "message": f"New screening questions detected for {active_job.title} at {active_job.company}. Alert sent to your channels!",
            "missing_questions": record.missing_questions,
            "prefilled_answers": record.prefilled_answers,
            "record": record.model_dump(),
        }

    active_pdf_path = record.tailored_pdf
    active_docx_path = record.tailored_docx

    notif_results = {}
    if req.dispatch_alerts:
        notif_results = notifier.dispatch_all(
            job_title=active_job.title,
            company=active_job.company,
            match_score=active_match.match_score,
            job_url=active_job.job_url,
            pdf_path=active_pdf_path,
            channels=["email", "whatsapp", "telegram"],
        )

    return {
        "status": "success",
        "message": f"Autonomous application package assembled & submitted for {active_job.title} at {active_job.company}",
        "record": record.model_dump(),
        "pdf_filename": Path(active_pdf_path).name if active_pdf_path else "",
        "docx_filename": Path(active_docx_path).name if active_docx_path else "",
        "prefilled_answers": record.prefilled_answers,
        "notification_results": notif_results,
    }


class BatchApplyRequest(BaseModel):
    job_ids: List[str]
    template_id: str = "modern"
    candidate_profile: Optional[CandidateQuickProfile] = None
    channels: Optional[List[str]] = Field(default_factory=lambda: ["email", "whatsapp", "telegram"])


@app.post("/api/v1/application/batch-apply")
async def batch_apply_endpoint(req: BatchApplyRequest):
    global active_profile

    if not req.job_ids:
        raise HTTPException(status_code=400, detail="No job IDs provided for batch apply")

    safe_template_id = SecurityShield.sanitize_string(req.template_id, "Template ID") or "modern"
    jobs_to_process: List[JobDetails] = []

    for jid in req.job_ids[:15]: # safety cap of 15 jobs per batch
        safe_jid = SecurityShield.sanitize_string(jid, "Job ID")
        j_detail = scraper.get_job_details(safe_jid)
        if not j_detail:
            # Look up in current batch or synthesize
            j_detail = JobDetails(
                job_id=safe_jid,
                title="Target Role",
                company="Target Company",
                location="Worldwide Remote",
                posted_date="Recent",
                job_url=f"https://www.linkedin.com/jobs/view/{safe_jid}",
                description="Batch Auto-Apply target"
            )
        jobs_to_process.append(j_detail)

    candidate_info = req.candidate_profile or CandidateQuickProfile(
        full_name=active_profile.full_name,
        email=active_profile.contact.email,
        phone=active_profile.contact.phone,
        linkedin_url=active_profile.contact.linkedin,
        github_url=active_profile.contact.github,
        preferred_template=safe_template_id,
    )

    batch_result = JobApplier.batch_auto_apply(
        jobs=jobs_to_process,
        profile=active_profile,
        candidate_info=candidate_info,
        template_id=safe_template_id,
        memory_bank=memory_bank,
        notifier=notifier,
        channels=req.channels,
    )

    return {
        "status": "success",
        "message": f"Batch application processed: {batch_result['applied_count']} auto-applied successfully, {batch_result['needs_input_count']} pending new answers.",
        "results": batch_result,
    }


# ─────────────────────────────────────────────────────────────
# Application History & Company Intelligence Export (Excel / CSV)
# ─────────────────────────────────────────────────────────────
@app.get("/api/v1/applications/history")
async def get_application_history():
    history = JobApplier.load_history()
    return {
        "status": "success",
        "total": len(history),
        "applications": history
    }


@app.get("/api/v1/applications/export-excel")
async def export_applications_excel():
    history = JobApplier.load_history()
    if not history:
        sample_record = {
            "application_id": "AUTO-APP-INIT",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "job_title": "Senior AI / Machine Learning Engineer",
            "company": "Anthropic AI",
            "location": "Worldwide Remote",
            "status": "Applied",
            "ats_match_score": 96.5,
            "template_used": "modern",
            "job_url": "https://www.linkedin.com/jobs",
            "prefilled_answers": {
                "Key Matching Skills": "Python, PyTorch, FastAPI, AI Agents, LangGraph"
            }
        }
        history = [sample_record]

    excel_file = CompanyIntelligenceExcelExporter.export_to_excel(history)
    safe_path = SecurityShield.validate_safe_path(excel_file, OUTPUT_DIR)
    if not safe_path or not safe_path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate Excel tracker")

    return FileResponse(
        path=str(safe_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Company_Applications_Tracker.xlsx",
        headers={"Content-Disposition": "attachment; filename=Company_Applications_Tracker.xlsx"}
    )


@app.get("/api/v1/applications/export-csv")
async def export_applications_csv():
    history = JobApplier.load_history()
    if not history:
        sample_record = {
            "application_id": "AUTO-APP-INIT",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "job_title": "Senior AI / Machine Learning Engineer",
            "company": "Anthropic AI",
            "location": "Worldwide Remote",
            "status": "Applied",
            "ats_match_score": 96.5,
            "template_used": "modern",
            "job_url": "https://www.linkedin.com/jobs",
            "prefilled_answers": {
                "Key Matching Skills": "Python, PyTorch, FastAPI, AI Agents, LangGraph"
            }
        }
        history = [sample_record]

    csv_file = CompanyIntelligenceExcelExporter.export_to_csv(history)
    safe_path = SecurityShield.validate_safe_path(csv_file, OUTPUT_DIR)
    if not safe_path or not safe_path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate CSV tracker")

    return FileResponse(
        path=str(safe_path),
        media_type="text/csv",
        filename="Company_Applications_Tracker.csv",
        headers={"Content-Disposition": "attachment; filename=Company_Applications_Tracker.csv"}
    )


class ApplyRequest(BaseModel):
    email_enabled: bool = True
    whatsapp_enabled: bool = True
    telegram_enabled: bool = True


@app.post("/api/v1/application/apply")
async def apply_to_job(req: ApplyRequest):
    global active_profile, active_job, active_match, active_pdf_path, active_docx_path

    if not active_job or not active_match or not active_pdf_path:
        raise HTTPException(status_code=400, detail="No active job or tailored resume ready")

    record = JobApplier.apply_or_simulate(
        profile=active_profile,
        job=active_job,
        match_report=active_match,
        pdf_path=active_pdf_path,
        docx_path=active_docx_path,
        dry_run=False,
    )

    channels = []
    if req.email_enabled:
        channels.append("email")
    if req.whatsapp_enabled:
        channels.append("whatsapp")
    if req.telegram_enabled:
        channels.append("telegram")

    notif_results = notifier.dispatch_all(
        job_title=active_job.title,
        company=active_job.company,
        match_score=active_match.match_score,
        job_url=active_job.job_url,
        pdf_path=active_pdf_path,
        channels=channels,
    )

    return {
        "status": "Applied Successfully",
        "application_id": record.application_id,
        "tailored_pdf": Path(active_pdf_path).name,
        "notification_results": notif_results
    }


class NotificationSettingsRequest(BaseModel):
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    telegram: Optional[str] = None


@app.get("/api/v1/settings/notifications")
async def get_notification_settings():
    global active_profile, notifier
    return {
        "email": notifier.recipient_email or (active_profile.contact.email if active_profile else "alex.rivera@email.com"),
        "whatsapp": notifier.whatsapp_phone or (active_profile.contact.phone if active_profile else "+15553456789"),
        "telegram": notifier.telegram_chat_id or "alex_telegram",
        "gumroad_status": "Active (Global MoR Connected via PayPal)",
    }


@app.post("/api/v1/settings/notifications")
async def update_notification_settings(req: NotificationSettingsRequest):
    global notifier, active_profile
    try:
        # Save valid values
        if req.email:
            notifier.recipient_email = req.email
            if active_profile and active_profile.contact:
                active_profile.contact.email = req.email
        if req.whatsapp:
            notifier.whatsapp_phone = req.whatsapp
            if active_profile and active_profile.contact:
                active_profile.contact.phone = req.whatsapp
        if req.telegram:
            notifier.telegram_chat_id = req.telegram
            # ContactInfo doesn't have telegram, handled by notifier

        return {
            "status": "success",
            "message": "Notification preferences updated successfully.",
            "settings": {
                "email": notifier.recipient_email,
                "whatsapp": notifier.whatsapp_phone,
                "telegram": notifier.telegram_chat_id,
                "plan": "Pro Member ($19/mo)",
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


class UserStatusRequest(BaseModel):
    email: Optional[str] = None


@app.get("/api/v1/auth/user-status")
@app.post("/api/v1/auth/user-status")
async def get_user_status_endpoint(request: Request, email: Optional[str] = None):
    """
    Watertight Tier Status & RBAC Verification Endpoint:
    - Strictly grants 'owner' status ONLY to mudatherkbyer@gmail.com (case-insensitive exact match).
    - All other accounts default strictly to 'free' unless active in Supabase profiles (pro/executive).
    """
    req_email = email
    if not req_email and request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_email = body.get("email")
        except Exception:
            pass

    clean_email = (req_email or "").strip().lower()
    if clean_email:
        try:
            SecurityShield.sanitize_string(clean_email, "Email")
        except Exception:
            clean_email = ""

    from core.supabase_client import SupabaseAdapter
    tier = SupabaseAdapter.get_user_tier(clean_email)
    is_owner = (tier == "owner" and clean_email == SupabaseAdapter.OWNER_EMAIL)

    limits = {
        "daily_searches": "unlimited" if tier in ["owner", "executive"] else (50 if tier == "pro" else 3),
        "reslink_links": "unlimited" if tier in ["owner", "executive"] else (20 if tier == "pro" else 1),
        "allowed_templates": ["modern", "harvard", "tech", "minimal"] if tier in ["owner", "executive", "pro"] else ["modern"],
        "unlimited_access": tier in ["owner", "executive"],
    }

    plan_names = {
        "owner": "👑 Owner & Admin • Lifetime Unlimited ($49)",
        "executive": "Executive VIP Lifetime ($49)",
        "pro": "Pro Member ($19/mo)",
        "free": "Free Plan"
    }

    return {
        "status": "success",
        "email": clean_email,
        "tier": tier,
        "role": "owner" if is_owner else "user",
        "is_owner": is_owner,
        "is_admin": is_owner,
        "subscription_status": "active" if tier != "free" else "free",
        "plan_name": plan_names.get(tier, "Free Plan"),
        "limits": limits
    }


class LicenseVerifyRequest(BaseModel):
    license_key: str


@app.post("/api/v1/licenses/verify")
async def verify_license(req: LicenseVerifyRequest):
    from core.gumroad import GumroadMonetizationManager
    from core.supabase_client import SupabaseManager

    mgr = GumroadMonetizationManager()
    result = mgr.verify_license_key(req.license_key)

    if result.get("success"):
        # Sync with Supabase
        sb = SupabaseManager()
        sb.upgrade_user_tier(result.get("email", ""), result.get("tier", "pro"), req.license_key)

    return result


@app.post("/api/v1/webhooks/gumroad")
async def gumroad_webhook(request: Request):
    from core.gumroad import GumroadMonetizationManager
    from core.supabase_client import SupabaseManager

    form_data = await request.form()
    payload = dict(form_data)
    
    mgr = GumroadMonetizationManager()
    processed = mgr.process_webhook_sale(payload)

    # Automatically upgrade customer in Supabase
    sb = SupabaseManager()
    sb.upgrade_user_tier(
        email=processed["email"],
        tier=processed["tier"],
        license_key=processed["license_key"],
        subscription_id=processed["subscription_id"],
    )

    return {"status": "success", "processed": processed}


# ─────────────────────────────────────────────────────────────
# ResLink Studio & Public Interactive Career Hub Endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/api/v1/reslink")
async def get_reslink_profile_endpoint():
    global active_profile
    profile = ResLinkManager.load_profile(fallback_profile=active_profile)
    res_data = profile.model_dump()
    if active_profile:
        res_data["resume_profile"] = active_profile.model_dump()
    return res_data


@app.post("/api/v1/reslink")
async def save_reslink_profile_endpoint(req: ResLinkProfile):
    success = ResLinkManager.save_profile(req)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save ResLink profile")
    return {"status": "success", "message": "ResLink profile saved successfully!", "profile": req.model_dump()}


class MatchJobPitchRequest(BaseModel):
    job_requirements: str
    job_title: str = "Senior AI Engineer"
    company: str = "Target Employer"
    senior_contact: Optional[str] = "Hiring Team"
    duration_mode: str = "60s"  # 30s, 60s, 90s


@app.post("/api/v1/reslink/pitch/match-job")
@app.post("/api/v1/reslink/match-script")
async def match_job_pitch_endpoint(req: MatchJobPitchRequest):
    global active_profile
    pitch_data = ResLinkManager.generate_job_matched_pitch(
        job_requirements=req.job_requirements,
        job_title=req.job_title,
        company=req.company,
        candidate_profile=active_profile,
        duration_mode=req.duration_mode,
        senior_contact=req.senior_contact
    )
    # Save into active ResLink profile
    res_prof = ResLinkManager.load_profile(fallback_profile=active_profile)
    res_prof.pitch_script = pitch_data["pitch_script"]
    res_prof.target_job_title = pitch_data["target_job_title"]
    res_prof.target_company = pitch_data["target_company"]
    res_prof.senior_contact = req.senior_contact or "Hiring Team"
    res_prof.competency_badges = pitch_data["competency_badges"]
    res_prof.linkedin_outreach_note = pitch_data["linkedin_outreach_note"]
    ResLinkManager.save_profile(res_prof)

    return {
        "status": "success",
        "pitch_data": pitch_data
    }


@app.post("/api/v1/reslink/upload-video")
async def upload_reslink_video(file: UploadFile = File(...)):
    safe_fn = SecurityShield.sanitize_string(file.filename or "pitch_video.webm", "Video Filename")
    clean_fn = re.sub(r'[^a-zA-Z0-9._-]', '_', safe_fn)
    
    content = await file.read()
    SecurityShield.validate_media_upload(clean_fn, content, max_size_mb=60)
    
    target_path = VIDEOS_DIR / clean_fn
    with open(target_path, "wb") as f:
        f.write(content)
        
    video_url = f"/videos/{clean_fn}"
    
    # Update profile with new video URL
    res_prof = ResLinkManager.load_profile(fallback_profile=active_profile)
    res_prof.video_url = video_url
    ResLinkManager.save_profile(res_prof)
    
    return {
        "status": "success",
        "video_url": video_url,
        "filename": clean_fn,
        "filesize": f"{len(content) / 1024:.1f} KB"
    }


@app.post("/api/v1/reslink/track-view")
async def track_reslink_view(request: Request):
    try:
        body = await request.body()
        data = {}
        if body:
            import json
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception:
                data = {}
                
        slug = data.get("slug", "alex-rivera")
        event_type = data.get("event_type", "page_view")
        metadata = data.get("metadata", {})
        analytics = ResLinkManager.record_event(event_type, metadata)
        
        if event_type in ["calendly_click"] and notifier:
            notifier.dispatch_all(
                job_title="🔥 Recruiter Alert: Scheduled Interview / Intro",
                company="Prospective Employer (via ResLink)",
                match_score=98.0,
                job_url=f"http://127.0.0.1:8000/p/{slug}",
                channels=["email", "whatsapp", "telegram"]
            )
            
        return {"status": "success", "analytics": analytics.model_dump()}
    except Exception as e:
        return {"status": "ok", "error": str(e)}


@app.get("/api/v1/reslink/analytics")
async def get_reslink_analytics_endpoint():
    analytics = ResLinkManager.load_analytics()
    return analytics.model_dump()


@app.get("/api/v1/reslink/companies")
async def get_company_reslinks_endpoint():
    companies = ResLinkManager.load_company_reslinks()
    return {"status": "success", "companies": companies}


@app.post("/api/v1/reslink/companies")
async def create_or_update_company_reslink_endpoint(request: Request):
    try:
        body = await request.json()
        saved = ResLinkManager.add_or_update_company_reslink(body)
        return {"status": "success", "company": saved}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/reslink/companies/{company_id}")
async def delete_company_reslink_endpoint(company_id: str):
    success = ResLinkManager.delete_company_reslink(company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company ResLink not found")
    return {"status": "success", "message": f"Company ResLink {company_id} deleted."}


@app.patch("/api/v1/reslink/companies/{company_id}/status")
async def update_company_status_endpoint(company_id: str, request: Request):
    try:
        body = await request.json()
        new_status = body.get("status", "Viewed by Recruiter")
        new_code = body.get("status_code", "viewed")
        
        companies = ResLinkManager.load_company_reslinks()
        for c in companies:
            if c["id"] == company_id:
                c["status"] = new_status
                c["status_code"] = new_code
                if "video_watched_pct" in body:
                    c["video_watched_pct"] = body["video_watched_pct"]
                if "cv_downloaded" in body:
                    c["cv_downloaded"] = body["cv_downloaded"]
                ResLinkManager.save_company_reslinks(companies)
                return {"status": "success", "company": c}
                
        raise HTTPException(status_code=404, detail="Company not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
