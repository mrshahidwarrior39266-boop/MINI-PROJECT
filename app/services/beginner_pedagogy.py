"""
Beginner Pedagogy Service:
Bridges the mental gap for learners with zero coding background using
real-world physical analogies, mental movies, and 'how the computer thinks' contrasts.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_ANALOGIES_FILE = DATA_DIR / "beginner_analogies.json"


class BeginnerPedagogyService:
    """Delivers zero-jargon mental models and physical analogies for all curriculum concepts."""

    def __init__(self, analogies_file: Optional[Path] = None):
        self.analogies_file = Path(analogies_file or DEFAULT_ANALOGIES_FILE)
        self.analogies: Dict[str, Dict[str, Any]] = {}
        self.load_analogies()

    def load_analogies(self) -> None:
        if self.analogies_file.exists():
            with open(self.analogies_file, "r", encoding="utf-8") as f:
                self.analogies = json.load(f)

    def get_analogy(self, concept_id: str) -> Optional[Dict[str, Any]]:
        return self.analogies.get(concept_id)

    def format_beginner_briefing(self, concept_id: str) -> str:
        """Render a zero-jargon mental model briefing for absolute beginners."""
        model = self.get_analogy(concept_id)
        if not model:
            return ""

        lines = [
            "\n" + "=" * 70,
            " ZERO-KNOWLEDGE INTUITION: HOW TO THINK ABOUT THIS (NO JARGON)",
            "=" * 70,
            f" Real-World Analogy: {model.get('real_world_analogy', '')}",
            f" Plain English     : {model.get('plain_english_concept', '')}",
            "",
            " The Beginner Trap (How Humans Think vs. How the Computer Thinks):",
            f"   {model.get('human_vs_computer_trap', '')}",
            "",
            " 3-Second Mental Movie (What the Computer Physically Does):",
        ]
        for m_line in model.get("mental_movie", "").split("\n"):
            lines.append(f"   {m_line}")
        lines.append("=" * 70 + "\n")

        return "\n".join(lines)

    def enrich_prompt_for_llm(self, concept_id: str) -> str:
        """Inject beginner analogy guidance into Socratic LLM evaluation."""
        model = self.get_analogy(concept_id)
        if not model:
            return ""

        return (
            f"BEGINNER PEDAGOGY GUIDANCE:\n"
            f"- Use this real-world analogy: {model.get('real_world_analogy', '')}\n"
            f"- Clarify this beginner intuition trap: {model.get('human_vs_computer_trap', '')}\n"
            f"- Ground your explanation in this mental movie:\n{model.get('mental_movie', '')}\n"
        )
