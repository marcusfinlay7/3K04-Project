"""FAULT HANDLER — owns fault registration, alarms and recovery policy.

RESPONSIBILITY: detect/record supported faults, inhibit unsafe operations,
monitor closure timing and verify that recovery conditions really hold.
HIDDEN DECISION / ANTICIPATED CHANGE: private fault taxonomy, _active/_alarms,
closure deadlines and software recovery checks. New fault policies belong here.

PUBLIC INTERFACE: handleFault/clearFault/restartSoftware -> bool;
reportFault/raiseAlarm/clearAlarm/operationCompleted/poll -> None;
getFaults/getAlarms -> copied dictionaries; getCategories -> immutable tuple;
isSafe -> bool. resolveSimulatedSoftwareCondition is a test input only.

TRUSTED WIRING: can_recover() -> bool and notify(id, description) -> None
are documented public callbacks. Hardware and ModeManager are used only through
their public operations. No caller may directly clear _active or set _mode.
raiseAlarm is an ordinary notification method, NOT Python exception raising."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["FaultHandler"]

import time
from typing import Callable
from config import TIMINGS, Timings
from event_logger import EventLogger
from mode_manager import ModeManager
from hardware_interface import HardwareInterface


class FaultHandler:
    # Private policy: supported safety faults inhibit transfers; HMS/lockout are separate.
    _SAFETY_FAULTS = frozenset({"drawer_jam", "closure_sensor", "hardware_interface",
                              "medication_mismatch", "cabinet_closure", "software_error", "inventory_uncertain"})

    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    # Connect fault handling to hardware, mode, logging and permission/notification callbacks.
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

    # PUBLIC INTERFACE: callers use these documented operations.
    # Store a visible notification and log its activation; this is not an exception.
    def raiseAlarm(self, alarmId: str, description: str) -> None:
        """An alarm is a visible notification that something needs attention."""
        self._alarms[alarmId] = description
        self._logger.logEvent("alarm", description, outcome="raised")

    # Remove an active notification and log that it ended.
    def clearAlarm(self, alarmId: str) -> None:
        """End the named notification after its condition ends; return None.

        Trusted coordination operation; unknown ID is a no-op. Safety fault
        registration is separate and cannot be bypassed by clearing a banner."""
        if alarmId in self._alarms:
            del self._alarms[alarmId]
            self._logger.logEvent("alarm_cleared", f"Alarm ended: {alarmId.replace('_', ' ')}.")

    # Return a copy of the notifications currently displayed to the user.
    def getAlarms(self) -> dict[str, str]:
        """Return a copy of alarm ID -> description; caller edits cannot clear alarms."""
        return dict(self._alarms)

    # Register a supported fault once, request locking, enter Fault mode and report it.
    def handleFault(self, faultId: str, description: str) -> bool:
        """Register supported safety faults once per occurrence; inhibit immediately."""
        if faultId not in self._SAFETY_FAULTS:
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

    # Pass a registered fault's ID and description to the alarm/HMS notification callback.
    def reportFault(self, faultId: str) -> None:
        """Publish a registered fault through the controller's communication boundary."""
        if faultId in self._active:
            self._notify(faultId, self._active[faultId])

    # Remove a fault only after permission and condition-specific recovery checks pass.
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

    # Start the drawer-closure deadline after a successful operation in Normal mode.
    def operationCompleted(self) -> None:
        """Begin closure timing at recorded operation completion in Normal mode."""
        if self._mode.getMode() == "Normal":
            self._closure_deadline = self._clock() + self._timings.cabinet_closure

    # Read reported hardware faults and check whether the drawer-closure deadline has expired.
    def poll(self) -> None:
        """Detect reported hardware failures and unconfirmed closure without sleeping."""
        for fault_id, description in self._hardware.getFaults().items():
            self.handleFault(fault_id, description)
        if self._closure_deadline is not None:
            if self._hardware.isClosed() is True:
                self._closure_deadline = None
            elif self._clock() >= self._closure_deadline:
                self._closure_deadline = None
                self.handleFault("cabinet_closure", "Cabinet closure was not confirmed before timeout.")

    # Mark the simulated software problem as resolved without clearing its registered fault.
    def resolveSimulatedSoftwareCondition(self) -> None:
        """Test fixture reports that its software condition ended; this does not clear the fault."""
        self._software_resolved = True

    # Perform an authorized simulated restart and mark the software self-check as passed.
    def restartSoftware(self) -> bool:
        """Simulate an authorized service restart, then require a separate recovery check."""
        if not self._can_recover():
            return False
        self._software_resolved = True
        self._logger.logEvent("maintenance", "Software restarted; self-check passed.", outcome="success")
        return True

    # Return a copy of the registered faults that still need recovery.
    def getFaults(self) -> dict[str, str]:
        """Return a copy of fault ID -> description; caller edits cannot clear faults."""
        return dict(self._active)

    # Group active fault IDs into Hardware, Software and Closure labels.
    def getCategories(self) -> tuple[str, ...]:
        """Fault submodes share the dispensing interlock but have different recovery."""
        categories = set()
        for fault_id in self._active:
            if fault_id in {"software_error", "inventory_uncertain"}:
                categories.add("Software")
            elif fault_id == "cabinet_closure":
                categories.add("Closure")
            else:
                categories.add("Hardware")
        return tuple(sorted(categories))

    # Check that faults are absent and drawer closure is positively confirmed.
    def isSafe(self) -> bool:
        """Return True only when no registered/reported faults remain and closure is confirmed."""
        return not self._active and not self._hardware.getFaults() and self._hardware.isClosed() is True
