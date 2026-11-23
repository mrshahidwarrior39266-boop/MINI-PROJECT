/**
 * Codex Tutor — Concept Animated Explainer Video Engine
 * Provides rich, easy-to-understand 4-scene animated video presentations
 * for every concept before introducing the Socratic question.
 */

const CONCEPT_VIDEO_STORYBOARDS = {
  "py.variables": {
    title: "Animated Explainer: Variables, Memory Boxes & Pointer References",
    duration: "0:45",
    scenes: [
      {
        id: 1,
        title: "Scene 1: The Warehouse Box Metaphor",
        narration: "Think of your computer's RAM as a warehouse full of storage boxes. A variable name is not a balance scale—it is just a yellow sticky label slapped on a box.",
        render: () => `
          <div class="flex items-center justify-center space-x-8 anim-float">
            <div class="flex flex-col items-center p-4 rounded-xl bg-[#1c1c22] border border-cyan-500/60 shadow-lg shadow-cyan-950/30">
              <span class="text-[10px] font-mono text-cyan-300 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-700/60 mb-2">STICKY LABEL: "score"</span>
              <div class="w-24 h-24 rounded-xl bg-[#121216] border border-zinc-700 flex items-center justify-center text-3xl font-mono text-white font-bold">
                100
              </div>
              <span class="text-[10px] text-zinc-500 font-mono mt-2">RAM Box 0x7ffe10</span>
            </div>
            <div class="text-2xl text-zinc-600 font-mono">&larr;</div>
            <div class="p-3 bg-zinc-900/90 rounded-lg border border-zinc-800 text-xs font-mono text-zinc-300 max-w-xs leading-relaxed">
              <span class="text-amber-400 font-bold">Rule:</span> '=' is an ACTION ARROW. It puts the item on the right into the box on the left.
            </div>
          </div>
        `
      },
      {
        id: 2,
        title: "Scene 2: How Python Evaluates Assignment",
        narration: "When Python sees 'score = score + 25', it completely evaluates the right-hand side first (100 + 25 = 125), and then rebinds the label 'score' to the new value.",
        render: () => `
          <div class="flex flex-col items-center space-y-4">
            <div class="px-4 py-1.5 rounded-lg bg-zinc-900 border border-zinc-700 font-mono text-xs text-amber-300">
              score = score + 25   # Step 1: Reads 100 &rarr; Computes 125 &rarr; Rebinds
            </div>
            <div class="flex items-center space-x-6">
              <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border border-zinc-700">
                <span class="text-[10px] font-mono text-zinc-500">Old Value</span>
                <span class="text-xl font-mono text-zinc-500 line-through mt-1">100</span>
              </div>
              <span class="text-xl text-cyan-400">&rarr;</span>
              <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border border-emerald-400 animate-pulse">
                <span class="text-[10px] font-mono text-emerald-400">New Value in RAM</span>
                <span class="text-2xl font-mono text-white font-bold mt-1">125</span>
              </div>
            </div>
          </div>
        `
      },
      {
        id: 3,
        title: "Scene 3: The Fatal Overwrite Trap & 3-Step Cup Swap",
        narration: "If you have two full cups (Milk in Cup A, Juice in Cup B) and write 'a = b', Cup A is overwritten and the Milk is destroyed forever! You MUST use a temporary holding cup 'temp'.",
        render: () => `
          <div class="grid grid-cols-3 gap-6 w-full max-w-md">
            <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border border-cyan-500/60">
              <span class="text-[10px] font-mono text-zinc-400">Cup A (Milk)</span>
              <div class="text-2xl font-mono text-cyan-300 mt-2">10</div>
              <span class="text-[10px] text-zinc-500 mt-1">0x7ffe10</span>
            </div>
            <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border border-emerald-500/60">
              <span class="text-[10px] font-mono text-zinc-400">Cup B (Juice)</span>
              <div class="text-2xl font-mono text-emerald-300 mt-2">20</div>
              <span class="text-[10px] text-zinc-500 mt-1">0x7ffe18</span>
            </div>
            <div class="flex flex-col items-center p-3 rounded-lg bg-[#18181c] border border-amber-500/60">
              <span class="text-[10px] font-mono text-amber-400">Holding Cup 'temp'</span>
              <div class="text-2xl font-mono text-amber-300 mt-2">10</div>
              <span class="text-[10px] text-zinc-500 mt-1">Buffer</span>
            </div>
          </div>
        `
      },
      {
        id: 4,
        title: "Scene 4: The Golden Invariant",
        narration: "Golden Rule: 'b = a' copies the address at that exact millisecond. Changing 'a' later NEVER alters 'b'. You are now ready to solve the diagnostic challenge below!",
        render: () => `
          <div class="p-5 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center space-y-2 max-w-md">
            <div class="text-xs font-mono text-emerald-400 uppercase font-bold tracking-wider">Concept Invariant Verified</div>
            <p class="text-xs text-zinc-200 leading-relaxed">
              Variables store memory references. To swap values safely without data loss:
              <br><code class="text-cyan-300 font-mono font-bold">temp = a; a = b; b = temp</code>
            </p>
            <div class="pt-2 text-[11px] font-mono text-zinc-400">
              Ready! Scroll down to the Socratic Checkpoint below.
            </div>
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


class ConceptVideoEngine {
  constructor() {
    this.currentConcept = "py.variables";
    this.sceneIndex = 0;
    this.isPlaying = false;
    this.timer = null;
    this.speedMs = 5000;
  }

  loadStoryboard(conceptId) {
    this.currentConcept = conceptId;
    this.sceneIndex = 0;
    this.stop();
    this.render();
  }

  getCurrentStoryboard() {
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

    const titleEl = document.getElementById("video-player-title");
    const indicatorEl = document.getElementById("video-scene-indicator");
    const durationEl = document.getElementById("video-duration-pill");
    const viewport = document.getElementById("video-viewport");
    const narrationEl = document.getElementById("video-narration-text");
    const scrubberStrip = document.getElementById("video-scrubber-strip");

    if (titleEl) titleEl.innerText = sb.title;
    if (indicatorEl) indicatorEl.innerText = `Scene ${this.sceneIndex + 1} of ${sb.scenes.length}`;
    if (durationEl) durationEl.innerText = sb.duration;
    if (narrationEl) narrationEl.innerText = scene.narration;

    if (viewport) {
      viewport.innerHTML = `
        <div class="flex flex-col items-center justify-center w-full h-full space-y-4">
          <div class="text-[11px] font-mono text-codex-muted uppercase tracking-wider">
            ${scene.title}
          </div>
          <div class="w-full flex items-center justify-center">
            ${scene.render()}
          </div>
        </div>
      `;
    }

    if (scrubberStrip) {
      scrubberStrip.innerHTML = sb.scenes.map((s, idx) => {
        const isCurrent = idx === this.sceneIndex;
        return `
          <button onclick="videoEngine.goToScene(${idx})"
            title="${s.title}"
            class="scrubber-segment h-2 rounded-full transition-all ${isCurrent ? 'w-8 bg-cyan-400' : (idx < this.sceneIndex ? 'w-4 bg-zinc-600' : 'w-4 bg-zinc-800')}">
          </button>
        `;
      }).join("");
    }
  }
}

// Global Video Engine Instance
const videoEngine = new ConceptVideoEngine();
