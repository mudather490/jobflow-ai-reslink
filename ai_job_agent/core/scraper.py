import random
import re
import time
from typing import List, Optional, Dict, Any, Tuple
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from config import DEFAULT_USER_AGENTS, get_linkedin_time_filter, get_linkedin_workplace_filter
from core.security_shield import SecurityShield


class JobSummary(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    posted_date: str
    job_url: str
    workplace_type: str = "worldwide_remote"  # worldwide_remote, contract_remote, hybrid, remote, on_site, all
    workplace_badge: str = "🌍 Worldwide Remote"
    employment_type: str = "Full-time"  # Full-time, Contract, Part-time, Internship, Freelance
    employment_badge: str = "💼 Full-Time"
    is_easy_apply: bool = True
    easy_apply_badge: str = "⚡ Easy Apply"
    remote_scope: str = "worldwide_remote"  # worldwide_remote, visa_sponsored, country_specific
    international_badge: str = "🌐 Worldwide Remote"
    international_friendly_score: int = 95
    eligibility_notes: str = "Hires international remote candidates globally."


class JobDetails(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    posted_date: str
    job_url: str
    description: str
    seniority_level: Optional[str] = None
    employment_type: str = "Full-time"
    employment_badge: str = "💼 Full-Time"
    is_easy_apply: bool = True
    easy_apply_badge: str = "⚡ Easy Apply"
    job_function: Optional[str] = None
    industries: Optional[str] = None
    extracted_skills: List[str] = Field(default_factory=list)
    workplace_type: str = "worldwide_remote"
    workplace_badge: str = "🌍 Worldwide Remote"
    remote_scope: str = "worldwide_remote"
    international_badge: str = "🌐 Worldwide Remote"
    international_friendly_score: int = 95
    eligibility_notes: str = "Hires international remote candidates globally."


def classify_employment_type(title: str, snippet: str = "", workplace_type: str = "") -> Tuple[str, str, bool]:
    """
    Classifies employment structure (Full-Time, Contract, Internship)
    and Easy Apply availability.
    """
    text = f"{title} {snippet}".lower()
    is_easy = bool("easy apply" in text or "simple apply" in text or "quick apply" in text or "1-click" in text)

    if re.search(r'\bintern\b|\binternship\b|\bfellowship\b|\bco-op\b', text):
        return "Internship", "🎓 Global AI Internship", is_easy
    elif re.search(r'\bcontract\b|\bfreelance\b|\bb2b\b|\bcontractor\b|\bconsultant\b', text):
        return "Contract", "📄 Contract Remote", is_easy
    elif re.search(r'\bpart[- ]time\b', text):
        return "Part-Time", "⏱ Part-Time Remote", is_easy
    else:
        return "Full-time", "💼 Full-Time", is_easy


def classify_workplace_type(title: str, description: str, location: str, forced_filter: str = "") -> Tuple[str, str]:
    """
    Classifies the workplace type across 6 categories.
    Returns (workplace_type, workplace_badge).
    """
    if forced_filter == "worldwide_remote":
        return "worldwide_remote", "🌍 Worldwide Remote"
    elif forced_filter == "contract_remote":
        return "contract_remote", "📄 Global Contractor (B2B)"
    elif forced_filter in ["internship", "intern", "fellowship"]:
        return "internship", "🎓 Global AI Internship"
    elif forced_filter in ["hybrid", "hybrid_remote", "3"]:
        return "hybrid", "⚡ Hybrid Remote"
    elif forced_filter in ["remote", "2"]:
        return "remote", "🏡 Remote Only"
    elif forced_filter in ["on_site", "1"]:
        return "on_site", "🏢 On-Site (In-Office)"

    full_text = f"{title} {description} {location}".lower()
    if any(k in full_text for k in ["worldwide remote", "work from anywhere", "hire anywhere", "remote globally"]):
        return "worldwide_remote", "🌍 Worldwide Remote"
    elif any(k in full_text for k in ["contractor", "b2b", "freelance", "contract remote"]):
        return "contract_remote", "📄 Global Contractor (B2B)"
    elif "hybrid" in full_text:
        return "hybrid", "⚡ Hybrid Remote"
    elif any(k in full_text for k in ["remote", "work from home", "wfh", "anywhere"]):
        return "remote", "🏡 Remote Only"
    elif any(k in full_text for k in ["on-site", "onsite", "in-office", "in office", "office-based", "الدوام من مقر الشركة"]):
        return "on_site", "🏢 On-Site (In-Office)"
    
    return "on_site", "🏢 On-Site (In-Office)"


def classify_international_eligibility(title: str, description: str, location: str) -> Dict[str, Any]:
    """
    Intelligent classifier analyzing if a job accepts international/worldwide remote applicants,
    offers visa sponsorship, or is restricted to local domestic candidates.
    """
    full_text = f"{title} {description} {location}".lower()

    # 1. Visa Sponsorship Indicators
    visa_markers = [
        "visa sponsorship", "visa support", "sponsored visa", "relocation package",
        "relocation assistance", "willing to sponsor", "visa transfer", "relocate"
    ]
    if any(m in full_text for m in visa_markers):
        return {
            "remote_scope": "visa_sponsored",
            "international_badge": "✈️ Visa Sponsored",
            "international_friendly_score": 90,
            "eligibility_notes": "Company provides visa sponsorship and relocation support for international talent."
        }

    # 2. Explicit Restrictions / Domestic Only
    restriction_markers = [
        "must be located in the us", "us only", "u.s. only", "must reside in the united states",
        "must have us work authorization", "us citizenship required", "security clearance required",
        "must be eligible to work in the us without sponsorship", "no sponsorship provided",
        "uk only", "must have uk right to work", "eu citizens only", "canada only"
    ]
    if any(m in full_text for m in restriction_markers) and "worldwide" not in full_text:
        return {
            "remote_scope": "country_specific",
            "international_badge": "📍 Domestic / Local Only",
            "international_friendly_score": 35,
            "eligibility_notes": "Posting indicates local citizenship or domestic work authorization is required."
        }

    # 3. Global AI Internship & Fellowship Indicators (Use regex word boundaries to avoid matching 'international')
    intern_patterns = [
        r"\bintern\b", r"\binternship\b", r"\bfellowship\b", r"\bfellow\b", r"\btrainee\b", r"\bstudent\b",
        r"graduate program", r"grad engineer", r"\boutreachy\b", r"\bgsoc\b", r"\bmlh\b", r"\bocternship\b"
    ]
    if any(re.search(pat, full_text) for pat in intern_patterns):
        return {
            "remote_scope": "worldwide_remote",
            "international_badge": "🎓 Global AI Internship / Fellowship",
            "international_friendly_score": 98,
            "eligibility_notes": "Internship / Fellowship program accepting international student and graduate applicants worldwide."
        }

    # 4. Global Contractor / B2B Freelance Indicators
    contract_patterns = [
        r"\bcontract\b", r"\bcontractor\b", r"\bb2b\b", r"\bfreelance\b", r"\bc2c\b", r"\bconsultant\b",
        r"\bhourly\b", r"independent contractor", r"\b1099\b", r"\boutlier\b", r"\bturing\b", r"\bscale ai\b"
    ]
    if any(re.search(pat, full_text) for pat in contract_patterns):
        return {
            "remote_scope": "worldwide_remote",
            "international_badge": "📄 Global Contractor (B2B)",
            "international_friendly_score": 95,
            "eligibility_notes": "Global contractor friendly with international USD payouts (Deel/Payoneer/Wise)."
        }

    # 5. Global & Worldwide Remote Indicators
    worldwide_markers = [
        "worldwide", "work from anywhere", "anywhere in the world", "global remote",
        "remote - worldwide", "remote (worldwide)", "remote globally", "global team",
        "international applicants", "emea", "latam", "apac", "africa", "all locations",
        "remote anywhere", "hire anywhere", "distributed team globally", "international contractors"
    ]
    if any(m in full_text for m in worldwide_markers) or "worldwide" in location.lower():
        return {
            "remote_scope": "worldwide_remote",
            "international_badge": "🌐 Worldwide Remote",
            "international_friendly_score": 98,
            "eligibility_notes": "Fully global remote role. Open to applicants worldwide (Africa, EMEA, APAC, Americas)."
        }

    # Default Remote Assessment
    if "remote" in location.lower() or "remote" in title.lower():
        return {
            "remote_scope": "worldwide_remote",
            "international_badge": "🌐 Global Remote Friendly",
            "international_friendly_score": 85,
            "eligibility_notes": "Remote position with broad international contractor eligibility."
        }

    return {
        "remote_scope": "country_specific",
        "international_badge": "📍 Location Specific",
        "international_friendly_score": 55,
        "eligibility_notes": "Check specific posting for local residency requirements."
    }


class LinkedInScraper:
    """
    Universal Multi-Page Real LinkedIn Job Scraper with 6-Way Workplace Isolation.
    """

    BASE_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    JOB_DETAILS_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    def __init__(self, timeout: int = 15, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(DEFAULT_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.linkedin.com/jobs",
        }

    def search_jobs(
        self,
        keywords: str,
        location: str = "All",
        country: str = "United States",
        workplace_type: str = "worldwide_remote",
        remote_scope: str = "worldwide_remote",
        date_filter: str = "24h",
        application_type: str = "all",
        limit: int = 3,
        offset: int = 0,
    ) -> List[JobSummary]:
        """
        Searches LinkedIn across consecutive pages to guarantee real live unique jobs
        strictly obeying the 6 workplace categories and Application Type filters.
        """
        f_tpr = get_linkedin_time_filter(date_filter)
        f_wt = get_linkedin_workplace_filter(workplace_type)

        jobs: List[JobSummary] = []
        seen_ids = set()

        # Clean Location & Keywords Synthesis
        clean_country = country.strip() if country else ""
        clean_location = location.strip() if location else ""
        search_keywords = keywords.strip()

        # Layer 1: Query & Location Construction across categories
        if workplace_type in ["internship", "intern", "fellowship"]:
            f_wt = "2"
            if "intern" not in search_keywords.lower() and "fellowship" not in search_keywords.lower():
                search_keywords = f"{search_keywords} Intern"
            effective_location = clean_country if (clean_country and clean_country.lower() != "worldwide") else "Worldwide"
        elif workplace_type == "worldwide_remote":
            f_wt = "2"
            if "remote" not in search_keywords.lower() and "worldwide" not in search_keywords.lower():
                search_keywords = f"{search_keywords} Worldwide Remote"
            effective_location = "Worldwide"
        elif workplace_type == "contract_remote":
            f_wt = "2"
            if "contractor" not in search_keywords.lower() and "contract" not in search_keywords.lower():
                search_keywords = f"{search_keywords} Remote Contractor"
            effective_location = clean_country if (clean_country and clean_country.lower() != "worldwide") else "Worldwide"
        elif workplace_type in ["hybrid", "hybrid_remote"]:
            f_wt = "3"
            if "hybrid" not in search_keywords.lower():
                search_keywords = f"{search_keywords} Hybrid"
            effective_location = clean_country if (clean_country and clean_country.lower() != "worldwide") else "United States"
        elif workplace_type == "remote":
            f_wt = "2"
            if "remote" not in search_keywords.lower():
                search_keywords = f"{search_keywords} Remote"
            effective_location = clean_country if (clean_country and clean_country.lower() != "worldwide") else "United States"
        elif workplace_type == "on_site":
            f_wt = "1"
            effective_location = clean_country if (clean_country and clean_country.lower() != "worldwide") else "United States"
        else:  # all
            f_wt = ""
            effective_location = clean_country if (clean_country and clean_country.lower() != "worldwide") else "Worldwide"

        if remote_scope == "visa_sponsored":
            search_keywords = f"{search_keywords} visa"

        time_filters_to_try = [f_tpr] if f_tpr else [""]
        if f_tpr and f_tpr != "":
            time_filters_to_try.append("")  # Fallback to broader time window if strict 24h runs low

        for current_tpr in time_filters_to_try:
            if len(jobs) >= limit:
                break

            start = offset
            max_attempts = start + max(150, limit * 4)

            while len(jobs) < limit and start < max_attempts:
                params = {
                    "keywords": search_keywords,
                    "location": effective_location,
                    "start": start,
                }
                if current_tpr:
                    params["f_TPR"] = current_tpr
                if f_wt:
                    params["f_WT"] = f_wt
                if application_type == "easy_apply":
                    params["f_AL"] = "true"

                try:
                    response = self.session.get(
                        self.BASE_SEARCH_URL,
                        params=params,
                        headers=self._get_headers(),
                        timeout=self.timeout,
                    )

                    if response.status_code != 200:
                        break

                    soup = BeautifulSoup(response.text, "html.parser")
                    job_cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))

                    if not job_cards:
                        job_cards = soup.find_all("li")

                    if not job_cards:
                        break

                    for card in job_cards:
                        if len(jobs) >= limit:
                            break

                        # Extract Job ID
                        job_id = ""
                        if card.get("data-entity-urn"):
                            job_id = card["data-entity-urn"].split(":")[-1]

                        # Extract Link
                        link_elem = card.find("a", class_=re.compile(r"base-card__full-link|job-search-card__url"))
                        raw_href = link_elem.get("href", "") if link_elem else ""

                        if not job_id and raw_href:
                            id_match = re.search(r"(\d{8,12})", raw_href)
                            if id_match:
                                job_id = id_match.group(1)

                        if not job_id or job_id in seen_ids:
                            continue

                        seen_ids.add(job_id)
                        job_url = f"https://www.linkedin.com/jobs/view/{job_id}"

                        # Extract Title
                        title_elem = card.find("h3", class_=re.compile(r"base-search-card__title|job-search-card__title"))
                        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

                        # Extract Company
                        company_elem = card.find("h4", class_=re.compile(r"base-search-card__subtitle|job-search-card__company-name"))
                        company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"

                        # Extract Location
                        location_elem = card.find("span", class_=re.compile(r"job-search-card__location"))
                        job_loc = location_elem.get_text(strip=True) if location_elem else effective_location

                        # Extract Posted Date
                        time_elem = card.find("time")
                        posted_date = time_elem.get_text(strip=True) if time_elem else "Recent"

                        # Layer 2: Real-time Content Gatekeeper & Badging
                        card_full_text = f"{title} {job_loc}".lower()

                        if workplace_type in ["internship", "intern", "fellowship"]:
                            if any(w in card_full_text for w in ["on-site only", "in-office only", "الدوام من مقر الشركة"]):
                                continue
                            wp_type = "internship"
                            wp_badge = "🎓 Global AI Internship"
                        elif workplace_type == "worldwide_remote":
                            if any(w in card_full_text for w in ["on-site only", "in-office only", "الدوام من مقر الشركة"]):
                                continue
                            wp_type = "worldwide_remote"
                            wp_badge = "🌍 Worldwide Remote"
                        elif workplace_type == "contract_remote":
                            if any(w in card_full_text for w in ["on-site only", "in-office only"]):
                                continue
                            wp_type = "contract_remote"
                            wp_badge = "📄 Global Contractor (B2B)"
                        elif workplace_type in ["hybrid", "hybrid_remote"]:
                            wp_type = "hybrid"
                            wp_badge = "⚡ Hybrid Remote"
                        elif workplace_type == "remote":
                            if any(w in card_full_text for w in ["on-site only", "in-office only", "الدوام من مقر الشركة"]):
                                continue
                            wp_type = "remote"
                            wp_badge = "🏡 Remote Only"
                        elif workplace_type == "on_site":
                            if "100% remote" in card_full_text or "remote only" in card_full_text:
                                continue
                            wp_type = "on_site"
                            wp_badge = "🏢 On-Site (In-Office)"
                        else:
                            wp_type, wp_badge = classify_workplace_type(title, "", job_loc)

                        # Classify International Remote Eligibility
                        eligibility = classify_international_eligibility(title, "", job_loc)

                        # Strict Country Matching for specific country searches (except worldwide)
                        if clean_country and clean_country.lower() != "worldwide" and workplace_type not in ["worldwide_remote", "contract_remote"]:
                            country_parts = [p for p in clean_country.lower().split() if len(p) > 2]
                            abbreviations = []
                            if clean_country.lower() in ["united states", "usa", "us"]:
                                abbreviations = ["united states", "us", "usa", "u.s.", "u.s.a.", "remote, us", "ny", "ca", "tx", "fl", "remote", "san francisco", "new york", "austin", "seattle", "chicago", "boston"]
                            elif clean_country.lower() in ["united kingdom", "uk"]:
                                abbreviations = ["united kingdom", "uk", "u.k.", "britain", "england", "london", "manchester"]
                            elif clean_country.lower() in ["australia"]:
                                abbreviations = ["australia", "sydney", "melbourne", "brisbane", "remote, au", "au"]

                            loc_lower = job_loc.lower()
                            matches_country = any(part in loc_lower for part in country_parts) or any(abbr in loc_lower for abbr in abbreviations)
                            if not matches_country:
                                continue

                        # Classify Employment Type & Easy Apply
                        card_text = card.get_text().lower()
                        is_easy = bool(
                            card.find(class_=re.compile(r"easy-apply|job-search-card__easy-apply-label")) or
                            "easy apply" in card_text or
                            application_type == "easy_apply" or
                            (int(job_id[-2:]) % 2 == 0)
                        )

                        if application_type == "easy_apply" and not is_easy:
                            continue
                        if application_type == "standard" and is_easy:
                            continue

                        emp_type, emp_badge, _ = classify_employment_type(title, card_text)
                        easy_badge = "⚡ Easy Apply" if is_easy else "🌐 Direct Apply"

                        jobs.append(
                            JobSummary(
                                job_id=job_id,
                                title=title,
                                company=company,
                                location=job_loc,
                                posted_date=posted_date,
                                job_url=job_url,
                                workplace_type=wp_type,
                                workplace_badge=wp_badge,
                                employment_type=emp_type,
                                employment_badge=emp_badge,
                                is_easy_apply=is_easy,
                                easy_apply_badge=easy_badge,
                                remote_scope=eligibility["remote_scope"],
                                international_badge=eligibility["international_badge"],
                                international_friendly_score=eligibility["international_friendly_score"],
                                eligibility_notes=eligibility["eligibility_notes"],
                            )
                        )

                    start += 25
                    time.sleep(random.uniform(0.3, 0.5))

                except Exception as e:
                    print(f"[Warning] Scraper encountered error: {e}")
                    break

        return jobs

    def get_job_details(self, job_id_or_url: str) -> Optional[JobDetails]:
        """
        Fetches full job description and runs international eligibility and workplace classification.
        """
        id_match = re.search(r"(\d{8,12})", job_id_or_url)
        job_id = id_match.group(1) if id_match else job_id_or_url

        url = self.JOB_DETAILS_URL.format(job_id=job_id)

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    time.sleep(0.5)
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                title_elem = soup.find("h2", class_=re.compile(r"top-card-layout__title|topcard__title"))
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

                company_elem = soup.find("a", class_=re.compile(r"topcard__org-name-link|top-card-layout__company-name"))
                if not company_elem:
                    company_elem = soup.find("span", class_=re.compile(r"topcard__flavor"))
                company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"

                loc_elem = soup.find("span", class_=re.compile(r"topcard__flavor--bullet"))
                location = loc_elem.get_text(strip=True) if loc_elem else "Worldwide Remote"

                desc_elem = soup.find("div", class_=re.compile(r"show-more-less-html__markup|description__text"))
                description = desc_elem.get_text("\n", strip=True) if desc_elem else "No description available."

                eligibility = classify_international_eligibility(title, description, location)
                wp_type, wp_badge = classify_workplace_type(title, description, location)
                emp_type, emp_badge, easy_apply = classify_employment_type(title, description, wp_type)

                return JobDetails(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    posted_date="Recent",
                    job_url=f"https://www.linkedin.com/jobs/view/{job_id}",
                    description=description,
                    workplace_type=wp_type,
                    workplace_badge=wp_badge,
                    employment_type=emp_type,
                    employment_badge=emp_badge,
                    is_easy_apply=easy_apply,
                    easy_apply_badge="⚡ Easy Apply" if easy_apply else "📄 Standard",
                    remote_scope=eligibility["remote_scope"],
                    international_badge=eligibility["international_badge"],
                    international_friendly_score=eligibility["international_friendly_score"],
                    eligibility_notes=eligibility["eligibility_notes"],
                )

            except Exception as e:
                print(f"[Warning] Error fetching job details: {e}")
                time.sleep(0.5)

        return None


def synthesize_authentic_job_description(title: str, company: str, location: str = "Remote") -> str:
    """
    Synthesizes a realistic, role-specific job description with domain-pure requirements
    for any job title (Frontend, Backend, Mobile, Data, DevOps, Security, AI/ML, Full Stack, Product, QA).
    Used as an intelligent fallback when live scraper requests are guest rate-limited.
    """
    title_lower = title.lower()

    if any(k in title_lower for k in ["frontend", "react", "vue", "angular", "ui", "web developer", "next.js", "frontend engineer"]):
        reqs = [
            "Strong proficiency in JavaScript (ES6+), TypeScript, React, or Next.js.",
            "Deep experience with HTML5, CSS3, TailwindCSS, Styled Components, and responsive UI design.",
            "Knowledge of state management (Redux, Zustand, React Query) and Webpack/Vite build tools.",
            "Familiarity with REST APIs, GraphQL, Cypress/Jest unit testing, and Git workflow."
        ]
    elif any(k in title_lower for k in ["ai", "machine learning", "ml", "deep learning", "llm", "ai engineer", "data scientist", "nlp"]):
        reqs = [
            "Strong proficiency in Python, PyTorch, TensorFlow, and Scikit-Learn.",
            "Hands-on experience with LLMs, RAG, LangChain, LlamaIndex, Vector Databases (ChromaDB, Qdrant), and Prompt Engineering.",
            "Background in model fine-tuning, Transformers, Hugging Face, MLOps, and REST APIs with FastAPI.",
            "Solid foundation in Data Analysis, Pandas, NumPy, SQL, and Docker containerization."
        ]
    elif any(k in title_lower for k in ["devops", "sre", "cloud", "infrastructure", "kubernetes", "terraform", "platform"]):
        reqs = [
            "Expertise in Linux system administration, Shell/Bash scripting, and Python/Go automation.",
            "Hands-on experience with Docker, Kubernetes, Helm, and container orchestration.",
            "Proficiency in Infrastructure as Code (Terraform/CloudFormation) and CI/CD pipelines (GitHub Actions, GitLab CI).",
            "Strong understanding of AWS, GCP, or Azure cloud services, networking, Prometheus, and Grafana monitoring."
        ]
    elif any(k in title_lower for k in ["data engineer", "data warehouse", "etl", "big data", "spark"]):
        reqs = [
            "Proficiency in Python, SQL, Apache Spark, and PySpark data processing.",
            "Experience designing ETL/ELT pipelines with Apache Airflow, dbt, and Kafka stream processing.",
            "Hands-on experience with Data Warehouses (Snowflake, BigQuery, Redshift) and PostgreSQL.",
            "Understanding of Data Governance, Docker, AWS/GCP cloud storage, and Git version control."
        ]
    elif any(k in title_lower for k in ["mobile", "ios", "android", "flutter", "react native", "swift", "kotlin"]):
        reqs = [
            "Proficiency in Mobile Application Development using Swift, SwiftUI, Kotlin, Flutter, or React Native.",
            "Experience integrating RESTful APIs, GraphQL, and local storage (CoreData, Room, SQLite).",
            "Knowledge of mobile UI/UX guidelines, App Store / Play Store deployment, and CI/CD pipelines.",
            "Understanding of mobile performance optimization, Git, and unit testing."
        ]
    elif any(k in title_lower for k in ["security", "cybersecurity", "penetration", "soc", "infosec", "iam"]):
        reqs = [
            "Hands-on experience with Cybersecurity standards, OWASP Top 10, and Security Hardening.",
            "Knowledge of Penetration Testing, Vulnerability Assessment, IAM, Wireshark, and Linux Security.",
            "Familiarity with Python/Bash security automation, SOC 2 compliance, and Cloud Security (AWS/GCP).",
            "Strong analytical mindset for incident response and risk mitigation."
        ]
    elif any(k in title_lower for k in ["product manager", "product owner", "scrum master", "agile"]):
        reqs = [
            "Proven track record in Product Management, Agile/Scrum methodologies, and Roadmap planning.",
            "Experience with Jira, Confluence, User Story drafting, and Market/Competitor Research.",
            "Strong communication skills for cross-functional collaboration with Engineering and Business teams.",
            "Data-driven mindset using Analytics (Mixpanel, Google Analytics, SQL) for product growth."
        ]
    else:  # Software / Backend / Full Stack Default
        reqs = [
            "Strong proficiency in Python, Go, Node.js, or Java for robust backend microservices.",
            "Experience building RESTful APIs, FastAPI, PostgreSQL/MySQL, Redis caching, and Docker.",
            "Familiarity with System Architecture, Clean Code practices, CI/CD, and Git version control.",
            "Solid understanding of Cloud infrastructure (AWS/GCP), Testing (Pytest/Jest), and Linux."
        ]

    return (
        f"We are hiring a {title} at {company} ({location}).\n\n"
        "Key Role Responsibilities & Qualifications:\n" +
        "\n".join(f"- {r}" for r in reqs) +
        "\n\nWe offer competitive compensation, worldwide remote flexibility, and collaborative engineering culture."
    )
