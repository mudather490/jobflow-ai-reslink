import os
from typing import Optional, Dict, Any, List
from pathlib import Path

# Optional Supabase Python client
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False


class SupabaseAdapter:
    """
    Production Supabase Cloud Database & Storage Adapter.
    Automatically switches to Supabase when credentials are configured in .env.
    Falls back gracefully to local JSON storage if offline or unconfigured.
    """
    _client: Optional[Any] = None

    @classmethod
    def get_client(cls) -> Optional[Any]:
        if cls._client is not None:
            return cls._client

        if not HAS_SUPABASE:
            return None

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if url and key and "your-project" not in url:
            try:
                cls._client = create_client(url, key)
                print(f"[Supabase] Connected to project: {url}")
                return cls._client
            except Exception as e:
                print(f"[Supabase] Connection error: {e}")
                return None
        return None

    @classmethod
    def is_connected(cls) -> bool:
        return cls.get_client() is not None

    @classmethod
    def save_reslink_profile(cls, profile_dict: Dict[str, Any]) -> bool:
        client = cls.get_client()
        if not client:
            return False
        try:
            slug = profile_dict.get("slug")
            # Upsert into 'reslinks' table
            client.table("reslinks").upsert(profile_dict, on_conflict="slug").execute()
            return True
        except Exception as e:
            print(f"[Supabase] Error saving reslink: {e}")
            return False

    @classmethod
    def get_reslink_profile(cls, slug: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        if not client:
            return None
        try:
            response = client.table("reslinks").select("*").eq("slug", slug).limit(1).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            print(f"[Supabase] Error fetching reslink: {e}")
        return None

    @classmethod
    def record_analytics_event(cls, event_dict: Dict[str, Any]) -> bool:
        client = cls.get_client()
        if not client:
            return False
        try:
            client.table("reslink_analytics").insert(event_dict).execute()
            return True
        except Exception as e:
            print(f"[Supabase] Error recording analytics: {e}")
            return False

    @classmethod
    def get_analytics_summary(cls, slug: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        if not client:
            return None
        try:
            resp = client.table("reslink_analytics").select("*").eq("reslink_slug", slug).execute()
            events = resp.data or []
            total_views = sum(1 for e in events if e.get("event_type") == "page_view")
            video_plays = sum(1 for e in events if e.get("event_type") == "video_play")
            cv_downloads = sum(1 for e in events if e.get("event_type") == "cv_download")
            return {
                "total_views": total_views,
                "video_plays": video_plays,
                "cv_downloads": cv_downloads,
                "recent_events": events[-10:]
            }
        except Exception as e:
            print(f"[Supabase] Error getting analytics: {e}")
        return None

    @classmethod
    def upgrade_user_tier(cls, email: str, tier: str, license_key: str = "", subscription_id: str = "") -> bool:
        """
        Updates a user's subscription tier in Supabase upon successful Gumroad payment.
        """
        if not email:
            return False
        
        client = cls.get_client()
        clean_email = email.strip().lower()
        clean_tier = tier.strip().lower()

        # Update data payload
        user_record = {
            "email": clean_email,
            "subscription_tier": clean_tier,
            "subscription_status": "active",
            "license_key": license_key,
            "gumroad_subscription_id": subscription_id,
            "updated_at": "now()"
        }

        if client:
            try:
                # Upsert into 'profiles' or 'users' table
                client.table("profiles").upsert(user_record, on_conflict="email").execute()
                print(f"[Supabase] Successfully upgraded user {clean_email} to {clean_tier} tier.")
                return True
            except Exception as e:
                print(f"[Supabase] Error upgrading user in Supabase: {e}")

        # Local fallback log
        print(f"[SaaS Manager] User {clean_email} active on tier: {clean_tier} (License: {license_key})")
        return True

    OWNER_EMAIL = "mudatherkbyer@gmail.com"

    @classmethod
    def get_user_tier(cls, email: str) -> str:
        """
        Retrieves user subscription tier ('free', 'pro', 'executive', 'owner').
        ONLY 'mudatherkbyer@gmail.com' (case-insensitive exact match) gets 'owner'.
        Any other account defaults strictly to 'free' unless active in Supabase profiles.
        """
        clean_email = (email or "").strip().lower()
        if not clean_email:
            return "free"

        if clean_email == cls.OWNER_EMAIL:
            return "owner"

        client = cls.get_client()
        if client:
            try:
                res = client.table("profiles").select("subscription_tier, subscription_status").eq("email", clean_email).limit(1).execute()
                if res.data and len(res.data) > 0:
                    row = res.data[0]
                    status = (row.get("subscription_status") or "").strip().lower()
                    tier = (row.get("subscription_tier") or "free").strip().lower()
                    if status == "active" and tier in ["pro", "executive", "owner"]:
                        return tier
            except Exception as e:
                print(f"[Supabase] Error fetching user tier: {e}")

        return "free"


    # ─────────────────────────────────────────────────────────────
    # User Profile, Resume & Settings Persistent Synchronization
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _get_local_user_cache_path(cls, email: str) -> Path:
        from config import DATA_DIR
        clean = (email or "anonymous").strip().lower().replace("@", "_at_").replace(".", "_")
        users_dir = DATA_DIR / "users"
        users_dir.mkdir(parents=True, exist_ok=True)
        return users_dir / f"{clean}_profile.json"

    @classmethod
    def save_user_profile(cls, email: str, profile_dict: Dict[str, Any], filename: str = "") -> bool:
        """
        Saves candidate resume profile, parsed sections, and filename in Supabase and local cache.
        """
        if not email:
            return False
        clean_email = email.strip().lower()
        client = cls.get_client()

        payload = {
            "email": clean_email,
            "full_name": profile_dict.get("full_name", "Candidate"),
            "headline": profile_dict.get("headline", ""),
            "phone_number": profile_dict.get("contact", {}).get("phone") or "",
            "location": profile_dict.get("contact", {}).get("location") or "",
            "linkedin": profile_dict.get("contact", {}).get("linkedin") or "",
            "github": profile_dict.get("contact", {}).get("github") or "",
            "summary": profile_dict.get("summary", ""),
            "skills": profile_dict.get("skills", []),
            "experience": [e if isinstance(e, dict) else (e.model_dump() if hasattr(e, "model_dump") else dict(e)) for e in profile_dict.get("experience", [])],
            "projects": [p if isinstance(p, dict) else (p.model_dump() if hasattr(p, "model_dump") else dict(p)) for p in profile_dict.get("projects", [])],
            "education": [ed if isinstance(ed, dict) else (ed.model_dump() if hasattr(ed, "model_dump") else dict(ed)) for ed in profile_dict.get("education", [])],
            "certifications": [c if isinstance(c, dict) else (c.model_dump() if hasattr(c, "model_dump") else dict(c)) for c in profile_dict.get("certifications", [])],
            "additional_background": profile_dict.get("additional_background", ""),
            "target_role": profile_dict.get("target_role", ""),
            "resume_profile": profile_dict,
            "updated_at": "now()"
        }
        if filename:
            payload["resume_filename"] = filename

        # 1. Update local cache
        try:
            cache_file = cls._get_local_user_cache_path(clean_email)
            cached_data = {}
            if cache_file.exists():
                import json
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                except Exception:
                    pass
            cached_data["profile"] = profile_dict
            if filename:
                cached_data["filename"] = filename
            with open(cache_file, "w", encoding="utf-8") as f:
                import json
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            print(f"[Local Cache] Failed to cache profile for {clean_email}: {e}")

        # 2. Update Supabase
        if client:
            try:
                client.table("profiles").upsert(payload, on_conflict="email").execute()
                print(f"[Supabase] Persisted resume profile for user: {clean_email}")
                return True
            except Exception as e:
                print(f"[Supabase] Error saving profile: {e}")

        return True

    @classmethod
    def get_user_profile(cls, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves user's resume profile from Supabase or local cache.
        """
        if not email:
            return None
        clean_email = email.strip().lower()
        client = cls.get_client()

        # 1. Try Supabase first
        if client:
            try:
                res = client.table("profiles").select("resume_profile, resume_filename, full_name, headline, phone_number, location, linkedin, github, summary, skills, experience, projects, education, certifications, additional_background, target_role").eq("email", clean_email).limit(1).execute()
                if res.data and len(res.data) > 0:
                    row = res.data[0]
                    profile = row.get("resume_profile")
                    if profile and isinstance(profile, dict) and profile.get("full_name"):
                        return {
                            "profile": profile,
                            "filename": row.get("resume_filename", "Resume.pdf")
                        }
            except Exception as e:
                print(f"[Supabase] Error fetching user profile: {e}")

        # 2. Fallback to local cache
        cache_file = cls._get_local_user_cache_path(clean_email)
        if cache_file.exists():
            import json
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data.get("profile"):
                        return {
                            "profile": cached_data["profile"],
                            "filename": cached_data.get("filename", "Resume.pdf")
                        }
            except Exception:
                pass

        return None

    @classmethod
    def save_user_notifications(cls, email: str, notif_dict: Dict[str, Any]) -> bool:
        if not email:
            return False
        clean_email = email.strip().lower()
        client = cls.get_client()

        # Cache locally
        try:
            cache_file = cls._get_local_user_cache_path(clean_email)
            cached_data = {}
            if cache_file.exists():
                import json
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                except Exception:
                    pass
            cached_data["notifications"] = notif_dict
            with open(cache_file, "w", encoding="utf-8") as f:
                import json
                json.dump(cached_data, f, indent=2)
        except Exception:
            pass

        if client:
            try:
                payload = {
                    "email": clean_email,
                    "notification_settings": notif_dict,
                    "updated_at": "now()"
                }
                client.table("profiles").upsert(payload, on_conflict="email").execute()
                return True
            except Exception as e:
                print(f"[Supabase] Error saving notifications: {e}")
        return True

    @classmethod
    def get_user_notifications(cls, email: str) -> Optional[Dict[str, Any]]:
        if not email:
            return None
        clean_email = email.strip().lower()
        client = cls.get_client()

        if client:
            try:
                res = client.table("profiles").select("notification_settings").eq("email", clean_email).limit(1).execute()
                if res.data and len(res.data) > 0:
                    ns = res.data[0].get("notification_settings")
                    if ns and isinstance(ns, dict):
                        return ns
            except Exception:
                pass

        cache_file = cls._get_local_user_cache_path(clean_email)
        if cache_file.exists():
            import json
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("notifications")
            except Exception:
                pass
        return None

    @classmethod
    def save_user_memory_bank(cls, email: str, bank_list: List[Dict[str, Any]]) -> bool:
        if not email:
            return False
        clean_email = email.strip().lower()
        client = cls.get_client()

        try:
            cache_file = cls._get_local_user_cache_path(clean_email)
            cached_data = {}
            if cache_file.exists():
                import json
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                except Exception:
                    pass
            cached_data["memory_bank"] = bank_list
            with open(cache_file, "w", encoding="utf-8") as f:
                import json
                json.dump(cached_data, f, indent=2)
        except Exception:
            pass

        if client:
            try:
                payload = {
                    "email": clean_email,
                    "memory_bank": bank_list,
                    "updated_at": "now()"
                }
                client.table("profiles").upsert(payload, on_conflict="email").execute()
                return True
            except Exception as e:
                print(f"[Supabase] Error saving memory bank: {e}")
        return True

    @classmethod
    def get_user_memory_bank(cls, email: str) -> Optional[List[Dict[str, Any]]]:
        if not email:
            return None
        clean_email = email.strip().lower()
        client = cls.get_client()

        if client:
            try:
                res = client.table("profiles").select("memory_bank").eq("email", clean_email).limit(1).execute()
                if res.data and len(res.data) > 0:
                    mb = res.data[0].get("memory_bank")
                    if mb and isinstance(mb, list) and len(mb) > 0:
                        return mb
            except Exception:
                pass

        cache_file = cls._get_local_user_cache_path(clean_email)
        if cache_file.exists():
            import json
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("memory_bank")
            except Exception:
                pass
        return None

    @classmethod
    def save_user_quick_profile(cls, email: str, quick_profile: Dict[str, Any]) -> bool:
        if not email:
            return False
        clean_email = email.strip().lower()
        client = cls.get_client()

        try:
            cache_file = cls._get_local_user_cache_path(clean_email)
            cached_data = {}
            if cache_file.exists():
                import json
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                except Exception:
                    pass
            cached_data["candidate_quick_profile"] = quick_profile
            with open(cache_file, "w", encoding="utf-8") as f:
                import json
                json.dump(cached_data, f, indent=2)
        except Exception:
            pass

        if client:
            try:
                payload = {
                    "email": clean_email,
                    "candidate_quick_profile": quick_profile,
                    "updated_at": "now()"
                }
                client.table("profiles").upsert(payload, on_conflict="email").execute()
                return True
            except Exception as e:
                print(f"[Supabase] Error saving quick profile: {e}")
        return True

    @classmethod
    def get_user_quick_profile(cls, email: str) -> Optional[Dict[str, Any]]:
        if not email:
            return None
        clean_email = email.strip().lower()
        client = cls.get_client()

        if client:
            try:
                res = client.table("profiles").select("candidate_quick_profile").eq("email", clean_email).limit(1).execute()
                if res.data and len(res.data) > 0:
                    qp = res.data[0].get("candidate_quick_profile")
                    if qp and isinstance(qp, dict):
                        return qp
            except Exception:
                pass

        cache_file = cls._get_local_user_cache_path(clean_email)
        if cache_file.exists():
            import json
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("candidate_quick_profile")
            except Exception:
                pass
        return None

    @classmethod
    def sync_all_user_data(cls, email: str) -> Dict[str, Any]:
        """
        Gathers all user-specific data (profile, notifications, memory bank, quick profile)
        to restore a complete user session across devices instantly.
        """
        clean_email = (email or "").strip().lower()
        if not clean_email:
            return {}

        tier = cls.get_user_tier(clean_email)
        profile_bundle = cls.get_user_profile(clean_email)
        notifications = cls.get_user_notifications(clean_email)
        memory_bank = cls.get_user_memory_bank(clean_email)
        quick_profile = cls.get_user_quick_profile(clean_email)

        return {
            "email": clean_email,
            "tier": tier,
            "is_owner": clean_email == cls.OWNER_EMAIL,
            "profile": profile_bundle.get("profile") if profile_bundle else None,
            "resume_filename": profile_bundle.get("filename") if profile_bundle else None,
            "notifications": notifications,
            "memory_bank": memory_bank,
            "candidate_quick_profile": quick_profile
        }


# Class alias for cross-compatibility
class SupabaseManager(SupabaseAdapter):
    pass
