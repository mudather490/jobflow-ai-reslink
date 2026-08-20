import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from core.resume_parser import UserProfile
from config import DATA_DIR, OUTPUT_DIR
from core.security_shield import SecurityShield


class RecruiterCTASettings(BaseModel):
    calendly_url: Optional[str] = "https://calendly.com"
    whatsapp_number: Optional[str] = ""
    telegram_username: Optional[str] = ""
    direct_email: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    github_url: Optional[str] = ""
    portfolio_url: Optional[str] = ""
    enable_booking: bool = True
    enable_cv_download: bool = True


class ResLinkProfile(BaseModel):
    slug: str = "candidate-profile"
    full_name: str = "Candidate Profile"
    tagline: str = "Engineering Specialist"
    location: str = ""
    summary_bio: str = ""
    video_url: str = ""
    video_duration: float = 60.0
    theme: str = "glassmorphic_dark"  # glassmorphic_dark, executive_slate, minimalist_light, cyber_neon
    selected_cv_template: str = "corporate_elite"  # modern, harvard, tech, corporate_elite
    target_job_title: str = "AI & Software Engineering Specialist"
    target_company: str = "Global Tech Employers"
    senior_contact: Optional[str] = "Hiring Team"
    pitch_script: str = ""
    linkedin_outreach_note: str = ""
    attached_resume_filename: Optional[str] = None
    attached_resume_filepath: Optional[str] = None
    attached_resume_size: Optional[str] = None
    attached_profile: Optional[Dict[str, Any]] = None
    competency_badges: List[str] = Field(default_factory=lambda: [
        "⚡ Verified Skills & Practical Projects",
        "🚀 Scalable Architecture & System Design",
        "🎓 Proven Track Record"
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

        # Check if user profiles exist in data/users
        users_dir = DATA_DIR / "users"
        if users_dir.exists():
            for p_file in users_dir.glob("*_profile.json"):
                try:
                    with open(p_file, "r", encoding="utf-8") as f:
                        u_data = json.load(f)
                    if "reslink" in u_data and isinstance(u_data["reslink"], dict):
                        return ResLinkProfile(**u_data["reslink"])
                except Exception:
                    continue

        slug = "candidate-profile"
        name = "Candidate Profile"
        tagline = "Engineering Specialist"
        loc = "Worldwide Remote"
        bio = ""

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
    def load_profile_by_slug(cls, slug: str, fallback_profile: Optional[UserProfile] = None) -> Tuple[ResLinkProfile, Optional[UserProfile]]:
        clean_slug = re.sub(r'[^a-zA-Z0-9-]', '', slug.lower()).strip('-')
        
        # 1. Search in data/users/ for stored profiles matching slug
        users_dir = DATA_DIR / "users"
        if users_dir.exists():
            for p_file in users_dir.glob("*_profile.json"):
                try:
                    with open(p_file, "r", encoding="utf-8") as f:
                        u_data = json.load(f)
                    prof_data = u_data.get("profile", {})
                    full_name = prof_data.get("full_name", "")
                    prof_slug = re.sub(r'[^a-zA-Z0-9-]', '', full_name.lower().replace(' ', '-')).strip('-')
                    slug_condensed = re.sub(r'[^a-zA-Z0-9]', '', clean_slug)
                    name_condensed = re.sub(r'[^a-zA-Z0-9]', '', full_name.lower())
                    p_file_condensed = re.sub(r'[^a-zA-Z0-9]', '', p_file.stem.lower())

                    if (prof_slug == clean_slug or 
                        slug_condensed == name_condensed or 
                        slug_condensed in p_file_condensed or 
                        (len(slug_condensed) > 4 and slug_condensed in name_condensed)):
                        u_prof = UserProfile(**prof_data)
                        att_fname = u_data.get("filename")
                        att_fsize = u_data.get("filesize")
                        reslink_prof = cls.sync_with_user_profile(
                            u_prof, filename=att_fname, filesize=att_fsize, save_user_cache=False, save_global=False
                        )
                        # Patch filepath if possible
                        if reslink_prof.attached_resume_filepath is None and att_fname:
                            possible_path = DATA_DIR / att_fname
                            if possible_path.exists():
                                reslink_prof.attached_resume_filepath = str(possible_path)
                        return reslink_prof, u_prof
                except Exception:
                    continue

        # 2. Check if a resume file exists in data/ matching the slug
        for f in DATA_DIR.glob("*.*"):
            if f.suffix.lower() in [".pdf", ".docx"]:
                f_name_condensed = re.sub(r'[^a-zA-Z0-9]', '', f.stem.lower())
                slug_condensed = re.sub(r'[^a-zA-Z0-9]', '', clean_slug)
                if (len(slug_condensed) > 4 and slug_condensed in f_name_condensed):
                    try:
                        u_prof = ResumeParser.parse_file(str(f))
                        reslink_prof = cls.sync_with_user_profile(
                            u_prof, filename=f.name, filepath=str(f), filesize=f"{round(f.stat().st_size/1024, 1)} KB", save_user_cache=True, save_global=False
                        )
                        return reslink_prof, u_prof
                    except Exception:
                        pass

        # 3. Fallback to main ResLink profile
        res_prof = cls.load_profile()
        u_prof = UserProfile(**res_prof.attached_profile) if res_prof.attached_profile else None
        return res_prof, u_prof

    @classmethod
    def sync_with_user_profile(
        cls,
        profile: UserProfile,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        filesize: Optional[str] = None,
        save_user_cache: bool = True,
        save_global: bool = True,
    ) -> ResLinkProfile:
        """
        Synchronizes the candidate's authentic uploaded resume profile with ResLink Video Profile:
        - Real Full Name and Clean URL Slug
        - Real Target Role / Tagline
        - Contact Info (Email, Phone/WhatsApp, LinkedIn, GitHub, Portfolio)
        - Location
        - Executive Summary / Bio
        - Real competence badges from user skills and top experience
        - Attached resume filename and parsed profile payload
        """
        if not profile:
            return cls.load_profile()

        clean_name = re.sub(r'\s{2,}', ' ', (profile.full_name or "Candidate").strip())
        clean_slug = re.sub(r'-+', '-', re.sub(r'[^a-zA-Z0-9-]', '', clean_name.lower().replace(' ', '-'))).strip('-') or "candidate"
        tagline = profile.headline or profile.target_role or "AI & Software Engineering Specialist"
        location = profile.contact.location or ""
        bio = profile.summary or ""
        
        # Load existing profile to preserve custom video if already recorded
        existing = None
        user_cache_file = DATA_DIR / "users" / f"{clean_slug}_profile.json"
        if user_cache_file.exists():
            try:
                with open(user_cache_file, "r", encoding="utf-8") as f:
                    u_data = json.load(f)
                    if "reslink" in u_data and isinstance(u_data["reslink"], dict):
                        existing = ResLinkProfile(**u_data["reslink"])
            except Exception:
                existing = None

        if not existing and cls.PROFILE_PATH.exists():
            try:
                with open(cls.PROFILE_PATH, "r", encoding="utf-8") as f:
                    existing = ResLinkProfile(**json.load(f))
            except Exception:
                existing = None

        video_url = existing.video_url if existing else ""
        video_duration = existing.video_duration if existing else 60.0
        theme = existing.theme if existing else "glassmorphic_dark"
        selected_template = existing.selected_cv_template if existing else "corporate_elite"
        att_filename = filename or (existing.attached_resume_filename if existing else None)
        att_filepath = filepath or (existing.attached_resume_filepath if existing else None)
        att_size = filesize or (existing.attached_resume_size if existing else None)

        # Construct authentic competency badges from user's real skills & experience
        real_badges = []
        if profile.skills:
            top_skills = profile.skills[:3]
            real_badges.append(f"⚡ Core: {', '.join(top_skills)}")
        if profile.experience and len(profile.experience) > 0:
            top_exp = profile.experience[0]
            real_badges.append(f"💼 {top_exp.role} at {top_exp.company}")
        if profile.certifications and len(profile.certifications) > 0:
            real_badges.append(f"🎓 {profile.certifications[0].name}")
        if not real_badges:
            real_badges = [
                f"⚡ {tagline}",
                "🎓 Verified Skills & Practical Projects"
            ]

        # Extract only real phone number (ignore dummy placeholder numbers)
        real_phone = profile.contact.phone or ""
        if "211920123456" in real_phone.replace(" ", "") or "920123456" in real_phone.replace(" ", ""):
            real_phone = ""

        cta = RecruiterCTASettings(
            direct_email=profile.contact.email or "",
            whatsapp_number=real_phone,
            linkedin_url=profile.contact.linkedin or "",
            github_url=profile.contact.github or "",
            portfolio_url=profile.contact.portfolio or "",
            calendly_url=existing.cta_settings.calendly_url if (existing and existing.cta_settings and "calendly.com" in existing.cta_settings.calendly_url) else "",
            telegram_username=existing.cta_settings.telegram_username if (existing and existing.cta_settings) else "",
            enable_booking=True,
            enable_cv_download=True,
        )

        synced_profile = ResLinkProfile(
            slug=clean_slug,
            full_name=clean_name,
            tagline=tagline,
            location=location,
            summary_bio=bio,
            video_url=video_url,
            video_duration=video_duration,
            theme=theme,
            selected_cv_template=selected_template,
            target_job_title=profile.target_role or tagline,
            attached_resume_filename=att_filename,
            attached_resume_filepath=att_filepath,
            attached_resume_size=att_size,
            attached_profile=profile.model_dump(),
            competency_badges=real_badges,
            cta_settings=cta,
            is_public=True,
        )

        if save_global:
            cls.save_profile(synced_profile)

        # Save to users cache directory for permanent slug-based lookup
        if save_user_cache:
            users_dir = DATA_DIR / "users"
            users_dir.mkdir(parents=True, exist_ok=True)
            user_cache_file = users_dir / f"{clean_slug}_profile.json"
            try:
                with open(user_cache_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "filename": att_filename or f"{clean_name.replace(' ', '_')}_Resume.pdf",
                        "filesize": att_size or "Verified (Cloud Synced)",
                        "profile": profile.model_dump(),
                        "reslink": synced_profile.model_dump()
                    }, f, indent=2)
            except Exception as ue:
                print(f"[Warning] Failed to write user cache file: {ue}")

        return synced_profile

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
        title_clean = SecurityShield.sanitize_text_content(job_title or "Target Role", "Job Title")
        company_clean = SecurityShield.sanitize_text_content(company or "your team", "Company Name")
        contact_clean = SecurityShield.sanitize_text_content(senior_contact or "", "Senior Contact")

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
        first_name = candidate_profile.full_name.split()[0] if (candidate_profile and candidate_profile.full_name) else "Mudather"
        full_name = candidate_profile.full_name if (candidate_profile and candidate_profile.full_name) else "Mudather Mohammed"

        generic_contacts = {"hiring team", "hiring manager", "recruiter", "talent team", "hr team", "hiring lead", "team"}
        if contact_clean and contact_clean.strip().lower() not in generic_contacts:
            contact_parts = contact_clean.strip().split()
            titles = {"dr.", "dr", "mr.", "mr", "mrs.", "mrs", "ms.", "ms", "prof.", "prof"}
            if contact_parts[0].lower() in titles and len(contact_parts) > 1:
                contact_salutation = f"{contact_parts[0]} {contact_parts[1]}"  # e.g., "Dr. Demis"
            else:
                contact_salutation = contact_parts[0]  # e.g., "Sarah"
            greeting_spoken = f"Hi {contact_salutation}, and the {company_clean} team!"
            greeting_written = f"Hi {contact_salutation},"
        else:
            greeting_spoken = f"Hi {company_clean} team!"
            greeting_written = f"Hi {company_clean} Hiring Team,"

        # Natural, authentic, conversational human pitch generation (NOT robotic AI sounding)
        skill_1 = matched_skills[0] if len(matched_skills) > 0 else "Python"
        skill_2 = matched_skills[1] if len(matched_skills) > 1 else "Machine Learning"
        skill_3 = matched_skills[2] if len(matched_skills) > 2 else "FastAPI & AI Systems"

        clean_bullet = top_bullet.strip().rstrip('.')
        if clean_bullet.startswith("•") or clean_bullet.startswith("-"):
            clean_bullet = clean_bullet[1:].strip()
        # lowercase start if needed
        clean_bullet_lower = clean_bullet[0].lower() + clean_bullet[1:] if len(clean_bullet) > 1 else clean_bullet

        if any(clean_bullet_lower.startswith(v) for v in ["building", "developing", "architecting", "implementing", "leading", "creating", "designing", "training"]):
            bullet_phrase = f"focused on {clean_bullet_lower}"
        elif any(clean_bullet_lower.startswith(v) for v in ["built", "developed", "architected", "implemented", "led", "created", "designed", "trained"]):
            bullet_phrase = clean_bullet_lower
        else:
            bullet_phrase = f"focused on {clean_bullet_lower}"

        if duration_mode == "30s":
            raw_script = (
                f"{greeting_spoken} I am {first_name}. "
                f"I saw your opening for the {title_clean} position and wanted to introduce myself directly. "
                f"With deep hands-on expertise in {skill_1} and {skill_2}, at {top_company} I {bullet_phrase}. "
                f"I am ready to step in and deliver immediate technical value for {company_clean}. "
                f"Feel free to explore my interactive project timeline below, or click to schedule a quick conversation. Thank you!"
            )
        elif duration_mode == "90s":
            raw_script = (
                f"{greeting_spoken} My name is {full_name}, and I am excited to share my background for the {title_clean} opportunity at {company_clean}. "
                f"Throughout my career as a {top_role}, I have focused on building resilient, high-performance systems with {skill_1}, {skill_2}, and {skill_3}. "
                f"During my time at {top_company}, a major milestone was when I {bullet_phrase}, which significantly improved system reliability and speed. "
                f"What excites me most about {company_clean} is the opportunity to solve meaningful technical challenges alongside an exceptional team. "
                f"I take complete ownership from architecture to production deployment. "
                f"Please take a look at my verified code repositories below, download my tailored resume, or book a short intro call directly. Looking forward to speaking with you!"
            )
        else:  # 60s default
            raw_script = (
                f"{greeting_spoken} My name is {full_name}, and I wanted to introduce myself for the {title_clean} role at {company_clean}. "
                f"Over the past several years, I have specialized in {skill_1} and {skill_2}, building reliable software that scales smoothly under heavy production loads. "
                f"At {top_company}, I recently {bullet_phrase}, delivering measurable impact for the engineering organization. "
                f"What excites me most about {company_clean} is your commitment to high-quality engineering. "
                f"My background enables me to contribute immediately and integrate seamlessly into your workflow. "
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

    @classmethod
    def load_company_reslinks(cls) -> List[Dict[str, Any]]:
        company_path = DATA_DIR / "company_reslinks.json"
        if company_path.exists():
            try:
                with open(company_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load company reslinks: {e}")
        
        # Default seeded company links for real-time tracking
        default_companies = [
            {
                "id": "amazon-ai",
                "company_name": "Amazon",
                "target_role": "Junior AI Engineer / ML Infrastructure",
                "recruiter_name": "David Miller (Tech Talent Lead)",
                "recruiter_channel": "LinkedIn InMail",
                "template_id": "corporate_elite",
                "template_label": "Corporate Elite",
                "custom_param": "Amazon",
                "reslink_url": "/p/mudather-mohammed?company=Amazon",
                "status": "Viewed by Recruiter (3m ago)",
                "status_code": "viewed",
                "video_watched_pct": 100,
                "cv_downloaded": True,
                "notes": "Focused on distributed ML models, FastAPI pipelines, and cloud engineering.",
                "created_at": "2026-08-16T18:30:00Z"
            },
            {
                "id": "openai-ml",
                "company_name": "OpenAI",
                "target_role": "Machine Learning Engineer",
                "recruiter_name": "Sarah Jenkins (AI Hiring Lead)",
                "recruiter_channel": "LinkedIn Connection",
                "template_id": "tech_specialist",
                "template_label": "Tech Specialist",
                "custom_param": "OpenAI",
                "reslink_url": "/p/mudather-mohammed?company=OpenAI",
                "status": "CV Downloaded (18m ago)",
                "status_code": "downloaded",
                "video_watched_pct": 94,
                "cv_downloaded": True,
                "notes": "Emphasized neural network architecture from scratch and LLM agent orchestration.",
                "created_at": "2026-08-16T19:00:00Z"
            },
            {
                "id": "google-ai",
                "company_name": "Google",
                "target_role": "AI Research / ML Systems Engineer",
                "recruiter_name": "Marcus Vance (Senior Technical Recruiter)",
                "recruiter_channel": "Direct Application",
                "template_id": "harvard_consulting",
                "template_label": "Harvard Consulting",
                "custom_param": "Google",
                "reslink_url": "/p/mudather-mohammed?company=Google",
                "status": "Interview Scheduled 🤝",
                "status_code": "interview",
                "video_watched_pct": 100,
                "cv_downloaded": True,
                "notes": "Highlighted mathematical foundations, PyTorch, Scikit-learn, and high-performance algorithms.",
                "created_at": "2026-08-16T20:15:00Z"
            },
            {
                "id": "scaleai-ml",
                "company_name": "Scale AI",
                "target_role": "Junior Machine Learning Engineer",
                "recruiter_name": "Elena Rostova (Head of AI Talent)",
                "recruiter_channel": "LinkedIn InMail",
                "template_id": "corporate_elite",
                "template_label": "Corporate Elite",
                "custom_param": "ScaleAI",
                "reslink_url": "/p/mudather-mohammed?company=ScaleAI",
                "status": "Video Watched 🎥 (88%)",
                "status_code": "watched",
                "video_watched_pct": 88,
                "cv_downloaded": False,
                "notes": "Tailored data annotation pipelines and RLHF evaluation workflows.",
                "created_at": "2026-08-16T21:40:00Z"
            }
        ]
        cls.save_company_reslinks(default_companies)
        return default_companies

    @classmethod
    def save_company_reslinks(cls, items: List[Dict[str, Any]]) -> bool:
        company_path = DATA_DIR / "company_reslinks.json"
        try:
            with open(company_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2)
            return True
        except Exception as e:
            print(f"[Warning] Failed to persist company reslinks: {e}")
            return False

    @classmethod
    def add_or_update_company_reslink(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        companies = cls.load_company_reslinks()
        cid = data.get("id") or re.sub(r'[^a-zA-Z0-9-]', '', (data.get("company_name", "company") + "-" + data.get("target_role", "role")).lower().replace(' ', '-'))
        data["id"] = cid
        
        template_map = {
            "corporate_elite": "Corporate Elite",
            "harvard_consulting": "Harvard Consulting",
            "tech_specialist": "Tech Specialist",
            "modern": "Modern Executive"
        }
        data["template_label"] = template_map.get(data.get("template_id", "corporate_elite"), "Corporate Elite")
        
        clean_company = re.sub(r'[^a-zA-Z0-9]', '', data.get("company_name", "General"))
        data["custom_param"] = clean_company
        data["reslink_url"] = f"/p/mudather-mohammed?company={clean_company}"
        
        if "status" not in data:
            data["status"] = "Link Generated & Ready"
            data["status_code"] = "ready"
        if "created_at" not in data:
            data["created_at"] = datetime.now().isoformat()

        # Update if existing, otherwise append
        idx = next((i for i, c in enumerate(companies) if c["id"] == cid), None)
        if idx is not None:
            companies[idx].update(data)
        else:
            companies.insert(0, data)

        cls.save_company_reslinks(companies)
        return data

    @classmethod
    def delete_company_reslink(cls, company_id: str) -> bool:
        companies = cls.load_company_reslinks()
        filtered = [c for c in companies if c["id"] != company_id]
        if len(filtered) != len(companies):
            cls.save_company_reslinks(filtered)
            return True
        return False
