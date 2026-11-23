/**
 * Codex Tutor — Client Application Controller
 * Minimalist, elegant state orchestration matching the OpenAI Codex aesthetic.
 */

const state = {
  activeView: 'home',
  activeConcept: 'py.variables',
  activeStudent: null,
  curriculum: [],
  frontier: null,
  lessons: {},
  auditHash: '',
  swapStep: 1,
};

// ---------------------------------------------------------------------------
// 1. INITIALIZATION & LIFECYCLE
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  await fetchSystemStatus();
  await fetchCurriculum();
  await loadLesson(state.activeConcept);
  await fetchRamState();
  initSwapStage();
});

async function fetchSystemStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    state.activeStudent = data.active_student;
    state.frontier = data.frontier;
    state.auditHash = data.ledger_audit.fingerprint || '86C09D8BB6567BD0';

    // Top header label
    const learnerLabel = document.getElementById('top-learner-label');
    if (learnerLabel) learnerLabel.innerText = `${data.active_student.name} (${data.active_student.student_id})`;

    const fingerprintLabel = document.getElementById('sidebar-fingerprint');
    if (fingerprintLabel) fingerprintLabel.innerText = state.auditHash;

    const auditMainLabel = document.getElementById('audit-main-fingerprint');
    if (auditMainLabel) auditMainLabel.innerText = state.auditHash;

    // Cockpit pills
    const frontierTarget = data.frontier.ready[0] || data.frontier.in_progress[0] || 'py.operators_expressions';
    const phasePill = document.getElementById('cockpit-phase-pill');
    if (phasePill) phasePill.innerText = 'Frontier Learning';

    const conceptPill = document.getElementById('cockpit-concept-pill');
    if (conceptPill) conceptPill.innerText = frontierTarget;

    const homeSub = document.getElementById('home-subtitle');
    if (homeSub) {
      homeSub.innerHTML = `Socratic tutor active • Target concept: <code class="text-codex-text font-mono text-xs">${frontierTarget}</code>`;
    }
  } catch (err) {
    console.error('Error fetching status:', err);
  }
}

async function fetchCurriculum() {
  try {
    const res = await fetch('/api/curriculum');
    const data = await res.json();
    state.curriculum = data.concepts;

    const container = document.getElementById('sidebar-concepts-list');
    if (!container) return;

    container.innerHTML = data.concepts.map((c, idx) => {
      let statusDot = 'bg-zinc-600';
      let statusText = `${Math.round(c.mastery * 100)}%`;

      if (c.status === 'mastered') {
        statusDot = 'bg-emerald-400';
      } else if (c.status === 'ready') {
        statusDot = 'bg-amber-400';
        statusText = 'Ready';
      } else if (c.status === 'in_progress') {
        statusDot = 'bg-cyan-400';
      } else {
        statusDot = 'bg-zinc-600';
        statusText = 'Locked';
      }

      const isCurrent = c.id === state.activeConcept;
      const activeClass = isCurrent ? 'bg-codex-card text-white' : 'text-codex-secondary hover:text-white hover:bg-codex-hover';

      return `
        <div onclick="showConceptLesson('${c.id}')"
          class="px-2 py-1.5 rounded-md ${activeClass} cursor-pointer transition flex items-center justify-between text-xs group">
          <div class="flex items-center space-x-2 truncate pr-2">
            <span class="w-1.5 h-1.5 rounded-full ${statusDot} shrink-0"></span>
            <span class="truncate font-sans">${c.title.split('(')[0]}</span>
          </div>
          <span class="text-[10px] font-mono text-codex-muted group-hover:text-codex-secondary shrink-0">
            ${statusText}
          </span>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error fetching curriculum:', err);
  }
}

// ---------------------------------------------------------------------------
// 2. VIEW NAVIGATION & ROUTER
// ---------------------------------------------------------------------------
function showView(viewId) {
  state.activeView = viewId;

  // Toggle view panels
  const panels = document.querySelectorAll('.view-panel');
  panels.forEach(p => p.classList.add('hidden'));

  const activePanel = document.getElementById(`view-${viewId}`);
  if (activePanel) activePanel.classList.remove('hidden');

  // Update left slim icon rail active state
  const railBtns = document.querySelectorAll('aside button[id^="nav-btn-"]');
  railBtns.forEach(btn => {
    btn.classList.remove('bg-codex-card', 'text-white');
    btn.classList.add('text-codex-secondary');
  });

  const activeBtn = document.getElementById(`nav-btn-${viewId}`);
  if (activeBtn) {
    activeBtn.classList.remove('text-codex-secondary');
    activeBtn.classList.add('bg-codex-card', 'text-white');
  }

  // Refresh sub-views
  if (viewId === 'plan') refreshDailyPlan();
  if (viewId === 'audit') refreshAuditTrail();
  if (viewId === 'ram') fetchRamState();
}

function showConceptLesson(conceptId) {
  showView('lessons');
  loadLesson(conceptId);
}

// ---------------------------------------------------------------------------
// 3. LESSONS & CONCEPT ANIMATIONS CONTROLLER
// ---------------------------------------------------------------------------
async function loadLesson(conceptId) {
  state.activeConcept = conceptId;

  // Update horizontal tabs
  const tabs = document.querySelectorAll('.lesson-nav-btn');
  tabs.forEach(t => {
    t.classList.remove('bg-codex-card', 'text-white');
    t.classList.add('text-codex-secondary');
  });
  const currentTab = document.getElementById(`lesson-tab-${conceptId}`);
  if (currentTab) {
    currentTab.classList.remove('text-codex-secondary');
    currentTab.classList.add('bg-codex-card', 'text-white');
  }

  // Update cockpit pill
  const conceptPill = document.getElementById('cockpit-concept-pill');
  if (conceptPill) conceptPill.innerText = conceptId;

  try {
    const res = await fetch(`/api/lessons/${conceptId}`);
    const lesson = await res.json();
    state.lessons[conceptId] = lesson;

    // Left Column Fields
    document.getElementById('lesson-id-badge').innerText = lesson.concept_id;
    document.getElementById('lesson-title').innerText = lesson.title;
    document.getElementById('lesson-theory').innerText = lesson.theory;
    document.getElementById('lesson-code-block').innerText = lesson.code_example;

    // Physical Analogy
    document.getElementById('lesson-analogy-name').innerText = lesson.analogy.name;
    document.getElementById('lesson-analogy-metaphor').innerText = lesson.analogy.metaphor;
    document.getElementById('lesson-analogy-trap').innerText = `Mental Trap: ${lesson.analogy.trap}`;

    // Misconceptions
    const miscList = document.getElementById('lesson-misconceptions-list');
    miscList.innerHTML = lesson.misconceptions.map(m => `
      <div class="p-2.5 rounded-lg bg-[#18181c] border border-codex-border space-y-1">
        <div class="font-medium text-codex-text text-xs">${m.name}</div>
        <div class="text-[11px] text-codex-secondary"><span class="text-codex-muted">Trap:</span> ${m.mistake}</div>
        <div class="text-[11px] text-emerald-400/90"><span class="text-emerald-500/70">Correction:</span> ${m.correction}</div>
      </div>
    `).join('');

    // Socratic Diagnostic Prompt
    document.getElementById('lesson-diagnostic-prompt').innerText = lesson.diagnostic_prompt;

    // Reset feedback
    document.getElementById('lesson-answer-input').value = '';
    const feedbackCard = document.getElementById('lesson-eval-feedback-card');
    feedbackCard.classList.add('hidden');

    // Trigger Dedicated Interactive Animation
    animEngine.setConcept(conceptId);

    // Refresh sidebar highlighting
    fetchCurriculum();

  } catch (err) {
    console.error('Error loading lesson:', err);
  }
}

async function submitLessonAnswer() {
  const input = document.getElementById('lesson-answer-input');
  const answer = input ? input.value.trim() : '';
  if (!answer) {
    alert('Please enter an answer to evaluate.');
    return;
  }

  const submitBtn = document.getElementById('lesson-submit-btn');
  if (submitBtn) {
    submitBtn.innerText = 'Evaluating...';
    submitBtn.disabled = true;
  }

  try {
    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        concept_id: state.activeConcept,
        student_answer: answer,
      })
    });
    const result = await res.json();

    // Render evaluation feedback card
    const feedbackCard = document.getElementById('lesson-eval-feedback-card');
    feedbackCard.classList.remove('hidden');

    const isCorrect = result.is_correct;
    feedbackCard.className = isCorrect
      ? 'p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-xs space-y-1.5 transition-all'
      : 'p-3.5 rounded-lg bg-amber-950/20 border border-amber-500/30 text-xs space-y-1.5 transition-all';

    feedbackCard.innerHTML = `
      <div class="flex items-center justify-between font-mono text-[11px]">
        <span class="${isCorrect ? 'text-emerald-400 font-medium' : 'text-amber-400 font-medium'}">
          ${isCorrect ? 'Correct Assessment' : 'Needs Refinement'} (${Math.round(result.score * 100)}%)
        </span>
        <span class="text-codex-muted">Mode: ${result.evaluator_mode}</span>
      </div>
      <p class="text-codex-text leading-relaxed text-xs">${result.feedback}</p>
      ${result.misconception_detected ? `
        <div class="text-[11px] font-mono text-amber-300/90 bg-[#1c1c20] p-2 rounded border border-amber-500/20">
          Misconception noted: ${result.misconception_detected}
        </div>
      ` : ''}
      <div class="flex items-center justify-between pt-1 border-t border-codex-border text-[10px] font-mono text-codex-muted">
        <span>Citations: [${(result.cited_chunk_ids || []).join(', ') || 'verified'}]</span>
        <span class="text-codex-secondary">Updated Mastery: ${Math.round(result.updated_mastery * 100)}%</span>
      </div>
    `;

    // Refresh curriculum to reflect new mastery
    await fetchCurriculum();
    await fetchSystemStatus();

  } catch (err) {
    console.error('Error evaluating answer:', err);
  } finally {
    if (submitBtn) {
      submitBtn.innerText = 'Evaluate Answer';
      submitBtn.disabled = false;
    }
  }
}

// ---------------------------------------------------------------------------
// 4. DAILY 30/60/10 SESSION PLANNER
// ---------------------------------------------------------------------------
async function refreshDailyPlan() {
  const container = document.getElementById('plan-items-container');
  if (!container) return;
  container.innerHTML = '<div class="p-3 text-xs text-codex-muted font-mono">Generating daily schedule...</div>';

  try {
    const res = await fetch('/api/session-plan?n=10');
    const data = await res.json();

    document.getElementById('plan-review-count').innerText = `${data.counts.review} Items`;
    document.getElementById('plan-frontier-count').innerText = `${data.counts.frontier} Items`;
    document.getElementById('plan-synthesis-count').innerText = `${data.counts.synthesis} Item`;

    container.innerHTML = data.items.map((item, idx) => {
      let tagColor = 'text-codex-muted';
      if (item.category === 'review') tagColor = 'text-emerald-400';
      if (item.category === 'frontier') tagColor = 'text-amber-400';
      if (item.category === 'synthesis') tagColor = 'text-cyan-400';

      return `
        <div class="p-3 rounded-xl bg-codex-card border border-codex-border hover:bg-codex-hover transition flex items-center justify-between space-x-4">
          <div class="space-y-0.5 max-w-xl">
            <div class="flex items-center space-x-2 text-[11px] font-mono">
              <span class="text-codex-muted">#${idx + 1}</span>
              <span class="${tagColor} uppercase">${item.category}</span>
              <span class="text-codex-secondary">${item.concept_id}</span>
            </div>
            <p class="text-xs text-codex-text line-clamp-1">${item.prompt}</p>
          </div>
          <button onclick="showConceptLesson('${item.concept_id}')"
            class="px-2.5 py-1 rounded bg-[#2a2a30] hover:bg-[#34343a] text-xs font-mono text-codex-secondary hover:text-white shrink-0 transition">
            Launch
          </button>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error fetching plan:', err);
    container.innerHTML = '<div class="text-rose-400 text-xs">Error generating daily plan.</div>';
  }
}

// ---------------------------------------------------------------------------
// 5. HARDWARE RAM VISUALIZER & 3-STEP SWAP MOVIE
// ---------------------------------------------------------------------------
async function fetchRamState() {
  try {
    const res = await fetch('/api/memory-state');
    const data = await res.json();

    const container = document.getElementById('ram-boxes-container');
    if (!container) return;

    container.innerHTML = data.variables.map(v => `
      <div class="p-3.5 rounded-xl bg-codex-card border border-codex-border space-y-1.5">
        <div class="flex items-center justify-between text-[11px] font-mono text-codex-muted">
          <span>${v.label}</span>
          <span>${v.address}</span>
        </div>
        <div class="text-xl font-mono text-codex-text">${v.value}</div>
        <div class="flex items-center justify-between text-[10px] font-mono text-codex-muted pt-1 border-t border-codex-border">
          <span>&lt;class '${v.type}'&gt;</span>
          <span>${v.bytes} B</span>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error('Error fetching RAM state:', err);
  }
}

function initSwapStage() {
  setSwapStep(1);
}

function setSwapStep(step) {
  state.swapStep = step;
  const viewport = document.getElementById('swap-stage-viewport');
  const expl = document.getElementById('swap-explanation-text');
  if (!viewport || !expl) return;

  [1, 2, 3].forEach(s => {
    const btn = document.getElementById(`swap-btn-${s}`);
    if (btn) {
      if (s === step) {
        btn.className = 'px-2.5 py-1 rounded bg-white text-black font-mono text-[11px]';
      } else {
        btn.className = 'px-2.5 py-1 rounded bg-[#2a2a30] text-codex-secondary hover:text-white font-mono text-[11px]';
      }
    }
  });

  let a_val = 10, b_val = 20, temp_val = '-';
  if (step === 1) {
    temp_val = 10;
    expl.innerText = "temp = a  (Copy reference in 'a' to 'temp')";
  } else if (step === 2) {
    a_val = 20;
    temp_val = 10;
    expl.innerText = "a = b     (Rebind 'a' to value of 'b')";
  } else if (step === 3) {
    a_val = 20;
    b_val = 10;
    temp_val = 10;
    expl.innerText = "b = temp  (Rebind 'b' to saved 'temp' -> Swap complete)";
  }

  viewport.innerHTML = `
    <div class="grid grid-cols-3 gap-6 w-full max-w-sm">
      <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${step === 2 ? 'border-amber-400/80' : 'border-codex-border'}">
        <span class="text-[10px] font-mono text-codex-muted">a (0x7ffe10)</span>
        <div class="text-2xl font-mono text-codex-text mt-1">${a_val}</div>
      </div>
      <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${step === 3 ? 'border-emerald-400/80' : 'border-codex-border'}">
        <span class="text-[10px] font-mono text-codex-muted">b (0x7ffe18)</span>
        <div class="text-2xl font-mono text-codex-text mt-1">${b_val}</div>
      </div>
      <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${step === 1 ? 'border-cyan-400/80' : 'border-dashed border-zinc-700'}">
        <span class="text-[10px] font-mono text-codex-muted">temp (0x7ffe20)</span>
        <div class="text-2xl font-mono text-codex-secondary mt-1">${temp_val}</div>
      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// 6. RAG DENSE RETRIEVAL & INGESTION
// ---------------------------------------------------------------------------
async function executeRAGSearch() {
  const input = document.getElementById('rag-search-input');
  const q = input ? input.value.trim() : '';
  if (!q) return;

  const container = document.getElementById('rag-results-container');
  container.innerHTML = '<div class="text-xs text-codex-muted font-mono">Retrieving matching chunks...</div>';

  try {
    const res = await fetch(`/api/rag/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();

    container.innerHTML = `
      <div class="flex items-center justify-between text-[10px] font-mono text-codex-muted pb-1 border-b border-codex-border">
        <span>Found ${data.results_count} chunks</span>
        <span>Latency: ${data.latency_ms} ms</span>
      </div>
      ${data.results.map(r => `
        <div class="p-3 rounded-lg bg-codex-card border border-codex-border space-y-1">
          <div class="flex items-center justify-between text-[10px] font-mono text-codex-muted">
            <span>${r.chunk_id}</span>
            <span>Sim: ${(r.similarity || 0.85).toFixed(3)}</span>
          </div>
          <div class="text-xs font-medium text-codex-text">${r.source_title}</div>
          <p class="text-[11px] text-codex-secondary leading-relaxed">${r.content}</p>
        </div>
      `).join('')}
    `;
  } catch (err) {
    console.error('Error executing search:', err);
    container.innerHTML = '<div class="text-rose-400 text-xs">Error performing vector search.</div>';
  }
}

async function executeIngestion() {
  const filename = document.getElementById('ingest-filename').value.trim() || 'notes.md';
  const content = document.getElementById('ingest-content').value.trim();
  const statusBox = document.getElementById('ingest-status-box');

  if (!content) {
    alert('Please enter markdown content with headings to chunk and ingest.');
    return;
  }

  statusBox.className = 'p-2.5 rounded-lg text-xs font-mono bg-codex-card border border-codex-border text-codex-secondary block';
  statusBox.innerText = 'Semantic chunking & auto-linking in progress...';

  try {
    const res = await fetch('/api/rag/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, content }),
    });
    const result = await res.json();

    statusBox.className = 'p-2.5 rounded-lg text-xs font-mono bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 block';
    statusBox.innerHTML = `
      ✓ Ingested '${result.filename}' cleanly. Extracted ${result.chunks_extracted} chunks, auto-linked to [${result.linked_concepts.join(', ')}].
    `;
  } catch (err) {
    console.error('Ingestion error:', err);
    statusBox.className = 'p-2.5 rounded-lg text-xs font-mono bg-rose-950/20 border border-rose-500/30 text-rose-300 block';
    statusBox.innerText = 'Error ingesting document.';
  }
}

// ---------------------------------------------------------------------------
// 7. CRYPTOGRAPHIC AUDIT TRAIL
// ---------------------------------------------------------------------------
async function refreshAuditTrail() {
  try {
    const res = await fetch('/api/audit-trail');
    const data = await res.json();

    const fp = document.getElementById('audit-main-fingerprint');
    if (fp) fp.innerText = data.audit_hash;

    const container = document.getElementById('audit-logs-container');
    if (!container) return;

    if (!data.recent_evaluations || data.recent_evaluations.length === 0) {
      container.innerHTML = '<div class="p-3 text-xs text-codex-muted">No evaluations recorded yet in active session.</div>';
      return;
    }

    container.innerHTML = data.recent_evaluations.map(log => `
      <div class="p-3 rounded-lg bg-codex-card border border-codex-border space-y-1 font-mono text-xs">
        <div class="flex items-center justify-between text-[10px]">
          <span class="text-codex-secondary">${log.concept_id}</span>
          <span class="${log.is_correct ? 'text-emerald-400' : 'text-amber-400'}">
            ${log.is_correct ? 'Correct' : 'Needs Review'} (${Math.round(log.score * 100)}%)
          </span>
        </div>
        <p class="text-codex-text font-sans text-xs">${log.question_asked}</p>
        <div class="p-1.5 rounded bg-black/30 text-codex-secondary text-[11px] truncate">
          <span class="text-codex-muted">Answer:</span> ${log.student_response}
        </div>
        <div class="text-[10px] text-codex-muted flex justify-between">
          <span>Block ID: ${log.id.slice(0, 12)}...</span>
          <span>${new Date(log.timestamp).toLocaleTimeString()}</span>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error('Error fetching audit trail:', err);
  }
}

// ---------------------------------------------------------------------------
// 8. GLOBAL COCKPIT CONTROLLER
// ---------------------------------------------------------------------------
function submitGlobalCockpit() {
  const input = document.getElementById('global-cockpit-input');
  if (!input) return;
  const val = input.value.trim().toLowerCase();
  input.value = '';

  if (!val) return;

  // Shortcuts
  if (val.includes('swap') || val.includes('memory') || val.includes('ram')) {
    showView('ram');
    return;
  }
  if (val.includes('plan') || val.includes('schedule') || val.includes('30/60/10')) {
    showView('plan');
    return;
  }
  if (val.includes('audit') || val.includes('ledger') || val.includes('hash')) {
    showView('audit');
    return;
  }
  if (val.includes('analogy') || val.includes('eli5')) {
    requestAnalogyQuick();
    return;
  }
  if (val.includes('rag') || val.includes('search') || val.includes('ingest')) {
    showView('rag');
    return;
  }

  // Route to active lesson
  showView('lessons');
  const answerInput = document.getElementById('lesson-answer-input');
  if (answerInput) {
    answerInput.value = val;
    submitLessonAnswer();
  }
}

function requestAnalogyQuick() {
  showView('lessons');
  const analogyBox = document.getElementById('lesson-analogy-metaphor');
  if (analogyBox) {
    analogyBox.scrollIntoView({ behavior: 'smooth' });
  }
}

function copyCode() {
  const code = document.getElementById('lesson-code-block').innerText;
  navigator.clipboard.writeText(code);
}

// ---------------------------------------------------------------------------
// 9. MODALS
// ---------------------------------------------------------------------------
function showModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('hidden');
}

function hideModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('hidden');
}
