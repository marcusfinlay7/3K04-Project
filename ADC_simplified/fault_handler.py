"""Own registered safety faults, visible alarms and guarded recovery.

PUBLIC INTERFACE: FaultHandler detects hardware/closure faults, reports alarms
and checks repairs. can_recover() supplies authorization; notify(id, description)
reports a fault to the controller. Clearing an alarm does not clear a fault."""

__all__ = ["FaultHandler"]

import time
from typing import Callable
from config import TIMINGS, Timings
from event_logger import EventLogger
from mode_manager import ModeManager
from hardware_interface import HardwareInterface


class FaultHandler:
    # One table defines both supported safety faults and their display categories.
    # HMS availability and login lockout are separate from these cabinet faults.
    _CATEGORIES = {
        "drawer_jam": "Hardware",
        "closure_sensor": "Hardware",
        "hardware_interface": "Hardware",
        "medication_mismatch": "Hardware",
        "cabinet_closure": "Closure",
        "software_error": "Software",
        "inventory_uncertain": "Software",
    }

    def __init__(self, mode: ModeManager, logger: EventLogger,
                 hardware: HardwareInterface, can_recover: Callable[[], bool],
                 notify: Callable, clock: Callable = time.monotonic,
                 timings: Timings = TIMINGS):
        self._mode = mode
        self._logger = logger
        self._hardware = hardware
        self._can_recover = can_recover
        self._notify = notify
        self._clock = clock
        self._timings = timings
        self._active = {}
        self._closure_deadline = None
        self._software_resolved = True
        self._alarms = {}

    def raiseAlarm(self, alarmId: str, description: str) -> None:
        """An alarm is a visible notification that something needs attention."""
        self._alarms[alarmId] = description
        self._logger.logEvent("alarm", description, outcome="raised")

    def clearAlarm(self, alarmId: str) -> None:
        """End the named notification after its condition ends; return None.

        Trusted coordination operation; unknown ID is a no-op. Safety fault
        registration is separate and cannot be bypassed by clearing a banner."""
        if alarmId in self._alarms:
            del self._alarms[alarmId]
            self._logger.logEvent("alarm_cleared", f"Alarm ended: {alarmId.replace('_', ' ')}.")

    def getAlarms(self) -> dict[str, str]:
        """Return a copy of alarm ID -> description; caller edits cannot clear alarms."""
        return dict(self._alarms)

    def handleFault(self, faultId: str, description: str) -> bool:
        """Register supported safety faults once per occurrence; inhibit immediately."""
        if faultId not in self._CATEGORIES:
            return False
        if faultId in self._active:
            return True
        self._active[faultId] = description
        if faultId == "software_error":
            self._software_resolved = False
        self._hardware.lock()
        self._mode.setMode("Fault")
        self._logger.logEvent("fault", f"{faultId}: {description}", outcome="active")
        self.reportFault(faultId)
        return True

    def reportFault(self, faultId: str) -> None:
        """Publish a registered fault through the controller's communication boundary."""
        if faultId in self._active:
            self._notify(faultId, self._active[faultId])

    def clearFault(self, faultId: str) -> bool:
        """Clear only for an authorized technician and a verified resolved condition."""
        if not self._can_recover() or faultId not in self._active:
            return False
        if faultId == "inventory_uncertain":
            # There is no approved stock reconciliation workflow in D2. Never guess.
            return False
        if faultId in self._hardware.getFaults():
            return False
        if self._hardware.isClosed() is not True:
            return False
        if faultId == "software_error" and not self._software_resolved:
            return False
        del self._active[faultId]
        self.clearAlarm(faultId)
        self._logger.logEvent("fault_cleared", f"Resolved {faultId}.", outcome="success")
        return True

    def operationCompleted(self) -> None:
        """Begin closure timing at recorded operation completion in Normal mode."""
        if self._mode.getMode() == "Normal":
            self._closure_deadline = self._clock() + self._timings.cabinet_closure

    def poll(self) -> None:
        """Detect reported hardware failures and unconfirmed closure without sleeping."""
        for fault_id, description in self._hardware.getFaults().items():
            self.handleFault(fault_id, description)
        if self._closure_deadline is None:
            return
        if self._hardware.isClosed() is True:
            self._closure_deadline = None
        elif self._clock() >= self._closure_deadline:
            self._closure_deadline = None
            self.handleFault("cabinet_closure", "Cabinet closure was not confirmed before timeout.")

    def resolveSimulatedSoftwareCondition(self) -> None:
        """Test fixture reports that its software condition ended; this does not clear the fault."""
        self._software_resolved = True

    def restartSoftware(self) -> bool:
        """Simulate an authorized service restart, then require a separate recovery check."""
        if not self._can_recover():
            return False
        self._software_resolved = True
        self._logger.logEvent("maintenance", "Software restarted; self-check passed.", outcome="success")
        return True

    def getFaults(self) -> dict[str, str]:
        """Return a copy of fault ID -> description; caller edits cannot clear faults."""
        return dict(self._active)

    def getCategories(self) -> tuple[str, ...]:
        """Fault submodes share the dispensing interlock but have different recovery."""
        categories = set()
        for fault_id in self._active:
            categories.add(self._CATEGORIES[fault_id])
        return tuple(sorted(categories))

    def isSafe(self) -> bool:
        """Return True only when no registered/reported faults remain and closure is confirmed."""
        return not self._active and not self._hardware.getFaults() and self._hardware.isClosed() is True
