"""Tests for the ASCII Memory State Visualizer."""
from app.services.memory_visualizer import MemoryStateVisualizer


def test_render_empty_variables():
    output = MemoryStateVisualizer.render_variable_boxes({})
    assert "COMPUTER MEMORY (RAM)" in output
    assert "Memory is currently empty" in output


def test_render_variable_boxes():
    variables = {
        "x": 10,
        "name": "Alice",
        "long_val": "abcdefghijklmnopqrstuvwxyz1234567890",
    }
    output = MemoryStateVisualizer.render_variable_boxes(variables, highlight_var="x")
    assert "Box: x" in output
    assert "10" in output
    assert "[UPDATED]" in output
    assert "Box: name" in output
    assert "'Alice'" in output
    assert "..." in output  # truncated


def test_render_swap_transition():
    output = MemoryStateVisualizer.render_swap_transition("a", "b", "temp")
    assert "3-STEP MEMORY MOVIE" in output
    assert "INITIAL STATE:" in output
    assert "STEP 1: temp = a" in output
    assert "STEP 2: a = b" in output
    assert "STEP 3: b = temp" in output
    assert "SWAPPED!" in output


def test_render_list_carton():
    items = ["cat", "dog", "elephant"]
    output = MemoryStateVisualizer.render_list_carton(items, list_name="animals")
    assert "Slot [0]" in output
    assert "Slot [1]" in output
    assert "Slot [2]" in output
    assert "cat" in output
    assert "dog" in output
    assert "Length is 3, but indices stop at 2" in output


def test_render_list_carton_empty():
    output = MemoryStateVisualizer.render_list_carton([], list_name="empty_list")
    assert "empty_list is empty: []" in output
