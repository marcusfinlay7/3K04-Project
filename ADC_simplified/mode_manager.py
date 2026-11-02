"""Own Normal/Maintenance/Fault transitions and mode restrictions.

PUBLIC INTERFACE: ModeManager reads/changes mode and checks allowed operations.
The safety callback guards permissive transitions; on_change reports successful
changes. User authorization remains the controller's responsibility."""

__all__ = ["ModeManager"]

from typing import Callable
from event_logger import EventLogger


class ModeManager:
    def __init__(self, logger: EventLogger, on_change: Callable = None):
        self._mode = "Normal"
        self._logger = logger
        self._on_change = on_change
        self._safe_to_leave = lambda: False
        self._allowed = {
            "Normal": {"dispense", "replenish", "register", "catalog", "inventory", "history",
                       "logs", "faults", "maintenance", "close_drawer", "traffic"},
            "Maintenance": {"fix", "logs", "faults", "maintenance", "inventory", "catalog", "close_drawer", "traffic"},
            "Fault": {"fix", "logs", "faults", "inventory", "catalog", "close_drawer", "traffic"},
        }

    def setSafetyCheck(self, check: Callable[[], bool]) -> None:
        """Wire the hardware/fault guard; missing guard prevents permissive transitions."""
        self._safe_to_leave = check

    def getMode(self) -> str:
        """Return the current mode string; no state change."""
        return self._mode

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

    def isOperationAllowed(self, operation: str) -> bool:
        """Return whether the named operation is permitted in this mode.

        Unknown operations return False; this does not authenticate a user."""
        return operation in self._allowed.get(self._mode, set())
