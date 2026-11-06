"""
Concept Graph Service:
Manages curriculum dependencies as a Directed Acyclic Graph (DAG).
Provides cycle validation, prerequisite resolution, topological ordering,
and computes the student's active Learning Frontier.
"""
import json
from pathlib import Path
from typing import Dict, List, Set, Optional

from app.models.concept import Concept, Misconception
from app.models.curriculum import LearningFrontier, ConceptState
from app.models.student import ConceptMastery


class ConceptGraphError(Exception):
    """Raised when the curriculum graph violates DAG integrity."""
    pass


class ConceptGraphService:
    def __init__(self, concepts_file: Optional[Path] = None):
        self.concepts: Dict[str, Concept] = {}
        # Adjacency lists
        # prerequisites_of[C] = [P1, P2] -> concepts that must be learned BEFORE C
        self.prerequisites_of: Dict[str, Set[str]] = {}
        # dependents_of[P] = [C1, C2] -> concepts that are unlocked AFTER P is mastered
        self.dependents_of: Dict[str, Set[str]] = {}

        if concepts_file and concepts_file.exists():
            self.load_from_json(concepts_file)

    def load_from_json(self, file_path: Path) -> None:
        """Load and index concept definitions from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            concept = Concept(**item)
            self.add_concept(concept)

        self.validate_graph_integrity()

    def add_concept(self, concept: Concept) -> None:
        """Add a concept and update adjacency mappings."""
        self.concepts[concept.id] = concept
        if concept.id not in self.prerequisites_of:
            self.prerequisites_of[concept.id] = set()
        if concept.id not in self.dependents_of:
            self.dependents_of[concept.id] = set()

        for prereq_id in concept.prerequisites:
            self.prerequisites_of[concept.id].add(prereq_id)
            if prereq_id not in self.dependents_of:
                self.dependents_of[prereq_id] = set()
            self.dependents_of[prereq_id].add(concept.id)

    def validate_graph_integrity(self) -> None:
        """
        Validates two critical DAG invariants:
        1. All referenced prerequisite IDs exist in the curriculum.
        2. There are NO circular dependencies (A -> B -> A).
        """
        # 1. Existence check
        for concept_id, prereqs in self.prerequisites_of.items():
            for p in prereqs:
                if p not in self.concepts:
                    raise ConceptGraphError(
                        f"Concept '{concept_id}' references unknown prerequisite '{p}'."
                    )

        # 2. Cycle detection via Kahn's algorithm (Topological sort)
        in_degree = {cid: len(prereqs) for cid, prereqs in self.prerequisites_of.items()}
        queue = [cid for cid, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for dependent in self.dependents_of.get(node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if visited_count != len(self.concepts):
            raise ConceptGraphError(
                "Circular dependency detected in concept prerequisites! Curriculum must be a strict DAG."
            )

    def get_all_prerequisites(self, concept_id: str, recursive: bool = True) -> Set[str]:
        """Retrieve direct or transitive prerequisites for a given concept."""
        if concept_id not in self.concepts:
            raise KeyError(f"Unknown concept ID: {concept_id}")

        direct = set(self.prerequisites_of.get(concept_id, set()))
        if not recursive:
            return direct

        transitive = set(direct)
        for p in direct:
            transitive.update(self.get_all_prerequisites(p, recursive=True))
        return transitive

    def compute_learning_frontier(
        self,
        mastery_map: Dict[str, ConceptMastery],
        mastery_threshold: float = 0.70
    ) -> LearningFrontier:
        """
        Calculates the pedagogical boundary for a student.

        Rules:
        - MASTERED: mastery >= threshold
        - READY: not mastered, but ALL prerequisites are mastered (>= threshold)
        - IN_PROGRESS: attempted (attempts > 0), not yet mastered, but prerequisites met
        - LOCKED: at least one prerequisite is not mastered (< threshold)
        """
        frontier = LearningFrontier()

        for concept_id, concept in self.concepts.items():
            current_state = mastery_map.get(concept_id)
            score = current_state.mastery if current_state else 0.0
            attempts = current_state.attempts_count if current_state else 0

            # Check if all prerequisites meet the mastery threshold
            prereqs = self.prerequisites_of.get(concept_id, set())
            prereqs_satisfied = True
            for p in prereqs:
                p_state = mastery_map.get(p)
                p_score = p_state.mastery if p_state else 0.0
                if p_score < mastery_threshold:
                    prereqs_satisfied = False
                    break

            if score >= mastery_threshold:
                frontier.mastered.append(concept_id)
            elif not prereqs_satisfied:
                frontier.locked.append(concept_id)
            else:
                # Prerequisites are satisfied, but target concept is not mastered
                if attempts > 0:
                    frontier.in_progress.append(concept_id)
                else:
                    frontier.ready.append(concept_id)

        return frontier

    def get_misconception(self, concept_id: str, misconception_id: str) -> Optional[Misconception]:
        """Lookup a specific misconception by concept and ID."""
        concept = self.concepts.get(concept_id)
        if not concept:
            return None
        for m in concept.misconceptions:
            if m.id == misconception_id:
                return m
        return None
