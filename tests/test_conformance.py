"""Run all spec conformance tests via pytest."""

from gate_test.spec_section2 import *
from gate_test.spec_section3 import *
from gate_test.spec_section4 import *
from gate_test.spec_section5 import *
from gate_test.spec_section7 import *
from gate_test.spec_section8 import *
from gate_test.spec_section9 import *
from gate_test.ecosystem_integration import *
from gate_test.benchmarks import (
    test_filter_10_tools_fast,
    test_filter_100_tools_fast,
    test_filter_1000_tools_acceptable,
    test_envelope_build_fast,
    test_envelope_verify_fast,
)
