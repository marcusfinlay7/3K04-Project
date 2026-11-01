import hashlib
import hmac

EMPLOYEES = {
    "101": {"role": "nurse", "salt": "68413d53d51de99b1e3acfbe03753a55", "pin_hash": "cadfa2371d085079a7d9cf28490849972cd145229c8ccb45123d89d09330dcae", "active": True},
    "102": {"role": "pharmacist", "salt": "fcd613ce95422534856b44f5e3c7c6bb", "pin_hash": "32c0c67c9cfc7bfcb833bff4dec3cb6931874ea50898aaae7f4ac0cff072dada", "active": True},
    "103": {"role": "technician", "salt": "816e2091fefbf7587c93d4d4722b443d", "pin_hash": "0447ec11bddd198a5706c60dacc33f004bddaff9b6b013432463623e49acc0a9", "active": True},
    "104": {"role": "administrator", "salt": "df2984cd8105a8f443d337930c842c0f", "pin_hash": "a30e58f6978b52b1c54aa8490f65edf54327c119bc8f413cef39787b6ffe1a1f", "active": True},
}

PERMISSIONS = {
    "nurse": {"view_status", "view_inventory", "view_alarms"},
    "pharmacist": {"view_status", "view_inventory", "view_alarms", "view_history", "view_reports"},
    "technician": {"view_status", "view_inventory", "view_alarms", "view_history", "view_reports", "acknowledge_system_alarm"},
    "administrator": {"view_status", "view_inventory", "view_alarms", "view_history", "view_reports", "acknowledge_system_alarm"},
}


def authenticate(employee_id, pin):
    employee = EMPLOYEES.get(str(employee_id))
    if not employee or not employee["active"] or not isinstance(pin, str):
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(employee["salt"]), 120_000)
    return hmac.compare_digest(candidate, bytes.fromhex(employee["pin_hash"]))


def role_for(employee_id):
    employee = EMPLOYEES.get(str(employee_id))
    return employee["role"] if employee and employee["active"] else None


def has_permission(employee_id, action):
    role = role_for(employee_id)
    return role is not None and action in PERMISSIONS.get(role, set())
