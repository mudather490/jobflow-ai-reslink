import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DATA_DIR, OUTPUT_DIR, get_linkedin_time_filter
from core.resume_parser import ResumeParser, UserProfile
from core.scraper import LinkedInScraper, JobDetails
from core.matcher import JobMatcher
from core.agent import GapQuestioningAgent
from core.tailor import ResumeTailor
from core.pdf_generator import ResumeDocumentGenerator
from core.applier import JobApplier
from core.notifier import NotificationManager


class TestFullJobHunterPipeline(unittest.TestCase):

    def setUp(self):
        self.sample_docx_path = DATA_DIR / "sample_resume.docx"
        ResumeParser.generate_sample_docx(str(self.sample_docx_path))
        self.assertTrue(self.sample_docx_path.exists(), "Sample DOCX must exist")

    def test_stage_1_scraper_and_time_filters(self):
        print("\n[Test 1] Testing Stage 1: Time Filter Calculations & LinkedIn Scraper...")
        from config import get_linkedin_workplace_filter
        self.assertEqual(get_linkedin_time_filter("24h"), "r86400")
        self.assertEqual(get_linkedin_time_filter("4d"), "r345600")
        self.assertEqual(get_linkedin_time_filter("7d"), "r604800")
        self.assertEqual(get_linkedin_time_filter("70d"), "r6048000")
        
        # Test Workplace Filter mappings
        self.assertEqual(get_linkedin_workplace_filter("remote"), "2")
        self.assertEqual(get_linkedin_workplace_filter("hybrid"), "3")
        self.assertEqual(get_linkedin_workplace_filter("on_site"), "1")
        self.assertEqual(get_linkedin_workplace_filter("all"), "")
        print("[OK] Time and Workplace filter mappings verified successfully.")

    def test_stage_2_parser_and_gap_agent(self):
        print("\n[Test 2] Testing Stage 2: Resume Ingestion, Semantic Matcher & Gap Agent...")
        profile = ResumeParser.parse_file(str(self.sample_docx_path))
        self.assertEqual(profile.full_name, "ALEX RIVERA")
        self.assertTrue(len(profile.skills) > 5)

        matcher = JobMatcher()
        mock_job = JobDetails(
            job_id="job-stage-test-101",
            title="Senior AI Backend Engineer",
            company="Anthropic-Scale Innovations",
            location="Remote",
            posted_date="3 hours ago",
            job_url="https://www.linkedin.com/jobs/view/job-stage-test-101",
            description=(
                "We are seeking a Senior AI Backend Engineer.\n"
                "Requirements:\n"
                "- Strong experience with Python, FastAPI, Docker, and PyTorch.\n"
                "- Production background in Kubernetes and Celery task queues.\n"
                "- Experience with GraphRAG, Qdrant, and Redis."
            ),
        )

        initial_report = matcher.evaluate_match(profile, mock_job)
        self.assertIn("Python", initial_report.matched_skills)
        self.assertIn("Kubernetes", initial_report.missing_critical_skills)
        print(f"[OK] Initial ATS Match Score: {initial_report.match_score}%")

        # Agent bridges gap with verified answers
        agent = GapQuestioningAgent(matcher=matcher)
        user_answers = {
            "Kubernetes": "Orchestrated container clusters with Kubernetes and Helm on AWS in freelance work.",
            "Celery": "Architected distributed asynchronous task queues with Celery and Redis."
        }
        updated_profile, updated_report = agent.run_interactive_resolution(
            profile, mock_job, initial_report, user_answers
        )
        self.assertGreater(updated_report.match_score, initial_report.match_score)
        print(f"[OK] Boosted ATS Match Score after Gap Session: {updated_report.match_score}%")

    def test_stage_3_resume_tailor_and_pdf_generation(self):
        print("\n[Test 3] Testing Stage 3: Dynamic Resume Tailoring & PDF Compilation...")
        profile = ResumeParser.parse_file(str(self.sample_docx_path))
        matcher = JobMatcher()
        mock_job = JobDetails(
            job_id="job-stage-test-102",
            title="Lead AI Engineer",
            company="Quantum AI Systems",
            location="San Francisco, CA",
            posted_date="1 day ago",
            job_url="https://www.linkedin.com/jobs/view/job-stage-test-102",
            description="Requirements: Python, FastAPI, PyTorch, Docker, Vector Search.",
        )
        report = matcher.evaluate_match(profile, mock_job)

        # 1. Tailor Profile
        tailor = ResumeTailor(matcher=matcher)
        tailored_profile = tailor.tailor_profile(profile, mock_job, report)
        self.assertIn("Quantum AI Systems", tailored_profile.summary)
        print("[OK] Tailored summary dynamically aligns with target company and role.")

        # 2. Compile DOCX & PDF
        docx_path, pdf_path = ResumeDocumentGenerator.export_tailored_documents(
            tailored_profile, mock_job.title, mock_job.company
        )
        self.assertTrue(Path(docx_path).exists(), "Tailored DOCX must exist")
        self.assertTrue(Path(pdf_path).exists(), "Tailored PDF must exist")
        self.assertGreater(Path(pdf_path).stat().st_size, 1000, "PDF file must not be empty")
        print(f"[OK] Generated DOCX: {docx_path}")
        print(f"[OK] Generated PDF: {pdf_path} (Size: {Path(pdf_path).stat().st_size} bytes)")

    def test_stage_4_applier_and_triple_channel_notifications(self):
        print("\n[Test 4] Testing Stage 4: Auto-Apply Session Manager & Triple-Channel Notifications...")
        profile = ResumeParser.parse_file(str(self.sample_docx_path))
        matcher = JobMatcher()
        mock_job = JobDetails(
            job_id="job-stage-test-103",
            title="AI Systems Architect",
            company="Apex Automation",
            location="Remote",
            posted_date="Just now",
            job_url="https://www.linkedin.com/jobs/view/job-stage-test-103",
            description="Requirements: Python, Docker, FastAPI, Qdrant, Machine Learning.",
        )
        report = matcher.evaluate_match(profile, mock_job)
        tailor = ResumeTailor(matcher=matcher)
        tailored_profile = tailor.tailor_profile(profile, mock_job, report)
        docx_path, pdf_path = ResumeDocumentGenerator.export_tailored_documents(
            tailored_profile, mock_job.title, mock_job.company
        )

        # 1. Test Application Record Persistence
        record = JobApplier.apply_or_simulate(
            profile=tailored_profile,
            job=mock_job,
            match_report=report,
            pdf_path=pdf_path,
            docx_path=docx_path,
            dry_run=True,
        )
        self.assertEqual(record.status, "Dry-Run Validated")
        self.assertTrue(JobApplier.HISTORY_FILE.exists())
        print(f"[OK] Application record logged: ID {record.application_id}")

        # 2. Test Triple-Channel Notifications
        notifier = NotificationManager(
            recipient_email="candidate@domain.com",
            whatsapp_phone="+15551234567",
            telegram_chat_id="test_tg_chat_123",
        )

        # Channel 1: Email
        email_res = notifier.send_email(
            job_title=mock_job.title,
            company=mock_job.company,
            match_score=report.match_score,
            job_url=mock_job.job_url,
            pdf_path=pdf_path,
        )
        self.assertIn(email_res.get("status"), ["success", "simulated_success"])
        print(f"[OK] Email Channel formatted with PDF attachment: {email_res.get('status')}")

        # Channel 2: WhatsApp
        wa_res = notifier.send_whatsapp(
            job_title=mock_job.title,
            company=mock_job.company,
            match_score=report.match_score,
            job_url=mock_job.job_url,
        )
        self.assertIn(wa_res.get("status"), ["success", "simulated_success"])
        print(f"[OK] WhatsApp Channel formatted: {wa_res.get('status')}")

        # Channel 3: Telegram
        tg_res = notifier.send_telegram(
            job_title=mock_job.title,
            company=mock_job.company,
            match_score=report.match_score,
            job_url=mock_job.job_url,
            pdf_path=pdf_path,
        )
        self.assertIn(tg_res.get("status"), ["success", "simulated_success"])
        print(f"[OK] Telegram Channel formatted with document payload: {tg_res.get('status')}")


if __name__ == "__main__":
    unittest.main()
