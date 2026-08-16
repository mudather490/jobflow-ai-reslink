# JobFlow.ai & ResLink Studio

> **AI-Powered Career Hub, ATS-Optimized Resume Generator & Autonomous Video Pitch Studio**

JobFlow.ai is an autonomous career acceleration engine built with FastAPI, ReportLab, and Supabase. It enables job seekers to parse resumes into structured profiles, tailor applications to job descriptions across 4 ATS-optimized templates, record personalized video pitches with live moving teleprompters, and track recruiter engagement in real time.

---

## 🌟 Key Features

1. **Universal Multi-Format Resume Parser**:
   - Ingests `.pdf`, `.docx`, and `.txt` files across all professional domains.
   - Extracts certifications, grouped skills, practical projects with GitHub links, and career transitions without section loss.

2. **Unified 4-Template Document Engine**:
   - **Modern Executive (`modern`)**: Royal Blue accents, 2-column header, metric badges.
   - **Harvard Consulting (`harvard_consulting`)**: Ivy-League `Times-Roman` serif typography, Oxford Navy accents, and 1.2pt solid divider rules.
   - **Corporate Elite (`corporate_elite`)**: Fortune 500 Deep Navy & Antique Gold accent bars with executive core competencies matrix.
   - **Tech Specialist (`tech_specialist`)**: Electric Violet & Cyan palette, technical skills matrix, and clickable GitHub repository tags.

3. **ResLink 4-Step Video Pitch Studio (`/reslink`)**:
   - **Step 1: Target Profile**: Senior contact personalization & job description matching.
   - **Step 2: Video Studio**: Live camera recording with moving teleprompter synced with the AI script and MP4 upload fallback.
   - **Step 3: CV Template Selector**: Live template selection with instant test download.
   - **Step 4: Share & Analytics**: Personalized LinkedIn outreach note and real-time telemetry (page views, video plays, CV downloads, booking clicks).

4. **Public Recruiter Profile Showcase (`/p/{slug}`)**:
   - Interactive candidate portfolio with video player, subtitle overlay, project repositories, and one-click interview booking via Calendly.

5. **Enterprise Security & Hardening**:
   - 100% shielded against OWASP Top 10 / Burp Suite vectors (Path Traversal, Stored/Reflected XSS, SQLi, Command Injection, ReDoS).
   - High-concurrency multi-user thread safety.

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/YOUR_USERNAME/jobflow-ai-reslink.git
cd jobflow-ai-reslink

# Create virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Run the Local Server
```bash
cd ai_job_agent
python -m uvicorn server:app --reload --port 8000
```
Visit:
- **Main Dashboard**: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
- **ResLink Studio**: [http://127.0.0.1:8000/reslink](http://127.0.0.1:8000/reslink)
- **Sample Recruiter Page**: [http://127.0.0.1:8000/p/mudather-mohammed](http://127.0.0.1:8000/p/mudather-mohammed)

---

## ☁️ Supabase Cloud Setup

1. Create a project on [Supabase](https://supabase.com).
2. Go to **SQL Editor** in your Supabase Dashboard.
3. Open [`ai_job_agent/supabase_schema.sql`](file:///c:/Users/MudaX/Documents/antigravity/quirky-pascal/ai_job_agent/supabase_schema.sql), copy its content, paste it into the editor, and click **Run**.
4. Set your environment variables in `.env`:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   ```
5. Test the connection:
   ```bash
   python ai_job_agent/scripts/setup_supabase.py
   ```

---

## ⚡ Vercel Deployment

This project is pre-configured with `vercel.json` for one-click deployment on Vercel:

1. Push your repository to GitHub.
2. Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **"Add New..." ➔ "Project"**.
3. Import your GitHub repository.
4. Add your Environment Variables (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`).
5. Click **Deploy**.
