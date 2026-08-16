import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

from config import DATA_DIR
from core.resume_parser import UserProfile


class QuestionEntry(BaseModel):
    id: str
    category: str  # "contact", "location", "work_auth", "custom"
    question: str
    answer: str
    answer_type: str = "text"  # "text", "number", "boolean", "choice"
    aliases: List[str] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


DEFAULT_QUESTIONNAIRE_ENTRIES: List[Dict[str, Any]] = [
    # ── 1. Contact & Identity ──
    {
        "id": "first_name",
        "category": "contact",
        "question": "First name?",
        "answer": "Alex",
        "answer_type": "text",
        "aliases": [
            "first name",
            "given name",
            "legal first name",
            "first_name",
            "forename",
            "first name (as shown on id)"
        ]
    },
    {
        "id": "last_name",
        "category": "contact",
        "question": "Last name?",
        "answer": "Rivera",
        "answer_type": "text",
        "aliases": [
            "last name",
            "family name",
            "surname",
            "legal last name",
            "last_name"
        ]
    },
    {
        "id": "phone_country_code",
        "category": "contact",
        "question": "Phone country code?",
        "answer": "South Sudan (+211)",
        "answer_type": "text",
        "aliases": [
            "phone country code",
            "country calling code",
            "phone prefix",
            "country code",
            "dialing code",
            "phone code",
            "international dial code",
            "mobile country code",
            "south sudan (+211)"
        ]
    },
    {
        "id": "mobile_phone",
        "category": "contact",
        "question": "Mobile phone number?",
        "answer": "+211 920 123 456",
        "answer_type": "text",
        "aliases": [
            "mobile phone number",
            "phone number",
            "mobile number",
            "cell phone number",
            "cell number",
            "telephone",
            "contact number",
            "mobile phone"
        ]
    },
    {
        "id": "email_address",
        "category": "contact",
        "question": "Email address?",
        "answer": "alex.rivera@example.com",
        "answer_type": "text",
        "aliases": [
            "email address",
            "email",
            "primary email",
            "contact email",
            "e-mail"
        ]
    },

    # ── 2. Location & Address ──
    {
        "id": "street_address",
        "category": "location",
        "question": "Address (Street / Line 1)?",
        "answer": "Airport Road, Sector 4",
        "answer_type": "text",
        "aliases": [
            "address",
            "street address",
            "address line 1",
            "home address",
            "residential address",
            "street",
            "mailing address"
        ]
    },
    {
        "id": "city",
        "category": "location",
        "question": "City?",
        "answer": "Juba",
        "answer_type": "text",
        "aliases": [
            "city",
            "town",
            "city / town",
            "current city",
            "city of residence",
            "municipality"
        ]
    },
    {
        "id": "state",
        "category": "location",
        "question": "State / Province / Region?",
        "answer": "Central Equatoria",
        "answer_type": "text",
        "aliases": [
            "state",
            "state / province",
            "province",
            "region",
            "state / province / region",
            "governorate",
            "county",
            "state/province"
        ]
    },

    # ── 3. Work Authorization ──
    {
        "id": "work_auth_us",
        "category": "work_auth",
        "question": "Are you legally authorized to work in your target country / United States?",
        "answer": "Yes",
        "answer_type": "boolean",
        "aliases": [
            "are you legally authorized to work",
            "legally authorized to work in the united states",
            "work authorization status",
            "eligible to work",
            "are you authorized to work in the country",
            "proof of employment eligibility"
        ]
    },
    {
        "id": "visa_sponsorship",
        "category": "work_auth",
        "question": "Will you now or in the future require visa sponsorship for employment?",
        "answer": "No",
        "answer_type": "boolean",
        "aliases": [
            "require visa sponsorship",
            "require sponsorship for employment",
            "need immigration sponsorship",
            "require sponsorship now or in the future",
            "require h-1b sponsorship",
            "sponsorship needed"
        ]
    }
]


class QuestionnaireMemoryBank:
    """
    Self-Learning Questionnaire Knowledge Base.
    - Stores candidate's permanent answers.
    - Matches job application questions via semantic aliases and keywords.
    - Identifies brand-new unseen questions and prompts user 1 time to answer.
    """
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (DATA_DIR / "questionnaire_bank.json")
        self.questions: Dict[str, QuestionEntry] = {}
        self.load()

    def load(self):
        """Loads saved questions from disk and merges default baseline questions."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        entry = QuestionEntry(**item)
                        self.questions[entry.id] = entry

                # Ensure all default baseline questions exist with correct categories
                updated = False
                for item in DEFAULT_QUESTIONNAIRE_ENTRIES:
                    if item["id"] not in self.questions:
                        entry = QuestionEntry(**item)
                        self.questions[entry.id] = entry
                        updated = True
                    else:
                        # Normalize category if outdated
                        if self.questions[item["id"]].category != item["category"]:
                            self.questions[item["id"]].category = item["category"]
                            updated = True
                if updated:
                    self.save()
                return
            except Exception as e:
                print(f"[!] Warning: Could not load questionnaire bank: {e}. Reinitializing defaults.")

        # Initialize defaults
        self.reset_to_defaults()

    def reset_to_defaults(self):
        """Resets the memory bank to clean default baseline questions."""
        self.questions.clear()
        for item in DEFAULT_QUESTIONNAIRE_ENTRIES:
            entry = QuestionEntry(**item)
            self.questions[entry.id] = entry
        self.save()

    def save(self):
        """Persists knowledge base to disk."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            serializable = [q.model_dump() for q in self.questions.values()]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            print(f"[!] Failed to save questionnaire bank: {e}")

    def get_all(self) -> List[Dict[str, Any]]:
        """Returns all questions formatted for API and UI."""
        return [q.model_dump() for q in self.questions.values()]

    def update_answer(self, q_id: str, new_answer: str) -> bool:
        """Updates answer for an existing question entry."""
        if q_id in self.questions:
            self.questions[q_id].answer = str(new_answer).strip()
            self.questions[q_id].updated_at = datetime.utcnow().isoformat()
            self.save()
            return True
        return False

    def delete_question(self, q_id: str) -> bool:
        """Deletes a custom question entry."""
        if q_id in self.questions:
            del self.questions[q_id]
            self.save()
            return True
        return False

    def add_custom_question(self, question_text: str, answer_val: str, category: str = "custom") -> QuestionEntry:
        """
        Learns and persists a new question from job screening prompt.
        """
        clean_q = question_text.strip()
        matched = self.match_question_in_memory(clean_q)
        if matched:
            matched.answer = str(answer_val).strip()
            matched.updated_at = datetime.utcnow().isoformat()
            self.save()
            return matched

        # Create new entry
        q_id = re.sub(r"[^\w\s]", "", clean_q.lower()).replace(" ", "_")[:35]
        if not q_id or q_id in self.questions:
            q_id = f"custom_{int(datetime.utcnow().timestamp())}"

        # Generate search aliases
        clean_alias = re.sub(r"[^\w\s]", "", clean_q.lower()).strip()
        aliases = [clean_alias]

        entry = QuestionEntry(
            id=q_id,
            category=category,
            question=clean_q,
            answer=str(answer_val).strip(),
            answer_type="text",
            aliases=aliases,
            updated_at=datetime.utcnow().isoformat()
        )
        self.questions[q_id] = entry
        self.save()
        return entry

    add_or_update_custom_question = add_custom_question

    def match_question_in_memory(self, question_text: str) -> Optional[QuestionEntry]:
        """
        Multi-tier precision matcher against memory bank:
        Tier 1: Exact string match with question or exact alias
        Tier 2: Semantic phrase routing (e.g. address vs email vs phone code)
        Tier 3: Substring alias match
        Tier 4: High token overlap match
        """
        q_clean = re.sub(r"[^\w\s]", "", question_text.lower()).strip()
        if not q_clean:
            return None
        q_tokens = set(q_clean.split())

        # Tier 1: Exact matches first
        for entry in self.questions.values():
            clean_entry_q = re.sub(r"[^\w\s]", "", entry.question.lower()).strip()
            if q_clean == clean_entry_q:
                return entry
            for alias in entry.aliases:
                if q_clean == re.sub(r"[^\w\s]", "", alias.lower()).strip():
                    return entry

        # Tier 2: Semantic phrase routing
        if "email" in q_clean:
            if "email_address" in self.questions:
                return self.questions["email_address"]
        if "first name" in q_clean or "given name" in q_clean or "forename" in q_clean:
            if "first_name" in self.questions:
                return self.questions["first_name"]
        if "last name" in q_clean or "surname" in q_clean or "family name" in q_clean:
            if "last_name" in self.questions:
                return self.questions["last_name"]
        if "country code" in q_clean or "dialing code" in q_clean or "phone prefix" in q_clean or "calling code" in q_clean:
            if "phone_country_code" in self.questions:
                return self.questions["phone_country_code"]
        if "mobile" in q_clean or "cell" in q_clean or "phone number" in q_clean:
            if "mobile_phone" in self.questions:
                return self.questions["mobile_phone"]
        if "address" in q_clean and "email" not in q_clean:
            if "street_address" in self.questions:
                return self.questions["street_address"]
        if q_clean in ["city", "town"] or "city of" in q_clean or "current city" in q_clean:
            if "city" in self.questions:
                return self.questions["city"]
        if q_clean in ["state", "province", "region"] or "state province" in q_clean:
            if "state" in self.questions:
                return self.questions["state"]

        # Tier 3: Substring alias match
        for entry in self.questions.values():
            for alias in entry.aliases:
                clean_alias = re.sub(r"[^\w\s]", "", alias.lower()).strip()
                if clean_alias and clean_alias in q_clean:
                    return entry

        # Tier 4: High token overlap match
        best_entry = None
        best_overlap = 0.60
        for entry in self.questions.values():
            entry_tokens = set(re.sub(r"[^\w\s]", "", entry.question.lower()).split())
            if not entry_tokens:
                continue
            overlap = len(q_tokens.intersection(entry_tokens)) / max(len(entry_tokens), len(q_tokens))
            if overlap > best_overlap:
                best_overlap = overlap
                best_entry = entry

        return best_entry

    def evaluate_job_screening_requirements(
        self,
        job_title: str,
        company: str,
        description: str = "",
        candidate_profile: Optional[UserProfile] = None
    ) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """
        Extracts questions required by a job and matches them against Memory Bank.
        Returns:
            answered_questions: Dict[question_text, answer]
            missing_questions: List[Dict containing question_text, suggested_answer, reason]
        """
        answered: Dict[str, str] = {}
        missing: List[Dict[str, Any]] = []

        # 1. Base Universal Questions (Populated directly from memory bank)
        base_keys = [
            "first_name",
            "last_name",
            "phone_country_code",
            "mobile_phone",
            "email_address",
            "street_address",
            "city",
            "state",
            "work_auth_us",
            "visa_sponsorship",
        ]
        for k in base_keys:
            if k in self.questions and self.questions[k].answer:
                answered[self.questions[k].question] = self.questions[k].answer
            else:
                missing.append({
                    "id": k,
                    "question": k.replace("_", " ").title() + "?",
                    "category": "contact",
                    "suggested_answer": "",
                    "reason": f"Required for Easy Apply to {company}"
                })

        # 2. Merge any custom questions saved by the candidate in memory bank
        for q_id, q_entry in self.questions.items():
            if q_id not in base_keys and q_entry.answer:
                answered[q_entry.question] = q_entry.answer

        return answered, missing
