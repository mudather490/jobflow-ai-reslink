from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field
from core.resume_parser import UserProfile, Project, WorkExperience
from core.scraper import JobDetails
from core.matcher import MatchReport, JobMatcher


class GapQuestion(BaseModel):
    skill_name: str
    question_text: str
    context_reason: str


class GapQuestioningAgent:
    """
    Interactive AI Agent that identifies resume gaps and asks targeted questions
    to discover unlisted candidate experience (freelance, side projects, past roles).
    Updates the profile state with grounded, truthful context.
    """

    def __init__(self, matcher: Optional[JobMatcher] = None):
        self.matcher = matcher or JobMatcher()

    def generate_gap_questions(
        self, profile: UserProfile, job: JobDetails, match_report: MatchReport
    ) -> List[GapQuestion]:
        """
        Formulates clear, professional clarification questions for missing requirements.
        """
        questions: List[GapQuestion] = []

        for skill in match_report.missing_critical_skills[:5]:  # Focus on top 5 most critical
            q_text = (
                f"The role at **{job.company}** highlights **{skill}** as a key requirement. "
                f"You have not mentioned it in your resume. Have you used {skill} in any freelance work, "
                f"personal projects, certifications, or previous jobs?"
            )
            reason = f"Required by {job.title} at {job.company}"
            questions.append(
                GapQuestion(
                    skill_name=skill,
                    question_text=q_text,
                    context_reason=reason,
                )
            )

        return questions

    def apply_user_answer(
        self, profile: UserProfile, skill: str, user_response: str
    ) -> Tuple[UserProfile, bool]:
        """
        Integrates user's verified response into the structured profile.
        Returns the updated profile and a boolean indicating if changes were made.
        """
        resp_clean = user_response.strip()
        if not resp_clean or resp_clean.lower() in ["no", "skip", "n", "none", "n/a", "don't have", "dont have"]:
            return profile, False

        # Add skill to skills list if not already present
        if skill not in profile.skills:
            profile.skills.append(skill)
            profile.skills = sorted(list(set(profile.skills)))

        # Create or update a project/experience entry grounded on the user's input
        project_name = f"{skill} Implementation"
        # Check if project already exists
        existing_proj = next((p for p in profile.projects if skill.lower() in p.name.lower() or skill.lower() in [t.lower() for t in p.technologies]), None)
        
        if existing_proj:
            existing_proj.description += f" {resp_clean}"
            if skill not in existing_proj.technologies:
                existing_proj.technologies.append(skill)
        else:
            profile.projects.append(
                Project(
                    name=project_name,
                    description=resp_clean,
                    technologies=[skill],
                )
            )

        return profile, True

    def run_interactive_resolution(
        self,
        profile: UserProfile,
        job: JobDetails,
        match_report: MatchReport,
        answers: Optional[Dict[str, str]] = None,
    ) -> Tuple[UserProfile, MatchReport]:
        """
        Applies a dictionary of answers to missing skills and recalculates the ATS match score.
        """
        updated_profile = profile.model_copy(deep=True)
        if answers:
            for skill, answer in answers.items():
                updated_profile, _ = self.apply_user_answer(updated_profile, skill, answer)

        # Recalculate match score with updated profile
        updated_report = self.matcher.evaluate_match(updated_profile, job)
        return updated_profile, updated_report
