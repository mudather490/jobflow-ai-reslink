---
name: saas-monetization-engine
description: Comprehensive framework for building, launching, and scaling AI-powered SaaS applications for passive income using Gumroad & global Merchant-of-Record payment gateways. Covers subscription billing, license key verification, credits systems, JWT authentication, and automated background jobs.
---

# SaaS Monetization & Passive Income Engineering Framework (Gumroad Edition)

This skill guides the design and deployment of scalable, profitable AI SaaS products with global payout support (PayPal and direct bank transfer in 190+ countries via Gumroad / Merchant-of-Record).

## 1. Monetization Tiers & Pricing Psychology

### Tier 1: Free Tier (Lead Magnet)
- 3 Job Searches per day
- Basic ATS Match Score preview
- Watermarked PDF download

### Tier 2: Pro Tier ($19 / month or $190 / year via Gumroad)
- Unlimited Searches & Full ATS Gap Breakdown
- Dynamic DOCX & ATS PDF Tailoring (XYZ formula)
- Interactive AI Gap Questioning session
- Up to 15 Tailored Resumes / month

### Tier 3: Autonomous Career Pilot ($49 / month or $490 / year via Gumroad)
- 24/7 Automated Background Job Radar (hourly scans)
- Autonomous Auto-Apply (with manual review checkpoints)
- Triple-Channel Real-Time Notifications (Email, WhatsApp, Telegram)
- Priority Support & Unlimited Resume Generations

## 2. Technical SaaS Stack

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend:       Next.js 14+ / React (Tailwind, Lucide UI)   │
│ Backend API:    FastAPI / Python (Async endpoints)          │
│ Database:       PostgreSQL / SQLite + SQLAlchemy            │
│ Global Billing: Gumroad Subscriptions & License Verification│
│ Auth:           JWT Tokens / OAuth2                         │
│ Worker / Cron:  APScheduler / Celery + Redis                │
│ Notifications:  SMTP, Twilio WhatsApp, Telegram Bot API    │
└─────────────────────────────────────────────────────────────┘
```

## 3. Gumroad Integration Architecture

### A. License Key Verification Endpoint (`/api/v1/licenses/verify`):
Users who purchase on Gumroad receive a License Key. The backend verifies it against the Gumroad API:
```python
import requests

def verify_gumroad_license(product_permalink: str, license_key: str) -> dict:
    url = "https://api.gumroad.com/v2/licenses/verify"
    payload = {
        "product_permalink": product_permalink,
        "license_key": license_key,
        "increment_uses_count": "false"
    }
    response = requests.post(url, data=payload)
    data = response.json()
    return {
        "success": data.get("success", False),
        "uses": data.get("uses", 0),
        "subscription_cancelled": data.get("purchase", {}).get("subscription_cancelled_at") is not None,
        "custom_fields": data.get("purchase", {}).get("custom_fields", {})
    }
```

### B. Gumroad Webhook Handler (`/api/v1/webhooks/gumroad`):
- **Event `sale` / `subscription_restart`:** Activates or renews user subscription tier, resets monthly credits, and enables background job radar.
- **Event `subscription_cancelled` / `refund` / `chargebacked`:** Downgrades user safely to the Free tier and pauses automated auto-apply workers.
