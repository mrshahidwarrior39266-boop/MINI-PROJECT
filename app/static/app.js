/**
 * ArchaLearn Codex Client Application:
 * Full state orchestration for the OpenAI Codex-inspired Intelligent Tutoring System.
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

    // Update top header
    const learnerLabel = document.getElementById('top-learner-label');
    if (learnerLabel) learnerLabel.innerText = `${data.active_student.name} (${data.active_student.student_id})`;

    const fingerprintLabel = document.getElementById('sidebar-fingerprint');
    if (fingerprintLabel) fingerprintLabel.innerText = `Hash: ${state.auditHash}`;

    const auditMainLabel = document.getElementById('audit-main-fingerprint');
    if (auditMainLabel) auditMainLabel.innerText = state.auditHash;

    // Update cockpit frontier pill
    const frontierTarget = data.frontier.ready[0] || data.frontier.in_progress[0] || 'py.operators_expressions';
    const phasePill = document.getElementById('cockpit-phase-pill');
    if (phasePill) phasePill.innerText = '60% Frontier Learning';

    const conceptPill = document.getElementById('cockpit-concept-pill');
    if (conceptPill) conceptPill.innerText = frontierTarget;

    const homeSub = document.getElementById('home-subtitle');
    if (homeSub) {
      homeSub.innerHTML = `Dual-Engine Socratic Tutor active • Frontier: <code class="text-amber-400 font-mono text-xs">${frontierTarget}</code>`;
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
      let badgeCol = 'bg-zinc-800 text-zinc-400';
      let borderCol = 'border-zinc-800';
      let statusText = `${Math.round(c.mastery * 100)}%`;

      if (c.status === 'mastered') {
        badgeCol = 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60';
        borderCol = 'border-zinc-800';
      } else if (c.status === 'ready') {
        badgeCol = 'bg-amber-950/80 text-amber-300 border border-amber-800/80 animate-pulse';
        borderCol = 'border-amber-500/40 bg-zinc-800/60';
        statusText = 'READY';
      } else if (c.status === 'in_progress') {
        badgeCol = 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/60';
        statusText = `${Math.round(c.mastery * 100)}%`;
      } else {
        badgeCol = 'bg-zinc-900 text-zinc-500';
        statusText = 'LOCKED';
      }

      return `
        <div onclick="showConceptLesson('${c.id}')"
          class="p-2.5 rounded-lg bg-zinc-900/60 border ${borderCol} hover:border-cyan-500/50 hover:bg-zinc-800/50 cursor-pointer transition flex items-center justify-between text-xs group">
          <div class="truncate pr-2">
            <span class="text-zinc-500 font-mono mr-1">${idx + 1}.</span>
            <span class="text-zinc-200 group-hover:text-white font-medium">${c.title.split('(')[0]}</span>
          </div>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded ${badgeCol} shrink-0">
            ${statusText}
          </span>
        </div>
      `;
    }).join('');

    const frontierLabel = document.getElementById('sidebar-frontier-label');
    if (frontierLabel && data.frontier_target) {
      frontierLabel.innerText = `next: ${data.frontier_target}`;
    }
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
    btn.classList.remove('bg-codex-panel', 'text-cyan-400', 'shadow-md', 'border', 'border-codex-border/60');
    btn.classList.add('text-zinc-400');
  });

  const activeBtn = document.getElementById(`nav-btn-${viewId}`);
  if (activeBtn) {
    activeBtn.classList.remove('text-zinc-400');
    activeBtn.classList.add('bg-codex-panel', 'text-cyan-400', 'shadow-md', 'border', 'border-codex-border/60');
  }

  // Auto-refresh data when landing on views
  if (viewId === 'plan') refreshDailyPlan();
  if (viewId === 'audit') refreshAuditTrail();
  if (viewId === 'ram') fetchRamState();
}

function showConceptLesson(conceptId) {
  showView('lessons');
  loadLesson(conceptId);
}

function toggleSidebar() {
  const sidebar = document.getElementById('curriculum-sidebar');
  if (sidebar) sidebar.classList.toggle('hidden');
}

// ---------------------------------------------------------------------------
// 3. LESSONS & CONCEPT ANIMATIONS CONTROLLER
// ---------------------------------------------------------------------------
async function loadLesson(conceptId) {
  state.activeConcept = conceptId;

  // Update active pill in horizontal tab strip
  const tabs = document.querySelectorAll('.lesson-nav-btn');
  tabs.forEach(t => {
    t.classList.remove('bg-zinc-800', 'text-white', 'border', 'border-zinc-700');
    t.classList.add('text-zinc-400');
  });
  const currentTab = document.getElementById(`lesson-tab-${conceptId}`);
  if (currentTab) {
    currentTab.classList.remove('text-zinc-400');
    currentTab.classList.add('bg-zinc-800', 'text-white', 'border', 'border-zinc-700');
  }

  // Update cockpit pill
  const conceptPill = document.getElementById('cockpit-concept-pill');
  if (conceptPill) conceptPill.innerText = conceptId;

  try {
    const res = await fetch(`/api/lessons/${conceptId}`);
    const lesson = await res.json();
    state.lessons[conceptId] = lesson;

    // Populate Left Column
    document.getElementById('lesson-id-badge').innerText = lesson.concept_id;
    document.getElementById('lesson-title').innerText = lesson.title;
    document.getElementById('lesson-tagline').innerText = lesson.tagline;
    document.getElementById('lesson-theory').innerText = lesson.theory;
    document.getElementById('lesson-code-block').innerText = lesson.code_example;

    // Physical Analogy
    document.getElementById('lesson-analogy-name').innerText = lesson.analogy.name;
    document.getElementById('lesson-analogy-metaphor').innerText = lesson.analogy.metaphor;
    document.getElementById('lesson-analogy-trap').innerText = `⚠️ Mental Trap: ${lesson.analogy.trap}`;

    // Misconceptions
    const miscList = document.getElementById('lesson-misconceptions-list');
    miscList.innerHTML = lesson.misconceptions.map(m => `
      <div class="p-2.5 rounded-lg bg-zinc-900 border border-zinc-800">
        <div class="font-semibold text-rose-300 font-mono">${m.name}</div>
        <div class="text-zinc-400 mt-0.5"><span class="text-zinc-500">Trap:</span> ${m.mistake}</div>
        <div class="text-emerald-400 mt-1"><span class="text-emerald-500">Correction:</span> ${m.correction}</div>
      </div>
    `).join('');

    // Socratic Diagnostic Prompt
    document.getElementById('lesson-diagnostic-prompt').innerText = lesson.diagnostic_prompt;

    // Clear previous feedback and answer input
    document.getElementById('lesson-answer-input').value = '';
    const feedbackCard = document.getElementById('lesson-eval-feedback-card');
    feedbackCard.classList.add('hidden');

    // Trigger Dedicated Interactive Animation
    animEngine.setConcept(conceptId);

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
      ? 'p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/60 space-y-2 text-xs transition-all'
      : 'p-4 rounded-xl bg-amber-950/40 border border-amber-500/60 space-y-2 text-xs transition-all';

    feedbackCard.innerHTML = `
      <div class="flex items-center justify-between font-mono">
        <span class="${isCorrect ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}">
          ${isCorrect ? '✓ ASSESSMENT: CORRECT' : '⚡ ASSESSMENT: NEEDS REFINEMENT'} (Score: ${Math.round(result.score * 100)}%)
        </span>
        <span class="text-[10px] text-zinc-400">Mode: ${result.evaluator_mode}</span>
      </div>
      <p class="text-zinc-200 leading-relaxed">${result.feedback}</p>
      ${result.misconception_detected ? `
        <div class="text-[11px] font-mono text-rose-400 bg-rose-950/50 p-2 rounded border border-rose-800/60">
          ⚠️ Misconception Identified: ${result.misconception_detected}
        </div>
      ` : ''}
      <div class="flex items-center justify-between pt-1 border-t border-zinc-800/60 text-[11px] font-mono text-zinc-400">
        <span>Citations: [${(result.cited_chunk_ids || []).join(', ') || 'verified'}]</span>
        <span class="text-cyan-400">Updated Mastery: ${Math.round(result.updated_mastery * 100)}%</span>
      </div>
    `;

    // Also add to Socratic dialogue stream
    addSocraticMessage('user', answer);
    addSocraticMessage('tutor', result.feedback, result.cited_chunk_ids, isCorrect, result.score);

    // Refresh curriculum to reflect new mastery
    await fetchCurriculum();
    await fetchSystemStatus();

  } catch (err) {
    console.error('Error evaluating answer:', err);
  } finally {
    if (submitBtn) {
      submitBtn.innerText = 'Evaluate Response ↵';
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
  container.innerHTML = '<div class="p-4 rounded-xl bg-codex-panel border border-codex-border text-xs text-zinc-400 animate-pulse">Calculating optimal 30/60/10 schedule...</div>';

  try {
    const res = await fetch('/api/session-plan?n=10');
    const data = await res.json();

    document.getElementById('plan-review-count').innerText = `${data.counts.review} Items`;
    document.getElementById('plan-frontier-count').innerText = `${data.counts.frontier} Items`;
    document.getElementById('plan-synthesis-count').innerText = `${data.counts.synthesis} Item`;

    container.innerHTML = data.items.map((item, idx) => {
      let badgeCol = 'bg-zinc-800 text-zinc-400';
      if (item.category === 'review') badgeCol = 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60';
      if (item.category === 'frontier') badgeCol = 'bg-amber-950/80 text-amber-300 border border-amber-800/60';
      if (item.category === 'synthesis') badgeCol = 'bg-indigo-950/80 text-indigo-300 border border-indigo-800/60';

      return `
        <div class="p-4 rounded-xl bg-codex-panel border border-codex-border hover:border-zinc-600 transition flex items-center justify-between space-x-4">
          <div class="space-y-1 max-w-xl">
            <div class="flex items-center space-x-2">
              <span class="text-xs font-mono text-zinc-500">#${idx + 1}</span>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded uppercase ${badgeCol}">${item.category}</span>
              <span class="text-xs font-mono text-cyan-400">${item.concept_id}</span>
            </div>
            <p class="text-xs text-zinc-200 line-clamp-2">${item.prompt}</p>
          </div>
          <button onclick="showConceptLesson('${item.concept_id}')"
            class="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-zinc-200 shrink-0 transition">
            Launch Drill ➔
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
      <div class="p-4 rounded-xl bg-codex-panel border border-codex-border space-y-2">
        <div class="flex items-center justify-between text-[11px] font-mono text-zinc-400">
          <span>LABEL: ${v.label}</span>
          <span class="text-cyan-400">${v.address}</span>
        </div>
        <div class="text-2xl font-bold font-mono text-white">${v.value}</div>
        <div class="flex items-center justify-between text-[10px] font-mono text-zinc-500 pt-1 border-t border-zinc-800">
          <span>&lt;class '${v.type}'&gt;</span>
          <span>${v.bytes} Bytes</span>
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

  // Update button active state
  [1, 2, 3].forEach(s => {
    const btn = document.getElementById(`swap-btn-${s}`);
    if (btn) {
      if (s === step) {
        btn.className = 'px-3.5 py-1.5 rounded-lg bg-cyan-600 text-white font-mono';
      } else {
        btn.className = 'px-3.5 py-1.5 rounded-lg bg-zinc-800 text-zinc-300 hover:text-white font-mono';
      }
    }
  });

  let a_val = 10, b_val = 20, temp_val = '(empty)';
  if (step === 1) {
    temp_val = 10;
    expl.innerText = "Step 1: temp = a  (Copy reference in 'a' into holding box 'temp')";
  } else if (step === 2) {
    a_val = 20;
    temp_val = 10;
    expl.innerText = "Step 2: a = b     (Safely rebind 'a' to address of 'b')";
  } else if (step === 3) {
    a_val = 20;
    b_val = 10;
    temp_val = 10;
    expl.innerText = "Step 3: b = temp  (Rebind 'b' to reference in 'temp' -> SWAP COMPLETE)";
  }

  viewport.innerHTML = `
    <div class="grid grid-cols-3 gap-6 w-full max-w-md">
      <div class="flex flex-col items-center p-3 rounded-xl bg-zinc-900 border ${step === 2 ? 'border-amber-400' : 'border-zinc-700'}">
        <span class="text-[10px] font-mono text-zinc-400">a (0x7ffe10)</span>
        <div class="text-3xl font-mono font-bold text-cyan-400 mt-2">${a_val}</div>
      </div>
      <div class="flex flex-col items-center p-3 rounded-xl bg-zinc-900 border ${step === 3 ? 'border-emerald-400' : 'border-zinc-700'}">
        <span class="text-[10px] font-mono text-zinc-400">b (0x7ffe18)</span>
        <div class="text-3xl font-mono font-bold text-emerald-400 mt-2">${b_val}</div>
      </div>
      <div class="flex flex-col items-center p-3 rounded-xl bg-zinc-900 border ${step === 1 ? 'border-cyan-400' : 'border-dashed border-zinc-700'}">
        <span class="text-[10px] font-mono text-zinc-400">temp (0x7ffe20)</span>
        <div class="text-2xl font-mono font-bold text-amber-400 mt-2">${temp_val}</div>
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
  container.innerHTML = '<div class="text-xs text-zinc-400 animate-pulse">Running cosine vector retrieval...</div>';

  try {
    const res = await fetch(`/api/rag/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();

    container.innerHTML = `
      <div class="flex items-center justify-between text-[11px] font-mono text-zinc-400 pb-1 border-b border-zinc-800">
        <span>Found ${data.results_count} matching chunks</span>
        <span class="text-emerald-400">Latency: ${data.latency_ms} ms</span>
      </div>
      ${data.results.map(r => `
        <div class="p-3 rounded-xl bg-zinc-900/90 border border-zinc-800 space-y-1">
          <div class="flex items-center justify-between text-[10px] font-mono">
            <span class="text-cyan-400">${r.chunk_id}</span>
            <span class="text-amber-300">Sim: ${(r.similarity || 0.85).toFixed(4)}</span>
          </div>
          <div class="text-xs font-semibold text-white">${r.source_title}</div>
          <p class="text-[11px] text-zinc-300 leading-relaxed">${r.content}</p>
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

  statusBox.className = 'p-3 rounded-lg text-xs font-mono bg-zinc-900 border border-zinc-700 text-zinc-300 block';
  statusBox.innerText = 'Semantic chunking & auto-linking to DAG in progress...';

  try {
    const res = await fetch('/api/rag/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, content }),
    });
    const result = await res.json();

    statusBox.className = 'p-3 rounded-lg text-xs font-mono bg-emerald-950/60 border border-emerald-500/60 text-emerald-300 block';
    statusBox.innerHTML = `
      ✓ Ingested '${result.filename}' cleanly!
      <br>• Extracted ${result.chunks_extracted} semantic chunks.
      <br>• Auto-linked to concepts: [${result.linked_concepts.join(', ')}].
    `;
  } catch (err) {
    console.error('Ingestion error:', err);
    statusBox.className = 'p-3 rounded-lg text-xs font-mono bg-rose-950/60 border border-rose-500/60 text-rose-300 block';
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
      container.innerHTML = '<div class="p-4 rounded-xl bg-codex-panel border border-codex-border text-xs text-zinc-500">No evaluations recorded yet in active session.</div>';
      return;
    }

    container.innerHTML = data.recent_evaluations.map(log => `
      <div class="p-3.5 rounded-xl bg-codex-panel border border-codex-border space-y-1.5 font-mono text-xs">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-cyan-400">${log.concept_id}</span>
          <span class="${log.is_correct ? 'text-emerald-400' : 'text-rose-400'}">
            ${log.is_correct ? 'CORRECT' : 'INCORRECT'} (${Math.round(log.score * 100)}%)
          </span>
        </div>
        <p class="text-zinc-300 font-sans text-xs">${log.question_asked}</p>
        <div class="p-2 rounded bg-black/40 text-zinc-400 text-[11px] truncate">
          <span class="text-zinc-500">Student:</span> ${log.student_response}
        </div>
        <div class="text-[10px] text-zinc-500 flex justify-between">
          <span>Block ID: ${log.id.slice(0, 16)}...</span>
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

  // Command Shortcuts
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

  // Otherwise, route as an answer to the active lesson
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
  alert('Code copied to clipboard!');
}

function addSocraticMessage(sender, text, citations = [], isCorrect = null, score = null) {
  const container = document.getElementById('socratic-thread-container');
  if (!container) return;

  const isUser = sender === 'user';
  const msgEl = document.createElement('div');
  msgEl.className = isUser ? 'flex justify-end' : 'flex justify-start';

  msgEl.innerHTML = `
    <div class="max-w-lg p-4 rounded-2xl ${isUser ? 'bg-cyan-950/40 border border-cyan-800/60 text-cyan-100' : 'bg-codex-panel border border-codex-border text-zinc-200'} space-y-1.5 text-xs">
      <div class="text-[10px] font-mono ${isUser ? 'text-cyan-400' : 'text-amber-400'} font-bold">
        ${isUser ? '👤 You (Learner)' : '🧠 Socratic Tutor'}
      </div>
      <p class="leading-relaxed font-sans">${text}</p>
      ${citations && citations.length > 0 ? `
        <div class="text-[10px] font-mono text-cyan-400 pt-1 border-t border-zinc-800/60">
          📚 Source Chunk Citations: [${citations.join(', ')}]
        </div>
      ` : ''}
    </div>
  `;
  container.appendChild(msgEl);
  msgEl.scrollIntoView({ behavior: 'smooth' });
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
