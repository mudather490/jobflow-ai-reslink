"""
Global Verified Employers, International Contractors, and Global Remote Internship Knowledge Base.
Curated for international talent (Sudan, Africa, Middle East, and Worldwide).
"""

from typing import Dict, List, Optional, Tuple

# 1. Top Worldwide Remote Tech Employers (Hire in 100+ countries globally via EOR / Deel / Direct)
WORLDWIDE_REMOTE_COMPANIES = [
    ("GitLab", "Worldwide Remote", "100% all-remote company hiring software & AI engineers globally across Africa, EMEA, and Americas."),
    ("Canonical (Ubuntu)", "Worldwide Remote", "Global open-source enterprise hiring remote AI, Linux, and Cloud engineers across 100+ countries."),
    ("Automattic (WordPress)", "Worldwide Remote", "Remote-first creator of WordPress & WooCommerce hiring talent globally with full equipment allowance."),
    ("Supabase", "Worldwide Remote", "Open source Firebase alternative with a 100% distributed remote team across 30+ countries."),
    ("DuckDuckGo", "Worldwide Remote", "Privacy-focused tech company hiring globally without geographic boundaries."),
    ("Zapier", "Worldwide Remote", "100% distributed automation platform hiring engineering talent worldwide."),
    ("Wikimedia Foundation", "Worldwide Remote", "Global non-profit operating Wikipedia with international remote staff across the globe."),
    ("Mozilla", "Worldwide Remote", "Open source non-profit behind Firefox hiring global engineers and open web advocates."),
    ("Vercel", "Worldwide Remote", "Frontend cloud platform hiring global distributed engineers and developer advocates."),
    ("Elastic", "Worldwide Remote", "Distributed search and data analytics enterprise hiring engineers across 40+ countries."),
    ("Docker, Inc", "Worldwide Remote", "Container platform enterprise operating as a remote-first international team."),
    ("Basecamp (37signals)", "Worldwide Remote", "Pioneers of remote work hiring globally for high-autonomy engineering roles."),
    ("Buffer", "Worldwide Remote", "Transparent, 100% distributed social media platform with a global team in 20+ countries."),
    ("PostHog", "Worldwide Remote", "Open-source product analytics platform hiring globally with transparent pay and USD equity."),
    ("Ghost Foundation", "Worldwide Remote", "Open-source publishing platform structured as a non-profit hiring remote developers globally."),
    ("Chainlink Labs", "Worldwide Remote", "Decentralized blockchain oracle network hiring global distributed engineers and AI researchers."),
    ("Nethermind", "Worldwide Remote", "Ethereum research & AI engineering team with 100+ remote contributors worldwide."),
    ("Protocol Labs", "Worldwide Remote", "Creators of IPFS and Filecoin hiring international distributed AI & distributed systems engineers."),
    ("Sourcegraph", "Worldwide Remote", "AI-powered code search & coding assistant enterprise hiring global remote talent."),
    ("Grafana Labs", "Worldwide Remote", "Open observability enterprise operating a remote-first global engineering organization."),
    ("Mattermost", "Worldwide Remote", "Secure collaboration platform hiring remote software engineers globally."),
    ("Hugging Face", "Worldwide Remote", "Open-source AI platform hiring remote Machine Learning researchers and community engineers worldwide.")
]

# 2. Top Global Contract / B2B Freelance AI & Tech Employers (USD Payouts via Deel, Payoneer, Wise)
GLOBAL_CONTRACT_COMPANIES = [
    ("Outlier AI", "Global Remote (Contractor / B2B)", "Frontier AI lab hiring international ML engineers and prompt evaluators globally. USD weekly payouts via Payoneer/Wise/Crypto."),
    ("Scale AI", "Global Remote (Contractor / B2B)", "Data foundry for frontier AI models hiring global AI experts to train, evaluate, and benchmark LLMs."),
    ("Turing.com", "Global Remote (Contractor / B2B)", "AI-powered talent cloud matching African and international ML engineers directly with US tech startups."),
    ("Mercor", "Global Remote (Contractor / B2B)", "AI-driven recruiting platform assessing and hiring top international AI talent for Silicon Valley companies."),
    ("Alignerr", "Global Remote (Contractor / B2B)", "Specialized platform hiring machine learning and software engineering contractors globally."),
    ("Mindrift", "Global Remote (Contractor / B2B)", "AI tutoring and model evaluation network hiring global AI writers and software engineers."),
    ("Invisible Tech", "Global Remote (Contractor / B2B)", "Operations platform for frontier AI labs hiring international AI trainers and workflow engineers."),
    ("Braintrust", "Global Remote (Contractor / B2B)", "User-owned talent network matching global engineers with Fortune 500 enterprises."),
    ("DataAnnotation.tech", "Global Remote (Contractor / B2B)", "Global AI evaluation network with hourly USD pay for coding, machine learning, and reasoning tasks."),
    ("Remotasks", "Global Remote (Contractor / B2B)", "Global task marketplace for AI model evaluation and computer vision annotation."),
    ("Toptal", "Global Remote (Contractor / B2B)", "Elite freelance network accepting the top 3% of global software and machine learning engineers."),
    ("Modus Create", "Global Remote (Contractor / B2B)", "Global consulting firm hiring international contractors across cloud, AI, and software engineering."),
    ("10x Management", "Global Remote (Contractor / B2B)", "Talent agency representing international independent tech contractors and AI specialists."),
    ("Andela", "Global Remote (Contractor / B2B)", "Global talent network connecting African and international technologists with long-term remote roles.")
]

# 3. Top International AI & Software Internships / Fellowships (Accepting applicants from Sudan & Worldwide)
GLOBAL_INTERNSHIP_PROGRAMS = [
    ("Outreachy Fellowship", "Worldwide Remote (Paid Fellowship)", "Internationally renowned 3-month paid remote fellowship ($7,000 USD stipend) specifically designed for international tech talent including Africa."),
    ("Google Summer of Code (GSoC)", "Worldwide Remote (Paid Mentorship)", "Global program offering paid stipends to university students and open-source beginners worldwide working with mentors on ML and software."),
    ("MLH Fellowship", "Worldwide Remote (Paid Internship)", "12-week remote internship fellowship pairing international students with real open-source projects and sponsor tech companies."),
    ("Linux Foundation Mentorship (LFX)", "Worldwide Remote (Paid Mentorship)", "Paid remote mentorship stipends for international developers contributing to Linux, Kubernetes, and Cloud Native AI projects."),
    ("GitHub Octernships", "Worldwide Remote (Paid Internship)", "Paid remote internships for global students connecting directly with partner tech companies worldwide."),
    ("Canonical Graduate AI Engineer Program", "Worldwide Remote (Junior / Entry-Level)", "Canonical's graduate hiring track offering structured entry-level remote engineering roles across 100+ countries."),
    ("Hugging Face Open Source Fellows", "Worldwide Remote (Fellowship)", "Paid fellowship program supporting global developers building open-source machine learning models and datasets."),
    ("Mozilla Open Source Mentorship", "Worldwide Remote (Mentorship)", "Remote program supporting global developers building open-source web and AI technologies."),
    ("NumFOCUS Open Source Mentorship", "Worldwide Remote (Paid Fellowship)", "Supports open-source scientific computing and ML libraries (NumPy, SciPy, Pandas) with international student stipends."),
    ("Python Software Foundation (PSF) Fellowship", "Worldwide Remote (Community Fellowship)", "Global initiative recognizing and supporting Python and ML contributors worldwide.")
]


def get_all_global_employers() -> List[Tuple[str, str, str]]:
    """Returns combined list of all global employers, contractors, and internship programs."""
    return WORLDWIDE_REMOTE_COMPANIES + GLOBAL_CONTRACT_COMPANIES + GLOBAL_INTERNSHIP_PROGRAMS


def get_employers_by_workplace_type(workplace_type: str) -> List[Tuple[str, str, str]]:
    """Returns list of employers specifically matching the requested workplace mode."""
    wt = workplace_type.lower()
    if wt == "contract_remote":
        return GLOBAL_CONTRACT_COMPANIES
    elif wt in ["internship", "intern"]:
        return GLOBAL_INTERNSHIP_PROGRAMS
    elif wt == "worldwide_remote":
        return WORLDWIDE_REMOTE_COMPANIES
    return get_all_global_employers()


def detect_internship_signals(title: str, description: str = "") -> bool:
    """Checks if a job title or description represents an internship, fellowship, or student role."""
    text = f"{title} {description}".lower()
    intern_markers = [
        "intern", "internship", "fellowship", "fellow", "trainee", "student",
        "graduate program", "grad engineer", "entry-level", "junior ml", "junior ai",
        "outreachy", "gsoc", "mlh", "octernship", "apprentice", "apprenticeship"
    ]
    return any(marker in text for marker in intern_markers)


def detect_contract_signals(title: str, description: str = "") -> bool:
    """Checks if a job title or description represents a contractor, freelance, or B2B role."""
    text = f"{title} {description}".lower()
    contract_markers = [
        "contract", "contractor", "b2b", "freelance", "c2c", "consultant",
        "hourly", "per diem", "independent contractor", "1099", "outlier", "turing"
    ]
    return any(marker in text for marker in contract_markers)


def get_company_metadata(company_name: str) -> Optional[Tuple[str, str, str]]:
    """Looks up verified company metadata from the international knowledge base."""
    name_clean = company_name.lower().strip()
    for comp in get_all_global_employers():
        if comp[0].lower() in name_clean or name_clean in comp[0].lower():
            return comp
    return None
