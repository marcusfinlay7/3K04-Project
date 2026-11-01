# Hospital Monitoring System — Part B

**SFWRENG / MECHTRON 3K04, Fall 2026 — educational prototype only.** This is NOT medical-device software, does not control dispensing hardware, and contains no patient records. It runs locally on one computer; it does not require internet after the Flask dependency has been installed.

## Run on Windows (VS Code terminal)

1. Unzip the project into a folder. Open the **`project b`** directory in VS Code.
2. Install Flask once (internet needed for the first installation):

   ```powershell
   py -m pip install -r requirements.txt
   ```
3. Start the demo:

   ```powershell
   py app.py --demo
   ```
4. Open **http://127.0.0.1:5000/login** in your browser. The interface refreshes every five seconds.

If `py` is not recognized, use `python` instead. Stop the app with **Ctrl+C**. To reset demo data, stop the app and delete `data/monitoring.db`.

### Demo accounts (fictional, demo PINs only)

| Role | Employee ID | PIN |
| --- | --- | --- |
| Nurse | 101 | 1111 |
| Pharmacist | 102 | 2222 |
| Technician | 103 | 3333 |
| Administrator | 104 | 4444 |

PIN verification uses PBKDF2-SHA256 with a different salt per demo account. Demo PINs are intentionally public, so the application is not suitable for real hospital use.

## Demonstrate the required behaviours

Start `py app.py --demo`, then open a second terminal for the JSON scenario commands below.
The browser is a read-only monitoring dashboard **except for technical alarm acknowledgment** by authorized staff. There are no manual ADC simulator buttons or scenario controls in the GUI.

1. **Low stock:** Run `01_low_inventory`, then `02_restock_clears_alarm` to see the informational alarm appear and clear.
2. **Technical fault:** Run `03_health_fault`, acknowledge the technical alarm in the browser as a technician/admin, and run `04_fault_repaired` to resolve it.
3. **Communication loss:** Run `05_offline_dispense` to simulate a cabinet losing connection and recording a dispense locally. The monitor shows OFFLINE/UNKNOWN, with no routine heartbeat entries in history.
4. **Recovery:** Run `06_reconnect_sync` to replay queued events, restore inventory/health, and see one connection-restored history entry.
5. **Validation:** Run `07_invalid_inventory` to show a negative quantity being rejected and logged without overwriting valid stock.
6. **History:** Run `08_normal_dispense` to demonstrate recording a dispensing event.
7. **Reports:** Select *Reports* to see all events from all cabinets together.
8. **Permissions:** Sign in as **101 / 1111** to confirm the nurse cannot view reports or acknowledge technical alarms.

The simulator sends heartbeats every **5 seconds**, with an **offline threshold of 15 seconds**. Routine heartbeats are not recorded or shown. Only communication loss and reconnection appear in history. The dashboard also updates every five seconds. Display times use **Eastern Time (EST/EDT automatically)** in 24-hour `YYYY-MM-DD HH:MM:SS` format; stored event timestamps remain UTC. The manually triggered disconnect used in scenarios is immediate.

## JSON scenarios (run from the terminal)

**Keep the dashboard running in one terminal.** Open a **second VS Code terminal**
(Terminal > New Terminal) to trigger scenarios. You do not need to
log into the Scenarios page; that page has been removed.

Terminal 1 — server (leave it running):

```powershell
py app.py --demo
```

Terminal 2 — JSON scenarios:

```powershell
py app.py --run 01_low_inventory
py app.py --run 02_restock_clears_alarm
```

**Watch the dashboard in the browser** (`http://127.0.0.1:5000`): the cabinet
values, alarms, and history update automatically. Terminal commands print
what they ran and the resulting inventory/health. The browser supports login, alarm acknowledgment, and a single unfiltered event report, but no ADC simulator/scenario controls.

Each scenario is stored as a `.json` file in `scenarios/`. Change the JSON in
VS Code, save, and run the same command again — the running server reads the
file on demand, **without a restart**. The command name is the filename's stem,
without `.json` (both forms work).

All scenario commands talk to the **already running server** through a
loopback-only, token-protected local endpoint, so they share the same simulated
ADC state as the dashboard. If you use a non-default port, add `--port 5001`
to both the server command and the scenario command. The local token is stored
in `data/.scenario_cli_token` and is excluded from Git; treat it as demo-only.

For example, `01_low_inventory.json`:

```json
{
  "name": "Low stock alarm",
  "adc_id": "ADC-01",
  "steps": [
    {"action": "reconnect"},
    {"action": "set_inventory", "medication": "Ibuprofen", "quantity": 2}
  ]
}
```

The JSON describes **actions for a simulated ADC**, not direct changes to the monitoring database.

Available `action` values:

| Action | Effect |
| --- | --- |
| `set_inventory` | Set simulated ADC stock and report its current snapshot; requires `medication`, `quantity` (zero or more) |
| `dispense` / `restock` | Simulated dispensing/restocking event; requires `medication`, positive `quantity` |
| `disconnect` | ADC goes offline, dashboard shows health UNKNOWN |
| `reconnect` | Replays queued messages and synchronizes inventory and health |
| `fault` / `repair` | Simulate technical health fault and subsequent repair |
| `door_fixed` | Clears door alarm if present |
| `invalid_inventory` | Sends rejected inventory message (negative `quantity`) and logs the error |

Each JSON scenario describes `name`, `adc_id`, and a list of `steps`. The demo runner does not perform a separate full scenario-validation pass; it runs the steps and reports execution errors. Incoming ADC messages are still checked by `protocol.validate()`, so invalid quantities cannot overwrite inventory. JSON is read again each time a scenario runs and cannot execute arbitrary Python code.

Recommended live demo order:

- **01** low stock → **02** auto-clear after restocking.
- **03** technical fault → manually acknowledge from ADC-02's alarm table → **04** resolved technical fault.
- **05** disconnect and queue a dispense → observe OFFLINE/UNKNOWN and unchanged central inventory → **06** reconnect, replay, synchronize.
- **07** invalid inventory rejected and logged; **08** normal dispensing and history.

The scripts are reproducible *demo sequences*, not automated pass/fail tests. Some scripts intentionally change the same cabinet's state. They do not reset the whole database between runs. Each `--run` executes its steps immediately and prints a cabinet URL. Execution is not transactional; if an action fails midway, earlier steps stay applied.

The project ships with editable JSON demonstrations. The previously built automated regression tests were used during development, but are not part of this compact demo bundle.

## Demonstration checks

Use terminal JSON scenarios to demonstrate the expected behaviour while the browser shows the results. These
are command-line demonstrations, **not automatic pass/fail tests**. The original
14 automated regression tests were run while refactoring but are not shipped in
this compact demo bundle. If you change the core monitoring logic later, use
independent automated tests again before submitting.

## Files and architecture

| File | Responsibility |
| --- | --- |
| `app.py` | Login, dashboard routes, alarm acknowledgment and server/terminal entry point |
| `authentication.py` | Demo PIN verification, roles and permissions |
| `monitor.py` | Validated ADC event processing and application coordination |
| `protocol.py` | Validates the internal ADC message format; real Part A transport will be added later |
| `cabinet_health.py` | Heartbeats, communication timeouts and unknown-health state |
| `inventory_supervision.py` | ADC inventory snapshots and low-stock detection |
| `alarm_management.py` | Informational/system alarm lifecycle and acknowledgment |
| `storage.py` | SQLite schema and queries, hidden from other modules |
| `reporting.py` | Read-only dashboard data and a combined event report |
| `demo_scenarios.py` | Simulated ADCs, JSON scenario execution and terminal-to-server requests |
| `scenarios/` | Editable JSON demo inputs invoked from the terminal |
| `templates/` | HTML pages and local CSS, no online assets |
| `docs/` | Traceability, design notes and open Part A decisions |

### Recommended order to read the code

To understand the program, start at `app.py` (`main()` at the bottom starts
Flask, and `create_app()` defines the pages). Next read `demo_scenarios.py`
to see how the simulated ADC generates messages. `protocol.py` validates the
message format, and `monitor.py` forwards validated messages to the appropriate
modules (`cabinet_health.py`, `inventory_supervision.py`, and
`alarm_management.py`). `storage.py` handles the database, while
`reporting.py` reads the database for the web pages. `authentication.py`
checks which employees can perform each action.

This organization separates the user interface, message processing, simulated
hardware, and database so you can change one part without rewriting the rest.

## Important limits

- The *actual* Part A network protocol, message names, fields, authentication, and recovery mechanism remain **unconfirmed**. All current messages go through the replaceable `protocol.py` boundary. We did **not** claim real integration.
- There is no physical cabinet connection, no production access control, no TLS, no reliable delivery guarantee from real hardware, and no patient-specific logic. A full hospital system needs professional safety and security engineering.
- SQLite stores valid source events using `(adc_id,event_id)` to reject duplicates. Older inventory snapshots cannot override newer ones. Invalid messages are logged separately and do not overwrite state.
- A reported ADC heartbeat proves connectivity, not good health. Heartbeats refresh the connection timer but do not generate history rows; only OFFLINE and ONLINE transitions are recorded. After a disconnect, the monitor displays `UNKNOWN` until the ADC sends a fresh health report; synchronization remains pending until `sync_complete`.
- Inventory changes only because a simulated ADC reports them; the Monitoring System does not dispense or independently edit medication inventory.
- The deliverable's **final polished Word document and real Part A integration are not included**. `docs/DESIGN_NOTES.md` and `docs/TRACEABILITY.csv` are drafting aids for Deliverable 2.

## Merging existing project files

For a clean install, extract this ZIP into a **new folder**, then open that
folder in VS Code. If replacing files in an older project folder, remove these
old modules after copying the new files: `main.py`, `scenario_runner.py`,
`adc_communication.py`, `request_handling.py`, `historical_data.py`,
`operator_dashboard.py`. They are no longer imported. Optionally remove the
old `tests/` folder and `run_windows.bat`. Do not delete `data/monitoring.db` if
you want to keep your previous demo history.
