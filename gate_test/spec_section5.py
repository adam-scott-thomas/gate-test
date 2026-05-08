"""SPEC.md Section 5 — Mode Zones.

| Zone     | Range             |
| normal   | mode <= 0.35      |
| elevated | 0.35 < mode <= 0.65 |
| crisis   | mode > 0.65       |
"""

from gatekeeper.core import Gate


def test_normal_zone():
    gate = Gate()
    for mode in [0.0, 0.1, 0.35]:
        result = gate.filter(mode)
        assert result.mode_zone == "normal", f"mode={mode} should be normal"


def test_elevated_zone():
    gate = Gate()
    for mode in [0.36, 0.5, 0.65]:
        result = gate.filter(mode)
        assert result.mode_zone == "elevated", f"mode={mode} should be elevated"


def test_crisis_zone():
    gate = Gate()
    for mode in [0.66, 0.8, 1.0]:
        result = gate.filter(mode)
        assert result.mode_zone == "crisis", f"mode={mode} should be crisis"


def test_mode_clamped_to_0_1():
    """Mode values MUST be clamped to [0.0, 1.0]."""
    gate = Gate()
    r_neg = gate.filter(-0.5)
    assert r_neg.mode == 0.0
    r_over = gate.filter(1.5)
    assert r_over.mode == 1.0
