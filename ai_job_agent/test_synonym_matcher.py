import unittest
from core.resume_parser import ResumeParser, UserProfile
from core.pdf_generator import ResumeDocumentGenerator
from config import OUTPUT_DIR


class TestComprehensiveSemanticSectionMatcher(unittest.TestCase):
    """
    Test suite verifying universal recognition and accurate parsing of all section title
    synonyms across domains (Finance, AI/Engineering, Healthcare, Legal, Marketing, Sales, Design).
    """

    def test_synonym_variation_1_engineering(self):
        resume_text = """
JANE DOE
Lead AI & Systems Engineer
Email: jane.doe@example.com
Phone: +1 555-019-2834
Location: San Francisco, CA
LinkedIn: linkedin.com/in/janedoe
GitHub: github.com/janedoe

ABOUT ME
Passionate AI Engineer with 6+ years of experience developing machine learning systems, distributed backend infrastructure, and scalable generative AI pipelines.

AREAS OF EXPERTISE
Programming: Python, Rust, Go, C++
Frameworks & Tools: PyTorch, TensorFlow, FastAPI, Docker, Kubernetes
Cloud & Data: AWS, PostgreSQL, Redis, Qdrant

KEY PROJECTS
Autonomous Agent Orchestrator: Built a multi-agent framework utilizing GraphRAG and LangGraph to automate software deployment.
• Reduced manual pipeline intervention by 70%.
• Repository: https://github.com/janedoe/agent-orchestrator

High-Throughput Feature Store: Architected real-time feature delivery service with sub-millisecond latency.
• Scaled to 50k requests per second across Kubernetes clusters.

CAREER HISTORY
Senior AI Engineer — Tech Innovations Inc. | 2021 - Present
• Designed and deployed LLM inference microservices serving 1M+ active users.
• Mentored a team of 8 junior and mid-level machine learning engineers.

Machine Learning Developer — DataCore Labs | 2018 - 2021
• Built production recommendation systems and supervised deep learning models.

ACADEMIC BACKGROUND
Stanford University — Master of Science in Computer Science | 2016 - 2018
University of California, Berkeley — Bachelor of Science in Electrical Engineering | 2012 - 2016

PROFESSIONAL CERTIFICATIONS
Deep Learning Specialization — DeepLearning.AI: Completed — Neural networks, CNNs, RNNs, and Transformers.
AWS Certified Machine Learning - Specialty — AWS: Completed
"""
        profile = ResumeParser.parse_text_to_profile(resume_text)
        
        self.assertEqual(profile.full_name, "JANE DOE")
        self.assertEqual(profile.headline, "Lead AI & Systems Engineer")
        self.assertIn("Passionate AI Engineer", profile.summary)
        
        # Verify Skills (mapped from AREAS OF EXPERTISE)
        self.assertTrue(len(profile.skills) >= 6)
        self.assertIn("Python", profile.skills)
        self.assertIn("PyTorch", profile.skills)
        
        # Verify Projects (mapped from KEY PROJECTS)
        self.assertEqual(len(profile.projects), 2)
        self.assertIn("Autonomous Agent Orchestrator", profile.projects[0].name)
        
        # Verify Experience (mapped from CAREER HISTORY)
        self.assertEqual(len(profile.experience), 2)
        self.assertIn("Tech Innovations Inc.", profile.experience[0].company)
        
        # Verify Education (mapped from ACADEMIC BACKGROUND)
        self.assertEqual(len(profile.education), 2)
        self.assertIn("Stanford University", profile.education[0].institution)
        
        # Verify Certifications (mapped from PROFESSIONAL CERTIFICATIONS)
        self.assertEqual(len(profile.certifications), 2)
        self.assertIn("Deep Learning Specialization", profile.certifications[0].name)

    def test_synonym_variation_2_finance(self):
        resume_text = """
MICHAEL CHANG
Senior Financial Analyst & Controller
Email: m.chang@financegroup.com
Phone: (212) 555-8392
Location: New York, NY

EXECUTIVE SUMMARY
Certified financial analyst with expertise in quantitative modeling, corporate valuation, SEC compliance, and financial reporting.

CORE COMPETENCIES
Financial Modeling, DCF Valuation, GAAP Accounting, SEC Reporting, Portfolio Management, Risk Analysis

SELECTED PROJECTS
M&A Valuation Matrix: Designed automated DCF and LBO valuation model for $500M enterprise acquisitions.
• Streamlined financial due diligence turnaround by 40%.

EMPLOYMENT HISTORY
Senior Financial Analyst — Goldman Capital | 2020 - 2024
• Spearheaded quarterly financial performance analysis across $2B asset portfolio.
• Presented financial strategy directly to C-suite executives.

DEGREES & EDUCATION
Columbia Business School — MBA in Finance | 2018 - 2020
New York University — B.S. in Accounting & Economics | 2014 - 2018

LICENSES & CERTIFICATIONS
Chartered Financial Analyst (CFA) — CFA Institute: Completed
Certified Public Accountant (CPA) — AICPA: Completed
"""
        profile = ResumeParser.parse_text_to_profile(resume_text)
        
        self.assertEqual(profile.full_name, "MICHAEL CHANG")
        self.assertIn("Certified financial analyst", profile.summary)
        self.assertIn("Financial Modeling", profile.skills)
        self.assertIn("GAAP Accounting", profile.skills)
        self.assertEqual(len(profile.projects), 1)
        self.assertEqual(len(profile.experience), 1)
        self.assertEqual(len(profile.education), 2)
        self.assertEqual(len(profile.certifications), 2)

    def test_synonym_variation_3_healthcare(self):
        resume_text = """
DR. SARAH JENKINS
Clinical Informatics Specialist
Email: s.jenkins@medcenter.org
Phone: (415) 555-9012
Location: Chicago, IL

PROFESSIONAL PROFILE
Healthcare clinical data analyst with 8+ years leading electronic health record (EHR) integration and clinical data workflows.

DOMAIN EXPERTISE
Clinical Informatics, Epic Systems, Cerner EHR, HIPAA Compliance, HL7 / FHIR, Medical Terminology, Clinical Data Analytics

FEATURED PROJECTS
EHR Modernization Program: Led cross-departmental transition to unified FHIR clinical data pipeline.
• Reduced medication error alerts by 35%.

PROFESSIONAL BACKGROUND
Lead Informatics Specialist — Northwestern Medicine | 2019 - Present
• Supervised clinical workflow automation and data governance.

UNIVERSITY EDUCATION
University of Illinois — Master of Science in Health Informatics | 2017 - 2019
Rush University — Bachelor of Science in Nursing (BSN) | 2012 - 2016

ACCREDITATIONS
CPHIMS Certified — HIMSS: Completed
Registered Health Information Administrator (RHIA) — AHIMA: Completed
"""
        profile = ResumeParser.parse_text_to_profile(resume_text)
        
        self.assertEqual(profile.full_name, "DR. SARAH JENKINS")
        self.assertIn("Healthcare clinical data analyst", profile.summary)
        self.assertIn("Epic Systems", profile.skills)
        self.assertEqual(len(profile.projects), 1)
        self.assertEqual(len(profile.experience), 1)
        self.assertEqual(len(profile.education), 2)
        self.assertEqual(len(profile.certifications), 2)

    def test_synonym_variation_4_marketing_design(self):
        resume_text = """
EMILY WATSON
Growth Marketing & Brand Director
Email: emily@brandcraft.co
Phone: (310) 555-4421
Location: Los Angeles, CA

CAREER SUMMARY
Omnichannel growth strategist and creative director managing $10M+ annual marketing budgets.

TOOLS & TECHNOLOGIES
HubSpot, Google Analytics 4, Meta Ads Manager, Figma, Webflow, Mixpanel, Segment, SQL

PORTFOLIO PROJECTS
Global Rebrand & Acquisition Funnel: Scaled DTC customer acquisition by 220% YoY through viral multimedia campaigns.
• Lowered CAC by 45%.

RELEVANT EXPERIENCE
Head of Growth — Apex Media Group | 2021 - Present
• Directed a multidisciplinary creative and performance marketing team of 14.

EDUCATION AND QUALIFICATIONS
UCLA — Bachelor of Arts in Communications & Design | 2016 - 2020

PROFESSIONAL DEVELOPMENT
Reforge Growth Series — Reforge: Completed
Google Ads Search Certification — Google: Completed
"""
        profile = ResumeParser.parse_text_to_profile(resume_text)
        
        self.assertEqual(profile.full_name, "EMILY WATSON")
        self.assertIn("Omnichannel growth strategist", profile.summary)
        self.assertIn("Figma", profile.skills)
        self.assertEqual(len(profile.projects), 1)
        self.assertEqual(len(profile.experience), 1)
        self.assertEqual(len(profile.education), 1)
        self.assertEqual(len(profile.certifications), 2)

    def test_template_rendering_with_all_synonyms(self):
        resume_text = """
ALEX RIVERA
Full Stack Engineer
Email: alex@example.com
Phone: 555-123-4567

CAREER SUMMARY
Full stack developer specialized in modern web applications.

TECH STACK
TypeScript, React, Next.js, Node.js, PostgreSQL, Docker

PORTFOLIO PROJECTS
E-Commerce Platform: High performance online shopping system with Stripe integration.
• Achieved 99.9% uptime.

WORK HISTORY
Software Engineer — WebCraft Studios | 2022 - Present
• Developed responsive client portals.

EDUCATIONAL BACKGROUND
MIT — B.S. in Computer Science | 2018 - 2022

COURSES
Advanced React Patterns — Frontend Masters: Completed
"""
        profile = ResumeParser.parse_text_to_profile(resume_text)
        
        # Test PDF generation in all 4 templates with no errors
        for tmpl in ["modern", "harvard_consulting", "corporate_elite", "tech_specialist"]:
            out_pdf = OUTPUT_DIR / f"Test_Synonym_{tmpl}.pdf"
            out_path = ResumeDocumentGenerator.generate_pdf(profile, str(out_pdf), template_id=tmpl)
            self.assertTrue(out_pdf.exists())
            self.assertGreater(out_pdf.stat().st_size, 1000)


    def test_universal_accounting_finance_parsing(self):
        resume_text = """
MICHAEL CARTER
Senior Financial Analyst & Accountant
Email: michael.carter@example.com
Phone: +1 555-432-8765
Location: Chicago, IL

PROFESSIONAL SUMMARY
Results-driven Senior Financial Analyst with 7+ years of experience in GAAP accounting, financial reporting, budgeting, forecasting, and corporate tax compliance.

AREAS OF EXPERTISE
Accounting & Audit: GAAP, IFRS, Tax Compliance, Auditing, General Ledger, Accounts Payable, Accounts Receivable
Financial Systems: QuickBooks, SAP, Financial Modeling, Excel VBA, Financial Reporting

WORK EXPERIENCE
Senior Accountant — Horizon Financial Services | 2020 - Present
• Prepared monthly GAAP financial statements, tax schedules, and variance analysis reports.
• Automated ledger reconciliations using Excel VBA and QuickBooks.

EDUCATION
University of Illinois — B.S. in Accounting & Finance | 2014 - 2018

LICENSES & CERTIFICATIONS
Certified Public Accountant (CPA) — State Board of Accountancy: Completed
"""
        profile = ResumeParser.parse_text_to_profile(resume_text)

        self.assertEqual(profile.full_name, "MICHAEL CARTER")
        self.assertIn("Senior Financial Analyst", profile.headline)
        self.assertTrue(any("GAAP" in s for s in profile.skills))
        self.assertTrue(any("QuickBooks" in s or "Financial Modeling" in s for s in profile.skills))
        self.assertEqual(len(profile.experience), 1)
        self.assertEqual(profile.experience[0].company, "Horizon Financial Services")
        self.assertEqual(len(profile.education), 1)
        self.assertEqual(len(profile.certifications), 1)


if __name__ == "__main__":
    unittest.main()

