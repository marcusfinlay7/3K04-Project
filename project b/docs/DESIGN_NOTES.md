# Deliverable 2 — Technical design notes (draft, not the final submission)

## Context and boundary

Part B supervises multiple ADCs, storing received inventory, health, operational events, and alarms for authorized hospital staff. It never controls an ADC's dispensing mechanism. The real Part A interface is undefined; `protocol.py` is a **demonstration contract** and isolates external transport/schema changes. See `PART_A_PENDING.md`.

### Four-variable model (provisional)

| Perspective | Prototype interpretation |
| --- | --- |
| Monitored environment variables (MON) | ADC connectivity, ADC-reported inventory/health/alarms, reported dispensing/restocking/maintenance actions |
| Software input variables (IN) | Validated ADC event envelopes containing ID, event type, time and data; dashboard alarm acknowledgment and employee PINs |
| Controlled environment variables (CON) | What the operator sees: health/connection display, alarm status and reports; acknowledgments recorded by monitoring system |
| Software output variables (OUT) | Browser pages and audit entries (including communication-loss/recovery events) |

**NAT assumptions:** The ADC is authoritative for its physical inventory/health, reports can be delayed or duplicated, and communication can fail. Monitoring cannot know current physical health during loss of communication.

**REQ rules:** The display must never label a disconnected ADC healthy. Events must be associated with source ADC and time. Duplicate event IDs must not duplicate actions. Invalid values cannot overwrite valid stored inventory. Acknowledging a technical alarm does not resolve it; ADC confirmation resolves it. Informational low-inventory alarms clear when a newer inventory report indicates stock is no longer low.

## Module API (code-aligned, abbreviated)

| Module | Exported operation | Inputs -> outputs and notable semantics |
| --- | --- | --- |
| `storage.py` | `Storage(path)`, `add_event`, `set_inventory`, `history`, `alarms`, `cabinets` | SQLite queries; raises DB exceptions; `add_event` returns False for duplicate; does not expose SQL outside storage |
| `authentication.py` | `authenticate(id,pin)`, `has_permission(id,action)` | Boolean; denies inactive/unknown ID, unknown action, wrong PIN |
| `protocol.py` | `validate(message)` | Validated dictionary or `InvalidMessage`; rejects missing keys, invalid quantities and unsupported types |
| `monitor.py` | `MonitoringSystem.receive(message)` | Validates, stores unique non-heartbeat events, updates state; returns success/duplicate or error |
| `monitor.py` | `MonitoringSystem.mark_offline(adc_id)`, `.check_timeouts(now)` | Marks communication lost, health unknown, sync pending; retains history |
| `monitor.py` | `MonitoringSystem.acknowledge(adc_id,alarm_id,id)` | Boolean, checks role and active technical alarm; acknowledgment is not resolution |
| `cabinet_health.py` | `observed_message`, `apply_health`, `check_timeouts`, `sync_finished` | Maintains availability/health; offline after three expected heartbeats |
| `inventory_supervision.py` | `apply_inventory` | ADC snapshot, quantity and optional ADC-provided low flag; no local physical write |
| `alarm_management.py` | `receive_alarm`, `acknowledge`, `auto_resolve` | Category and life cycle, system alarm role gating |
| `reporting.py` | `generate_report(store)` | Combined events from all cabinets (no report filters), plus rejected messages |
| `reporting.py` | `overview`, `detail` | Read-only values supplied to UI |
| `demo_scenarios.py` | `DemoADCs.pause`, `.restore`, `.local_event`; `run_scenario` | Simulated ADCs, replay and direct JSON scenario execution |
| `app.py` | `create_app(db_path,start_simulator,cli_token)`; CLI dashboard/JSON execution | Flask factory, routes, login, alarm acknowledgment, reports and demo server startup |

## State machine semantics

**Connection:** `UNKNOWN -> ONLINE` on first valid ADC message. `ONLINE -> OFFLINE` after 15 seconds since last valid message, or by a demo disconnect command. `OFFLINE -> ONLINE` on receipt of a valid message; health remains `UNKNOWN` until a subsequent health report. `needs_sync=1` until `sync_complete`.

**Technical alarm:** `ACTIVE (unacknowledged) -> ACTIVE (acknowledged)` when a technician/admin acknowledges; either active state -> `RESOLVED` only when reported by ADC. Historical audit entries retain both acknowledgments and incoming resolution events.

**Informational inventory alarm:** Created/maintained from low-stock ADC reports or (in this demo) quantity <=5; it clears only when a newer inventory snapshot shows the stock is no longer low. There is no manual acknowledgement.

## Safety-related invariants

- `connection=OFFLINE` => `health=UNKNOWN` (no stale healthy status presented as current).
- No accepted inventory entry has negative quantity; invalid messages leave valid values unchanged.
- No monitoring-side operation dispenses a dose or modifies the physical ADC.
- A role not permitted to acknowledge a system alarm cannot do so in the service layer or web route.
- Identical `(adc_id,event_id)` is processed at most once.
- Missed events are replayed by the *simulated* ADC, not invented by the monitoring database.

## Assumptions and decisions needing inclusion in submission

- Five-second ADC heartbeat and UI refresh; fifteen-second offline timeout (chosen prototype thresholds). Routine heartbeats are not persisted or displayed. Offline/online transitions are stored; historical heartbeat rows from older databases are hidden.
- No patient identifiers in history, only employee ID, medication, amount, action and timestamp.
- Events kept without automatic deletion in the prototype; five-year retention is a proposed requirement, **not guaranteed** by local storage or backups.
- Local SQLite and fictional credential dictionary keep the course demo simple. For actual deployment these are not sufficient safeguards.
- One unfiltered event report combines operations, problems, and rejected messages.
- Each ADC is the source of truth; the central server is an observational mirror and never assumes unavailable hardware is healthy.
- No dependency on Part A until integration. Change the adapter after coordinating external messages with that team.

## Verification

The original automated test suite was used during the refactor. JSON demos
exercise monitoring scenarios via terminal commands, but do not replace automated pass/fail testing.
Live browser interactions should be confirmed locally with Flask installed.
The real Part A communication interface and medical safety/security validation
remain outside this course simulator.
