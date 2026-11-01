from datetime import datetime, timezone
from uuid import uuid4
from storage import utc_now

HEARTBEAT_INTERVAL = 5
OFFLINE_AFTER_SECONDS = 15


def mark_offline(store, adc_id):
    cabinet = store.cabinet(adc_id)
    if cabinet and cabinet["connection"] != "OFFLINE":
        store.update_cabinet(adc_id, connection="OFFLINE", health="UNKNOWN", needs_sync=1)
        store.add_event(adc_id, f"system-{uuid4()}", "offline", "Communication lost; health unknown", utc_now())


def check_timeouts(store, now=None, timeout=OFFLINE_AFTER_SECONDS):
    now = now or datetime.now(timezone.utc)
    for cabinet in store.cabinets():
        if cabinet["connection"] != "ONLINE" or not cabinet["last_seen"]:
            continue
        last = datetime.fromisoformat(cabinet["last_seen"])
        if (now - last).total_seconds() >= timeout:
            mark_offline(store, cabinet["adc_id"])


def observed_message(store, adc_id):
    previous = store.cabinet(adc_id)
    was_offline = previous is not None and previous["connection"] == "OFFLINE"
    when = utc_now()
    store.update_cabinet(adc_id, connection="ONLINE", last_seen=when,
                         health="UNKNOWN" if was_offline else None,
                         needs_sync=1 if was_offline else None)
    if was_offline:
        store.add_event(adc_id, f"online-{uuid4()}", "online",
                        "Communication restored; synchronization pending", when)


def apply_health(store, adc_id, status):
    store.update_cabinet(adc_id, health=status)


def sync_finished(store, adc_id):
    store.update_cabinet(adc_id, needs_sync=0)
