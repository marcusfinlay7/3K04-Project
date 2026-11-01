from uuid import uuid4

import alarm_management as alarms
import cabinet_health as health
import inventory_supervision as inventory
from protocol import InvalidMessage, validate
from storage import Storage, utc_now


class MonitoringSystem:
    def __init__(self, db_path=None):
        self.store = Storage(db_path)

    def receive(self, message):
        try:
            event = validate(message)
        except InvalidMessage as error:
            adc_id = message.get("adc_id") if isinstance(message, dict) else None
            self.store.log_error(str(error), adc_id if isinstance(adc_id, str) else None)
            return {"ok": False, "error": str(error)}

        adc_id = event["adc_id"]
        event_id = event["event_id"]
        kind = event["type"]
        data = event["data"]
        timestamp = event["timestamp"]

        descriptions = {
            "health": f"Health: {data.get('status')}",
            "inventory": f"Inventory: {data.get('medication')} = {data.get('quantity')}",
            "alarm": f"Alarm {data.get('alarm_id')}: {data.get('state')}",
            "event": f"{data.get('action')}: {data.get('medication', 'cabinet')}",
            "sync_complete": "History/inventory synchronization complete",
        }

        if kind != "heartbeat":
            saved = self.store.add_event(
                adc_id, event_id, kind, descriptions[kind], timestamp,
                data.get("medication"), data.get("quantity"), data.get("employee_id"),
            )
            if not saved:
                return {"ok": True, "duplicate": True}

        health.observed_message(self.store, adc_id)

        if kind == "health":
            health.apply_health(self.store, adc_id, data["status"])
        elif kind == "inventory":
            inventory.apply_inventory(
                self.store, adc_id, data["medication"], data["quantity"],
                timestamp, data.get("low_stock"),
            )
        elif kind == "alarm":
            alarms.receive_alarm(
                self.store, adc_id, data["alarm_id"], data["category"],
                data["description"], data["state"], timestamp,
            )
        elif kind == "sync_complete":
            health.sync_finished(self.store, adc_id)

        return {"ok": True}

    def mark_offline(self, adc_id):
        health.mark_offline(self.store, adc_id)

    def check_timeouts(self, now=None):
        health.check_timeouts(self.store, now)

    def acknowledge(self, adc_id, alarm_id, employee_id):
        return alarms.acknowledge(self.store, adc_id, alarm_id, employee_id)

    def make_demo_message(self, adc_id, kind, data, event_id=None, timestamp=None):
        return {
            "adc_id": adc_id,
            "event_id": event_id or str(uuid4()),
            "type": kind,
            "timestamp": timestamp or utc_now(),
            "data": data,
        }
