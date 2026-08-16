import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.resume_parser import UserProfile
from core.scraper import JobDetails
from config import GEMINI_API_KEY, OPENAI_API_KEY


class MatchReport(BaseModel):
    job_title: str
    company: str
    match_score: float = Field(description="Match percentage between 0.0 and 100.0")
    matched_skills: List[str] = Field(default_factory=list)
    missing_critical_skills: List[str] = Field(default_factory=list)
    partial_skills: List[str] = Field(default_factory=list)
    experience_assessment: str = ""
    summary_analysis: str = ""
    actionable_recommendations: List[str] = Field(default_factory=list)
    international_badge: str = "🌐 Worldwide Remote"
    international_friendly_score: int = 95
    eligibility_notes: str = "Hires international remote candidates globally."


class JobMatcher:
    """
    Universal ATS Job Matcher for ANY Profession or Industry.
    Extracts core competencies, tools, frameworks, and domain knowledge from job descriptions
    and matches them against the candidate's resume profile.
    """

    KNOWN_COMPETENCIES = {
        # Tech & AI
        "python", "javascript", "typescript", "golang", "c++", "rust", "java", "c#", "ruby", "scala",
        "fastapi", "flask", "django", "react", "next.js", "vue", "angular", "node.js", "express",
        "docker", "kubernetes", "helm", "terraform", "ansible", "aws", "gcp", "azure", "ci/cd", "github actions",
        "postgresql", "mongodb", "redis", "mysql", "elasticsearch", "neo4j", "sqlite", "cassandra",
        "pytorch", "tensorflow", "scikit-learn", "keras", "transformers", "hugging face", "onnx", "vllm",
        "langchain", "langgraph", "llamaindex", "dspy", "crewai", "autogen", "semantic kernel",
        "qdrant", "pinecone", "milvus", "weaviate", "chroma", "faiss", "pgvector",
        "rag", "graphrag", "vector search", "hybrid search", "fine-tuning", "prompt engineering",
        "rest api", "graphql", "grpc", "microservices", "celery", "kafka", "rabbitmq", "linux", "git",

        # Design & Creative
        "figma", "adobe xd", "photoshop", "illustrator", "indesign", "after effects", "premiere pro",
        "ui/ux design", "wireframing", "prototyping", "user research", "typography", "design systems",
        "3d modeling", "blender", "canva", "motion design",

        # Business, Management & Marketing
        "project management", "product management", "scrum", "agile", "jira", "confluence", "trello",
        "seo", "sem", "google analytics", "hubspot", "salesforce", "content marketing", "copywriting",
        "email marketing", "social media management", "b2b sales", "crm", "lead generation",
        "financial modeling", "accounting", "excel", "powerbi", "tableau", "budgeting", "forecasting",
        "data analysis", "market research", "stakeholder management", "strategic planning", "okrs",

        # General Professional Skills
        "communication", "leadership", "problem solving", "cross-functional collaboration",
        "customer service", "negotiation", "presentation skills", "team leadership", "operations"
    }

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

    def extract_job_requirements(self, job_text: str) -> List[str]:
        """Extracts required competencies and skills for ANY profession."""
        text_lower = job_text.lower()
        found = set()

        # 1. Match against known catalog
        for comp in self.KNOWN_COMPETENCIES:
            pattern = r"(?<!\w)" + re.escape(comp) + r"(?!\w)"
            if re.search(pattern, text_lower):
                found.add(comp.title())

        # 2. Extract dynamic requirement bullet points (e.g. "Proficient in X", "Experience with Y")
        dynamic_patterns = [
            r"(?:experience with|proficient in|knowledge of|familiarity with|expertise in|skilled in|understanding of)\s+([A-Za-z0-9\+\#\.\s,/]+?)(?:\.|\;|\n|\band\b)",
            r"(?:requirements|qualifications|what you bring|skills needed)[\s\S]*?(?:responsibilities|benefits|about us|\Z)"
        ]
        
        for pat in dynamic_patterns[:1]:
            matches = re.finditer(pat, text_lower)
            for m in matches:
                phrase = m.group(1).strip()
                for item in re.split(r"[,/]", phrase):
                    cleaned = item.strip().title()
                    if 2 < len(cleaned) < 30 and (cleaned.lower() in self.KNOWN_COMPETENCIES or len(cleaned.split()) <= 3):
                        found.add(cleaned)

        return sorted(list(found))

    def evaluate_match(self, profile: UserProfile, job: JobDetails) -> MatchReport:
        """
        Runs comprehensive ATS match evaluation between candidate and target role.
        """
        job_reqs = self.extract_job_requirements(job.description)
        if not job_reqs:
            job_reqs = ["Project Management", "Communication", "Problem Solving", "Collaboration"]

        candidate_text = profile.get_full_text().lower()
        candidate_skills_lower = {s.lower() for s in profile.skills}

        matched: List[str] = []
        missing: List[str] = []
        partial: List[str] = []

        for req in job_reqs:
            r_lower = req.lower()
            if r_lower in candidate_skills_lower or re.search(r"(?<!\w)" + re.escape(r_lower) + r"(?!\w)", candidate_text):
                matched.append(req)
            else:
                missing.append(req)

        # Calculate Score
        total_reqs = len(job_reqs)
        score_base = (len(matched) / total_reqs) * 100.0 if total_reqs > 0 else 50.0
        experience_bonus = min(10.0, len(profile.experience) * 2.5)
        final_score = min(100.0, round(score_base + (experience_bonus if score_base < 90 else 0), 1))

        recommendations = []
        if missing:
            recommendations.append(f"Highlight missing requirements: {', '.join(missing[:4])}")
        if not profile.summary:
            recommendations.append("Add a targeted career summary tailored to this position.")
        if len(profile.projects) < 2:
            recommendations.append("Include practical projects or freelance experience demonstrating key competencies.")

        exp_assessment = (
            f"Candidate satisfies {len(matched)} of {total_reqs} detected role requirements. "
            f"Demonstrated background in: {', '.join(matched[:4]) if matched else 'general relevant areas'}."
        )

        return MatchReport(
            job_title=job.title,
            company=job.company,
            match_score=final_score,
            matched_skills=matched,
            missing_critical_skills=missing,
            partial_skills=partial,
            experience_assessment=exp_assessment,
            summary_analysis=f"ATS Match Score: {final_score}%.",
            actionable_recommendations=recommendations,
            international_badge=job.international_badge,
            international_friendly_score=job.international_friendly_score,
            eligibility_notes=job.eligibility_notes,
        )
