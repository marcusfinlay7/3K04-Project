"""Simulate compartments, locks, closure sensing and confirmed medicine movement.

PUBLIC INTERFACE: HardwareInterface; immutable HardwareOutcome. perform()
returns actual movement separately from completion. isClosed() returns True,
False or None (unknown). Test controls never update inventory themselves."""

__all__ = ["HardwareInterface","HardwareOutcome"]

from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareOutcome:
    completed: bool
    medicationId: str
    confirmedQuantity: int
    description: str


class HardwareInterface:
    def __init__(self, medicationIds: list[str]):
        self._compartments = set(medicationIds)
        self._faults = {}
        self._selected = None
        self._closed = True
        self._locked = True
        self._hold_open = False
        self._next_outcome = "normal"

    def supportedFaults(self) -> tuple[str, ...]:
        """Return an immutable tuple of supported hardware fault IDs."""
        return ("drawer_jam", "closure_sensor", "hardware_interface", "medication_mismatch")

    def registerCompartment(self, medicationId: str) -> bool:
        """Provision an empty simulated compartment while closed and fault-free.

        Reject invalid/duplicate IDs or unsafe hardware. The controller checks
        role permissions and InventoryManager's cabinet capacity first.
        """
        if not isinstance(medicationId, str) or not medicationId.isdecimal():
            return False
        if medicationId in self._compartments or self._faults or self.isClosed() is not True:
            return False
        self._compartments.add(medicationId)
        return True

    def discardCompartment(self, medicationId: str) -> None:
        """Undo provisioning of an unused compartment after registration fails.

        Trusted controller rollback only; this is not a medicine-removal workflow.
        An open selected compartment cannot be discarded.
        """
        if medicationId == self._selected:
            raise ValueError("Cannot discard an active compartment.")
        self._compartments.discard(medicationId)

    def injectFault(self, faultId: str) -> None:
        """Test harness input; detection and recovery are owned by Fault Handler."""
        if faultId not in self.supportedFaults():
            raise ValueError("Unsupported hardware fault.")
        self._faults[faultId] = faultId.replace("_", " ").capitalize()
        self.lock()

    def repair(self, faultId: str) -> bool:
        """Simulate technician repair, but never pretend an open door is closed."""
        if faultId in self._faults:
            del self._faults[faultId]
            return True
        return False

    def getFaults(self) -> dict[str, str]:
        """Return a copy of hardware fault ID -> description; no mutation."""
        return dict(self._faults)

    def isClosed(self) -> bool | None:
        """Read closure: True = confirmed closed, False = open, None = sensor unknown."""
        if "closure_sensor" in self._faults or "hardware_interface" in self._faults:
            return None
        return self._closed

    def lock(self) -> bool:
        """A lock command does not count as confirmation of cabinet closure."""
        self._locked = self.isClosed() is True
        if self._locked:
            self._selected = None
        return self._locked

    def unlock(self, medicationId: str) -> bool:
        """Unlock only the requested known compartment if fault-free and closed.

        Return False without opening anything if a precondition fails."""
        if medicationId not in self._compartments or self._faults or self.isClosed() is not True:
            return False
        self._selected = medicationId
        self._locked = False
        self._closed = False
        return True

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

    def setNextOutcome(self, outcome: str) -> None:
        """Arm normal/fail/partial for the next physical action; return None.

        Test control. Unsupported choices raise ValueError before mutation."""
        if outcome not in {"normal", "fail", "partial"}:
            raise ValueError("Unsupported physical outcome.")
        self._next_outcome = outcome

    def setHoldOpen(self, enabled: bool) -> None:
        """Set whether completed test actions leave the drawer open; return None."""
        self._hold_open = bool(enabled)

    def closeDrawer(self) -> bool:
        """Simulate physically closing the drawer; sensor faults remain unresolved."""
        if "drawer_jam" in self._faults:
            return False
        self._closed = True
        return self.lock()

    def getStatus(self) -> dict:
        """Return a fresh snapshot of selected compartment, closure/lock and test settings."""
        return {"selectedMedication": self._selected, "closed": self.isClosed(),
                "locked": self._locked, "holdOpen": self._hold_open,
                "nextOutcome": self._next_outcome}
