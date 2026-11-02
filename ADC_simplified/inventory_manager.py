"""Own medicine records and stock/capacity validation; hardware is a separate concern.

PUBLIC INTERFACE: InventoryManager looks up, validates and changes stock, and
returns independent medicationId/name/quantity/capacity records. Invalid startup
data or unknown lookups raise ValueError; rejected changes return False.
Callers must confirm physical movement before addStock/removeStock."""

__all__ = ["InventoryManager"]

from copy import deepcopy
from config import LOCATION_CAPACITY, MAX_MEDICATION_TYPES
from starting_inventory import STARTING_INVENTORY


class InventoryManager:
    def __init__(self, records: list[dict] | None = None):
        if records is None:
            records = STARTING_INVENTORY
        if len(records) > MAX_MEDICATION_TYPES:
            raise ValueError("Too many medicines in starting_inventory.py.")
        self._records = {}
        for record in records:
            medication_id = record.get("medicationId")
            name = record.get("name")
            quantity = record.get("quantity")
            capacity = record.get("capacity")
            if not isinstance(medication_id, str) or not medication_id.isdecimal():
                raise ValueError("Starting medicine IDs must be quoted numbers.")
            if medication_id in self._records:
                raise ValueError(f"Duplicate starting medicine ID: {medication_id}")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"Medicine {medication_id} needs a name.")
            if type(capacity) is not int or capacity <= 0:
                raise ValueError(f"Medicine {medication_id} needs a positive capacity.")
            if type(quantity) is not int or not 0 <= quantity <= capacity:
                raise ValueError(f"Invalid starting quantity for medicine {medication_id}.")
            self._records[medication_id] = deepcopy(record)

    def getStock(self, medicationId: str) -> int:
        """Return recorded quantity for a known string medication ID.

        Read-only. Raises ValueError for an unknown ID; never exposes _records."""
        if medicationId not in self._records:
            raise ValueError("Unknown medication identifier.")
        return self._records[medicationId]["quantity"]

    def getName(self, medicationId: str) -> str:
        """Return the name for a known string medication ID.

        Read-only. Raises ValueError for an unknown ID."""
        if medicationId not in self._records:
            raise ValueError("Unknown medication identifier.")
        return self._records[medicationId]["name"]

    def validateChange(self, medicationId: str, quantity: int, operation: str) -> str:
        """Return a rejection reason, or empty string; never change stock."""
        if not isinstance(medicationId, str) or medicationId not in self._records:
            return "Unknown medication identifier."
        if type(quantity) is not int or quantity <= 0:
            return "Quantity must be a positive whole number."
        record = self._records[medicationId]
        if operation not in ("dispense", "replenish"):
            return "Unknown inventory operation."
        if operation == "dispense" and quantity > record["quantity"]:
            return "Insufficient stock."
        if operation == "replenish" and quantity + record["quantity"] > record["capacity"]:
            return "Storage capacity would be exceeded."
        return ""

    def addStock(self, medicationId: str, quantity: int) -> bool:
        """Add a positive integer quantity after hardware confirms movement.

        True means applied; False means unknown ID, invalid quantity or excess
        capacity. False leaves inventory unchanged. Caller owns confirmation."""
        if self.validateChange(medicationId, quantity, "replenish"):
            return False
        self._records[medicationId]["quantity"] += quantity
        return True

    def removeStock(self, medicationId: str, quantity: int) -> bool:
        """Remove a positive integer quantity after hardware confirms movement.

        True means applied; False means unknown ID, invalid quantity or too little
        stock. False leaves inventory unchanged. Caller owns confirmation."""
        if self.validateChange(medicationId, quantity, "dispense"):
            return False
        self._records[medicationId]["quantity"] -= quantity
        return True

    def getRecords(self) -> list[dict]:
        """Return a deep copy of public medicine snapshots.

        Each has medicationId/name/quantity/capacity. Caller edits do not affect
        stored stock. No input and no state change."""
        return deepcopy(list(self._records.values()))

    def validateRegistration(self, medicationId: str, name: str) -> str:
        """Return a registration rejection reason, or empty text; change no records."""
        if not isinstance(medicationId, str) or not medicationId.isdecimal():
            return "Medicine ID must contain only digits."
        if not isinstance(name, str) or not name.strip():
            return "Medicine name is required."
        if medicationId in self._records:
            return "Medicine ID is already registered."
        if len(self._records) >= MAX_MEDICATION_TYPES:
            return f"Cabinet is full: all {MAX_MEDICATION_TYPES} medicine slots are in use."
        return ""

    def registerMedication(self, medicationId: str, name: str) -> bool:
        """Create a zero-stock record; return False for invalid/duplicate/full input.

        The controller owns authorization and simulated compartment provisioning.
        Registration does not move medicine or persist the record.
        """
        if self.validateRegistration(medicationId, name):
            return False
        self._records[medicationId] = {"medicationId": medicationId, "name": name.strip(),
                                       "quantity": 0, "capacity": LOCATION_CAPACITY}
        return True
