"""INVENTORY MANAGER — owns stock, not dispensing hardware.

RESPONSIBILITY: validate medication records and apply confirmed quantity changes.
HIDDEN DECISION / ANTICIPATED CHANGE: _records is currently a dictionary; its
storage structure and capacity rules can change without callers changing.

PUBLIC INTERFACE: InventoryManager.getStock/getName -> scalar values;
validateChange -> reason or ""; addStock/removeStock/registerMedication -> bool;
getRecords -> independent list of medicine snapshots.
SNAPSHOT CONTRACT: medicationId, name, quantity, capacity. These public values
are copies, NOT handles to _records. Editing a returned snapshot cannot restock
the cabinet. Only this module reads/writes _records.

CALLER EXAMPLE: controller calls inventory.getStock("001").
FORBIDDEN: controller reading inventory._records or invoking private helpers.
Raises ValueError for invalid startup records or unknown lookup IDs; normal
rejected quantity changes return False and preserve stock. See method contracts."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["InventoryManager"]

from copy import deepcopy
from config import LOCATION_CAPACITY, MAX_MEDICATION_TYPES
from starting_inventory import STARTING_INVENTORY


class InventoryManager:
    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
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

    # PUBLIC INTERFACE: callers use these documented operations.
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
        if operation == "dispense":
            if quantity > record["quantity"]:
                return "Insufficient stock."
            return ""
        if operation == "replenish":
            if quantity + record["quantity"] > record["capacity"]:
                return "Storage capacity would be exceeded."
            return ""
        return "Unknown inventory operation."

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

    def registerMedication(self, medicationId: str, name: str) -> bool:
        """Create a zero-stock record; return False for invalid/duplicate/full input.

        Currently exercised by module tests, not wired into the running GUI.
        Does not create a hardware compartment or persist the medicine. The demo
        loads starting_inventory.py instead. Live registration needs controller
        authorization and hardware provisioning before stock can be replenished."""
        if (not isinstance(medicationId, str) or not medicationId.isdecimal()
                or not isinstance(name, str) or not name.strip()
                or medicationId in self._records or len(self._records) >= MAX_MEDICATION_TYPES):
            return False
        self._records[medicationId] = {"medicationId": medicationId, "name": name.strip(),
                                       "quantity": 0, "capacity": LOCATION_CAPACITY}
        return True
