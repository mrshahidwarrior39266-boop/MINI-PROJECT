/**
 * Codex Tutor — Concept Animated Explainer Video Engine
 * Provides rich, easy-to-understand 4-scene animated video presentations
 * for every concept before introducing the Socratic question.
 */

const CONCEPT_VIDEO_STORYBOARDS = {
  "py.variables": {
    title: "Animated Concept Explainer: Memory Labels, Action Arrow '=' & The 3-Cup Swap",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: The Warehouse Box Metaphor",
        narration: "Think of your computer's RAM as a warehouse full of storage boxes. A variable name is not an equation balance—it is just a yellow sticky label slapped on a box.",
        render: () => `
          <div class="flex items-center justify-center space-x-8 anim-float py-2">
            <div class="flex flex-col items-center p-4 rounded-xl bg-[#1c1c22] border border-cyan-500/70 glow-box-cyan">
              <span class="text-[10px] font-mono text-cyan-300 bg-cyan-950/80 px-2.5 py-0.5 rounded-full border border-cyan-700/60 mb-2">STICKY LABEL: "x"</span>
              <div class="w-24 h-24 rounded-xl bg-[#121216] border border-zinc-700 flex flex-col items-center justify-center">
                <span class="text-3xl font-mono text-white font-bold tracking-tight">10</span>
                <span class="text-[10px] text-zinc-500 font-mono mt-1">int (28 B)</span>
              </div>
              <span class="text-[10px] text-cyan-400/80 font-mono mt-2">RAM Box 0x7ffe10</span>
            </div>
            <div class="anim-arrow-flow flex flex-col items-center text-cyan-400 font-mono">
              <span class="text-2xl font-bold">&larr;</span>
              <span class="text-[10px] uppercase tracking-wider text-cyan-300">Action '='</span>
            </div>
            <div class="p-3.5 bg-zinc-900/90 rounded-xl border border-zinc-800 text-xs font-mono text-zinc-300 max-w-xs leading-relaxed space-y-1">
              <div class="text-amber-400 font-bold flex items-center space-x-1">
                <span>⚡ Golden Rule:</span>
              </div>
              <p class="text-[11px] text-zinc-300">
                '=' is an ACTION ARROW. Python calculates the value on the right first, and binds the name tag on the left.
              </p>
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: How Python Evaluates Rebinding (x = x + 1)",
        narration: "When Python sees 'x = x + 1', it completely evaluates the right-hand side first (10 + 1 = 11), and then rebinds the label 'x' to the new value in memory.",
        render: () => `
          <div class="flex flex-col items-center space-y-4 py-2">
            <div class="px-5 py-2 rounded-xl bg-zinc-900 border border-zinc-700 font-mono text-xs text-amber-300 shadow-md">
              x = x + 1   <span class="text-zinc-500"># Step 1: Reads 10 &rarr; Computes 11 &rarr; Rebinds tag 'x'</span>
            </div>
            <div class="flex items-center space-x-8">
              <div class="flex flex-col items-center p-3.5 rounded-xl bg-[#18181c] border border-zinc-700/80">
                <span class="text-[10px] font-mono text-zinc-500">Old Value in 0x7ffe10</span>
                <span class="text-2xl font-mono text-zinc-500 line-through mt-1">10</span>
                <span class="text-[9px] text-zinc-600 font-mono mt-1">Discarded</span>
              </div>
              <div class="anim-arrow-flow text-xl text-cyan-400 font-mono">&rarr;</div>
              <div class="flex flex-col items-center p-3.5 rounded-xl bg-[#18181c] border border-emerald-400 glow-box-emerald anim-pulse-glow">
                <span class="text-[10px] font-mono text-emerald-400 font-medium">New Value in RAM</span>
                <span class="text-3xl font-mono text-white font-bold mt-1">11</span>
                <span class="text-[9px] text-emerald-400/70 font-mono mt-1">Label 'x' bound</span>
              </div>
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: The Fatal Overwrite Trap & The 3-Cup Swap",
        narration: "If you have two cups (Milk in Cup x, Juice in Cup y) and write 'x = y', Cup x is overwritten and the Milk is destroyed forever! You MUST pour Cup x into a third buffer cup 'temp' first.",
        render: () => `
          <div class="flex flex-col items-center space-y-3 py-1">
            <div class="grid grid-cols-3 gap-6 w-full max-w-md">
              <div class="flex flex-col items-center p-3 rounded-xl bg-[#18181c] border border-cyan-500/70 glow-box-cyan">
                <span class="text-[10px] font-mono text-cyan-300">Cup x (Milk)</span>
                <div class="text-2xl font-mono text-cyan-200 font-bold mt-1">10</div>
                <span class="text-[9px] text-zinc-500 mt-1">0x7ffe10</span>
              </div>
              <div class="flex flex-col items-center p-3 rounded-xl bg-[#18181c] border border-emerald-500/70 glow-box-emerald">
                <span class="text-[10px] font-mono text-emerald-300">Cup y (Juice)</span>
                <div class="text-2xl font-mono text-emerald-200 font-bold mt-1">20</div>
                <span class="text-[9px] text-zinc-500 mt-1">0x7ffe18</span>
              </div>
              <div class="flex flex-col items-center p-3 rounded-xl bg-[#18181c] border border-amber-500/70 glow-box-amber">
                <span class="text-[10px] font-mono text-amber-300">Buffer 'temp'</span>
                <div class="text-2xl font-mono text-amber-200 font-bold mt-1">10</div>
                <span class="text-[9px] text-zinc-500 mt-1">Safe Copy</span>
              </div>
            </div>
            <div class="px-4 py-1.5 rounded-lg bg-rose-950/40 border border-rose-800/40 text-[11px] font-mono text-rose-300 text-center">
              ⚠ If you do <code class="text-white font-bold">x = y</code> directly, x becomes 20 and 10 is destroyed forever!
            </div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: The Golden Invariant (3-Step Safe Swap)",
        narration: "Golden Rule: To swap values safely without data loss in Python: 1) temp = x, 2) x = y, 3) y = temp. You are now fully prepared to solve the Socratic Checkpoint below!",
        render: () => `
          <div class="p-5 rounded-xl bg-emerald-950/40 border border-emerald-500/50 glow-box-emerald text-center space-y-2 max-w-md">
            <div class="text-xs font-mono text-emerald-400 uppercase font-bold tracking-wider flex items-center justify-center space-x-1.5">
              <span>✓ Concept Invariant Verified</span>
            </div>
            <div class="p-2.5 rounded-lg bg-black/40 border border-emerald-800/40 font-mono text-xs text-cyan-300 text-left space-y-0.5">
              <div>1. <span class="text-amber-300">temp = x</span>  <span class="text-zinc-500"># Save Milk into holding buffer</span></div>
              <div>2. <span class="text-emerald-300">x = y</span>     <span class="text-zinc-500"># Overwrite x with Juice safely</span></div>
              <div>3. <span class="text-cyan-300">y = temp</span>  <span class="text-zinc-500"># Rebind y to saved Milk</span></div>
            </div>
            <p class="text-[11px] text-zinc-300 pt-1">
              Scroll down to the Socratic Practice Checkpoint below to confirm your understanding!
            </p>
          </div>
        `
      }
    ]
  },

  "py.data_types": {
    title: "Animated Explainer: Primitive Data Types & Explicit Type Casting",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Counting Marbles vs Alphabet Paper Tapes",
        narration: "Integers and Floats are physical counting marbles you can weigh. Strings are ink stamped on paper tape. Even if you stamp '100' on paper tape, it remains a piece of paper!",
        render: () => `
          <div class="flex items-center space-x-6 anim-float">
            <div class="p-4 rounded-xl bg-[#18181c] border border-purple-500/60 text-center">
              <span class="text-[10px] font-mono text-purple-400">PAPER TAPE (str)</span>
              <div class="text-2xl font-mono text-white mt-1">'100'</div>
              <span class="text-[10px] text-zinc-500 mt-1">UTF-8 Characters</span>
            </div>
            <span class="text-xl text-zinc-500">vs</span>
            <div class="p-4 rounded-xl bg-[#18181c] border border-emerald-500/60 text-center">
              <span class="text-[10px] font-mono text-emerald-400">COUNTING MARBLES (int)</span>
              <div class="text-2xl font-mono text-white mt-1">100</div>
              <span class="text-[10px] text-zinc-500 mt-1">28 Heap Bytes</span>
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: The 4 Core Primitives in RAM",
        narration: "Python provides 4 foundational primitives: int (arbitrary precision ~28 bytes), float (64-bit IEEE 754 ~24 bytes), str (immutable Unicode sequence), and bool (True or False).",
        render: () => `
          <div class="grid grid-cols-4 gap-3 text-center font-mono text-xs">
            <div class="p-2.5 bg-[#18181c] border border-emerald-500/40 rounded-lg">
              <div class="text-[10px] text-emerald-400">int</div>
              <div class="text-white font-bold mt-1">42</div>
              <div class="text-[9px] text-zinc-500">28 B</div>
            </div>
            <div class="p-2.5 bg-[#18181c] border border-cyan-500/40 rounded-lg">
              <div class="text-[10px] text-cyan-400">float</div>
              <div class="text-white font-bold mt-1">19.99</div>
              <div class="text-[9px] text-zinc-500">24 B</div>
            </div>
            <div class="p-2.5 bg-[#18181c] border border-purple-500/40 rounded-lg">
              <div class="text-[10px] text-purple-400">str</div>
              <div class="text-white font-bold mt-1">'PY'</div>
              <div class="text-[9px] text-zinc-500">Sequence</div>
            </div>
            <div class="p-2.5 bg-[#18181c] border border-amber-500/40 rounded-lg">
              <div class="text-[10px] text-amber-400">bool</div>
              <div class="text-white font-bold mt-1">True</div>
              <div class="text-[9px] text-zinc-500">1 Bit</div>
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Strong Typing & The Scanner Transformer",
        narration: "Python is strongly typed: it will NEVER automatically turn '100' into a number during addition. You must explicitly scan the tape with int('100') to convert it into real marbles.",
        render: () => `
          <div class="flex items-center space-x-4 font-mono text-xs">
            <div class="p-3 bg-[#18181c] border border-purple-500/50 rounded-lg text-purple-300">'100' (str)</div>
            <span class="text-cyan-400">&rarr; [ int() Scanner ] &rarr;</span>
            <div class="p-3 bg-[#18181c] border border-emerald-500/50 rounded-lg text-emerald-300">100 (int)</div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Key Invariant",
        narration: "Never expect Python to guess your types. Explicit casting with int(), float(), or str() is required and prevents runtime TypeErrors.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center space-y-1">
            <div class="text-xs font-mono text-emerald-400 font-bold">Strong Typing Invariant</div>
            <p class="text-xs text-zinc-200">
              '15' + 5 &rarr; TypeError!
              <br>int('15') + 5 &rarr; 20 (Safe Evaluated Arithmetic)
            </p>
          </div>
        `
      }
    ]
  },

  "py.operators_expressions": {
    title: "Animated Explainer: Division Mechanics & Floor Semantics",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: The Precision Knife vs Whole Shipping Box",
        narration: "Single slash '/' is a precision chef knife that cuts exact decimals (7 / 2 -> 3.5). Double slash '//' is a packing box that only packs complete units, throwing away fractions.",
        render: () => `
          <div class="flex items-center space-x-6 font-mono text-xs">
            <div class="p-4 rounded-xl bg-[#18181c] border border-cyan-500/60 text-center">
              <span class="text-[10px] text-cyan-400">7 / 2 (True Division)</span>
              <div class="text-2xl text-white mt-1">3.5</div>
              <span class="text-[10px] text-zinc-500">Returns float</span>
            </div>
            <div class="p-4 rounded-xl bg-[#18181c] border border-emerald-500/60 text-center">
              <span class="text-[10px] text-emerald-400">7 // 2 (Floor Division)</span>
              <div class="text-2xl text-white mt-1">3</div>
              <span class="text-[10px] text-zinc-500">Rounds down to int</span>
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: The Negative Floor Surprise",
        narration: "Why does -7 // 2 equal -4 instead of -3? Because 'floor' means rounding DOWN towards negative infinity on the number line!",
        render: () => `
          <div class="p-4 rounded-xl bg-amber-950/20 border border-amber-500/40 text-center space-y-2">
            <div class="text-xs font-mono text-amber-300">-7 // 2 &rarr; -4</div>
            <p class="text-xs text-zinc-300 max-w-sm font-sans">
              -3.5 lies between -3 and -4. Rounding DOWN toward negative infinity leads directly to -4!
            </p>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Modulo Remainder Scrap Bin",
        narration: "The modulo operator '%' collects whatever scrap doesn't fit into a full box. For 7 % 2: two boxes of 3 take 6, leaving remainder 1.",
        render: () => `
          <div class="p-3.5 rounded-xl bg-[#18181c] border border-zinc-700 text-center font-mono text-xs">
            <div class="text-cyan-300 font-bold">7 % 2 == 1</div>
            <div class="text-[11px] text-zinc-400 mt-1">(2 * (7 // 2)) + (7 % 2) == 7</div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Key Invariant",
        narration: "In Python 3, single '/' ALWAYS produces a float. Floor '//' always rounds towards negative infinity.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center space-y-1">
            <div class="text-xs font-mono text-emerald-400 font-bold">Division Summary</div>
            <p class="text-xs text-zinc-200">7 / 2 = 3.5 &bull; 7 // 2 = 3 &bull; -7 // 2 = -4</p>
          </div>
        `
      }
    ]
  },

  "py.conditionals": {
    title: "Animated Explainer: Railway Track Switches & Short-Circuit Logic",
    duration: "0:40",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Railway Track Switch",
        narration: "A computer's execution pointer is a locomotive traveling down a rail line. An 'if' statement is a track switch: Green takes the branch, Red stays on the main line.",
        render: () => `
          <div class="flex items-center space-x-4 font-mono text-xs">
            <div class="p-3 rounded-lg bg-[#18181c] border border-zinc-700">Train &rarr;</div>
            <div class="p-3 rounded-lg bg-emerald-950/50 border border-emerald-500 text-emerald-300">if score &gt;= 80: [Branch A]</div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Cascading Elif Ladder",
        narration: "In an if-elif ladder, Python tests guards top to bottom. The VERY FIRST guard that evaluates to True runs its block, and all other branches are skipped.",
        render: () => `
          <div class="space-y-1 font-mono text-xs max-w-xs">
            <div class="p-2 rounded bg-zinc-900 border border-zinc-800 text-zinc-500">if 85 &gt;= 90: (False) &rarr; Skip</div>
            <div class="p-2 rounded bg-emerald-950 border border-emerald-500 text-emerald-300">elif 85 &gt;= 80: (True) &rarr; Run!</div>
            <div class="p-2 rounded bg-zinc-900 border border-zinc-800 text-zinc-500">else: Bypassed</div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Short-Circuit Security Gate",
        narration: "In 'A and B', if A is False, Python stops immediately and never touches B. This protects your code from ZeroDivisionError crashes!",
        render: () => `
          <div class="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/50 text-center font-mono text-xs">
            <div>if len(items) &gt; 0 and (total / len(items)) &gt; 10:</div>
            <div class="text-emerald-400 mt-1">len([]) &gt; 0 is False &rarr; Stops right there. No crash!</div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Key Invariant",
        narration: "Always put protective safety guards on the left side of 'and' to leverage short-circuit safety.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center">
            <div class="text-xs font-mono text-emerald-400 font-bold">Short-Circuit Invariant</div>
            <p class="text-xs text-zinc-200 mt-1">Left-to-right evaluation protects uninitialized pointers and divisions.</p>
          </div>
        `
      }
    ]
  },

  "py.lists_sequences": {
    title: "Animated Explainer: Sequential Memory Arrays & Half-Open Slicing",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Mailboxes with Zero Steps",
        narration: "Think of an array as apartment mailboxes. Index 0 means 'take 0 steps from the lobby door'—the first mailbox! Index 1 is 1 step down.",
        render: () => `
          <div class="flex items-center space-x-2 font-mono text-xs">
            <div class="p-2.5 bg-[#18181c] border border-cyan-400 rounded-lg text-center">
              <span class="text-[9px] text-zinc-500">idx: 0</span>
              <div class="text-white font-bold">10</div>
            </div>
            <div class="p-2.5 bg-[#18181c] border border-zinc-700 rounded-lg text-center">
              <span class="text-[9px] text-zinc-500">idx: 1</span>
              <div class="text-white">20</div>
            </div>
            <div class="p-2.5 bg-[#18181c] border border-zinc-700 rounded-lg text-center">
              <span class="text-[9px] text-zinc-500">idx: 2</span>
              <div class="text-white">30</div>
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Negative Indices Count Backwards",
        narration: "Negative indices start from the right end: list[-1] taps the back wall to get the final element directly in constant time.",
        render: () => `
          <div class="p-3 bg-[#18181c] border border-zinc-700 rounded-xl font-mono text-xs text-center">
            items = [10, 20, 30, 40, 50] &bull; items[-1] == 50
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: The Cardboard Stencil Slicing Cutout",
        narration: "Slicing items[1:4] is like laying a cardboard cutout over mailboxes 1, 2, and 3. Box 4 is covered by the edge because the stop index is always exclusive!",
        render: () => `
          <div class="p-3.5 bg-cyan-950/30 border border-cyan-500/50 rounded-xl text-center font-mono text-xs">
            <div>items[1:4] &rarr; [20, 30, 40]</div>
            <div class="text-[10px] text-zinc-400 mt-1">Half-open range [1, 4) strictly excludes index 4.</div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Key Invariant",
        narration: "Slicing creates a new shallow copy without modifying the original sequence.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center">
            <div class="text-xs font-mono text-emerald-400 font-bold">Slicing Invariant</div>
            <p class="text-xs text-zinc-200 mt-1">len(items[start:stop]) == stop - start (when step=1).</p>
          </div>
        `
      }
    ]
  },

  "py.for_loops": {
    title: "Animated Explainer: Iterator Conveyor Belts & State Accumulators",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Factory Conveyor Belt",
        narration: "A for loop is a factory conveyor belt. The list is the tray of parts waiting in line. On each click, one part drops into your hands as variable 'item'.",
        render: () => `
          <div class="p-3.5 rounded-xl bg-[#18181c] border border-zinc-700 font-mono text-xs text-center">
            Conveyor Tray: [ 12, 45, 8, 20 ] &rarr; Drops 12 into 'item'
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Running Accumulator Box",
        narration: "As items drop from the belt, your accumulator box updates: total += item. Step by step, the running total compounds.",
        render: () => `
          <div class="flex items-center space-x-4 font-mono text-xs">
            <div class="p-3 bg-[#18181c] border border-cyan-400 rounded-lg">item: 45</div>
            <span>+</span>
            <div class="p-3 bg-[#18181c] border border-emerald-400 rounded-lg">total: 57</div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: The StopIteration Signal",
        narration: "When the conveyor runs out of parts, Python receives an internal StopIteration exception and cleanly exits the loop without crashing.",
        render: () => `
          <div class="p-3 bg-zinc-900 border border-zinc-800 rounded-xl font-mono text-xs text-center text-zinc-400">
            End of sequence &rarr; StopIteration received &rarr; Loop completed.
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Key Invariant",
        narration: "Never delete or add items to a list while iterating over it, or pointer offsets will skip items!",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center">
            <div class="text-xs font-mono text-emerald-400 font-bold">Iterator Invariant</div>
            <p class="text-xs text-zinc-200 mt-1">range() is a lazy sequence that calculates numbers on demand in O(1) RAM.</p>
          </div>
        `
      }
    ]
  },

  "py.while_loops": {
    title: "Animated Explainer: Gated Tollbooths & Loop Termination",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Gated Security Tollbooth",
        narration: "A while loop is a gated tollbooth. Before EVERY lap, the guard inspects your ticket (the boolean condition). If True, you drive through.",
        render: () => `
          <div class="p-3.5 bg-[#18181c] border border-amber-500/50 rounded-xl font-mono text-xs text-center">
            Security Gate: while attempts &lt; 3: &rarr; Ticket verified!
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Punching the Ticket (In-Loop Modification)",
        narration: "Every time you drive through the gate, you MUST punch the ticket (attempts += 1) so you get closer to the exit condition.",
        render: () => `
          <div class="flex items-center space-x-4 font-mono text-xs">
            <div class="p-3 bg-[#18181c] border border-zinc-700 rounded-lg">Lap 1: attempts = 1</div>
            <span>&rarr;</span>
            <div class="p-3 bg-[#18181c] border border-zinc-700 rounded-lg">Lap 2: attempts = 2</div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: The Infinite Loop Alarm",
        narration: "If you forget to increment the counter, the guard lets you drive in circles forever, consuming 100% CPU thread cycles!",
        render: () => `
          <div class="p-3 bg-rose-950/40 border border-rose-500/50 rounded-xl font-mono text-xs text-rose-300 text-center">
            WARNING: Infinite loop without counter increment hangs execution!
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Key Invariant",
        narration: "Guarantee loop termination by modifying state variables or providing explicit 'break' sentinels.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center">
            <div class="text-xs font-mono text-emerald-400 font-bold">Termination Invariant</div>
            <p class="text-xs text-zinc-200 mt-1">Every while loop must have a reachable state path to False.</p>
          </div>
        `
      }
    ]
  },

  "py.functions": {
    title: "Animated Explainer: Sealed Laboratories & Call Stack Frames",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Sealed Soundproof Laboratory",
        narration: "A function is a soundproof lab room with two openings: an Input Mail Slot (parameters) and an Output Chute (return value).",
        render: () => `
          <div class="flex items-center space-x-4 font-mono text-xs">
            <div class="p-3 bg-[#18181c] border border-cyan-400 rounded-lg">Input: subtotal=150.0</div>
            <span>&rarr; [ Lab Room ] &rarr;</span>
            <div class="p-3 bg-[#18181c] border border-emerald-400 rounded-lg">Output: 12.0</div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Pushing the Stack Frame",
        narration: "When you call a function, Python pushes a new Stack Frame on memory. Local whiteboards are created that cannot be seen from outside.",
        render: () => `
          <div class="flex flex-col space-y-1.5 font-mono text-xs w-48">
            <div class="p-2 bg-indigo-950 border border-indigo-400 rounded-md text-white text-[10px]">
              STACK TOP: calculate_tax() Frame
            </div>
            <div class="p-2 bg-[#18181c] border border-zinc-700 rounded-md text-zinc-500 text-[10px]">
              Global Frame (Waiting)
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Return vs Print",
        narration: "print() merely writes text to your screen; it gives nothing to your program. return delivers the real evaluated object to the caller and deallocates the frame.",
        render: () => `
          <div class="p-3 bg-[#18181c] border border-zinc-700 rounded-xl font-mono text-xs text-center space-y-1">
            <div class="text-rose-300">print(x) &rarr; returns None</div>
            <div class="text-emerald-300">return x &rarr; delivers data to caller</div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Key Invariant",
        narration: "Local variables dissolve when the stack frame pops off memory. Functions without 'return' return None implicitly.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center">
            <div class="text-xs font-mono text-emerald-400 font-bold">Scope Invariant</div>
            <p class="text-xs text-zinc-200 mt-1">LEGB scope resolution: Local &rarr; Enclosing &rarr; Global &rarr; Built-in.</p>
          </div>
        `
      }
    ]
  }
};

// ---------------------------------------------------------------------------
// DEDICATED INDIVIDUAL VIDEO STORYBOARDS PER QUESTION
// Every single question in the curriculum has its own visual 4-scene video!
// ---------------------------------------------------------------------------
const QUESTION_VIDEO_STORYBOARDS = {
  // Question 1: x = x + 1 Order of Evaluation
  "q_var_01": {
    title: "Question 1 Explainer: Action Arrow '=' & Evaluation Order (x = x + 1)",
    duration: "0:40",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Equality vs Action Arrow",
        narration: "In mathematics, 'x = x + 1' is impossible because '=' means simultaneous equality. In Python, '=' is an ACTION ARROW (←) that assigns state across time.",
        render: () => `
          <div class="flex items-center justify-center space-x-8 anim-float py-2">
            <div class="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/50 text-center">
              <span class="text-[10px] font-mono text-rose-400 uppercase">Math Algebra</span>
              <div class="text-xl font-mono text-white mt-1">x = x + 1</div>
              <span class="text-[10px] text-rose-300 font-mono mt-1 block">❌ Impossible (No solution)</span>
            </div>
            <div class="text-2xl text-zinc-500">&ne;</div>
            <div class="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/50 glow-box-cyan text-center">
              <span class="text-[10px] font-mono text-cyan-400 uppercase">Python Programming</span>
              <div class="text-xl font-mono text-cyan-200 mt-1">x &larr; (x + 1)</div>
              <span class="text-[10px] text-cyan-300 font-mono mt-1 block">✓ Sequential Rebinding</span>
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Right-Hand Side Evaluates First",
        narration: "When Python executes 'x = x + 1', it stops and completely computes the right-hand side first. If x was 10, it fetches 10 and calculates 10 + 1 = 11.",
        render: () => `
          <div class="flex flex-col items-center space-y-3 py-1">
            <div class="px-4 py-1.5 rounded-lg bg-zinc-900 border border-amber-500/50 font-mono text-xs text-amber-300">
              x = <span class="bg-amber-500/20 px-2 py-0.5 rounded text-white border border-amber-400">x + 1</span>  &larr; Evaluates right side first!
            </div>
            <div class="flex items-center space-x-4">
              <div class="p-3 bg-[#18181c] border border-zinc-700 rounded-lg text-center font-mono">
                <span class="text-[10px] text-zinc-400">Fetch x</span>
                <div class="text-lg text-white">10</div>
              </div>
              <span class="text-xl font-mono text-amber-400">+ 1 &rarr;</span>
              <div class="p-3 bg-[#18181c] border border-emerald-500 rounded-lg text-center font-mono glow-box-emerald">
                <span class="text-[10px] text-emerald-400">Computed Result</span>
                <div class="text-2xl text-emerald-300 font-bold">11</div>
              </div>
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Rebinding the Sticky Label in RAM",
        narration: "Once 11 is calculated, Python allocates heap memory and moves the yellow sticky label 'x' to point to 11. The old 10 is left behind.",
        render: () => `
          <div class="flex items-center space-x-8 py-2">
            <div class="flex flex-col items-center p-3 rounded-xl bg-[#141416] border border-zinc-800">
              <span class="text-[10px] text-zinc-500 font-mono">Old Address 0x7ffe10</span>
              <span class="text-xl font-mono text-zinc-600 line-through mt-1">10</span>
              <span class="text-[9px] text-zinc-600 font-mono mt-1">Detached</span>
            </div>
            <div class="anim-arrow-flow text-cyan-400 text-xl font-mono">&rarr;</div>
            <div class="flex flex-col items-center p-3.5 rounded-xl bg-[#141416] border border-cyan-400 glow-box-cyan">
              <span class="text-[10px] text-cyan-300 font-mono">STICKY LABEL: "x"</span>
              <span class="text-3xl font-mono text-white font-bold mt-1">11</span>
              <span class="text-[9px] text-cyan-400 font-mono mt-1">New Address 0x7ffe28</span>
            </div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Time Invariant Verified",
        narration: "Summary: Statements execute sequentially in time. 'x = x + 1' is not an assertion of equality; it is an instruction to compute a new value and update the name tag.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center space-y-1.5 max-w-sm">
            <div class="text-xs font-mono text-emerald-400 font-bold">✓ Mechanism Mastered</div>
            <p class="text-xs text-zinc-200">
              1. Right-side computes <code>10 + 1 = 11</code>.<br>
              2. Label <code>x</code> binds to <code>11</code> in RAM.
            </p>
          </div>
        `
      }
    ]
  },

  // Question 2: Snapshot Copy vs Permanent Link
  "q_var_02": {
    title: "Question 2 Explainer: Independent Sticky Labels & Snapshots (a = 10, b = a, a = 20)",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Line 1 — Initializing Label 'a'",
        narration: "Line 1: 'a = 10'. Python creates an integer object 10 in RAM and binds the label 'a' to that address.",
        render: () => `
          <div class="flex items-center justify-center space-x-6 py-2">
            <div class="flex flex-col items-center p-3.5 rounded-xl bg-[#141416] border border-cyan-500/70 glow-box-cyan">
              <span class="text-[10px] font-mono text-cyan-300">Label: "a"</span>
              <div class="text-3xl font-mono text-white font-bold mt-1">10</div>
              <span class="text-[9px] font-mono text-zinc-500 mt-1">0x7ffe10</span>
            </div>
            <div class="p-3 bg-zinc-900 rounded-lg border border-zinc-800 text-xs font-mono text-zinc-300">
              <code>a = 10</code><br>
              <span class="text-zinc-500 text-[10px]">Points tag 'a' to 10</span>
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Line 2 — Snapshot Copy (b = a)",
        narration: "Line 2: 'b = a'. Python inspects what 'a' points to at this split-second (10), and binds label 'b' to 10 as well. It does NOT link them together!",
        render: () => `
          <div class="flex flex-col items-center space-y-3 py-1">
            <div class="flex items-center space-x-4">
              <span class="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-500 text-cyan-300 font-mono text-xs">Label "a"</span>
              <span class="text-zinc-400 font-mono">&rarr;</span>
              <div class="w-20 h-16 rounded-xl bg-[#121216] border border-emerald-500 flex flex-col items-center justify-center glow-box-emerald">
                <span class="text-2xl font-mono text-white font-bold">10</span>
                <span class="text-[9px] text-zinc-500">0x7ffe10</span>
              </div>
              <span class="text-zinc-400 font-mono">&larr;</span>
              <span class="px-2 py-0.5 rounded bg-amber-950 border border-amber-500 text-amber-300 font-mono text-xs">Label "b"</span>
            </div>
            <span class="text-[10px] font-mono text-amber-300">Both labels point to 10 independently.</span>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Line 3 — Rebinding 'a' Leaves 'b' Untouched",
        narration: "Line 3: 'a = 20'. Python allocates a new integer 20 and moves tag 'a' to 20. But notice label 'b' never moved—it still points to 10!",
        render: () => `
          <div class="flex items-center justify-center space-x-8 py-2">
            <div class="flex flex-col items-center p-3 rounded-xl bg-[#141416] border border-cyan-500/70 glow-box-cyan">
              <span class="text-[10px] font-mono text-cyan-300">Label "a" (Moved!)</span>
              <div class="text-3xl font-mono text-white font-bold mt-1">20</div>
              <span class="text-[9px] font-mono text-cyan-400 mt-1">0x7ffe28</span>
            </div>
            <div class="flex flex-col items-center p-3 rounded-xl bg-[#141416] border border-amber-500/70 glow-box-amber">
              <span class="text-[10px] font-mono text-amber-300">Label "b" (Untouched)</span>
              <div class="text-3xl font-mono text-white font-bold mt-1">10</div>
              <span class="text-[9px] font-mono text-amber-400 mt-1">0x7ffe10</span>
            </div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: The Snapshot Invariant",
        narration: "Golden Rule: Assignment in Python captures a snapshot at that instant. Variables are never linked like spreadsheet formulas. 'b' remains 10 forever until reassigned.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center space-y-1 max-w-sm">
            <div class="text-xs font-mono text-emerald-400 font-bold">✓ b = 10 Confirmed</div>
            <p class="text-xs text-zinc-200">
              Modifying <code>a</code> later has zero effect on <code>b</code>.
            </p>
          </div>
        `
      }
    ]
  },

  // Question 3: Swapping Variables Without Data Loss
  "q_var_03": {
    title: "Question 3 Explainer: The 3-Cup Swap & Buffer Variables (temp = x, x = y, y = temp)",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Two Full Cups (x = 10, y = 20)",
        narration: "Suppose Cup x holds Milk (10) and Cup y holds Juice (20). How can you swap their contents without spilling or losing either value?",
        render: () => `
          <div class="flex items-center space-x-8 py-2">
            <div class="p-3.5 rounded-xl bg-[#141416] border border-cyan-500 text-center glow-box-cyan">
              <span class="text-[10px] font-mono text-cyan-300">Cup x (Milk)</span>
              <div class="text-3xl font-mono text-white font-bold mt-1">10</div>
            </div>
            <div class="p-3.5 rounded-xl bg-[#141416] border border-emerald-500 text-center glow-box-emerald">
              <span class="text-[10px] font-mono text-emerald-300">Cup y (Juice)</span>
              <div class="text-3xl font-mono text-white font-bold mt-1">20</div>
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: The Direct Overwrite Trap",
        narration: "If you execute 'x = y' directly, you pour Juice into Cup x—instantly destroying the Milk forever! Both cups now hold 20. The original value 10 is lost.",
        render: () => `
          <div class="flex flex-col items-center space-y-2 py-1">
            <div class="p-2.5 rounded bg-rose-950/50 border border-rose-500 text-rose-300 text-xs font-mono text-center">
              ❌ If you do: <code>x = y</code><br>
              Cup x becomes 20, and 10 is destroyed forever!
            </div>
            <div class="flex space-x-6">
              <div class="p-3 rounded-lg bg-zinc-900 border border-zinc-700 text-center font-mono">
                <span class="text-[10px] text-zinc-500">x</span>
                <div class="text-2xl text-rose-400 font-bold">20</div>
              </div>
              <div class="p-3 rounded-lg bg-zinc-900 border border-zinc-700 text-center font-mono">
                <span class="text-[10px] text-zinc-500">y</span>
                <div class="text-2xl text-rose-400 font-bold">20</div>
              </div>
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: The 3-Step Safe Solution with 'temp'",
        narration: "To solve this, use an empty third cup 'temp'. 1) temp = x saves Milk. 2) x = y pours Juice into x safely. 3) y = temp pours Milk into y.",
        render: () => `
          <div class="grid grid-cols-3 gap-3 font-mono text-xs text-center py-1">
            <div class="p-2.5 bg-black/40 border border-amber-500 rounded-lg">
              <span class="text-amber-400 text-[10px]">1. temp = x</span>
              <div class="text-sm text-zinc-300 mt-1">Saves 10 into temp</div>
            </div>
            <div class="p-2.5 bg-black/40 border border-emerald-500 rounded-lg">
              <span class="text-emerald-400 text-[10px]">2. x = y</span>
              <div class="text-sm text-zinc-300 mt-1">Copies 20 into x</div>
            </div>
            <div class="p-2.5 bg-black/40 border border-cyan-500 rounded-lg">
              <span class="text-cyan-400 text-[10px]">3. y = temp</span>
              <div class="text-sm text-zinc-300 mt-1">Copies 10 into y</div>
            </div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Swapped Result & Tuple Unpacking",
        narration: "Done! Now x is 20 and y is 10. Python also provides tuple packing shortcut: 'x, y = y, x'.",
        render: () => `
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center space-y-1.5 max-w-sm">
            <div class="text-xs font-mono text-emerald-400 font-bold">✓ Successfully Swapped!</div>
            <div class="font-mono text-xs text-cyan-200">x = 20 &nbsp;•&nbsp; y = 10</div>
            <div class="text-[11px] text-zinc-400 font-mono">Pythonic syntax: <code>x, y = y, x</code></div>
          </div>
        `
      }
    ]
  },

  // Question: Data Types "5" + "5"
  "q_types_01": {
    title: "Question 1 Explainer: String Concatenation vs Integer Math ('5' + '5')",
    duration: "0:40",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Quotes Mean Text, Not Numbers",
        narration: "In Python, quotes ' ' denote a string—a sequence of character glyphs stamped on paper tape, not a numerical quantity.",
        render: () => `
          <div class="flex items-center space-x-6 py-2">
            <div class="p-3.5 bg-purple-950/30 border border-purple-500/60 rounded-xl text-center">
              <span class="text-[10px] font-mono text-purple-400">STRING LITERAL</span>
              <div class="text-2xl font-mono text-white mt-1">'5'</div>
            </div>
            <span class="text-xl text-zinc-500">&ne;</span>
            <div class="p-3.5 bg-emerald-950/30 border border-emerald-500/60 rounded-xl text-center">
              <span class="text-[10px] font-mono text-emerald-400">INTEGER NUMBER</span>
              <div class="text-2xl font-mono text-white mt-1">5</div>
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Overloaded '+' Operator",
        narration: "The '+' operator behaves differently depending on type: between integers it adds; between strings it GLUES characters together (concatenation).",
        render: () => `
          <div class="flex flex-col items-center space-y-2 py-1 font-mono text-xs">
            <div class="p-2 rounded bg-black/40 border border-emerald-500 text-emerald-300">
              5 + 5 &rarr; 10 &nbsp; (Arithmetic Addition)
            </div>
            <div class="p-2 rounded bg-black/40 border border-purple-500 text-purple-300">
              '5' + '5' &rarr; '55' &nbsp; (String Concatenation)
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: The Result in RAM",
        narration: "Evaluating '5' + '5' glues the two text characters into the 2-character string '55'. It will never produce 10.",
        render: () => `
          <div class="p-4 rounded-xl bg-purple-950/40 border border-purple-500/60 text-center font-mono space-y-1">
            <span class="text-[10px] text-purple-300 uppercase">Evaluated Result</span>
            <div class="text-3xl text-white font-bold">'55'</div>
            <span class="text-[10px] text-zinc-400">Type: str (length 2)</span>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Explicit Conversion to Add",
        narration: "To add mathematically, you must explicitly convert them with int(): int('5') + int('5') equals 10.",
        render: () => `
          <div class="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/40 text-center font-mono text-xs space-y-1">
            <div class="text-emerald-400 font-bold">int('5') + int('5') == 10</div>
            <p class="text-[11px] text-zinc-300 font-sans">Explicit casting tells Python to interpret the text as integers.</p>
          </div>
        `
      }
    ]
  },

  // Question: Casting age = '18'
  "q_types_02": {
    title: "Question 2 Explainer: Strong Typing & Explicit Casting (int(age) + 1)",
    duration: "0:40",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Strong Typing Prevents Silent Errors",
        narration: "Python is strongly typed: it will NEVER silently coerce string '18' into a number when performing addition. Doing '18' + 1 raises a TypeError.",
        render: () => `
          <div class="p-3 rounded-xl bg-rose-950/40 border border-rose-500/50 text-center font-mono text-xs space-y-1">
            <div class="text-rose-400 font-bold">TypeError: can only concatenate str to str, not "int"</div>
            <p class="text-[10px] text-zinc-300">Python refuses to guess whether you want '181' or 19.</p>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Explicit Conversion with int()",
        narration: "To fix this, you must explicitly call int(age). The int() function parses the ASCII digits '1' and '8' and allocates an integer 18.",
        render: () => `
          <div class="flex items-center space-x-6 py-2">
            <span class="font-mono text-purple-300 text-sm">'18'</span>
            <span class="text-cyan-400 font-mono text-sm">&rarr; int('18') &rarr;</span>
            <span class="font-mono text-emerald-300 text-lg font-bold">18</span>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Adding 1 Safely",
        narration: "Once cast, int(age) + 1 adds 18 + 1 to produce the integer 19 safely.",
        render: () => `
          <div class="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/40 font-mono text-xs text-center space-y-1">
            <div class="text-emerald-400 font-bold">int(age) + 1 &rarr; 19</div>
            <span class="text-[10px] text-zinc-400">Safe integer arithmetic</span>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Core Invariant",
        narration: "Always explicitly cast input text or strings with int() or float() before performing numerical calculations.",
        render: () => `
          <div class="p-3 bg-black/40 border border-zinc-700 rounded-lg text-center font-mono text-xs">
            Explicit is better than implicit.
          </div>
        `
      }
    ]
  }
};

// ---------------------------------------------------------------------------
// DEDICATED REMEDIAL EXPLAINER STORYBOARDS (Shown ONLY on Wrong Answers!)
// ---------------------------------------------------------------------------
const REMEDIAL_VIDEO_STORYBOARDS = {
  // Remedial for q_var_01: Math vs Programming Rebinding
  "q_var_01": {
    title: "Remedial Explainer: Why 'x = x + 1' Is NOT Math — The 2-Step CPU Sequence",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Misconception Identified",
        narration: "You treated '=' as an algebraic equation balance. In math, x cannot equal x + 1. But in Python, '=' is an assignment command, not an equation!",
        render: () => `
          <div class="p-3.5 rounded-xl bg-amber-950/40 border border-amber-500/60 text-center space-y-1.5 font-sans">
            <div class="text-amber-400 font-mono font-bold text-xs uppercase">⚠ Mental Trap Detected</div>
            <p class="text-xs text-zinc-200">
              You are thinking of <code>x = x + 1</code> as an equation to be solved. In Python, there is no equation to solve!
            </p>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: The 2-Step Mechanical Sequence",
        narration: "Here is what Python really does: Step 1) It takes the current number in x (10) and calculates 10 + 1 = 11. Step 2) It binds the name tag x to 11.",
        render: () => `
          <div class="flex flex-col items-center space-y-2 py-1 font-mono text-xs">
            <div class="p-2 rounded bg-black/50 border border-cyan-500 text-cyan-300">
              1. Compute Right Side: <code>x + 1</code> &rarr; <code>10 + 1 = 11</code>
            </div>
            <div class="text-amber-400">&darr;</div>
            <div class="p-2 rounded bg-black/50 border border-emerald-500 text-emerald-300">
              2. Rebind Label: <code>x = 11</code>
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Visual Proof in RAM",
        narration: "Notice the sequence across time: old value 10 is replaced by 11. Now answer the follow-up transfer challenge below to lock this concept in!",
        render: () => `
          <div class="flex items-center space-x-6 py-1">
            <div class="p-3 bg-[#141416] border border-zinc-700 rounded-lg text-center font-mono">
              <span class="text-[10px] text-zinc-500">Old</span>
              <div class="text-lg text-zinc-500 line-through">10</div>
            </div>
            <span class="text-cyan-400 font-mono">&rarr;</span>
            <div class="p-3.5 bg-[#141416] border border-emerald-400 rounded-xl text-center font-mono glow-box-emerald">
              <span class="text-[10px] text-emerald-400 font-bold">New x</span>
              <div class="text-2xl text-white font-bold">11</div>
            </div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Ready for Follow-up",
        narration: "Now apply this exact two-step rule to the follow-up question directly below!",
        render: () => `
          <div class="p-3 rounded-lg bg-cyan-950/30 border border-cyan-500/40 text-center font-mono text-xs">
            👇 Scroll down to answer the Follow-up Question below!
          </div>
        `
      }
    ]
  },

  // Remedial for q_var_02: Mirror Myth
  "q_var_02": {
    title: "Remedial Explainer: The Mirror Myth Debunked — Why 'b' Stays 10",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Misconception Identified",
        narration: "You assumed 'b = a' created a permanent mirror link between variables. In Python, variables are NEVER linked together!",
        render: () => `
          <div class="p-3.5 rounded-xl bg-amber-950/40 border border-amber-500/60 text-center space-y-1.5 font-sans">
            <div class="text-amber-400 font-mono font-bold text-xs uppercase">⚠ The Mirror Myth</div>
            <p class="text-xs text-zinc-200">
              <code>b = a</code> does NOT create a live cable or spreadsheet formula. It only takes a one-time photo!
            </p>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: Independent Name Tags",
        narration: "When 'b = a' runs, 'a' is 10, so 'b' receives 10. Later, when 'a = 20' runs, only 'a' moves. 'b' remains on 10.",
        render: () => `
          <div class="flex items-center space-x-6 py-2 font-mono text-xs">
            <div class="p-3 bg-[#141416] border border-cyan-500 rounded-lg text-center">
              <span class="text-cyan-300 text-[10px]">a was reassigned</span>
              <div class="text-xl text-white font-bold">20</div>
            </div>
            <div class="p-3 bg-[#141416] border border-amber-500 rounded-lg text-center">
              <span class="text-amber-300 text-[10px]">b was NOT touched</span>
              <div class="text-xl text-amber-200 font-bold">10</div>
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: Proof",
        narration: "Since no line of code reassigned 'b', 'b' is still 10. Now solve the transfer challenge below!",
        render: () => `
          <div class="p-3 bg-emerald-950/30 border border-emerald-500/40 rounded-lg font-mono text-xs text-center text-emerald-300">
            ✓ Result: b is 10!
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Next Action",
        narration: "Complete the follow-up question below to prove you understand reference snapshots!",
        render: () => `
          <div class="p-3 rounded-lg bg-cyan-950/30 border border-cyan-500/40 text-center font-mono text-xs">
            👇 Scroll down to answer the Follow-up Question below!
          </div>
        `
      }
    ]
  },

  // Remedial for q_var_03: Data Loss Overwrite Trap
  "q_var_03": {
    title: "Remedial Explainer: Fatal Data Loss — Why Direct 'x = y' Overwrites Data",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: Why Writing 'x = y' First Fails",
        narration: "If you write 'x = y' without saving x first, x immediately takes y's value (20), and 10 is wiped out from computer memory forever!",
        render: () => `
          <div class="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/60 text-center space-y-1.5">
            <div class="text-rose-400 font-mono font-bold text-xs uppercase">❌ Irrevocable Data Loss</div>
            <p class="text-xs text-zinc-200">
              When you do <code>x = y</code>, the value <code>10</code> inside <code>x</code> is overwritten immediately!
            </p>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: The Mandatory Buffer 'temp'",
        narration: "To prevent data loss, you MUST copy x into a temporary holding variable 'temp' first: temp = x. Now x's value is safe!",
        render: () => `
          <div class="flex items-center space-x-6 py-2 font-mono text-xs">
            <div class="p-3 bg-[#141416] border border-amber-500 rounded-lg text-center">
              <span class="text-amber-400 text-[10px]">Holding Box</span>
              <div class="text-xl text-white font-bold">temp = 10</div>
            </div>
            <span class="text-emerald-400 text-sm">Secured before overwrite!</span>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: The 3-Step Sequence",
        narration: "Step 1: temp = x. Step 2: x = y. Step 3: y = temp. All values preserved and swapped!",
        render: () => `
          <div class="p-3 rounded-xl bg-black/40 border border-emerald-500 font-mono text-xs text-left space-y-1">
            <div>1. <span class="text-amber-300">temp = x</span>  # save 10</div>
            <div>2. <span class="text-emerald-300">x = y</span>     # overwrite x with 20</div>
            <div>3. <span class="text-cyan-300">y = temp</span>  # copy saved 10 into y</div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: Ready for Follow-up",
        narration: "Now write the 3 lines of code for the transfer variables below!",
        render: () => `
          <div class="p-3 rounded-lg bg-cyan-950/30 border border-cyan-500/40 text-center font-mono text-xs">
            👇 Scroll down to write the swap code in the Follow-up Question below!
          </div>
        `
      }
    ]
  }
};


class ConceptVideoEngine {
  constructor() {
    this.currentConcept = "py.variables";
    this.currentQuestionId = "q_var_01";
    this.isRemedial = false;
    this.sceneIndex = 0;
    this.isPlaying = false;
    this.timer = null;
    this.speedMs = 5000;
  }

  loadStoryboard(conceptId, questionId = null, isRemedial = false) {
    this.currentConcept = conceptId || this.currentConcept;
    this.currentQuestionId = questionId || this.currentQuestionId;
    this.isRemedial = !!isRemedial;
    this.sceneIndex = 0;
    this.stop();
    this.render();
  }

  getCurrentStoryboard() {
    // 1. If remedial requested, check remedial storyboards first
    if (this.isRemedial && this.currentQuestionId && REMEDIAL_VIDEO_STORYBOARDS[this.currentQuestionId]) {
      return REMEDIAL_VIDEO_STORYBOARDS[this.currentQuestionId];
    }
    // 2. Check question-specific storyboards
    if (this.currentQuestionId && QUESTION_VIDEO_STORYBOARDS[this.currentQuestionId]) {
      return QUESTION_VIDEO_STORYBOARDS[this.currentQuestionId];
    }
    // 3. Fallback to concept-level storyboard
    return CONCEPT_VIDEO_STORYBOARDS[this.currentConcept] || CONCEPT_VIDEO_STORYBOARDS["py.variables"];
  }

  nextScene() {
    const sb = this.getCurrentStoryboard();
    if (this.sceneIndex < sb.scenes.length - 1) {
      this.sceneIndex++;
    } else {
      this.sceneIndex = 0;
    }
    this.render();
  }

  prevScene() {
    const sb = this.getCurrentStoryboard();
    if (this.sceneIndex > 0) {
      this.sceneIndex--;
    } else {
      this.sceneIndex = sb.scenes.length - 1;
    }
    this.render();
  }

  goToScene(idx) {
    const sb = this.getCurrentStoryboard();
    if (idx >= 0 && idx < sb.scenes.length) {
      this.sceneIndex = idx;
      this.render();
    }
  }

  replay() {
    this.sceneIndex = 0;
    this.play();
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
    const btn = document.getElementById("btn-video-play");
    if (btn) btn.innerText = "Pause";
    if (this.timer) clearInterval(this.timer);
    this.timer = setInterval(() => {
      this.nextScene();
    }, this.speedMs);
  }

  stop() {
    this.isPlaying = false;
    const btn = document.getElementById("btn-video-play");
    if (btn) btn.innerText = "Play";
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  render() {
    const sb = this.getCurrentStoryboard();
    const scene = sb.scenes[this.sceneIndex];
    this.renderedOnce = true;

    const titleEl = document.getElementById("video-player-title");
    const indicatorEl = document.getElementById("video-scene-indicator");
    const durationEl = document.getElementById("video-duration-pill");
    const viewport = document.getElementById("video-viewport");
    const narrationEl = document.getElementById("video-narration-text");
    const scrubberStrip = document.getElementById("video-scrubber-strip");

    if (titleEl) {
      if (this.isRemedial) {
        titleEl.innerHTML = `<span class="text-amber-400 font-bold flex items-center space-x-1.5"><span>🎬</span><span>Remedial Explainer:</span></span> <span class="text-zinc-200">${sb.title}</span>`;
      } else {
        titleEl.innerHTML = `<span class="text-cyan-400 font-medium">Concept Explainer:</span> <span class="text-white">${sb.title}</span>`;
      }
    }
    if (indicatorEl) indicatorEl.innerText = `Scene ${this.sceneIndex + 1} of ${sb.scenes.length}`;
    if (durationEl) durationEl.innerText = sb.duration;
    if (narrationEl) narrationEl.innerText = scene.narration;

    const badgeColor = this.isRemedial
      ? 'text-amber-400/90 bg-amber-950/60 border border-amber-800/60'
      : 'text-cyan-400/80 bg-cyan-950/40 border border-cyan-800/40';

    if (viewport) {
      viewport.innerHTML = `
        <div class="scene-enter flex flex-col items-center justify-center w-full h-full space-y-3 p-2">
          <div class="text-[11px] font-mono ${badgeColor} uppercase tracking-widest px-3 py-0.5 rounded-full">
            ${scene.title}
          </div>
          <div class="w-full flex items-center justify-center">
            ${scene.render()}
          </div>
        </div>
      `;
    }

    if (scrubberStrip) {
      const activeColor = this.isRemedial ? 'w-8 bg-amber-400 shadow-sm shadow-amber-400/50' : 'w-8 bg-cyan-400 shadow-sm shadow-cyan-400/50';
      scrubberStrip.innerHTML = sb.scenes.map((s, idx) => {
        const isCurrent = idx === this.sceneIndex;
        return `
          <button onclick="videoEngine.goToScene(${idx})"
            title="${s.title}"
            class="scrubber-segment h-2 rounded-full transition-all ${isCurrent ? activeColor : (idx < this.sceneIndex ? 'w-4 bg-zinc-600' : 'w-4 bg-zinc-800')}">
          </button>
        `;
      }).join("");
    }
  }
}

// Global Video Engine Instance
const videoEngine = new ConceptVideoEngine();
window.videoEngine = videoEngine;

// Auto-render initial scene on DOM load
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      videoEngine.loadStoryboard("py.variables");
    }, 150);
  });
}
