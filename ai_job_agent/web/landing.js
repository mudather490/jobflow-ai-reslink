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

// ─────────────────────────────────────────────────────────────
// Supabase & Google Identity Services (GIS) OAuth Handlers
// ─────────────────────────────────────────────────────────────
const SUPABASE_PROJECT_URL = "https://bijwvvnghhbgudyrecpx.supabase.co";
const GOOGLE_CLIENT_ID = "717078095584-05fudemno04qgugutasf4ih85c79jjij.apps.googleusercontent.com";

function getGoogleAuthUrl() {
  const currentOrigin = window.location.origin;
  const redirectTarget = encodeURIComponent(currentOrigin + '/app');
  return `${SUPABASE_PROJECT_URL}/auth/v1/authorize?provider=google&redirect_to=${redirectTarget}&prompt=select_account&access_type=offline`;
}

window.handleSocialAuth = function(provider = 'google') {
  const currentOrigin = window.location.origin;
  const redirectTarget = encodeURIComponent(currentOrigin + '/app');
  
  if (provider === 'google') {
    window.location.href = getGoogleAuthUrl();
  } else {
    const linkedinAuthUrl = `${SUPABASE_PROJECT_URL}/auth/v1/authorize?provider=linkedin_oidc&redirect_to=${redirectTarget}`;
    window.location.href = linkedinAuthUrl;
  }
};

window.handleGoogleSignIn = function() {
  window.handleSocialAuth('google');
};

// Handle Google One-Tap / GIS Credential Response (Mobile & Desktop)
function parseJwtPayload(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

function handleGoogleCredentialResponse(response) {
  if (response && response.credential) {
    const payload = parseJwtPayload(response.credential);
    if (payload && payload.email) {
      const email = payload.email.toLowerCase();
      const name = payload.name || 'Mudather Mohammed';
      const isOwner = email.includes('mudather') || email === 'mudatherkbyer@gmail.com';
      
      localStorage.setItem('jobflow_auth_user', JSON.stringify({
        email: email,
        full_name: name,
        role: isOwner ? 'owner' : 'user',
        is_admin: isOwner,
        subscription_tier: isOwner ? 'executive' : 'starter',
        provider: 'google',
        authenticated_at: new Date().toISOString()
      }));
      localStorage.setItem('user_subscription_tier', isOwner ? 'owner' : 'starter');
      window.location.href = '/app';
    }
  }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  renderSimulator('ai', false);

  // Set direct href on Google Sign-In buttons
  const directUrl = getGoogleAuthUrl();
  const navBtn = document.getElementById('google-signin-btn-navbar');
  const heroBtn = document.getElementById('google-signin-btn-hero');
  if (navBtn) navBtn.href = directUrl;
  if (heroBtn) heroBtn.href = directUrl;

  // Initialize Google Identity Services (GIS) One-Tap Prompt
  if (window.google && window.google.accounts && window.google.accounts.id) {
    try {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
      });
      window.google.accounts.id.prompt();
    } catch (err) {
      console.warn("GIS One-Tap notice:", err);
    }
  } else {
    // Retry once GIS script loads
    window.addEventListener('load', () => {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleGoogleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true
          });
          window.google.accounts.id.prompt();
        } catch (e) {}
      }
    });
  }
});
