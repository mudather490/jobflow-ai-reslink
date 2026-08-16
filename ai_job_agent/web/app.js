// State Management
let currentProfile = null;
let currentJobs = [];
let selectedJob = null;
let currentMatchReport = null;
let currentOffset = 0;
let autoApplyTargetJob = null;

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
  modern: 'Modern Executive',
  harvard: 'Harvard Consulting (MBB)',
  harvard_consulting: 'Harvard Consulting (MBB)',
  tech: 'Tech Specialist & AI Innovator',
  tech_specialist: 'Tech Specialist & AI Innovator',
  minimal: 'Silicon Valley Minimalist',
  corporate_elite: 'Silicon Valley Minimalist'
};

const templateShortNames = {
  modern: 'Modern',
  harvard: 'Harvard',
  harvard_consulting: 'Harvard',
  tech: 'Tech',
  tech_specialist: 'Tech',
  minimal: 'Minimal',
  corporate_elite: 'Minimal'
};

window.selectedTemplateId = localStorage.getItem('selected_resume_template') || 'modern';

window.selectTemplate = function(templateId) {
  const normId = (templateId === 'harvard_consulting' ? 'harvard' : (templateId === 'tech_specialist' ? 'tech' : (templateId === 'corporate_elite' ? 'minimal' : templateId))) || 'modern';
  window.selectedTemplateId = normId;
  localStorage.setItem('selected_resume_template', normId);

  // Sync with server and ResLink profile
  try {
    fetch('/api/v1/templates/active', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template_id: normId })
    });
  } catch (e) {
    console.warn("Failed to sync active template with server:", e);
  }

  // Update UI Button Selection
  const btns = document.querySelectorAll('.template-btn');
  btns.forEach(b => {
    const bid = b.dataset.templateId;
    if (bid === normId || bid === templateId || b.id === `btn-tmpl-${normId}` || b.id === `btn-tmpl-${templateId}`) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  // Update active badge label
  const badge = document.getElementById('active-template-badge');
  if (badge) {
    badge.innerText = templateNames[normId] || 'Modern Executive';
  }

  // Update download button label indicators
  const pdfLbl = document.getElementById('lbl-pdf-template');
  if (pdfLbl) pdfLbl.innerText = templateShortNames[normId] || 'Modern';

  const docxLbl = document.getElementById('lbl-docx-template');
  if (docxLbl) docxLbl.innerText = templateShortNames[normId] || 'Modern';
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

// Attach Modal Listeners
document.getElementById('btn-pricing-modal')?.addEventListener('click', () => openModal('modal-pricing'));
document.getElementById('btn-settings-modal')?.addEventListener('click', async () => {
  await loadNotificationSettings();
  openModal('modal-settings');
});

// Step 1: Initialize Base Resume
async function loadInitialProfile() {
  try {
    const res = await fetch('/api/v1/resume/current');
    if (res.ok) {
      const data = await res.json();
      currentProfile = data.profile;
      renderActiveFileCard(data.filename, data.filesize, currentProfile);
    }
  } catch (err) {
    console.error("Failed to load profile:", err);
  }
}

function renderActiveFileCard(filename, filesize, profile) {
  if (filename) document.getElementById('file-display-name').innerText = filename;
  if (filesize) document.getElementById('file-size-display').innerText = filesize;
  if (profile.full_name) document.getElementById('candidate-name-display').innerText = profile.full_name;
  document.getElementById('skills-count').innerText = profile.skills.length;
  
  const cloud = document.getElementById('profile-skills-cloud');
  cloud.innerHTML = profile.skills.map(s => `
    <span class="skill-chip chip-match" style="display: inline-flex; align-items: center; gap: 4px;">
      ${s}
      <span class="skill-remove-btn" onclick="removeSkill('${s.replace(/'/g, "\\'")}', event)" title="Remove ${s}">&times;</span>
    </span>
  `).join('');
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
  const formData = new FormData();
  formData.append('file', file);

  const statusBadge = document.getElementById('resume-status-badge');
  statusBadge.innerText = '⏳ INGESTING & PARSING...';
  statusBadge.style.color = 'var(--accent-cyan)';

  try {
    const res = await fetch('/api/v1/resume/upload', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error("Upload failed");

    const data = await res.json();
    currentProfile = data.profile;
    renderActiveFileCard(data.filename, data.filesize, currentProfile);

    statusBadge.innerText = '✓ UPLOADED & READY';
    statusBadge.style.color = '#34D399';

    if (selectedJob) {
      selectJob(selectedJob);
    }
  } catch (err) {
    alert("Error uploading resume: " + err.message);
    statusBadge.innerText = '✗ UPLOAD ERROR';
    statusBadge.style.color = 'var(--accent-rose)';
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
          <div class="job-title">${job.title}</div>
          <div class="job-company">${job.company}</div>
        </div>
        <span class="nav-badge" style="border-color: rgba(56, 189, 248, 0.3); color: var(--accent-cyan);">${job.posted_date}</span>
      </div>
      <div style="display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0 6px 0; align-items: center;">
        <span class="${getWorkplaceBadgeClass(job.workplace_type)}">${job.workplace_badge || '🏡 Remote Only'}</span>
        <span class="badge-employment">${job.employment_badge || '💼 Full-Time'}</span>
        <span class="${getBadgeClass(job.remote_scope)}">${job.international_badge || '🌐 Worldwide'}</span>
        ${job.is_easy_apply ? `<span class="badge-easy-apply">${job.easy_apply_badge || '⚡ Easy Apply'}</span>` : `<span class="badge-employment" style="background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.12); color: var(--text-dim);">🌐 Direct Apply</span>`}
      </div>
      <div class="job-meta" style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
        <div>
          <span>📍 ${job.location}</span>
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
    const res = await fetch('/api/v1/jobs/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: job.job_id, job_title: job.title, company: job.company, location: job.location, job_url: job.job_url })
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
  matchedCloud.innerHTML = report.matched_skills.map(s => `<span class="skill-chip chip-match">✓ ${s}</span>`).join('') || '<span style="color:var(--text-dim);font-size:12px;">None detected</span>';

  // Render Missing Skills
  const missingCloud = document.getElementById('missing-skills-cloud');
  const missingCountBadge = document.getElementById('missing-count-badge');
  if (missingCountBadge) missingCountBadge.innerText = `${report.missing_critical_skills.length} Missing`;
  missingCloud.innerHTML = report.missing_critical_skills.map(s => `<span class="skill-chip chip-gap">✗ ${s}</span>`).join('') || '<span class="skill-chip chip-match">✓ 100% Match (No Gaps)</span>';

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

// Step 5: Multi-Template Document Downloads
document.getElementById('btn-download-pdf')?.addEventListener('click', (e) => {
  e.preventDefault();
  const tmpl = window.selectedTemplateId || 'modern';
  window.open(`/api/v1/resume/download-pdf?template_id=${encodeURIComponent(tmpl)}&t=${Date.now()}`, '_blank');
});

document.getElementById('btn-download-docx')?.addEventListener('click', (e) => {
  e.preventDefault();
  const tmpl = window.selectedTemplateId || 'modern';
  window.open(`/api/v1/resume/download-docx?template_id=${encodeURIComponent(tmpl)}&t=${Date.now()}`, '_blank');
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
  try {
    const res = await fetch('/api/v1/questionnaire');
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

  try {
    if (btn) {
      btn.disabled = true;
      btn.innerText = "⏳ Saving...";
    }
    const res = await fetch('/api/v1/questionnaire/save-all', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: answersPayload })
    });

    if (res.ok) {
      if (btn) {
        btn.innerText = "✓ Saved to Memory Bank!";
        btn.style.background = "#10B981";
      }
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
  document.getElementById('auto-app-name').value = saved.full_name || (currentProfile?.full_name || 'Mudather Mohammed');
  document.getElementById('auto-app-email').value = saved.email || (currentProfile?.contact?.email || 'mudatherkbyer@gmail.com');
  document.getElementById('auto-app-phone').value = saved.phone || (currentProfile?.contact?.phone || '+1 (555) 345-6789');
  document.getElementById('auto-app-linkedin').value = saved.linkedin_url || (currentProfile?.contact?.linkedin || 'linkedin.com/in/mudather-mohammed');
  document.getElementById('auto-app-github').value = saved.github_url || (currentProfile?.contact?.github || 'github.com/mudather');
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
      alert(`🚀 Autonomous Batch Auto-Apply Complete!\n\n• Successfully Auto-Applied: ${results.applied_count} Jobs\n• Needs New Answers: ${results.needs_input_count} Jobs\n\nAll tailored PDF application bundles were generated in the ${window.selectedTemplateId.toUpperCase()} template and company records were logged to your Excel Tracker!`);
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

// Step 9: Download Application History & Company Intelligence as Excel / CSV
window.downloadApplicationExcel = function() {
  const url = `/api/v1/applications/export-excel?t=${Date.now()}`;
  window.open(url, '_blank');
};

window.downloadApplicationCSV = function() {
  const url = `/api/v1/applications/export-csv?t=${Date.now()}`;
  window.open(url, '_blank');
};

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
  execBtn.innerText = '⏳ AI Packaging Application...';

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
      successBox.style.display = 'block';
      document.getElementById('auto-apply-msg').innerText = `Your application for ${autoApplyTargetJob.title} at ${autoApplyTargetJob.company} was assembled with the "${window.selectedTemplateId.toUpperCase()}" CV template. Email & Telegram notifications dispatched!`;

      const answersContainer = document.getElementById('prefilled-answers-container');
      const answers = data.prefilled_answers || {};
      answersContainer.innerHTML = Object.entries(answers).map(([key, val]) => `
        <div class="prefilled-card">
          <div class="prefilled-label">${key}</div>
          <div class="prefilled-val">${val}</div>
        </div>
      `).join('');

      document.getElementById('btn-auto-download-pdf').onclick = () => {
        window.open(`/api/v1/resume/download-pdf?template_id=${encodeURIComponent(window.selectedTemplateId || 'modern')}&t=${Date.now()}`, '_blank');
      };
      document.getElementById('btn-auto-download-docx').onclick = () => {
        window.open(`/api/v1/resume/download-docx?template_id=${encodeURIComponent(window.selectedTemplateId || 'modern')}&t=${Date.now()}`, '_blank');
      };

      execBtn.innerText = '✓ Submitted Successfully';
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

// Step 9: Notification Channels & Alert Settings Controller
async function loadNotificationSettings() {
  try {
    const res = await fetch('/api/v1/settings/notifications');
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

  msgEl.innerHTML = '<span style="color: var(--accent-cyan)">Saving preferences...</span>';

  try {
    const res = await fetch('/api/v1/settings/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, whatsapp: wa, telegram: tg })
    });
    if (res.ok) {
      msgEl.innerHTML = '<span style="color: var(--accent-emerald)">✓ Preferences saved successfully!</span>';
      
      if (document.getElementById('bar-email')) document.getElementById('bar-email').innerText = email || 'Not Configured';
      if (document.getElementById('bar-whatsapp')) document.getElementById('bar-whatsapp').innerText = wa || 'Not Configured';
      if (document.getElementById('bar-telegram')) document.getElementById('bar-telegram').innerText = tg ? (tg.startsWith('@') ? tg : '@' + tg) : 'Not Configured';

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
    clearInterval(prompterScrollInterval);
    isPrompterScrolling = false;
    btn.innerHTML = '▶ Start Prompter';
    btn.classList.remove('btn-emerald');
  } else {
    isPrompterScrolling = true;
    btn.innerHTML = '⏸ Pause Prompter';
    btn.classList.add('btn-emerald');

    const wpm = parseInt(document.getElementById('teleprompter-wpm').value) || 135;
    const pixelsPerStep = (wpm / 135) * 1.5;

    prompterScrollInterval = setInterval(() => {
      container.scrollTop += pixelsPerStep;
      if (container.scrollTop >= container.scrollHeight - container.clientHeight) {
        clearInterval(prompterScrollInterval);
        isPrompterScrolling = false;
        btn.innerHTML = '▶ Restart Prompter';
        btn.classList.remove('btn-emerald');
      }
    }, 50);
  }
};

window.updateTeleprompterSpeed = function() {
  if (isPrompterScrolling) {
    window.toggleTeleprompterScroll(); // pause
    window.toggleTeleprompterScroll(); // restart with new speed
  }
};

window.toggleWebcam = async function() {
  const videoElem = document.getElementById('studio-webcam-preview');
  const placeholder = document.getElementById('camera-placeholder');
  const btnCam = document.getElementById('btn-toggle-camera');
  const btnRec = document.getElementById('btn-record-pitch');

  if (studioMediaStream) {
    // Stop camera
    studioMediaStream.getTracks().forEach(track => track.stop());
    studioMediaStream = null;
    videoElem.srcObject = null;
    placeholder.style.display = 'block';
    btnCam.innerHTML = '📹 Start Camera';
    btnRec.disabled = true;
  } else {
    try {
      studioMediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: 'user' },
        audio: true
      });
      videoElem.srcObject = studioMediaStream;
      placeholder.style.display = 'none';
      btnCam.innerHTML = '⏹ Turn Off Camera';
      btnRec.disabled = false;
      showToast("✓ Studio Camera & Microphone Active");
    } catch (err) {
      console.warn("Camera video stream unavailable, attempting audio fallback:", err);
      try {
        studioMediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        placeholder.innerHTML = `
          <div style="font-size: 32px; margin-bottom: 8px;">🎙️</div>
          <div style="font-weight: 700; color: #34D399; font-size: 14px;">Microphone Connected (Voice Mode)</div>
          <div style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">Camera was blocked; recording voice pitch</div>
        `;
        btnCam.innerHTML = '⏹ Disconnect Mic';
        btnRec.disabled = false;
        showToast("🎙️ Microphone Connected for Voice Pitch!");
      } catch (audioErr) {
        placeholder.innerHTML = `
          <div style="font-size: 28px; margin-bottom: 8px;">📁</div>
          <div style="font-weight: 700; color: #F59E0B; font-size: 14px;">Camera / Mic Permission Denied</div>
          <div style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">You can upload an MP4 video or use AI Voice Pitch</div>
        `;
        showToast("Camera permission not granted. You can upload an MP4 video directly.");
      }
    }
  }
};

window.toggleRecording = function() {
  const btnRec = document.getElementById('btn-record-pitch');
  const indicator = document.getElementById('recording-indicator');

  if (studioMediaRecorder && studioMediaRecorder.state === 'recording') {
    // Stop recording
    studioMediaRecorder.stop();
    clearInterval(recordingTimerInterval);
    indicator.style.display = 'none';
    btnRec.innerHTML = '🔴 Start Recording';
    btnRec.style.background = '#EF4444';
    if (isPrompterScrolling) window.toggleTeleprompterScroll(); // pause prompter
  } else {
    if (!studioMediaStream) {
      showToast("Please start camera before recording.");
      return;
    }

    recordedVideoChunks = [];
    studioMediaRecorder = new MediaRecorder(studioMediaStream, { mimeType: 'video/webm' });

    studioMediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) recordedVideoChunks.push(e.data);
    };

    studioMediaRecorder.onstop = async () => {
      const blob = new Blob(recordedVideoChunks, { type: 'video/webm' });
      showToast("⏳ Uploading video pitch to ResLink...");
      
      const formData = new FormData();
      formData.append('file', blob, 'pitch_recording.webm');

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

    studioMediaRecorder.start();
    recordingSeconds = 0;
    indicator.style.display = 'inline';
    indicator.innerText = '● REC 00:00';
    btnRec.innerHTML = '⏹ Stop & Save Video';
    btnRec.style.background = '#10B981';

    // Start prompter automatically on record
    if (!isPrompterScrolling) window.toggleTeleprompterScroll();

    recordingTimerInterval = setInterval(() => {
      recordingSeconds++;
      const mins = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
      const secs = String(recordingSeconds % 60).padStart(2, '0');
      indicator.innerText = `● REC ${mins}:${secs}`;
    }, 1000);
  }
};

window.saveResLinkConfiguration = async function() {
  const calendly = document.getElementById('reslink-setting-calendly').value.trim();
  const whatsapp = document.getElementById('reslink-setting-whatsapp').value.trim();
  const theme = document.getElementById('reslink-setting-theme').value;

  try {
    const getRes = await fetch('/api/v1/reslink');
    const cur = await getRes.json();

    cur.cta_settings = cur.cta_settings || {};
    cur.cta_settings.calendly_url = calendly;
    cur.cta_settings.whatsapp_number = whatsapp;
    cur.theme = theme;
    cur.selected_cv_template = window.selectedTemplateId || 'harvard';

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
      localStorage.setItem('user_subscription_tier', data.tier || 'pro');
      localStorage.setItem('gumroad_license_key', key);
      statusMsg.style.display = 'block';
      statusMsg.style.color = '#10B981';
      statusMsg.innerText = `✓ Successfully activated ${data.plan}! Unlimited access enabled.`;
      showToast(`✓ Activated ${data.plan}!`);
      
      const badge = document.getElementById('btn-pricing-modal');
      if (badge) {
        badge.innerText = `⚡ ${data.plan}`;
        badge.style.borderColor = '#10B981';
        badge.style.color = '#10B981';
      }
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

// ─────────────────────────────────────────────────────────────
// Master Unified App Navigation & ResLink Studio Integration
// ─────────────────────────────────────────────────────────────

window.switchAppTab = function(tabName) {
  const radarView = document.getElementById('view-radar');
  const studioView = document.getElementById('view-studio');
  const showcaseView = document.getElementById('view-showcase');

  const btnRadar = document.getElementById('tab-btn-radar');
  const btnStudio = document.getElementById('tab-btn-studio');
  const btnShowcase = document.getElementById('tab-btn-showcase');

  // Reset tab button states
  [btnRadar, btnStudio, btnShowcase].forEach(btn => {
    if (btn) {
      btn.style.background = 'transparent';
      btn.style.color = 'var(--text-muted)';
      btn.style.borderColor = 'transparent';
      btn.classList.remove('active');
    }
  });

  // Hide all view panes
  [radarView, studioView, showcaseView].forEach(v => {
    if (v) v.style.display = 'none';
  });

  if (tabName === 'studio') {
    if (studioView) studioView.style.display = 'block';
    if (btnStudio) {
      btnStudio.style.background = 'rgba(0, 240, 255, 0.15)';
      btnStudio.style.color = '#00F0FF';
      btnStudio.style.borderColor = 'rgba(0, 240, 255, 0.4)';
      btnStudio.classList.add('active');
    }
    window.location.hash = 'studio';
    window.loadStudioProfile?.();
  } else if (tabName === 'showcase') {
    if (showcaseView) {
      showcaseView.style.display = 'block';
      const iframe = document.getElementById('showcase-preview-frame');
      const slug = (reslinkProfileState && reslinkProfileState.slug) ? reslinkProfileState.slug : 'mudather-mohammed';
      if (iframe) {
        iframe.src = `/p/${slug}`;
      }
    }
    if (btnShowcase) {
      btnShowcase.style.background = 'rgba(0, 240, 255, 0.15)';
      btnShowcase.style.color = '#00F0FF';
      btnShowcase.style.borderColor = 'rgba(0, 240, 255, 0.4)';
      btnShowcase.classList.add('active');
    }
    window.location.hash = 'showcase';
  } else {
    // Default: radar
    if (radarView) radarView.style.display = 'block';
    if (btnRadar) {
      btnRadar.style.background = 'rgba(0, 240, 255, 0.15)';
      btnRadar.style.color = '#00F0FF';
      btnRadar.style.borderColor = 'rgba(0, 240, 255, 0.4)';
      btnRadar.classList.add('active');
    }
    window.location.hash = 'radar';
  }
};

window.goToStudioStep = function(stepNum) {
  for (let i = 1; i <= 4; i++) {
    const pane = document.getElementById(`pane-step-${i}`);
    const tab = document.getElementById(`tab-step-${i}`);
    if (pane) pane.style.display = (i === stepNum) ? 'block' : 'none';
    if (tab) {
      if (i === stepNum) {
        tab.classList.add('active');
        tab.style.background = 'rgba(56, 189, 248, 0.15)';
        tab.style.borderColor = 'rgba(56, 189, 248, 0.4)';
        tab.style.color = '#fff';
      } else {
        tab.classList.remove('active');
        tab.style.background = 'transparent';
        tab.style.borderColor = 'transparent';
        tab.style.color = 'var(--text-muted)';
      }
    }
  }
};

window.selectStudioTemplate = function(templateId) {
  window.selectTemplate(templateId);
  const btns = ['modern', 'harvard', 'corporate', 'tech'];
  btns.forEach(b => {
    const el = document.getElementById(`btn-studio-tmpl-${b}`);
    if (el) {
      if (templateId.startsWith(b)) el.classList.add('active');
      else el.classList.remove('active');
    }
  });
  const nameEl = document.getElementById('studio-active-template-name');
  if (nameEl) nameEl.innerText = templateNames[templateId] || 'Corporate Elite';
};

window.downloadStudioTestPDF = function() {
  const tmpl = window.selectedTemplateId || 'corporate_elite';
  const url = `/api/v1/resume/download/pdf?template_id=${tmpl}`;
  window.open(url, '_blank');
  showToast(`📥 Downloading test CV (${templateNames[tmpl] || 'Corporate Elite'})...`);
};

window.copyPublicResLink = function() {
  const slug = (reslinkProfileState && reslinkProfileState.slug) ? reslinkProfileState.slug : 'mudather-mohammed';
  const url = `${window.location.origin}/p/${slug}`;
  navigator.clipboard.writeText(url).then(() => {
    showToast("✓ Public ResLink URL copied to clipboard!");
  }).catch(() => {
    showToast(`URL: ${url}`);
  });
};

window.copyLinkedInMessage = function() {
  const el = document.getElementById('studio-linkedin-outreach');
  const text = el ? el.value : '';
  if (text) {
    navigator.clipboard.writeText(text).then(() => {
      showToast("✓ Tailored LinkedIn outreach note copied!");
    });
  }
};

window.regeneratePitchScript = function() {
  const job = document.getElementById('studio-target-job')?.value || 'AI Engineer';
  const comp = document.getElementById('studio-target-company')?.value || 'Tech Labs';
  const name = (currentProfile && currentProfile.full_name) ? currentProfile.full_name : 'MUDATHER MOHAMMED';
  
  const script = `Hi Hiring Team at ${comp}! My name is ${name}, and I'm thrilled to present my candidacy for the ${job} position. Over the past several years, I have engineered scalable software, Machine Learning models, and LLM APIs. What excites me most about ${comp} is your commitment to high-impact technical excellence. You can explore my full interactive project portfolio below, download my tailored CV, or schedule a conversation directly. Looking forward to connecting!`;
  
  const txt = document.getElementById('studio-pitch-script');
  if (txt) txt.value = script;
  const prompterTxt = document.getElementById('teleprompter-text');
  if (prompterTxt) prompterTxt.innerText = script;
  showToast("✨ Generated fresh personalized pitch script!");
};

window.setPrompterSpeed = function(spd) {
  teleprompterSpeed = spd;
  showToast(`Teleprompter speed set to ${spd}x`);
};

window.handleStudioVideoUpload = function(e) {
  const file = e.target.files[0];
  if (!file) return;
  const videoElem = document.getElementById('studio-webcam-preview');
  const placeholder = document.getElementById('camera-placeholder');
  if (videoElem) {
    videoElem.srcObject = null;
    videoElem.src = URL.createObjectURL(file);
    videoElem.muted = false;
    videoElem.controls = true;
    if (placeholder) placeholder.style.display = 'none';
    showToast(`✓ Uploaded video pitch: ${file.name}`);
  }
};

// Load on start
document.addEventListener('DOMContentLoaded', () => {
  loadInitialProfile();
  loadNotificationSettings();
  loadQuestionnaireBank();
  loadInitialResLinkProfile();

  // Restore active subscription tier badge if present
  const savedTier = localStorage.getItem('user_subscription_tier');
  if (savedTier && savedTier !== 'starter') {
    const badge = document.getElementById('btn-pricing-modal');
    if (badge) {
      const planName = savedTier === 'executive' ? 'Executive Pilot' : 'Pro Member';
      badge.innerText = `⚡ ${planName}`;
      badge.style.borderColor = '#10B981';
      badge.style.color = '#10B981';
    }
  }

  // Attach direct click listeners to all template buttons
  document.querySelectorAll('.template-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const tid = btn.dataset.templateId;
      if (tid) window.selectTemplate(tid);
    });
  });

  window.selectTemplate(window.selectedTemplateId || 'corporate_elite');

  // Check initial hash route
  const hash = (window.location.hash || '').replace('#', '');
  if (hash === 'studio') {
    window.switchAppTab('studio');
  } else if (hash === 'showcase') {
    window.switchAppTab('showcase');
  } else {
    window.switchAppTab('radar');
  }

  document.getElementById('search-form')?.dispatchEvent(new Event('submit'));
});


