"""LOGIN FIXTURE — editable startup input, not the active authentication state.

PUBLIC INTERFACE: VALID_LOGINS maps role names to lists of numeric-string IDs.
Each ID must be unique. Restart after edits. AccessControl validates and copies
these inputs into its own private lookup; it does not share a mutable session
with this file. ANTICIPATED CHANGE: demo IDs can change without editing GUI code.
Tester has all role actions plus simulation controls. These are demo IDs."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["VALID_LOGINS"]

VALID_LOGINS = {
    "Nurse": ["12345", "71842", "39561", "86207", "54093"],
    "Pharmacist": ["23456", "64918", "30752", "98143", "42680"],
    "Technician": ["34567", "57294", "80316", "16928", "75402"],
    "Tester": ["99999"],
}
