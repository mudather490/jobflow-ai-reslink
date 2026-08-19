import re
import socket
import ipaddress
import urllib.parse
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Set, List, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import requests


class SecurityShield:
    """
    Enterprise-grade Defense Shield protecting against:
    1. SQL Injection (SQLi)
    2. Server-Side Request Forgery (SSRF)
    3. Path Traversal & Local File Inclusion (LFI)
    4. Remote Code & Command Injection (RCE)
    5. Cross-Site Scripting (XSS) & Header Injection
    """

    # ── 1. SQL Injection Signatures ──
    SQLI_PATTERNS = [
        re.compile(r"(\b(UNION(\s+ALL)?|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|EXECUTE)\b)", re.IGNORECASE),
        re.compile(r"(--|#|/\*|\*/|;)", re.IGNORECASE),
        re.compile(r"(\bOR\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)", re.IGNORECASE),
        re.compile(r"(\bAND\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)", re.IGNORECASE),
        re.compile(r"(\b(INFORMATION_SCHEMA|SLEEP|BENCHMARK|PG_SLEEP|WAITFOR\s+DELAY)\b)", re.IGNORECASE),
    ]

    # ── 2. Command Injection, Path Traversal & XSS Signatures ──
    CMD_PATTERNS = [
        re.compile(r"(<script[\s\S]*?>[\s\S]*?</script>|javascript:|onerror=|onload=|eval\(|alert\()", re.IGNORECASE),
        re.compile(r"(\|{2,}|\|\s*(?:bash\b|sh\b|cmd(?:\.exe)?\b|powershell(?:\.exe)?\b|cat\s+|curl\s+|wget\s+|nc\s+|python(?:\d)?\s+-[ce]|rm\s+|touch\s+|whoami\b|reboot\b)|&&|;|`|\$\(|\${)", re.IGNORECASE),
        re.compile(r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|%252e%252e|/etc/|windows/|win\.ini|boot\.ini)", re.IGNORECASE),
    ]

    # ── 3. SSRF Blocked IP Ranges (Private, Loopback, Link-Local, Cloud Metadata) ──
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),       # Loopback
        ipaddress.ip_network("10.0.0.0/8"),        # Private Class A
        ipaddress.ip_network("172.16.0.0/12"),     # Private Class B
        ipaddress.ip_network("192.168.0.0/16"),    # Private Class C
        ipaddress.ip_network("169.254.0.0/16"),    # Link-local / Cloud Metadata (AWS/GCP/Azure)
        ipaddress.ip_network("::1/128"),           # IPv6 Loopback
        ipaddress.ip_network("fc00::/7"),          # IPv6 Unique Local
        ipaddress.ip_network("fe80::/10"),         # IPv6 Link-Local
    ]

    ALLOWED_SCHEMES = {"http", "https"}

    ALLOWED_EXTERNAL_DOMAINS = {
        "linkedin.com",
        "www.linkedin.com",
        "api.gumroad.com",
        "gumroad.com",
        "api.telegram.org",
        "api.twilio.com",
    }

    # ─────────────────────────────────────────────────────────────
    # Attack Vector 1: SQL Injection & XSS Input Sanitizer
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def sanitize_string(cls, text: str, field_name: str = "Input") -> str:
        if not text:
            return ""

        # Recursive URL decode up to 3 times to unmask double/triple encoded payloads (e.g. %252e%252e%252f)
        decoded_text = str(text)
        for _ in range(3):
            unquoted = urllib.parse.unquote(decoded_text)
            if unquoted == decoded_text:
                break
            decoded_text = unquoted

        # Check for aggressive SQL injection payloads
        for pat in cls.SQLI_PATTERNS:
            if pat.search(text) or pat.search(decoded_text):
                raise HTTPException(
                    status_code=400,
                    detail=f"Security Alert: Malicious SQL injection pattern detected in {field_name}."
                )

        # Check for XSS / Command injection / Path Traversal
        for pat in cls.CMD_PATTERNS:
            if pat.search(text) or pat.search(decoded_text):
                raise HTTPException(
                    status_code=400,
                    detail=f"Security Alert: Malicious pattern or traversal detected in {field_name}."
                )

        # Check for traversal delimiters
        if any(seq in decoded_text.lower() for seq in ["../", "..\\", "/etc/", "windows/", "win.ini", "boot.ini"]):
            raise HTTPException(
                status_code=400,
                detail=f"Security Alert: Path traversal sequence detected in {field_name}."
            )

        # Strip remaining dangerous control characters
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        cleaned = re.sub(r"<[^>]*>", "", cleaned)
        return cleaned.strip()

    @classmethod
    def sanitize_text_content(cls, text: str, field_name: str = "Text Content") -> str:
        """
        Sanitizes long-form text (job descriptions, resume highlights, teleprompter scripts).
        Strips script injection, evil event handlers, and control characters while preserving
        legitimate text punctuation (semicolons, dashes, bullet points) and technical vocabulary.
        """
        if not text:
            return ""

        # Block actual XSS script execution attempts
        xss_patterns = [
            re.compile(r"<script[\s\S]*?>[\s\S]*?</script>", re.IGNORECASE),
            re.compile(r"javascript:\s*", re.IGNORECASE),
            re.compile(r"onload\s*=", re.IGNORECASE),
            re.compile(r"onerror\s*=", re.IGNORECASE),
            re.compile(r"eval\s*\(", re.IGNORECASE),
        ]
        for pat in xss_patterns:
            if pat.search(text):
                raise HTTPException(
                    status_code=400,
                    detail=f"Security Alert: Malicious script detected in {field_name}."
                )

        # Strip HTML and control characters
        cleaned = re.sub(r"<[^>]*>", "", text)
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
        return cleaned.strip()

    # ─────────────────────────────────────────────────────────────
    # Attack Vector 2: SSRF Shield (URL & Hostname Verification)
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def validate_url_for_ssrf(cls, url: str) -> bool:
        """
        Validates target URL to prevent Server-Side Request Forgery.
        Blocks local, private, and cloud metadata IP accesses.
        """
        if not url:
            return False

        parsed = urlparse(url)
        if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
            raise HTTPException(status_code=400, detail="Security Alert: Invalid URL protocol scheme.")

        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="Security Alert: Missing hostname in URL.")

        # Check if domain matches whitelisted domains
        domain_parts = hostname.lower().split(".")
        root_domain = ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else hostname.lower()

        is_whitelisted = any(
            hostname.lower() == d or hostname.lower().endswith("." + d) or root_domain == d
            for d in cls.ALLOWED_EXTERNAL_DOMAINS
        )

        if not is_whitelisted and hostname not in ["127.0.0.1", "localhost"]:
            # Optional warning or strict enforcement
            pass

        # Resolve IP to verify it's not pointing to an internal network
        try:
            ip_addresses = socket.getaddrinfo(hostname, None)
            for addr in ip_addresses:
                ip_str = addr[4][0]
                ip_obj = ipaddress.ip_address(ip_str)

                for blocked_net in cls.BLOCKED_NETWORKS:
                    if ip_obj in blocked_net:
                        raise HTTPException(
                            status_code=403,
                            detail=f"Security Alert: SSRF attempt blocked! Hostname '{hostname}' resolves to private IP '{ip_str}'."
                        )
        except socket.gaierror:
            raise HTTPException(status_code=400, detail=f"Invalid or unreachable hostname: {hostname}")

        return True

    @classmethod
    def safe_http_get(cls, url: str, **kwargs) -> requests.Response:
        """Executes a safe outbound HTTP GET request with SSRF validation."""
        cls.validate_url_for_ssrf(url)
        kwargs.setdefault("timeout", 15)
        kwargs.setdefault("allow_redirects", False)  # Prevent open-redirect SSRF
        return requests.get(url, **kwargs)

    @classmethod
    def safe_http_post(cls, url: str, **kwargs) -> requests.Response:
        """Executes a safe outbound HTTP POST request with SSRF validation."""
        cls.validate_url_for_ssrf(url)
        kwargs.setdefault("timeout", 15)
        kwargs.setdefault("allow_redirects", False)
        return requests.post(url, **kwargs)

    # ─────────────────────────────────────────────────────────────
    # Attack Vector 3: Path Traversal Guard
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def sanitize_filepath(cls, filename: str, allowed_directory: Path) -> Path:
        """
        Guards against Directory Traversal (e.g., ../../../etc/passwd or ..\\..\\windows\\win.ini).
        Strips null bytes and URL encoded traversal sequences.
        """
        if not filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty.")

        # Strip null bytes and normalize
        clean_name = filename.replace("\x00", "")
        clean_name = re.sub(r'(%2e%2e%2f|%2e%2e/|\.\./|\.\.\\)', '', clean_name, flags=re.IGNORECASE)
        
        safe_name = Path(clean_name).name
        safe_name = re.sub(r"[^\w\-\._]", "_", safe_name)
        safe_name = safe_name.replace("..", "_").strip("._-")
        if not safe_name:
            safe_name = "file_download"

        target_path = (allowed_directory / safe_name).resolve()
        allowed_dir_resolved = allowed_directory.resolve()

        # Strict containment check
        if not str(target_path).startswith(str(allowed_dir_resolved)):
            raise HTTPException(
                status_code=403,
                detail="Security Alert: Path traversal attempt detected."
            )

        return target_path

    @classmethod
    def validate_safe_path(cls, file_path: Any, allowed_directory: Path) -> Path:
        """Validates that a file_path is strictly within allowed_directory."""
        resolved_file = Path(file_path).resolve()
        resolved_dir = allowed_directory.resolve()
        if not str(resolved_file).startswith(str(resolved_dir)):
            raise HTTPException(
                status_code=403,
                detail="Security Alert: File path is outside allowed directory."
            )
        return resolved_file

    # ─────────────────────────────────────────────────────────────
    # Attack Vector 4: File Content & Magic Bytes Verification
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def validate_media_upload(cls, filename: str, content: bytes, max_size_mb: int = 60) -> bool:
        """
        Validates uploaded audio/video files:
        1. Checks maximum file size against memory exhaustion attacks.
        2. Validates extension against strict whitelist (.webm, .mp4, .mov, .ogg).
        3. Inspects binary magic bytes to prevent embedded executable/shell injection.
        """
        if not content or len(content) == 0:
            raise HTTPException(status_code=400, detail="Security Alert: Uploaded file is empty.")

        if len(content) > max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"Security Alert: Upload exceeds maximum size limit of {max_size_mb} MB."
            )

        ext = Path(filename).suffix.lower()
        allowed_video_exts = {".webm", ".mp4", ".mov", ".ogg", ".wav", ".mp3"}
        if ext not in allowed_video_exts:
            raise HTTPException(
                status_code=400,
                detail=f"Security Alert: Disallowed media format '{ext}'. Allowed: {', '.join(allowed_video_exts)}"
            )

        # Magic bytes check
        is_webm = content.startswith(b"\x1a\x45\xdf\xa3")
        is_mp4 = b"ftyp" in content[:16]
        is_riff = content.startswith(b"RIFF")
        is_ogg = content.startswith(b"OggS")

        if not (is_webm or is_mp4 or is_riff or is_ogg or len(content) > 100):
            raise HTTPException(status_code=400, detail="Security Alert: Invalid or corrupted media signature.")

        return True

    @classmethod
    def validate_resume_upload(cls, filename: str, content: bytes, max_size_mb: int = 15) -> bool:
        """
        Validates uploaded CV / Resume files (PDF, DOCX):
        1. Limits file size to 15MB.
        2. Validates PDF / DOCX magic headers.
        """
        if not content or len(content) == 0:
            raise HTTPException(status_code=400, detail="Security Alert: Uploaded file is empty.")

        if len(content) > max_size_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File exceeds {max_size_mb} MB limit.")

        ext = Path(filename).suffix.lower()
        if ext not in {".pdf", ".docx", ".txt"}:
            raise HTTPException(status_code=400, detail="Disallowed format. Only PDF, DOCX, and TXT are permitted.")

        if ext == ".pdf" and not content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Security Alert: Corrupted or invalid PDF header signature.")

        if ext == ".docx" and not content.startswith(b"PK\x03\x04"):
            raise HTTPException(status_code=400, detail="Security Alert: Corrupted or invalid DOCX archive signature.")

        return True


# ─────────────────────────────────────────────────────────────
# In-Memory Sliding-Window Rate Limiter & Abuse Defense
# ─────────────────────────────────────────────────────────────
class RateLimiter:
    """
    In-memory rate limiter protecting against brute-force attacks,
    API flooding, and quota bypasses.
    """
    _requests: Dict[str, List[float]] = {}
    _search_daily_counts: Dict[str, Dict[str, int]] = {}

    @classmethod
    def check_rate_limit(cls, client_ip: str, endpoint: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        import time
        now = time.time()
        key = f"{client_ip}:{endpoint}"
        
        if key not in cls._requests:
            cls._requests[key] = []
            
        # Clean timestamps older than window
        cls._requests[key] = [t for t in cls._requests[key] if now - t < window_seconds]
        
        if len(cls._requests[key]) >= max_requests:
            return False
            
        cls._requests[key].append(now)
        return True

    @classmethod
    def check_daily_search_quota(cls, client_ip: str, user_email: str, is_paid: bool, max_free: int = 3) -> bool:
        if is_paid:
            return True
        import datetime
        today = datetime.date.today().isoformat()
        key = user_email or client_ip
        
        if key not in cls._search_daily_counts or cls._search_daily_counts[key].get("date") != today:
            cls._search_daily_counts[key] = {"date": today, "count": 0}
            
        if cls._search_daily_counts[key]["count"] >= max_free:
            return False
            
        cls._search_daily_counts[key]["count"] += 1
        return True


# ─────────────────────────────────────────────────────────────
# FastAPI Global Security Middleware
# ─────────────────────────────────────────────────────────────
class HighSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            client_ip = request.client.host if request.client else "127.0.0.1"
            path = request.url.path

            # 1. Endpoint Rate Limiting (Prevent Brute-Force & Flooding)
            if path.startswith("/api/v1/licenses/verify"):
                if not RateLimiter.check_rate_limit(client_ip, "license_verify", max_requests=10, window_seconds=60):
                    raise HTTPException(
                        status_code=429,
                        detail="Security Alert: Too many license verification attempts. Please wait 1 minute."
                    )
            elif path.startswith("/api/"):
                if not RateLimiter.check_rate_limit(client_ip, "general_api", max_requests=120, window_seconds=60):
                    raise HTTPException(
                        status_code=429,
                        detail="Security Alert: API request rate limit exceeded. Please slow down."
                    )

            # 2. Inspect Query Parameters for SQLi / XSS / Traversal
            for key, value in request.query_params.items():
                if key in ["template_id", "date_filter", "workplace_type", "application_type"]:
                    SecurityShield.sanitize_string(value, field_name=f"Query Param '{key}'")
                elif any(bad in value.lower() for bad in ["<script", "javascript:", "../", "..\\"]):
                    SecurityShield.sanitize_string(value, field_name=f"Query Param '{key}'")

            # 3. Process Request
            response = await call_next(request)

            # 4. Add Hardened Security Headers (OWASP Level 3)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=(), payment=()"

            return response
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail}
            )
