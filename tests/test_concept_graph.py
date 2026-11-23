from pathlib import Path
import pytest

from app.models.concept import Concept
from app.services.concept_graph import ConceptGraphService, ConceptGraphError


DATA_DIR = Path(__file__).parent.parent / "app" / "data"
CONCEPTS_FILE = DATA_DIR / "python_concepts.json"


def test_load_and_validate_dag():
    graph = ConceptGraphService(CONCEPTS_FILE)
    assert len(graph.concepts) == 8
    assert "py.variables" in graph.concepts
    assert "py.functions" in graph.concepts


def test_prerequisite_traversal():
    graph = ConceptGraphService(CONCEPTS_FILE)
    
    # Direct prerequisites of for_loops
    direct_prereqs = graph.get_all_prerequisites("py.for_loops", recursive=False)
    assert direct_prereqs == {"py.lists_sequences", "py.conditionals"}

    # Transitive prerequisites of for_loops
    transitive = graph.get_all_prerequisites("py.for_loops", recursive=True)
    assert "py.variables" in transitive
    assert "py.data_types" in transitive
    assert "py.operators_expressions" in transitive
    assert "py.conditionals" in transitive
    assert "py.lists_sequences" in transitive


def test_topological_sort_tie_break_is_deterministic():
    graph = ConceptGraphService(CONCEPTS_FILE)
    expected = [
        "py.variables",
        "py.data_types",
        "py.operators_expressions",
        "py.lists_sequences",
        "py.conditionals",
        "py.for_loops",
        "py.while_loops",
        "py.functions",
    ]
    order = graph.topological_sort()
    assert order == expected

    positions = {concept_id: index for index, concept_id in enumerate(order)}
    for concept_id, concept in graph.concepts.items():
        for prerequisite in concept.prerequisites:
            assert positions[prerequisite] < positions[concept_id]


def test_circular_dependency_detected():
    graph = ConceptGraphService()
    # Add a -> b -> a
    c1 = Concept(id="node_a", subject="test", title="A", description="desc", prerequisites=["node_b"])
    c2 = Concept(id="node_b", subject="test", title="B", description="desc", prerequisites=["node_a"])
    
    graph.add_concept(c1)
    graph.add_concept(c2)

    with pytest.raises(ConceptGraphError, match="Circular dependency detected"):
        graph.validate_graph_integrity()
