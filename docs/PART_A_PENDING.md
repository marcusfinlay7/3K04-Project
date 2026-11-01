# Open Part A integration questions (intentionally deferred)

The current simulator uses a suggested **internal** envelope:

```json
{
  "adc_id": "ADC-01",
  "event_id": "unique-id-from-adc",
  "type": "inventory",
  "timestamp": "2026-10-29T21:00:00-04:00",
  "data": {"medication": "Ibuprofen", "quantity": 8}
}
```

Possible `type` values: `heartbeat`, `health`, `inventory`, `alarm`, `event`, `sync_complete`. Provisional ADC request/response messages are deferred until Part A integration. The external format is **not approved by Part A** and none of these field names should be presented as agreed requirements.

Before integrating with Part A, confirm how its software communicates (HTTP/TCP/process interface), identification/authentication of ADCs, actual message payloads, timestamps and unique IDs, inventory snapshot versus change events, alarm IDs/categories/clear confirmations, dispensed-event content, retries and acknowledgments, full snapshot/since-outage replay semantics, and configuration/authorization queries.

Only after those decisions should `protocol.py` be adapted and transport-level tests added. The simulator exercises the intended behaviours without requiring any specific Part A implementation.
