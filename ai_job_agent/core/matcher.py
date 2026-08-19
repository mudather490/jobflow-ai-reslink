import re
from typing import List, Dict, Any, Optional, Set
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
    Universal Intelligent ATS Job Matcher.
    Uses a Bi-Directional Semantic Concept Equivalence Graph to accurately map
    job requirements against candidate skills, projects, experience, and certifications.
    """

    # Comprehensive Concept Equivalence & Synonym Taxonomy
    EQUIVALENCE_GRAPH: Dict[str, List[str]] = {
        "Python": [
            "python", "python3", "py", "python programming", "asyncio", "pydantic"
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
        "Docker & Containerization": [
            "docker", "containerization", "containers", "container", "dockerfile",
            "docker-compose", "docker compose"
        ],
        "Kubernetes & Orchestration": [
            "kubernetes", "k8s", "helm", "orchestration", "cluster management"
        ],
        "SQL & Relational Databases": [
            "sql", "postgresql", "postgres", "supabase", "mysql", "sqlite",
            "relational database", "relational databases", "rdbms", "database design", "database querying"
        ],
        "NoSQL & Cache Databases": [
            "nosql", "mongodb", "redis", "cassandra", "dynamodb", "elasticsearch", "neo4j"
        ],
        "Cloud Infrastructure": [
            "aws", "amazon web services", "gcp", "google cloud", "google cloud platform",
            "azure", "microsoft azure", "cloud computing", "cloud infrastructure",
            "serverless", "lambda", "cloud run", "vercel"
        ],
        "DevOps & CI/CD": [
            "ci/cd", "continuous integration", "continuous deployment", "github actions",
            "gitlab ci", "jenkins", "terraform", "ansible", "devops"
        ],
        "Linux & Version Control": [
            "linux", "bash", "shell", "unix", "ubuntu", "git", "github", "gitlab",
            "version control", "command line", "cli"
        ],
        "Data Analysis & Mathematics": [
            "numpy", "pandas", "matplotlib", "seaborn", "data analysis", "data processing",
            "eda", "exploratory data analysis", "linear algebra", "calculus", "applied statistics",
            "probability", "statistics", "data science"
        ],
        "Distributed Systems & Async Queues": [
            "distributed systems", "microservices", "celery", "kafka", "rabbitmq",
            "event-driven", "message queues", "async processing", "scalability", "caching"
        ],
        "TypeScript & JavaScript": [
            "javascript", "js", "typescript", "ts", "node.js", "nodejs", "react", "next.js", "vue"
        ],
        "C++ & Systems Programming": [
            "c++", "cpp", "c", "rust", "golang", "go", "systems programming"
        ],
        "Agile & Project Management": [
            "agile", "scrum", "jira", "kanban", "project management", "sprint planning"
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

        # 3. Default fallback for AI/Engineering roles if description was minimal or generic
        if not found_reqs:
            title_lower = job_title.lower()
            if any(k in title_lower for k in ["ai", "machine learning", "ml", "deep learning"]):
                found_reqs.update(["Python", "Machine Learning", "Deep Learning", "PyTorch", "LLMs & Generative AI", "FastAPI & REST APIs", "SQL & Relational Databases"])
            elif any(k in title_lower for k in ["software", "engineer", "developer", "backend"]):
                found_reqs.update(["Python", "FastAPI & REST APIs", "Docker & Containerization", "SQL & Relational Databases", "Linux & Version Control"])
            else:
                found_reqs.update(["Python", "SQL & Relational Databases", "Data Analysis & Mathematics", "Linux & Version Control"])

        return sorted(list(found_reqs))

    def evaluate_match(self, profile: Optional[UserProfile], job: JobDetails) -> MatchReport:
        """
        Runs comprehensive ATS match evaluation between candidate and target role
        using bidirectional semantic equivalence mapping.
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
                candidate_skills_flat.extend([t.lower() for t in (p.technologies or [])])
                candidate_text += f" {p.name.lower()} {' '.join(p.bullets).lower()}"

        # Also collect experience details
        if profile.experience:
            for exp in profile.experience:
                candidate_text += f" {exp.company.lower()} {exp.role.lower()} {' '.join(exp.bullets).lower()}"

        # Also collect certifications
        if profile.certifications:
            for c in profile.certifications:
                candidate_skills_flat.append(c.name.lower())
                candidate_text += f" {c.name.lower()} {c.details.lower()}"

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

        # Calculate ATS Match Score
        total_reqs = len(job_reqs)
        if total_reqs == 0:
            final_score = 90.0
        else:
            match_ratio = len(matched) / total_reqs
            # Base match points (up to 85%)
            score_base = match_ratio * 85.0
            
            # Experience & project portfolio bonuses (up to 15%)
            proj_bonus = min(8.0, len(profile.projects) * 4.0)
            exp_bonus = min(7.0, len(profile.experience) * 3.5)
            
            final_score = min(100.0, round(score_base + proj_bonus + exp_bonus, 1))
            
            # If all requirements matched, guarantee high tier (92% - 100%)
            if len(missing) == 0:
                final_score = max(92.0, final_score)

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
            matched_skills=matched,
            missing_critical_skills=missing,
            partial_skills=[],
            experience_assessment=exp_assessment,
            summary_analysis=f"Real-Time ATS Match Score: {final_score}%.",
            actionable_recommendations=recommendations,
            international_badge=job.international_badge,
            international_friendly_score=job.international_friendly_score,
            eligibility_notes=job.eligibility_notes,
        )
