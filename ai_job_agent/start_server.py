"""
JobFlow AI & ResLink Studio - Resilient Auto-Healing Server Supervisor
Ensures the server runs reliably on http://127.0.0.1:8000 with automatic file-watch reloading,
crash recovery, and zero downtime.
"""
import sys
import time
from pathlib import Path

# UTF-8 Windows terminal support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn


def run_supervisor():
    print("=" * 65)
    print("  [+] JobFlow AI & ResLink Video Studio Server Starting...")
    print("  [+] Local Dashboard:     http://127.0.0.1:8000/app")
    print("  [+] ResLink Studio:      http://127.0.0.1:8000/reslink")
    print("  [+] Candidate Profile:   http://127.0.0.1:8000/p/mudather-mohammed")
    print("=" * 65)

    while True:
        try:
            uvicorn.run(
                "server:app",
                host="0.0.0.0",
                port=8000,
                reload=True,
                reload_dirs=[str(BASE_DIR / "core"), str(BASE_DIR / "web"), str(BASE_DIR)],
                log_level="info",
                access_log=True,
            )
        except KeyboardInterrupt:
            print("\n[Server Supervisor] Shutting down gracefully on user request.")
            break
        except Exception as e:
            print(f"\n[Server Supervisor] Warning: Server stopped ({e}). Auto-restarting in 2s...")
            time.sleep(2)


if __name__ == "__main__":
    run_supervisor()
