from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ResumeTemplate(BaseModel):
    id: str
    name: str
    badge: str
    inspired_by: str
    description: str
    primary_color: str
    secondary_color: str
    accent_color: Optional[str] = None
    header_style: str  # "two_column", "centered_classic", "accent_bar", "tech_grid"
    font_name: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"
    font_oblique: str = "Helvetica-Oblique"
    docx_font_name: str = "Calibri"
    section_order: List[str] = Field(default_factory=list)
    recommended_roles: List[str] = Field(default_factory=list)


AVAILABLE_TEMPLATES: Dict[str, ResumeTemplate] = {
    "modern": ResumeTemplate(
        id="modern",
        name="Modern Executive",
        badge="⭐ Active Default",
        inspired_by="Tech Industry Standard / Modern Executive",
        description="Clean 2-column header with Royal Blue accents (#2563EB), crisp 1pt divider rules, categorized skills with bold prefixes, and practical projects flow.",
        primary_color="#2563EB",
        secondary_color="#1D4ED8",
        accent_color="#3B82F6",
        header_style="two_column",
        font_name="Helvetica",
        font_bold="Helvetica-Bold",
        font_oblique="Helvetica-Oblique",
        docx_font_name="Calibri",
        section_order=["summary", "certifications", "skills", "projects", "experience", "education", "additional_background", "target_role"],
        recommended_roles=["AI Engineer", "Software Engineer", "Product Manager", "All Disciplines"],
    ),
    "harvard_consulting": ResumeTemplate(
        id="harvard_consulting",
        name="Harvard Consulting (MBB)",
        badge="🏛️ Ivy Standard",
        inspired_by="McKinsey / BCG / Bain / Harvard Business School Standard",
        description="Centered formal layout with Deep Oxford Navy (#0F2A47) and Charcoal accents, 1.2pt solid divider bars, right-aligned dates, and dense quantified impact bullets in classic Ivy-League serif typography.",
        primary_color="#0F2A47",
        secondary_color="#111827",
        accent_color="#334155",
        header_style="centered_classic",
        font_name="Times-Roman",
        font_bold="Times-Bold",
        font_oblique="Times-Italic",
        docx_font_name="Times New Roman",
        section_order=["summary", "experience", "projects", "education", "certifications", "skills", "additional_background", "target_role"],
        recommended_roles=["Management Consulting", "Investment Banking", "Strategy", "Operations", "Finance", "Corporate Development"],
    ),
    "corporate_elite": ResumeTemplate(
        id="corporate_elite",
        name="Corporate Elite",
        badge="👑 Fortune 500",
        inspired_by="Fortune 500 Executive Leadership / Law / Finance",
        description="Prestigious Deep Navy (#1A3A5C) structure accented with Antique Gold (#D4AF37) header bars and divider rules, featuring a styled Executive Core Competencies matrix.",
        primary_color="#1A3A5C",
        secondary_color="#D4AF37",
        accent_color="#C59B27",
        header_style="accent_bar",
        font_name="Helvetica",
        font_bold="Helvetica-Bold",
        font_oblique="Helvetica-Oblique",
        docx_font_name="Arial",
        section_order=["summary", "skills", "experience", "projects", "education", "certifications", "additional_background", "target_role"],
        recommended_roles=["Corporate Leadership", "Healthcare", "Legal & Compliance", "Accounting", "HR", "C-Suite & VP"],
    ),
    "tech_specialist": ResumeTemplate(
        id="tech_specialist",
        name="Tech Specialist & AI Innovator",
        badge="⚡ AI & Cloud",
        inspired_by="Silicon Valley / Cloud / AI Specialist Standard",
        description="Skills-first and repository-driven engineering layout with Electric Violet (#7C3AED) and Cyan (#0284C7) accents, top-level Technical Skills Matrix, and prominent clickable GitHub links.",
        primary_color="#7C3AED",
        secondary_color="#0284C7",
        accent_color="#06B6D4",
        header_style="tech_grid",
        font_name="Helvetica",
        font_bold="Helvetica-Bold",
        font_oblique="Helvetica-Oblique",
        docx_font_name="Segoe UI",
        section_order=["summary", "skills", "projects", "certifications", "experience", "education", "additional_background", "target_role"],
        recommended_roles=["Machine Learning", "Data Science", "Cloud / DevOps", "Full-Stack Dev", "AI Engineering", "Systems Engineering"],
    ),
}

# Aliases for robust cross-component and legacy compatibility
TEMPLATE_ALIASES = {
    "harvard": "harvard_consulting",
    "mbb": "harvard_consulting",
    "tech": "tech_specialist",
    "tech_innovator": "tech_specialist",
    "corporate": "corporate_elite",
    "minimal": "corporate_elite",
    "minimalist": "corporate_elite",
}


import re

def get_template(template_id: str) -> ResumeTemplate:
    clean_id = (template_id or "modern").lower().strip()
    clean_id = re.sub(r'[^a-z0-9_\-]', '', clean_id)
    resolved_id = TEMPLATE_ALIASES.get(clean_id, clean_id)
    return AVAILABLE_TEMPLATES.get(resolved_id, AVAILABLE_TEMPLATES["modern"])


def list_templates() -> List[Dict[str, Any]]:
    return [t.model_dump() for t in AVAILABLE_TEMPLATES.values()]
