"""
ASCII Memory State Visualizer:
Renders physical memory boxes, slot cartons, and frame-by-frame memory transitions
so learners can visually see how variables and data structures exist in RAM.
"""
from typing import Dict, Any, List, Optional


class MemoryStateVisualizer:
    """ASCII Visualizer for computer memory states and transitions."""

    @staticmethod
    def render_variable_boxes(
        variables: Dict[str, Any],
        title: str = "COMPUTER MEMORY (RAM)",
        highlight_var: Optional[str] = None,
    ) -> str:
        """Render a physical diagram of variables as labeled storage boxes."""
        if not variables:
            return (
                "+-------------------------------------------------------------+\n"
                f"|  {title.center(57)}  |\n"
                "+-------------------------------------------------------------+\n"
                "|  (Memory is currently empty)                               |\n"
                "+-------------------------------------------------------------+"
            )

        width = 62
        lines = [
            "+" + "-" * (width - 2) + "+",
            f"|  {title.center(width - 6)}  |",
            "+" + "-" * (width - 2) + "+",
            "|                                                           |",
        ]

        for name, val in variables.items():
            val_repr = repr(val) if isinstance(val, str) else str(val)
            if len(val_repr) > 24:
                val_repr = val_repr[:21] + "..."
            tag = " [UPDATED]" if name == highlight_var else ""
            line_content = f"   [ Box: {name:<8} ] ---------> ( {val_repr:<16} ){tag}"
            lines.append(f"| {line_content:<58}|")

        lines.append("|                                                           |")
        lines.append("+" + "-" * (width - 2) + "+")
        return "\n".join(lines)

    @staticmethod
    def render_swap_transition(v1: str = "x", v2: str = "y", temp_var: str = "temp") -> str:
        """Render the complete 3-step physical cup/box swap movie."""
        return (
            "===============================================================\n"
            "   3-STEP MEMORY MOVIE: SWAPPING VARIABLES WITHOUT DATA LOSS   \n"
            "===============================================================\n"
            " INITIAL STATE:\n"
            f"   [ Box: {v1} ] ---------> ( 10 )\n"
            f"   [ Box: {v2} ] ---------> ( 20 )\n"
            f"   [ Box: {temp_var} ] ------> ( Empty / None )\n"
            "\n"
            f" STEP 1: {temp_var} = {v1}  (Save {v1}'s value into holding box)\n"
            f"   [ Box: {v1} ] ---------> ( 10 )\n"
            f"   [ Box: {v2} ] ---------> ( 20 )\n"
            f"   [ Box: {temp_var} ] ------> ( 10 )  <-- [Copied]\n"
            "\n"
            f" STEP 2: {v1} = {v2}  (Copy {v2}'s value into {v1})\n"
            f"   [ Box: {v1} ] ---------> ( 20 )  <-- [Overwritten safely]\n"
            f"   [ Box: {v2} ] ---------> ( 20 )\n"
            f"   [ Box: {temp_var} ] ------> ( 10 )\n"
            "\n"
            f" STEP 3: {v2} = {temp_var}  (Move saved value into {v2})\n"
            f"   [ Box: {v1} ] ---------> ( 20 )  [SWAPPED!]\n"
            f"   [ Box: {v2} ] ---------> ( 10 )  [SWAPPED!]\n"
            f"   [ Box: {temp_var} ] ------> ( 10 )  [Used temporary holder]\n"
            "==============================================================="
        )

    @staticmethod
    def render_list_carton(
        items: List[Any],
        list_name: str = "my_list",
        title: str = "LIST COMPARTMENTS (INDEXED FROM 0)",
    ) -> str:
        """Render a list as an ice cube tray / egg carton with numbered slots."""
        if not items:
            return f"[{list_name} is empty: []]"

        slot_headers = []
        slot_values = []
        for idx, item in enumerate(items):
            item_str = repr(item) if isinstance(item, str) else str(item)
            if len(item_str) > 10:
                item_str = item_str[:8] + ".."
            slot_headers.append(f" Slot [{idx}] ")
            slot_values.append(f"  {item_str:<8} ")

        divider = "+-" + "-+-".join("-" * len(h) for h in slot_headers) + "-+"
        header_row = "| " + " | ".join(slot_headers) + " |"
        value_row = "| " + " | ".join(slot_values) + " |"

        return "\n".join([
            f"\n{title}:",
            divider,
            header_row,
            divider,
            value_row,
            divider,
            f" Note: Length is {len(items)}, but indices stop at {len(items) - 1}!\n",
        ])
