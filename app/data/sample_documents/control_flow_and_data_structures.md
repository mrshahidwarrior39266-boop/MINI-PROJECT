# Advanced Python Mechanics: Control Flow and Sequences

This textbook chapter covers essential runtime patterns in Python, focusing on execution order and memory binding.

## Iteration with While Loops and Sentinel Flags

The while statement repeatedly evaluates a boolean expression before executing its indented loop body. If the condition begins as False, the loop body is bypassed entirely. When designing loops, always ensure an update step (such as incrementing a counter or toggling a sentinel flag) occurs within the loop body. Without a progress mechanism, the loop creates an unbounded infinite loop that exhausts CPU resources and prevents subsequent code execution.

```python
count = 0
while count < 5:
    print(f"Current iteration: {count}")
    count = count + 1
```

### Breaking Loops Cleanly with Break and Continue

The break statement immediately terminates the innermost enclosing loop, skipping any remaining statements in the body and resuming execution at the statement following the loop block. In contrast, the continue statement terminates only the current iteration, immediately jumping back to evaluate the conditional expression.

## Python Lists and Sequential Memory Structures

A list in Python is an ordered, mutable sequence of object references. Unlike lower-level languages where arrays require homogeneous types and fixed dimensions, Python lists can store arbitrary objects.

```python
inventory = ["iron_sword", "health_potion", 42, True]
```

### Indexing and Zero-Based Compartments

Python sequences use zero-based indexing. The first element resides at index 0, the second at index 1, and the final element at index len(sequence) - 1. Attempting to access an index equal to or greater than the sequence length triggers an IndexError. Python also provides negative indexing, where index -1 denotes the rightmost element.

### In-Place Mutation versus Rebinding

When appending to a list using inventory.append("shield"), Python mutates the existing list object in place. The memory address bound to the variable name remains identical. In contrast, concatenating lists with inventory = inventory + ["shield"] constructs a completely new list in memory and rebinds the identifier.
