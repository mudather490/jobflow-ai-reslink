import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 1. Email Notification Settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")  # App password for Gmail
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

# 2. WhatsApp Notification Settings
WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "")  # e.g., +1234567890
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# 3. Telegram Notification Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# LinkedIn Scraper Settings
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

def get_linkedin_time_filter(time_input: str) -> str:
    cleaned = str(time_input).strip().lower()
    if cleaned in ["24h", "1d", "past_24h", "24 hours", "1 day"]:
        return "r86400"
    elif cleaned in ["7d", "1w", "past_week", "7 days", "1 week"]:
        return "r604800"
    elif cleaned in ["14d", "2w", "14 days", "2 weeks"]:
        return "r1209600"
    elif cleaned in ["30d", "1m", "past_month", "30 days", "1 month"]:
        return "r2592000"
    elif cleaned in ["70d", "70 days"]:
        return "r6048000"
    elif cleaned in ["all", "any", "anytime"]:
        return ""
    
    digits = "".join(filter(str.isdigit, cleaned))
    if digits:
        days = int(digits)
        return f"r{days * 86400}"
    
    return "r86400"

def get_linkedin_workplace_filter(workplace_input: str) -> str:
    """
    Maps user-facing workplace preferences to LinkedIn's native f_WT parameter:
    - 'worldwide_remote', 'contract_remote', 'remote' -> '2' (Strictly Remote / Work from Home)
    - 'hybrid', 'hybrid_remote' -> '3' (Hybrid)
    - 'on_site' / 'onsite' / 'in_office' -> '1' (On-site / In-Office)
    - 'all' / 'any' -> '' (No restriction)
    """
    cleaned = str(workplace_input).strip().lower()
    if cleaned in ["worldwide_remote", "contract_remote", "internship", "intern", "fellowship", "remote", "2", "work from home", "wfh"]:
        return "2"
    elif cleaned in ["hybrid", "hybrid_remote", "3", "hyper"]:
        return "3"
    elif cleaned in ["on_site", "onsite", "in_office", "1", "inside_company", "office", "local"]:
        return "1"
    return ""

MIN_MATCH_THRESHOLD = 60.0

# 4. Supabase & Gumroad SaaS Integration Settings
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
GUMROAD_PRODUCT_PERMALINK = os.getenv("GUMROAD_PRODUCT_PERMALINK", "jobflow-pro")
