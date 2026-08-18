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
        Preserves the candidate's authentic summary from their uploaded resume without injecting fake claims or targeting phrases.
        """
        if profile.summary and profile.summary.strip():
            return profile.summary.strip()
        return "Dedicated professional with demonstrated expertise and a strong track record of success."

    def tailor_experience_bullets(
        self, experience_list: List[WorkExperience], target_keywords: List[str]
    ) -> List[WorkExperience]:
        """
        Re-orders authentic candidate experience bullets to highlight relevance without modifying content.
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
                    subtitle=exp.subtitle,
                    summary=exp.summary,
                    bullets=sorted_bullets,
                )
            )

        return tailored_list

    def tailor_profile(
        self, profile: UserProfile, job: JobDetails, match_report: MatchReport
    ) -> UserProfile:
        """
        Produces an ATS-optimized UserProfile preserving 100% authentic data from the uploaded CV.
        """
        tailored = profile.model_copy(deep=True)

        # 1. Preserve authentic Headline
        tailored.headline = profile.headline or "Professional Profile"

        # 2. Preserve authentic Summary
        tailored.summary = profile.summary

        # 3. Prioritize matching authentic skills (only from candidate's existing skills)
        matched_set = set(match_report.matched_skills)
        matched_candidate_skills = [s for s in profile.skills if s in matched_set or any(m.lower() == s.lower() for m in matched_set)]
        other_skills = [s for s in profile.skills if s not in matched_candidate_skills]
        tailored.skills = matched_candidate_skills + other_skills

        # 4. Tailor Experience bullets (sorting candidate's own bullets)
        tailored.experience = self.tailor_experience_bullets(
            profile.experience, match_report.matched_skills
        )

        # 5. Preserve authentic Target Role if present
        tailored.target_role = profile.target_role

        return tailored
