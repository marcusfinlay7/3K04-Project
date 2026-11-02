"""MODE MANAGER — the only owner of the cabinet operating mode.

RESPONSIBILITY: validate transitions and mode-based operation restrictions.
HIDDEN DECISION / ANTICIPATED CHANGE: _mode and transition/permission tables.
Changing these rules does not require exposing the mode variable to callers.

PUBLIC INTERFACE: getMode -> str; setMode(mode) -> bool;
isOperationAllowed(operation) -> bool; setSafetyCheck(check) -> None.
Modes are Normal, Maintenance and Fault. Callers receive a string, not mutable
state. User authorization belongs to AccessControl/Controller.

TRUSTED WIRING: check() -> bool is a public safety callback; the optional
on_change(previous, current) -> None callback reports confirmed transitions.
Unknown/unsafe transitions return False without changing the mode."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["ModeManager"]

from typing import Callable
from event_logger import EventLogger


class ModeManager:
    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    # Start in Normal mode and define which actions each mode permits.
    def __init__(self, logger: EventLogger, on_change: Callable = None):
        self._mode = "Normal"
        self._logger = logger
        self._on_change = on_change
        self._safe_to_leave = lambda: False
        self._allowed = {
            "Normal": {"dispense", "replenish", "catalog", "inventory", "history",
                       "logs", "faults", "maintenance", "close_drawer", "traffic"},
            "Maintenance": {"fix", "logs", "faults", "maintenance", "inventory", "catalog", "close_drawer", "traffic"},
            "Fault": {"fix", "logs", "faults", "inventory", "catalog", "close_drawer", "traffic"},
        }

    # PUBLIC INTERFACE: callers use these documented operations.
    # Connect the public check that must approve leaving a restrictive mode.
    def setSafetyCheck(self, check: Callable[[], bool]) -> None:
        """Wire the hardware/fault guard; missing guard prevents permissive transitions."""
        self._safe_to_leave = check

    # Return the cabinet's current operating mode.
    def getMode(self) -> str:
        """Return the current mode string; no state change."""
        return self._mode

    # Apply an allowed, safe mode transition and notify logging and the controller.
    def setMode(self, mode: str) -> bool:
        """Request Normal, Maintenance or Fault; return whether accepted.

        Trusted internal operation: Controller checks the user's permission.
        Unknown/unsafe transitions return False without mutation. Successful
        changes log the transition and invoke the public on_change callback."""
        transitions = {"Normal": {"Maintenance", "Fault"},
                       "Maintenance": {"Normal", "Fault"}, "Fault": {"Normal"}}
        if mode == self._mode:
            return True
        if mode not in transitions[self._mode]:
            return False
        if mode != "Fault" and not self._safe_to_leave():
            return False
        previous = self._mode
        self._mode = mode
        self._logger.logEvent("mode", f"{previous} -> {mode}", outcome="success")
        if self._on_change:
            self._on_change(previous, mode)
        return True

    # Check the named action against the current mode's permitted actions.
    def isOperationAllowed(self, operation: str) -> bool:
        """Return whether the named operation is permitted in this mode.

        Unknown operations return False; this does not authenticate a user."""
        return operation in self._allowed.get(self._mode, set())
