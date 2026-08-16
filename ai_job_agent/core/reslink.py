import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from core.resume_parser import UserProfile
from config import DATA_DIR, OUTPUT_DIR
from core.security_shield import SecurityShield


class RecruiterCTASettings(BaseModel):
    calendly_url: Optional[str] = "https://calendly.com"
    whatsapp_number: Optional[str] = "+211920123456"
    telegram_username: Optional[str] = "@career_agent"
    direct_email: Optional[str] = "alex.rivera@example.com"
    linkedin_url: Optional[str] = "https://linkedin.com"
    github_url: Optional[str] = "https://github.com"
    portfolio_url: Optional[str] = "https://portfolio.dev"
    enable_booking: bool = True
    enable_cv_download: bool = True


class ResLinkProfile(BaseModel):
    slug: str = "alex-rivera"
    full_name: str = "Alex Rivera"
    tagline: str = "Senior AI Engineer & LLM Systems Specialist"
    location: str = "Juba, South Sudan (Worldwide Remote)"
    summary_bio: str = "Passionate AI Engineer with 4+ years of experience architecting high-throughput LLM pipelines, autonomous multi-agent systems, and scalable full-stack applications."
    video_url: str = ""
    video_duration: float = 60.0
    theme: str = "glassmorphic_dark"  # glassmorphic_dark, executive_slate, minimalist_light, cyber_neon
    selected_cv_template: str = "harvard"  # modern, harvard, tech, minimal
    target_job_title: str = "Senior AI Engineer"
    target_company: str = "Global Tech Employers"
    senior_contact: Optional[str] = "Hiring Team"
    pitch_script: str = (
        "Hi there! I'm Alex Rivera, a Senior AI Engineer specializing in autonomous multi-agent systems and high-scale LLM pipelines. "
        "Over the past 4 years, I have architected production AI applications that reduced inference latency by 45% and scaled to millions of queries. "
        "I thrive in worldwide remote environments and deliver immediate impact in Python, PyTorch, FastAPI, and modern cloud infrastructures. "
        "Feel free to explore my interactive experience below, download my tailored resume, or schedule a quick intro call directly. Looking forward to connecting!"
    )
    linkedin_outreach_note: str = (
        "Hi [Hiring Manager], I saw your opening for the Senior AI Engineer position. "
        "I recorded a 60-second video pitch introducing how my background in multi-agent systems and LLM pipelines directly aligns with your requirements: {reslink_url}\n\n"
        "Best regards,\nAlex Rivera"
    )
    competency_badges: List[str] = Field(default_factory=lambda: [
        "⚡ 4+ Yrs Python & AI Architecture",
        "🚀 Scaled LLM Pipelines to 5M+ Queries",
        "🌍 Worldwide Remote & Global Delivery",
        "🎓 Proven Track Record in Production Agents"
    ])
    cta_settings: RecruiterCTASettings = Field(default_factory=RecruiterCTASettings)
    is_public: bool = True
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class AnalyticsRecord(BaseModel):
    total_views: int = 0
    unique_visitors: int = 0
    video_plays: int = 0
    cv_downloads: int = 0
    calendly_clicks: int = 0
    average_watch_seconds: float = 0.0
    recent_events: List[Dict[str, Any]] = Field(default_factory=list)


class ResLinkManager:
    """
    Core Management Engine for ResLink Interactive Video Resumes & Recruiter Outreach Hub.
    """
    PROFILE_PATH = DATA_DIR / "reslink_profile.json"
    ANALYTICS_PATH = DATA_DIR / "reslink_analytics.json"

    @classmethod
    def sanitize_teleprompter_script(cls, raw_text: str) -> str:
        """
        Sanitizes and cleans script text for smooth, natural human reading on teleprompters:
        - Removes robotic AI bracket placeholders, markdown tokens, and asterisks.
        - Expands shorthand abbreviations to natural spoken English.
        - Cleans punctuation and whitespace for natural cadence.
        """
        if not raw_text:
            return ""
        
        text = str(raw_text)
        # Strip markdown bold/italic/code/headers
        text = re.sub(r'[\*\#\_`~]', '', text)
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean robotic brackets like [Insert Name], [Company], etc.
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\{.*?\}', '', text)
        
        # Expand spoken shorthands for natural teleprompter speech
        shorthand_map = {
            r'\bw/\b': 'with',
            r'\bw/o\b': 'without',
            r'\be\.g\.,?\b': 'for example,',
            r'\bi\.e\.,?\b': 'that is,',
            r'\betc\.\b': 'and more',
            r'\b&\b': 'and',
            r'\bapprox\.\b': 'approximately',
            r'\bmgmt\b': 'management',
            r'\bdev\b': 'development',
            r'\bdevs\b': 'developers',
            r'\bprod\b': 'production',
            r'\bdept\b': 'department',
            r'\byrs\b': 'years',
            r'\byr\b': 'year',
            r'\bexp\b': 'experience',
        }
        for pattern, replacement in shorthand_map.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Standardize multiple spaces and newlines into clean teleprompter paragraphs
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{2,}', '\n\n', text)
        text = text.strip()

        # Sanitize string through SecurityShield
        return SecurityShield.sanitize_text_content(text, "Pitch Script")

    @classmethod
    def load_profile(cls, fallback_profile: Optional[UserProfile] = None) -> ResLinkProfile:
        if cls.PROFILE_PATH.exists():
            try:
                with open(cls.PROFILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return ResLinkProfile(**data)
            except Exception as e:
                print(f"[Warning] Failed to parse ResLink profile from disk: {e}")

        # Initialize from candidate profile if available
        prof = fallback_profile
        slug = "alex-rivera"
        name = "Alex Rivera"
        tagline = "Senior AI Engineer & LLM Specialist"
        loc = "Worldwide Remote"
        bio = "Experienced professional ready to deliver immediate value."

        if prof:
            name = prof.full_name or name
            clean_slug = re.sub(r'[^a-zA-Z0-9-]', '', name.lower().replace(' ', '-'))
            slug = clean_slug or slug
            exp_list = getattr(prof, 'experience', None) or getattr(prof, 'experiences', [])
            if exp_list and len(exp_list) > 0:
                first_role = getattr(exp_list[0], 'role', None) or getattr(exp_list[0], 'title', 'Engineering Specialist')
                tagline = f"{first_role} & Technical Specialist"
            if prof.contact and prof.contact.location:
                loc = prof.contact.location
            if prof.summary:
                bio = prof.summary

        new_profile = ResLinkProfile(
            slug=slug,
            full_name=name,
            tagline=tagline,
            location=loc,
            summary_bio=bio,
        )
        cls.save_profile(new_profile)
        return new_profile

    @classmethod
    def save_profile(cls, profile: ResLinkProfile) -> bool:
        try:
            profile.updated_at = datetime.now().isoformat()
            with open(cls.PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(profile.model_dump(), f, indent=2)
            return True
        except Exception as e:
            print(f"[Error] Failed to save ResLink profile: {e}")
            return False

    @classmethod
    def generate_job_matched_pitch(
        cls,
        job_requirements: str,
        job_title: str,
        company: str,
        candidate_profile: UserProfile,
        duration_mode: str = "60s",
        senior_contact: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translates target job offer requirements & candidate CV experience into:
        1. An authentic, human-sounding spoken pitch script for the teleprompter.
        2. Animated competency badges for on-screen highlight.
        3. A personalized LinkedIn DM / InMail outreach note addressed to the senior contact.
        """
        req_clean = SecurityShield.sanitize_text_content(job_requirements, "Job Requirements")
        title_clean = SecurityShield.sanitize_string(job_title or "Target Role", "Job Title")
        company_clean = SecurityShield.sanitize_string(company or "your team", "Company Name")
        contact_clean = SecurityShield.sanitize_string(senior_contact or "", "Senior Contact")

        req_lower = req_clean.lower()
        skills = candidate_profile.skills or ["Python", "Machine Learning", "FastAPI", "Cloud Infrastructure", "System Architecture"]
        experiences = getattr(candidate_profile, 'experience', None) or getattr(candidate_profile, 'experiences', [])

        # Find matching skills from candidate CV
        matched_skills = [s for s in skills if s.lower() in req_lower]
        if not matched_skills:
            matched_skills = skills[:4]

        # Top achievement highlights
        top_exp = experiences[0] if experiences else None
        if top_exp:
            top_role = getattr(top_exp, 'role', None) or getattr(top_exp, 'title', 'Engineering Specialist')
            top_company = getattr(top_exp, 'company', 'Tech Innovation')
            bullets = getattr(top_exp, 'bullets', None) or getattr(top_exp, 'highlights', None) or []
            top_bullet = bullets[0] if bullets else "delivered scalable systems with measurable performance gains"
        else:
            top_role = "Engineering Specialist"
            top_company = "Tech Innovation"
            top_bullet = "delivered scalable systems with measurable performance gains"

        # Format Senior Contact Greeting
        first_name = candidate_profile.full_name.split()[0] if candidate_profile.full_name else "Alex"
        full_name = candidate_profile.full_name or "Alex Rivera"

        if contact_clean and len(contact_clean.strip()) > 0:
            contact_parts = contact_clean.strip().split()
            titles = {"dr.", "dr", "mr.", "mr", "mrs.", "mrs", "ms.", "ms", "prof.", "prof"}
            if contact_parts[0].lower() in titles and len(contact_parts) > 1:
                contact_salutation = f"{contact_parts[0]} {contact_parts[1]}"  # e.g., "Dr. Demis"
            else:
                contact_salutation = contact_parts[0]  # e.g., "Sarah" from "Sarah Jenkins"
            greeting_spoken = f"Hi {contact_salutation}, and the {company_clean} team!"
            greeting_written = f"Hi {contact_salutation},"
        else:
            greeting_spoken = f"Hi {company_clean} team!"
            greeting_written = f"Hi {company_clean} Hiring Team,"

        # Natural, authentic, conversational human pitch generation (NOT robotic AI sounding)
        skill_1 = matched_skills[0] if len(matched_skills) > 0 else "system architecture"
        skill_2 = matched_skills[1] if len(matched_skills) > 1 else "high-throughput engineering"
        skill_3 = matched_skills[2] if len(matched_skills) > 2 else "cloud infrastructure"

        clean_bullet = top_bullet.strip().rstrip('.')
        if clean_bullet.startswith("•") or clean_bullet.startswith("-"):
            clean_bullet = clean_bullet[1:].strip()
        # lowercase start if needed
        clean_bullet_lower = clean_bullet[0].lower() + clean_bullet[1:] if len(clean_bullet) > 1 else clean_bullet

        if duration_mode == "30s":
            raw_script = (
                f"{greeting_spoken} I am {first_name}. "
                f"I saw your opening for the {title_clean} position and wanted to introduce myself directly. "
                f"With deep hands-on expertise in {skill_1} and {skill_2}, my recent focus at {top_company} was when I {clean_bullet_lower}. "
                f"I am ready to step in and deliver immediate technical value for {company_clean}. "
                f"Feel free to explore my interactive project timeline below, or click to schedule a quick conversation. Thank you!"
            )
        elif duration_mode == "90s":
            raw_script = (
                f"{greeting_spoken} My name is {full_name}, and I am excited to share my background for the {title_clean} opportunity at {company_clean}. "
                f"Throughout my career as a {top_role}, I have focused on architecting resilient, high-performance systems with {skill_1}, {skill_2}, and {skill_3}. "
                f"During my time at {top_company}, a major milestone was when I {clean_bullet_lower}, which significantly improved system reliability and speed. "
                f"Reviewing the requirements for {company_clean}, your focus on scalable execution and technical excellence directly matches how I build software. "
                f"I enjoy solving high-impact problems, collaborating with cross-functional teams, and shipping production-ready features quickly. "
                f"Right below this video, you can review my interactive experience timeline, test live project demos, download my tailored PDF resume, or book an introductory call on my calendar. "
                f"Thank you for your time, and I look forward to speaking with you!"
            )
        else:  # Default 60s
            raw_script = (
                f"{greeting_spoken} My name is {full_name}, and I wanted to introduce myself for the {title_clean} role at {company_clean}. "
                f"Over the past several years, I have specialized in {skill_1} and {skill_2}, building reliable software that scales smoothly under heavy production loads. "
                f"At {top_company}, I recently {clean_bullet_lower}, delivering measurable impact for the business and engineering organization. "
                f"What excites me most about {company_clean} is your commitment to high-quality engineering. My background enables me to contribute immediately and integrate seamlessly into your workflow. "
                f"You can explore my full interactive resume below, download my tailored CV, or schedule a quick chat directly. Looking forward to connecting!"
            )

        # Sanitize script for natural teleprompter readability
        pitch_script = cls.sanitize_teleprompter_script(raw_script)

        # Dynamic badges for video overlays
        competency_badges = [
            f"⚡ {skill_1} Specialist",
            f"🚀 {top_role} @ {top_company}",
            f"🎯 Matched for {title_clean}",
            f"🌍 Worldwide Remote & Immediate Delivery"
        ]

        # LinkedIn Outreach Note
        slug = re.sub(r'[^a-zA-Z0-9-]', '', full_name.lower().replace(' ', '-')) or "alex-rivera"
        outreach_note = (
            f"{greeting_written}\n\n"
            f"I came across the {title_clean} role at {company_clean} and wanted to reach out directly. "
            f"Rather than just sending a flat resume, I recorded a 60-second video pitch and interactive experience tailored to your team's requirements:\n\n"
            f"👉 http://127.0.0.1:8000/p/{slug}\n\n"
            f"It highlights my direct experience in {skill_1} and {skill_2}, along with key deliverables from my time at {top_company}. "
            f"I would love to connect and discuss how I can add immediate value to {company_clean}!\n\n"
            f"Best regards,\n{full_name}"
        )

        # Dynamic badges for video overlays
        competency_badges = [
            f"⚡ {matched_skills[0]} Specialist" if len(matched_skills) > 0 else "⚡ Technical Specialist",
            f"🚀 {top_role} @ {top_company}",
            f"🎯 Matched for {title_clean}",
            f"🌍 Worldwide Remote & Immediate Impact"
        ]

        # LinkedIn Outreach Note
        slug = re.sub(r'[^a-zA-Z0-9-]', '', full_name.lower().replace(' ', '-')) or "alex-rivera"
        outreach_note = (
            f"Hi Hiring Team,\n\n"
            f"I came across the {title_clean} role at {company_clean} and was very impressed by your team's mission. "
            f"Rather than just sending a flat resume, I put together a 60-second video pitch and interactive project link tailored to your requirements:\n\n"
            f"👉 http://127.0.0.1:8000/p/{slug}\n\n"
            f"It covers my direct experience in {', '.join(matched_skills[:2])} and key accomplishments at {top_company}. "
            f"Would love to connect and discuss how I can contribute to {company_clean}!\n\n"
            f"Best regards,\n{full_name}"
        )

        return {
            "pitch_script": pitch_script,
            "competency_badges": competency_badges,
            "linkedin_outreach_note": outreach_note,
            "target_job_title": title_clean,
            "target_company": company_clean,
            "matched_skills": matched_skills,
            "estimated_reading_seconds": len(pitch_script.split()) / 2.3  # approx 130 WPM
        }

    @classmethod
    def load_analytics(cls) -> AnalyticsRecord:
        if cls.ANALYTICS_PATH.exists():
            try:
                with open(cls.ANALYTICS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return AnalyticsRecord(**data)
            except Exception:
                pass
        return AnalyticsRecord()

    @classmethod
    def record_event(cls, event_type: str, metadata: Optional[Dict[str, Any]] = None) -> AnalyticsRecord:
        analytics = cls.load_analytics()
        meta = metadata or {}
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if event_type == "page_view":
            analytics.total_views += 1
            if meta.get("is_unique", True):
                analytics.unique_visitors += 1
        elif event_type == "video_play":
            analytics.video_plays += 1
        elif event_type == "cv_download":
            analytics.cv_downloads += 1
        elif event_type == "calendly_click":
            analytics.calendly_clicks += 1

        if "watch_seconds" in meta:
            duration = float(meta["watch_seconds"])
            if analytics.average_watch_seconds == 0:
                analytics.average_watch_seconds = duration
            else:
                analytics.average_watch_seconds = round((analytics.average_watch_seconds + duration) / 2.0, 1)

        event_log = {
            "event": event_type,
            "timestamp": now_str,
            "referrer": meta.get("referrer", "direct"),
            "device": meta.get("device", "desktop"),
            "city": meta.get("city", "Global Recruiter View")
        }
        analytics.recent_events.insert(0, event_log)
        analytics.recent_events = analytics.recent_events[:50]  # Keep latest 50 events

        try:
            with open(cls.ANALYTICS_PATH, "w", encoding="utf-8") as f:
                json.dump(analytics.model_dump(), f, indent=2)
        except Exception as e:
            print(f"[Warning] Failed to persist analytics: {e}")

        return analytics
