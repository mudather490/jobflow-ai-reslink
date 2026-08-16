# SaaS & Passive Income Engineering Standards

## 1. Security & Data Isolation
- User resume data and contact information must be strictly scoped to the authenticated `user_id`.
- Never store raw passwords or unencrypted API keys in source code; use `.env` and hashed credentials (bcrypt).

## 2. Monetization & Rate Limiting
- Enforce tier limits before executing heavy operations (e.g. max daily searches, PDF compilations).
- Provide clear upgrade hooks when users hit tier boundaries.

## 3. High-Converting UX
- Clean modern aesthetics, dark mode support, glassmorphism, instant feedback spinners, and clear value metrics (e.g. "ATS Match Score: 94%").
