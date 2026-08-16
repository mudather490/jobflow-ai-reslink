import sys
from pathlib import Path

# Add root directory to sys.path for Vercel serverless environment
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from server import app

# Export FastAPI instance for Vercel Serverless Functions
handler = app
