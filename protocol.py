from datetime import datetime, timezone

MESSAGE_TYPES = {"heartbeat", "health", "inventory", "alarm", "event", "sync_complete"}


class InvalidMessage(ValueError):
    pass


def require(condition, error):
    if not condition:
        raise InvalidMessage(error)


def validate(message):
    require(isinstance(message, dict), "Message must be a JSON object")
    for field in ("adc_id", "event_id", "type", "timestamp", "data"):
        require(field in message, f"Missing {field}")
    adc, eid, kind, ts, data = (message[k] for k in ("adc_id", "event_id", "type", "timestamp", "data"))
    for value, name, limit in ((adc, "adc_id", 80), (eid, "event_id", 120)):
        require(isinstance(value, str) and value.strip() and len(value) <= limit, f"Invalid {name}")
    require(isinstance(kind, str) and kind in MESSAGE_TYPES, "Unsupported message type")
    require(isinstance(data, dict), "data must be an object")

    try:
        when = datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        raise InvalidMessage("timestamp must be ISO-8601 with timezone") from None
    require(when.tzinfo is not None, "timestamp must be ISO-8601 with timezone")
    ts = when.astimezone(timezone.utc).isoformat(timespec="microseconds")

    def string(name):
        val = data.get(name)
        require(isinstance(val, str) and val.strip() and len(val) <= 240,
                f"Invalid or missing data.{name}")

    if kind == "health":
        require(data.get("status") in ("HEALTHY", "DEGRADED", "FAULT", "MAINTENANCE"),
                "Invalid health status")
    if kind == "inventory":
        string("medication")
        qty = data.get("quantity")
        require(type(qty) is int and qty >= 0, "Invalid inventory quantity")
        require("low_stock" not in data or type(data["low_stock"]) is bool,
                "Invalid low_stock flag")
    if kind == "alarm":
        string("alarm_id")
        string("description")
        for field, allowed, error in (
            ("category", ("system", "informational"), "Invalid alarm category"),
            ("state", ("ACTIVE", "RESOLVED"), "Invalid alarm state"),
        ):
            require(data.get(field) in allowed, error)
    if kind == "event":
        action = data.get("action")
        require(action in ("dispense", "restock", "maintenance"),
                "Invalid operational action")
        string("employee_id")
        if action in {"dispense", "restock"}:
            string("medication")
            require(type(data.get("quantity")) is int and data["quantity"] > 0,
                    "Invalid event quantity")
    return {"adc_id": adc, "event_id": eid, "type": kind, "timestamp": ts, "data": data}
