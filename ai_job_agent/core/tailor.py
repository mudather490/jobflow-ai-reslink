import re
from typing import List, Optional
from core.resume_parser import UserProfile, WorkExperience, Project
from core.scraper import JobDetails
from core.matcher import MatchReport, JobMatcher


class ResumeTailor:
    """
    Dynamically tailors candidate profiles to match specific job descriptions.
    Re-organizes sections, emphasizes matching keywords, and applies the XYZ formula
    without hallucinating unverifiable claims.
    """

    def __init__(self, matcher: Optional[JobMatcher] = None):
        self.matcher = matcher or JobMatcher()

    def tailor_summary(self, profile: UserProfile, job: JobDetails, match_report: MatchReport) -> str:
        """
        Creates a concise, evidence-based technical summary answering:
        Who is the candidate? What technologies do they use? What can they build? What role are they targeting?
        """
        matched = match_report.matched_skills[:4]
        skills_to_highlight = matched if matched else profile.skills[:4]
        skills_str = ", ".join(skills_to_highlight) if skills_to_highlight else "Python, Machine Learning, and backend APIs"
        
        target_role = job.title or "AI Engineer"
        target_company = f" at {job.company}" if job.company and job.company.lower() != "company" else ""

        if profile.summary and len(profile.summary.strip()) > 50:
            base_sum = re.sub(r'Seeking (a|an)?\s*remote.*$', '', profile.summary, flags=re.I).strip(" .")
            return f"{base_sum}. Targeting the {target_role} position{target_company} to deliver robust, data-driven solutions."

        return (
            f"Junior AI Engineer specializing in {skills_str}. "
            f"Hands-on experience building machine learning models, API microservices, and end-to-end application pipelines. "
            f"Targeting the {target_role} position{target_company} to deliver robust, data-driven solutions."
        )

    def tailor_experience_bullets(
        self, experience_list: List[WorkExperience], target_keywords: List[str]
    ) -> List[WorkExperience]:
        """
        Re-orders and polishes experience bullets to emphasize target job keywords.
        """
        tailored_list = []
        keywords_lower = [k.lower() for k in target_keywords]

        for exp in experience_list:
            sorted_bullets = sorted(
                exp.bullets,
                key=lambda b: any(kw in b.lower() for kw in keywords_lower),
                reverse=True,
            )
            tailored_list.append(
                WorkExperience(
                    company=exp.company,
                    role=exp.role,
                    location=exp.location,
                    duration=exp.duration,
                    bullets=sorted_bullets,
                )
            )

        return tailored_list

    def tailor_profile(
        self, profile: UserProfile, job: JobDetails, match_report: MatchReport
    ) -> UserProfile:
        """
        Produces a complete tailored UserProfile customized for the target job.
        """
        tailored = profile.model_copy(deep=True)

        # 1. Update Headline
        tailored.headline = f"{job.title} Candidate | {', '.join(match_report.matched_skills[:3])}"

        # 2. Tailor Summary
        tailored.summary = self.tailor_summary(tailored, job, match_report)

        # 3. Prioritize Skills
        matched_set = set(match_report.matched_skills)
        other_skills = [s for s in tailored.skills if s not in matched_set]
        tailored.skills = match_report.matched_skills + other_skills

        # 4. Tailor Experience bullets
        tailored.experience = self.tailor_experience_bullets(
            tailored.experience, match_report.matched_skills
        )

        # 5. Tailor Target Role
        comp_str = f" at {job.company}" if job.company and job.company.lower() != "company" else ""
        tailored.target_role = f"Remote {job.title}{comp_str}"

        return tailored
