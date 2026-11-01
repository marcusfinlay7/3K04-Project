"""INVENTORY FIXTURE — editable startup input, not the live inventory.

PUBLIC INTERFACE: STARTING_INVENTORY is a list of medicationId/name/quantity/
capacity dictionaries. IDs must be unique. Restart after edits.
InventoryManager validates and deep-copies these records. Dispensing never
mutates this file or lets another module manipulate live stock through it.
ANTICIPATED CHANGE: change demo medicines and initial quantities here without
changing the controller or GUI. All quantities are simulated units."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["STARTING_INVENTORY"]

STARTING_INVENTORY = [
    {"medicationId": "001", "name": "Ibuprofen", "quantity": 20, "capacity": 50},
    {"medicationId": "002", "name": "Acetaminophen", "quantity": 25, "capacity": 50},
    {"medicationId": "003", "name": "Amoxicillin", "quantity": 15, "capacity": 50},
    {"medicationId": "004", "name": "Aspirin", "quantity": 30, "capacity": 50},
    {"medicationId": "005", "name": "Cetirizine", "quantity": 18, "capacity": 50},
    {"medicationId": "006", "name": "Loratadine", "quantity": 22, "capacity": 50},
    {"medicationId": "007", "name": "Omeprazole", "quantity": 12, "capacity": 50},
    {"medicationId": "008", "name": "Metformin", "quantity": 28, "capacity": 50},
    {"medicationId": "009", "name": "Atorvastatin", "quantity": 16, "capacity": 50},
    {"medicationId": "010", "name": "Vitamin D", "quantity": 40, "capacity": 50},
]
