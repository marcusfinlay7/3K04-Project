"""Read-only queries for the dashboard and event report."""


def overview(store):
    return store.cabinets()


def detail(store, adc_id):
    cabinet = store.cabinet(adc_id)
    if cabinet is None:
        return None
    return {
        "cabinet": cabinet,
        "inventory": store.inventory(adc_id),
        "alarms": store.alarms(adc_id),
        "history": store.history(adc_id, limit=80),
    }


def generate_report(store):
    """All cabinet events and rejected messages, newest first."""
    records = store.history()
    for error in store.errors():
        records.append({
            "adc_id": error["adc_id"] or "Unknown",
            "occurred_at": error["logged_at"],
            "event_type": "invalid_message",
            "description": error["reason"],
            "medication": None,
            "quantity": None,
            "employee_id": None,
        })
    records.sort(key=lambda event: event["occurred_at"], reverse=True)
    return records
