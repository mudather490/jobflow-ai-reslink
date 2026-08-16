// JobFlow.ai Landing Page Interactive Controller

const SIM_ROLES = {
  ai: {
    title: "Target: Senior AI Engineer at Nexus AI",
    desc: "Requires Python, FastAPI, Docker, Kubernetes, Celery, and GraphRAG pipelines.",
    matched: ["Python", "FastAPI", "Docker", "PyTorch"],
    gaps: ["Kubernetes", "Celery", "GraphRAG"],
    initialScore: 68,
    boostedScore: 96,
    initialStatus: "Moderate Match (Automated screening risk)",
    boostedStatus: "Top Tier Candidate (96% ATS Match - Interview Ready)"
  },
  pm: {
    title: "Target: Lead Product Manager at Scale Systems",
    desc: "Requires Roadmap Planning, PRD Writing, SQL, A/B Testing, and Agile Leadership.",
    matched: ["Product Strategy", "PRD Writing", "User Research"],
    gaps: ["Advanced SQL", "A/B Experimentation", "Jira Automation"],
    initialScore: 62,
    boostedScore: 94,
    initialStatus: "Needs Optimization",
    boostedStatus: "High Match (Passes Recruiter Screen)"
  },
  design: {
    title: "Target: Staff UI/UX Designer at Quantum Studio",
    desc: "Requires Figma, Design Systems, Prototyping, User Testing, and Micro-animations.",
    matched: ["Figma", "Wireframing", "UI Prototyping"],
    gaps: ["Design Tokens Architecture", "Framer Code", "Accessibility Audits"],
    initialScore: 71,
    boostedScore: 98,
    initialStatus: "Strong Portfolio Match",
    boostedStatus: "Top 1% Candidate Portfolio"
  },
  growth: {
    title: "Target: Growth Marketing Lead at Apex Digital",
    desc: "Requires Paid Acquisition, Google Ads, GA4, Funnel Optimization, and SQL.",
    matched: ["Paid Social", "Copywriting", "Email Marketing"],
    gaps: ["Attribution Modeling", "SQL Querying", "Programmatic SEO"],
    initialScore: 64,
    boostedScore: 95,
    initialStatus: "Standard Match",
    boostedStatus: "Elite Growth Profile"
  }
};

let currentRoleKey = 'ai';
let isBoosted = false;

function renderSimulator(roleKey, boosted = false) {
  const role = SIM_ROLES[roleKey];
  if (!role) return;

  document.getElementById('sim-role-title').innerText = role.title;
  document.getElementById('sim-role-desc').innerText = role.desc;

  const matchedContainer = document.getElementById('sim-matched-skills');
  const gapsContainer = document.getElementById('sim-gap-skills');
  const scoreNumber = document.getElementById('sim-score-text');
  const gauge = document.getElementById('sim-gauge');
  const statusTitle = document.getElementById('sim-status-title');
  const statusDesc = document.getElementById('sim-status-desc');
  const btnBoost = document.getElementById('btn-sim-boost');

  const score = boosted ? role.boostedScore : role.initialScore;
  gauge.style.setProperty('--score', score);
  scoreNumber.innerText = `${score}%`;

  if (boosted) {
    matchedContainer.innerHTML = [...role.matched, ...role.gaps].map(s => `<span class="skill-chip chip-match">✓ ${s}</span>`).join('');
    gapsContainer.innerHTML = '<span class="skill-chip chip-match">✓ 100% Competency Coverage</span>';
    statusTitle.innerText = "✓ " + role.boostedStatus;
    statusDesc.innerText = "Google XYZ formulas incorporated into resume bullets. Ready for 1-click submission.";
    btnBoost.innerText = "✓ Score Boosted! Ingest Your Real CV";
    btnBoost.classList.add('btn-emerald');
  } else {
    matchedContainer.innerHTML = role.matched.map(s => `<span class="skill-chip chip-match">✓ ${s}</span>`).join('');
    gapsContainer.innerHTML = role.gaps.map(s => `<span class="skill-chip chip-gap">✗ ${s}</span>`).join('');
    statusTitle.innerText = "Status: " + role.initialStatus;
    statusDesc.innerText = "Candidate shows strong foundations. AI tailoring recommended to pass automated screening filters.";
    btnBoost.innerText = `🤖 Simulate AI Gap Resolution (+${role.boostedScore - role.initialScore}% Boost)`;
    btnBoost.classList.remove('btn-emerald');
  }
}

// Role Selector Click Handlers
document.querySelectorAll('.role-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentRoleKey = btn.dataset.role;
    isBoosted = false;
    renderSimulator(currentRoleKey, false);
  });
});

// Simulate Boost Button
document.getElementById('btn-sim-boost')?.addEventListener('click', () => {
  isBoosted = !isBoosted;
  renderSimulator(currentRoleKey, isBoosted);
});

// ROI Calculator Slider
const slider = document.getElementById('calc-apps-slider');
const appsVal = document.getElementById('calc-apps-val');
const hoursSaved = document.getElementById('calc-hours-saved');
const boostVal = document.getElementById('calc-interview-boost');
const moneySaved = document.getElementById('calc-money-saved');

slider?.addEventListener('input', (e) => {
  const apps = parseInt(e.target.value, 10);
  appsVal.innerText = `${apps} Applications`;
  
  const hours = Math.round(apps * 1.5);
  hoursSaved.innerText = `${hours} Hours`;
  
  const boost = Math.min(480, Math.round(180 + (apps * 2.8)));
  boostVal.innerText = `+${boost}%`;

  const money = hours * 30; // $30/hr estimated value of job seeker's time
  moneySaved.innerText = `$${money.toLocaleString()}`;
});

// FAQ Accordion Toggles
document.querySelectorAll('.faq-question').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.parentElement;
    item.classList.toggle('open');
  });
});

// Initial Simulator Render
document.addEventListener('DOMContentLoaded', () => {
  renderSimulator('ai', false);
});
