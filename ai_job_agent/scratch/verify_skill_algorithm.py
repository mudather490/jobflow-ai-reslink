import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.matcher import JobMatcher
from core.scraper import JobDetails
from core.resume_parser import ResumeParser

def run_verification():
    print("=" * 70)
    print("[+] HIGH-PRECISION SKILL MATCH & ATS SCORE ALGORITHM VERIFICATION")
    print("=" * 70)

    # Candidate Resume
    resume_text = """
    Mudather Mohammed
    Senior AI & Software Engineer | Python & Cloud Architect
    
    Technical Skills:
    Python, FastAPI, PyTorch, Deep Learning, Docker, SQL, LLMs & Generative AI, RAG & Vector Search, AI Agents & Workflows, Git & Version Control
    
    Professional Experience:
    Senior Software Engineer at AI Innovations (3 years)
    - Engineered high-throughput FastAPI REST microservices for LLM model inference.
    - Built RAG vector search pipelines using PyTorch, Qdrant, and Docker containers.
    """

    # Test Job 1: High Match Role (Senior AI Engineer)
    job1 = JobDetails(
        job_id="job_001",
        title="Senior AI Engineer",
        company="AI Vanguard Labs",
        location="Remote",
        posted_date="12h ago",
        job_url="https://linkedin.com/jobs/view/1001",
        description="""
        We are seeking a Senior AI Engineer to design autonomous multi-agent systems and LLM pipelines.
        
        Requirements:
        - Deep proficiency in Python, FastAPI, PyTorch, and Deep Learning.
        - Experience with LLMs & Generative AI, RAG & Vector Search, and AI Agents & Workflows.
        - Knowledge of Docker & Containerization, SQL & Relational Databases, Git & Version Control.
        """,
        is_easy_apply=True
    )

    # Test Job 2: Moderate Match Role (Full Stack Lead)
    job2 = JobDetails(
        job_id="job_002",
        title="Full Stack Lead Engineer",
        company="Global Web Solutions",
        location="Remote",
        posted_date="1d ago",
        job_url="https://linkedin.com/jobs/view/1002",
        description="""
        Seeking a Full Stack Lead Engineer to build web applications.
        
        Requirements:
        - Strong background in React, TypeScript, Node.js, and HTML5 & CSS3.
        - Backend experience with Python, FastAPI, Docker, and Kubernetes.
        """,
        is_easy_apply=True
    )

    matcher = JobMatcher()
    profile = ResumeParser.parse_text_to_profile(resume_text)

    for idx, job in enumerate([job1, job2], 1):
        report = matcher.evaluate_match(profile, job)
        print(f"\n--- [Test Case {idx}: {job.title} at {job.company}] ---")
        print(f"📌 LinkedIn Callout: {report.linkedin_qualification_text}")
        print(f"🏅 Qualification Tier: {report.qualification_tier} (Badge Color: {report.qualification_badge_color})")
        print(f"📊 Exact Skill Match: {report.matched_skills_count} Matched / {report.required_skills_count} Required ({report.skill_match_percentage}%)")
        print(f"✓ Matched Skills ({len(report.matched_skills)}): {', '.join(report.matched_skills)}")
        print(f"✗ Missing Skills ({len(report.missing_critical_skills)}): {', '.join(report.missing_critical_skills) if report.missing_critical_skills else 'None'}")
        print(f"★ Bonus Profile Strengths ({len(report.candidate_extra_skills)}): {', '.join(report.candidate_extra_skills)}")
        print(f"📈 Sub-scores: Skills 60% wt = {report.skill_match_percentage}% | Title 25% wt = {report.title_relevance_score}% | Depth 15% wt = {report.experience_alignment_score}%")
        print(f"⚡ Final Composite ATS Score: {report.overall_ats_score}%")
        print("-" * 70)

if __name__ == "__main__":
    run_verification()
