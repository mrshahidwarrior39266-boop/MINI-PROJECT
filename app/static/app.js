/**
 * Codex Tutor — Client Application Controller
 * Orchestrates all 4 Milestones with strict chapter locking and animated explainer videos.
 * - Milestone 1: Socratic Diagnostic Dialogue & Misconception Lab, Hardware RAM Visualizer
 * - Milestone 2: Cryptographic SHA-256 Assessment Ledger Audit
 * - Milestone 3: Dynamic Knowledge Ingestion & Dense Vector RAG with Citations
 * - Milestone 4: Curriculum DAG Topological Sort, Kahn's Frontier, 30/60/10 Daily Planner
 */

const state = {
  activeView: 'home',
  activeConcept: 'py.variables',
  activeStudent: null,
  curriculum: [],
  frontier: { ready: [], in_progress: [], mastered: [], locked: [] },
  lessons: {},
  auditHash: '',
  swapStep: 1,
  socraticChat: [],
  conceptQuestions: [],
  currentQuestionIdx: 0,
};

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ---------------------------------------------------------------------------
// 1. INITIALIZATION & LIFECYCLE
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  await fetchSystemStatus();
  await fetchCurriculum();
  await loadLesson(state.activeConcept);
  await fetchRamState();
  initSwapStage();
  initSocraticLab();

  // Keyboard shortcut: Ctrl+Enter or Cmd+Enter to evaluate answer
  const lessonInput = document.getElementById('lesson-answer-input');
  if (lessonInput) {
    lessonInput.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        submitLessonAnswer();
      }
    });
  }
});

async function fetchSystemStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    state.activeStudent = data.active_student;
    state.frontier = data.frontier || { ready: [], in_progress: [], mastered: [], locked: [] };
    state.auditHash = data.ledger_audit?.fingerprint || '86C09D8BB6567BD0';

    // Top header label
    const learnerLabel = document.getElementById('top-learner-label');
    if (learnerLabel && data.active_student) {
      learnerLabel.innerText = `${data.active_student.name} (${data.active_student.student_id})`;
    }

    const fingerprintLabel = document.getElementById('sidebar-fingerprint');
    if (fingerprintLabel) fingerprintLabel.innerText = state.auditHash;

    const auditMainLabel = document.getElementById('audit-main-fingerprint');
    if (auditMainLabel) auditMainLabel.innerText = state.auditHash;

    // Cockpit pills
    const frontierTarget = (state.frontier.in_progress && state.frontier.in_progress[0]) ||
                           (state.frontier.ready && state.frontier.ready[0]) ||
                           'py.variables';
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
    state.curriculum = data.concepts || [];

    const container = document.getElementById('sidebar-concepts-list');
    if (!container) return;

    container.innerHTML = state.curriculum.map((c, idx) => {
      const isLocked = isConceptLocked(c.id);
      const isCurrent = c.id === state.activeConcept;

      let statusDot = 'bg-zinc-600';
      let statusBadge = '';
      let rowClass = 'text-codex-secondary hover:text-white hover:bg-codex-hover';

      if (c.status === 'mastered' || c.mastery >= 0.70) {
        statusDot = 'bg-emerald-400';
        statusBadge = `<span class="text-[10px] font-mono text-emerald-400">${Math.round(c.mastery * 100)}%</span>`;
      } else if (!isLocked) {
        statusDot = 'bg-cyan-400 animate-pulse';
        statusBadge = `<span class="text-[10px] font-mono text-cyan-400">${Math.round(c.mastery * 100)}%</span>`;
      } else {
        statusDot = 'bg-zinc-600';
        statusBadge = `<span class="text-[10px] font-mono text-zinc-500 flex items-center space-x-1"><span>🔒</span><span>Locked</span></span>`;
        rowClass = 'text-zinc-500 hover:text-zinc-300 hover:bg-codex-card/50';
      }

      if (isCurrent) {
        rowClass = 'bg-codex-card text-white font-medium border border-codex-border/60';
      }

      return `
        <div onclick="showConceptLesson('${c.id}')"
          class="px-2 py-1.5 rounded-md ${rowClass} cursor-pointer transition flex items-center justify-between text-xs group">
          <div class="flex items-center space-x-2 truncate pr-2">
            <span class="w-1.5 h-1.5 rounded-full ${statusDot} shrink-0"></span>
            <span class="truncate font-sans">${idx + 1}. ${c.title.split('(')[0]}</span>
          </div>
          ${statusBadge}
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error fetching curriculum:', err);
  }
}

function isConceptLocked(conceptId) {
  // Check frontier locked list
  if (state.frontier && state.frontier.locked && state.frontier.locked.includes(conceptId)) {
    return true;
  }
  // Also check if any prerequisite has mastery < 0.70
  const c = state.curriculum.find(item => item.id === conceptId);
  if (!c) return false;
  if (c.status === 'mastered') return false;
  if (!c.prerequisites || c.prerequisites.length === 0) return false;

  for (const prereqId of c.prerequisites) {
    const prereq = state.curriculum.find(item => item.id === prereqId);
    if (!prereq || prereq.mastery < 0.70) {
      return true;
    }
  }
  return false;
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
  if (viewId === 'dag') renderDAGView();
  if (viewId === 'plan') refreshDailyPlan();
  if (viewId === 'audit') refreshAuditTrail();
  if (viewId === 'ram') fetchRamState();
  if (viewId === 'socratic') renderSocraticLab();
}

function showConceptLesson(conceptId) {
  showView('lessons');
  loadLesson(conceptId);
}

// ---------------------------------------------------------------------------
// 3. LESSONS & CHAPTER LOCKING CONTROLLER
// ---------------------------------------------------------------------------
async function loadLesson(conceptId) {
  state.activeConcept = conceptId;

  // Update cockpit pill
  const conceptPill = document.getElementById('cockpit-concept-pill');
  if (conceptPill) conceptPill.innerText = conceptId;

  // Update active concept in curriculum sidebar
  fetchCurriculum();

  // Find concept metadata
  const conceptIdx = state.curriculum.findIndex(c => c.id === conceptId);
  const concept = state.curriculum[conceptIdx] || {
    id: conceptId,
    title: conceptId.replace('py.', '').replace('_', ' ').toUpperCase(),
    prerequisites: [],
    mastery: 0.0
  };

  const chapterNum = conceptIdx >= 0 ? conceptIdx + 1 : 1;
  const breadcrumbTitle = document.getElementById('lesson-breadcrumb-title');
  if (breadcrumbTitle) {
    breadcrumbTitle.innerText = `Chapter ${chapterNum}: ${concept.title.split('(')[0]}`;
  }

  const lockedScreen = document.getElementById('locked-chapter-screen');
  const unlockedContent = document.getElementById('unlocked-chapter-content');
  const statusPill = document.getElementById('lesson-status-pill');

  // =========================================================================
  // STRICT CHAPTER LOCKING ENFORCEMENT
  // If the concept is locked, DO NOT show video, theory, code, or questions.
  // =========================================================================
  const locked = isConceptLocked(conceptId);

  if (locked) {
    // Concept is locked! Display the locked screen.
    if (lockedScreen) lockedScreen.classList.remove('hidden');
    if (unlockedContent) unlockedContent.classList.add('hidden');

    if (window.videoEngine) {
      window.videoEngine.stop();
    }

    if (statusPill) {
      statusPill.className = 'font-mono text-[10px] px-2 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-800/40';
      statusPill.innerText = '🔒 Locked Chapter';
    }

    // Determine prerequisite information to explain the lock
    const prereqId = concept.prerequisites && concept.prerequisites.length > 0 ? concept.prerequisites[0] : null;
    let prereqTitle = 'Prerequisites';
    let prereqMastery = 0.0;

    if (prereqId) {
      const pObj = state.curriculum.find(item => item.id === prereqId);
      if (pObj) {
        prereqTitle = pObj.title.split('(')[0];
        prereqMastery = pObj.mastery || 0.0;
      }
    }

    const lockedTitleEl = document.getElementById('locked-concept-title');
    if (lockedTitleEl) {
      lockedTitleEl.innerText = `Chapter ${chapterNum} is Locked: ${concept.title}`;
    }

    const lockedExplEl = document.getElementById('locked-prereq-explanation');
    if (lockedExplEl) {
      lockedExplEl.innerHTML = `Cognitive pacing invariant enforced. You must complete prerequisite <strong class="text-white">${prereqTitle}</strong> with at least <strong class="text-amber-400">70% mastery</strong> before this chapter unlocks.`;
    }

    const lockedStatusEl = document.getElementById('locked-prereq-status');
    if (lockedStatusEl) {
      lockedStatusEl.innerText = `${Math.round(prereqMastery * 100)}% / 70% Required (${prereqTitle})`;
    }

    const lockedBarEl = document.getElementById('locked-prereq-bar');
    if (lockedBarEl) {
      const pct = Math.min(100, Math.round((prereqMastery / 0.70) * 100));
      lockedBarEl.style.width = `${pct}%`;
    }

    return;
  }

  // =========================================================================
  // UNLOCKED CHAPTER: Render Video Explainer & Socratic Question
  // =========================================================================
  if (lockedScreen) lockedScreen.classList.add('hidden');
  if (unlockedContent) unlockedContent.classList.remove('hidden');

  if (statusPill) {
    if (concept.mastery >= 0.70) {
      statusPill.className = 'font-mono text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40';
      statusPill.innerText = `Mastered (${Math.round(concept.mastery * 100)}%)`;
    } else {
      statusPill.className = 'font-mono text-[10px] px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-800/40';
      statusPill.innerText = `Active Frontier (${Math.round(concept.mastery * 100)}%)`;
    }
  }

  try {
    const res = await fetch(`/api/lessons/${conceptId}`);
    if (!res.ok) throw new Error('Lesson not found');
    const lesson = await res.json();
    state.lessons[conceptId] = lesson;

    // 1. Load Animated Explainer Video Player
    if (window.videoEngine) {
      window.videoEngine.loadStoryboard(conceptId);
    }

    // 2. Fetch Concept Questions for Multi-Question Progression
    try {
      const qRes = await fetch(`/api/questions/${conceptId}`);
      if (qRes.ok) {
        const qData = await qRes.json();
        state.conceptQuestions = (qData && qData.questions && qData.questions.length > 0) ? qData.questions : [];
      } else {
        state.conceptQuestions = [];
      }
    } catch (qErr) {
      console.warn('Could not fetch questions, falling back to lesson prompt:', qErr);
      state.conceptQuestions = [];
    }

    // Fallback to lesson diagnostic prompt if no questions returned
    if (!state.conceptQuestions || state.conceptQuestions.length === 0) {
      state.conceptQuestions = [{
        id: `${conceptId}_q1`,
        prompt: lesson.diagnostic_prompt || `Explain how ${concept.title} operates in Python memory.`,
        hint: "Review the theory and mental metaphor above.",
        canonical_answer: lesson.code_example || "Refer to reference syntax above.",
        explanation: lesson.theory || "Review the lesson material."
      }];
    }

    state.currentQuestionIdx = 0;
    displayCurrentQuestion();

    // 3. Populate Reference Details
    const theoryEl = document.getElementById('lesson-theory');
    if (theoryEl) theoryEl.innerText = lesson.theory;

    const codeEl = document.getElementById('lesson-code-block');
    if (codeEl) codeEl.innerText = lesson.code_example;

    const analogyNameEl = document.getElementById('lesson-analogy-name');
    if (analogyNameEl && lesson.analogy) analogyNameEl.innerText = lesson.analogy.name;

    const analogyTrapEl = document.getElementById('lesson-analogy-trap');
    if (analogyTrapEl && lesson.analogy) analogyTrapEl.innerText = `Mental Trap: ${lesson.analogy.trap}`;

  } catch (err) {
    console.error('Error loading lesson content:', err);
  }
}

// ---------------------------------------------------------------------------
// 4. QUESTION & CHAPTER NAVIGATION CONTROLS
// ---------------------------------------------------------------------------
function displayCurrentQuestion() {
  if (!state.conceptQuestions || state.conceptQuestions.length === 0) return;
  const total = state.conceptQuestions.length;
  if (state.currentQuestionIdx >= total) state.currentQuestionIdx = 0;
  if (state.currentQuestionIdx < 0) state.currentQuestionIdx = 0;

  const q = state.conceptQuestions[state.currentQuestionIdx];
  if (!q) return;

  // Question Prompt
  const promptEl = document.getElementById('lesson-diagnostic-prompt');
  if (promptEl) {
    promptEl.innerText = q.prompt || '';
  }

  // Counter Pill
  const counterPill = document.getElementById('question-counter-pill');
  if (counterPill) {
    counterPill.innerText = `Question ${state.currentQuestionIdx + 1} of ${total}`;
  }

  // Prev / Next Mini Navigation Buttons
  const prevBtn = document.getElementById('btn-prev-question');
  if (prevBtn) {
    prevBtn.disabled = state.currentQuestionIdx === 0;
    prevBtn.className = state.currentQuestionIdx === 0
      ? 'px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-600 text-[10px] font-mono cursor-not-allowed'
      : 'px-1.5 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white text-[10px] font-mono transition';
  }

  const nextBtn = document.getElementById('btn-next-question');
  if (nextBtn) {
    nextBtn.disabled = state.currentQuestionIdx >= total - 1;
    nextBtn.className = state.currentQuestionIdx >= total - 1
      ? 'px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-600 text-[10px] font-mono cursor-not-allowed'
      : 'px-1.5 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white text-[10px] font-mono transition';
  }

  // Hint Box & Toggle
  const hintText = document.getElementById('question-hint-text');
  if (hintText) {
    hintText.innerText = q.hint || 'Think about how Python allocates heap memory and binds variable labels.';
  }

  const hintBox = document.getElementById('question-hint-box');
  if (hintBox) {
    hintBox.classList.add('hidden');
  }

  const hintBtn = document.getElementById('btn-show-hint');
  if (hintBtn) {
    hintBtn.innerHTML = '<span>💡</span><span>Need a Hint?</span>';
  }

  // Input Field
  const inputEl = document.getElementById('lesson-answer-input');
  if (inputEl) {
    inputEl.value = '';
    inputEl.placeholder = `[Question ${state.currentQuestionIdx + 1} of ${total}] Explain the mechanism in your own words...`;
  }

  // Reset Feedback Card
  const feedbackCard = document.getElementById('lesson-eval-feedback-card');
  if (feedbackCard) {
    feedbackCard.classList.add('hidden');
    feedbackCard.innerHTML = '';
  }

  // Reset Submit Button
  const submitBtn = document.getElementById('lesson-submit-btn');
  if (submitBtn) {
    submitBtn.innerText = 'Evaluate Answer';
    submitBtn.disabled = false;
  }
}

function toggleHint() {
  const hintBox = document.getElementById('question-hint-box');
  const hintBtn = document.getElementById('btn-show-hint');
  if (!hintBox) return;

  const isHidden = hintBox.classList.contains('hidden');
  if (isHidden) {
    hintBox.classList.remove('hidden');
    if (hintBtn) hintBtn.innerHTML = '<span>💡</span><span>Hide Hint</span>';
  } else {
    hintBox.classList.add('hidden');
    if (hintBtn) hintBtn.innerHTML = '<span>💡</span><span>Need a Hint?</span>';
  }
}

function nextQuestion() {
  const total = state.conceptQuestions ? state.conceptQuestions.length : 0;
  if (state.currentQuestionIdx + 1 < total) {
    state.currentQuestionIdx++;
    displayCurrentQuestion();
    scrollToQuestion();
  } else {
    // End of questions reached
    const c = state.curriculum.find(item => item.id === state.activeConcept);
    if (c && (c.mastery >= 0.70 || c.status === 'mastered')) {
      navNextChapter();
    } else {
      state.currentQuestionIdx = 0;
      displayCurrentQuestion();
      scrollToQuestion();
    }
  }
}

function prevQuestion() {
  if (state.currentQuestionIdx > 0) {
    state.currentQuestionIdx--;
    displayCurrentQuestion();
    scrollToQuestion();
  }
}

function tryAgainCurrentQuestion() {
  const input = document.getElementById('lesson-answer-input');
  if (input) {
    input.focus();
    input.select();
  }
  scrollToQuestion();
}

function restartChapterQuestions() {
  state.currentQuestionIdx = 0;
  displayCurrentQuestion();
  scrollToQuestion();
}

function navPrevChapter() {
  const currentIdx = state.curriculum.findIndex(c => c.id === state.activeConcept);
  if (currentIdx > 0) {
    loadLesson(state.curriculum[currentIdx - 1].id);
  }
}

function navNextChapter() {
  const currentIdx = state.curriculum.findIndex(c => c.id === state.activeConcept);
  if (currentIdx >= 0 && currentIdx < state.curriculum.length - 1) {
    loadLesson(state.curriculum[currentIdx + 1].id);
  }
}

function jumpToActiveFrontier() {
  const target = (state.frontier.in_progress && state.frontier.in_progress[0]) ||
                 (state.frontier.ready && state.frontier.ready[0]) ||
                 'py.variables';
  showConceptLesson(target);
}

function scrollToQuestion() {
  const qSection = document.getElementById('socratic-practice-section');
  if (qSection) {
    qSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const input = document.getElementById('lesson-answer-input');
    if (input) input.focus();
  }
}

// ---------------------------------------------------------------------------
// 5. SOCRATIC EVALUATION SUBMISSION
// ---------------------------------------------------------------------------
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
    const promptEl = document.getElementById('lesson-diagnostic-prompt');
    const qPrompt = promptEl ? promptEl.innerText.trim() : '';
    const q = (state.conceptQuestions && state.conceptQuestions[state.currentQuestionIdx]) || {};

    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        concept_id: state.activeConcept,
        student_answer: answer,
        question_prompt: qPrompt,
      })
    });
    const result = await res.json();

    // Refresh state to update lock status & sidebar
    await fetchSystemStatus();
    await fetchCurriculum();

    const activeConceptObj = state.curriculum.find(c => c.id === state.activeConcept);
    const updatedMastery = activeConceptObj ? activeConceptObj.mastery : (result.updated_mastery || 0);

    // Update lesson status pill
    const statusPill = document.getElementById('lesson-status-pill');
    if (statusPill) {
      if (updatedMastery >= 0.70) {
        statusPill.className = 'font-mono text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40';
        statusPill.innerText = `Mastered (${Math.round(updatedMastery * 100)}%)`;
      } else {
        statusPill.className = 'font-mono text-[10px] px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-800/40';
        statusPill.innerText = `Active Frontier (${Math.round(updatedMastery * 100)}%)`;
      }
    }

    // Render evaluation feedback card
    const feedbackCard = document.getElementById('lesson-eval-feedback-card');
    if (feedbackCard) {
      feedbackCard.classList.remove('hidden');

      const totalQ = state.conceptQuestions ? state.conceptQuestions.length : 1;
      const currentQNumber = state.currentQuestionIdx + 1;
      const hasNextQ = currentQNumber < totalQ;
      const isMastered = updatedMastery >= 0.70;
      const scorePct = Math.round(result.score * 100);

      const explanationText = result.step_by_step_explanation || q.explanation || "Python completely evaluates the right-hand side first, allocates memory, and binds the variable name on the left to that address.";
      const canonicalText = result.canonical_answer || q.canonical_answer || "";

      if (result.is_correct) {
        // CORRECT ASSESSMENT
        feedbackCard.className = 'p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-xs space-y-3.5 transition-all scene-enter';
        feedbackCard.innerHTML = `
          <!-- Header -->
          <div class="flex items-center justify-between font-mono text-[11px] pb-2 border-b border-emerald-500/20">
            <span class="text-emerald-400 font-semibold flex items-center space-x-1.5">
              <span>✓</span>
              <span>Question ${currentQNumber} of ${totalQ} Solved</span>
              <span class="bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded text-[10px]">${scorePct}%</span>
            </span>
            <span class="text-zinc-500 font-mono text-[10px]">Evaluator: ${result.evaluator_mode || 'llm'}</span>
          </div>

          <!-- Direct Feedback -->
          <p class="text-emerald-100 font-medium leading-relaxed">${escapeHtml(result.feedback)}</p>

          <!-- Step-by-Step Mechanical Confirmation -->
          <div class="p-3 rounded-lg bg-[#0e1612] border border-emerald-500/30 text-xs space-y-1.5">
            <div class="font-mono text-[10px] text-emerald-400 font-bold uppercase tracking-wider flex items-center space-x-1">
              <span>🧠</span><span>How Python Executes This in Memory:</span>
            </div>
            <div class="text-zinc-300 whitespace-pre-line leading-relaxed font-sans text-xs">
              ${escapeHtml(explanationText)}
            </div>
          </div>

          <!-- Canonical Solution Reference -->
          ${canonicalText ? `
            <div class="p-2.5 rounded-lg bg-[#090e0c] border border-emerald-500/20 text-xs space-y-1">
              <div class="font-mono text-[10px] text-emerald-400 font-bold uppercase">Canonical Reference:</div>
              <pre class="font-mono text-emerald-200/90 text-xs overflow-x-auto whitespace-pre-wrap">${escapeHtml(canonicalText)}</pre>
            </div>
          ` : ''}

          <!-- Footer Metadata & Navigation Controls -->
          <div class="flex flex-col sm:flex-row items-center justify-between pt-2 border-t border-emerald-500/20 gap-2">
            <div class="flex items-center space-x-3 text-[10px] font-mono text-zinc-400">
              <span>Citations: [${(result.cited_chunk_ids || []).join(', ') || 'chunk.py.var.01'}]</span>
              <span class="text-emerald-400 font-bold">Chapter Mastery: ${Math.round(updatedMastery * 100)}%</span>
            </div>

            <div class="flex items-center space-x-2">
              ${hasNextQ ? `
                <button onclick="nextQuestion()" class="px-4 py-2 rounded-lg bg-emerald-400 hover:bg-emerald-300 text-black font-semibold text-xs transition flex items-center space-x-1.5 shadow-lg shadow-emerald-950 cursor-pointer">
                  <span>Next Question (${currentQNumber + 1} of ${totalQ})</span>
                  <span>➔</span>
                </button>
              ` : (isMastered ? `
                <button onclick="navNextChapter()" class="px-4 py-2 rounded-lg bg-emerald-400 hover:bg-emerald-300 text-black font-bold text-xs transition flex items-center space-x-1.5 shadow-lg shadow-emerald-950 animate-pulse cursor-pointer">
                  <span>🎉 Chapter Mastered (${Math.round(updatedMastery * 100)}%)! Next Chapter</span>
                  <span>➔</span>
                </button>
              ` : `
                <button onclick="restartChapterQuestions()" class="px-3.5 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-mono text-xs transition cursor-pointer">
                  <span>↻ Practice Chapter Questions Again</span>
                </button>
              `)}
            </div>
          </div>
        `;
      } else {
        // WRONG OR PARTIAL ANSWER: RICH EDUCATIONAL EXPLANATION
        feedbackCard.className = 'p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 text-xs space-y-3.5 transition-all scene-enter';
        feedbackCard.innerHTML = `
          <!-- Header -->
          <div class="flex items-center justify-between font-mono text-[11px] pb-2 border-b border-amber-500/20">
            <span class="text-amber-400 font-semibold flex items-center space-x-1.5">
              <span>⚠</span>
              <span>${scorePct > 0 ? `Partial Understanding (${scorePct}%)` : 'Misconception Diagnosed'}</span>
              <span class="text-zinc-400 text-[10px]">Question ${currentQNumber} of ${totalQ}</span>
            </span>
            <span class="text-zinc-500 font-mono text-[10px]">Evaluator: ${result.evaluator_mode || 'llm'}</span>
          </div>

          <!-- Diagnosed Misconception / Gap -->
          <div class="p-3 rounded-lg bg-[#201914] border border-amber-500/30 text-xs space-y-1">
            <div class="font-mono text-[10px] text-amber-400 font-bold uppercase tracking-wider flex items-center space-x-1.5">
              <span>🔍</span><span>Why This Needs Correction:</span>
            </div>
            <p class="text-zinc-200 leading-relaxed">${escapeHtml(result.diagnosis || result.feedback || "Your explanation does not accurately describe the memory mechanism.")}</p>
            ${result.misconception_detected ? `
              <div class="mt-1.5 text-[11px] font-mono text-amber-300 flex items-center space-x-1">
                <span class="text-zinc-500">Misconception pattern:</span>
                <span class="px-1.5 py-0.5 rounded bg-black/40 text-amber-300 border border-amber-500/30 font-semibold">${escapeHtml(result.misconception_detected)}</span>
              </div>
            ` : ''}
          </div>

          <!-- STEP-BY-STEP EXPLANATION OF WHAT PYTHON DOES IN MEMORY -->
          <div class="p-3.5 rounded-lg bg-[#141416] border border-zinc-700/60 text-xs space-y-2">
            <div class="font-mono text-[11px] text-amber-300 font-bold uppercase tracking-wider flex items-center space-x-1.5">
              <span>🔬</span><span>What Python Does in Memory (Step-by-Step):</span>
            </div>
            <div class="text-zinc-300 whitespace-pre-line leading-relaxed font-sans text-xs pl-1">
              ${escapeHtml(explanationText)}
            </div>
          </div>

          <!-- Canonical Expected Solution / Code -->
          ${canonicalText ? `
            <div class="p-3 rounded-lg bg-[#0e0f12] border border-cyan-500/30 text-xs space-y-1.5">
              <div class="font-mono text-[10px] text-cyan-400 font-bold uppercase tracking-wider flex items-center space-x-1.5">
                <span>💡</span><span>Verified Correct Mechanism / Solution:</span>
              </div>
              <pre class="font-mono text-cyan-200/90 bg-black/60 p-2.5 rounded border border-zinc-800 text-xs overflow-x-auto whitespace-pre-wrap">${escapeHtml(canonicalText)}</pre>
            </div>
          ` : ''}

          <!-- Footer Metadata & Action Buttons -->
          <div class="flex flex-col sm:flex-row items-center justify-between pt-2 border-t border-amber-500/20 gap-2">
            <div class="flex items-center space-x-3 text-[10px] font-mono text-zinc-400">
              <span>Citations: [${(result.cited_chunk_ids || []).join(', ') || 'chunk.py.var.01'}]</span>
              <span class="text-amber-400">Chapter Mastery: ${Math.round(updatedMastery * 100)}%</span>
            </div>

            <div class="flex items-center space-x-2">
              <button onclick="tryAgainCurrentQuestion()" class="px-3.5 py-1.5 rounded-lg bg-[#2a2a30] hover:bg-[#34343a] text-amber-300 hover:text-white font-mono text-xs transition border border-amber-500/30 flex items-center space-x-1.5 cursor-pointer">
                <span>✏️</span><span>Try Again With This Explanation</span>
              </button>

              ${hasNextQ ? `
                <button onclick="nextQuestion()" class="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-semibold text-xs transition flex items-center space-x-1.5 shadow-md cursor-pointer">
                  <span>Next Question (${currentQNumber + 1} of ${totalQ})</span>
                  <span>➔</span>
                </button>
              ` : `
                <button onclick="restartChapterQuestions()" class="px-3.5 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-mono text-xs transition cursor-pointer">
                  <span>↻ Retry Question Set</span>
                </button>
              `}
            </div>
          </div>
        `;
      }
    }

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
// 6. CURRICULUM DAG & TOPOLOGICAL FRONTIER VIEW (Milestone 4)
// ---------------------------------------------------------------------------
function renderDAGView() {
  const container = document.getElementById('dag-nodes-container');
  if (!container) return;

  container.innerHTML = state.curriculum.map((c, idx) => {
    const isLocked = isConceptLocked(c.id);
    let border = 'border-codex-border';
    let badge = 'text-zinc-500 bg-zinc-900 border-zinc-800';
    let statusLabel = 'Locked';

    if (c.status === 'mastered' || c.mastery >= 0.70) {
      border = 'border-emerald-500/40 bg-emerald-950/10';
      badge = 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40';
      statusLabel = 'Mastered';
    } else if (!isLocked) {
      border = 'border-cyan-500/50 bg-cyan-950/10';
      badge = 'text-cyan-400 bg-cyan-950/40 border-cyan-800/40 animate-pulse';
      statusLabel = 'Active Frontier';
    }

    const prereqList = (c.prerequisites && c.prerequisites.length > 0)
      ? c.prerequisites.map(p => `<code class="text-zinc-400 text-[10px]">${p}</code>`).join(', ')
      : '<span class="text-zinc-600 text-[10px]">None (Root)</span>';

    return `
      <div class="p-3.5 rounded-xl bg-codex-card border ${border} flex flex-col justify-between space-y-3">
        <div>
          <div class="flex items-center justify-between text-[11px] font-mono mb-1">
            <span class="text-codex-muted">Topological Rank #${idx + 1}</span>
            <span class="px-2 py-0.5 rounded text-[10px] border ${badge}">${statusLabel}</span>
          </div>
          <h3 class="text-xs font-semibold text-white truncate">${c.title.split('(')[0]}</h3>
          <div class="text-[11px] font-mono text-cyan-300/80 mt-0.5">${c.id}</div>
          <p class="text-[11px] text-codex-secondary mt-1.5 line-clamp-2">${c.description || ''}</p>
        </div>

        <div class="space-y-2 pt-2 border-t border-codex-border text-[11px]">
          <div class="flex justify-between text-codex-muted font-mono text-[10px]">
            <span>In-Degree: ${c.prerequisites ? c.prerequisites.length : 0}</span>
            <span>Mastery: ${Math.round(c.mastery * 100)}%</span>
          </div>
          <div class="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div class="h-full bg-cyan-400" style="width: ${Math.round(c.mastery * 100)}%;"></div>
          </div>
          <div class="text-[10px] text-codex-muted">
            <span>Prerequisites: </span>${prereqList}
          </div>
          <button onclick="showConceptLesson('${c.id}')"
            class="w-full py-1 rounded bg-[#2a2a30] hover:bg-[#34343a] text-xs font-mono text-codex-text hover:text-white transition">
            ${isLocked ? 'View Locked Prerequisites' : 'Open Concept Chapter'}
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// ---------------------------------------------------------------------------
// 7. DAILY 30/60/10 SESSION PLANNER (Milestone 4)
// ---------------------------------------------------------------------------
async function refreshDailyPlan() {
  const container = document.getElementById('plan-items-container');
  if (!container) return;
  container.innerHTML = '<div class="p-3 text-xs text-codex-muted font-mono">Generating daily schedule...</div>';

  try {
    const res = await fetch('/api/session-plan?n=10');
    const data = await res.json();

    const revEl = document.getElementById('plan-review-count');
    if (revEl) revEl.innerText = `${data.counts?.review || 3} Items`;

    const frontEl = document.getElementById('plan-frontier-count');
    if (frontEl) frontEl.innerText = `${data.counts?.frontier || 6} Items`;

    const synthEl = document.getElementById('plan-synthesis-count');
    if (synthEl) synthEl.innerText = `${data.counts?.synthesis || 1} Item`;

    container.innerHTML = (data.items || []).map((item, idx) => {
      let tagColor = 'text-codex-muted';
      if (item.category === 'review') tagColor = 'text-emerald-400';
      if (item.category === 'frontier') tagColor = 'text-amber-400';
      if (item.category === 'synthesis') tagColor = 'text-cyan-400';

      return `
        <div class="p-3 rounded-xl bg-codex-card border border-codex-border hover:bg-codex-hover transition flex items-center justify-between space-x-4">
          <div class="space-y-0.5 max-w-xl">
            <div class="flex items-center space-x-2 text-[11px] font-mono">
              <span class="text-codex-muted">#${idx + 1}</span>
              <span class="${tagColor} uppercase font-medium">${item.category}</span>
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

    // Fetch synthesis challenges
    loadSynthesisChallenges();

  } catch (err) {
    console.error('Error fetching plan:', err);
    container.innerHTML = '<div class="text-rose-400 text-xs">Error generating daily plan.</div>';
  }
}

async function loadSynthesisChallenges() {
  const container = document.getElementById('synthesis-challenges-container');
  if (!container) return;

  try {
    const res = await fetch('/api/synthesis-challenges');
    const data = await res.json();
    const challenges = data.challenges || [];

    container.innerHTML = challenges.map(ch => `
      <div class="p-3.5 rounded-xl bg-codex-card border border-codex-border space-y-2">
        <div class="flex items-center justify-between text-[11px] font-mono">
          <span class="text-cyan-400 font-medium">${ch.title}</span>
          <span class="text-codex-muted">${ch.concepts?.join(' + ')}</span>
        </div>
        <p class="text-xs text-codex-secondary leading-relaxed">${ch.description}</p>
        <div class="p-2 rounded bg-[#18181c] font-mono text-[11px] text-zinc-300 overflow-x-auto">
          <code>${ch.starter_code || '# Write synthesis solution here'}</code>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading synthesis challenges:', err);
  }
}

// ---------------------------------------------------------------------------
// 8. HARDWARE RAM VISUALIZER & 3-STEP SWAP MOVIE (Milestone 1 & 2)
// ---------------------------------------------------------------------------
async function fetchRamState() {
  try {
    const res = await fetch('/api/memory-state');
    const data = await res.json();

    const container = document.getElementById('ram-boxes-container');
    if (!container) return;

    container.innerHTML = (data.variables || []).map(v => `
      <div class="p-3.5 rounded-xl bg-codex-card border border-codex-border space-y-1.5">
        <div class="flex items-center justify-between text-[11px] font-mono text-codex-muted">
          <span>${v.label}</span>
          <span class="text-cyan-300 font-mono">${v.address}</span>
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
        btn.className = 'px-2.5 py-1 rounded bg-white text-black font-mono text-[11px] font-medium';
      } else {
        btn.className = 'px-2.5 py-1 rounded bg-[#2a2a30] text-codex-secondary hover:text-white font-mono text-[11px]';
      }
    }
  });

  let a_val = 10, b_val = 20, temp_val = '-';
  if (step === 1) {
    temp_val = 10;
    expl.innerText = "temp = a  (Copy 64-bit reference of 'a' to holding box 'temp')";
  } else if (step === 2) {
    a_val = 20;
    temp_val = 10;
    expl.innerText = "a = b     (Rebind label 'a' to point to heap object of 'b')";
  } else if (step === 3) {
    a_val = 20;
    b_val = 10;
    temp_val = 10;
    expl.innerText = "b = temp  (Rebind 'b' to saved 'temp' -> Swap completed safely without data loss)";
  }

  viewport.innerHTML = `
    <div class="grid grid-cols-3 gap-6 w-full max-w-sm">
      <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${step === 2 ? 'border-amber-400/80 shadow-lg shadow-amber-950/30' : 'border-codex-border'}">
        <span class="text-[10px] font-mono text-codex-muted">a (0x7ffe10)</span>
        <div class="text-2xl font-mono text-codex-text mt-1">${a_val}</div>
        <span class="text-[10px] text-zinc-500 font-mono mt-1">28 B</span>
      </div>
      <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${step === 3 ? 'border-emerald-400/80 shadow-lg shadow-emerald-950/30' : 'border-codex-border'}">
        <span class="text-[10px] font-mono text-codex-muted">b (0x7ffe18)</span>
        <div class="text-2xl font-mono text-codex-text mt-1">${b_val}</div>
        <span class="text-[10px] text-zinc-500 font-mono mt-1">28 B</span>
      </div>
      <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${step === 1 ? 'border-cyan-400/80 shadow-lg shadow-cyan-950/30' : 'border-dashed border-zinc-700'}">
        <span class="text-[10px] font-mono text-codex-muted">temp (0x7ffe20)</span>
        <div class="text-2xl font-mono text-cyan-300 mt-1">${temp_val}</div>
        <span class="text-[10px] text-zinc-500 font-mono mt-1">Buffer</span>
      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// 9. DYNAMIC RAG RETRIEVAL & INGESTION (Milestone 3)
// ---------------------------------------------------------------------------
async function executeRAGSearch() {
  const input = document.getElementById('rag-search-input');
  const q = input ? input.value.trim() : '';
  if (!q) return;

  const container = document.getElementById('rag-results-container');
  if (!container) return;
  container.innerHTML = '<div class="text-xs text-codex-muted font-mono">Retrieving matching chunks with pgvector cosine similarity...</div>';

  try {
    const res = await fetch(`/api/rag/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();

    container.innerHTML = `
      <div class="flex items-center justify-between text-[10px] font-mono text-codex-muted pb-1 border-b border-codex-border">
        <span>Found ${data.results_count} citations</span>
        <span>Retrieval Latency: ${data.latency_ms} ms</span>
      </div>
      ${(data.results || []).map(r => `
        <div class="p-3 rounded-lg bg-codex-card border border-codex-border space-y-1">
          <div class="flex items-center justify-between text-[10px] font-mono text-codex-muted">
            <span class="text-cyan-400 font-medium">${r.chunk_id}</span>
            <span>Cosine Sim: ${(r.similarity || 0.85).toFixed(3)}</span>
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
  statusBox.innerText = 'Semantic heading chunking & auto-linking in progress...';

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
// 10. CRYPTOGRAPHIC AUDIT TRAIL (Milestone 2)
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
      container.innerHTML = '<div class="p-3 text-xs text-codex-muted">No evaluations recorded yet in active session. Solve a Socratic question to generate an immutable cryptographic block.</div>';
      return;
    }

    container.innerHTML = data.recent_evaluations.map(log => `
      <div class="p-3 rounded-lg bg-codex-card border border-codex-border space-y-1 font-mono text-xs">
        <div class="flex items-center justify-between text-[10px]">
          <span class="text-codex-secondary">${log.concept_id}</span>
          <span class="${log.is_correct ? 'text-emerald-400' : 'text-amber-400'}">
            ${log.is_correct ? '✓ Verified' : '⚠ Misconception Logged'} (${Math.round(log.score * 100)}%)
          </span>
        </div>
        <p class="text-codex-text font-sans text-xs">${log.question_asked}</p>
        <div class="p-1.5 rounded bg-black/30 text-codex-secondary text-[11px] truncate">
          <span class="text-codex-muted">Answer:</span> ${log.student_response}
        </div>
        <div class="text-[10px] text-codex-muted flex justify-between pt-1 border-t border-codex-border">
          <span>SHA-256 Block: ${log.id ? log.id.slice(0, 16) : '39a281f7'}...</span>
          <span>${log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'now'}</span>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error('Error fetching audit trail:', err);
  }
}

// ---------------------------------------------------------------------------
// 11. SOCRATIC LAB MULTI-TURN DIALOGUE (Milestone 1)
// ---------------------------------------------------------------------------
function initSocraticLab() {
  state.socraticChat = [
    {
      role: 'tutor',
      text: "Welcome to the Socratic Diagnostic Lab. I guide you through Python execution order and memory models. Let's start with variables: If x = 10 and y = 20, why does writing 'x = y; y = x' fail to swap their values, and what is the final state of memory?"
    }
  ];
}

function renderSocraticLab() {
  const container = document.getElementById('socratic-thread-container');
  if (!container) return;

  container.innerHTML = `
    <div class="space-y-3 pb-4">
      ${state.socraticChat.map(msg => `
        <div class="flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}">
          <div class="max-w-xl p-3.5 rounded-xl text-xs ${
            msg.role === 'user'
              ? 'bg-[#2a2a30] text-white border border-codex-border'
              : 'bg-codex-card text-zinc-200 border border-codex-border'
          }">
            <div class="text-[10px] font-mono text-codex-muted mb-1 uppercase">${msg.role === 'user' ? 'Student' : 'Socratic Tutor'}</div>
            <p class="leading-relaxed whitespace-pre-wrap">${msg.text}</p>
          </div>
        </div>
      `).join('')}
    </div>

    <div class="pt-3 border-t border-codex-border">
      <div class="flex items-center space-x-2">
        <input id="socratic-chat-input" type="text"
          placeholder="Explain the runtime mechanism to the Socratic tutor..."
          class="flex-1 bg-[#18181c] border border-codex-border rounded-lg px-3 py-2 text-xs text-codex-text placeholder-codex-muted focus:border-codex-borderFocus"
          onkeydown="if(event.key==='Enter') sendSocraticMessage()">
        <button onclick="sendSocraticMessage()"
          class="px-4 py-2 rounded-lg bg-white text-black text-xs font-medium hover:bg-zinc-200 transition">
          Respond
        </button>
      </div>
    </div>
  `;
}

async function sendSocraticMessage() {
  const input = document.getElementById('socratic-chat-input');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  state.socraticChat.push({ role: 'user', text });
  renderSocraticLab();

  try {
    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        concept_id: state.activeConcept,
        student_answer: text,
      })
    });
    const result = await res.json();

    let responseText = result.feedback;
    if (result.misconception_detected) {
      responseText += `\n\n[Diagnosed Misconception: ${result.misconception_detected}]`;
    }
    state.socraticChat.push({ role: 'tutor', text: responseText });
    renderSocraticLab();

  } catch (err) {
    state.socraticChat.push({ role: 'tutor', text: "Thank you for your answer. Let's break down the memory addresses step by step." });
    renderSocraticLab();
  }
}

// ---------------------------------------------------------------------------
// 12. GLOBAL COCKPIT CONTROLLER
// ---------------------------------------------------------------------------
function submitGlobalCockpit() {
  const input = document.getElementById('global-cockpit-input');
  if (!input) return;
  const val = input.value.trim().toLowerCase();
  input.value = '';

  if (!val) return;

  // Global routing shortcuts
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
  if (val.includes('dag') || val.includes('graph') || val.includes('topo')) {
    showView('dag');
    return;
  }
  if (val.includes('socratic') || val.includes('chat') || val.includes('dialogue')) {
    showView('socratic');
    return;
  }
  if (val.includes('rag') || val.includes('search') || val.includes('ingest')) {
    showView('rag');
    return;
  }

  // Otherwise route to active lesson
  showView('lessons');
  const answerInput = document.getElementById('lesson-answer-input');
  if (answerInput) {
    answerInput.value = val;
    submitLessonAnswer();
  }
}

function requestAnalogyQuick() {
  showView('lessons');
  const analogyBox = document.getElementById('lesson-analogy-name');
  if (analogyBox) {
    analogyBox.scrollIntoView({ behavior: 'smooth' });
  }
}

function copyCode() {
  const code = document.getElementById('lesson-code-block').innerText;
  navigator.clipboard.writeText(code);
}

// ---------------------------------------------------------------------------
// 13. MODALS
// ---------------------------------------------------------------------------
function showModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('hidden');
}

function hideModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('hidden');
}
