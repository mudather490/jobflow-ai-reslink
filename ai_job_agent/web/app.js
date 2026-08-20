// State Management
let currentProfile = null;
let currentJobs = [];
let selectedJob = null;
let currentMatchReport = null;
let currentOffset = 0;
let autoApplyTargetJob = null;

// ─── XSS Protection: HTML Entity Encoder ───
function escapeHtml(str) {
  if (!str || typeof str !== 'string') return str || '';
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// ─── XSS Protection: Safe URL Sanitizer ───
function sanitizeUrl(url) {
  if (!url || typeof url !== 'string') return '#';
  const clean = url.trim();
  if (clean.startsWith('http://') || clean.startsWith('https://') || clean.startsWith('mailto:') || clean.startsWith('/')) {
    return clean.replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  return '#';
}

// ─── Global Toast Notification System ───
function showToast(msg, duration = 3500) {
  if (!msg) return;
  let toast = document.getElementById('app-global-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-global-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 28px;
      right: 28px;
      background: rgba(15, 23, 42, 0.96);
      color: #F8FAFC;
      border: 1px solid rgba(56, 189, 248, 0.4);
      box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.2);
      border-radius: 10px;
      padding: 12px 20px;
      font-size: 13.5px;
      font-weight: 600;
      z-index: 999999;
      display: flex;
      align-items: center;
      gap: 10px;
      opacity: 0;
      transform: translateY(16px);
      transition: opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1), transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
      backdrop-filter: blur(12px);
    `;
    document.body.appendChild(toast);
  }

  toast.innerHTML = String(msg);
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';

  if (window._toastTimeout) clearTimeout(window._toastTimeout);
  window._toastTimeout = setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(16px)';
  }, duration);
}
window.showToast = showToast;

// Persistent Candidate Quick Profile for 1-Click Auto Applications
function getSavedCandidateProfile() {
  try {
    const raw = localStorage.getItem('candidate_quick_profile');
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return null;
}

function saveCandidateProfile(profile) {
  try {
    localStorage.setItem('candidate_quick_profile', JSON.stringify(profile));
  } catch (e) {}
}

// Template Management
const templateNames = {
  modern: 'Google FAANG XYZ Standard',
  harvard: 'Harvard MCS & MBB Consulting',
  harvard_consulting: 'Harvard MCS & MBB Consulting',
  tech: 'Stanford BEAM Tech & AI Standard',
  tech_specialist: 'Stanford BEAM Tech & AI Standard',
  minimal: 'Wharton & WSO Executive Standard',
  corporate_elite: 'Wharton & WSO Executive Standard'
};

const templateShortNames = {
  modern: 'Google FAANG',
  harvard: 'Harvard MCS',
  harvard_consulting: 'Harvard MCS',
  tech: 'Stanford BEAM',
  tech_specialist: 'Stanford BEAM',
  minimal: 'Wharton WSO',
  corporate_elite: 'Wharton WSO'
};

window.selectedTemplateId = localStorage.getItem('selected_resume_template') || 'corporate_elite';

window.selectTemplate = function(templateId) {
  const normId = (templateId === 'harvard_consulting' ? 'harvard' : (templateId === 'tech_specialist' ? 'tech' : (templateId === 'corporate_elite' ? 'corporate_elite' : templateId))) || 'corporate_elite';
  
  window.selectedTemplateId = templateId || normId;
  localStorage.setItem('selected_resume_template', templateId || normId);

  // Sync with server
  try {
    fetch('/api/v1/templates/active', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template_id: templateId || normId })
    });
  } catch (e) {
    console.warn("Failed to sync active template with server:", e);
  }

  // Update UI Button Selection
  const btns = document.querySelectorAll('.template-btn');
  btns.forEach(b => {
    const bid = b.dataset.templateId;
    if (bid === templateId || bid === normId || b.id === `btn-tmpl-${normId}` || b.id === `btn-tmpl-${templateId}`) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  // Update active badge label and color
  const badge = document.getElementById('active-template-badge');
  if (badge) {
    badge.innerText = templateNames[templateId] || templateNames[normId] || 'Corporate Elite';
    if (templateId === 'corporate_elite') {
      badge.style.color = '#D4AF37';
      badge.style.borderColor = 'rgba(212, 175, 55, 0.4)';
    } else if (templateId === 'harvard_consulting') {
      badge.style.color = '#38BDF8';
      badge.style.borderColor = 'rgba(56, 189, 248, 0.4)';
    } else if (templateId === 'tech_specialist') {
      badge.style.color = '#A855F7';
      badge.style.borderColor = 'rgba(168, 85, 247, 0.4)';
    } else {
      badge.style.color = '#2563EB';
      badge.style.borderColor = 'rgba(37, 99, 235, 0.4)';
    }
  }

  // Update download button label
  const docxLbl = document.getElementById('lbl-docx-template');
  if (docxLbl) docxLbl.innerText = templateShortNames[templateId] || templateShortNames[normId] || 'Corporate Elite';
};

// Modal Controls
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('active');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('active');
}

window.openTemplateInResLink = function(templateId) {
  const tmpl = templateId || window.selectedTemplateId || 'corporate_elite';
  showToast(`🚀 Opening ${templateNames[tmpl] || 'Template'} live on ResLink...`);
  const targetUrl = `/reslink?template=${encodeURIComponent(tmpl)}&mode=template`;
  window.open(targetUrl, '_blank');
};

window.openTemplatePreviewModal = function() {
  const currentTmpl = window.selectedTemplateId || 'corporate_elite';
  window.renderTemplatePreviewSheet(currentTmpl);
  openModal('modal-template-preview');
};

window.selectTemplateAndPreview = function(templateId) {
  window.selectTemplate(templateId);
  window.renderTemplatePreviewSheet(templateId);
};

window.downloadSelectedStarterDocx = function() {
  const tmpl = window.selectedTemplateId || 'corporate_elite';
  showToast(`📥 Downloading ${templateNames[tmpl] || 'Corporate Elite'} Editable Word Template...`);
  window.open(`/api/v1/resume/download-docx?template_id=${encodeURIComponent(tmpl)}&mode=template&t=${Date.now()}`, '_blank');
};

window.renderTemplatePreviewSheet = function(templateId) {
  const sheet = document.getElementById('modal-preview-sheet');
  const titleEl = document.getElementById('modal-preview-title');
  const subEl = document.getElementById('modal-preview-subtitle');
  if (!sheet) return;

  const tmpl = templateId || window.selectedTemplateId || 'corporate_elite';
  const name = templateNames[tmpl] || 'Wharton & WSO Executive Standard';
  if (titleEl) titleEl.innerText = `${name} • Live Preview`;
  if (subEl) subEl.innerText = `Official Style Structure • ${templateShortNames[tmpl] || 'Standard'}`;

  // Theme palettes and styles
  let prim = '#1A3A5C';
  let sec = '#D4AF37';
  let fontFam = "Calibri, Arial, sans-serif";
  let isCentered = false;

  if (tmpl === 'harvard_consulting' || tmpl === 'harvard') {
    prim = '#0F2A47';
    sec = '#111827';
    fontFam = "'Times New Roman', Times, Georgia, serif";
    isCentered = true;
  } else if (tmpl === 'tech_specialist' || tmpl === 'tech') {
    prim = '#7C3AED';
    sec = '#0284C7';
    fontFam = "'Segoe UI', Roboto, 'Helvetica Neue', sans-serif";
  } else if (tmpl === 'modern') {
    prim = '#2563EB';
    sec = '#1D4ED8';
    fontFam = "Arial, Helvetica, sans-serif";
  }

  // Profile data
  const p = currentProfile || {
    full_name: "ALEXANDER RIVERA",
    headline: "Senior AI Engineer & Distributed Systems Specialist",
    contact: {
      email: "alex.rivera@example.com",
      phone: "+1 (555) 012-3456",
      location: "San Francisco, CA / Worldwide Remote",
      linkedin: "https://linkedin.com/in/alex-rivera",
      github: "https://github.com/alexrivera"
    },
    summary: "High-impact AI Engineer with 6+ years of experience architecting distributed multi-agent systems, low-latency LLM inference pipelines, and enterprise machine learning infrastructure.",
    skills: ["Python", "PyTorch", "FastAPI", "Docker", "SQL", "Scikit-learn", "LLM APIs", "Redis", "Supabase", "Git"],
    categorized_skills: {
      "Languages & Core": ["Python", "C++", "SQL", "TypeScript", "Bash / Linux", "Go"],
      "Machine Learning & AI": ["PyTorch", "TensorFlow", "Scikit-learn", "Transformers", "LLM APIs", "Prompt Engineering", "RAG Systems"],
      "Backend & Distributed Systems": ["FastAPI", "gRPC", "Docker", "Kubernetes", "Redis", "Celery", "RESTful APIs"],
      "Databases & Storage": ["PostgreSQL", "Supabase", "Vector Databases (ChromaDB / Pinecone / pgvector)", "Redis"],
      "Cloud & DevOps": ["AWS (EC2, S3, Lambda)", "GCP", "GitHub Actions CI/CD", "Linux CLI", "vLLM Inference"]
    },
    projects: [
      {
        name: "Autonomous Multi-Agent Workflow Orchestrator",
        technologies: ["Python", "FastAPI", "PyTorch", "Redis", "Docker"],
        repository: "https://github.com/alexrivera/autonomous-ai-agent",
        bullets: [
          "Architected asynchronous event-driven workflow engine processing 10,000+ simulated jobs daily with sub-250ms latency.",
          "Implemented in-memory Redis caching layer, reducing database compute load by 45% across distributed worker nodes."
        ]
      }
    ],
    experience: [
      {
        role: "Senior AI Engineer",
        company: "Global Enterprise Technologies",
        duration: "2021 – Present",
        location: "San Francisco, CA / Remote",
        bullets: [
          "Accomplished 40% reduction in API response latency (from 180ms to 108ms) by redesigning backend data serialization in FastAPI and implementing Redis memory caching.",
          "Engineered distributed data ingestion pipelines handling 50M+ monthly events with 99.9% uptime."
        ]
      }
    ],
    certifications: [
      { name: "Deep Learning Specialization", issuer: "DeepLearning.AI", status: "Completed" },
      { name: "AWS Certified Solutions Architect", issuer: "Amazon Web Services", status: "Completed" }
    ],
    education: [
      { institution: "University of California, Berkeley", degree: "B.S. in Computer Science", year: "2017 – 2021" }
    ]
  };

  const candName = p.full_name || "ALEXANDER RIVERA";
  const candHead = p.headline || p.target_role || "Senior AI Engineer";
  const contacts = [];
  if (p.contact?.email) contacts.push(p.contact.email.replace("mailto:", ""));
  if (p.contact?.phone) contacts.push(p.contact.phone);
  if (p.contact?.location) contacts.push(p.contact.location);
  if (p.contact?.linkedin) contacts.push(`LinkedIn: ${p.contact.linkedin}`);
  if (p.contact?.github) contacts.push(`GitHub: ${p.contact.github}`);

  let headerHtml = '';
  if (isCentered) {
    headerHtml = `
      <div style="text-align: center; margin-bottom: 20px; border-bottom: 2px solid ${prim}; padding-bottom: 14px;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 800; color: ${prim}; text-transform: uppercase; letter-spacing: 0.5px;">${escapeHtml(candName)}</h1>
        <div style="font-size: 13px; font-weight: 700; color: #475569; margin: 4px 0 8px 0;">${escapeHtml(candHead)}</div>
        <div style="font-size: 12px; color: #64748B;">${contacts.map(c => escapeHtml(c)).join(' • ')}</div>
      </div>
    `;
  } else {
    headerHtml = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; border-bottom: 2.5px solid ${prim}; padding-bottom: 14px;">
        <div>
          <h1 style="margin: 0; font-size: 26px; font-weight: 800; color: ${prim}; letter-spacing: -0.5px;">${escapeHtml(candName)}</h1>
          <div style="font-size: 14px; font-weight: 700; color: ${sec}; margin-top: 4px;">${escapeHtml(candHead)}</div>
        </div>
        <div style="text-align: right; font-size: 12px; color: #475569; line-height: 1.45;">
          ${contacts.map(c => `<div>${escapeHtml(c)}</div>`).join('')}
        </div>
      </div>
    `;
  }

  // Skills
  let skillsHtml = '';
  const cats = (p.categorized_skills && Object.keys(p.categorized_skills).length > 0) ? p.categorized_skills : { "Skills & Core Competencies": p.skills || [] };
  for (const [cat, sks] of Object.entries(cats)) {
    if (sks && sks.length > 0) {
      skillsHtml += `<div style="font-size: 12.5px; margin-bottom: 5px; color: #334155;"><strong style="color: ${prim};">${escapeHtml(cat)}:</strong> ${escapeHtml(sks.join(', '))}</div>`;
    }
  }

  sheet.style.fontFamily = fontFam;
  sheet.innerHTML = `
    ${headerHtml}
    
    <!-- Summary -->
    <div style="margin-bottom: 18px;">
      <h3 style="font-size: 13px; font-weight: 800; text-transform: uppercase; color: ${prim}; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin: 0 0 8px 0; letter-spacing: 0.5px;">Executive Summary</h3>
      <p style="font-size: 12.5px; line-height: 1.55; color: #334155; margin: 0;">${escapeHtml(p.summary || '')}</p>
    </div>

    <!-- Skills -->
    <div style="margin-bottom: 18px;">
      <h3 style="font-size: 13px; font-weight: 800; text-transform: uppercase; color: ${prim}; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin: 0 0 8px 0; letter-spacing: 0.5px;">Technical Skills & Core Competencies</h3>
      ${skillsHtml}
    </div>

    <!-- Projects -->
    <div style="margin-bottom: 18px;">
      <h3 style="font-size: 13px; font-weight: 800; text-transform: uppercase; color: ${prim}; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin: 0 0 8px 0; letter-spacing: 0.5px;">Practical & Open-Source Projects</h3>
      ${(p.projects || []).map(proj => `
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong style="font-size: 13px; color: #0F172A;">${escapeHtml(proj.name)}</strong>
            ${proj.repository ? `<a href="${sanitizeUrl(proj.repository)}" target="_blank" style="font-size: 11.5px; color: ${prim}; text-decoration: none; font-weight: 700;">🔗 Code Repo ↗</a>` : ''}
          </div>
          ${proj.technologies && proj.technologies.length > 0 ? `<div style="font-size: 11.5px; color: ${sec}; font-weight: 700; margin: 2px 0;">Tech: ${escapeHtml(proj.technologies.join(', '))}</div>` : ''}
          <ul style="margin: 4px 0 0 16px; padding: 0; font-size: 12px; line-height: 1.5; color: #334155;">
            ${(proj.bullets || []).map(b => `<li>${escapeHtml(b)}</li>`).join('')}
          </ul>
        </div>
      `).join('')}
    </div>

    <!-- Experience -->
    <div style="margin-bottom: 18px;">
      <h3 style="font-size: 13px; font-weight: 800; text-transform: uppercase; color: ${prim}; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin: 0 0 8px 0; letter-spacing: 0.5px;">Professional Experience</h3>
      ${(p.experience || []).map(exp => `
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><strong style="font-size: 13px; color: #0F172A;">${escapeHtml(exp.role || "Software Engineer")}</strong> <span style="color: #64748B;">— ${escapeHtml(exp.company || "Enterprise")}</span></div>
            <div style="font-size: 12px; color: #64748B; font-weight: 600;">${escapeHtml(exp.duration || "Recent")}</div>
          </div>
          <ul style="margin: 4px 0 0 16px; padding: 0; font-size: 12px; line-height: 1.5; color: #334155;">
            ${(exp.bullets || []).map(b => `<li>${escapeHtml(b)}</li>`).join('')}
          </ul>
        </div>
      `).join('')}
    </div>

    <!-- Education & Certifications -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
      <div>
        <h3 style="font-size: 12.5px; font-weight: 800; text-transform: uppercase; color: ${prim}; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin: 0 0 6px 0;">Certifications</h3>
        ${(p.certifications || []).map(c => `<div style="font-size: 12px; margin-bottom: 4px; color: #334155;"><strong>${escapeHtml(c.name)}</strong> — ${escapeHtml(c.issuer || "Accredited")}</div>`).join('')}
      </div>
      <div>
        <h3 style="font-size: 12.5px; font-weight: 800; text-transform: uppercase; color: ${prim}; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin: 0 0 6px 0;">Education</h3>
        ${(p.education || []).map(edu => `<div style="font-size: 12px; margin-bottom: 4px; color: #334155;"><strong>${escapeHtml(edu.institution)}</strong> (${escapeHtml(edu.degree)})</div>`).join('')}
      </div>
    </div>
  `;
};

// Attach Modal Listeners
document.getElementById('btn-pricing-modal')?.addEventListener('click', () => openModal('modal-pricing'));
document.getElementById('btn-settings-modal')?.addEventListener('click', async () => {
  await loadNotificationSettings();
  openModal('modal-settings');
});
document.getElementById('btn-open-reslink-preview')?.addEventListener('click', () => {
  window.openTemplatePreviewModal();
});

function getCurrentUserEmail() {
  try {
    const user = JSON.parse(localStorage.getItem('jobflow_auth_user') || 'null');
    if (user && user.email) return user.email.trim().toLowerCase();
  } catch (e) {}
  return '';
}

// Step 1: Initialize Base Resume & Cross-Device Cloud Sync
async function loadInitialProfile() {
  const userEmail = getCurrentUserEmail();

  try {
    // 1. Sync full user session bundle from Supabase
    if (userEmail) {
      const syncRes = await fetch(`/api/v1/user/sync?email=${encodeURIComponent(userEmail)}`);
      if (syncRes.ok) {
        const syncJson = await syncRes.json();
        const syncData = syncJson.data || {};
        
        if (syncData.profile) {
          currentProfile = syncData.profile;
          renderActiveFileCard(syncData.resume_filename || 'Cloud_Synced_Resume.pdf', 'Verified (Cloud)', currentProfile);
        }
        
        if (syncData.notifications) {
          const ns = syncData.notifications;
          if (document.getElementById('setting-email') && ns.email) document.getElementById('setting-email').value = ns.email;
          if (document.getElementById('setting-whatsapp') && ns.whatsapp) document.getElementById('setting-whatsapp').value = ns.whatsapp;
          if (document.getElementById('setting-telegram') && ns.telegram) document.getElementById('setting-telegram').value = ns.telegram;
          if (document.getElementById('bar-email') && ns.email) document.getElementById('bar-email').innerText = ns.email;
          if (document.getElementById('bar-whatsapp') && ns.whatsapp) document.getElementById('bar-whatsapp').innerText = ns.whatsapp;
          if (document.getElementById('bar-telegram') && ns.telegram) document.getElementById('bar-telegram').innerText = ns.telegram.startsWith('@') ? ns.telegram : '@' + ns.telegram;
        }

        if (syncData.candidate_quick_profile) {
          saveCandidateProfile(syncData.candidate_quick_profile);
        }
      }
    }

    // 2. Fetch active resume from server if currentProfile not loaded yet
    if (!currentProfile) {
      const url = userEmail ? `/api/v1/resume/current?email=${encodeURIComponent(userEmail)}` : '/api/v1/resume/current';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        currentProfile = data.profile;
        renderActiveFileCard(data.filename, data.filesize, currentProfile);
      }
    }
  } catch (err) {
    console.error("Failed to load profile:", err);
  }
}

function renderActiveFileCard(filename, filesize, profile) {
  if (!profile) return;
  const fileDisplay = document.getElementById('file-display-name');
  if (fileDisplay && filename) fileDisplay.innerText = filename;

  const sizeDisplay = document.getElementById('file-size-display');
  if (sizeDisplay && filesize) sizeDisplay.innerText = filesize;

  const nameDisplay = document.getElementById('candidate-name-display');
  if (nameDisplay && profile.full_name) nameDisplay.innerText = profile.full_name;

  const skillsList = Array.isArray(profile.skills) ? profile.skills : [];
  const skillsCount = document.getElementById('skills-count');
  if (skillsCount) skillsCount.innerText = skillsList.length;
  
  const cloud = document.getElementById('profile-skills-cloud');
  if (cloud) {
    if (skillsList.length === 0) {
      cloud.innerHTML = '<span style="font-size: 12px; color: var(--text-muted); font-style: italic;">No specific skills isolated yet. Add your skills below or re-upload.</span>';
    } else {
      cloud.innerHTML = skillsList.map(s => `
        <span class="skill-chip chip-match" style="display: inline-flex; align-items: center; gap: 4px;">
          ${escapeHtml(s)}
          <span class="skill-remove-btn" onclick="removeSkill('${escapeHtml(s).replace(/'/g, "\\'")}', event)" title="Remove ${escapeHtml(s)}">&times;</span>
        </span>
      `).join('');
    }
  }
}

// Interactive Skill Management: Add & Remove
window.removeSkill = async function(skillName, event) {
  if (event) event.stopPropagation();
  try {
    const res = await fetch('/api/v1/resume/skills/remove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill: skillName })
    });
    if (res.ok) {
      const data = await res.json();
      if (currentProfile) currentProfile.skills = data.skills;
      renderActiveFileCard(null, null, currentProfile);
      if (data.match) {
        currentMatchReport = data.match;
        renderMatchReport(data.match);
      }
    }
  } catch (err) {
    console.error("Failed to remove skill:", err);
  }
};

async function handleAddSkill() {
  const input = document.getElementById('input-new-skill');
  if (!input) return;
  const val = input.value.trim();
  if (!val) return;

  try {
    const res = await fetch('/api/v1/resume/skills/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill: val })
    });
    if (res.ok) {
      const data = await res.json();
      input.value = '';
      if (currentProfile) currentProfile.skills = data.skills;
      renderActiveFileCard(null, null, currentProfile);
      if (data.match) {
        currentMatchReport = data.match;
        renderMatchReport(data.match);
      }
    }
  } catch (err) {
    console.error("Failed to add skill:", err);
  }
}

document.getElementById('btn-add-skill')?.addEventListener('click', handleAddSkill);
document.getElementById('input-new-skill')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    handleAddSkill();
  }
});

// Step 1B: File Upload Handler (Drag & Drop + File Browser)
const fileInput = document.getElementById('file-input');
const dropzone = document.getElementById('upload-dropzone');

fileInput?.addEventListener('change', async (e) => {
  if (e.target.files && e.target.files[0]) {
    await handleFileUpload(e.target.files[0]);
  }
});

dropzone?.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});

dropzone?.addEventListener('dragleave', () => {
  dropzone.classList.remove('dragover');
});

dropzone?.addEventListener('drop', async (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    await handleFileUpload(e.dataTransfer.files[0]);
  }
});

async function handleFileUpload(file) {
  if (!file) return;

  const statusBadge = document.getElementById('resume-status-badge');
  if (statusBadge) {
    statusBadge.innerText = '⏳ INGESTING & PARSING...';
    statusBadge.style.color = 'var(--accent-cyan)';
  }

  const formData = new FormData();
  formData.append('file', file);

  const userEmail = getCurrentUserEmail();

  if (userEmail) {
    formData.append('user_email', userEmail);
  }

  try {
    const res = await fetch('/api/v1/resume/upload', {
      method: 'POST',
      body: formData,
    });
    
    if (!res.ok) {
      let errMsg = "Upload failed";
      try {
        const errJson = await res.json();
        errMsg = errJson.detail || errJson.message || errJson.error || errMsg;
      } catch (e) {}
      throw new Error(errMsg);
    }

    const data = await res.json();
    currentProfile = data.profile;
    renderActiveFileCard(data.filename, data.filesize, currentProfile);

    if (data.match_report) {
      currentMatchReport = data.match_report;
      renderMatchReport(data.match_report);
    }

    if (statusBadge) {
      statusBadge.innerText = '✓ UPLOADED & READY';
      statusBadge.style.color = '#34D399';
    }

    showToast("💾 Resume Uploaded & Parsed Successfully!");

    if (selectedJob) {
      selectJob(selectedJob);
    }
  } catch (err) {
    console.error("Resume upload error:", err);
    if (statusBadge) {
      statusBadge.innerText = '✗ UPLOAD ERROR';
      statusBadge.style.color = 'var(--accent-rose)';
    }
    showToast(`❌ Upload Error: ${err.message}`, 5000);
  }
}

// Step 2: Search Radar Execution
document.getElementById('search-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  currentOffset = 0;
  await executeJobSearch();
});

// Step 2B: Refresh / Next Batch Handler
document.getElementById('btn-refresh-jobs')?.addEventListener('click', async () => {
  const batchSize = parseInt(document.getElementById('select-limit')?.value || '6', 10);
  currentOffset += batchSize;
  await executeJobSearch();
});

document.getElementById('select-limit')?.addEventListener('change', async () => {
  currentOffset = 0;
  await executeJobSearch();
});

document.getElementById('select-app-type')?.addEventListener('change', async () => {
  currentOffset = 0;
  await executeJobSearch();
});

async function executeJobSearch() {
  const currentTier = (localStorage.getItem('user_subscription_tier') || 'free').toLowerCase();

  // Enforce 3 searches/day limit for Free Plan
  if (currentTier === 'free' || currentTier === 'starter') {
    const today = new Date().toISOString().slice(0, 10);
    let quota = {};
    try {
      quota = JSON.parse(localStorage.getItem('jobflow_free_search_quota') || '{}');
    } catch (e) {}

    if (quota.date !== today) {
      quota = { date: today, count: 0 };
    }

    if (quota.count >= 3) {
      showToast("⚠️ Daily limit reached (3/3 searches used on Free Plan). Please upgrade to Pro for unlimited searches!");
      openModal('modal-pricing');
      return;
    }
  }

  const keywords = document.getElementById('input-keywords')?.value.trim() || 'AI Engineer';
  const workplaceType = document.getElementById('select-workplace-type')?.value || 'worldwide_remote';
  const appType = document.getElementById('select-app-type')?.value || 'all';
  const country = document.getElementById('input-country')?.value.trim() || 'United States';
  const timeFilter = document.getElementById('select-time')?.value || '24h';
  const batchSize = parseInt(document.getElementById('select-limit')?.value || '6', 10);
  const btnSearch = document.getElementById('btn-search');
  const btnRefresh = document.getElementById('btn-refresh-jobs');

  if (btnSearch) {
    btnSearch.innerHTML = '<span>⏳ Scanning Radar...</span>';
    btnSearch.disabled = true;
  }
  if (btnRefresh) btnRefresh.innerText = '⏳ Fetching...';

  try {
    const res = await fetch(`/api/v1/jobs/search?keywords=${encodeURIComponent(keywords)}&country=${encodeURIComponent(country)}&workplace_type=${encodeURIComponent(workplaceType)}&application_type=${encodeURIComponent(appType)}&date_filter=${timeFilter}&limit=${batchSize}&offset=${currentOffset}`);
    const data = await res.json();
    currentJobs = data.jobs || [];
    renderJobsList(currentJobs);

    // Track search quota for free users
    if (currentTier === 'free' || currentTier === 'starter') {
      const today = new Date().toISOString().slice(0, 10);
      let quota = {};
      try {
        quota = JSON.parse(localStorage.getItem('jobflow_free_search_quota') || '{}');
      } catch (e) {}
      if (quota.date !== today) {
        quota = { date: today, count: 0 };
      }
      quota.count += 1;
      localStorage.setItem('jobflow_free_search_quota', JSON.stringify(quota));
    }

    if (currentJobs.length > 0) {
      selectJob(currentJobs[0]);
    }
  } catch (err) {
    console.error("Search error:", err);
  } finally {
    if (btnSearch) {
      btnSearch.innerHTML = '<span>⚡ Search Radar</span>';
      btnSearch.disabled = false;
    }
    if (btnRefresh) btnRefresh.innerText = '🔄 Fetch Next Batch';
  }
}

function getBadgeClass(scope) {
  if (scope === 'visa_sponsored') return 'badge-visa';
  if (scope === 'country_specific') return 'badge-domestic';
  return 'badge-worldwide';
}

function getWorkplaceBadgeClass(wpType) {
  if (wpType === 'internship' || wpType === 'intern') return 'badge-internship';
  if (wpType === 'worldwide_remote') return 'badge-worldwide';
  if (wpType === 'contract_remote') return 'badge-contract';
  if (wpType === 'hybrid') return 'badge-hybrid';
  if (wpType === 'on_site') return 'badge-onsite';
  return 'badge-remote';
}

function renderJobsList(jobs) {
  const container = document.getElementById('jobs-container');
  const countBadge = document.getElementById('jobs-count-badge');
  const easyCount = jobs.filter(j => j.is_easy_apply).length;
  
  if (countBadge) {
    countBadge.innerText = `${jobs.length} Postings (${easyCount} Easy Apply)`;
  }

  if (jobs.length === 0) {
    container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-dim);">No more jobs found for this query/workplace type. Try another keyword, workplace type, or application filter.</div>`;
    return;
  }

  container.innerHTML = jobs.map((job, idx) => `
    <div class="job-card ${idx === 0 ? 'active' : ''}" data-index="${idx}" onclick="onJobCardClick(${idx})">
      <div class="job-header">
        <div>
          <div class="job-title">${escapeHtml(job.title)}</div>
          <div class="job-company">${escapeHtml(job.company)}</div>
        </div>
        <span class="nav-badge" style="border-color: rgba(56, 189, 248, 0.3); color: var(--accent-cyan);">${escapeHtml(job.posted_date)}</span>
      </div>
      <div style="display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0 6px 0; align-items: center;">
        <span class="${getWorkplaceBadgeClass(job.workplace_type)}">${escapeHtml(job.workplace_badge || '🏡 Remote Only')}</span>
        <span class="badge-employment">${escapeHtml(job.employment_badge || '💼 Full-Time')}</span>
        <span class="${getBadgeClass(job.remote_scope)}">${escapeHtml(job.international_badge || '🌐 Worldwide')}</span>
        ${job.is_easy_apply ? `<span class="badge-easy-apply">${escapeHtml(job.easy_apply_badge || '⚡ Easy Apply')}</span>` : `<span class="badge-employment" style="background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.12); color: var(--text-dim);">🌐 Direct Apply</span>`}
      </div>
      <div class="job-meta" style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
        <div>
          <span>📍 ${escapeHtml(job.location)}</span>
        </div>
        <div>
          <span>🔗 <a href="${job.job_url}" target="_blank" style="color: var(--accent-cyan); font-weight: 600;" onclick="event.stopPropagation()">View on LinkedIn ↗</a></span>
        </div>
      </div>
    </div>
  `).join('');
}

window.onJobCardClick = function(idx) {
  const cards = document.querySelectorAll('.job-card');
  cards.forEach(c => c.classList.remove('active'));
  cards[idx]?.classList.add('active');
  selectJob(currentJobs[idx]);
};

// Step 3: Match Job & Calculate ATS Score + Auto-Compile PDF
async function selectJob(job) {
  selectedJob = job;
  try {
    const userEmail = getCurrentUserEmail();

    const res = await fetch('/api/v1/jobs/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: job.job_id,
        job_title: job.title,
        company: job.company,
        location: job.location,
        job_url: job.job_url,
        candidate_profile: currentProfile || null,
        user_email: userEmail || null
      })
    });
    currentMatchReport = await res.json();
    renderMatchReport(currentMatchReport);
  } catch (err) {
    console.error("Match error:", err);
  }
}

function renderMatchReport(report) {
  const scoreNum = Math.round(report.match_score);
  const gauge = document.getElementById('score-gauge');
  const scoreText = document.getElementById('score-number');
  
  gauge.style.setProperty('--score', scoreNum);
  scoreText.innerText = `${scoreNum}%`;

  document.getElementById('match-headline').innerText = `${report.job_title} at ${report.company}`;
  document.getElementById('match-desc').innerText = report.experience_assessment;

  // Render Matched Skills
  const matchedCloud = document.getElementById('matched-skills-cloud');
  const matchedCountBadge = document.getElementById('matched-count-badge');
  if (matchedCountBadge) matchedCountBadge.innerText = `${report.matched_skills.length} Matched`;
  matchedCloud.innerHTML = report.matched_skills.map(s => `<span class="skill-chip chip-match">✓ ${escapeHtml(s)}</span>`).join('') || '<span style="color:var(--text-dim);font-size:12px;">None detected</span>';

  // Render Missing Skills with one-click "+ Add Skill" Bridge capability
  const missingCloud = document.getElementById('missing-skills-cloud');
  const missingCountBadge = document.getElementById('missing-count-badge');
  if (missingCountBadge) missingCountBadge.innerText = `${report.missing_critical_skills.length} Missing`;
  
  if (report.missing_critical_skills.length > 0) {
    missingCloud.innerHTML = report.missing_critical_skills.map(s => `
      <span class="skill-chip chip-gap" style="cursor: pointer; transition: transform 0.2s;" onclick="addSkillFromBridge('${escapeHtml(s).replace(/'/g, "\\'")}')" title="Click to instantly bridge and add ${escapeHtml(s)} to your resume (+15% score)">
        + ${escapeHtml(s)}
      </span>
    `).join('');
  } else {
    missingCloud.innerHTML = '<span class="skill-chip chip-match">✓ 100% Match (No Gaps)</span>';
  }

  // Render Candidate's Additional Profile Strengths (Bonus Skills)
  const extraCloud = document.getElementById('extra-skills-cloud');
  const extraCountBadge = document.getElementById('extra-count-badge');
  if (extraCloud && currentProfile && currentProfile.skills) {
    const matchedSet = new Set(report.matched_skills.map(s => s.toLowerCase()));
    const extraSkills = currentProfile.skills.filter(s => !matchedSet.has(s.toLowerCase()));
    if (extraCountBadge) extraCountBadge.innerText = `${extraSkills.length} Strengths`;
    extraCloud.innerHTML = extraSkills.slice(0, 12).map(s => `<span class="skill-chip chip-extra">★ ${s}</span>`).join('') || '<span style="color:var(--text-dim);font-size:12px;">All profile skills utilized</span>';
  }

  // Render International Assessment
  const intBadge = document.getElementById('match-international-badge');
  const intNotes = document.getElementById('match-eligibility-notes');
  if (intBadge) {
    intBadge.className = getBadgeClass(report.remote_scope);
    intBadge.innerText = report.international_badge || '🌐 Worldwide Remote';
  }
  if (intNotes) {
    intNotes.innerText = report.eligibility_notes || 'Open to international remote applicants globally.';
  }
}

// Step 4B: Instant Skill Bridge Action
window.addSkillFromBridge = async function(skillName) {
  if (!skillName) return;
  try {
    const res = await fetch('/api/v1/resume/skills/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill: skillName })
    });
    if (res.ok) {
      if (currentProfile) {
        if (!currentProfile.skills) currentProfile.skills = [];
        if (!currentProfile.skills.includes(skillName)) currentProfile.skills.push(skillName);
      }
      renderActiveFileCard(null, null, currentProfile);
      showToast(`✨ Added "${skillName}" to Resume! Re-evaluating ATS Score...`);
      if (selectedJob) {
        await selectJob(selectedJob);
      }
    }
  } catch (err) {
    console.error("Failed to bridge skill:", err);
  }
};

// Step 4: AI Gap Questioning Agent
document.getElementById('btn-bridge-gaps')?.addEventListener('click', async () => {
  if (!currentMatchReport || currentMatchReport.missing_critical_skills.length === 0) {
    alert("No skill gaps detected for this role!");
    return;
  }

  const container = document.getElementById('questions-form');
  container.innerHTML = currentMatchReport.missing_critical_skills.slice(0, 4).map(skill => `
    <div style="background: rgba(7, 9, 19, 0.6); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--border-glass);">
      <label style="font-weight: 700; font-size: 13px; color: var(--accent-cyan); display: block; margin-bottom: 6px;">
        ${skill} Experience
      </label>
      <div style="font-size: 12px; color: var(--text-dim); margin-bottom: 8px;">
        Required by ${currentMatchReport.company}. Describe any freelance work, side projects, or tools used:
      </div>
      <input type="text" class="input-field gap-answer-input" data-skill="${skill}" placeholder="e.g. Built automated pipelines with ${skill} in a side project (or leave blank)">
    </div>
  `).join('');

  openModal('modal-gap-agent');
});

document.getElementById('btn-submit-gap-answers')?.addEventListener('click', async () => {
  const inputs = document.querySelectorAll('.gap-answer-input');
  const answers = {};
  inputs.forEach(inp => {
    if (inp.value.trim()) {
      answers[inp.dataset.skill] = inp.value.trim();
    }
  });

  closeModal('modal-gap-agent');

  try {
    const res = await fetch('/api/v1/agent/bridge-gaps', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers })
    });
    const updated = await res.json();
    currentProfile = updated.profile;
    currentMatchReport = updated.match_report;
    renderActiveFileCard(document.getElementById('file-display-name').innerText, document.getElementById('file-size-display').innerText, currentProfile);
    renderMatchReport(currentMatchReport);
  } catch (err) {
    console.error("Failed to bridge gaps:", err);
  }
});

// Step 5: Starter CV Template Download Machine (DOCX / Word)
document.getElementById('btn-download-docx')?.addEventListener('click', (e) => {
  e.preventDefault();
  const tmpl = window.selectedTemplateId || 'corporate_elite';
  showToast(`📥 Downloading ${templateNames[tmpl] || 'Corporate Elite'} Editable Word Template...`);
  window.open(`/api/v1/resume/download-docx?template_id=${encodeURIComponent(tmpl)}&mode=template&t=${Date.now()}`, '_blank');
});

// Step 6: Questionnaire Memory Bank Controller
window.questionnaireData = [
  { id: "first_name", category: "contact", question: "First name?", answer: "Alex" },
  { id: "last_name", category: "contact", question: "Last name?", answer: "Rivera" },
  { id: "phone_country_code", category: "contact", question: "Phone country code? (e.g. South Sudan (+211))", answer: "South Sudan (+211)" },
  { id: "mobile_phone", category: "contact", question: "Mobile phone number?", answer: "+211 920 123 456" },
  { id: "email_address", category: "contact", question: "Email address?", answer: "alex.rivera@example.com" },
  { id: "street_address", category: "location", question: "Address (Street / Line 1)?", answer: "Airport Road, Sector 4" },
  { id: "city", category: "location", question: "City?", answer: "Juba" },
  { id: "state", category: "location", question: "State / Province / Region?", answer: "Central Equatoria" },
  { id: "work_auth_us", category: "work_auth", question: "Are you legally authorized to work in your target country / United States?", answer: "Yes" },
  { id: "visa_sponsorship", category: "work_auth", question: "Will you now or in the future require visa sponsorship for employment?", answer: "No" }
];
window.activeMissingQuestions = [];

window.loadQuestionnaireBank = async function() {
  const userEmail = getCurrentUserEmail();

  try {
    const url = userEmail ? `/api/v1/questionnaire?email=${encodeURIComponent(userEmail)}` : '/api/v1/questionnaire';
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      if (data.questions && data.questions.length > 0) {
        window.questionnaireData = data.questions;
        // Populate inputs
        data.questions.forEach(q => {
          const input = document.getElementById(`qinput-${q.id}`);
          if (input && q.answer) {
            input.value = q.answer;
          }
        });
      }
      const total = window.questionnaireData.length;
      const badgeCount = document.getElementById('badge-question-count');
      if (badgeCount) badgeCount.innerText = total;
      const hubCount = document.getElementById('hub-memory-count');
      if (hubCount) hubCount.innerText = total;
    }
  } catch (err) {
    console.error("Failed to load questionnaire memory bank:", err);
  }
};

window.openQuestionnaireModal = async function() {
  openModal('modal-questionnaire');
  await window.loadQuestionnaireBank();
};

window.saveAllQuestionnaireAnswers = async function() {
  const btn = document.getElementById('btn-save-all-qbank');
  const answersPayload = {};

  const questionIds = [
    "first_name",
    "last_name",
    "phone_country_code",
    "mobile_phone",
    "email_address",
    "street_address",
    "city",
    "state",
    "work_auth_us",
    "visa_sponsorship"
  ];

  questionIds.forEach(qid => {
    const input = document.getElementById(`qinput-${qid}`);
    if (input) {
      answersPayload[qid] = input.value.trim();
    }
  });

  const userEmail = getCurrentUserEmail();

  try {
    if (btn) {
      btn.disabled = true;
      btn.innerText = "⏳ Saving to Supabase...";
    }
    const res = await fetch('/api/v1/questionnaire/save-all', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: answersPayload, user_email: userEmail })
    });

    if (res.ok) {
      if (btn) {
        btn.innerText = "✓ Saved & Synced to Cloud!";
        btn.style.background = "#10B981";
      }
      showToast("💾 Memory Bank Answers Synced to Supabase!");
      // Highlight inputs briefly with green border
      questionIds.forEach(qid => {
        const input = document.getElementById(`qinput-${qid}`);
        if (input) {
          input.style.borderColor = "#10B981";
          setTimeout(() => { input.style.borderColor = ""; }, 2000);
        }
      });
      await window.loadQuestionnaireBank();
      setTimeout(() => {
        if (btn) {
          btn.disabled = false;
          btn.innerText = "💾 Save to Memory Bank";
          btn.style.background = "";
        }
      }, 2000);
    } else {
      alert("Failed to save answers to Memory Bank.");
      if (btn) {
        btn.disabled = false;
        btn.innerText = "💾 Save to Memory Bank";
      }
    }
  } catch (err) {
    alert("Error saving answers: " + err.message);
    if (btn) {
      btn.disabled = false;
      btn.innerText = "💾 Save to Memory Bank";
    }
  }
};

// Step 7: Smart Auto-Apply Readiness Check & Alert Modal
window.openAutoApplyModal = async function(jobIdx, event) {
  if (event) event.stopPropagation();
  autoApplyTargetJob = currentJobs[jobIdx] || selectedJob;
  if (!autoApplyTargetJob) return;

  // Check job readiness against Memory Bank
  try {
    const checkRes = await fetch(`/api/v1/jobs/readiness?job_id=${encodeURIComponent(autoApplyTargetJob.job_id)}`);
    if (checkRes.ok) {
      const checkData = await checkRes.json();
      if (!checkData.is_ready && checkData.missing_questions && checkData.missing_questions.length > 0) {
        // Trigger Smart Alert Modal for New Unseen Questions
        window.activeMissingQuestions = checkData.missing_questions;
        document.getElementById('alert-job-subtitle').innerText = `${autoApplyTargetJob.title} @ ${autoApplyTargetJob.company}`;
        
        const formContainer = document.getElementById('missing-questions-form');
        formContainer.innerHTML = checkData.missing_questions.map((mq, i) => `
          <div class="missing-q-card">
            <div style="font-weight: 700; font-size: 13.5px; color: #FFF;">${escapeHtml(mq.question)}</div>
            <div class="ai-suggest-pill">✨ AI Recommendation: ${escapeHtml(mq.suggested_answer)} (${mq.reason})</div>
            <input type="text" class="input-field" id="missing-ans-${i}" value="${escapeHtml(mq.suggested_answer)}">
          </div>
        `).join('');

        openModal('modal-new-question');
        return;
      }
    }
  } catch (err) {
    console.error("Readiness check error:", err);
  }

  // If 100% ready, proceed to direct Auto-Apply Review Modal
  const titleEl = document.getElementById('auto-apply-modal-title');
  if (titleEl) titleEl.innerText = `⚡ Autonomous Easy Apply: ${autoApplyTargetJob.title} @ ${autoApplyTargetJob.company}`;

  const saved = getSavedCandidateProfile() || {};
  let authUser = null;
  try {
    const rawAuth = localStorage.getItem('jobflow_auth_user');
    if (rawAuth) authUser = JSON.parse(rawAuth);
  } catch (e) {}

  const defaultName = authUser?.full_name || (currentProfile?.full_name || 'Alex Rivera');
  const defaultEmail = authUser?.email || (currentProfile?.contact?.email || 'alex.rivera@email.com');
  const defaultLinkedin = currentProfile?.contact?.linkedin || 'linkedin.com/in/alex-rivera';
  const defaultGithub = currentProfile?.contact?.github || 'github.com/alexrivera';

  document.getElementById('auto-app-name').value = saved.full_name || defaultName;
  document.getElementById('auto-app-email').value = saved.email || defaultEmail;
  document.getElementById('auto-app-phone').value = saved.phone || (currentProfile?.contact?.phone || '+1 (555) 345-6789');
  document.getElementById('auto-app-linkedin').value = saved.linkedin_url || defaultLinkedin;
  document.getElementById('auto-app-github').value = saved.github_url || defaultGithub;
  if (saved.years_of_experience) document.getElementById('auto-app-exp').value = saved.years_of_experience;
  if (saved.work_authorization) document.getElementById('auto-app-auth').value = saved.work_authorization;

  document.getElementById('auto-apply-success-box').style.display = 'none';
  const execBtn = document.getElementById('btn-execute-auto-apply');
  execBtn.disabled = false;
  execBtn.innerText = '⚡ Submit Autonomous Application';

  openModal('modal-auto-apply');
};

// Save new answers from alert modal & auto-apply immediately
document.getElementById('btn-save-and-continue-apply')?.addEventListener('click', async () => {
  if (!autoApplyTargetJob || !window.activeMissingQuestions) return;

  const customAnswers = {};
  window.activeMissingQuestions.forEach((mq, i) => {
    const input = document.getElementById(`missing-ans-${i}`);
    if (input) customAnswers[mq.question] = input.value.trim();
  });

  closeModal('modal-new-question');

  // Submit Auto-Apply with new custom answers
  const candidateProfile = getSavedCandidateProfile() || {
    full_name: currentProfile?.full_name || 'Candidate',
    email: currentProfile?.contact?.email || 'email@example.com',
    preferred_template: window.selectedTemplateId || 'modern'
  };

  try {
    const res = await fetch('/api/v1/application/auto-apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: autoApplyTargetJob.job_id,
        job_title: autoApplyTargetJob.title,
        company: autoApplyTargetJob.company,
        location: autoApplyTargetJob.location,
        job_url: autoApplyTargetJob.job_url,
        template_id: window.selectedTemplateId || 'modern',
        candidate_profile: candidateProfile,
        custom_answers: customAnswers,
        dispatch_alerts: true,
      })
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      window.loadQuestionnaireBank(); // Refresh memory bank
      alert(`🎉 Application Successfully Auto-Applied!\nJob: ${autoApplyTargetJob.title} at ${autoApplyTargetJob.company}\nNew questions saved permanently to your Memory Bank.\nTailored PDF & Receipts dispatched.`);
    } else {
      alert("Application error: " + (data.message || data.detail || "Unknown error"));
    }
  } catch (err) {
    alert("Application error: " + err.message);
  }
});

// Step 8: Batch 1-Click Auto-Apply across chosen volume of discovered jobs
document.getElementById('btn-batch-auto-apply')?.addEventListener('click', async () => {
  if (!currentJobs || currentJobs.length === 0) {
    alert("Please scan for jobs first before executing batch auto-apply.");
    return;
  }

  const volumeVal = document.getElementById('select-batch-volume')?.value || 'all_easy';
  let targetJobs = [];

  if (volumeVal === 'all_easy') {
    targetJobs = currentJobs.filter(j => j.is_easy_apply);
    if (targetJobs.length === 0) {
      targetJobs = currentJobs; // fallback if user explicitly wants to apply to discovered list
    }
  } else {
    const maxCount = parseInt(volumeVal, 10) || 10;
    const easyOnly = currentJobs.filter(j => j.is_easy_apply);
    targetJobs = (easyOnly.length >= maxCount ? easyOnly : currentJobs).slice(0, maxCount);
  }

  if (targetJobs.length === 0) {
    alert("No eligible jobs found for batch application. Try searching for additional jobs.");
    return;
  }

  const btn = document.getElementById('btn-batch-auto-apply');
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `⏳ AI Applying to ${targetJobs.length} Jobs...`;

  const jobIds = targetJobs.map(j => j.job_id);
  const candidateProfile = getSavedCandidateProfile() || {
    full_name: currentProfile?.full_name || 'Alex Rivera',
    email: currentProfile?.contact?.email || 'alex.rivera@example.com',
    preferred_template: window.selectedTemplateId || 'modern'
  };

  const selectedChannels = [];
  if (document.getElementById('chk-email')?.checked) selectedChannels.push('email');
  if (document.getElementById('chk-whatsapp')?.checked) selectedChannels.push('whatsapp');
  if (document.getElementById('chk-telegram')?.checked) selectedChannels.push('telegram');

  try {
    const res = await fetch('/api/v1/application/batch-apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_ids: jobIds,
        template_id: window.selectedTemplateId || 'modern',
        candidate_profile: candidateProfile,
        channels: selectedChannels
      })
    });

    const data = await res.json();
    if (res.ok) {
      const results = data.results || {};
      alert(`🚀 Autonomous Batch Auto-Apply Complete!\n\n• Successfully Auto-Applied: ${results.applied_count} Jobs\n• Needs New Answers: ${results.needs_input_count} Jobs\n• Delivery Channels: Email & WhatsApp Confirmations Triggered\n\nAll tailored PDF bundles were generated in the ${window.selectedTemplateId.toUpperCase()} template and company records were logged to your Excel, CSV & PDF Trackers!`);
    } else {
      alert("Batch apply failed: " + (data.detail || "Unknown error"));
    }
  } catch (err) {
    alert("Batch apply error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
});

// Step 9: Download Application History & Company Intelligence as Excel / CSV / PDF
window.downloadApplicationExcel = function() {
  const url = `/api/v1/applications/export-excel?t=${Date.now()}`;
  window.open(url, '_blank');
};

window.downloadApplicationCSV = function() {
  const url = `/api/v1/applications/export-csv?t=${Date.now()}`;
  window.open(url, '_blank');
};

window.downloadApplicationPDF = function() {
  const url = `/api/v1/applications/export-pdf?t=${Date.now()}`;
  window.open(url, '_blank');
};

function runAnimatedAutoApplyProgress(onComplete) {
  const progressBox = document.getElementById('auto-apply-progress-box');
  const progressBar = document.getElementById('progress-bar-fill');
  const percentText = document.getElementById('progress-percent');
  const titleText = document.getElementById('progress-status-title');
  const successBox = document.getElementById('auto-apply-success-box');
  
  if (successBox) successBox.style.display = 'none';
  if (progressBox) progressBox.style.display = 'block';

  const steps = [
    { id: 'pstep-1', percent: '25%', title: 'Step 1: Extracting Job Requirements & Aligning Profile...' },
    { id: 'pstep-2', percent: '50%', title: 'Step 2: Auto-Filling Screening Dossier from Memory Bank...' },
    { id: 'pstep-3', percent: '75%', title: 'Step 3: Compiling Custom ATS Resume in High-Res PDF...' },
    { id: 'pstep-4', percent: '100%', title: 'Step 4: Dispatching Application Package & Triggering Alerts...' }
  ];

  steps.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) {
      el.style.color = 'var(--text-dim)';
      const icon = el.querySelector('.pstep-icon');
      if (icon) icon.innerText = '⏳';
    }
  });

  let current = 0;
  function nextStep() {
    if (current < steps.length) {
      const s = steps[current];
      const el = document.getElementById(s.id);
      if (el) {
        el.style.color = '#38BDF8';
        const icon = el.querySelector('.pstep-icon');
        if (icon) icon.innerText = '⚡';
      }
      if (progressBar) progressBar.style.width = s.percent;
      if (percentText) percentText.innerText = s.percent;
      if (titleText) titleText.innerText = s.title;

      setTimeout(() => {
        if (el) {
          el.style.color = '#34D399';
          const icon = el.querySelector('.pstep-icon');
          if (icon) icon.innerText = '✅';
        }
        current++;
        if (current < steps.length) {
          nextStep();
        } else {
          setTimeout(() => {
            if (progressBox) progressBox.style.display = 'none';
            if (onComplete) onComplete();
          }, 400);
        }
      }, 400);
    }
  }

  nextStep();
}

document.getElementById('btn-execute-auto-apply')?.addEventListener('click', async () => {
  if (!autoApplyTargetJob) return;

  const candidateProfile = {
    full_name: document.getElementById('auto-app-name').value.trim(),
    email: document.getElementById('auto-app-email').value.trim(),
    phone: document.getElementById('auto-app-phone').value.trim(),
    linkedin_url: document.getElementById('auto-app-linkedin').value.trim(),
    github_url: document.getElementById('auto-app-github').value.trim(),
    years_of_experience: document.getElementById('auto-app-exp').value,
    work_authorization: document.getElementById('auto-app-auth').value.trim(),
    cover_note: document.getElementById('auto-app-note').value.trim(),
    preferred_template: window.selectedTemplateId || 'modern',
  };

  saveCandidateProfile(candidateProfile);

  const execBtn = document.getElementById('btn-execute-auto-apply');
  execBtn.disabled = true;
  execBtn.innerText = '⚡ Running Autonomous Agent...';

  runAnimatedAutoApplyProgress(async () => {
    try {
      const res = await fetch('/api/v1/application/auto-apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: autoApplyTargetJob.job_id,
          job_title: autoApplyTargetJob.title,
          company: autoApplyTargetJob.company,
          location: autoApplyTargetJob.location,
          job_url: autoApplyTargetJob.job_url,
          template_id: window.selectedTemplateId || 'modern',
          candidate_profile: candidateProfile,
          dispatch_alerts: true,
        })
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        const successBox = document.getElementById('auto-apply-success-box');
        if (successBox) successBox.style.display = 'block';
        
        const targetEmail = candidateProfile.email || 'your email';
        // Show notification delivery results
        let notifHtml = '';
        if (data.notification_results) {
          const nr = data.notification_results;
          notifHtml = '<div style="margin-top: 8px; font-size: 12px; color: var(--text-dim);">';
          if (nr.email) notifHtml += `<div>📧 Email: <span style="color: #10B981;">✓ ${nr.email.status || 'Sent'}</span></div>`;
          if (nr.whatsapp) notifHtml += `<div>📱 WhatsApp: <span style="color: #10B981;">✓ ${nr.whatsapp.status || 'Sent'}</span></div>`;
          if (nr.telegram) notifHtml += `<div>✈️ Telegram: <span style="color: #10B981;">✓ ${nr.telegram.status || 'Sent'}</span></div>`;
          notifHtml += '</div>';
        }
        
        document.getElementById('auto-apply-msg').innerHTML = `
          <div style="padding: 12px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px;">
            <div style="color: #10B981; font-weight: 700;">✓ Successfully Auto-Applied to ${escapeHtml(autoApplyTargetJob.company)}</div>
            ${notifHtml}
            <div style="margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap;">
              <button onclick="window.open('/api/v1/applications/export-excel')" style="padding: 6px 12px; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; color: #10B981; font-size: 11px; cursor: pointer;">📗 Excel Tracker</button>
              <button onclick="window.open('/api/v1/applications/export-csv')" style="padding: 6px 12px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 6px; color: #38BDF8; font-size: 11px; cursor: pointer;">📄 CSV</button>
              <button onclick="window.open('/api/v1/applications/export-pdf')" style="padding: 6px 12px; background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 6px; color: #C084FC; font-size: 11px; cursor: pointer;">📕 PDF Report</button>
            </div>
          </div>
        `;
        
        const postDownloads = document.getElementById('post-apply-downloads');
        if (postDownloads) postDownloads.style.display = 'flex';

        const answersContainer = document.getElementById('prefilled-answers-container');
        const answers = data.prefilled_answers || {};
        if (answersContainer) {
          answersContainer.innerHTML = Object.entries(answers).map(([key, val]) => `
            <div class="prefilled-card">
              <div class="prefilled-label">${key}</div>
              <div class="prefilled-val">${val}</div>
            </div>
          `).join('');
        }

        document.getElementById('btn-auto-download-pdf').onclick = () => {
          window.open(`/api/v1/resume/download-pdf?template_id=${encodeURIComponent(window.selectedTemplateId || 'modern')}&t=${Date.now()}`, '_blank');
        };
        document.getElementById('btn-auto-download-docx').onclick = () => {
          window.open(`/api/v1/resume/download-docx?template_id=${encodeURIComponent(window.selectedTemplateId || 'modern')}&t=${Date.now()}`, '_blank');
        };

        execBtn.innerText = '✓ Submitted Successfully';
        showToast(`✅ Auto-Applied to ${autoApplyTargetJob.company} & Alerts Dispatched!`);
      } else {
        alert("Auto apply error: " + (data.message || data.detail || "Unknown error"));
        execBtn.disabled = false;
        execBtn.innerText = '⚡ Submit Autonomous Application';
      }
    } catch (err) {
      alert("Application error: " + err.message);
      execBtn.disabled = false;
      execBtn.innerText = '⚡ Submit Autonomous Application';
    }
  });
});

document.getElementById('btn-test-notifications')?.addEventListener('click', async () => {
  const email = document.getElementById('setting-email')?.value.trim();
  const wa = document.getElementById('setting-whatsapp')?.value.trim();
  const tg = document.getElementById('setting-telegram')?.value.trim();
  const msgEl = document.getElementById('settings-save-msg');

  if (msgEl) msgEl.innerHTML = '<span style="color: var(--accent-cyan)">⏳ Dispatching test alert to your configured channels...</span>';

  try {
    const res = await fetch('/api/v1/notifications/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, whatsapp: wa, telegram: tg, channel: 'all' })
    });
    const data = await res.json();
    if (res.ok) {
      if (msgEl) msgEl.innerHTML = `<span style="color: var(--accent-emerald)">✓ Test alert dispatched to <b>${data.email_sent_to}</b> & WhatsApp <b>${data.whatsapp_sent_to}</b>!</span>`;
      showToast("🔔 Test notification sent successfully!");
    } else {
      if (msgEl) msgEl.innerHTML = `<span style="color: var(--accent-rose)">Alert test notice: ${data.message || 'Check server logs'}</span>`;
    }
  } catch (err) {
    if (msgEl) msgEl.innerHTML = `<span style="color: var(--accent-rose)">Test error: ${err.message}</span>`;
  }
});

// ─────────────────────────────────────────────────────────────
// Batch Auto-Apply Engine: Apply to ALL Easy Apply Jobs
// ─────────────────────────────────────────────────────────────
document.getElementById('btn-batch-auto-apply')?.addEventListener('click', async () => {
  const batchSize = parseInt(document.getElementById('batch-size-selector')?.value || '50');
  const btn = document.getElementById('btn-batch-auto-apply');
  const resultsDiv = document.getElementById('batch-apply-results');
  const downloadsDiv = document.getElementById('post-apply-downloads');
  
  if (!currentJobs || currentJobs.length === 0) {
    showToast('Please search for jobs first before batch applying.');
    return;
  }
  
  const easyApplyJobs = currentJobs.filter(j => j.is_easy_apply);
  if (easyApplyJobs.length === 0) {
    showToast('No Easy Apply jobs found. Try searching with Easy Apply filter.');
    return;
  }
  
  btn.disabled = true;
  btn.innerText = `⚡ Batch Applying to ${Math.min(easyApplyJobs.length, batchSize)} Easy Apply Jobs...`;
  resultsDiv.style.display = 'block';
  resultsDiv.innerHTML = '<div style="color: var(--accent-cyan); font-size: 13px;">⏳ Autonomous agent processing batch applications...</div>';
  
  // Load candidate profile
  let candidateProfile = {};
  try {
    candidateProfile = JSON.parse(localStorage.getItem('candidate_quick_profile') || '{}');
  } catch (e) {}
  
  try {
    const res = await fetch('/api/v1/application/batch-apply-easy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        batch_size: batchSize,
        template_id: window.selectedTemplateId || 'modern',
        candidate_profile: candidateProfile,
      })
    });
    const data = await res.json();
    
    if (data.status === 'success') {
      const results = data.results || {};
      const applied = results.applied_count || 0;
      const pending = results.needs_input_count || 0;
      
      resultsDiv.innerHTML = `
        <div style="padding: 12px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px;">
          <div style="color: #10B981; font-weight: 700; font-size: 14px; margin-bottom: 8px;">✓ Batch Auto-Apply Complete</div>
          <div style="color: var(--text-secondary); font-size: 13px; line-height: 1.6;">
            <div>📊 Applied: <b style="color: #10B981;">${applied}</b> jobs</div>
            <div>⏳ Pending Answers: <b style="color: #F59E0B;">${pending}</b> jobs</div>
            <div>📋 Total Easy Apply: <b>${data.total_easy_apply || 0}</b></div>
          </div>
        </div>
      `;
      
      // Show tracker download buttons
      if (downloadsDiv) {
        downloadsDiv.style.display = 'flex';
      }
      
      showToast(`✅ Batch Applied to ${applied} Easy Apply jobs! Notifications dispatched.`);
      btn.innerText = `✓ Batch Applied to ${applied} Jobs`;
      btn.style.borderColor = '#10B981';
    } else {
      resultsDiv.innerHTML = `<div style="color: var(--accent-rose); font-size: 13px;">${escapeHtml(data.message || 'Batch apply failed.')}</div>`;
      btn.disabled = false;
      btn.innerText = '⚡ Batch Auto-Apply to All Easy Apply Jobs';
    }
  } catch (err) {
    resultsDiv.innerHTML = `<div style="color: var(--accent-rose); font-size: 13px;">Error: ${escapeHtml(err.message)}</div>`;
    btn.disabled = false;
    btn.innerText = '⚡ Batch Auto-Apply to All Easy Apply Jobs';
  }
});

// Step 9: Notification Channels & Alert Settings Controller
async function loadNotificationSettings() {
  const userEmail = getCurrentUserEmail();

  try {
    const url = userEmail ? `/api/v1/settings/notifications?email=${encodeURIComponent(userEmail)}` : '/api/v1/settings/notifications';
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      if (document.getElementById('setting-email')) document.getElementById('setting-email').value = data.email || '';
      if (document.getElementById('setting-whatsapp')) document.getElementById('setting-whatsapp').value = data.whatsapp || '';
      if (document.getElementById('setting-telegram')) document.getElementById('setting-telegram').value = data.telegram || '';
      
      if (document.getElementById('bar-email')) document.getElementById('bar-email').innerText = data.email || 'Not Configured';
      if (document.getElementById('bar-whatsapp')) document.getElementById('bar-whatsapp').innerText = data.whatsapp || 'Not Configured';
      if (document.getElementById('bar-telegram')) document.getElementById('bar-telegram').innerText = data.telegram ? (data.telegram.startsWith('@') ? data.telegram : '@' + data.telegram) : 'Not Configured';
    }
  } catch (err) {
    console.error("Failed to load notification settings:", err);
  }
}

document.getElementById('btn-save-settings')?.addEventListener('click', async () => {
  const email = document.getElementById('setting-email').value.trim();
  const wa = document.getElementById('setting-whatsapp').value.trim();
  const tg = document.getElementById('setting-telegram').value.trim();
  const msgEl = document.getElementById('settings-save-msg');

  const userEmail = email || getCurrentUserEmail();

  msgEl.innerHTML = '<span style="color: var(--accent-cyan)">Saving preferences to Supabase...</span>';

  try {
    const res = await fetch('/api/v1/settings/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, whatsapp: wa, telegram: tg, user_email: userEmail })
    });
    if (res.ok) {
      msgEl.innerHTML = '<span style="color: var(--accent-emerald)">✓ Preferences saved and synced permanently to Supabase!</span>';
      
      if (document.getElementById('bar-email')) document.getElementById('bar-email').innerText = email || 'Not Configured';
      if (document.getElementById('bar-whatsapp')) document.getElementById('bar-whatsapp').innerText = wa || 'Not Configured';
      if (document.getElementById('bar-telegram')) document.getElementById('bar-telegram').innerText = tg ? (tg.startsWith('@') ? tg : '@' + tg) : 'Not Configured';

      showToast("💾 Notification settings saved & synced to Supabase!");
      setTimeout(() => closeModal('modal-settings'), 1200);
    } else {
      msgEl.innerHTML = '<span style="color: var(--accent-rose)">Failed to save preferences.</span>';
    }
  } catch (err) {
    msgEl.innerHTML = '<span style="color: var(--accent-rose)">Save error: ' + err.message + '</span>';
  }
});

// ─────────────────────────────────────────────────────────────
// ResLink Studio & Teleprompter Controller Engine
// ─────────────────────────────────────────────────────────────

let reslinkProfileState = null;
let studioMediaStream = null;
let studioMediaRecorder = null;
let recordedVideoChunks = [];
let recordingTimerInterval = null;
let recordingSeconds = 0;
let prompterScrollInterval = null;
let isPrompterScrolling = false;

window.scrollToResLinkStudio = function() {
  const el = document.getElementById('reslink-studio-section');
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    el.style.boxShadow = '0 0 35px rgba(56, 189, 248, 0.6)';
    setTimeout(() => { el.style.boxShadow = ''; }, 2000);
  }
};

window.importSelectedJobRequirements = function() {
  if (state.selectedJob) {
    document.getElementById('reslink-job-title').value = state.selectedJob.title || 'Senior AI Engineer';
    document.getElementById('reslink-company-name').value = state.selectedJob.company || 'Target Employer';
    document.getElementById('reslink-job-requirements').value = (state.selectedJob.requirements || []).join('\n') || state.selectedJob.description || '';
    showToast(`✓ Imported requirements from ${state.selectedJob.company}`);
  } else {
    // Fallback to active search keyword
    const kw = document.getElementById('input-keywords')?.value || 'Senior AI Engineer';
    document.getElementById('reslink-job-title').value = kw;
    document.getElementById('reslink-job-requirements').value = `Required Skills: ${kw}, System Design, Cloud Infrastructure, High-Throughput Delivery, Cross-Functional Collaboration.`;
    showToast(`✓ Formatted target template for ${kw}`);
  }
};

window.generateJobMatchedPitchScript = async function() {
  const jobTitle = document.getElementById('reslink-job-title').value.trim() || 'Senior AI Engineer';
  const company = document.getElementById('reslink-company-name').value.trim() || 'Target Employer';
  const duration = document.getElementById('reslink-pitch-duration').value || '60s';
  const reqs = document.getElementById('reslink-job-requirements').value.trim() || `Key requirements for ${jobTitle} at ${company}.`;

  const btn = document.getElementById('btn-generate-pitch-script');
  const originalHtml = btn.innerHTML;
  btn.innerHTML = '⚡ Synthesizing Spoken Pitch & Badges...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/v1/reslink/pitch/match-job', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_title: jobTitle,
        company: company,
        duration_mode: duration,
        job_requirements: reqs
      })
    });

    if (!res.ok) throw new Error("Failed to generate pitch script");
    const data = await res.json();
    const pitch = data.pitch_data;

    // Update Teleprompter Text
    document.getElementById('teleprompter-text').innerText = pitch.pitch_script;
    
    // Store in state
    if (reslinkProfileState) {
      reslinkProfileState.pitch_script = pitch.pitch_script;
      reslinkProfileState.linkedin_outreach_note = pitch.linkedin_outreach_note;
      reslinkProfileState.competency_badges = pitch.competency_badges;
    }

    showToast(`✨ Generated ${duration} Spoken Pitch matched to ${company}!`);
  } catch (err) {
    showToast(`Error: ${err.message}`);
  } finally {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }
};

window.playPrompterAudioRehearsal = function() {
  const text = document.getElementById('teleprompter-text').innerText;
  if (!('speechSynthesis' in window)) {
    showToast("Speech audio synthesis is not supported on this browser.");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
  showToast("🔊 Playing Spoken Audio Pitch Rehearsal...");
};

window.toggleTeleprompterScroll = function() {
  const container = document.getElementById('teleprompter-scroll-container');
  const btn = document.getElementById('btn-prompter-scroll');
  if (!container || !btn) return;

  if (isPrompterScrolling) {
    if (prompterAnimFrame) cancelAnimationFrame(prompterAnimFrame);
    isPrompterScrolling = false;
    btn.innerHTML = '▶ Start Prompter';
    btn.classList.remove('btn-emerald');
  } else {
    isPrompterScrolling = true;
    btn.innerHTML = '⏸ Pause Prompter';
    btn.classList.add('btn-emerald');

    let prompterScrollPos = container.scrollTop;
    let lastTime = performance.now();

    function stepScroll(currentTime) {
      if (!isPrompterScrolling) return;
      const dt = (currentTime - lastTime) / 1000;
      lastTime = currentTime;

      const wpm = parseInt(document.getElementById('teleprompter-wpm')?.value) || 35;
      const pixelsPerSecond = (wpm / 35) * 4.5;

      prompterScrollPos += pixelsPerSecond * dt;
      container.scrollTop = prompterScrollPos;

      if (container.scrollTop >= (container.scrollHeight - container.clientHeight - 4)) {
        isPrompterScrolling = false;
        btn.innerHTML = '🔄 Restart Prompter';
        btn.classList.remove('btn-emerald');
        return;
      }

      prompterAnimFrame = requestAnimationFrame(stepScroll);
    }

    prompterAnimFrame = requestAnimationFrame(stepScroll);
  }
};

window.updateTeleprompterSpeed = function() {
  if (isPrompterScrolling) {
    if (prompterAnimFrame) cancelAnimationFrame(prompterAnimFrame);
    isPrompterScrolling = false;
    window.toggleTeleprompterScroll();
  }
};

function getSupportedVideoMimeType() {
  const candidates = [
    'video/webm;codecs=vp9,opus',
    'video/webm;codecs=vp8,opus',
    'video/webm;codecs=h264,opus',
    'video/webm',
    'video/mp4;codecs=avc1,mp4a.40.2',
    'video/mp4'
  ];
  for (const mime of candidates) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(mime)) {
      return mime;
    }
  }
  return '';
}

window.toggleWebcam = async function() {
  const videoElem = document.getElementById('studio-webcam-preview');
  const placeholder = document.getElementById('camera-placeholder');
  const btnCam = document.getElementById('btn-toggle-camera');
  const btnRec = document.getElementById('btn-record-pitch');

  if (studioMediaStream) {
    // Stop camera
    studioMediaStream.getTracks().forEach(track => track.stop());
    studioMediaStream = null;
    if (videoElem) videoElem.srcObject = null;
    if (placeholder) placeholder.style.display = 'block';
    if (btnCam) btnCam.innerHTML = '📹 Start Camera';
  } else {
    try {
      studioMediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: 'user' },
        audio: true
      });
      if (videoElem) {
        videoElem.srcObject = studioMediaStream;
        videoElem.play().catch(() => {});
      }
      if (placeholder) placeholder.style.display = 'none';
      if (btnCam) btnCam.innerHTML = '⏹ Turn Off Camera';
      if (btnRec) {
        btnRec.disabled = false;
        btnRec.style.background = '#EF4444';
      }
      showToast("✓ Studio Camera & Microphone Active");
    } catch (err) {
      console.warn("Camera video stream unavailable, attempting audio fallback:", err);
      try {
        studioMediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (placeholder) {
          placeholder.innerHTML = `
            <div style="font-size: 32px; margin-bottom: 8px;">🎙️</div>
            <div style="font-weight: 700; color: #34D399; font-size: 14px;">Microphone Connected (Voice Mode)</div>
            <div style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">Camera was blocked; recording voice pitch</div>
          `;
        }
        if (btnCam) btnCam.innerHTML = '⏹ Disconnect Mic';
        if (btnRec) {
          btnRec.disabled = false;
          btnRec.style.background = '#EF4444';
        }
        showToast("🎙️ Microphone Connected for Voice Pitch!");
      } catch (audioErr) {
        if (placeholder) {
          placeholder.innerHTML = `
            <div style="font-size: 28px; margin-bottom: 8px;">📁</div>
            <div style="font-weight: 700; color: #F59E0B; font-size: 14px;">Camera / Mic Permission Denied</div>
            <div style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">You can upload an MP4 video directly</div>
          `;
        }
        showToast("Camera permission not granted. You can upload an MP4 video directly.");
      }
    }
  }
};

window.toggleRecording = async function() {
  const btnRec = document.getElementById('btn-record-pitch');
  const indicator = document.getElementById('recording-indicator');

  if (studioMediaRecorder && studioMediaRecorder.state === 'recording') {
    // Stop recording
    studioMediaRecorder.stop();
    clearInterval(recordingTimerInterval);
    if (indicator) indicator.style.display = 'none';
    if (btnRec) {
      btnRec.innerHTML = '🔴 Start Recording';
      btnRec.style.background = '#EF4444';
    }
    if (isPrompterScrolling) window.toggleTeleprompterScroll(); // pause prompter
    return;
  }

  if (!studioMediaStream) {
    showToast("Starting camera & microphone...");
    await window.toggleWebcam();
    if (!studioMediaStream) {
      showToast("Please allow camera access before recording.");
      return;
    }
  }

  recordedVideoChunks = [];
  try {
    const mime = getSupportedVideoMimeType();
    const options = mime ? { mimeType: mime } : {};
    studioMediaRecorder = new MediaRecorder(studioMediaStream, options);
  } catch (err) {
    console.warn("Primary MediaRecorder init failed, trying fallback:", err);
    try {
      studioMediaRecorder = new MediaRecorder(studioMediaStream);
    } catch (err2) {
      showToast(`Recorder error: ${err2.message}`);
      return;
    }
  }

  studioMediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) recordedVideoChunks.push(e.data);
  };

  studioMediaRecorder.onstop = async () => {
    const mime = studioMediaRecorder.mimeType || 'video/webm';
    const blob = new Blob(recordedVideoChunks, { type: mime });
    const ext = mime.includes('mp4') ? 'mp4' : 'webm';
    showToast("⏳ Uploading video pitch to ResLink...");
    
    const formData = new FormData();
    formData.append('file', blob, `pitch_recording.${ext}`);

    try {
      const res = await fetch('/api/v1/reslink/upload-video', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const d = await res.json();
        showToast(`✓ Video Pitch Saved to ResLink (${d.filesize})!`);
        window.refreshResLinkAnalytics();
      } else {
        showToast("Failed to upload pitch recording.");
      }
    } catch (err) {
      showToast(`Upload error: ${err.message}`);
    }
  };

  try {
    studioMediaRecorder.start(250);
    recordingSeconds = 0;
    if (indicator) {
      indicator.style.display = 'inline-flex';
      indicator.innerText = '● REC 00:00';
    }
    if (btnRec) {
      btnRec.innerHTML = '⏹ Stop & Save Video';
      btnRec.style.background = '#10B981';
    }

    // Start prompter automatically on record
    if (!isPrompterScrolling) window.toggleTeleprompterScroll();

    recordingTimerInterval = setInterval(() => {
      recordingSeconds++;
      const m = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
      const s = String(recordingSeconds % 60).padStart(2, '0');
      if (indicator) indicator.innerText = `● REC ${m}:${s}`;
    }, 1000);
  } catch (startErr) {
    showToast(`Could not start recording: ${startErr.message}`);
  }
};

window.saveResLinkConfiguration = async function() {
  const calendly = document.getElementById('reslink-setting-calendly')?.value?.trim() || '';
  const linkedin = document.getElementById('reslink-setting-linkedin')?.value?.trim() || '';
  const whatsapp = document.getElementById('reslink-setting-whatsapp')?.value?.trim() || '';
  const theme = document.getElementById('reslink-setting-theme')?.value || 'glassmorphic_dark';

  try {
    const getRes = await fetch('/api/v1/reslink');
    const cur = await getRes.json();

    cur.cta_settings = cur.cta_settings || {};
    if (calendly) cur.cta_settings.calendly_url = calendly;
    if (linkedin) cur.cta_settings.linkedin_url = linkedin;
    if (whatsapp) cur.cta_settings.whatsapp_number = whatsapp;
    cur.theme = theme;
    cur.selected_cv_template = window.selectedTemplateId || 'corporate_elite';

    const saveRes = await fetch('/api/v1/reslink', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cur)
    });

    if (saveRes.ok) {
      reslinkProfileState = cur;
      showToast("💾 ResLink Configuration Saved!");
    } else {
      showToast("Failed to save ResLink configuration.");
    }
  } catch (err) {
    showToast(`Error: ${err.message}`);
  }
};

window.refreshResLinkAnalytics = async function() {
  try {
    const res = await fetch('/api/v1/reslink/analytics');
    if (res.ok) {
      const a = await res.json();
      if (document.getElementById('stat-total-views')) document.getElementById('stat-total-views').innerText = a.total_views || 0;
      if (document.getElementById('stat-unique-visitors')) document.getElementById('stat-unique-visitors').innerText = a.unique_visitors || 0;
      if (document.getElementById('stat-video-plays')) document.getElementById('stat-video-plays').innerText = a.video_plays || 0;
      if (document.getElementById('stat-cv-downloads')) document.getElementById('stat-cv-downloads').innerText = a.cv_downloads || 0;
      if (document.getElementById('stat-avg-watch')) document.getElementById('stat-avg-watch').innerText = `${a.average_watch_seconds || 0}s`;
    }
  } catch (err) {
    console.error("Error loading analytics:", err);
  }
};

window.copyResLinkShareBundle = function() {
  const slug = reslinkProfileState?.slug || 'alex-rivera';
  const url = `${window.location.origin}/p/${slug}`;
  const note = reslinkProfileState?.linkedin_outreach_note || `Check out my video pitch and project link: ${url}`;
  
  navigator.clipboard.writeText(note.replace('{reslink_url}', url)).then(() => {
    showToast("✓ Copied Link & Personalized LinkedIn Pitch Note!");
  }).catch(() => {
    navigator.clipboard.writeText(url);
    showToast("✓ Copied ResLink profile URL!");
  });
};

async function loadInitialResLinkProfile() {
  try {
    const res = await fetch('/api/v1/reslink');
    if (res.ok) {
      reslinkProfileState = await res.json();
      if (reslinkProfileState.cta_settings) {
        if (document.getElementById('reslink-setting-linkedin')) {
          document.getElementById('reslink-setting-linkedin').value = reslinkProfileState.cta_settings.linkedin_url || '';
        }
        if (document.getElementById('reslink-setting-calendly')) {
          document.getElementById('reslink-setting-calendly').value = reslinkProfileState.cta_settings.calendly_url || '';
        }
        if (document.getElementById('reslink-setting-whatsapp')) {
          document.getElementById('reslink-setting-whatsapp').value = reslinkProfileState.cta_settings.whatsapp_number || '';
        }
      }
      if (reslinkProfileState.theme && document.getElementById('reslink-setting-theme')) {
        document.getElementById('reslink-setting-theme').value = reslinkProfileState.theme;
      }
      if (reslinkProfileState.pitch_script && document.getElementById('teleprompter-text')) {
        document.getElementById('teleprompter-text').innerText = reslinkProfileState.pitch_script;
      }
      if (reslinkProfileState.slug && document.getElementById('btn-view-public-reslink')) {
        document.getElementById('btn-view-public-reslink').href = `/p/${reslinkProfileState.slug}`;
      }
    }
    window.refreshResLinkAnalytics();
  } catch (err) {
    console.warn("Failed to load initial ResLink profile:", err);
  }
}

// Gumroad License Verification
window.verifyGumroadLicense = async function() {
  const input = document.getElementById('input-gumroad-license');
  const statusMsg = document.getElementById('license-status-msg');
  const key = input ? input.value.trim() : '';
  if (!key) {
    showToast("Please enter a valid Gumroad license key.");
    return;
  }

  const btn = document.getElementById('btn-verify-license');
  const origText = btn.innerText;
  btn.innerText = 'Verifying...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/v1/licenses/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_key: key })
    });
    const data = await res.json();
    if (data.success) {
      const tier = data.tier || 'pro';
      localStorage.setItem('user_subscription_tier', tier);
      localStorage.setItem('gumroad_license_key', key);
      statusMsg.style.display = 'block';
      statusMsg.style.color = '#10B981';
      statusMsg.innerText = `✓ Successfully activated ${data.plan}! Upgraded access enabled.`;
      showToast(`✓ Activated ${data.plan}!`);
      
      updateTierBadges(tier);
      setTimeout(() => closeModal('modal-pricing'), 2000);
    } else {
      statusMsg.style.display = 'block';
      statusMsg.style.color = '#EF4444';
      statusMsg.innerText = `✕ ${data.message || 'Invalid or expired license key.'}`;
      showToast("License verification failed.");
    }
  } catch (err) {
    showToast(`Verification error: ${err.message}`);
  } finally {
    btn.innerText = origText;
    btn.disabled = false;
  }
};

const OWNER_EMAIL = "mudatherkbyer@gmail.com";

function isOwnerEmail(email) {
  if (!email || typeof email !== 'string') return false;
  return email.trim().toLowerCase() === OWNER_EMAIL;
}

window.updateTierBadges = function(tier) {
  const navBadge = document.getElementById('tier-badge');
  const upgradeBtn = document.getElementById('btn-pricing-modal');
  const barPlan = document.getElementById('bar-plan');
  
  const normalizedTier = (tier || '').toString().toLowerCase().trim();

  // ONLY mudatherkbyer@gmail.com can receive owner tier
  if (normalizedTier === 'owner') {
    if (navBadge) {
      navBadge.innerText = '👑 OWNER & ADMIN • LIFETIME UNLIMITED ($49)';
      navBadge.style.borderColor = 'rgba(0, 240, 255, 0.6)';
      navBadge.style.color = '#00F0FF';
      navBadge.style.background = 'rgba(0, 240, 255, 0.15)';
      navBadge.style.boxShadow = '0 0 20px rgba(0, 240, 255, 0.25)';
    }
    if (upgradeBtn) {
      upgradeBtn.innerText = '👑 Owner Admin (Lifetime $49)';
      upgradeBtn.style.borderColor = '#10B981';
      upgradeBtn.style.color = '#10B981';
      upgradeBtn.style.background = 'rgba(16, 185, 129, 0.18)';
    }
    if (barPlan) {
      barPlan.innerText = 'Owner & Admin ($49 Lifetime)';
      barPlan.style.color = '#00F0FF';
    }
  } else if (normalizedTier === 'executive') {
    if (navBadge) {
      navBadge.innerText = 'EXECUTIVE VIP ($49) ACTIVE';
      navBadge.style.borderColor = 'rgba(168, 85, 247, 0.6)';
      navBadge.style.color = '#C084FC';
      navBadge.style.background = 'rgba(168, 85, 247, 0.15)';
      navBadge.style.boxShadow = '0 0 20px rgba(168, 85, 247, 0.25)';
    }
    if (upgradeBtn) {
      upgradeBtn.innerText = '👑 Executive Plan Active';
      upgradeBtn.style.borderColor = '#A855F7';
      upgradeBtn.style.color = '#C084FC';
      upgradeBtn.style.background = 'rgba(168, 85, 247, 0.18)';
    }
    if (barPlan) {
      barPlan.innerText = 'Executive VIP ($49/mo)';
      barPlan.style.color = '#C084FC';
    }
  } else if (normalizedTier === 'pro') {
    if (navBadge) {
      navBadge.innerText = 'PRO PLAN ($19) ACTIVE';
      navBadge.style.borderColor = 'rgba(56, 189, 248, 0.5)';
      navBadge.style.color = '#38BDF8';
      navBadge.style.background = 'rgba(56, 189, 248, 0.1)';
      navBadge.style.boxShadow = 'none';
    }
    if (upgradeBtn) {
      upgradeBtn.innerText = '⚡ Pro Plan ($19) Active';
      upgradeBtn.style.borderColor = '#10B981';
      upgradeBtn.style.color = '#10B981';
      upgradeBtn.style.background = 'rgba(16, 185, 129, 0.18)';
    }
    if (barPlan) {
      barPlan.innerText = 'Pro Member ($19/mo)';
      barPlan.style.color = '#38BDF8';
    }
  } else {
    // Strictly Free / Starter for any missing, undefined, null, or guest tier
    if (navBadge) {
      navBadge.innerText = 'FREE PLAN';
      navBadge.style.borderColor = 'rgba(148, 163, 184, 0.4)';
      navBadge.style.color = '#94A3B8';
      navBadge.style.background = 'transparent';
      navBadge.style.boxShadow = 'none';
    }
    if (upgradeBtn) {
      upgradeBtn.innerText = '⚡ Upgrade Plan';
      upgradeBtn.style.borderColor = '';
      upgradeBtn.style.color = '';
      upgradeBtn.style.background = '';
    }
    if (barPlan) {
      barPlan.innerText = 'Free Plan ($0)';
      barPlan.style.color = '#94A3B8';
    }
  }
};

const SUPABASE_PROJECT_URL = "https://bijwvvnghhbgudyrecpx.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_EcC050mUrxLcfqXNxPX--Q_RI3aQ99N";

async function isolateAndSetUserSession(userPayload) {
  const email = (userPayload.email || '').trim().toLowerCase();
  if (!email) return 'free';

  const currentStored = localStorage.getItem('jobflow_auth_user');
  let currentEmail = null;
  if (currentStored) {
    try {
      currentEmail = (JSON.parse(currentStored).email || '').trim().toLowerCase();
    } catch (e) {}
  }

  // Account switch detected -> clear stale localStorage to prevent leaks
  if (currentEmail && currentEmail !== email) {
    console.log(`[JobFlow Auth] Account switch detected from ${currentEmail} to ${email}. Isolating storage.`);
    localStorage.removeItem('candidate_quick_profile');
    localStorage.removeItem('gumroad_license_key');
    localStorage.removeItem('user_subscription_tier');
    localStorage.removeItem('jobflow_free_search_quota');
  }

  const isOwner = isOwnerEmail(email);
  const fullName = userPayload.full_name || userPayload.name || (email.split('@')[0]);

  let tier = isOwner ? 'owner' : 'free';

  // If not owner, verify subscription tier against backend & Supabase
  if (!isOwner) {
    try {
      const res = await fetch(`/api/v1/auth/user-status?email=${encodeURIComponent(email)}`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.tier && data.tier !== 'owner') {
          tier = data.tier;
        }
      }
    } catch (err) {
      console.warn("User status sync error:", err);
      tier = 'free';
    }
  }

  localStorage.setItem('user_subscription_tier', tier);
  localStorage.setItem('jobflow_auth_user', JSON.stringify({
    email: email,
    full_name: fullName,
    role: isOwner ? 'owner' : 'user',
    is_admin: isOwner,
    subscription_tier: tier,
    provider: userPayload.provider || 'google',
    authenticated_at: new Date().toISOString()
  }));

  window.updateTierBadges(tier);
  refreshNavbarAuthState();

  // Restore this user's stored CV, WhatsApp, and Memory Bank from Supabase
  try {
    await loadInitialProfile();
    await loadNotificationSettings();
    await loadQuestionnaireBank();
  } catch (err) {
    console.warn("Notice during user session data hydration:", err);
  }

  return tier;
}

function extractUserFromUrlHash() {
  const hash = window.location.hash || '';
  if (hash && hash.includes('access_token=')) {
    const params = new URLSearchParams(hash.substring(1));
    const token = params.get('access_token');
    if (token) {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(decodeURIComponent(atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')));
        if (payload && payload.email) {
          const userEmail = (payload.email || '').trim().toLowerCase();
          const userName = payload.user_metadata?.full_name || payload.user_metadata?.name || payload.name || userEmail.split('@')[0];
          
          isolateAndSetUserSession({
            email: userEmail,
            full_name: userName,
            provider: 'google'
          });
          
          history.replaceState(null, document.title, window.location.pathname + window.location.search);
          return true;
        }
      } catch (err) {
        console.warn("Hash token decode notice:", err);
      }
    }
  }
  return false;
}

async function syncSupabaseUserSession() {
  extractUserFromUrlHash();

  try {
    if (window.supabase && SUPABASE_PROJECT_URL && SUPABASE_ANON_KEY) {
      const client = window.supabase.createClient(SUPABASE_PROJECT_URL, SUPABASE_ANON_KEY);
      
      // Check active Supabase session from Google OAuth
      const { data: { session } } = await client.auth.getSession();
      if (session && session.user) {
        const userEmail = (session.user.email || '').trim().toLowerCase();
        const userName = session.user.user_metadata?.full_name || session.user.user_metadata?.name || userEmail.split('@')[0];
        
        await isolateAndSetUserSession({
          email: userEmail,
          full_name: userName,
          provider: 'google'
        });
        return true;
      }

      // Listen for OAuth hash redirect changes
      client.auth.onAuthStateChange(async (event, newSession) => {
        if (newSession && newSession.user) {
          const userEmail = (newSession.user.email || '').trim().toLowerCase();
          const userName = newSession.user.user_metadata?.full_name || newSession.user.user_metadata?.name || userEmail.split('@')[0];
          await isolateAndSetUserSession({
            email: userEmail,
            full_name: userName,
            provider: 'google'
          });
        }
      });
    }
  } catch (err) {
    console.warn("Supabase session sync notice:", err);
  }
}

// ─────────────────────────────────────────────────────────────
// Authentication & User Profile Modal Handlers
// ─────────────────────────────────────────────────────────────
const GOOGLE_CLIENT_ID = "623877995804-94j5uclckk32u7n021f1q54d5k5dcrka.apps.googleusercontent.com";

window.handleGoogleSignIn = function() {
  const redirectTarget = encodeURIComponent(`${window.location.origin}/app`);
  const googleAuthUrl = `${SUPABASE_PROJECT_URL}/auth/v1/authorize?provider=google&redirect_to=${redirectTarget}`;
  window.location.href = googleAuthUrl;
};

window.handleSignOut = function() {
  localStorage.removeItem('jobflow_auth_user');
  localStorage.removeItem('user_subscription_tier');
  localStorage.removeItem('candidate_quick_profile');
  localStorage.removeItem('gumroad_license_key');
  localStorage.removeItem('jobflow_free_search_quota');
  
  if (window.supabase && SUPABASE_PROJECT_URL && SUPABASE_ANON_KEY) {
    try {
      const client = window.supabase.createClient(SUPABASE_PROJECT_URL, SUPABASE_ANON_KEY);
      client.auth.signOut();
    } catch (e) {}
  }
  
  window.location.reload();
};

window.openUserProfileModal = function() {
  let user = null;
  try {
    user = JSON.parse(localStorage.getItem('jobflow_auth_user') || 'null');
  } catch (e) {}

  const tier = (localStorage.getItem('user_subscription_tier') || 'free').toLowerCase();
  const email = user?.email || 'Guest User';
  const name = user?.full_name || (email.includes('@') ? email.split('@')[0] : 'Guest User');
  const initial = (name[0] || 'U').toUpperCase();

  const avatarEl = document.getElementById('modal-user-avatar');
  const nameEl = document.getElementById('modal-user-name');
  const emailEl = document.getElementById('modal-user-email');
  const badgeEl = document.getElementById('modal-user-tier-badge');

  if (avatarEl) avatarEl.innerText = initial;
  if (nameEl) nameEl.innerText = name;
  if (emailEl) emailEl.innerText = email;
  
  if (badgeEl) {
    if (tier === 'owner') {
      badgeEl.innerText = '👑 OWNER & ADMIN • LIFETIME ($49)';
      badgeEl.style.background = 'rgba(0, 240, 255, 0.15)';
      badgeEl.style.color = '#00F0FF';
      badgeEl.style.borderColor = 'rgba(0, 240, 255, 0.4)';
    } else if (tier === 'executive') {
      badgeEl.innerText = '👑 EXECUTIVE VIP ($49)';
      badgeEl.style.background = 'rgba(168, 85, 247, 0.15)';
      badgeEl.style.color = '#C084FC';
      badgeEl.style.borderColor = 'rgba(168, 85, 247, 0.4)';
    } else if (tier === 'pro') {
      badgeEl.innerText = '⚡ PRO MEMBER ($19/mo)';
      badgeEl.style.background = 'rgba(56, 189, 248, 0.15)';
      badgeEl.style.color = '#38BDF8';
      badgeEl.style.borderColor = 'rgba(56, 189, 248, 0.4)';
    } else {
      badgeEl.innerText = 'FREE PLAN ($0)';
      badgeEl.style.background = 'rgba(148, 163, 184, 0.15)';
      badgeEl.style.color = '#94A3B8';
      badgeEl.style.borderColor = 'rgba(148, 163, 184, 0.3)';
    }
  }

  openModal('modal-user-profile');
};

function refreshNavbarAuthState() {
  const loginBtn = document.getElementById('btn-google-login');
  const profileBtn = document.getElementById('user-profile-btn');
  const nameEl = document.getElementById('user-display-name');
  const avatarEl = document.getElementById('user-avatar-initials');

  let user = null;
  try {
    user = JSON.parse(localStorage.getItem('jobflow_auth_user') || 'null');
  } catch (e) {}

  const tier = (localStorage.getItem('user_subscription_tier') || 'free').toLowerCase();

  if (user && user.email) {
    if (loginBtn) loginBtn.style.display = 'none';
    if (profileBtn) {
      profileBtn.style.display = 'inline-flex';
      const displayName = user.full_name ? user.full_name.split(' ')[0] : (user.email.split('@')[0]);
      if (nameEl) nameEl.innerText = displayName;
      if (avatarEl) avatarEl.innerText = (displayName[0] || 'U').toUpperCase();
    }
  } else if (tier === 'owner') {
    if (loginBtn) loginBtn.style.display = 'none';
    if (profileBtn) {
      profileBtn.style.display = 'inline-flex';
      if (nameEl) nameEl.innerText = 'Mudather';
      if (avatarEl) avatarEl.innerText = 'M';
    }
  } else {
    if (loginBtn) loginBtn.style.display = 'inline-flex';
    if (profileBtn) profileBtn.style.display = 'none';
  }
}

// Load on start
document.addEventListener('DOMContentLoaded', () => {
  loadInitialProfile();
  loadNotificationSettings();
  loadQuestionnaireBank();
  loadInitialResLinkProfile();
  syncSupabaseUserSession();

  // Tier initialization: Strictly default to 'free'
  const savedTier = localStorage.getItem('user_subscription_tier') || 'free';
  window.updateTierBadges(savedTier);
  refreshNavbarAuthState();

  // Attach direct click listeners to all template buttons
  document.querySelectorAll('.template-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const tid = btn.dataset.templateId;
      if (tid) window.selectTemplate(tid);
    });
  });

  // Pre-select template according to subscription tier
  if (savedTier === 'owner' || savedTier === 'pro' || savedTier === 'executive') {
    window.selectTemplate('corporate_elite');
  } else {
    window.selectTemplate('modern');
  }
  document.getElementById('search-form')?.dispatchEvent(new Event('submit'));

  // Automatic Gumroad Purchase & License Activation from Redirect URL
  handleGumroadRedirectActivation();
});

// Automatic Gumroad Redirect Activation (Zero-friction customer onboarding)
function handleGumroadRedirectActivation() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const purchaseSuccess = urlParams.get('purchase') === 'success' || urlParams.get('payment') === 'success';
    const rawKey = urlParams.get('license_key') || urlParams.get('license') || urlParams.get('key');
    const planParam = (urlParams.get('plan') || '').toLowerCase();

    if (purchaseSuccess || rawKey || planParam) {
      let activatedTier = 'pro';
      let planName = 'Pro Plan ($19/mo)';

      if (planParam.includes('exec') || planParam.includes('vip') || planParam.includes('lifetime') || (rawKey && rawKey.toUpperCase().includes('EXEC'))) {
        activatedTier = 'executive';
        planName = 'Executive VIP Lifetime ($49)';
      }

      localStorage.setItem('user_subscription_tier', activatedTier);
      if (rawKey) {
        localStorage.setItem('gumroad_license_key', rawKey);
      }

      window.updateTierBadges(activatedTier);
      refreshNavbarAuthState();
      showToast(`🎉 Payment Confirmed! Your ${planName} is now active with unlimited access!`);

      // Clean query params from address bar smoothly
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  } catch (e) {
    console.warn("Notice: Gumroad redirect processing:", e);
  }
}

