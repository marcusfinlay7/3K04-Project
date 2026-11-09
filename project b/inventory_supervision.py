from alarm_management import auto_resolve

LOW_THRESHOLD = 5


def apply_inventory(store, adc_id, medication, quantity, occurred_at, low_stock=None):
    low = quantity <= LOW_THRESHOLD if low_stock is None else low_stock
    applied = store.set_inventory(adc_id, medication, quantity, low, occurred_at)
    if not applied:
        return False
    alarm_id = f"inventory:{medication}"
    if low:
        store.open_alarm(adc_id, alarm_id, "informational", f"Low inventory: {medication}", occurred_at)
    else:
        auto_resolve(store, adc_id, alarm_id, f"Inventory for {medication} restored")
    return True
