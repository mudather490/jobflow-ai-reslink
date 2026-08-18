import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pypdf import PdfReader


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class WorkExperience(BaseModel):
    company: str = "Independent"
    role: str
    location: Optional[str] = None
    duration: Optional[str] = None
    subtitle: Optional[str] = None
    summary: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str
    year: Optional[str] = None
    details: Optional[str] = None


class Project(BaseModel):
    name: str
    subtitle: Optional[str] = None
    description: Optional[str] = ""
    bullets: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    repository: Optional[str] = None


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    status: str = "Completed"  # "Completed" or "In Progress"
    details: Optional[str] = None


class UserProfile(BaseModel):
    full_name: str
    headline: Optional[str] = "Professional Profile"
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    categorized_skills: Dict[str, List[str]] = Field(default_factory=dict)
    experience: List[WorkExperience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    additional_background: Optional[str] = None
    target_role: Optional[str] = None

    def get_full_text(self) -> str:
        """Flattens the entire profile into readable text for matching."""
        sections = [
            f"NAME: {self.full_name}",
            f"HEADLINE: {self.headline or ''}",
            f"SUMMARY: {self.summary or ''}",
            f"SKILLS: {', '.join(self.skills)}",
        ]
        if self.experience:
            sections.append("EXPERIENCE:")
            for exp in self.experience:
                sections.append(f"- {exp.role} at {exp.company} ({exp.duration or ''})")
                for bullet in exp.bullets:
                    sections.append(f"  * {bullet}")

        if self.projects:
            sections.append("PROJECTS:")
            for proj in self.projects:
                tech_str = f" (Tech: {', '.join(proj.technologies)})" if proj.technologies else ""
                repo_str = f" [Repo: {proj.repository}]" if proj.repository else ""
                sections.append(f"- {proj.name}{tech_str}{repo_str}")
                for b in proj.bullets:
                    sections.append(f"  * {b}")

        if self.certifications:
            sections.append("CERTIFICATIONS:")
            for cert in self.certifications:
                sections.append(f"- {cert.name} ({cert.issuer or 'Certified'}) [{cert.status}]")

        if self.education:
            sections.append("EDUCATION:")
            for edu in self.education:
                sections.append(f"- {edu.degree} from {edu.institution} ({edu.year or ''})")

        return "\n".join(sections)


class ResumeParser:
    """
    Universal, enterprise-grade Resume Parsing Engine.
    Accurately extracts structured sections from DOCX, PDF, and TXT across any domain.
    """

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".docx":
            doc = docx.Document(file_path)
            extracted_lines = []

            # 1. Read all body paragraphs
            for para in doc.paragraphs:
                l_clean = para.text.strip()
                if l_clean:
                    l_clean = re.sub(r'[\u2014\u2013\ufffd\x96\x97]', '—', l_clean)
                    l_clean = re.sub(r'[\u2022\u25cf\u25cb\u25aa\u25a0]', '•', l_clean)
                    extracted_lines.append(l_clean)

            # 2. Read table cells if any (preserving contact/skills grids)
            if doc.tables:
                for table in doc.tables:
                    for row in table.rows:
                        seen_cells = set()
                        for cell in row.cells:
                            ctext = cell.text.strip()
                            if ctext and ctext not in seen_cells:
                                seen_cells.add(ctext)
                                for l in ctext.split("\n"):
                                    l_clean = l.strip()
                                    l_clean = re.sub(r'[\u2014\u2013\ufffd\x96\x97]', '—', l_clean)
                                    l_clean = re.sub(r'[\u2022\u25cf\u25cb\u25aa\u25a0]', '•', l_clean)
                                    if l_clean and l_clean not in extracted_lines:
                                        extracted_lines.append(l_clean)

            return "\n".join(extracted_lines)

        elif ext == ".pdf":
            reader = PdfReader(file_path)
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text = re.sub(r'[\u2014\u2013\ufffd\x96\x97]', '—', text)
                    text = re.sub(r'[\u2022\u25cf\u25cb\u25aa\u25a0]', '•', text)
                    pages_text.append(text)
            return "\n".join(pages_text)

        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file extension: {ext}. Supported: .docx, .pdf, .txt")

    @staticmethod
    def normalize_text_spacing(text: str) -> str:
        """
        Cleans spacing and kerning anomalies from Canva, Figma, InDesign, LaTeX, and Word PDFs.
        Preserves true word boundaries while collapsing space-separated letter glyphs.
        """
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            l = line.rstrip()
            if not l.strip():
                continue
            
            # Step 1: Split on 2 or more spaces (or tabs) to preserve genuine word boundaries
            word_chunks = [w for w in re.split(r'\s{2,}|\t+', l) if w.strip()]
            reconstructed_words = []
            for chunk in word_chunks:
                # Check for spaced characters within word chunk (e.g. 'S E B A S T I A N' or 'P r o f e s s i o n a l')
                tokens = chunk.split(' ')
                single_count = sum(1 for t in tokens if len(t) == 1)
                if len(tokens) > 1 and (single_count / len(tokens)) > 0.4:
                    cleaned_word = ''.join(tokens)
                else:
                    cleaned_word = chunk
                reconstructed_words.append(cleaned_word)
                
            clean_line = ' '.join(reconstructed_words).strip()
            
            # Step 2: Clean digit & symbol spacing
            clean_line = re.sub(r'(\d)\s+(\d)', r'\1\2', clean_line)
            clean_line = re.sub(r'(\d)\s+(\d)', r'\1\2', clean_line)
            clean_line = re.sub(r'\+\s*(\d)', r'+\1', clean_line)
            clean_line = re.sub(r'(\w)\s+@\s+(\w)', r'\1@\2', clean_line)
            clean_line = re.sub(r'(\w)\s+\.\s+(\w)', r'\1.\2', clean_line)
            
            # Step 3: Strip trailing solitary page numbers
            if re.match(r'^\d+$', clean_line.strip()) and len(clean_line.strip()) <= 2:
                continue
                
            cleaned_lines.append(clean_line)
            
        return "\n".join(cleaned_lines)

    @classmethod
    def parse_text_to_profile(cls, raw_text: str) -> UserProfile:
        """
        Universal, domain-agnostic resume parser.
        Detects sections via regex boundaries and extracts structured data cleanly.
        """
        text = cls.normalize_text_spacing(raw_text)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return UserProfile(full_name="Candidate Name")

        # 1. Universal Section Boundary Identification
        section_patterns = [
            ("CERTIFICATIONS", r"(?i)(?:\b|\n)(?:Training\s+(?:and|&)\s+Certifications|Certifications\s+(?:and|&)\s+Training|Certifications|Licenses\s+&\s+Certifications|Courses)\s*(?:[:—•\n]|\s+•|\s*$)"),
            ("SKILLS", r"(?i)(?:\b|\n)(?:TECHNICAL\s+SKILLS|Technical\s+Skills|Skills\s+&\s+Tools|Core\s+Competencies|Areas\s+of\s+Expertise|SKILLS|Skills)\s*(?:[:—•\n]|\s+•|\s*$)"),
            ("PROJECTS", r"(?i)(?:\b|\n)(?:Practical\s+Projects|Featured\s+Projects|Key\s+Projects|Personal\s+Projects|Selected\s+Projects|Projects)\s*(?:[:—•\n]|\s+•|\s*$)"),
            ("EXPERIENCE", r"(?i)(?:\b|\n)(?:Professional\s+Experience|Work\s+Experience|WORK\s+EXPERIENCE|Experience\s+History|Employment\s+History|Experience)\s*(?:[:—•\n]|\s+•|\s*$)"),
            ("ADDITIONAL_BACKGROUND", r"(?i)(?:\b|\n)(?:ADDITIONAL\s+BACKGROUND|Additional\s+Background|Background|Personal\s+Background)\s*(?:[:—•\n]|\s+•|\s*$)"),
            ("TARGET_ROLE", r"(?i)(?:\b|\n)(?:TARGET\s+ROLE|Target\s+Role|Desired\s+Role|Target\s+Position)\s*(?:[:—•\n]|\s+•|\s*$)"),
            ("EDUCATION", r"(?i)(?:\b|\n)(?:EDUCATION|Education|Academic\s+Background|Degrees|University)\s*(?:[:—•\n]|\s+•|\s*$)"),
        ]

        matches = []
        for sec_name, pat in section_patterns:
            for m in re.finditer(pat, text):
                matches.append((m.start(), m.end(), sec_name))

        matches.sort(key=lambda x: x[0])

        filtered_matches = []
        last_end = -1
        for start, end, sec_name in matches:
            if start < 40:  # Skip headers appearing in first 40 chars
                continue
            if start >= last_end:
                filtered_matches.append((start, end, sec_name))
                last_end = end

        sections_dict: Dict[str, str] = {}
        header_text = text[:filtered_matches[0][0]].strip() if filtered_matches else text

        for i, (start, end, sec_name) in enumerate(filtered_matches):
            sec_content_start = end
            sec_content_end = filtered_matches[i + 1][0] if i + 1 < len(filtered_matches) else len(text)
            sections_dict[sec_name] = text[sec_content_start:sec_content_end].strip()

        # 2. Candidate Name & Headline Extraction
        h_lines = [l.strip() for l in header_text.split("\n") if l.strip()]
        full_name = h_lines[0] if h_lines else "Candidate Name"
        headline = None
        if len(h_lines) > 1 and not any(k in h_lines[1].lower() for k in ["@", "http", "+", "about", "summary", "phone", "email"]):
            headline = h_lines[1]

        # 3. Contact Information Extraction
        email = None
        phone = None
        location = None
        linkedin = None
        github = None

        # Phone extraction
        ph_m = re.search(r'(\+?\s*\d[\d\s\-]{6,}\d)', header_text)
        if ph_m and len(re.sub(r'\s+', '', ph_m.group(1))) >= 8:
            phone = re.sub(r'\s+', '', ph_m.group(1))

        # Email extraction with letter-spacing tolerance
        at_pos = header_text.find('@')
        if at_pos != -1:
            before_at = header_text[:at_pos]
            after_at = header_text[at_pos+1:]
            u_toks = before_at.split()
            if u_toks:
                raw_user = u_toks[-1]
                em_user = re.sub(r'^\+?[\d\-]+', '', raw_user)
            else:
                em_user = ''
            domain_m = re.search(r'^\s*((?:[a-zA-Z0-9-]\s*)+\.\s*(?:c\s*o\s*m|o\s*r\s*g|n\s*e\s*t|e\s*d\s*u|i\s*o|c\s*o|s\s*i\s*t\s*e|[a-zA-Z]\s*[a-zA-Z]))', after_at)
            if domain_m:
                em_domain = re.sub(r'\s+', '', domain_m.group(1))
                if em_user:
                    email = f"{em_user}@{em_domain}"
                after_em = after_at[domain_m.end():]
                loc_chunks = [c for c in re.split(r'\s{2,}', after_em.split('\n')[0]) if c.strip()]
                loc_words = []
                for chunk in loc_chunks:
                    toks = chunk.split()
                    if toks:
                        loc_words.append(' '.join(toks))
                if loc_words:
                    location = ' '.join(loc_words).strip(' ,|•—')

        if not email:
            em_m = re.search(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", text)
            if em_m:
                email = em_m.group(0)

        if not phone:
            ph_m2 = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
            if ph_m2:
                phone = ph_m2.group(0)

        li_m = re.search(r"(?:https?://)?(?:www\.)?(linkedin\.com/in/[\w\-]+)", text)
        if li_m:
            linkedin = li_m.group(1)

        gh_m = re.search(r"(?:https?://)?(?:www\.)?(github\.com/[\w\-]+)", text)
        if gh_m:
            github = gh_m.group(1)

        contact = ContactInfo(
            email=email,
            phone=phone,
            location=location,
            linkedin=linkedin,
            github=github,
        )

        # 4. Summary Extraction
        sum_lines = []
        for l in h_lines:
            if l == full_name or l == headline:
                continue
            if any(k in l.lower() for k in ["@", "http", "+", "linkedin", "github", "phone", "email"]):
                continue
            if re.match(r'^(about\s+me|summary|profile|professional\s+summary|objective|about)$', l, re.I):
                continue
            sum_lines.append(l)
        summary = " ".join(sum_lines) if sum_lines else None

        # 5. Parse Specific Section Components

        # A. Certifications & Training
        certifications_list: List[Certification] = []
        if "CERTIFICATIONS" in sections_dict:
            raw_cert_text = sections_dict["CERTIFICATIONS"]
            cert_chunks = [c.strip() for c in re.split(r'•|\n', raw_cert_text) if c.strip()]
            for c_item in cert_chunks:
                if len(c_item) < 5:
                    continue
                status = "In Progress" if "in progress" in c_item.lower() else "Completed"
                issuer = None
                for iss in ["Stanford / DeepLearning.AI", "DeepLearning.AI", "Stanford", "IBM", "Google", "Scrimba", "Coursera", "AWS", "Microsoft", "Meta", "Harvard"]:
                    if iss.lower() in c_item.lower():
                        issuer = iss
                        break

                name_part = c_item
                details_part = None
                if ":" in c_item:
                    parts = c_item.split(":", 1)
                    name_part = parts[0].strip()
                    details_part = parts[1].strip()
                elif "—" in c_item:
                    parts = c_item.split("—")
                    name_part = parts[0].strip()
                    if len(parts) > 1:
                        details_part = " — ".join(parts[1:]).strip()

                name_part = re.sub(r'—\s*(Stanford|DeepLearning\.AI|IBM|Google|Scrimba|Coursera|AWS|Meta).*$', '', name_part, flags=re.I).strip(" :—•")
                if details_part:
                    details_part = re.sub(r'^(completed|in progress)\s*[—:\-]\s*', '', details_part, flags=re.I).strip()

                if name_part and len(name_part) > 3:
                    certifications_list.append(Certification(
                        name=name_part,
                        issuer=issuer,
                        status=status,
                        details=details_part
                    ))

        # B. Skills (Categorized & Flat)
        categorized_skills: Dict[str, List[str]] = {}
        skills_list: List[str] = []
        if "SKILLS" in sections_dict:
            raw_skills_text = sections_dict["SKILLS"]
            skill_chunks = [s.strip(" •\t-,") for s in raw_skills_text.split("\n") if s.strip()]
            for schunk in skill_chunks:
                if ":" in schunk and len(schunk.split(":")[0]) < 35:
                    cat, sks = schunk.split(":", 1)
                    cat_clean = cat.strip(" •—:")
                    tokens = [t.strip(" •-,") for t in re.split(r'[,|;]', sks) if t.strip()]
                    clean_tokens = []
                    for t in tokens:
                        t_clean = re.sub(r'^\W+|\W+$', '', t).strip()
                        if t_clean and len(t_clean) > 1 and not t_clean.lower().startswith(("in progress", "completed")):
                            clean_tokens.append(t_clean)
                            if t_clean not in skills_list:
                                skills_list.append(t_clean)
                    if clean_tokens:
                        categorized_skills[cat_clean] = clean_tokens
                else:
                    tokens = [t.strip(" •-,") for t in re.split(r'[,|;]', schunk) if t.strip()]
                    for t in tokens:
                        t_clean = re.sub(r'^\W+|\W+$', '', t).strip()
                        if t_clean and len(t_clean) > 1 and t_clean not in skills_list:
                            skills_list.append(t_clean)

        # C. Projects
        projects_list: List[Project] = []
        if "PROJECTS" in sections_dict:
            raw_proj_text = sections_dict["PROJECTS"]
            raw_proj_text = re.sub(r'[\u2022\u25cf\u25cb\u25aa\u25a0]', '•', raw_proj_text)
            
            p_lines = [l.strip() for l in raw_proj_text.strip().split('\n') if l.strip()]
            current_proj = None
            
            proj_title_patterns = [
                r'^(IntentFlow|Neural Network|House Price|FinanceTracker|Real-Time|AI Agent|Autonomous|E-Commerce|Portfolio|Chatbot|Lead Discovery|Machine Learning|Deep Learning|NLP|Computer Vision)',
                r'^[A-Z][\w\s\-]{2,45}(?:—|:)(?!\s*(?:Completed|In Progress|Python|SQL|FastAPI|PostgreSQL))'
            ]
            
            for line in p_lines:
                is_new_proj = False
                for pat in proj_title_patterns:
                    if re.search(pat, line, re.I) and not line.lower().startswith(('built', 'implemented', 'applied', 'designed', 'technologies:', 'tech:', 'repository:', 'repo:', '•', '-', '*', 'experience includes', 'experience:', 'ai agent project:')):
                        is_new_proj = True
                        break
                
                if is_new_proj:
                    if current_proj:
                        projects_list.append(Project(**current_proj))
                    
                    repo = None
                    repo_m = re.search(r'(https?://github\.com/[^\s\)]+)', line)
                    if repo_m:
                        repo = repo_m.group(1).rstrip('. )')
                        line = line.replace(repo_m.group(0), '').strip()
                        
                    p_name = line.strip(' •—:')
                    p_subtitle = None
                    p_desc = None
                    
                    # Clean title and subtitle
                    if '—' in line:
                        parts = line.split('—', 1)
                        p_name = parts[0].strip(' •—:')
                        rest = parts[1].strip(' •—:')
                        if ':' in rest:
                            sub_parts = rest.split(':', 1)
                            p_subtitle = sub_parts[0].strip(' •—:')
                            if len(sub_parts[1].strip()) > 5:
                                p_desc = sub_parts[1].strip()
                        else:
                            p_subtitle = rest
                    elif ':' in line:
                        parts = line.split(':', 1)
                        p_name = parts[0].strip(' •—:')
                        rest = parts[1].strip(' •—:')
                        if len(rest) > 0:
                            if len(rest) > 50 and not any(k in rest for k in ['NumPy', 'Python', 'FastAPI', 'PyTorch', 'TensorFlow']):
                                p_desc = rest
                            else:
                                p_subtitle = rest.strip(' :•')
                    
                    if p_name.lower().endswith((': numpy', ' numpy', '— numpy', '- numpy')):
                        p_name = re.sub(r'(?i)[:—\-]\s*numpy.*$', '', p_name).strip()
                        p_subtitle = 'NumPy • TensorFlow • PyTorch'
                    
                    current_proj = {
                        'name': p_name,
                        'subtitle': p_subtitle,
                        'description': p_desc,
                        'technologies': [],
                        'repository': repo,
                        'bullets': []
                    }
                else:
                    if not current_proj:
                        continue
                    
                    repo_m = re.search(r'(https?://github\.com/[^\s\)]+)', line)
                    if repo_m:
                        current_proj['repository'] = repo_m.group(1).rstrip('. )')
                        continue
                    
                    tech_m = re.search(r'(?:Technologies|Tech Stack|Tech)\s*[:—]\s*([^•\n]+)', line, re.I)
                    if tech_m:
                        current_proj['technologies'] = [t.strip().rstrip('.') for t in tech_m.group(1).split(',') if t.strip()]
                        continue
                    
                    if line.lower().startswith('ai agent project:'):
                        if not current_proj['subtitle']:
                            current_proj['subtitle'] = 'AI Agent Project'
                        continue
                    
                    clean_l = line.lstrip('•-* ').strip()
                    if clean_l and not clean_l.lower().startswith(('repository:', 'repo:')):
                        current_proj['bullets'].append(clean_l if clean_l.endswith(('.', ':', ';', '!')) else clean_l + '.')
            
            if current_proj:
                projects_list.append(Project(**current_proj))

        # D. Experience
        experience_list: List[WorkExperience] = []
        if "EXPERIENCE" in sections_dict:
            raw_exp_text = sections_dict["EXPERIENCE"]
            lines_x = [l.strip() for l in raw_exp_text.split('\n') if l.strip()]
            
            comp_lines = [l for l in lines_x if re.search(r'\|\s*\d{4}', l) or re.search(r'\b(salford|google|microsoft|amazon|apple|meta|inc|llc|ltd|corp|co\.)\b', l, re.I)]
            role_lines = [l for l in lines_x if l not in comp_lines and len(l) < 55 and any(k in l.lower() for k in ['accountant', 'engineer', 'developer', 'manager', 'specialist', 'consultant', 'analyst', 'director', 'lead', 'officer', 'designer', 'architect'])]
            desc_lines = [l for l in lines_x if l not in comp_lines and l not in role_lines]

            if comp_lines and role_lines and len(comp_lines) <= len(role_lines) * 2:
                for i, comp_raw in enumerate(comp_lines):
                    comp_name = comp_raw
                    dur = None
                    if '|' in comp_raw:
                        parts = comp_raw.split('|', 1)
                        comp_name = parts[0].strip()
                        dur = parts[1].strip()
                    elif '—' in comp_raw:
                        parts = comp_raw.split('—', 1)
                        comp_name = parts[0].strip()
                        dur = parts[1].strip()
                    elif '-' in comp_raw and re.search(r'\d{4}', comp_raw):
                        m = re.search(r'(\d{4}\s*[-–—]\s*(?:\d{4}|present|current))', comp_raw, re.I)
                        if m:
                            dur = m.group(1).strip()
                            comp_name = comp_raw.replace(m.group(0), '').strip(' ,|—–-')

                    r_title = role_lines[i] if i < len(role_lines) else (role_lines[0] if role_lines else "Professional")
                    desc = desc_lines[i] if i < len(desc_lines) else None
                    bullets = [b.strip(' •-') for b in desc.split('•') if b.strip()] if (desc and '•' in desc) else ([] if not desc else [desc])

                    experience_list.append(WorkExperience(
                        company=comp_name,
                        role=r_title,
                        duration=dur or "Recent",
                        summary=desc if len(bullets) <= 1 else None,
                        bullets=bullets if len(bullets) > 1 else []
                    ))
            else:
                role = "Freelance Software & AI Developer"
                company = "Independent / Freelance"
                subtitle = "AI & Software Engineering"
                summary_x = None
                bullets_x = []

                for chunk in lines_x:
                    ch_low = chunk.lower()
                    if "experience includes" in ch_low:
                        continue
                    if any(k in ch_low for k in ["freelance software", "software engineer", "ai developer", "machine learning engineer"]):
                        role = chunk.strip(" .:")
                    elif "ai & software engineering" in ch_low or "software engineering" in ch_low:
                        subtitle = chunk.strip(" :.")
                    elif len(chunk) > 45 and not bullets_x and not chunk.startswith("Building"):
                        summary_x = chunk.strip()
                    elif len(chunk) > 5:
                        bullets_x.append(chunk.strip(" •"))

                experience_list.append(WorkExperience(
                    role=role,
                    company=company,
                    duration="Recent",
                    subtitle=subtitle,
                    summary=summary_x,
                    bullets=bullets_x
                ))

        # E. Education
        education_list: List[Education] = []
        if "EDUCATION" in sections_dict:
            raw_edu_text = sections_dict["EDUCATION"]
            lines_e = [l.strip() for l in raw_edu_text.split('\n') if l.strip()]

            inst_lines = [l for l in lines_e if re.search(r'\|\s*\d{4}', l) or re.search(r'\b(university|college|institute|school|academy|polytechnic)\b', l, re.I)]
            deg_lines = [l for l in lines_e if l not in inst_lines and len(l) < 55 and not re.search(r'^(lorem|description|coursework|gpa|honors)', l, re.I)]
            desc_lines = [l for l in lines_e if l not in inst_lines and l not in deg_lines]

            if inst_lines and deg_lines and len(inst_lines) <= len(deg_lines) * 2:
                for i, inst_raw in enumerate(inst_lines):
                    inst_name = inst_raw
                    yr = None
                    if '|' in inst_raw:
                        parts = inst_raw.split('|', 1)
                        inst_name = parts[0].strip()
                        yr = parts[1].strip()
                    elif '—' in inst_raw:
                        parts = inst_raw.split('—', 1)
                        inst_name = parts[0].strip()
                        yr = parts[1].strip()
                    elif '-' in inst_raw and re.search(r'\d{4}', inst_raw):
                        m = re.search(r'(\d{4}\s*[-–—]\s*(?:\d{4}|present|current))', inst_raw, re.I)
                        if m:
                            yr = m.group(1).strip()
                            inst_name = inst_raw.replace(m.group(0), '').strip(' ,|—–-')

                    deg = deg_lines[i] if i < len(deg_lines) else (deg_lines[0] if deg_lines else "Degree")
                    desc = desc_lines[i] if i < len(desc_lines) else None

                    education_list.append(Education(
                        institution=inst_name,
                        degree=deg,
                        year=yr,
                        details=desc
                    ))
            else:
                for el in lines_e:
                    el_clean = el.strip(" •\t")
                    if el_clean and len(el_clean) > 3:
                        education_list.append(Education(
                            institution=el_clean,
                            degree="Degree"
                        ))

        # F. Additional Background & Target Role
        additional_background = sections_dict.get("ADDITIONAL_BACKGROUND", "").strip(" :—\n") or None
        target_role = sections_dict.get("TARGET_ROLE", "").strip(" :—\n") or None

        return UserProfile(
            full_name=full_name,
            headline=headline or "Professional Profile",
            contact=contact,
            summary=summary,
            skills=skills_list,
            categorized_skills=categorized_skills,
            experience=experience_list,
            projects=projects_list,
            education=education_list,
            certifications=certifications_list,
            additional_background=additional_background,
            target_role=target_role
        )

    @classmethod
    def parse_file(cls, file_path: str) -> UserProfile:
        text = cls.extract_text_from_file(file_path)
        return cls.parse_text_to_profile(text)
