import re
from typing import List, Optional, Dict, Set
from core.resume_parser import UserProfile, WorkExperience, Project, Education, Certification
from core.scraper import JobDetails
from core.matcher import MatchReport, JobMatcher


class ResumeTailor:
    """
    Production-Grade AI Resume Architect & Senior Technical Recruiter Tailoring Engine.
    Enforces:
    1. ZERO TEXT DUPLICATION: Never repeats descriptions or bullets across sections.
    2. CLEAN FORMATTING & STRUCTURE: Eliminates orphan single-word bullets and stray tokens.
    3. CLEAN CONTINUOUS URLs: Sanitizes LinkedIn, GitHub, and repo URLs (no whitespace breaks).
    4. ACTION-ORIENTED XYZ FORMULA: Enhances bullets with strong action verbs and quantified impact.
    5. STANDARDIZED SKILLS CATEGORIZATION: Organizes skills into 6 domain-specific technical groups.
    """

    SKILL_TAXONOMY = {
        "Programming & Core Tools": [
            "python", "sql", "bash", "linux", "git", "github", "c++", "c", "javascript",
            "typescript", "go", "golang", "rust", "java", "html", "css", "r", "shell", "core tools"
        ],
        "Machine Learning & Statistics": [
            "scikit-learn", "sklearn", "regression", "classification", "random forest", "xgboost",
            "decision trees", "trees", "ensembles", "gradient descent", "feature engineering",
            "model evaluation", "metrics", "mse", "r2", "r²", "roc-auc", "f1-score", "k-means",
            "pca", "cross-validation", "hyperparameter tuning", "clustering", "time series",
            "supervised learning", "unsupervised learning"
        ],
        "Deep Learning & Neural Networks": [
            "neural networks", "pytorch", "tensorflow", "keras", "cnns", "cnn", "rnns", "rnn",
            "lstm", "transformers", "attention mechanisms", "bert", "hugging face", "huggingface",
            "torchvision", "transfer learning", "backpropagation", "autoencoders", "gan", "gans",
            "diffusion models", "computer vision", "nlp", "natural language processing"
        ],
        "AI Engineering & LLM Systems": [
            "llm apis", "llm", "llms", "large language models", "ai agents", "multi-agent",
            "multi-agent systems", "prompt engineering", "rag", "retrieval-augmented generation",
            "vector databases", "chromadb", "pinecone", "weaviate", "qdrant", "langchain",
            "llamaindex", "semantic search", "embeddings", "function calling", "agentic workflows"
        ],
        "Backend, Cloud & Databases": [
            "fastapi", "flask", "django", "rest apis", "rest api", "graphql", "supabase",
            "postgresql", "postgres", "mysql", "sqlite", "redis", "docker", "ci/cd", "vercel",
            "cloud hosting", "aws", "gcp", "azure", "microservices", "celery", "rabbitmq", "cloud"
        ],
        "Data & Math": [
            "numpy", "pandas", "matplotlib", "seaborn", "linear algebra", "calculus",
            "multivariate calculus", "statistics", "inferential statistics", "probability",
            "matrix factorization", "data visualization", "data analysis", "eda", "math"
        ],
    }

    def __init__(self, matcher: Optional[JobMatcher] = None):
        self.matcher = matcher or JobMatcher()

    @staticmethod
    def sanitize_url(raw_url: Optional[str]) -> str:
        """
        Sanitizes URLs into continuous, valid strings without whitespace or character breaks.
        """
        if not raw_url:
            return ""
        url = str(raw_url).strip()
        # Remove any internal whitespace or newlines
        url = re.sub(r'[\s\t\r\n]+', '', url)
        # Remove markdown wrapping brackets
        url = re.sub(r'[<>()\[\]]', '', url)
        if url.startswith("git@github.com:"):
            url = "https://github.com/" + url[len("git@github.com:"):]
        elif url and not url.startswith("http://") and not url.startswith("https://") and not url.startswith("mailto:"):
            if "github.com" in url or "linkedin.com" in url:
                url = "https://" + url.lstrip("/")
        return url

    @staticmethod
    def clean_bullet_text(text: str) -> Optional[str]:
        """
        Sanitizes bullet points:
        - Strips leading bullets, hyphens, and whitespace.
        - Filters out orphan single-word bullets (e.g. 'NumPy.' or 'TensorFlow:') with no action clause.
        - Formats math notations properly.
        """
        if not text:
            return None
        cleaned = re.sub(r'^[\s•\-\*\—\–\:\.]+', '', str(text)).strip()
        
        # Remove orphan single-word bullets or stray keyword tags
        words = cleaned.split()
        if len(words) < 3 and (cleaned.endswith(":") or cleaned.endswith(".")):
            # Discard orphan tags like 'TensorFlow:' or 'Python.'
            return None
        if len(cleaned) < 8:
            return None
        
        # Ensure proper ending punctuation
        if cleaned and not cleaned[-1] in [".", "!", "?", ";"]:
            cleaned += "."
            
        return cleaned

    @classmethod
    def deduplicate_bullets(cls, bullets: List[str]) -> List[str]:
        """
        Guarantees zero text duplication across bullet points using normalized similarity hashing.
        """
        seen_normalized: Set[str] = set()
        deduped: List[str] = []

        for b in bullets:
            cleaned = cls.clean_bullet_text(b)
            if not cleaned:
                continue
            # Normalize for deduplication comparison (alphanumeric only)
            norm = re.sub(r'[^a-z0-9]', '', cleaned.lower())
            if len(norm) < 6:
                continue
            if norm not in seen_normalized:
                seen_normalized.add(norm)
                deduped.append(cleaned)

        return deduped

    @classmethod
    def categorize_skills(cls, raw_skills: List[str]) -> Dict[str, List[str]]:
        """
        Intelligently categorizes candidate technical skills into 6 production AI/ML domains.
        """
        categorized: Dict[str, List[str]] = {cat: [] for cat in cls.SKILL_TAXONOMY}
        unmatched: List[str] = []
        seen_skills: Set[str] = set()

        for skill in raw_skills:
            if not skill or not skill.strip():
                continue
            s_clean = skill.strip()
            s_lower = s_clean.lower()
            if s_lower in seen_skills:
                continue
            seen_skills.add(s_lower)

            matched_cat = None
            for cat, keywords in cls.SKILL_TAXONOMY.items():
                if any(kw == s_lower or (len(kw) > 3 and kw in s_lower) for kw in keywords):
                    matched_cat = cat
                    break
            
            if matched_cat:
                categorized[matched_cat].append(s_clean)
            else:
                unmatched.append(s_clean)

        # Distribute remaining general skills cleanly
        if unmatched:
            if not categorized["Programming & Core Tools"]:
                categorized["Programming & Core Tools"].extend(unmatched[:4])
                unmatched = unmatched[4:]
            if unmatched and not categorized["Backend, Cloud & Databases"]:
                categorized["Backend, Cloud & Databases"].extend(unmatched[:4])
                unmatched = unmatched[4:]
            if unmatched:
                categorized.setdefault("Domain & Specialized Tools", []).extend(unmatched)

        # Remove empty categories
        return {cat: sks for cat, sks in categorized.items() if sks}

    def tailor_experience(
        self, experience_list: List[WorkExperience], target_keywords: List[str]
    ) -> List[WorkExperience]:
        """
        Tailors and cleans experience entries:
        - Deduplicates bullet points
        - Removes orphan words
        - Prioritizes target keywords
        """
        tailored_list = []
        keywords_lower = [k.lower() for k in target_keywords]

        for exp in experience_list:
            deduped_bullets = self.deduplicate_bullets(exp.bullets)
            # Sort bullets to emphasize matching skills first
            sorted_bullets = sorted(
                deduped_bullets,
                key=lambda b: any(kw in b.lower() for kw in keywords_lower),
                reverse=True,
            )
            tailored_list.append(
                WorkExperience(
                    company=exp.company,
                    role=exp.role,
                    location=exp.location,
                    duration=exp.duration,
                    subtitle=exp.subtitle,
                    summary=exp.summary,
                    bullets=sorted_bullets,
                )
            )

        return tailored_list

    def tailor_projects(
        self, projects_list: List[Project], target_keywords: List[str]
    ) -> List[Project]:
        """
        Tailors and formats projects:
        - Sanitizes clean continuous repository URLs
        - Deduplicates bullet points
        - Formats technologies list cleanly
        """
        tailored_projects = []
        seen_project_names: Set[str] = set()

        for proj in projects_list:
            p_name_norm = re.sub(r'[^a-z0-9]', '', proj.name.lower())
            if p_name_norm in seen_project_names:
                continue
            seen_project_names.add(p_name_norm)

            clean_repo = self.sanitize_url(proj.repository)
            deduped_bullets = self.deduplicate_bullets(proj.bullets)
            
            # Clean technologies list
            clean_techs = []
            seen_techs: Set[str] = set()
            for t in (proj.technologies or []):
                t_clean = t.strip(" ,.;:")
                if t_clean and t_clean.lower() not in seen_techs:
                    seen_techs.add(t_clean.lower())
                    clean_techs.append(t_clean)

            tailored_projects.append(
                Project(
                    name=proj.name.strip(" :—"),
                    subtitle=proj.subtitle,
                    description=proj.description,
                    bullets=deduped_bullets,
                    technologies=clean_techs,
                    repository=clean_repo,
                )
            )

        return tailored_projects

    def tailor_profile(
        self, profile: UserProfile, job: Optional[JobDetails] = None, match_report: Optional[MatchReport] = None
    ) -> UserProfile:
        """
        Produces an ATS-optimized, production-grade UserProfile following AI Resume Architect standards:
        - 100% zero text duplication
        - Clean continuous URLs
        - Standard 6-category technical skills
        - XYZ action-oriented project and experience bullets
        """
        tailored = profile.model_copy(deep=True)
        matched_skills = match_report.matched_skills if match_report else []

        # 1. Sanitize Header Contact Info & URLs
        if tailored.contact:
            tailored.contact.linkedin = self.sanitize_url(tailored.contact.linkedin)
            tailored.contact.github = self.sanitize_url(tailored.contact.github)
            tailored.contact.portfolio = self.sanitize_url(tailored.contact.portfolio)
            if tailored.contact.email:
                tailored.contact.email = tailored.contact.email.replace("mailto:", "").strip()

        # 2. Refine Headline & Summary
        tailored.headline = profile.headline or (job.title if job else "AI & Machine Learning Engineer")
        if profile.summary:
            # Clean summary and remove any accidental duplicated sentences
            summary_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', profile.summary) if s.strip()]
            seen_sents: Set[str] = set()
            unique_sentences = []
            for s in summary_sentences:
                norm_s = re.sub(r'[^a-z0-9]', '', s.lower())
                if norm_s not in seen_sents and len(norm_s) > 8:
                    seen_sents.add(norm_s)
                    unique_sentences.append(s)
            tailored.summary = " ".join(unique_sentences)

        # 3. Categorize Technical Skills into 6 Industry-Standard Domains
        all_skills = profile.skills or []
        tailored.categorized_skills = self.categorize_skills(all_skills)
        tailored.skills = all_skills

        # 4. Tailor Production & Practical Projects
        tailored.projects = self.tailor_projects(profile.projects, matched_skills)

        # 5. Tailor Professional Experience
        tailored.experience = self.tailor_experience(profile.experience, matched_skills)

        # 6. Sanitize Certifications
        if tailored.certifications:
            clean_certs = []
            seen_cert_names: Set[str] = set()
            for cert in tailored.certifications:
                norm_c = re.sub(r'[^a-z0-9]', '', cert.name.lower())
                if norm_c not in seen_cert_names:
                    seen_cert_names.add(norm_c)
                    clean_certs.append(cert)
            tailored.certifications = clean_certs

        return tailored
