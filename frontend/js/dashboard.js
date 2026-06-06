/**
 * SkillBridge AI — Dashboard Rendering Logic
 * Dark glassmorphism UI matching SkillSync AI design system.
 */

document.addEventListener('DOMContentLoaded', () => {
  const raw = sessionStorage.getItem('analysisResult');

  if (!raw) {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (id) {
      fetchAnalysisById(id);
    } else {
      showError('No analysis data found. Please <a href="/upload">upload your resume</a> first.');
    }
    return;
  }

  try {
    const data = JSON.parse(raw);
    renderDashboard(data);
  } catch {
    showError('Failed to parse analysis data. Please try again.');
  }
});

async function fetchAnalysisById(id) {
  try {
    const res = await fetch(`/api/analysis/${id}`, { credentials: 'include' });
    if (!res.ok) throw new Error('Analysis not found.');
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    showError(err.message);
  }
}

// ─── Main Render ─────────────────────────────────────────────────────────────

function renderDashboard(data) {
  renderHeader(data);
  renderScoreDonut(data.job_fit_score);
  renderBreakdown(data.job_fit_score.breakdown);
  renderMatchedSkills(data.skills_analysis.matched_skills);
  renderMissingSkills(data.skills_analysis.missing_skills);
  renderCareerReadiness(data.career_readiness);
  renderRoadmap(data.career_readiness);
  renderQuestions(data.interview_questions);
  renderSuggestions(data.ai_suggestions);
  renderStrengths(data.strengths);
}

// ─── Header ──────────────────────────────────────────────────────────────────

function renderHeader(data) {
  document.getElementById('targetRoleInline').textContent = data.target_role;
  document.title = `${data.target_role} Analysis — SkillBridge AI`;
}

// ─── Score Donut ──────────────────────────────────────────────────────────────

function renderScoreDonut(fitScore) {
  const score = fitScore.overall;
  document.getElementById('overallScore').textContent = score + '%';
  document.getElementById('scoreAlignment').textContent =
    score >= 75 ? 'Strong Alignment' : score >= 55 ? 'Moderate Alignment' : 'Developing Fit';
  document.getElementById('scoreSummary').textContent =
    `You matched key attributes for this role. Closing the remaining skill gaps will elevate you to premium candidate tiers.`;

  // Animate SVG donut — r=95, circumference = 2π×95 ≈ 596.9
  const circumference = 2 * Math.PI * 95;
  const fill = document.getElementById('donutFill');
  fill.style.strokeDasharray = circumference;
  fill.style.strokeDashoffset = circumference;

  setTimeout(() => {
    const offset = circumference - (score / 100) * circumference;
    fill.style.strokeDashoffset = offset;
  }, 200);
}

// ─── Breakdown ────────────────────────────────────────────────────────────────

function renderBreakdown(b) {
  const fields = [
    { score: 'scoreTech', bar: 'barTech', val: b.technical_skills },
    { score: 'scoreExp',  bar: 'barExp',  val: b.experience_relevance },
    { score: 'scoreEdu',  bar: 'barEdu',  val: b.education_alignment },
    { score: 'scoreSoft', bar: 'barSoft', val: b.soft_skills },
  ];
  fields.forEach(({ score, bar, val }) => {
    document.getElementById(score).textContent = val;
    setTimeout(() => { document.getElementById(bar).style.width = val + '%'; }, 300);
  });
}

// ─── Matched Skills ───────────────────────────────────────────────────────────

function renderMatchedSkills(skills) {
  const el = document.getElementById('matchedSkills');
  if (!skills || !skills.length) {
    el.innerHTML = '<span style="color:var(--text-muted);font-size:0.85rem;">No matched skills found.</span>';
    return;
  }
  el.innerHTML = skills.map(s =>
    `<span class="skill-tag" title="${s.evidence}">${s.skill} · ${s.proficiency}</span>`
  ).join('');
}

// ─── Missing Skills ───────────────────────────────────────────────────────────

function renderMissingSkills(skills) {
  const el = document.getElementById('missingSkills');
  if (!skills || !skills.length) {
    el.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;">No critical skill gaps found!</p>';
    return;
  }
  el.innerHTML = skills.map(s => `
    <div class="missing-item">
      <span class="priority-pill p-${s.priority}">${s.priority}</span>
      <div>
        <div class="missing-name">${s.skill}</div>
        <div class="missing-impact">${s.hiring_impact}</div>
        <div class="missing-weeks">⏱ ~${s.estimated_weeks} week${s.estimated_weeks !== 1 ? 's' : ''} to learn</div>
      </div>
    </div>
  `).join('');
}

// ─── Career Readiness ─────────────────────────────────────────────────────────

function renderCareerReadiness(r) {
  document.getElementById('readinessPercent').textContent = r.current_readiness_percent + '%';
  document.getElementById('readinessWeeks').textContent  = r.estimated_weeks_to_ready;
  document.getElementById('readinessDate').textContent   = formatDate(r.predicted_ready_date);
  document.getElementById('bottleneck').textContent      = r.bottleneck_skill || '—';
}

// ─── Roadmap ──────────────────────────────────────────────────────────────────

function renderRoadmap(readiness) {
  const el = document.getElementById('roadmapTrack');

  // Build a visual 4-step milestone track from career readiness data
  const steps = [
    { icon: '👤', label: 'Profile Baseline',  time: 'Completed',       status: 'done' },
    { icon: '📚', label: 'Upskilling Focus',   time: 'This Week',       status: 'current' },
    { icon: '💬', label: 'Mock Drills',        time: 'Next Week',       status: 'future' },
    { icon: '💼', label: 'Apply',              time: `~${readiness.estimated_weeks_to_ready}w`, status: 'future' },
  ];

  el.innerHTML = steps.map(s => `
    <div class="roadmap-step">
      <div class="roadmap-icon ${s.status}">${s.icon}</div>
      <div class="roadmap-milestone ${s.status === 'current' ? 'current' : ''}">${s.label}</div>
      <div class="roadmap-time">${s.time}</div>
    </div>
  `).join('');
}

// ─── Interview Questions ──────────────────────────────────────────────────────

function renderQuestions(questions) {
  const el = document.getElementById('questionsGrid');
  if (!questions || !questions.length) {
    el.innerHTML = '<p style="color:var(--text-muted);">No questions generated.</p>';
    return;
  }

  el.innerHTML = questions.map((q, i) => `
    <div class="question-card glass-card">
      <div class="q-meta">
        <span class="q-category">Question ${String(i + 1).padStart(2, '0')}</span>
        <span class="q-type-badge">${q.type}</span>
      </div>
      ${q.danger_zone ? '<span class="danger-badge">⚠ Danger Zone</span>' : ''}
      <p class="q-text">"${q.question}"</p>
      <div class="q-actions">
        <button class="btn-practice" onclick="openPractice(${i})">Practice Now</button>
        <button class="btn-hint" onclick="toggleHint(${i})" title="Show tip">💡</button>
      </div>
      <div class="hint-box" id="hint-${i}">
        <div class="hint-label">Pro Tip</div>
        ${getHintText(q.type, q.topic)}
      </div>
    </div>
  `).join('');
}

function toggleHint(i) {
  const hint = document.getElementById(`hint-${i}`);
  hint.classList.toggle('visible');
}

function getHintText(type, topic) {
  if (type === 'Technical')
    return `Discuss real-world trade-offs, performance constraints, and failure scenarios related to ${topic || 'this topic'}.`;
  if (type === 'Behavioral')
    return 'Use the STAR method: Situation, Task, Action, and quantifiable Result.';
  return `Structure your answer with context, your specific actions, and measurable outcomes.`;
}

function openPractice(i) {
  alert(`Practice mode for Question ${i + 1} — coming soon! Focus your answer on specific technical depth and real-world examples.`);
}

// ─── Suggestions ─────────────────────────────────────────────────────────────

function renderSuggestions(suggestions) {
  const el = document.getElementById('suggestionsList');
  if (!suggestions || !suggestions.length) { el.innerHTML = ''; return; }
  el.innerHTML = suggestions.map(s =>
    `<li><span class="dot">›</span>${s}</li>`
  ).join('');
}

// ─── Strengths ────────────────────────────────────────────────────────────────

function renderStrengths(strengths) {
  const el = document.getElementById('strengthsList');
  if (!strengths || !strengths.length) { el.innerHTML = ''; return; }
  el.innerHTML = strengths.map(s =>
    `<li><span class="dot">✓</span>${s}</li>`
  ).join('');
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function showError(msg) {
  const b = document.getElementById('errorBanner');
  b.innerHTML = '⚠ ' + msg;
  b.classList.add('visible');
}

function formatDate(str) {
  if (!str) return '—';
  try {
    return new Date(str).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch { return str; }
}
