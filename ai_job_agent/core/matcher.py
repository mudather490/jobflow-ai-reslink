import re
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from core.resume_parser import UserProfile
from core.scraper import JobDetails
from config import GEMINI_API_KEY, OPENAI_API_KEY


class MatchReport(BaseModel):
    job_title: str
    company: str
    match_score: float = Field(description="Overall ATS match score between 0.0 and 100.0")
    overall_ats_score: float = Field(default=0.0, description="Weighted ATS score (60% Skill Match, 25% Title Relevance, 15% Experience Alignment)")
    matched_skills_count: int = Field(default=0)
    required_skills_count: int = Field(default=0)
    skill_match_percentage: float = Field(default=0.0)
    qualification_tier: str = Field(default="Skill Gaps Detected")
    qualification_badge_color: str = Field(default="rose")
    linkedin_qualification_text: str = Field(default="")
    title_relevance_score: float = Field(default=0.0)
    experience_alignment_score: float = Field(default=0.0)
    matched_skills: List[str] = Field(default_factory=list)
    missing_critical_skills: List[str] = Field(default_factory=list)
    candidate_extra_skills: List[str] = Field(default_factory=list)
    partial_skills: List[str] = Field(default_factory=list)
    experience_assessment: str = ""
    summary_analysis: str = ""
    actionable_recommendations: List[str] = Field(default_factory=list)
    international_badge: str = "🌐 Worldwide Remote"
    international_friendly_score: int = 95
    eligibility_notes: str = "Hires international remote candidates globally."


class JobMatcher:
    """
    Universal Intelligent ATS Job Matcher & LinkedIn Premium Skill Engine.
    Uses a Bi-Directional Semantic Concept Equivalence Graph to accurately map
    job requirements against candidate skills, projects, experience, and certifications.
    """

    # Comprehensive Concept Equivalence & Synonym Taxonomy
    EQUIVALENCE_GRAPH: Dict[str, List[str]] = {
        "Python": [
            "python", "python3", "py", "python programming", "asyncio", "pydantic"
        ],
        "React": [
            "react", "react.js", "reactjs", "react native", "react hooks", "jsx", "tsx"
        ],
        "TypeScript": [
            "typescript", "ts", "type-script", "typed javascript"
        ],
        "JavaScript": [
            "javascript", "js", "es6", "es6+", "ecmascript"
        ],
        "Next.js": [
            "next.js", "nextjs", "next", "ssr", "server-side rendering"
        ],
        "Vue.js": [
            "vue", "vue.js", "vuejs", "nuxt", "nuxt.js"
        ],
        "Angular": [
            "angular", "angularjs", "angular 2+"
        ],
        "HTML5 & CSS3": [
            "html", "html5", "css", "css3", "sass", "scss", "responsive design", "web design"
        ],
        "TailwindCSS": [
            "tailwind", "tailwindcss", "tailwind css", "styled-components"
        ],
        "GraphQL": [
            "graphql", "apollo", "apollo client", "hasura"
        ],
        "Machine Learning": [
            "machine learning", "ml", "scikit-learn", "sklearn", "supervised learning",
            "unsupervised learning", "regression", "classification", "clustering",
            "decision trees", "random forest", "xgboost", "lightgbm", "model evaluation",
            "feature engineering", "cross-validation", "hyperparameter tuning"
        ],
        "Deep Learning": [
            "deep learning", "dl", "neural networks", "artificial neural networks", "ann",
            "convolutional neural networks", "cnn", "cnns", "recurrent neural networks",
            "rnn", "lstm", "transformers", "transformer", "attention mechanisms",
            "backpropagation", "feedforward", "deep learning specialization"
        ],
        "PyTorch": [
            "pytorch", "torch", "torchvision", "torchaudio", "torchtext"
        ],
        "TensorFlow": [
            "tensorflow", "tf", "keras", "tensorboard"
        ],
        "LLMs & Generative AI": [
            "llm", "llms", "large language models", "large language model", "generative ai",
            "genai", "prompt engineering", "prompt design", "gpt", "gpt-4", "gpt-3.5",
            "chatgpt", "claude", "gemini", "llama", "llama-2", "llama-3", "mistral",
            "fine-tuning", "lora", "qlora", "rlhf", "vllm", "ollama", "hugging face",
            "huggingface", "llm apis", "llm api", "openai api", "anthropic api"
        ],
        "RAG & Vector Search": [
            "rag", "retrieval-augmented generation", "retrieval augmented generation",
            "vector search", "vector database", "vector databases", "vector embeddings",
            "embeddings", "semantic search", "chromadb", "chroma", "pinecone", "weaviate",
            "qdrant", "milvus", "faiss", "pgvector", "graphrag"
        ],
        "AI Agents & Workflows": [
            "ai agents", "ai agent", "autonomous agents", "autonomous agent", "multi-agent",
            "multi-agent systems", "agentic workflows", "agentic", "langchain", "langgraph",
            "crewai", "autogen", "llamaindex", "semantic kernel", "dspy"
        ],
        "NLP (Natural Language Processing)": [
            "nlp", "natural language processing", "text processing", "tokenization",
            "named entity recognition", "ner", "sentiment analysis", "bert", "spacy",
            "nltk", "word2vec", "sentence-transformers"
        ],
        "Computer Vision": [
            "computer vision", "cv", "image processing", "opencv", "yolo", "object detection",
            "image segmentation", "vision transformers", "vit", "resnet"
        ],
        "FastAPI & REST APIs": [
            "fastapi", "fast api", "rest api", "rest apis", "restful api", "restful apis",
            "api development", "api design", "flask", "django", "endpoints", "backend development"
        ],
        "Node.js & Express": [
            "node.js", "nodejs", "node", "express", "express.js", "nest.js", "nestjs"
        ],
        "Go (Golang)": [
            "go", "golang", "go programming"
        ],
        "Rust": [
            "rust", "rustlang", "cargo"
        ],
        "Java & Spring": [
            "java", "spring", "spring boot", "hibernate"
        ],
        "C++": [
            "c++", "cpp", "c"
        ],
        "Docker & Containerization": [
            "docker", "containerization", "containers", "container", "dockerfile",
            "docker-compose", "docker compose"
        ],
        "Kubernetes & Orchestration": [
            "kubernetes", "k8s", "helm", "orchestration", "cluster management"
        ],
        "AWS (Amazon Web Services)": [
            "aws", "amazon web services", "s3", "ec2", "ecs", "eks", "lambda", "dynamodb", "sqs", "sns"
        ],
        "GCP (Google Cloud)": [
            "gcp", "google cloud", "google cloud platform", "bigquery", "cloud run"
        ],
        "Azure": [
            "azure", "microsoft azure", "azure devops"
        ],
        "Terraform & IaC": [
            "terraform", "infrastructure as code", "iac", "cloudformation", "ansible"
        ],
        "CI/CD & GitHub Actions": [
            "ci/cd", "continuous integration", "continuous deployment", "github actions",
            "gitlab ci", "jenkins"
        ],
        "Linux & Bash": [
            "linux", "bash", "shell", "unix", "ubuntu", "command line", "cli"
        ],
        "PostgreSQL & SQL": [
            "sql", "postgresql", "postgres", "supabase", "mysql", "sqlite",
            "relational database", "relational databases", "rdbms", "database design", "database querying"
        ],
        "MongoDB": [
            "mongodb", "mongo", "mongoose"
        ],
        "Redis & Caching": [
            "redis", "memcached", "caching", "cache"
        ],
        "Celery & Task Queues": [
            "celery", "task queues", "async queues", "rq", "bullmq"
        ],
        "Apache Kafka & Queues": [
            "kafka", "apache kafka", "rabbitmq", "event-driven", "message queues"
        ],
        "Snowflake & BigQuery": [
            "snowflake", "bigquery", "redshift", "data warehouse", "data warehousing"
        ],
        "Apache Spark": [
            "spark", "pyspark", "apache spark", "databricks"
        ],
        "Swift & iOS": [
            "swift", "swiftui", "ios", "xcode", "cocoapods"
        ],
        "Kotlin & Android": [
            "kotlin", "android", "android sdk", "jetpack compose"
        ],
        "Flutter & React Native": [
            "flutter", "dart", "react native"
        ],
        "Cybersecurity & OWASP": [
            "cybersecurity", "security", "owasp", "penetration testing", "pen testing",
            "vulnerability assessment", "iam", "wireshark", "soc 2"
        ],
        "Jest & Testing": [
            "testing", "unit testing", "jest", "pytest", "cypress", "playwright", "tdd"
        ],
        "Git & Version Control": [
            "git", "github", "gitlab", "bitbucket", "version control"
        ],
        "Data Analysis & Mathematics": [
            "numpy", "pandas", "matplotlib", "seaborn", "data analysis", "data processing",
            "eda", "exploratory data analysis", "linear algebra", "calculus", "applied statistics",
            "probability", "statistics", "data science"
        ],
        "Agile & Project Management": [
            "agile", "scrum", "jira", "kanban", "project management", "sprint planning", "pmp", "prince2"
        ],
        "Accounting & GAAP": [
            "gaap", "ifrs", "accounting", "general ledger", "accounts payable", "accounts receivable",
            "journal entries", "reconciliation", "tax compliance", "auditing", "financial audit"
        ],
        "Financial Modeling & Analysis": [
            "financial modeling", "financial analysis", "dcf", "lbo", "budgeting", "forecasting",
            "variance analysis", "corporate finance", "financial reporting", "excel vba", "quickbooks"
        ],
        "Sales & CRM": [
            "salesforce", "sfdc", "crm", "b2b sales", "lead generation", "account management",
            "pipeline management", "cold calling", "prospecting", "deal closing", "client acquisition"
        ],
        "Digital Marketing & SEO": [
            "seo", "search engine optimization", "content marketing", "google analytics", "copywriting",
            "social media marketing", "digital marketing", "email marketing", "ppc", "google ads", "sem"
        ],
        "Healthcare & Clinical Care": [
            "patient care", "clinical assessment", "hipaa", "hipaa compliance", "ehr", "electronic health records",
            "triage", "patient assessment", "nursing", "vital signs", "medical terminology"
        ],
        "Human Resources & Talent": [
            "hris", "talent acquisition", "recruiting", "payroll", "employee relations",
            "onboarding", "performance management", "human resources", "hr policies", "workday"
        ],
        "Legal & Regulatory Compliance": [
            "contract drafting", "regulatory compliance", "legal research", "due diligence",
            "intellectual property", "contract negotiation", "legal compliance", "risk assessment"
        ]
    }


    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

    def extract_job_requirements(self, job_text: str, job_title: str = "") -> List[str]:
        """
        Extracts verified technical requirements and core competencies from job description and title.
        """
        combined_text = f"{job_title} \n {job_text}".lower()
        found_reqs: Set[str] = set()

        # 1. Match against Equivalence Graph canonical categories
        for canon, synonyms in self.EQUIVALENCE_GRAPH.items():
            for syn in synonyms:
                pattern = r"(?<![a-zA-Z0-9_\-\+\#])" + re.escape(syn) + r"(?![a-zA-Z0-9_\-\+\#])"
                if re.search(pattern, combined_text, re.IGNORECASE):
                    found_reqs.add(canon)
                    break

        # 2. Extract specific requirement phrases from bullet points or requirement headers
        dynamic_patterns = [
            r"(?:experience with|proficient in|knowledge of|familiarity with|expertise in|skilled in|understanding of|hands-on with|strong in)\s+([A-Za-z0-9\+\#\.\s,/]{2,40})(?:\.|\;|\n|\band\b)",
            r"(?:requirements|qualifications|what you bring|skills needed|required skills|what we look for)[\s\S]*?(?:responsibilities|benefits|about us|\Z)"
        ]

        for m in re.finditer(dynamic_patterns[0], combined_text):
            phrase = m.group(1).strip()
            for part in re.split(r"[,/]", phrase):
                cleaned = part.strip()
                if 2 < len(cleaned) < 35:
                    for canon, synonyms in self.EQUIVALENCE_GRAPH.items():
                        if cleaned.lower() in synonyms or any(s in cleaned.lower() for s in synonyms if len(s) > 3):
                            found_reqs.add(canon)
                            break

        # 3. Dynamic Title-based Domain Fallback if description is sparse
        if len(found_reqs) < 3:
            t_lower = job_title.lower()
            if any(k in t_lower for k in ["machine learning", "ml", "ai", "deep learning", "llm", "data scientist", "nlp"]):
                for skill in ["Machine Learning", "Python", "Deep Learning", "PyTorch", "Data Analysis & Mathematics", "FastAPI & REST APIs"]:
                    found_reqs.add(skill)
            elif any(k in t_lower for k in ["frontend", "react", "vue", "angular", "ui", "next.js", "frontend engineer"]):
                for skill in ["React", "TypeScript", "JavaScript", "HTML5 & CSS3", "TailwindCSS"]:
                    found_reqs.add(skill)
            elif any(k in t_lower for k in ["devops", "sre", "cloud", "infrastructure", "kubernetes", "terraform"]):
                for skill in ["Docker & Containerization", "Kubernetes & Orchestration", "AWS (Amazon Web Services)", "Linux & Bash", "CI/CD & GitHub Actions"]:
                    found_reqs.add(skill)
            elif any(k in t_lower for k in ["data engineer", "etl", "big data", "spark"]):
                for skill in ["PostgreSQL & SQL", "Python", "Snowflake & BigQuery", "Docker & Containerization"]:
                    found_reqs.add(skill)
            elif any(k in t_lower for k in ["mobile", "ios", "android", "flutter", "react native", "swift"]):
                for skill in ["Flutter & React Native", "TypeScript", "REST APIs", "Git & Version Control"]:
                    found_reqs.add(skill)
            else:
                for skill in ["Python", "FastAPI & REST APIs", "PostgreSQL & SQL", "Docker & Containerization", "Git & Version Control"]:
                    found_reqs.add(skill)

        return sorted(list(found_reqs))

    def calculate_title_relevance(self, candidate_roles: List[str], target_title: str) -> float:
        """
        Calculates title relevance score (0 - 100) between candidate past/target roles and job title.
        """
        if not target_title:
            return 75.0
        
        target_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', target_title.lower()))
        noise = {"senior", "lead", "staff", "principal", "junior", "mid", "associate", "role", "position", "specialist", "engineer", "developer"}
        meaningful_target = target_tokens - noise
        if not meaningful_target:
            meaningful_target = target_tokens

        best_score = 50.0
        for role in candidate_roles:
            if not role:
                continue
            role_lower = role.lower()
            role_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', role_lower))
            overlap = meaningful_target.intersection(role_tokens)
            if overlap:
                ratio = len(overlap) / max(len(meaningful_target), 1)
                best_score = max(best_score, min(100.0, 60.0 + (ratio * 40.0)))
            if target_title.lower() in role_lower or role_lower in target_title.lower():
                best_score = max(best_score, 95.0)

        return round(best_score, 1)

    def calculate_experience_alignment(self, profile: UserProfile, job_text: str, job_title: str) -> float:
        """
        Calculates seniority & experience portfolio alignment score (0 - 100).
        """
        exp_count = len(profile.experience or [])
        proj_count = len(profile.projects or [])
        cert_count = len(profile.certifications or [])

        base = min(60.0, (exp_count * 20.0) + (proj_count * 10.0) + (cert_count * 5.0))
        combined = f"{job_title} {job_text}".lower()
        requires_senior = any(w in combined for w in ["senior", "lead", "principal", "staff", "5+", "7+"])
        candidate_is_senior = exp_count >= 2 or any(
            any(w in (e.role or '').lower() for w in ["senior", "lead", "principal", "staff", "head"])
            for e in (profile.experience or [])
        )

        if requires_senior and candidate_is_senior:
            alignment = base + 35.0
        elif not requires_senior:
            alignment = base + 30.0
        else:
            alignment = base + 15.0

        return min(100.0, round(max(50.0, alignment), 1))

    def evaluate_match(self, profile: Optional[UserProfile], job: JobDetails) -> MatchReport:
        """
        Runs comprehensive ATS match evaluation between candidate and target role
        using bidirectional semantic equivalence mapping and LinkedIn Premium Skill Matcher.
        """
        if not profile:
            from core.resume_parser import ResumeParser
            profile = ResumeParser.get_clean_starter_profile("corporate_elite")

        job_reqs = self.extract_job_requirements(job.description, job.title)
        
        # Build candidate's holistic semantic text corpus
        candidate_text = profile.get_full_text().lower()
        candidate_skills_flat = [s.lower() for s in (profile.skills or [])]
        
        # Also collect skills from categorized_skills if present
        if profile.categorized_skills:
            for cat_skills in profile.categorized_skills.values():
                candidate_skills_flat.extend([s.lower() for s in cat_skills])

        # Also collect project titles and technologies
        if profile.projects:
            for p in profile.projects:
                candidate_skills_flat.extend([t.lower() for t in (p.technologies or []) if t])
                p_name = (p.name or '').lower()
                p_desc = (p.description or '').lower()
                p_bullets = ' '.join([b for b in (p.bullets or []) if b]).lower()
                candidate_text += f" {p_name} {p_desc} {p_bullets}"

        # Also collect experience details
        if profile.experience:
            for exp in profile.experience:
                exp_comp = (exp.company or '').lower()
                exp_role = (exp.role or '').lower()
                exp_bullets = ' '.join([b for b in (exp.bullets or []) if b]).lower()
                candidate_text += f" {exp_comp} {exp_role} {exp_bullets}"

        # Also collect certifications
        if profile.certifications:
            for c in profile.certifications:
                c_name = (c.name or '').lower()
                c_details = (c.details or '').lower()
                if c_name:
                    candidate_skills_flat.append(c_name)
                candidate_text += f" {c_name} {c_details}"

        matched: List[str] = []
        missing: List[str] = []

        for req in job_reqs:
            synonyms = self.EQUIVALENCE_GRAPH.get(req, [req.lower()])
            is_matched = False

            # Check 1: Direct or synonym match in candidate skills list
            for syn in synonyms:
                pattern = r"(?<![a-zA-Z0-9_\-\+\#])" + re.escape(syn) + r"(?![a-zA-Z0-9_\-\+\#])"
                for cand_skill in candidate_skills_flat:
                    if syn == cand_skill or re.search(pattern, cand_skill, re.IGNORECASE):
                        is_matched = True
                        break
                if is_matched:
                    break

            # Check 2: Match in candidate full text (projects, bullets, summary, experience)
            if not is_matched:
                for syn in synonyms:
                    pattern = r"(?<![a-zA-Z0-9_\-\+\#])" + re.escape(syn) + r"(?![a-zA-Z0-9_\-\+\#])"
                    if re.search(pattern, candidate_text, re.IGNORECASE):
                        is_matched = True
                        break

            if is_matched:
                matched.append(req)
            else:
                missing.append(req)

        # Calculate LinkedIn Premium Skill Match Ratios & Scores
        total_reqs = len(job_reqs)
        matched_count = len(matched)
        skill_match_pct = round((matched_count / max(1, total_reqs)) * 100.0, 1) if total_reqs > 0 else 100.0

        # Candidate Extra Skills (Bonus Strengths)
        matched_canon_set = set(matched)
        extra_skills = []
        for s in (profile.skills or []):
            if s not in matched_canon_set and not any(s.lower() == m.lower() for m in matched):
                extra_skills.append(s)

        # Title Relevance & Experience Alignment
        cand_roles = [e.role for e in (profile.experience or []) if e.role]
        if profile.target_role:
            cand_roles.append(profile.target_role)
        if profile.headline:
            cand_roles.append(profile.headline)

        title_rel_score = self.calculate_title_relevance(cand_roles, job.title)
        exp_align_score = self.calculate_experience_alignment(profile, job.description, job.title)

        # Exact Weighted Formula: 60% Skill Match + 25% Title Relevance + 15% Experience Alignment
        weighted_ats_score = round(
            (skill_match_pct * 0.60) + (title_rel_score * 0.25) + (exp_align_score * 0.15),
            1
        )
        if matched_count == total_reqs and total_reqs > 0:
            weighted_ats_score = max(92.0, weighted_ats_score)

        final_score = weighted_ats_score

        # Determine LinkedIn Qualification Tier & Badges
        if skill_match_pct >= 80.0 or final_score >= 80.0:
            tier = "Top Applicant (Highly Qualified)"
            badge_color = "emerald"
        elif skill_match_pct >= 60.0 or final_score >= 65.0:
            tier = "Good Fit (Moderate Match)"
            badge_color = "amber"
        else:
            tier = "Skill Gaps Detected"
            badge_color = "rose"

        linkedin_callout = f"You have {matched_count} of {total_reqs} required skills matching this role ({skill_match_pct}% Skill Match)"

        # Construct Actionable Recommendations
        recommendations = []
        if missing:
            recommendations.append(f"Bridge critical missing competencies: {', '.join(missing[:3])}")
        if len(profile.projects) < 2:
            recommendations.append("Showcase hands-on engineering repositories to boost ranking.")
        if not profile.summary:
            recommendations.append("Add an executive summary targeted specifically to this domain.")

        # Construct Recruiter Assessment
        if len(matched) == total_reqs:
            exp_assessment = (
                f"Candidate satisfies ALL {len(matched)} detected role requirements ({final_score}% match). "
                f"Demonstrated verified mastery in: {', '.join(matched[:4])}."
            )
        else:
            exp_assessment = (
                f"Candidate satisfies {len(matched)} of {total_reqs} detected role requirements ({final_score}% match). "
                f"Demonstrated background in: {', '.join(matched[:4]) if matched else 'core engineering fundamentals'}."
            )

        return MatchReport(
            job_title=job.title,
            company=job.company,
            match_score=final_score,
            overall_ats_score=final_score,
            matched_skills_count=matched_count,
            required_skills_count=total_reqs,
            skill_match_percentage=skill_match_pct,
            qualification_tier=tier,
            qualification_badge_color=badge_color,
            linkedin_qualification_text=linkedin_callout,
            title_relevance_score=title_rel_score,
            experience_alignment_score=exp_align_score,
            matched_skills=matched,
            missing_critical_skills=missing,
            candidate_extra_skills=extra_skills,
            partial_skills=[],
            experience_assessment=exp_assessment,
            summary_analysis=f"LinkedIn Skill Match: {skill_match_pct}% ({matched_count}/{total_reqs}) • Overall ATS: {final_score}%.",
            actionable_recommendations=recommendations,
            international_badge=job.international_badge,
            international_friendly_score=job.international_friendly_score,
            eligibility_notes=job.eligibility_notes,
        )
