"""SPEC.md Section 3 — Suppression Rule.

A tool is suppressed when mode > threshold for its execution class.
If a class has no threshold (null), the tool is never suppressed.
"""

from maelstrom_gate.core import Gate, Tool, is_suppressed


def test_suppression_when_mode_exceeds_threshold():
    """Tool suppressed when mode > threshold."""
    assert is_suppressed("high_impact", 0.36) is True
    assert is_suppressed("external_action", 0.66) is True
    assert is_suppressed("state_mutation", 0.66) is True


def test_not_suppressed_at_or_below_threshold():
    """Tool NOT suppressed when mode <= threshold."""
    assert is_suppressed("high_impact", 0.35) is False
    assert is_suppressed("external_action", 0.65) is False
    assert is_suppressed("state_mutation", 0.65) is False


def test_null_threshold_never_suppressed():
    """read_only and advisory have null thresholds — never suppressed."""
    for mode in [0.0, 0.5, 1.0]:
        assert is_suppressed("read_only", mode) is False
        assert is_suppressed("advisory", mode) is False


def test_suppression_via_gate_filter():
    """Verify suppression through the Gate.filter() interface."""
    gate = Gate()
    gate.add_tools([
        Tool(name="safe", execution_class="read_only"),
        Tool(name="dangerous", execution_class="high_impact"),
    ])
    result = gate.filter(0.5)
    assert "safe" in result.visible_names
    assert "dangerous" in result.suppressed_names
