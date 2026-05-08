"""SPEC.md Section 9 — Ingress Validation.

1. Registration check: tool must exist in registry. Reject with tool_not_found.
2. Suppression check: tool must not be suppressed. Reject with execution_class_suppressed.
"""

from gatekeeper.core import Gate, Tool
from gatekeeper.ingress import validate_proposal, IngressResult


def test_registration_check_passes():
    """Registered tool passes validation."""
    gate = Gate()
    gate.add_tool(Tool(name="read_file", execution_class="read_only"))
    result = validate_proposal("read_file", gate, 0.1)
    assert result.accepted is True
    assert result.reason is None


def test_registration_check_rejects_unknown():
    """Unregistered tool rejected with tool_not_found."""
    gate = Gate()
    gate.add_tool(Tool(name="read_file", execution_class="read_only"))
    result = validate_proposal("unknown_tool", gate, 0.1)
    assert result.accepted is False
    assert result.reason == "tool_not_found"


def test_suppression_check_rejects_suppressed():
    """Suppressed tool rejected at current mode."""
    gate = Gate()
    gate.add_tool(Tool(name="deploy", execution_class="high_impact"))
    result = validate_proposal("deploy", gate, 0.9)
    assert result.accepted is False
    assert result.reason == "execution_class_suppressed"
