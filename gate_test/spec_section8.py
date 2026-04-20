"""SPEC.md Section 8 — Authorization Envelope.

An authorization envelope is a signed, frozen permission set that
accompanies a tool invocation. Envelope parameters tighten as mode rises.
"""

import json
from dataclasses import asdict

import pytest

from maelstrom_gate.core import Tool
from maelstrom_gate.envelope import (
    AuthorizationEnvelope, build_envelope, verify_envelope,
)


KEY = "spec-conformance-key"


def test_envelope_has_required_fields():
    """Envelope MUST contain all 12 fields from the spec."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.1, "ctx", KEY)
    fields = asdict(e)
    required = [
        "envelope_id", "context_id", "tool_name", "allowed_tools",
        "max_tool_calls", "max_retries", "budget_seconds",
        "execution_mode", "dry_run", "branching", "human_approved", "signature",
    ]
    for f in required:
        assert f in fields, f"Missing required field: {f}"


def test_envelope_is_frozen():
    """Envelope MUST be immutable."""
    e = build_envelope(Tool("r"), 0.1, "ctx", KEY)
    with pytest.raises(AttributeError):
        e.budget_seconds = 999


def test_envelope_signature_verifies():
    """A correctly built envelope MUST verify with the same key."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.1, "ctx", KEY)
    assert verify_envelope(e, KEY)


def test_envelope_wrong_key_fails():
    """Verification with a different key MUST fail."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.1, "ctx", KEY)
    assert not verify_envelope(e, "wrong-key")


# --- Crisis adjustment table ---


def test_normal_envelope_parameters():
    """Normal zone (mode <= 0.35): standard, 30s budget, 20 calls."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.1, "ctx", KEY)
    assert e.budget_seconds == 30
    assert e.max_tool_calls == 20
    assert e.execution_mode == "standard"


def test_elevated_envelope_parameters():
    """Elevated zone (0.35 < mode <= 0.65): cautious, 15s budget, 10 calls."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.5, "ctx", KEY)
    assert e.budget_seconds == 15
    assert e.max_tool_calls == 10
    assert e.execution_mode == "cautious"


def test_crisis_envelope_parameters():
    """Crisis zone (mode > 0.65): minimal, 7s budget, 5 calls."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.8, "ctx", KEY)
    assert e.budget_seconds == 7
    assert e.max_tool_calls == 5
    assert e.execution_mode == "minimal"


# --- Branching rules ---


def test_branching_auto_for_read_only():
    """read_only tools get branching=auto in normal zone."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.1, "ctx", KEY)
    assert e.branching == "auto"


def test_branching_auto_for_advisory():
    """advisory tools get branching=auto in normal zone."""
    e = build_envelope(Tool("a", execution_class="advisory"), 0.1, "ctx", KEY)
    assert e.branching == "auto"


def test_branching_deny_for_state_mutation():
    """state_mutation tools get branching=deny in normal zone."""
    e = build_envelope(Tool("w", execution_class="state_mutation"), 0.1, "ctx", KEY)
    assert e.branching == "deny"


def test_branching_deny_in_elevated():
    """All tools get branching=deny in elevated zone."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.5, "ctx", KEY)
    assert e.branching == "deny"


def test_branching_deny_in_crisis():
    """All tools get branching=deny in crisis zone."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.8, "ctx", KEY)
    assert e.branching == "deny"


# --- Signature computation ---


def test_signature_is_hex_string():
    """Signature MUST be a hex-encoded HMAC-SHA256 digest (64 chars)."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.1, "ctx", KEY)
    assert len(e.signature) == 64
    assert all(c in "0123456789abcdef" for c in e.signature)


def test_tampered_envelope_fails_verification():
    """Any field tampering MUST cause verification to fail."""
    e = build_envelope(Tool("r", execution_class="read_only"), 0.1, "ctx", KEY)
    tampered = AuthorizationEnvelope(
        envelope_id=e.envelope_id, context_id=e.context_id,
        tool_name="TAMPERED", allowed_tools=e.allowed_tools,
        max_tool_calls=e.max_tool_calls, max_retries=e.max_retries,
        budget_seconds=e.budget_seconds, execution_mode=e.execution_mode,
        dry_run=e.dry_run, branching=e.branching,
        human_approved=e.human_approved, signature=e.signature,
    )
    assert not verify_envelope(tampered, KEY)
