"""SPEC.md Section 7 — Filter Result.

The output of a filter operation contains: visible (tool array), suppressed
(tool array), mode (float), mode_zone (string), and thresholds (object).
"""

from maelstrom_gate.core import Gate, Tool


def _gate():
    g = Gate()
    g.add_tools([
        Tool("read", execution_class="read_only"),
        Tool("advise", execution_class="advisory"),
        Tool("email", execution_class="external_action"),
        Tool("write", execution_class="state_mutation"),
        Tool("deploy", execution_class="high_impact"),
    ])
    return g


def test_filter_result_has_visible():
    """Result MUST contain 'visible' as a tuple of Tool objects."""
    r = _gate().filter(0.0)
    assert isinstance(r.visible, tuple)
    assert all(isinstance(t, Tool) for t in r.visible)


def test_filter_result_has_suppressed():
    """Result MUST contain 'suppressed' as a tuple of Tool objects."""
    r = _gate().filter(0.5)
    assert isinstance(r.suppressed, tuple)
    assert all(isinstance(t, Tool) for t in r.suppressed)


def test_filter_result_has_mode():
    """Result MUST contain 'mode' as a float."""
    r = _gate().filter(0.5)
    assert isinstance(r.mode, float)
    assert r.mode == 0.5


def test_filter_result_has_mode_status():
    """Result MUST contain 'mode_status' as a string (zone name)."""
    r = _gate().filter(0.5)
    assert isinstance(r.mode_status, str)
    assert r.mode_status in ("normal", "elevated", "crisis")


def test_filter_result_has_thresholds():
    """Result MUST contain 'thresholds' mapping class names to float|None."""
    r = _gate().filter(0.5)
    assert isinstance(r.thresholds, dict)
    assert "read_only" in r.thresholds
    assert "high_impact" in r.thresholds


def test_visible_plus_suppressed_equals_total():
    """visible + suppressed MUST account for all registered tools."""
    g = _gate()
    r = g.filter(0.5)
    assert len(r.visible) + len(r.suppressed) == len(g.tools)


def test_filter_result_is_frozen():
    """Filter result MUST be immutable (frozen dataclass)."""
    import pytest
    r = _gate().filter(0.0)
    with pytest.raises(AttributeError):
        r.mode = 0.5
