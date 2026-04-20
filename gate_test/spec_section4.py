"""SPEC.md Section 4 — Default Thresholds.

| Class            | Threshold | Suppressed When |
| read_only        | null      | Never           |
| advisory         | null      | Never           |
| external_action  | 0.65      | mode > 0.65     |
| state_mutation   | 0.65      | mode > 0.65     |
| high_impact      | 0.35      | mode > 0.35     |
"""

from maelstrom_gate.core import Gate, Tool, SUPPRESSION_THRESHOLDS, ExecutionClass


def test_default_thresholds_match_spec():
    """Default thresholds must match SPEC.md Section 4."""
    assert SUPPRESSION_THRESHOLDS[ExecutionClass.READ_ONLY] is None
    assert SUPPRESSION_THRESHOLDS[ExecutionClass.ADVISORY] is None
    assert SUPPRESSION_THRESHOLDS[ExecutionClass.EXTERNAL_ACTION] == 0.65
    assert SUPPRESSION_THRESHOLDS[ExecutionClass.STATE_MUTATION] == 0.65
    assert SUPPRESSION_THRESHOLDS[ExecutionClass.HIGH_IMPACT] == 0.35


def test_custom_thresholds_override():
    """Implementations MAY allow custom thresholds."""
    gate = Gate(thresholds={"high_impact": 0.9})
    gate.add_tool(Tool(name="deploy", execution_class="high_impact"))
    result = gate.filter(0.5)
    assert "deploy" in result.visible_names  # custom threshold 0.9 not exceeded
