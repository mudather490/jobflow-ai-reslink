import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

def check_supabase():
    print("==================================================")
    print("🚀  SUPABASE CLOUD DATABASE CONNECTION TEST")
    print("==================================================")

    if not HAS_SUPABASE:
        print("❌ Supabase Python package is not installed.")
        print("   Run: pip install supabase")
        return False

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key or "your-project" in url:
        print("⚠️  Supabase environment variables not configured in .env:")
        print("   SUPABASE_URL=<your-supabase-url>")
        print("   SUPABASE_ANON_KEY=<your-supabase-anon-key>")
        print("   SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key>")
        print("\n   The app is currently using local JSON persistence.")
        return False

    try:
        supabase = create_client(url, key)
        print(f"✓ Connected successfully to Supabase: {url}")

        # Check tables
        tables = ["profiles", "reslinks", "reslink_analytics", "saved_jobs", "applications", "questionnaire_memory"]
        print("\nChecking database tables:")
        for t in tables:
            try:
                res = supabase.table(t).select("*").limit(1).execute()
                print(f"  ✓ Table '{t}': Operational")
            except Exception as e:
                print(f"  ⚠️ Table '{t}': Not found or permission issue ({e})")
                print(f"     Please run supabase_schema.sql in your Supabase SQL Editor.")

        print("\n==================================================")
        print("SUPABASE CHECK COMPLETE")
        print("==================================================")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

if __name__ == "__main__":
    check_supabase()
