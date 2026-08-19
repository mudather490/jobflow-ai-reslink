"""
Test Suite: Production-Grade AI Resume Architect & 'Corporate Elite' Engine
Verifies:
1. Zero text duplication across projects, experience, and summary.
2. Elimination of orphan single-word bullets (e.g. 'NumPy.', 'TensorFlow:').
3. Continuous, whitespace-free GitHub and LinkedIn URLs.
4. Standardized 6-category technical skills mapping.
5. High-fidelity PDF and DOCX generation for 'corporate_elite' template.
"""
import unittest
from pathlib import Path

from core.resume_parser import (
    UserProfile,
    ContactInfo,
    WorkExperience,
    Project,
    Education,
    Certification,
)
from core.tailor import ResumeTailor
from core.pdf_generator import ResumeDocumentGenerator
from config import OUTPUT_DIR


class TestCorporateEliteAIArchitect(unittest.TestCase):

    def setUp(self):
        self.tailor = ResumeTailor()

        # Construct candidate data containing raw noise, duplicates, orphan bullets, and broken URLs
        self.raw_profile = UserProfile(
            full_name="MUDATHER MOHAMMED",
            headline="Lead AI & Machine Learning Engineer",
            target_role="Senior AI Engineer | Machine Learning Specialist",
            contact=ContactInfo(
                email="mudatherkbyer@gmail.com",
                phone="+249 92 012 3456",
                location="Dubai, UAE (Open to Worldwide Remote)",
                linkedin="https://linkedin.com/in/mudather-mohammed ",
                github="https://github.com/mudather490/jobflow ai reslink",
                portfolio="https://jobflow.ai ",
            ),
            summary="Distinguished AI Engineer specializing in autonomous multi-agent orchestration and high-throughput LLM pipelines. Distinguished AI Engineer specializing in autonomous multi-agent orchestration and high-throughput LLM pipelines. Proven track record of designing scalable ML models and production-ready REST APIs.",
            skills=[
                "Python", "SQL", "Bash/Linux", "Git/GitHub",
                "Scikit-learn", "Regression/Classification", "Gradient Descent", "Feature Engineering", "MSE", "R2", "ROC-AUC",
                "PyTorch", "TensorFlow", "CNNs", "Transformers", "Neural Networks",
                "LLM APIs", "AI Agents", "Prompt Engineering", "RAG Architectures", "Vector Databases", "LangChain",
                "FastAPI", "REST APIs", "Supabase/PostgreSQL", "Docker", "Vercel",
                "NumPy", "Pandas", "Matplotlib", "Linear Algebra", "Calculus", "Statistics"
            ],
            projects=[
                Project(
                    name="Autonomous Multi-Agent JobFlow Orchestrator",
                    subtitle="Distributed Agentic Workflow Engine",
                    description="Architected multi-agent system processing 10,000+ applications daily with sub-second latency.",
                    bullets=[
                        "Architected distributed agent network processing 10,000+ applications daily with sub-second latency.",
                        "Architected distributed agent network processing 10,000+ applications daily with sub-second latency.",  # Duplicate
                        "NumPy.",  # Orphan bullet
                        "Engineered custom async queue workers and Redis caching, cutting memory footprint by 45%.",
                        "Implemented RAG semantic retrieval pipeline achieving 94.8% precision on unstructured job specs."
                    ],
                    technologies=["Python", "FastAPI", "PyTorch", "Redis", "Docker"],
                    repository="https://github.com/mudather490/jobflow-ai-reslink ",
                ),
                Project(
                    name="ResLink Interactive Video Pitch & Recruiter Hub",
                    subtitle="Real-Time Teleprompter & Dynamic ATS Canvas",
                    description="Built browser-native video pitch recorder and interactive ATS resume renderer.",
                    bullets=[
                        "TensorFlow:",  # Orphan bullet
                        "Developed WebRTC video recorder and sanitized teleprompter script engine with zero runtime latency.",
                        "Designed dynamic ATS canvas with instant template switcher across 4 executive themes.",
                        "Benchmarked PDF generation pipeline, achieving 250ms render time using ReportLab flowables."
                    ],
                    technologies=["Python", "FastAPI", "ReportLab", "JavaScript", "WebRTC"],
                    repository="https://github.com/mudather490/reslink-studio",
                )
            ],
            experience=[
                WorkExperience(
                    company="Tech Frontier Innovations",
                    role="Principal AI Architect",
                    duration="2021 - Present",
                    location="Remote",
                    subtitle="Enterprise AI Systems Division",
                    summary="Led engineering team building autonomous agents and high-throughput ML pipelines.",
                    bullets=[
                        "Spearheaded enterprise AI agent deployment across 12 services, reducing operational latency by 85%.",
                        "Spearheaded enterprise AI agent deployment across 12 services, reducing operational latency by 85%.", # Duplicate
                        "PyTorch.", # Orphan bullet
                        "Benchmarked and deployed fine-tuned transformer models, boosting inference throughput to 4,200 req/s.",
                        "Mentored 12 machine learning engineers across 4 time zones on clean code and automated CI/CD."
                    ]
                )
            ],
            education=[
                Education(
                    institution="University of Khartoum",
                    degree="Bachelor of Science in Computer Engineering",
                    year="2013 - 2018",
                    details="Rigorous foundation in Discrete Mathematics, Linear Algebra, Algorithms, and Distributed Systems."
                )
            ],
            certifications=[
                Certification(
                    name="Deep Learning Specialization",
                    issuer="DeepLearning.AI",
                    status="Completed",
                    details="Neural Networks, CNNs, Sequence Models, and Hyperparameter Optimization."
                ),
                Certification(
                    name="AWS Certified Solutions Architect — Professional",
                    issuer="Amazon Web Services",
                    status="Active",
                    details="Cloud Architecture, Microservices, and High-Availability Systems."
                )
            ]
        )

    def test_01_url_sanitization(self):
        """Verify all URLs are continuous, valid strings with zero whitespace breaks."""
        tailored = self.tailor.tailor_profile(self.raw_profile)
        
        self.assertEqual(tailored.contact.github, "https://github.com/mudather490/jobflowaireslink")
        self.assertEqual(tailored.contact.linkedin, "https://linkedin.com/in/mudather-mohammed")
        self.assertEqual(tailored.contact.portfolio, "https://jobflow.ai")
        self.assertNotIn(" ", tailored.projects[0].repository)

    def test_02_zero_text_duplication(self):
        """Verify identical bullet points and duplicate summary sentences are eliminated."""
        tailored = self.tailor.tailor_profile(self.raw_profile)

        # Check summary duplication
        summary_sentences = tailored.summary.split(". ")
        self.assertEqual(len(summary_sentences), len(set(summary_sentences)), "Duplicate sentence in summary!")

        # Check project bullets duplication
        for proj in tailored.projects:
            self.assertEqual(len(proj.bullets), len(set(proj.bullets)), f"Duplicate bullets in project '{proj.name}'!")

        # Check experience bullets duplication
        for exp in tailored.experience:
            self.assertEqual(len(exp.bullets), len(set(exp.bullets)), f"Duplicate bullets in experience '{exp.role}'!")

    def test_03_orphan_bullet_elimination(self):
        """Verify single-word orphan tokens like 'NumPy.' or 'TensorFlow:' are eliminated."""
        tailored = self.tailor.tailor_profile(self.raw_profile)

        for proj in tailored.projects:
            for b in proj.bullets:
                self.assertFalse(b.strip().lower() in ["numpy.", "tensorflow:", "pytorch."], f"Orphan bullet found: {b}")
                self.assertTrue(len(b.split()) >= 3, f"Bullet too short: {b}")

        for exp in tailored.experience:
            for b in exp.bullets:
                self.assertFalse(b.strip().lower() in ["numpy.", "tensorflow:", "pytorch."], f"Orphan bullet found: {b}")
                self.assertTrue(len(b.split()) >= 3, f"Bullet too short: {b}")

    def test_04_skills_categorization_domains(self):
        """Verify technical skills are categorized into standard AI/ML domains."""
        tailored = self.tailor.tailor_profile(self.raw_profile)
        cats = tailored.categorized_skills

        self.assertIn("Programming & Core Tools", cats)
        self.assertIn("Machine Learning & Statistics", cats)
        self.assertIn("Deep Learning & Neural Networks", cats)
        self.assertIn("AI Engineering & LLM Systems", cats)
        self.assertIn("Backend, Cloud & Databases", cats)
        self.assertIn("Data & Math", cats)

        self.assertIn("Python", cats["Programming & Core Tools"])
        self.assertIn("PyTorch", cats["Deep Learning & Neural Networks"])
        self.assertIn("FastAPI", cats["Backend, Cloud & Databases"])
        self.assertIn("NumPy", cats["Data & Math"])

    def test_05_zero_section_contamination(self):
        """Verify skills contain ONLY keywords and tools, never URLs or project sentences."""
        from core.resume_parser import ResumeParser
        raw_text = """
        MUDATHER MOHAMMED
        mudatherkbyer@gmail.com | +249 92 012 3456 | Dubai, UAE
        
        TECHNICAL SKILLS:
        • Programming & Tools: Python, SQL, Linux, Git, GitHub
        • Machine Learning: Scikit-learn, Regression, Decision Trees
        • https://github.com/mudather490/jobflow-ai-reslink
        • Built autonomous agent network processing 10,000 requests per second with high throughput.
        • Deep Learning: PyTorch, TensorFlow, CNNs
        
        PRACTICAL PROJECTS:
        • Autonomous Agent Orchestrator:
        Built multi-agent system processing 10,000+ applications daily with sub-second latency.
        Repository: https://github.com/mudather490/jobflow-ai-reslink
        """
        parsed = ResumeParser.parse_text_to_profile(raw_text)
        for s in parsed.skills:
            self.assertNotIn("http", s.lower(), f"Contaminated skill with URL: {s}")
            self.assertNotIn("github.com", s.lower(), f"Contaminated skill with URL: {s}")
            self.assertLess(len(s.split()), 6, f"Skill is too long / sentence: {s}")

    def test_06_corporate_elite_pdf_and_docx_generation(self):
        """Verify error-free PDF and DOCX generation in corporate_elite style."""
        tailored = self.tailor.tailor_profile(self.raw_profile)

        docx_path = str(OUTPUT_DIR / "Test_Corporate_Elite_Resume.docx")
        pdf_path = str(OUTPUT_DIR / "Test_Corporate_Elite_Resume.pdf")

        # Generate DOCX
        ResumeDocumentGenerator.generate_docx(tailored, docx_path, template_id="corporate_elite")
        self.assertTrue(Path(docx_path).exists())
        self.assertTrue(Path(docx_path).stat().st_size > 1000)

        # Generate PDF
        ResumeDocumentGenerator.generate_pdf(tailored, pdf_path, template_id="corporate_elite")
        self.assertTrue(Path(pdf_path).exists())
        self.assertTrue(Path(pdf_path).stat().st_size > 1000)

    def test_07_to_ats_schema_json(self):
        """Verify export to structured ATS JSON schema."""
        tailored = self.tailor.tailor_profile(self.raw_profile)
        schema = tailored.to_ats_schema_dict()

        self.assertIn("personal_info", schema)
        self.assertIn("professional_summary", schema)
        self.assertIn("technical_skills", schema)
        self.assertIn("certifications", schema)
        self.assertIn("practical_projects", schema)
        self.assertIn("professional_experience", schema)
        self.assertIn("additional_background", schema)

        # Check technical_skills keys
        skills = schema["technical_skills"]
        self.assertIn("Programming", skills)
        self.assertIn("Machine Learning", skills)
        self.assertIn("Deep Learning", skills)
        self.assertIn("AI Engineering", skills)
        self.assertIn("Backend & Deployment", skills)
        self.assertIn("Data & Tools", skills)

        # Check personal_info keys
        p_info = schema["personal_info"]
        self.assertIn("full_name", p_info)
        self.assertIn("target_title", p_info)
        self.assertIn("email", p_info)
        self.assertIn("linkedin_url", p_info)
        self.assertIn("github_url", p_info)

    def test_08_no_work_professional_or_lead_professional(self):
        """Verify that 'Work Professional', 'Lead Professional', or 'Professional Role' never appear."""
        from core.resume_parser import ResumeParser
        raw_text = """
        MUDATHER MOHAMMED
        mudatherkbyer@gmail.com
        
        EXPERIENCE
        Google Cloud | 2022 - Present
        • Built scalable distributed backend systems.
        """
        parsed = ResumeParser.parse_text_to_profile(raw_text)
        schema = parsed.to_ats_schema_dict()
        for exp in schema["professional_experience"]:
            self.assertNotIn("work professional", exp["role_title"].lower())
            self.assertNotIn("lead professional", exp["role_title"].lower())
            self.assertNotIn("professional role", exp["role_title"].lower())


if __name__ == "__main__":
    unittest.main()
