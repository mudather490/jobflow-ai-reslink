import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.applier import JobApplier
from core.scraper import JobDetails
from core.resume_parser import ResumeParser
from core.excel_exporter import CompanyIntelligenceExcelExporter

def test_export_and_batch_id():
    print("[+] Testing Batch Auto-Apply, JSON Exporter & Single-Batch Filtering...")

    # Parse profile
    profile = ResumeParser.parse_text_to_profile("Mudather Mohammed\nPython Engineer with FastAPI, Docker, PyTorch")

    # Create dummy jobs
    job1 = JobDetails(job_id="j1", title="AI Engineer", company="AI Corp", location="Remote", posted_date="1d", job_url="http://ex1.com", description="Python, PyTorch", is_easy_apply=True)
    job2 = JobDetails(job_id="j2", title="Backend Lead", company="Cloud Inc", location="Remote", posted_date="1d", job_url="http://ex2.com", description="Python, Docker, FastAPI", is_easy_apply=True)

    # Run batch auto-apply
    res = JobApplier.batch_auto_apply(
        jobs=[job1, job2],
        profile=profile,
        candidate_info=None,
        min_score_threshold=50.0
    )

    batch_id = res.get("batch_id")
    print(f"✓ Generated Batch ID: {batch_id}")
    print(f"✓ Applied Count: {res.get('applied_count')}")

    # Load history and check batch_id
    history = JobApplier.load_history()
    batch_records = [a for a in history if a.get("batch_id") == batch_id]
    print(f"✓ Records found for {batch_id}: {len(batch_records)}")

    # Test JSON export
    json_path = CompanyIntelligenceExcelExporter.export_to_json(batch_records)
    print(f"✓ JSON Export created at: {json_path} (File Exists: {json_path.exists()})")

    assert len(batch_records) >= 1, "Failed to persist batch records with batch_id"
    assert json_path.exists(), "Failed to create JSON export"
    print("✅ All Batch Export & JSON Tests Passed Successfully!")

if __name__ == "__main__":
    test_export_and_batch_id()
