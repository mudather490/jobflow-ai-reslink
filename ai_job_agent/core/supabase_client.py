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
