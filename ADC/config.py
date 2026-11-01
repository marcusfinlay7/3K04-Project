"""CONFIGURATION — public immutable settings, not shared live cabinet state.

RESPONSIBILITY: choose the demo/D1 timing profile and numeric simulation limits.
ANTICIPATED CHANGE: timing/capacity adjustments belong here, not in GUI rules.
PUBLIC INTERFACE: frozen Timings values and the constants listed in __all__.
Consumers read these settings; private deadlines/counters belong to their
owning modules. This file does not expose a live inventory or authenticated user."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = [
    "Timings", "DEMO_MODE", "D1_TIMINGS", "DEMO_TIMINGS", "TIMINGS",
    "FAILED_LOGIN_LIMIT", "MISSED_HEARTBEAT_LIMIT", "MAX_MEDICATION_TYPES",
    "LOCATION_CAPACITY", "GUI_POLL_MS",
]

from dataclasses import dataclass

DEMO_MODE = True


@dataclass(frozen=True)
class Timings:
    lockout: float
    cabinet_closure: float
    heartbeat_interval: float
    heartbeat_response: float
    message_retry: float


D1_TIMINGS = Timings(60, 30, 60, 3, 60)
DEMO_TIMINGS = Timings(10, 10, 5, 1, 10)
if DEMO_MODE:
    TIMINGS = DEMO_TIMINGS
else:
    TIMINGS = D1_TIMINGS
FAILED_LOGIN_LIMIT = 3
MISSED_HEARTBEAT_LIMIT = 3
MAX_MEDICATION_TYPES = 10
LOCATION_CAPACITY = 50
GUI_POLL_MS = 100
