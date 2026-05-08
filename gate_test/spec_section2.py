"""SPEC.md Section 2 — Execution Classes.

Every tool MUST be assigned exactly one execution class.
Unrecognized classes MUST be treated as high_impact.
"""

from gatekeeper.core import Gate, Tool, ExecutionClass

VALID_CLASSES = ["read_only", "advisory", "external_action", "state_mutation", "high_impact"]


def test_all_five_classes_supported():
    """A conforming implementation MUST support all five execution classes."""
    gate = Gate()
    for cls in VALID_CLASSES:
        gate.add_tool(Tool(name=f"tool_{cls}", execution_class=cls))
    assert len(gate.tools) == 5


def test_unrecognized_class_treated_as_high_impact():
    """Unrecognized execution classes MUST be treated as high_impact."""
    gate = Gate()
    gate.add_tool(Tool(name="mystery", execution_class="ultra_secret"))
    result = gate.filter(0.4)  # elevated: high_impact suppressed at 0.35
    assert "mystery" in result.suppressed_names


def test_each_tool_has_exactly_one_class():
    """Each tool has exactly one execution_class field."""
    for cls in VALID_CLASSES:
        t = Tool(name="t", execution_class=cls)
        assert t.execution_class == cls
