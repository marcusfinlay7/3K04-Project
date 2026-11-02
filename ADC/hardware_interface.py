"""HARDWARE INTERFACE — owns the cabinet hardware simulation.

RESPONSIBILITY: select compartments, command locks, inspect sensors and confirm
actual medication movement independently of a requested quantity.
HIDDEN DECISION / ANTICIPATED CHANGE: _compartments/_selected, lock/sensor states,
simulated fault inputs and outcome generation. A hardware driver can replace
these variables behind the same interface.

PUBLIC INTERFACE: perform -> frozen HardwareOutcome; unlock/lock/repair/
closeDrawer -> bool; isClosed -> bool or None; getFaults/getStatus -> copies.
Outcome fields: completed/medicationId/confirmedQuantity/description.
Status fields: selectedMedication/closed/locked/holdOpen/nextOutcome.
supportedFaults/injectFault/setNextOutcome/setHoldOpen are explicit test controls.

Controller cannot set a sensor or infer success from an unlock request.
Unknown test choices raise ValueError; physical rejection returns False or an
incomplete outcome. None from isClosed means UNKNOWN, never safely closed."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["HardwareInterface","HardwareOutcome"]

from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareOutcome:
    completed: bool
    medicationId: str
    confirmedQuantity: int
    description: str


class HardwareInterface:
    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    # Create the known simulated compartments and start with the drawer closed and locked.
    def __init__(self, medicationIds: list[str]):
        self._compartments = set(medicationIds)
        self._faults = {}
        self._selected = None
        self._closed = True
        self._locked = True
        self._hold_open = False
        self._next_outcome = "normal"

    # PUBLIC INTERFACE: callers use these documented operations.
    # List the hardware fault IDs that the test controls may inject.
    def supportedFaults(self) -> tuple[str, ...]:
        """Return an immutable tuple of supported hardware fault IDs."""
        return ("drawer_jam", "closure_sensor", "hardware_interface", "medication_mismatch")

    # Introduce a supported hardware problem and request a lock.
    def injectFault(self, faultId: str) -> None:
        """Test harness input; detection and recovery are owned by Fault Handler."""
        if faultId not in self.supportedFaults():
            raise ValueError("Unsupported hardware fault.")
        self._faults[faultId] = faultId.replace("_", " ").capitalize()
        self.lock()

    # Remove one simulated hardware problem without claiming that the drawer has closed.
    def repair(self, faultId: str) -> bool:
        """Simulate technician repair, but never pretend an open door is closed."""
        if faultId in self._faults:
            del self._faults[faultId]
            return True
        return False

    # Return a copy of the hardware problems currently reported by the simulator.
    def getFaults(self) -> dict[str, str]:
        """Return a copy of hardware fault ID -> description; no mutation."""
        return dict(self._faults)

    # Read closure as confirmed closed, open, or unknown because the sensor cannot be trusted.
    def isClosed(self) -> bool | None:
        """Read closure: True = confirmed closed, False = open, None = sensor unknown."""
        if "closure_sensor" in self._faults or "hardware_interface" in self._faults:
            return None
        return self._closed

    # Engage the simulated lock only when closure can be confirmed.
    def lock(self) -> bool:
        """A lock command does not count as confirmation of cabinet closure."""
        self._locked = self.isClosed() is True
        if self._locked:
            self._selected = None
        return self._locked

    # Select and open a known compartment only while the hardware is fault-free and closed.
    def unlock(self, medicationId: str) -> bool:
        """Unlock only the requested known compartment if fault-free and closed.

        Return False without opening anything if a precondition fails."""
        if medicationId not in self._compartments or self._faults or self.isClosed() is not True:
            return False
        self._selected = medicationId
        self._locked = False
        self._closed = False
        return True

    # Simulate a medicine transfer and return how much actually moved, including failures.
    def perform(self, operation: str, medicationId: str, quantity: int) -> HardwareOutcome:
        """Confirm exact/partial/zero movement separately from the request."""
        if operation not in {"dispense", "replenish"} or type(quantity) is not int or quantity <= 0:
            return HardwareOutcome(False, medicationId, 0, "Invalid physical operation.")
        if not self.unlock(medicationId):
            return HardwareOutcome(False, medicationId, 0, "Hardware not safe or cabinet not confirmed closed.")
        # Consume the one-shot test setting, then compute the quantity that moved.
        outcome = self._next_outcome
        self._next_outcome = "normal"
        confirmed = quantity
        if outcome == "fail":
            confirmed = 0
        elif outcome == "partial":
            confirmed = max(0, quantity - 1)
        if outcome != "normal":
            self._faults["drawer_jam"] = "Mechanism stopped before completing the request."
        # Normally simulate closure after movement; the test checkbox can leave it open.
        if not self._hold_open:
            self._closed = True
            self.lock()
        completed = outcome == "normal"
        if completed:
            description = f"Completed: {confirmed} units confirmed."
        else:
            description = f"Incomplete: only {confirmed} units confirmed."
        return HardwareOutcome(completed, medicationId, confirmed, description)

    # Choose whether the next transfer completes, moves nothing, or moves only part.
    def setNextOutcome(self, outcome: str) -> None:
        """Arm normal/fail/partial for the next physical action; return None.

        Test control. Unsupported choices raise ValueError before mutation."""
        if outcome not in {"normal", "fail", "partial"}:
            raise ValueError("Unsupported physical outcome.")
        self._next_outcome = outcome

    # Choose whether a completed transfer leaves the drawer open for the closure test.
    def setHoldOpen(self, enabled: bool) -> None:
        """Set whether completed test actions leave the drawer open; return None."""
        self._hold_open = bool(enabled)

    # Attempt to close the drawer and confirm locking; a jam or sensor fault can prevent success.
    def closeDrawer(self) -> bool:
        """Simulate physically closing the drawer; sensor faults remain unresolved."""
        if "drawer_jam" in self._faults:
            return False
        self._closed = True
        return self.lock()

    # Return a snapshot of drawer, lock, selected compartment and simulation settings.
    def getStatus(self) -> dict:
        """Return a fresh snapshot of selected compartment, closure/lock and test settings."""
        return {"selectedMedication": self._selected, "closed": self.isClosed(),
                "locked": self._locked, "holdOpen": self._hold_open,
                "nextOutcome": self._next_outcome}
