from uuid import uuid4
from authentication import has_permission
from storage import utc_now


def receive_alarm(store, adc_id, alarm_id, category, description, state, occurred_at):
    if state == "ACTIVE":
        store.open_alarm(adc_id, alarm_id, category, description, occurred_at)
    else:
        store.resolve_alarm(adc_id, alarm_id, occurred_at)


def acknowledge(store, adc_id, alarm_id, employee_id):
    if not has_permission(employee_id, "acknowledge_system_alarm"):
        return False
    when = utc_now()
    if not store.acknowledge_alarm(adc_id, alarm_id, employee_id, when):
        return False
    store.add_event(adc_id, f"ack-{uuid4()}", "acknowledgment",
                    f"System alarm {alarm_id} acknowledged by {employee_id}", when, employee_id=employee_id)
    return True


def auto_resolve(store, adc_id, alarm_id, reason):
    when = utc_now()
    if store.resolve_alarm(adc_id, alarm_id, when):
        store.add_event(adc_id, f"resolved-{uuid4()}", "alarm_resolved", reason, when)
