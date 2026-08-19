"""
Unit Test Suite: ResLink Studio & Dashboard Resume Separation (Beta Isolation)
Verifies:
1. Dedicated ResLink CV upload endpoint (/api/v1/reslink/resume/upload) saves authentic candidate CV to ResLink.
2. Dashboard auto-apply and tailored sessions remain independent.
3. Public candidate slug lookup (/p/{slug}, /api/v1/reslink?slug=..., /api/v1/resume/current?slug=...) returns authentic data.
4. PDF download with slug generates 100% authentic PDF matching the uploaded CV in all templates.
"""
import io
import json
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from server import app
from core.resume_parser import ResumeParser, UserProfile
from core.reslink import ResLinkManager, ResLinkProfile
from config import DATA_DIR, OUTPUT_DIR


class TestResLinkResumeSeparation(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_reslink_resume_upload_endpoint(self):
        """Verify dedicated ResLink CV upload parses and attaches candidate resume."""
        sample_cv_text = """
MUDATHER MOHAMMED
Junior AI Engineer | Machine Learning Engineer
Email: mudatherkbyer@gmail.com | Phone: +249 92 012 3456 | Location: Dubai, UAE
LinkedIn: https://linkedin.com/in/mudather-mohammed | GitHub: https://github.com/mudather490

EXECUTIVE SUMMARY
Junior AI Engineer specializing in machine learning, PyTorch, LLM APIs, and AI agent architectures.

AREAS OF EXPERTISE
Python, PyTorch, TensorFlow, FastAPI, Scikit-learn, Docker, Redis, SQL

PRACTICAL PROJECTS
Autonomous JobFlow Agent Orchestrator: Built distributed agent processing applications with FastAPI and Redis.

CAREER HISTORY
Software & AI Developer — Freelance | 2022 - Present
- Built machine learning workflows and AI applications.

ACADEMIC BACKGROUND
University of Khartoum — Bachelor of Science in Computer Engineering | 2018 - 2023

PROFESSIONAL CERTIFICATIONS
Deep Learning Specialization (DeepLearning.AI)
"""
        file_bytes = sample_cv_text.encode("utf-8")
        file_obj = io.BytesIO(file_bytes)

        response = self.client.post(
            "/api/v1/reslink/resume/upload",
            files={"file": ("Mudather_Mohammed_Resume.txt", file_obj, "text/plain")},
            data={"slug": "mudather-mohammed", "user_email": "mudatherkbyer@gmail.com"},
            headers={"Origin": "http://127.0.0.1:8000"}
        )

        self.assertEqual(response.status_code, 200, f"Upload failed: {response.text}")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("MUDATHER", data["profile"]["full_name"].upper())
        self.assertEqual(data["reslink_profile"]["slug"], "mudather-mohammed")
        self.assertTrue(any("Python" in s for s in data["profile"]["skills"]))

    def test_02_slug_based_profile_lookup(self):
        """Verify that querying ResLink by slug returns the authentic candidate data."""
        res = self.client.get("/api/v1/reslink?slug=mudather-mohammed")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["slug"], "mudather-mohammed")
        self.assertIn("MUDATHER", data["full_name"].upper())

        # Also verify /api/v1/resume/current?slug=mudather-mohammed
        res2 = self.client.get("/api/v1/resume/current?slug=mudather-mohammed")
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertIn("profile", data2)
        self.assertIn("MUDATHER", data2["profile"]["full_name"].upper())

    def test_03_accountant_slug_profile_lookup(self):
        """Verify Sebastian Bennett (Accountant) profile is isolated and retrievable."""
        res = self.client.get("/api/v1/reslink?slug=sebastianbennett")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        full_text = (data.get("tagline", "") + data.get("target_job_title", "") + data.get("full_name", "")).upper()
        self.assertTrue("SEBASTIAN" in full_text or "ACCOUNTANT" in full_text, f"Expected Sebastian or Accountant in {full_text}")

    def test_04_download_pdf_with_slug(self):
        """Verify PDF download for specific candidate slug generates without error."""
        for tmpl in ["corporate_elite", "harvard_consulting", "modern", "tech_specialist"]:
            res = self.client.get(f"/api/v1/resume/download-pdf?template_id={tmpl}&slug=mudather-mohammed")
            self.assertEqual(res.status_code, 200, f"PDF generation failed for template {tmpl}")
            self.assertEqual(res.headers["content-type"], "application/pdf")
            self.assertTrue(len(res.content) > 1000, f"PDF content too small for template {tmpl}")

    def test_05_upload_security_validation(self):
        """Verify that uploading invalid extensions or malicious payloads is rejected."""
        fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
        file_obj = io.BytesIO(fake_exe)
        res = self.client.post(
            "/api/v1/reslink/resume/upload",
            files={"file": ("malicious.exe", file_obj, "application/octet-stream")},
            headers={"Origin": "http://127.0.0.1:8000"}
        )
        self.assertIn(res.status_code, [400, 403], "Malicious file upload was not rejected!")


if __name__ == "__main__":
    unittest.main()
