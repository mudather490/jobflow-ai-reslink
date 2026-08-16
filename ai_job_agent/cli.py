import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DATA_DIR, OUTPUT_DIR
from core.scraper import LinkedInScraper, JobSummary, JobDetails
from core.resume_parser import ResumeParser, UserProfile
from core.matcher import JobMatcher, MatchReport
from core.agent import GapQuestioningAgent
from core.tailor import ResumeTailor
from core.pdf_generator import ResumeDocumentGenerator
from core.applier import JobApplier
from core.notifier import NotificationManager

console = Console()


def print_banner():
    banner_text = (
        "[bold cyan]╔═══════════════════════════════════════════════════════════════════════════════════╗[/bold cyan]\n"
        "[bold cyan]║[/bold cyan]   [bold white]⚡ AUTONOMOUS AI JOB HUNTER: DISCOVERY, ATS TAILOR, PDF & NOTIFICATIONS ⚡[/bold white]   [bold cyan]║[/bold cyan]\n"
        "[bold cyan]╚═══════════════════════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    console.print(banner_text)


def ensure_sample_resume() -> str:
    resume_path = DATA_DIR / "sample_resume.docx"
    if not resume_path.exists():
        console.print(f"[dim]Generating sample resume at: {resume_path}[/dim]")
        ResumeParser.generate_sample_docx(str(resume_path))
    return str(resume_path)


def display_jobs_table(jobs: list[JobSummary]):
    table = Table(title="🔍 Live LinkedIn Job Postings", show_lines=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Job Title", style="bold green", min_width=25)
    table.add_column("Company", style="yellow", min_width=20)
    table.add_column("Location", style="blue", min_width=18)
    table.add_column("Posted", style="cyan", min_width=12)
    table.add_column("Direct Link", style="underline blue", min_width=30)

    for idx, job in enumerate(jobs, start=1):
        table.add_row(
            str(idx),
            job.title,
            job.company,
            job.location,
            job.posted_date,
            job.job_url,
        )

    console.print(table)


def display_match_report(report: MatchReport):
    score_color = "green" if report.match_score >= 80 else ("yellow" if report.match_score >= 60 else "red")
    
    panel_content = (
        f"[bold]Target Role:[/bold] {report.job_title} at [bold yellow]{report.company}[/bold yellow]\n"
        f"[bold]ATS Match Score:[/bold] [{score_color}]{report.match_score}%[/{score_color}]\n\n"
        f"[bold green]✓ Matched Competencies ({len(report.matched_skills)}):[/bold green] "
        f"{', '.join(report.matched_skills) if report.matched_skills else 'None'}\n\n"
        f"[bold red]✗ Missing Requirements ({len(report.missing_critical_skills)}):[/bold red] "
        f"{', '.join(report.missing_critical_skills) if report.missing_critical_skills else 'None'}\n\n"
        f"[bold cyan]ℹ Assessment:[/bold cyan] {report.experience_assessment}"
    )

    console.print(Panel(panel_content, title="📊 Match Analysis Report", border_style="bold cyan"))


def run():
    print_banner()

    # ── STEP 1: Ingest Resume ──
    default_resume_path = ensure_sample_resume()
    resume_file = Prompt.ask(
        "\n[bold green]📁 Enter path to your Base Resume (.docx / .pdf / .txt)[/bold green]",
        default=default_resume_path,
    )

    with console.status("[bold green]Parsing Resume Document...[/bold green]"):
        try:
            profile = ResumeParser.parse_file(resume_file)
            console.print(f"[bold green]✓ Resume Ingested:[/bold green] {profile.full_name} ({len(profile.skills)} skills extracted)")
        except Exception as e:
            console.print(f"[bold red]Failed to parse resume:[/bold red] {e}")
            return

    # ── STEP 2: Universal Job Search ──
    scraper = LinkedInScraper()
    keywords = Prompt.ask(
        "\n[bold cyan]🔎 Enter ANY Job Title / Keywords (e.g. AI Engineer, Product Manager, Graphic Designer)[/bold cyan]",
        default="AI Engineer",
    )
    location = Prompt.ask("[bold cyan]📍 Location (e.g. Remote, San Francisco, London)[/bold cyan]", default="Remote")
    date_filter = Prompt.ask(
        "[bold cyan]⏱ Time Filter (24h, 4d, 7d, 14d, 30d, 70d, or all)[/bold cyan]",
        default="24h",
    )
    limit = int(Prompt.ask("[bold cyan]🔢 Max Jobs to Fetch[/bold cyan]", default="5"))

    with console.status(f"[bold cyan]Searching LinkedIn for '{keywords}' in '{location}' ({date_filter})...[/bold cyan]"):
        jobs = scraper.search_jobs(keywords=keywords, location=location, date_filter=date_filter, limit=limit)

    if not jobs:
        console.print(f"[yellow]No live jobs returned for '{keywords}' in {date_filter}. Creating a simulated posting to test the pipeline.[/yellow]")
        selected_job = JobDetails(
            job_id="live-demo-101",
            title=f"Senior {keywords}",
            company="NextGen Intelligence Inc",
            location=location,
            posted_date="2 hours ago",
            job_url="https://www.linkedin.com/jobs/view/live-demo-101",
            description=(
                f"We are hiring a Senior {keywords} to lead critical initiatives.\n"
                "Requirements:\n"
                f"- 3+ years experience as a {keywords}.\n"
                "- Strong proficiency in Python, FastAPI, Docker, and Kubernetes.\n"
                "- Experience with Celery, GraphRAG, and Agile project delivery."
            ),
        )
    else:
        display_jobs_table(jobs)
        choice = int(Prompt.ask("\n[bold green]👉 Select Job # to Process[/bold green]", choices=[str(i) for i in range(1, len(jobs) + 1)], default="1"))
        chosen_summary = jobs[choice - 1]

        with console.status(f"[bold green]Fetching full job description for '{chosen_summary.title}'...[/bold green]"):
            selected_job = scraper.get_job_details(chosen_summary.job_id)
            if not selected_job:
                selected_job = JobDetails(
                    job_id=chosen_summary.job_id,
                    title=chosen_summary.title,
                    company=chosen_summary.company,
                    location=chosen_summary.location,
                    posted_date=chosen_summary.posted_date,
                    job_url=chosen_summary.job_url,
                    description=f"{chosen_summary.title} at {chosen_summary.company}.",
                )

    # ── STEP 3: ATS Matching ──
    matcher = JobMatcher()
    match_report = matcher.evaluate_match(profile, selected_job)
    display_match_report(match_report)

    # ── STEP 4: Interactive Gap-Questioning Agent ──
    if match_report.missing_critical_skills:
        if Confirm.ask("\n[bold yellow]🤖 Would you like the AI Agent to help bridge your missing requirements?[/bold yellow]", default=True):
            agent = GapQuestioningAgent(matcher=matcher)
            questions = agent.generate_gap_questions(profile, selected_job, match_report)

            console.print("\n[bold cyan]─── INTERACTIVE GAP QUESTIONING SESSION ───[/bold cyan]")
            console.print("[dim]If you have experience in any of these from freelance work or projects, type a brief sentence. Otherwise type 'skip'.[/dim]\n")

            answers = {}
            for q in questions:
                console.print(f"[bold yellow]Question:[/bold yellow] {q.question_text}")
                ans = Prompt.ask("[bold green]Your Experience[/bold green]", default="skip")
                if ans.lower() not in ["skip", "no", "n", ""]:
                    answers[q.skill_name] = ans
                console.print()

            if answers:
                with console.status("[bold green]Updating Profile & Recalculating Match Score...[/bold green]"):
                    profile, match_report = agent.run_interactive_resolution(profile, selected_job, match_report, answers)

                console.print("\n[bold green]🎉 Profile Updated with Verified Experience![/bold green]")
                display_match_report(match_report)

    # ── STEP 5: Dynamic Resume Tailoring & PDF Compilation ──
    console.print("\n[bold cyan]─── STAGE 3: RESUME TAILORING & PDF COMPILATION ───[/bold cyan]")
    with console.status("[bold green]Tailoring Summary & Experience Bullets with XYZ Formula...[/bold green]"):
        tailor = ResumeTailor(matcher=matcher)
        tailored_profile = tailor.tailor_profile(profile, selected_job, match_report)

    with console.status("[bold green]Compiling Tailored DOCX and ATS-Compliant PDF Documents...[/bold green]"):
        docx_path, pdf_path = ResumeDocumentGenerator.export_tailored_documents(
            tailored_profile, selected_job.title, selected_job.company
        )

    console.print(f"[bold green]✓ Tailored DOCX Created:[/bold green] {docx_path}")
    console.print(f"[bold green]✓ Tailored PDF Compiled:[/bold green] {pdf_path}")

    # ── STEP 6: Auto-Apply / Application Audit ──
    console.print("\n[bold cyan]─── STAGE 4: AUTONOMOUS APPLICATION EXECUTION ───[/bold cyan]")
    dry_run = not Confirm.ask("[bold yellow]Proceed with Live Application Submission? (No = Dry-Run Audit Mode)[/bold yellow]", default=False)

    with console.status("[bold green]Processing Application Payload & Saving Audit Record...[/bold green]"):
        record = JobApplier.apply_or_simulate(
            profile=tailored_profile,
            job=selected_job,
            match_report=match_report,
            pdf_path=pdf_path,
            docx_path=docx_path,
            dry_run=dry_run,
        )

    console.print(f"[bold green]✓ Application Status:[/bold green] [bold yellow]{record.status}[/bold yellow] (ID: {record.application_id})")

    # ── STEP 7: Triple-Channel Notifications (Email, WhatsApp, Telegram) ──
    console.print("\n[bold cyan]─── TRIPLE-CHANNEL NOTIFICATION DISPATCHER ───[/bold cyan]")
    notifier = NotificationManager()

    # 1. Email Channel
    if Confirm.ask("📧 Send Application Receipt & Tailored PDF to Email?", default=True):
        email_addr = Prompt.ask("   Enter Recipient Email Address", default=profile.contact.email or "candidate@email.com")
        with console.status(f"Sending email notification to {email_addr}..."):
            email_res = notifier.send_email(
                job_title=selected_job.title,
                company=selected_job.company,
                match_score=match_report.match_score,
                job_url=selected_job.job_url,
                pdf_path=pdf_path,
                recipient=email_addr,
            )
            console.print(f"   [bold green]✓ Email Notification:[/bold green] {email_res.get('status')} ({email_addr})")

    # 2. WhatsApp Channel
    if Confirm.ask("📱 Send Instant Notification to WhatsApp?", default=True):
        phone_num = Prompt.ask("   Enter WhatsApp Phone Number (with country code, e.g. +1234567890)", default=profile.contact.phone or "+15553456789")
        with console.status(f"Sending WhatsApp notification to {phone_num}..."):
            wa_res = notifier.send_whatsapp(
                job_title=selected_job.title,
                company=selected_job.company,
                match_score=match_report.match_score,
                job_url=selected_job.job_url,
                phone_number=phone_num,
            )
            console.print(f"   [bold green]✓ WhatsApp Notification:[/bold green] {wa_res.get('status')} ({phone_num})")

    # 3. Telegram Channel
    if Confirm.ask("✈️ Send Telegram Notification & Upload PDF to Telegram Chat?", default=True):
        chat_id = Prompt.ask("   Enter Telegram Chat ID (or username)", default="user_telegram_id")
        with console.status(f"Sending Telegram document & message to {chat_id}..."):
            tg_res = notifier.send_telegram(
                job_title=selected_job.title,
                company=selected_job.company,
                match_score=match_report.match_score,
                job_url=selected_job.job_url,
                pdf_path=pdf_path,
                chat_id=chat_id,
            )
            console.print(f"   [bold green]✓ Telegram Notification:[/bold green] {tg_res.get('status')} ({chat_id})")

    console.print("\n[bold green]✨ END-TO-END PIPELINE COMPLETED SUCCESSFULLY! ✨[/bold green]")


if __name__ == "__main__":
    run()
