import sys
from pathlib import Path

# Add project root and ai_job_agent directory to sys.path for Vercel serverless environment
ROOT_DIR = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT_DIR / "ai_job_agent"

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from server import app

# Export FastAPI instance for Vercel Serverless Functions
handler = app
