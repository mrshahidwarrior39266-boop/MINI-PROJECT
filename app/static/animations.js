/**
 * Codex Tutor — Concept Animation Engine
 * Minimalist, precision-engineered visualizers for all 8 Python curriculum concepts.
 */

class ConceptAnimationEngine {
  constructor() {
    this.currentConcept = "py.variables";
    this.step = 1;
    this.totalSteps = 3;
    this.isPlaying = false;
    this.timer = null;
    this.speedMs = 1800;
  }

  setConcept(conceptId) {
    this.currentConcept = conceptId;
    this.step = 1;
    this.stop();
    this.render();
  }

  nextStep() {
    if (this.step < this.totalSteps) {
      this.step++;
    } else {
      this.step = 1;
    }
    this.render();
  }

  prevStep() {
    if (this.step > 1) {
      this.step--;
    } else {
      this.step = this.totalSteps;
    }
    this.render();
  }

  reset() {
    this.step = 1;
    this.stop();
    this.render();
  }

  togglePlay() {
    if (this.isPlaying) {
      this.stop();
    } else {
      this.play();
    }
  }

  play() {
    this.isPlaying = true;
    const btn = document.getElementById("anim-play-btn");
    if (btn) btn.innerText = "Pause";
    this.timer = setInterval(() => {
      this.nextStep();
    }, this.speedMs);
  }

  stop() {
    this.isPlaying = false;
    const btn = document.getElementById("anim-play-btn");
    if (btn) btn.innerText = "Play";
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  render() {
    const container = document.getElementById("animation-stage-viewport");
    const badge = document.getElementById("anim-step-badge");
    const expl = document.getElementById("anim-step-explanation");
    const title = document.getElementById("anim-stage-title");

    if (!container) return;

    switch (this.currentConcept) {
      case "py.variables":
        this.renderVariables(container, badge, expl, title);
        break;
      case "py.data_types":
        this.renderDataTypes(container, badge, expl, title);
        break;
      case "py.operators_expressions":
        this.renderOperators(container, badge, expl, title);
        break;
      case "py.conditionals":
        this.renderConditionals(container, badge, expl, title);
        break;
      case "py.lists_sequences":
        this.renderLists(container, badge, expl, title);
        break;
      case "py.for_loops":
        this.renderForLoops(container, badge, expl, title);
        break;
      case "py.while_loops":
        this.renderWhileLoops(container, badge, expl, title);
        break;
      case "py.functions":
        this.renderFunctions(container, badge, expl, title);
        break;
      default:
        this.renderVariables(container, badge, expl, title);
    }
  }

  /* -------------------------------------------------------------------------
   * 1. py.variables: Memory Box & 3-Step Swap Movie
   * ------------------------------------------------------------------------- */
  renderVariables(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Memory Allocation & Swap Simulation";
    badge.innerText = `Step ${this.step} of 3`;

    let a_val = 10, b_val = 20, temp_val = "—";
    let code_snippet = "";

    if (this.step === 1) {
      temp_val = 10;
      code_snippet = "temp = a  # Copy reference in 'a' to holding box 'temp'";
      expl.innerText = "Step 1: 'temp' securely stores reference 10 from 'a'.";
    } else if (this.step === 2) {
      a_val = 20;
      temp_val = 10;
      code_snippet = "a = b     # Rebind label 'a' to reference of 'b'";
      expl.innerText = "Step 2: 'a' safely receives 20; old value safe in 'temp'.";
    } else if (this.step === 3) {
      a_val = 20;
      b_val = 10;
      temp_val = 10;
      code_snippet = "b = temp  # Rebind 'b' to reference in 'temp'";
      expl.innerText = "Step 3: 'b' receives 10 from 'temp'. Swap complete (zero loss).";
    }

    container.innerHTML = `
      <div class="flex flex-col items-center justify-between w-full h-full py-1">
        <div class="px-3 py-1 rounded bg-[#18181c] border border-codex-border font-mono text-xs text-codex-text">
          ${code_snippet}
        </div>

        <div class="grid grid-cols-3 gap-6 w-full max-w-md">
          <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${this.step === 2 ? 'border-amber-400/80' : 'border-codex-border'} transition-all">
            <span class="text-[10px] font-mono text-codex-muted">a (0x7ffe10)</span>
            <div class="text-2xl font-mono text-codex-text mt-1.5">${a_val}</div>
            <span class="text-[10px] text-codex-muted mt-1 font-mono">28 B</span>
          </div>

          <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${this.step === 3 ? 'border-emerald-400/80' : 'border-codex-border'} transition-all">
            <span class="text-[10px] font-mono text-codex-muted">b (0x7ffe18)</span>
            <div class="text-2xl font-mono text-codex-text mt-1.5">${b_val}</div>
            <span class="text-[10px] text-codex-muted mt-1 font-mono">28 B</span>
          </div>

          <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border ${this.step === 1 ? 'border-cyan-400/80' : 'border-dashed border-zinc-700'} transition-all">
            <span class="text-[10px] font-mono text-codex-muted">temp (0x7ffe20)</span>
            <div class="text-2xl font-mono text-codex-secondary mt-1.5">${temp_val}</div>
            <span class="text-[10px] text-codex-muted mt-1 font-mono">Buffer</span>
          </div>
        </div>

        <div class="text-[11px] font-mono text-codex-muted">
          Invariant: Data integrity preserved via temporary pointer binding.
        </div>
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 2. py.data_types: Type Casting Transformer
   * ------------------------------------------------------------------------- */
  renderDataTypes(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Type Casting & Memory Representation";
    badge.innerText = `Step ${this.step} of 3`;

    let stageContent = "";
    if (this.step === 1) {
      expl.innerText = "Step 1: '100' is an immutable string tape; cannot add directly to integer 5.";
      stageContent = `
        <div class="flex items-center space-x-3 text-xs font-mono">
          <div class="p-3 bg-[#18181c] border border-codex-border rounded-lg text-center">
            <span class="text-codex-muted text-[10px]">&lt;class 'str'&gt;</span>
            <div class="text-base text-codex-text mt-0.5">'100'</div>
          </div>
          <span class="text-codex-muted">+</span>
          <div class="p-3 bg-[#18181c] border border-codex-border rounded-lg text-center">
            <span class="text-codex-muted text-[10px]">&lt;class 'int'&gt;</span>
            <div class="text-base text-codex-text mt-0.5">5</div>
          </div>
          <span class="text-codex-muted">➔</span>
          <div class="p-2.5 bg-rose-950/30 border border-rose-500/40 rounded-lg text-center text-rose-300">
            TypeError: can only concatenate str to str
          </div>
        </div>
      `;
    } else if (this.step === 2) {
      expl.innerText = "Step 2: String passes through explicit int('100') constructor.";
      stageContent = `
        <div class="flex items-center space-x-3 text-xs font-mono">
          <div class="p-3 bg-[#18181c] border border-codex-border rounded-lg text-center">
            <span class="text-codex-muted text-[10px]">&lt;class 'str'&gt;</span>
            <div class="text-base text-codex-text mt-0.5">'100'</div>
          </div>
          <span class="text-codex-muted">➔ [ int() ] ➔</span>
          <div class="p-3 bg-[#18181c] border border-emerald-400/80 rounded-lg text-center">
            <span class="text-emerald-400 text-[10px]">&lt;class 'int'&gt;</span>
            <div class="text-base text-white mt-0.5">100 (28 B)</div>
          </div>
        </div>
      `;
    } else if (this.step === 3) {
      expl.innerText = "Step 3: Arithmetic evaluates cleanly: 100 + 5 yields integer 105.";
      stageContent = `
        <div class="flex items-center space-x-3 text-xs font-mono">
          <div class="p-3 bg-[#18181c] border border-codex-border rounded-lg text-center">
            <span class="text-codex-muted text-[10px]">100 (int)</span>
          </div>
          <span class="text-codex-muted">+</span>
          <div class="p-3 bg-[#18181c] border border-codex-border rounded-lg text-center">
            <span class="text-codex-muted text-[10px]">5 (int)</span>
          </div>
          <span class="text-codex-muted">=</span>
          <div class="p-3 bg-[#18181c] border border-cyan-400/80 rounded-lg text-center">
            <span class="text-cyan-400 text-[10px]">Result</span>
            <div class="text-lg text-white font-medium">105</div>
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full">
        ${stageContent}
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 3. py.operators_expressions: Division Semantics
   * ------------------------------------------------------------------------- */
  renderOperators(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Division Mechanics: True (/) vs Floor (//)";
    badge.innerText = `Step ${this.step} of 3`;

    let stageContent = "";
    if (this.step === 1) {
      expl.innerText = "Step 1: '/' always creates a float: 7 / 2 evaluates to 3.5 (24 bytes).";
      stageContent = `
        <div class="p-4 bg-[#18181c] border border-codex-border rounded-xl text-center space-y-1 font-mono">
          <div class="text-[11px] text-codex-muted">EXPRESSION: 7 / 2</div>
          <div class="text-2xl text-codex-text">3.5</div>
          <div class="text-[10px] text-codex-secondary">&lt;class 'float'&gt; • IEEE 754</div>
        </div>
      `;
    } else if (this.step === 2) {
      expl.innerText = "Step 2: '//' performs floor division: 7 // 2 rounds down to integer 3.";
      stageContent = `
        <div class="p-4 bg-[#18181c] border border-codex-border rounded-xl text-center space-y-1 font-mono">
          <div class="text-[11px] text-codex-muted">EXPRESSION: 7 // 2</div>
          <div class="text-2xl text-emerald-400">3</div>
          <div class="text-[10px] text-codex-secondary">&lt;class 'int'&gt; • 28 Bytes</div>
        </div>
      `;
    } else if (this.step === 3) {
      expl.innerText = "Step 3: Negative floor: -7 // 2 evaluates to -4 (rounds toward negative infinity).";
      stageContent = `
        <div class="p-4 bg-[#18181c] border border-amber-500/40 rounded-xl text-center space-y-1.5 font-mono">
          <div class="text-[11px] text-amber-300">EXPRESSION: -7 // 2</div>
          <div class="text-2xl text-amber-400">-4</div>
          <div class="text-[11px] text-codex-secondary max-w-xs font-sans">
            -3.5 floored toward -∞ equals -4, not -3.
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full">
        ${stageContent}
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 4. py.conditionals: Short-Circuit Logic
   * ------------------------------------------------------------------------- */
  renderConditionals(container, badge, expl, title) {
    this.totalSteps = 2;
    title.innerText = "Branching & Short-Circuit Logic";
    badge.innerText = `Step ${this.step} of 2`;

    let stageContent = "";
    if (this.step === 1) {
      expl.innerText = "Step 1: If-Elif chain evaluates guards sequentially until first True matches.";
      stageContent = `
        <div class="w-full max-w-sm space-y-1.5 font-mono text-xs">
          <div class="p-2 rounded bg-[#18181c] border border-codex-border flex justify-between text-codex-muted">
            <span>if score &gt;= 90: (85 &gt;= 90 is False)</span>
            <span>Skipped</span>
          </div>
          <div class="p-2 rounded bg-[#1c2220] border border-emerald-500/40 flex justify-between text-emerald-300">
            <span>elif score &gt;= 80: (85 &gt;= 80 is True)</span>
            <span class="text-emerald-400 font-medium">grade = 'B'</span>
          </div>
          <div class="p-2 rounded bg-[#18181c] border border-codex-border flex justify-between text-codex-muted">
            <span>else:</span>
            <span>Bypassed</span>
          </div>
        </div>
      `;
    } else if (this.step === 2) {
      expl.innerText = "Step 2: Short-circuit guard: 'len([]) > 0 and (total / len)' safely halts before division.";
      stageContent = `
        <div class="p-3.5 bg-[#18181c] border border-codex-border rounded-xl text-center space-y-2 font-mono text-xs">
          <div class="text-codex-secondary">if len(items) &gt; 0 and (total / len(items)) &gt; 10:</div>
          <div class="flex items-center justify-center space-x-2 text-[11px]">
            <span class="px-2 py-0.5 bg-rose-950/40 border border-rose-500/30 text-rose-300 rounded">False</span>
            <span class="text-codex-muted">➔ Stops evaluation</span>
            <span class="px-2 py-0.5 bg-zinc-900 text-codex-muted line-through rounded">total / 0</span>
          </div>
          <p class="text-[11px] text-emerald-400 font-sans">ZeroDivisionError avoided via short-circuit evaluation.</p>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full">
        ${stageContent}
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 5. py.lists_sequences: Sequential Offsets & Slicing
   * ------------------------------------------------------------------------- */
  renderLists(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Array Indices & Slicing Window";
    badge.innerText = `Step ${this.step} of 3`;

    let highlightIndices = [0];
    if (this.step === 1) {
      expl.innerText = "Step 1: Zero-based indexing points to elements by base memory offset.";
      highlightIndices = [0];
    } else if (this.step === 2) {
      expl.innerText = "Step 2: Negative indices count backwards from the right ([-1] is the last item).";
      highlightIndices = [4];
    } else if (this.step === 3) {
      expl.innerText = "Step 3: Slice [1:4] extracts indices 1, 2, 3 (stop index 4 is excluded).";
      highlightIndices = [1, 2, 3];
    }

    const elements = [10, 20, 30, 40, 50];
    let boxes = elements.map((val, idx) => {
      const isHi = highlightIndices.includes(idx);
      return `
        <div class="flex flex-col items-center space-y-1">
          <span class="text-[10px] font-mono ${isHi ? 'text-white' : 'text-codex-muted'}">${idx}</span>
          <div class="w-12 h-12 rounded bg-[#18181c] border ${isHi ? 'border-white text-white' : 'border-codex-border text-codex-secondary'} flex items-center justify-center font-mono text-sm transition-all">
            ${val}
          </div>
        </div>
      `;
    }).join("");

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full space-y-3">
        <div class="flex items-center space-x-2">
          ${boxes}
        </div>
        <div class="text-[11px] font-mono text-codex-secondary">
          ${this.step === 3 ? "Slice Result: [20, 30, 40]" : "Base Address: 0x7ffe00"}
        </div>
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 6. py.for_loops: Iterator Protocol
   * ------------------------------------------------------------------------- */
  renderForLoops(container, badge, expl, title) {
    this.totalSteps = 4;
    title.innerText = "Iterator Protocol & Accumulator";
    badge.innerText = `Step ${this.step} of 4`;

    const items = [12, 45, 8, 20];
    const idx = this.step - 1;
    const currentItem = items[idx];
    const runningTotal = items.slice(0, this.step).reduce((a, b) => a + b, 0);

    expl.innerText = `Iteration ${this.step}: Loop pointer bound to ${currentItem}. Total = ${runningTotal}.`;

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full space-y-4">
        <div class="flex items-center space-x-2 text-xs font-mono">
          ${items.map((val, i) => `
            <span class="px-2.5 py-1 rounded ${i === idx ? 'bg-white text-black font-medium' : (i < idx ? 'bg-[#18181c] text-codex-muted line-through' : 'bg-[#18181c] text-codex-secondary')}">
              ${val}
            </span>
          `).join("")}
        </div>

        <div class="flex items-center space-x-4 text-xs font-mono">
          <div class="p-2.5 rounded bg-[#18181c] border border-codex-border text-center">
            <span class="text-[10px] text-codex-muted">ITEM</span>
            <div class="text-lg text-codex-text mt-0.5">${currentItem}</div>
          </div>
          <span class="text-codex-muted">+</span>
          <div class="p-2.5 rounded bg-[#18181c] border border-codex-border text-center">
            <span class="text-[10px] text-codex-muted">TOTAL</span>
            <div class="text-lg text-emerald-400 mt-0.5">${runningTotal}</div>
          </div>
        </div>
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 7. py.while_loops: Sentinel Loop Gate
   * ------------------------------------------------------------------------- */
  renderWhileLoops(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Sentinel Flag & Loop Termination";
    badge.innerText = `Step ${this.step} of 3`;

    let attempts = this.step;
    let auth = this.step === 3;

    expl.innerText = auth
      ? "Step 3: Sentinel condition evaluates to False. Loop exits deterministically."
      : `Step ${this.step}: Attempt ${attempts} of 3. Loop body executes.`;

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full space-y-3 font-mono text-xs">
        <div class="px-3 py-1 rounded bg-[#18181c] border border-codex-border text-codex-text">
          while not authenticated and attempts &lt; 3:
        </div>

        <div class="flex items-center space-x-4">
          <div class="p-3 bg-[#18181c] border border-codex-border rounded-lg text-center">
            <span class="text-[10px] text-codex-muted">ATTEMPTS</span>
            <div class="text-xl text-codex-text mt-0.5">${attempts} / 3</div>
          </div>

          <div class="p-3 bg-[#18181c] border ${auth ? 'border-emerald-400/80' : 'border-codex-border'} rounded-lg text-center">
            <span class="text-[10px] text-codex-muted">STATUS</span>
            <div class="text-xs ${auth ? 'text-emerald-400' : 'text-codex-secondary'} mt-1">
              ${auth ? 'Terminated' : 'Iterating'}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 8. py.functions: Call Stack Frame
   * ------------------------------------------------------------------------- */
  renderFunctions(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Call Stack Frame Allocation & Scope";
    badge.innerText = `Step ${this.step} of 3`;

    let stageContent = "";
    if (this.step === 1) {
      expl.innerText = "Step 1: Global Stack Frame allocates variables. Function defined in memory.";
      stageContent = `
        <div class="w-56 p-2.5 bg-[#18181c] border border-codex-border rounded-lg font-mono text-xs space-y-0.5">
          <div class="text-[10px] text-codex-muted">GLOBAL STACK FRAME</div>
          <div class="text-codex-text">order_total = 150.0</div>
          <div class="text-codex-muted text-[11px]">calculate_tax = &lt;func&gt;</div>
        </div>
      `;
    } else if (this.step === 2) {
      expl.innerText = "Step 2: Invocation pushes local frame: parameters bound, local scope isolated.";
      stageContent = `
        <div class="flex flex-col space-y-1.5 w-56 font-mono text-xs">
          <div class="p-2.5 bg-[#1e1e24] border border-white/20 rounded-lg space-y-0.5">
            <div class="text-[10px] text-cyan-400">FRAME: calculate_tax()</div>
            <div class="text-codex-secondary text-[11px]">subtotal = 150.0</div>
            <div class="text-emerald-400">tax_amount = 12.0 (Local)</div>
          </div>
          <div class="p-2 bg-[#18181c] border border-codex-border rounded-lg text-[10px] text-codex-muted">
            Global Frame (Suspended)
          </div>
        </div>
      `;
    } else if (this.step === 3) {
      expl.innerText = "Step 3: Return delivers 12.0 to caller. Local frame pops off memory and deallocates.";
      stageContent = `
        <div class="w-56 p-2.5 bg-[#18181c] border border-emerald-500/40 rounded-lg font-mono text-xs space-y-0.5">
          <div class="text-[10px] text-emerald-400">GLOBAL FRAME (RESUMED)</div>
          <div class="text-codex-text">tax = 12.0</div>
          <div class="text-[10px] text-codex-muted">Local frame deallocated</div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full">
        ${stageContent}
      </div>
    `;
  }
}

// Global Animation Engine Instance
const animEngine = new ConceptAnimationEngine();
