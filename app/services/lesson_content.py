"""
Lesson Content Catalog:
Authoritative, highly detailed curriculum lesson definitions for all 8 Python concepts
in the Intelligent Tutoring System.
"""
from typing import Dict, Any, List


LESSONS_CATALOG: Dict[str, Dict[str, Any]] = {
    "py.variables": {
        "concept_id": "py.variables",
        "title": "Variables and Assignment Mechanics",
        "tagline": "Memory addresses, box labels, and the action-arrow '=' operator",
        "difficulty": 1,
        "prerequisites": [],
        "theory": (
            "In Python, a variable is not an algebraic equation balance; it is a labeled name-tag "
            "pointing to a discrete storage compartment in computer RAM. The assignment operator '=' "
            "is an 'action arrow' (←): Python completely evaluates the expression on the right-hand side first, "
            "allocates a heap object with a unique 64-bit memory address (id), and then binds the variable label "
            "on the left to that address. Because variables store references, swapping two variables "
            "requires a temporary holding location or Python's tuple packing syntax (a, b = b, a) to prevent "
            "overwriting and irrevocably losing data."
        ),
        "code_example": (
            "# 1. Variable Assignment creates a value in RAM and binds a label\n"
            "score = 100            # Address 0x7ffe10: int 100\n"
            "bonus = 25             # Address 0x7ffe18: int 25\n"
            "\n"
            "# 2. Rebinding evaluates right-side first, then rebinds the label\n"
            "score = score + bonus  # Fetches 100 & 25 -> computes 125 -> binds 'score' to 125\n"
            "\n"
            "# 3. Safe 3-Step Swap using a temporary holding box\n"
            "temp = score           # Step 1: Copy score reference to holding box\n"
            "score = bonus          # Step 2: Overwrite score with bonus\n"
            "bonus = temp           # Step 3: Move saved value from temp into bonus"
        ),
        "analogy": {
            "name": "Warehouse Boxes with Sticky Labels & The 3-Cup Swap",
            "metaphor": (
                "Think of computer RAM as a warehouse of storage compartments. A variable name is a sticky label "
                "attached to a box. The '=' sign is not an algebraic equation scale; it is an action arrow (←) that calculates "
                "the value on the right first and puts it into the box on the left. If you have two full cups (Milk in Cup A, Juice in Cup B) "
                "and write 'A = B', you pour Juice directly into Cup A—destroying the Milk forever! You must use a third empty cup (Temp) "
                "as a temporary buffer to preserve Cup A's value before transferring Cup B."
            ),
            "trap": "Direct Swap Overwrite: Believing 'x = y; y = x' swaps values. In reality, the first line 'x = y' immediately overwrites and destroys x's original value (both become 20!). A temporary holding variable 'temp' is mandatory."
        },
        "misconceptions": [
            {
                "name": "Equality vs Assignment",
                "mistake": "Believing 'a = b' creates a permanent mirror between variables.",
                "correction": "Assignment is a one-time copy of the object reference at that exact millisecond."
            },
            {
                "name": "Direct Swap Overwrite",
                "mistake": "Writing 'x = y; y = x' expecting a swap.",
                "correction": "Writing 'x = y' immediately destroys x's original value. A temporary variable or tuple packing is mandatory."
            }
        ],
        "animation_id": "variables_swap",
        "diagnostic_prompt": "If x = 10 and y = 20, why does running 'x = y; y = x' fail to swap the values, and what is the resulting state of memory?",
        "rubric_keywords": ["overwrite", "destroy", "lost", "20", "temp", "temporary"]
    },
    "py.data_types": {
        "concept_id": "py.data_types",
        "title": "Primitive Data Types and Memory Footprint",
        "tagline": "Integers, Floats, Strings, Booleans, and Explicit Type Casting",
        "difficulty": 1,
        "prerequisites": ["py.variables"],
        "theory": (
            "Every object in Python possesses three immutable properties: an Identity (its memory address), "
            "a Type (which defines the valid operations and internal binary representation), and a Value. "
            "Python's four foundational primitives are: int (arbitrary-precision integers, ~28 bytes), "
            "float (64-bit IEEE 754 floating point numbers, ~24 bytes), str (immutable sequences of UTF-8/Unicode characters), "
            "and bool (True or False, a specialized int subclass). Python is strongly typed: it will never implicitly coerce "
            "a string '18' into a number when performing arithmetic; explicit casting via int('18') or float('3.14') is required."
        ),
        "code_example": (
            "# Primitives in Memory\n"
            "count = 42             # <class 'int'> -> 28 bytes\n"
            "price = 19.99          # <class 'float'> -> 24 bytes IEEE 754\n"
            "tag = 'PYTHON'         # <class 'str'> -> immutable text tape\n"
            "is_active = True       # <class 'bool'> -> boolean flag\n"
            "\n"
            "# Strong Typing & Explicit Casting\n"
            "user_input = '100'     # String from console or file\n"
            "# total = user_input + 5  # FAILS! TypeError: can only concatenate str to str\n"
            "total = int(user_input) + 5  # 105 (int)"
        ),
        "analogy": {
            "name": "Counting Marbles vs Alphabet Stamps",
            "metaphor": (
                "Integers and Floats are physical counting marbles you can weigh and add on a scale. Strings are "
                "characters printed on a paper tape with alphabet stamps. Even if you stamp the digits '100' on the tape, "
                "it remains a piece of paper tape. You cannot drop a paper tape onto an arithmetic scale with marbles—you "
                "must run the tape through an int() scanner that counts out 100 real marbles."
            ),
            "trap": "Assuming '10' + 5 will automatically result in 15 like in loosely-typed languages like JavaScript."
        },
        "misconceptions": [
            {
                "name": "Implicit String Coercion",
                "mistake": "Assuming print('Result: ' + 5) works without str(5).",
                "correction": "Python requires explicit str() casting when concatenating non-strings."
            },
            {
                "name": "Float Representation Exactness",
                "mistake": "Expecting 0.1 + 0.2 == 0.3 to be exactly True.",
                "correction": "Binary IEEE 754 floating points have small rounding approximations (0.30000000000000004)."
            }
        ],
        "animation_id": "data_types_transformer",
        "diagnostic_prompt": "Explain why Python raises a TypeError if you try to evaluate '15' + 5, and describe how explicit casting resolves it.",
        "rubric_keywords": ["str", "int", "TypeError", "explicit", "cast", "convert"]
    },
    "py.operators_expressions": {
        "concept_id": "py.operators_expressions",
        "title": "Operators, Precedence, and Division Mechanics",
        "tagline": "True division (/), floor division (//), modulo (%), and expression stacks",
        "difficulty": 2,
        "prerequisites": ["py.variables", "py.data_types"],
        "theory": (
            "Operators compute new values from operands. In Python 3, division possesses strict mathematical semantics: "
            "the single-slash operator '/' always performs true division and returns a float object (e.g. 7 / 2 -> 3.5). "
            "The double-slash operator '//' performs floor division: it divides operands and rounds down towards "
            "negative infinity (math.floor), returning an int when both operands are integers (e.g. 7 // 2 -> 3, but -7 // 2 -> -4!). "
            "The modulo operator '%' yields the division remainder such that (b * (a // b)) + (a % b) == a."
        ),
        "code_example": (
            "# True vs Floor Division\n"
            "a, b = 7, 2\n"
            "print(a / b)    # 3.5  (always returns float)\n"
            "print(a // b)   # 3    (floor rounded towards -infinity)\n"
            "\n"
            "# Negative Floor Division Surprise\n"
            "print(-7 // 2)  # -4   (because -3.5 rounded DOWN is -4!)\n"
            "print(7 % 2)    # 1    (remainder clock)"
        ),
        "analogy": {
            "name": "Precision Knife vs Whole Box Packing",
            "metaphor": (
                "True division '/' is a precision chef's knife that cuts pizzas into fractional slices (yielding decimals). "
                "Floor division '//' is a packing warehouse that only ships complete, sealed shipping boxes—any leftover "
                "fraction is chopped off. Modulo '%' is the scrap bin that collects whatever loose items didn't fit into "
                "a full box."
            ),
            "trap": "Expecting -7 // 2 to be -3 (truncation toward zero). Python always floors towards negative infinity."
        },
        "misconceptions": [
            {
                "name": "Integer Division in Python 3",
                "mistake": "Assuming 4 / 2 returns the integer 2.",
                "correction": "In Python 3, '/' always produces a float (2.0)."
            },
            {
                "name": "Negative Floor Direction",
                "mistake": "Thinking floor division simply drops the decimal digits.",
                "correction": "Floor means largest integer less than or equal to the quotient. For -3.5, the floor is -4."
            }
        ],
        "animation_id": "operators_precedence",
        "diagnostic_prompt": "What are the exact evaluated results of 7 / 2, 7 // 2, and -7 // 2 in Python 3, and why does -7 // 2 evaluate to -4?",
        "rubric_keywords": ["3.5", "3", "-4", "float", "floor", "negative infinity", "round down"]
    },
    "py.conditionals": {
        "concept_id": "py.conditionals",
        "title": "Conditional Branching and Short-Circuit Logic",
        "tagline": "Decision trees, if-elif-else ladders, and Boolean short-circuiting",
        "difficulty": 2,
        "prerequisites": ["py.operators_expressions"],
        "theory": (
            "Conditional statements direct program execution along divergent logical pathways based on the truth value "
            "of boolean expressions. In Python, blocks are defined strictly through whitespace indentation (PEP 8 standard: 4 spaces). "
            "An if-elif-else chain tests guards sequentially from top to bottom; the first guard that evaluates to True executes "
            "its body and the remaining branches are skipped entirely. Python features short-circuit evaluation: in 'A and B', "
            "if A evaluates to False, B is never evaluated at all; in 'A or B', if A evaluates to True, B is never evaluated."
        ),
        "code_example": (
            "# Conditional Guard Ladder\n"
            "score = 85\n"
            "if score >= 90:\n"
            "    grade = 'A'\n"
            "elif score >= 80:     # Evaluated only if score < 90\n"
            "    grade = 'B'       # Matches 85!\n"
            "else:\n"
            "    grade = 'C'\n"
            "\n"
            "# Short-Circuit Guard: avoids ZeroDivisionError\n"
            "items = []\n"
            "if len(items) > 0 and (total / len(items)) > 10:\n"
            "    print('Average exceeds 10')  # len(items) is 0 -> stops immediately!"
        ),
        "analogy": {
            "name": "Railway Track Switches & Security Gate Bypasses",
            "metaphor": (
                "A computer's instruction pointer is a locomotive traveling down a rail line. An 'if' condition is a track switch. "
                "If the switch flag is Green (True), the train takes the high branch. If Red (False), it stays on the mainline. "
                "In an 'and' guard, if the first security gate fails, the inspector immediately rejects the pass without "
                "wasting time checking second or third gates."
            ),
            "trap": "Writing multiple independent 'if' statements when an 'elif' ladder was intended, causing duplicate executions."
        },
        "misconceptions": [
            {
                "name": "Parallel 'if' vs Cascading 'elif'",
                "mistake": "Using 'if' for every condition expecting only one to execute.",
                "correction": "Every standalone 'if' is evaluated unconditionally. 'elif' binds to the preceding check."
            },
            {
                "name": "Truthy Evaluation of Non-Booleans",
                "mistake": "Thinking only True and False can be passed to an 'if'.",
                "correction": "Empty containers ([], {}, ''), 0, and None evaluate to False (falsy); non-empty objects evaluate to True."
            }
        ],
        "animation_id": "conditionals_railway",
        "diagnostic_prompt": "Explain how short-circuit evaluation in 'if count > 0 and (total / count) > 5' protects your program from crashing.",
        "rubric_keywords": ["short-circuit", "ZeroDivisionError", "crash", "left-to-right", "stops", "skip"]
    },
    "py.lists_sequences": {
        "concept_id": "py.lists_sequences",
        "title": "Lists, Zero-Based Indexing, and Slicing",
        "tagline": "Contiguous pointer arrays, negative offsets, and memory slicing [start:stop:step]",
        "difficulty": 2,
        "prerequisites": ["py.variables", "py.data_types"],
        "theory": (
            "A Python list is a mutable dynamic array of object references. Unlike static arrays in C, Python lists "
            "store pointers to heap objects, allowing heterogeneous data types. Elements reside in sequential order "
            "indexed starting at 0 (representing the offset from the array's starting memory address). Negative indices "
            "count backwards from the end (list[-1] is the final element). Slicing list[start:stop:step] produces a "
            "shallow copy containing elements from 'start' up to (but strictly excluding) 'stop', advancing by 'step'."
        ),
        "code_example": (
            "# Lists and Memory Offsets\n"
            "fruits = ['apple', 'banana', 'cherry', 'date']\n"
            "# Index:     0         1         2         3\n"
            "# Offset:   -4        -3        -2        -1\n"
            "\n"
            "print(fruits[0])        # 'apple' (0 offset from start)\n"
            "print(fruits[-1])       # 'date'  (first from the right)\n"
            "\n"
            "# Slicing creates a new shallow copy\n"
            "middle = fruits[1:3]    # ['banana', 'cherry'] (stop=3 is excluded)\n"
            "reversed_f = fruits[::-1] # ['date', 'cherry', 'banana', 'apple']"
        ),
        "analogy": {
            "name": "Apartment Mailboxes & Stencil Windows",
            "metaphor": (
                "Imagine a row of apartment mailboxes starting at the lobby door. Index 0 means 'take 0 steps from the entrance' "
                "(the very first mailbox). Index 1 means 'step 1 door down'. Index -1 means 'tap on the back wall mailbox'. "
                "Slicing [1:3] is like placing a cardboard stencil cutout over boxes 1 and 2—box 3 is covered by the edge."
            ),
            "trap": "Believing slice numbers are inclusive of the end boundary (expecting [1:3] to take 3 items instead of 2)."
        },
        "misconceptions": [
            {
                "name": "One-Based Indexing Fallacy",
                "mistake": "Thinking fruits[1] retrieves the first item.",
                "correction": "In computer memory, index 0 is the starting base element. Index 1 is the second element."
            },
            {
                "name": "Inclusive Slice Stop",
                "mistake": "Assuming numbers[0:5] includes index 5.",
                "correction": "The stop index is always half-open: [start, stop) excludes index 5 (takes indices 0, 1, 2, 3, 4)."
            }
        ],
        "animation_id": "lists_slicing",
        "diagnostic_prompt": "For items = [10, 20, 30, 40, 50], what are items[0], items[-1], and items[1:4], and why is the element at index 4 excluded from the slice?",
        "rubric_keywords": ["10", "50", "[20, 30, 40]", "exclusive", "half-open", "stop"]
    },
    "py.for_loops": {
        "concept_id": "py.for_loops",
        "title": "For Loops, Iterators, and Sequence Traversal",
        "tagline": "The iterator protocol (__iter__, __next__), range(), and deterministic iteration",
        "difficulty": 3,
        "prerequisites": ["py.conditionals", "py.lists_sequences"],
        "theory": (
            "Python's 'for' loop is fundamentally a 'for-each' loop built on the iterator protocol. When Python executes "
            "'for item in iterable:', it invokes iter(iterable) to construct an iterator object, and then repeatedly calls "
            "next(iterator) on each cycle until a StopIteration exception is raised internally. The loop variable 'item' is "
            "re-bound to the next sequence object on every turn. The range(start, stop, step) built-in yields an arithmetic "
            "progression without pre-allocating the entire sequence in RAM, maintaining O(1) memory efficiency."
        ),
        "code_example": (
            "# Iterating directly over items\n"
            "total = 0\n"
            "prices = [12, 45, 8, 20]\n"
            "for p in prices:        # p is rebound on each step\n"
            "    total += p\n"
            "\n"
            "# Iterating with range for counted steps\n"
            "for i in range(1, 4):   # Produces 1, 2, 3 (4 is excluded)\n"
            "    print(f'Round {i}')"
        ),
        "analogy": {
            "name": "Conveyor Belt with Inspection Station",
            "metaphor": (
                "Think of a factory conveyor belt. The list is the tray of parts waiting in line. The 'for' loop is a conveyor "
                "motor that steps forward one click per cycle. On each click, one part drops into your inspection hands "
                "(the variable 'item'). You do your work, and the next click drops the next part until the belt runs empty."
            ),
            "trap": "Mutating (adding or removing items from) a list while iterating over it, causing skipped elements."
        },
        "misconceptions": [
            {
                "name": "Modifying List During Iteration",
                "mistake": "Using 'for x in my_list: my_list.remove(x)' to delete items.",
                "correction": "Removing elements shifts internal list pointers, causing the iterator to skip adjacent items."
            },
            {
                "name": "Range Pre-Allocation Myth",
                "mistake": "Thinking range(1000000) consumes millions of bytes of RAM.",
                "correction": "range is a lazy generator-like sequence object that computes values on demand in constant memory."
            }
        ],
        "animation_id": "for_loops_conveyor",
        "diagnostic_prompt": "Describe what happens behind the scenes when Python runs 'for x in [10, 20, 30]:' in terms of the loop pointer and StopIteration.",
        "rubric_keywords": ["iter", "next", "pointer", "rebind", "StopIteration", "sequence"]
    },
    "py.while_loops": {
        "concept_id": "py.while_loops",
        "title": "While Loops, Sentinel Flags, and Loop Termination",
        "tagline": "Condition-controlled iteration, sentinel gates, and avoiding infinite execution",
        "difficulty": 3,
        "prerequisites": ["py.conditionals"],
        "theory": (
            "A 'while' loop repeatedly executes its code block as long as its controlling predicate condition remains True. "
            "Unlike a 'for' loop which iterates over a predetermined sequence, a 'while' loop is indefinite: the number of iterations "
            "is governed by dynamic runtime state. To prevent catastrophic infinite loops (which consume 100% CPU thread cycles and hang), "
            "the loop body MUST modify one or more state variables affecting the condition towards false, use an explicit 'break' sentinel, "
            "or hit an external event threshold."
        ),
        "code_example": (
            "# Sentinel Condition Pattern\n"
            "attempts = 0\n"
            "max_attempts = 3\n"
            "authenticated = False\n"
            "\n"
            "while not authenticated and attempts < max_attempts:\n"
            "    attempts += 1\n"
            "    # Simulated auth check\n"
            "    if attempts == 2:\n"
            "        authenticated = True\n"
            "\n"
            "print('Auth status:', authenticated)"
        ),
        "analogy": {
            "name": "Security Guard Gate & Countdown Meter",
            "metaphor": (
                "A while loop is a gated tollbooth. Before EVERY car passes through the gate, the guard checks the toll receipt "
                "(the condition). If valid, the car drives through, and your ticket gets punched. If your ticket punches run out, "
                "the gate closes permanently. If you forget to punch the ticket, the guard lets you loop around forever!"
            ),
            "trap": "Forgetting to increment the loop counter inside the loop body, creating an infinite loop."
        },
        "misconceptions": [
            {
                "name": "Continuous Mid-Loop Checking",
                "mistake": "Assuming the loop exits the very instant a condition becomes False halfway through the block.",
                "correction": "The while condition is evaluated ONLY at the top of the loop (or start of next iteration), not mid-statement."
            },
            {
                "name": "Unbounded Loop Hang",
                "mistake": "Using 'while count != 10:' when incrementing by steps of 2 starting at odd numbers.",
                "correction": "Equality guards can skip past the target (1, 3, 5... 9, 11). Use boundary inequalities like '< 10'."
            }
        ],
        "animation_id": "while_loops_gate",
        "diagnostic_prompt": "What causes an infinite loop in a while statement, and what two distinct mechanisms can guarantee its safe termination?",
        "rubric_keywords": ["condition", "True", "counter", "increment", "break", "sentinel", "terminate"]
    },
    "py.functions": {
        "concept_id": "py.functions",
        "title": "Functions, Call Stacks, and Scope Boundaries",
        "tagline": "Stack frames, parameter passing by object reference, local vs global namespaces, and return values",
        "difficulty": 3,
        "prerequisites": ["py.variables", "py.conditionals", "py.lists_sequences"],
        "theory": (
            "Functions encapsulate reusable subroutines. When a function is called, the Python runtime allocates a new "
            "Call Stack Frame containing local variable bindings, argument values, and an instruction return pointer. "
            "Arguments in Python are passed by 'assignment' (call by object reference): the local parameter label is bound "
            "to the caller's heap object. Local variables defined inside the function cannot be accessed from outer scopes (LEGB rule: "
            "Local -> Enclosing -> Global -> Built-in). When the function encounters 'return expr', the evaluated object is yielded "
            "back to the calling context, and the stack frame is popped off memory and deallocated."
        ),
        "code_example": (
            "# Pure Function with Stack Frame\n"
            "def calculate_tax(subtotal: float, rate: float = 0.08) -> float:\n"
            "    # 'subtotal' and 'rate' are local to this frame\n"
            "    tax_amount = subtotal * rate   # Local variable\n"
            "    return round(tax_amount, 2)    # Returned to caller\n"
            "\n"
            "# Invocation pushes stack frame, returns value, pops frame\n"
            "order_total = 150.0\n"
            "tax = calculate_tax(order_total)  # tax receives 12.0\n"
            "# print(tax_amount)               # NameError! tax_amount only existed inside frame"
        ),
        "analogy": {
            "name": "Sealed Laboratory Room & Input/Output Mail Slots",
            "metaphor": (
                "A function is a soundproof, sealed laboratory room with only two openings: an 'Input Mail Slot' (arguments) "
                "and an 'Output Chute' (return value). When you invoke the function, the lab door locks, workers inside "
                "use temporary whiteboards (local variables), compute the result, slide the answer out the Output Chute, "
                "and erase all whiteboards before shutting down. People outside in the hallway cannot see through the walls."
            ),
            "trap": "Believing printing a value ('print(x)') is the same as returning it ('return x'). Print only displays text on screen; return delivers data to the program."
        },
        "misconceptions": [
            {
                "name": "Print vs Return Confusion",
                "mistake": "Using print() instead of return and wondering why result = func() has value None.",
                "correction": "Functions without an explicit return statement implicitly return None. print() merely writes to stdout."
            },
            {
                "name": "Global Variable Mutation",
                "mistake": "Attempting to reassign a global variable inside a function without the 'global' keyword.",
                "correction": "Assigning to a variable inside a function makes it local to that frame, shadowing outer variables."
            }
        ],
        "animation_id": "functions_call_stack",
        "diagnostic_prompt": "Explain the difference between 'print(result)' and 'return result' inside a function, and describe what happens to local variables when the function returns.",
        "rubric_keywords": ["print", "return", "stdout", "None", "stack", "pop", "deallocate", "scope", "local"]
    }
}
