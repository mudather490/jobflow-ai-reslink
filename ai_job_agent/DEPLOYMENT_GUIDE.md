# 🚀 JobFlow.ai — Complete Production Deployment & SaaS Launch Guide

This guide walks you step-by-step through setting up **Supabase** for your database, **Gumroad** for worldwide subscription payments via PayPal, and **Vercel** for 1-click global cloud deployment.

---

## 📋 Architecture Checklist

| Component | Service | Role | Free Tier Available? |
| :--- | :--- | :--- | :--- |
| **Frontend & Landing Page** | Vercel Edge CDN | Serves Marketing Landing Page (`/`) & Workspace App (`/app`) | ✅ Yes |
| **Backend & APIs** | FastAPI on Vercel Serverless | Scraping, ATS Gap Matching, XYZ Tailoring & Webhooks | ✅ Yes |
| **Database & Auth** | Supabase (PostgreSQL) | Stores User Profiles, Resumes, Applications & RLS | ✅ Yes |
| **Payment & Subscriptions** | Gumroad (Global MoR) | Accepts PayPal & Cards from 190+ countries | ✅ Yes (0 upfront fees) |

---

## Step 1: Set Up Supabase Database (5 Minutes)

1. Go to [supabase.com](https://supabase.com) and create a **Free Account**.
2. Click **"New Project"**, name it `jobflow-ai`, and set a database password.
3. Once the dashboard opens, navigate to the **SQL Editor** tab in the left sidebar.
4. Open the file [`supabase/schema.sql`](file:///c:/Users/MudaX/Documents/antigravity/quirky-pascal/ai_job_agent/supabase/schema.sql) from this project, copy its entire contents, paste it into the Supabase SQL Editor, and click **RUN**.
5. Go to **Project Settings -> API** and copy:
   - **Project URL** (e.g. `https://xyzcompany.supabase.co`)
   - **anon / public key** (e.g. `eyJhbGciOi...`)

---

## Step 2: Set Up Gumroad Global Subscriptions (5 Minutes)

1. Go to [gumroad.com](https://gumroad.com) and sign up (takes 1 minute).
2. Connect your **PayPal account** or bank details under **Settings -> Payouts** so Gumroad can send you your revenue.
3. Click **Products -> New Product**:
   - **Type:** *Subscription* or *Digital Product*
   - **Name:** `JobFlow.ai Pro Membership`
   - **Price:** `$19 / month`
4. Enable **"Generate a unique license key for each sale"** under the product settings.
5. Copy your **Product URL** (e.g. `https://gumroad.com/l/jobflow-pro`) and paste it into the **"Subscribe via Gumroad"** buttons in `web/landing.html` and `web/index.html`.
6. Go to **Settings -> Advanced -> Ping (Webhooks)** and set:
   - **URL:** `https://your-app-name.vercel.app/api/v1/webhooks/gumroad`
   - Whenever anyone purchases, Gumroad will automatically upgrade their account in Supabase in real time!

---

## Step 3: Deploy to Vercel (3 Minutes)

### Option A: Via GitHub (Recommended)
1. Push this project folder to your GitHub account:
   ```bash
   git init
   git add .
   git commit -m "Launch JobFlow.ai SaaS"
   git branch -M main
   git remote add origin https://github.com/yourusername/jobflow-ai.git
   git push -u origin main
   ```
2. Go to [vercel.com](https://vercel.com) and click **"Add New Project"**.
3. Select your `jobflow-ai` repository.
4. Add the following **Environment Variables** in the Vercel dashboard:
   - `SUPABASE_URL`: `https://your-project.supabase.co`
   - `SUPABASE_KEY`: `your-anon-key`
   - `GUMROAD_PRODUCT_PERMALINK`: `jobflow-pro`
5. Click **"Deploy"**! Vercel will build and launch your live application with a global `*.vercel.app` URL and free SSL certificate.

### Option B: Via Vercel CLI
```bash
npx vercel
```
Follow the interactive prompts to deploy directly from your local terminal.

---

## 🌐 Live URLs Once Deployed:
- **Landing Page:** `https://your-domain.vercel.app/`
- **Application Dashboard:** `https://your-domain.vercel.app/app`
- **API Documentation:** `https://your-domain.vercel.app/docs`
- **Gumroad Webhook:** `https://your-domain.vercel.app/api/v1/webhooks/gumroad`
