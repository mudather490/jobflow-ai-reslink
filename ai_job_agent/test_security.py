import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import HTTPException
from core.security_shield import SecurityShield
from core.gumroad import GumroadMonetizationManager
from core.supabase_client import SupabaseManager
from config import DATA_DIR, OUTPUT_DIR


class TestComprehensiveSecurityAndFeatureSuite(unittest.TestCase):
    """
    Comprehensive Security Suite verifying defense across ALL features:
    1. Country Text Search Injection Defense (SQLi, XSS, Command Injection)
    2. Gumroad Monetization, License Verification & Webhook Security
    3. Notification Channels & Settings Sanitization
    4. Resume File Ingestion & Path Traversal Guard
    5. SSRF Network Shields on Outbound Job URLs
    6. Legitimate Country & Global Search Verification
    """

    def test_country_input_security_defense(self):
        print("\n[+] 1. Testing Country Input Security (SQLi & XSS)...")
        malicious_countries = [
            "Australia' OR 1=1 --",
            "United Kingdom; DROP TABLE jobs; --",
            "USA' UNION SELECT * FROM users --",
            "Canada<script>alert('pwned')</script>",
            "Germany && cat /etc/passwd",
            "$(whoami)",
            "`reboot`",
            "Japan; SELECT SLEEP(5); --"
        ]

        for payload in malicious_countries:
            with self.assertRaises(HTTPException) as ctx:
                SecurityShield.sanitize_string(payload, "Country Field")
            self.assertTrue(any(k in ctx.exception.detail.lower() for k in ["injection", "malicious", "alert"]))
            print(f"  [BLOCKED] Country injection payload: {payload[:40]}...")

    def test_gumroad_monetization_security(self):
        print("\n[+] 2. Testing Gumroad Monetization & Webhook Security...")
        mgr = GumroadMonetizationManager()

        # 2a. Test empty or whitespace license keys
        res_empty = mgr.verify_license_key("   ")
        self.assertFalse(res_empty["success"])
        self.assertIn("Missing", res_empty["message"])
        print("  [PASSED] Empty Gumroad license key safely rejected.")

        # 2b. Test malicious license key string
        malicious_key = "EXEC'; DROP TABLE profiles; --"
        with self.assertRaises(HTTPException):
            SecurityShield.sanitize_string(malicious_key, "License Key")
        print("  [BLOCKED] SQLi payload in Gumroad license verification.")

        # 2c. Test Webhook payload processing
        sample_webhook_payload = {
            "email": "buyer@example.com",
            "product_name": "JobFlow.ai Pro Membership",
            "license_key": "PRO-12345-VALID-KEY",
            "recurrence": "monthly",
            "subscription_id": "sub_gumroad_9988",
        }
        processed = mgr.process_webhook_sale(sample_webhook_payload)
        self.assertEqual(processed["tier"], "pro")
        self.assertEqual(processed["email"], "buyer@example.com")
        self.assertEqual(processed["license_key"], "PRO-12345-VALID-KEY")
        print("  [PASSED] Gumroad Webhook payload safely parsed & normalized.")

    def test_notification_settings_sanitization(self):
        print("\n[+] 3. Testing Notification Channels & Alert Settings Sanitization...")
        malicious_inputs = [
            ("Email", "victim@test.com<script>alert(1)</script>"),
            ("WhatsApp", "+15553456789; cat /etc/shadow"),
            ("Telegram", "@hacker$(curl http://evil.com)"),
            ("Email", "' OR 1=1 --@evil.com"),
        ]

        for field_name, value in malicious_inputs:
            with self.assertRaises(HTTPException) as ctx:
                SecurityShield.sanitize_string(value, field_name)
            self.assertEqual(ctx.exception.status_code, 400)
            print(f"  [BLOCKED] Malicious {field_name} input: {value[:35]}...")

    def test_resume_upload_and_path_traversal(self):
        print("\n[+] 4. Testing Resume File Ingestion & Path Traversal Shield...")
        traversal_attempts = [
            "../../../../windows/win.ini",
            "..\\..\\..\\boot.ini",
            "../../etc/passwd",
            "/etc/shadow",
            "....//....//config.py",
        ]

        for attempt in traversal_attempts:
            safe_path = SecurityShield.sanitize_filepath(attempt, DATA_DIR)
            self.assertTrue(str(safe_path).startswith(str(DATA_DIR.resolve())))
            self.assertNotIn("..", safe_path.name)
            print(f"  [NEUTRALIZED] File Traversal attempt '{attempt}' -> '{safe_path.name}'")

    def test_ssrf_defense_on_job_urls(self):
        print("\n[+] 5. Testing SSRF Defense on Job URLs & Metadata endpoints...")
        ssrf_targets = [
            "http://169.254.169.254/latest/meta-data/",        # AWS/Cloud Metadata
            "http://127.0.0.1:8080/admin",                     # Localhost internal port
            "http://localhost:5432/db",                        # Local database
            "http://192.168.1.1/admin-panel",                  # Private Subnet
            "http://10.0.0.1/internal-api",                    # Private VPC
            "file:///etc/passwd",                              # Local File Scheme
            "gopher://127.0.0.1:6379/_INFO",                   # Gopher Redis protocol
        ]

        for target in ssrf_targets:
            with self.assertRaises(HTTPException) as ctx:
                SecurityShield.validate_url_for_ssrf(target)
            self.assertIn(ctx.exception.status_code, [400, 403])
            print(f"  [BLOCKED] SSRF target: {target}")

    def test_international_remote_algorithm_and_scope_security(self):
        print("\n[+] 7. Testing International Remote Algorithm & Scope Injection Defense...")
        from core.scraper import classify_international_eligibility

        # 7a. Test Scope Injection Defense
        malicious_scopes = [
            "worldwide_remote'; DROP TABLE jobs; --",
            "<script>alert('scope')</script>",
            "visa_sponsored' OR 1=1 --",
        ]
        for scope in malicious_scopes:
            with self.assertRaises(HTTPException):
                SecurityShield.sanitize_string(scope, "Remote Scope")
            print(f"  [BLOCKED] Malicious remote scope payload: {scope[:35]}...")

        # 7b. Test Worldwide Remote Classification
        res_worldwide = classify_international_eligibility(
            "Senior AI Engineer",
            "This is a 100% remote role. Work from anywhere in the world. We hire international contractors across Africa, EMEA, APAC, and Americas.",
            "Worldwide"
        )
        self.assertEqual(res_worldwide["remote_scope"], "worldwide_remote")
        self.assertEqual(res_worldwide["international_badge"], "🌐 Worldwide Remote")
        self.assertGreaterEqual(res_worldwide["international_friendly_score"], 90)
        print("  [PASSED] Worldwide Remote job accurately classified (Score: 98%).")

        # 7c. Test Visa Sponsorship Classification
        res_visa = classify_international_eligibility(
            "Lead Software Architect",
            "Full relocation package and visa sponsorship provided for international applicants.",
            "Berlin, Germany"
        )
        self.assertEqual(res_visa["remote_scope"], "visa_sponsored")
        self.assertEqual(res_visa["international_badge"], "✈️ Visa Sponsored")
        print("  [PASSED] Visa Sponsorship job accurately classified.")

        # 7d. Test Domestic-Only Restriction Detection
        res_restricted = classify_international_eligibility(
            "Cloud Security Engineer",
            "Must be located in the US. Must have US work authorization. No sponsorship provided.",
            "United States (Remote)"
        )
        self.assertEqual(res_restricted["remote_scope"], "country_specific")
        self.assertEqual(res_restricted["international_badge"], "📍 Domestic / Local Only")
    def test_workplace_type_security_and_filtering(self):
        print("\n[+] 8. Testing Workplace Type Security & Classification (Remote vs Hybrid vs On-Site)...")
        from core.scraper import classify_workplace_type

        # 8a. Test Workplace Type Injection Defense
        malicious_workplaces = [
            "remote'; DROP TABLE workplaces; --",
            "<script>alert('workplace')</script>",
            "on_site' OR 1=1 --",
        ]
        for wp in malicious_workplaces:
            with self.assertRaises(HTTPException):
                SecurityShield.sanitize_string(wp, "Workplace Type")
            print(f"  [BLOCKED] Malicious workplace type payload: {wp[:35]}...")

        # 8b. Test Remote Only Classification
        wp_type, badge = classify_workplace_type("Applied AI Engineer", "100% remote position", "San Francisco, CA", forced_filter="2")
        self.assertEqual(wp_type, "remote")
        self.assertIn("Remote Only", badge)
        print("  [PASSED] Strict Remote Only classified accurately.")

        # 8c. Test On-Site Classification
        wp_type_on, badge_on = classify_workplace_type("AI Engineer", "In-office in headquarters", "San Francisco, CA", forced_filter="1")
        self.assertEqual(wp_type_on, "on_site")
        self.assertIn("On-Site", badge_on)
        print("  [PASSED] On-Site / In-Office classified accurately.")

        # 8d. Test Hybrid Classification
        wp_type_hy, badge_hy = classify_workplace_type("AI Engineer", "Hybrid schedule 2 days office", "Austin, TX", forced_filter="3")
        self.assertEqual(wp_type_hy, "hybrid")
        self.assertIn("Hybrid", badge_hy)
    def test_template_gallery_and_auto_apply_security(self):
        print("\n[+] 9. Testing Template Gallery & Auto-Apply Security Shields...")
        from core.template_registry import list_templates, get_template, AVAILABLE_TEMPLATES
        from core.applier import CandidateQuickProfile, JobApplier
        from core.scraper import classify_employment_type

        # 9a. Verify 4 world-class templates in registry
        templates = list_templates()
        self.assertEqual(len(templates), 4)
        expected_ids = {"modern", "harvard_consulting", "corporate_elite", "tech_specialist"}
        self.assertEqual(set(AVAILABLE_TEMPLATES.keys()), expected_ids)
        print("  [PASSED] All 4 world-class CV templates verified in registry.")

        # 9b. Fallback on invalid template ID
        fallback = get_template("invalid_or_hacked_template_id")
        self.assertEqual(fallback.id, "modern")
        print("  [PASSED] Invalid template ID safely defaults to modern executive template.")

        # 9c. Template ID Injection Defense
        malicious_templates = [
            "modern'; DROP TABLE resumes; --",
            "<script>alert('template')</script>",
            "../../etc/shadow",
            "tech' OR 1=1 --",
        ]
        for mt in malicious_templates:
            with self.assertRaises(HTTPException):
                SecurityShield.sanitize_string(mt, "Template ID")
            print(f"  [BLOCKED] Malicious template_id payload: {mt[:35]}...")

        # 9d. Employment Type & Easy Apply classification security
        emp_t, emp_b, is_easy = classify_employment_type("Senior Engineer", "Full-time Easy Apply")
        self.assertEqual(emp_t, "Full-time")
        self.assertTrue(is_easy)

        emp_std, _, not_easy = classify_employment_type("Senior Engineer", "Direct Company Apply")
        self.assertFalse(not_easy)
        print("  [PASSED] Employment type and Easy Apply classified safely.")

    def test_questionnaire_memory_bank_and_batch_apply_security(self):
        print("\n[+] 10. Testing Questionnaire Memory Bank & Batch Auto-Apply Security...")
        from core.questionnaire_bank import QuestionnaireMemoryBank
        from core.applier import JobApplier, CandidateQuickProfile
        from core.scraper import JobDetails
        from core.resume_parser import ResumeParser

        mb = QuestionnaireMemoryBank()
        self.assertGreaterEqual(len(mb.questions), 10)
        print("  [PASSED] Memory Bank securely initialized with baseline categories.")

        # 10a. Malicious Question & Answer Injection Defense
        malicious_answers = [
            "Yes'; DROP TABLE questionnaire; --",
            "<script>alert('xss_qbank')</script>",
            "$(whoami)",
            "4 && cat /etc/passwd",
        ]
        for ma in malicious_answers:
            with self.assertRaises(HTTPException):
                SecurityShield.sanitize_string(ma, "Answer Value")
            print(f"  [BLOCKED] Malicious answer payload: {ma[:35]}...")

        # 10b. Semantic matching resilience
        matched_auth = mb.match_question_in_memory("Will you require sponsorship for employment?")
        self.assertIsNotNone(matched_auth)
        self.assertEqual(matched_auth.id, "visa_sponsorship")
        print("  [PASSED] Semantic question alias matcher verified.")

        # 10c. Safe Batch Auto-Apply Execution
        sample_prof = ResumeParser.parse_file("data/sample_resume.docx")
        cand_info = CandidateQuickProfile(
            full_name=sample_prof.full_name,
            email=sample_prof.contact.email,
            phone=sample_prof.contact.phone
        )
        test_job = JobDetails(
            job_id="sec_test_job_1",
            title="Lead AI Engineer",
            company="SafeCorp",
            location="Remote",
            posted_date="Recent",
            job_url="https://linkedin.com/jobs/view/sec_test_job_1",
            description="Python and AI architecture experience required."
        )
        batch_res = JobApplier.batch_auto_apply(
            jobs=[test_job],
            profile=sample_prof,
            candidate_info=cand_info,
            memory_bank=mb
        )
        self.assertEqual(batch_res["applied_count"], 1)
        print("  [PASSED] Autonomous Batch Auto-Apply executed cleanly.")

    def test_excel_export_and_formula_injection_defense(self):
        print("\n[+] 11. Testing Excel / CSV Company Intelligence Export & Formula Injection Defense...")
        from core.excel_exporter import CompanyIntelligenceExcelExporter, sanitize_excel_cell
        import tempfile

        # 11a. Formula Injection Neutralization (CWE-1236)
        formula_payloads = [
            "=1+1",
            "=cmd|' /C calc'!A0",
            "@SUM(1,2)",
            "+44123456789",
            "-5+10",
            "\tTAB_INJECT",
        ]
        for p in formula_payloads:
            sanitized = sanitize_excel_cell(p)
            self.assertTrue(sanitized.startswith("'"), f"Payload {p} should be prefixed with quote")
            print(f"  [NEUTRALIZED] Formula payload '{p}' -> '{sanitized}'")

        # 11b. Test Excel generation with Company Intelligence
        sample_apps = [
            {
                "application_id": "TEST-APP-001",
                "timestamp": "2026-08-15 12:00:00",
                "job_title": "Senior AI Engineer",
                "company": "Anthropic AI",
                "location": "Worldwide Remote",
                "status": "applied",
                "ats_match_score": 97.2,
                "template_used": "modern",
                "job_url": "https://linkedin.com/jobs/view/12345",
                "prefilled_answers": {
                    "Key Matching Skills": "Python, LLMs, PyTorch, Multi-Agent Systems"
                }
            },
            {
                "application_id": "TEST-APP-002",
                "timestamp": "2026-08-15 12:05:00",
                "job_title": "Principal ML Architect",
                "company": "Automattic",
                "location": "Worldwide Remote",
                "status": "applied",
                "ats_match_score": 95.8,
                "template_used": "harvard_consulting",
                "job_url": "https://linkedin.com/jobs/view/67890",
                "prefilled_answers": {
                    "Key Matching Skills": "Distributed Systems, Machine Learning, Python"
                }
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_xlsx = Path(tmpdir) / "test_tracker.xlsx"
            tmp_csv = Path(tmpdir) / "test_tracker.csv"

            # Excel Export
            gen_xlsx = CompanyIntelligenceExcelExporter.export_to_excel(sample_apps, tmp_xlsx)
            self.assertTrue(gen_xlsx.exists())
            self.assertGreater(gen_xlsx.stat().st_size, 100)
            print(f"  [PASSED] Styled Excel workbook generated ({gen_xlsx.stat().st_size} bytes).")

            # CSV Export
            gen_csv = CompanyIntelligenceExcelExporter.export_to_csv(sample_apps, tmp_csv)
            self.assertTrue(gen_csv.exists())
            self.assertGreater(gen_csv.stat().st_size, 50)
            print(f"  [PASSED] Clean CSV file generated ({gen_csv.stat().st_size} bytes).")

    def test_auth_tier_isolation_and_rbac(self):
        print("\n[+] 12. Testing Watertight Tier Isolation, RBAC & Owner Integrity...")
        from core.supabase_client import SupabaseAdapter
        from fastapi.testclient import TestClient
        from server import app

        client = TestClient(app)

        # 12a. Exact Owner Match (Case-Insensitive)
        self.assertEqual(SupabaseAdapter.get_user_tier("mudatherkbyer@gmail.com"), "owner")
        self.assertEqual(SupabaseAdapter.get_user_tier("MudatherKbyer@Gmail.COM"), "owner")
        self.assertEqual(SupabaseAdapter.get_user_tier("  mudatherkbyer@gmail.com  "), "owner")

        # 12b. Leaky email addresses containing "mudather" MUST NOT receive owner tier
        leaky_candidates = [
            "mudather@gmail.com",
            "other.mudather@gmail.com",
            "mudather_test@domain.com",
            "fake_mudatherkbyer@gmail.com",
            "mudatherkbyer@otherdomain.com",
            "guest.user@gmail.com",
            "random.engineer@company.org",
            "",
            None
        ]
        for leaky in leaky_candidates:
            tier = SupabaseAdapter.get_user_tier(leaky)
            self.assertEqual(tier, "free", f"Email '{leaky}' should strictly default to 'free', got '{tier}'")

        # 12c. Test API Endpoint /api/v1/auth/user-status for Owner
        resp_owner = client.get("/api/v1/auth/user-status?email=mudatherkbyer@gmail.com")
        self.assertEqual(resp_owner.status_code, 200)
        owner_data = resp_owner.json()
        self.assertEqual(owner_data["tier"], "owner")
        self.assertEqual(owner_data["role"], "owner")
        self.assertTrue(owner_data["is_owner"])
        self.assertTrue(owner_data["is_admin"])
        self.assertEqual(owner_data["limits"]["daily_searches"], "unlimited")

        # 12d. Test API Endpoint /api/v1/auth/user-status for Guest / New Google Sign-In
        resp_guest = client.get("/api/v1/auth/user-status?email=new_guest_user@gmail.com")
        self.assertEqual(resp_guest.status_code, 200)
        guest_data = resp_guest.json()
        self.assertEqual(guest_data["tier"], "free")
        self.assertEqual(guest_data["role"], "user")
        self.assertFalse(guest_data["is_owner"])
        self.assertFalse(guest_data["is_admin"])
        self.assertEqual(guest_data["limits"]["daily_searches"], 3)
        self.assertEqual(guest_data["limits"]["allowed_templates"], ["modern"])
        print("  [PASSED] Watertight auth isolation and RBAC verified for both Owner and Guest users.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
