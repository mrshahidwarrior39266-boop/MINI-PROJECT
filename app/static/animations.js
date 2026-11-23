/**
 * ArchaLearn Codex Animation Engine:
 * Dedicated visual state machines and interactive step-by-step animations
 * for all 8 Python concepts in the curriculum.
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
    if (btn) btn.innerHTML = "⏸ Pause";
    this.timer = setInterval(() => {
      this.nextStep();
    }, this.speedMs);
  }

  stop() {
    this.isPlaying = false;
    const btn = document.getElementById("anim-play-btn");
    if (btn) btn.innerHTML = "▶ Play";
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
    title.innerText = "Memory Box & 3-Step Swap Simulation";
    badge.innerText = `Step ${this.step} of 3`;

    let a_val = 10;
    let b_val = 20;
    let temp_val = "(empty)";
    let code_snippet = "";
    let step_desc = "";

    if (this.step === 1) {
      temp_val = 10;
      code_snippet = "temp = a  # Step 1: Copy reference in 'a' to holding box 'temp'";
      step_desc = "Step 1: 'temp' saves value 10 from box 'a'. Both now hold 10.";
    } else if (this.step === 2) {
      a_val = 20;
      temp_val = 10;
      code_snippet = "a = b     # Step 2: Overwrite 'a' with reference in 'b'";
      step_desc = "Step 2: Box 'a' is safely updated to 20 because its old value is safe in 'temp'.";
    } else if (this.step === 3) {
      a_val = 20;
      b_val = 10;
      temp_val = 10;
      code_snippet = "b = temp  # Step 3: Move saved reference from 'temp' into 'b'";
      step_desc = "Step 3: Box 'b' receives 10 from 'temp'. Swap complete: a=20, b=10, data loss=0%!";
    }

    expl.innerText = step_desc;

    container.innerHTML = `
      <div class="flex flex-col items-center justify-between w-full h-full p-2 space-y-4">
        <!-- Live Code Action Pill -->
        <div class="w-full text-center py-1.5 px-3 rounded-lg bg-zinc-900 border border-codex-border font-mono text-xs text-amber-400">
          ${code_snippet}
        </div>

        <!-- 3 Hardware RAM Boxes -->
        <div class="grid grid-cols-3 gap-6 w-full max-w-lg">
          <!-- Box A -->
          <div class="flex flex-col items-center p-3 rounded-xl bg-codex-card border ${this.step === 2 ? 'border-amber-400 shadow-lg shadow-amber-900/30' : 'border-codex-border'} transition-all">
            <span class="text-[11px] font-mono text-zinc-400 mb-1">LABEL: a (0x7ffe10)</span>
            <div class="w-20 h-20 rounded-lg bg-[#111114] border border-cyan-500/40 flex items-center justify-center text-2xl font-bold font-mono text-cyan-400 shadow-inner">
              ${a_val}
            </div>
            <span class="text-[10px] text-zinc-500 mt-2 font-mono">int 28 Bytes</span>
          </div>

          <!-- Box B -->
          <div class="flex flex-col items-center p-3 rounded-xl bg-codex-card border ${this.step === 3 ? 'border-emerald-400 shadow-lg shadow-emerald-900/30' : 'border-codex-border'} transition-all">
            <span class="text-[11px] font-mono text-zinc-400 mb-1">LABEL: b (0x7ffe18)</span>
            <div class="w-20 h-20 rounded-lg bg-[#111114] border border-emerald-500/40 flex items-center justify-center text-2xl font-bold font-mono text-emerald-400 shadow-inner">
              ${b_val}
            </div>
            <span class="text-[10px] text-zinc-500 mt-2 font-mono">int 28 Bytes</span>
          </div>

          <!-- Box Temp -->
          <div class="flex flex-col items-center p-3 rounded-xl bg-codex-card border ${this.step === 1 ? 'border-cyan-400 shadow-lg shadow-cyan-900/30' : 'border-dashed border-zinc-700'} transition-all">
            <span class="text-[11px] font-mono text-zinc-400 mb-1">LABEL: temp (0x7ffe20)</span>
            <div class="w-20 h-20 rounded-lg bg-[#111114] border border-zinc-600 flex items-center justify-center text-xl font-bold font-mono ${temp_val === '(empty)' ? 'text-zinc-600' : 'text-amber-400'} shadow-inner">
              ${temp_val}
            </div>
            <span class="text-[10px] text-zinc-500 mt-2 font-mono">Buffer Box</span>
          </div>
        </div>

        <!-- Transfer Verification Banner -->
        <div class="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-4 py-1 rounded-full flex items-center gap-1.5">
          <span>✓</span>
          <span>Zero Data Loss Guaranteed via Intermediate Buffer</span>
        </div>
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 2. py.data_types: Type Casting Transformer & Memory Allocation Grid
   * ------------------------------------------------------------------------- */
  renderDataTypes(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Type Casting Transformer & Memory Footprints";
    badge.innerText = `Step ${this.step} of 3`;

    let stageContent = "";
    if (this.step === 1) {
      expl.innerText = "Step 1: Raw String input '100' sits in memory as an immutable UTF-8 character tape.";
      stageContent = `
        <div class="flex items-center space-x-4">
          <div class="p-3 bg-purple-950/40 border border-purple-500/60 rounded-xl text-center">
            <div class="text-xs font-mono text-purple-300">Type: &lt;class 'str'&gt;</div>
            <div class="text-xl font-mono font-bold text-white mt-1">'100'</div>
            <div class="text-[10px] text-zinc-400 mt-1">UTF-8 tape [ '1', '0', '0' ]</div>
          </div>
          <span class="text-xl text-zinc-500">+</span>
          <div class="p-3 bg-green-950/40 border border-emerald-500/60 rounded-xl text-center">
            <div class="text-xs font-mono text-emerald-300">Type: &lt;class 'int'&gt;</div>
            <div class="text-xl font-mono font-bold text-white mt-1">5</div>
            <div class="text-[10px] text-zinc-400 mt-1">Binary int (28 bytes)</div>
          </div>
          <span class="text-xl text-zinc-500">➔</span>
          <div class="p-3 bg-rose-950/50 border border-rose-500/60 rounded-xl text-center text-rose-300">
            <div class="text-xs font-mono font-bold">CRASH: TypeError</div>
            <div class="text-[10px] mt-1">Cannot add str + int</div>
          </div>
        </div>
      `;
    } else if (this.step === 2) {
      expl.innerText = "Step 2: String passes through the explicit int('100') type casting transformer.";
      stageContent = `
        <div class="flex items-center space-x-4">
          <div class="p-3 bg-purple-950/40 border border-purple-500/60 rounded-xl text-center">
            <div class="text-xs font-mono text-purple-300">'100' (str)</div>
          </div>
          <span class="text-xl text-cyan-400">➔ [ int() Transformer ] ➔</span>
          <div class="p-3 bg-emerald-950/50 border border-emerald-500/60 rounded-xl text-center animate-bounce">
            <div class="text-xs font-mono text-emerald-300">100 (&lt;class 'int'&gt;)</div>
            <div class="text-[10px] text-emerald-400">Allocated 28 heap bytes</div>
          </div>
        </div>
      `;
    } else if (this.step === 3) {
      expl.innerText = "Step 3: Arithmetic executes cleanly: 100 + 5 evaluates to integer 105.";
      stageContent = `
        <div class="flex items-center space-x-4">
          <div class="p-3 bg-emerald-950/40 border border-emerald-500/60 rounded-xl text-center">
            <div class="text-xs font-mono text-emerald-300">100 (int)</div>
          </div>
          <span class="text-xl text-zinc-400">+</span>
          <div class="p-3 bg-emerald-950/40 border border-emerald-500/60 rounded-xl text-center">
            <div class="text-xs font-mono text-emerald-300">5 (int)</div>
          </div>
          <span class="text-xl text-emerald-400">=</span>
          <div class="p-4 bg-cyan-950/60 border border-cyan-400 rounded-2xl text-center shadow-lg shadow-cyan-950/40">
            <div class="text-xs font-mono text-cyan-300">Result: 105</div>
            <div class="text-[10px] text-zinc-400 font-mono mt-1">&lt;class 'int'&gt; • 28 Bytes</div>
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full space-y-4">
        ${stageContent}
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 3. py.operators_expressions: Precedence & Division Floor Visualizer
   * ------------------------------------------------------------------------- */
  renderOperators(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Division Operators: True (/) vs Floor (//) vs Modulo (%)";
    badge.innerText = `Step ${this.step} of 3`;

    let stageContent = "";
    if (this.step === 1) {
      expl.innerText = "Step 1: Single slash '/' always creates a 64-bit float object in memory (7 / 2 -> 3.5).";
      stageContent = `
        <div class="p-4 bg-codex-card border border-cyan-500/60 rounded-2xl text-center space-y-2">
          <div class="text-xs font-mono text-zinc-400">EXPRESSION: 7 / 2 (True Division)</div>
          <div class="text-3xl font-bold font-mono text-cyan-400">3.5</div>
          <div class="text-[11px] font-mono text-zinc-400">Always returns &lt;class 'float'&gt; • 24 bytes IEEE 754</div>
        </div>
      `;
    } else if (this.step === 2) {
      expl.innerText = "Step 2: Double slash '//' performs floor division: truncating down to integer 3 (7 // 2 -> 3).";
      stageContent = `
        <div class="p-4 bg-codex-card border border-emerald-500/60 rounded-2xl text-center space-y-2">
          <div class="text-xs font-mono text-zinc-400">EXPRESSION: 7 // 2 (Floor Division)</div>
          <div class="text-3xl font-bold font-mono text-emerald-400">3</div>
          <div class="text-[11px] font-mono text-zinc-400">Rounds down towards -infinity • Returns &lt;class 'int'&gt;</div>
        </div>
      `;
    } else if (this.step === 3) {
      expl.innerText = "Step 3: Negative floor surprise! -7 // 2 equals -4 because floor rounds towards negative infinity!";
      stageContent = `
        <div class="p-4 bg-amber-950/30 border border-amber-500/70 rounded-2xl text-center space-y-3">
          <div class="text-xs font-mono text-amber-300">EXPRESSION: -7 // 2 (Negative Floor Direction)</div>
          <div class="text-3xl font-bold font-mono text-amber-400">-4</div>
          <p class="text-[11px] text-zinc-300 max-w-sm">
            -3.5 is between -3 and -4. Since floor rounds DOWN (left on number line towards -∞), it becomes -4!
          </p>
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
   * 4. py.conditionals: Railway Branching & Short-Circuit Track
   * ------------------------------------------------------------------------- */
  renderConditionals(container, badge, expl, title) {
    this.totalSteps = 2;
    title.innerText = "Railway Track Switches & Short-Circuit Logic";
    badge.innerText = `Step ${this.step} of 2`;

    let stageContent = "";
    if (this.step === 1) {
      expl.innerText = "Step 1: If-Elif-Else Ladder tests conditions top-to-bottom. First True branch executes, rest skipped.";
      stageContent = `
        <div class="w-full max-w-md space-y-2 font-mono text-xs">
          <div class="p-2.5 rounded-lg bg-zinc-800/80 border border-zinc-700 flex justify-between items-center text-zinc-400">
            <span>if score &gt;= 90: (85 &gt;= 90 is False)</span>
            <span class="text-rose-400 font-bold">✖ SKIPPED</span>
          </div>
          <div class="p-2.5 rounded-lg bg-emerald-950/60 border border-emerald-500/70 flex justify-between items-center text-emerald-300 shadow">
            <span>elif score &gt;= 80: (85 &gt;= 80 is True!)</span>
            <span class="text-emerald-400 font-bold animate-pulse">✓ EXECUTED (grade = 'B')</span>
          </div>
          <div class="p-2.5 rounded-lg bg-zinc-800/80 border border-zinc-700 flex justify-between items-center text-zinc-500">
            <span>else:</span>
            <span>BYPASSED</span>
          </div>
        </div>
      `;
    } else if (this.step === 2) {
      expl.innerText = "Step 2: Short-circuit guard: 'if len(items) > 0 and ...' stops immediately at False, avoiding ZeroDivisionError.";
      stageContent = `
        <div class="p-4 rounded-xl bg-cyan-950/30 border border-cyan-500/60 text-center space-y-3 font-mono text-xs">
          <div class="text-cyan-300">Guard: if len(items) &gt; 0 and (total / len(items)) &gt; 10:</div>
          <div class="flex items-center justify-center space-x-3">
            <span class="px-3 py-1 bg-rose-950 border border-rose-500 text-rose-300 rounded">len([]) &gt; 0 -> False</span>
            <span class="text-amber-400 font-bold">🛑 STOP!</span>
            <span class="px-3 py-1 bg-zinc-900 border border-zinc-700 text-zinc-500 rounded line-through">total / 0</span>
          </div>
          <p class="text-[11px] text-emerald-400">ZeroDivisionError Crash Prevented by Short-Circuiting!</p>
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
   * 5. py.lists_sequences: Sequential Compartments & Slicing Window
   * ------------------------------------------------------------------------- */
  renderLists(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Sequential Array Compartments & [start:stop:step] Slicing";
    badge.innerText = `Step ${this.step} of 3`;

    let highlightIndices = [0];
    if (this.step === 1) {
      expl.innerText = "Step 1: Zero-based indexing points to elements by offset: numbers[0] is the very first element.";
      highlightIndices = [0];
    } else if (this.step === 2) {
      expl.innerText = "Step 2: Negative indexing counts backwards from the right: numbers[-1] is the final element.";
      highlightIndices = [4];
    } else if (this.step === 3) {
      expl.innerText = "Step 3: Slicing numbers[1:4] creates a shallow copy of indices 1, 2, 3 (index 4 is strictly excluded).";
      highlightIndices = [1, 2, 3];
    }

    const elements = [10, 20, 30, 40, 50];
    const posOffsets = [0, 1, 2, 3, 4];
    const negOffsets = [-5, -4, -3, -2, -1];

    let boxesHtml = elements.map((val, idx) => {
      const isHi = highlightIndices.includes(idx);
      return `
        <div class="flex flex-col items-center space-y-1">
          <span class="text-[10px] font-mono ${isHi ? 'text-amber-400 font-bold' : 'text-zinc-500'}">idx: ${posOffsets[idx]}</span>
          <div class="w-14 h-14 rounded-lg bg-[#111115] border ${isHi ? 'border-cyan-400 bg-cyan-950/40 text-cyan-300 shadow-md shadow-cyan-900/30' : 'border-zinc-700 text-zinc-300'} flex items-center justify-center font-mono font-bold text-base transition-all">
            ${val}
          </div>
          <span class="text-[10px] font-mono text-zinc-500">neg: ${negOffsets[idx]}</span>
        </div>
      `;
    }).join("");

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full space-y-4">
        <div class="flex items-center space-x-3">
          ${boxesHtml}
        </div>
        <div class="p-2 rounded bg-zinc-900 border border-codex-border font-mono text-xs text-cyan-300">
          ${this.step === 3 ? "Slice Result: [20, 30, 40] (3 items extracted)" : "Array Address Base: 0x7ffe00"}
        </div>
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 6. py.for_loops: Iterator Conveyor Belt & Loop Pointer
   * ------------------------------------------------------------------------- */
  renderForLoops(container, badge, expl, title) {
    this.totalSteps = 4;
    title.innerText = "Iterator Protocol Conveyor Belt & Accumulator";
    badge.innerText = `Step ${this.step} of 4`;

    const items = [12, 45, 8, 20];
    const idx = this.step - 1;
    const currentItem = items[idx];
    const runningTotal = items.slice(0, this.step).reduce((a, b) => a + b, 0);

    expl.innerText = `Iteration ${this.step}: Loop variable 'item' is bound to ${currentItem}. Total accumulated = ${runningTotal}.`;

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full space-y-5">
        <!-- Conveyor Belt -->
        <div class="flex items-center space-x-4 p-3 bg-zinc-900/80 border border-zinc-700 rounded-xl font-mono text-xs">
          <span class="text-zinc-500 text-[10px]">CONVEYOR TRAY:</span>
          ${items.map((val, i) => `
            <span class="px-3 py-1.5 rounded-lg ${i === idx ? 'bg-cyan-500 text-black font-bold scale-110 shadow' : (i < idx ? 'bg-zinc-800 text-zinc-600 line-through' : 'bg-zinc-800 text-zinc-300')} transition-all">
              ${val}
            </span>
          `).join("")}
        </div>

        <!-- Loop State Boxes -->
        <div class="flex items-center space-x-6">
          <div class="p-3 bg-codex-card border border-cyan-400 rounded-xl text-center">
            <span class="text-[10px] text-zinc-400 font-mono">CURRENT ITEM</span>
            <div class="text-2xl font-bold font-mono text-cyan-400">${currentItem}</div>
          </div>
          <span class="text-xl text-zinc-400">+</span>
          <div class="p-3 bg-codex-card border border-emerald-400 rounded-xl text-center">
            <span class="text-[10px] text-zinc-400 font-mono">RUNNING TOTAL</span>
            <div class="text-2xl font-bold font-mono text-emerald-400">${runningTotal}</div>
          </div>
        </div>
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 7. py.while_loops: Sentinel Gatekeeper & Infinite Loop Warning
   * ------------------------------------------------------------------------- */
  renderWhileLoops(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Sentinel Condition Gate & Loop Cycle Monitor";
    badge.innerText = `Step ${this.step} of 3`;

    let attempts = this.step;
    let auth = this.step === 3;
    let gateStatus = auth ? "OPEN (Terminated Cleanly)" : "PASSING TOLLBOOTH";

    expl.innerText = auth
      ? "Step 3: Condition 'not authenticated' evaluates to False. Toll gate shuts, preventing infinite hang!"
      : `Step ${this.step}: Attempt ${attempts} of 3. Toll gate allows iteration to cycle.`;

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full space-y-4">
        <div class="p-3 bg-zinc-900 border border-codex-border rounded-xl font-mono text-xs text-amber-300 text-center">
          while not authenticated and attempts &lt; 3:
        </div>

        <div class="flex items-center space-x-6">
          <div class="p-4 bg-codex-card border border-codex-border rounded-xl text-center">
            <span class="text-[10px] text-zinc-400 font-mono">ATTEMPTS COUNTER</span>
            <div class="text-2xl font-mono font-bold text-cyan-400">${attempts} / 3</div>
          </div>

          <div class="p-4 bg-codex-card border ${auth ? 'border-emerald-500' : 'border-amber-500'} rounded-xl text-center">
            <span class="text-[10px] text-zinc-400 font-mono">GATE STATUS</span>
            <div class="text-sm font-mono font-bold ${auth ? 'text-emerald-400' : 'text-amber-400'}">${gateStatus}</div>
          </div>
        </div>

        <span class="text-[11px] font-mono text-zinc-400">In-loop variable modification guarantees deterministic termination.</span>
      </div>
    `;
  }

  /* -------------------------------------------------------------------------
   * 8. py.functions: Call Stack Frame Push/Pop & Scope Boundary
   * ------------------------------------------------------------------------- */
  renderFunctions(container, badge, expl, title) {
    this.totalSteps = 3;
    title.innerText = "Call Stack Frame Allocation & Scope Isolation";
    badge.innerText = `Step ${this.step} of 3`;

    let stageContent = "";
    if (this.step === 1) {
      expl.innerText = "Step 1: Global Stack Frame allocates 'order_total = 150.0'. Function defined but not yet invoked.";
      stageContent = `
        <div class="w-64 p-3 bg-zinc-900 border border-zinc-700 rounded-xl space-y-1 font-mono text-xs">
          <div class="text-zinc-500 text-[10px]">STACK BOTTOM: Global Frame</div>
          <div class="text-cyan-300">order_total = 150.0</div>
          <div class="text-zinc-500 text-[10px]">calculate_tax = &lt;function ref&gt;</div>
        </div>
      `;
    } else if (this.step === 2) {
      expl.innerText = "Step 2: Invocation pushes new frame on top: parameters bound, local variable 'tax_amount' created.";
      stageContent = `
        <div class="flex flex-col space-y-2 w-64 font-mono text-xs">
          <div class="p-3 bg-indigo-950/70 border border-indigo-400 rounded-xl space-y-1 animate-pulse">
            <div class="text-indigo-300 text-[10px] font-bold">STACK TOP: calculate_tax() Frame</div>
            <div class="text-zinc-300">subtotal = 150.0, rate = 0.08</div>
            <div class="text-emerald-400 font-bold">tax_amount = 12.0 (Local)</div>
          </div>
          <div class="p-3 bg-zinc-900 border border-zinc-700 rounded-xl">
            <div class="text-zinc-500 text-[10px]">Global Frame (Suspended)</div>
          </div>
        </div>
      `;
    } else if (this.step === 3) {
      expl.innerText = "Step 3: Return yields 12.0 back to caller. Local frame pops off memory and dissolves!";
      stageContent = `
        <div class="w-64 p-3 bg-zinc-900 border border-emerald-500 rounded-xl space-y-1 font-mono text-xs">
          <div class="text-emerald-400 text-[10px] font-bold">Global Frame (Active)</div>
          <div class="text-cyan-300">order_total = 150.0</div>
          <div class="text-emerald-300 font-bold">tax = 12.0 (Returned Value)</div>
          <div class="text-[10px] text-zinc-500 pt-1">Local frame deallocated from stack</div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="flex flex-col items-center justify-center w-full h-full space-y-4">
        ${stageContent}
      </div>
    `;
  }
}

// Global Animation Engine Instance
const animEngine = new ConceptAnimationEngine();
