# Simplified ADC

From the repository root, with Python 3.11+ and Tkinter:

```powershell
python ADC_simplified/gui.py
```

This directory runs independently of `ADC/`; it needs no third-party packages.
Sign in with an ID only: Nurse `12345`, Pharmacist `23456`, Technician `34567`,
or Tester `99999`. All authenticated roles can see inventory. Tester has all role
actions and simulation controls, but still obeys stock, safety and lockout rules.

## Module ownership

| File | Owns |
|---|---|
| `gui.py` | Tk widgets, confirmations, auxiliary windows and polling |
| `adc_controller.py` | Authorization and workflow coordination through public interfaces |
| `access_control.py` | ID lookup, session, role permissions and login lockout |
| `inventory_manager.py` | Medicine records, validation, stock and capacity |
| `hardware_interface.py` | Simulated compartments, sensors, locks and confirmed movement |
| `mode_manager.py` | Operating mode, permitted transitions and mode restrictions |
| `fault_handler.py` | Fault categories, alarms, closure deadline and recovery checks |
| `event_logger.py` | Audit records, display formatting and export progress |
| `communication_link.py` | Packets, matching ACKs, retained data, retries and heartbeats |
| `simulated_hms.py` | External mock receiver and controllable reply failures |
| `config.py` | Both timing profiles, active default and numeric limits |
| `valid_logins.py` | Editable startup IDs |
| `starting_inventory.py` | Editable starting medicines, quantities and capacities |

Restart after changing settings or fixtures. The unchanged default is demo timing:
lockout/closure/heartbeat/response/retry = **10/10/5/1/10 seconds**. Set `DEMO_MODE`
to `False` for the preserved D1 profile: **60/30/60/3/60 seconds**.

## Following the code

- **Login:** GUI submits an ID to `ADCController.login`, then
  `AccessControl.Authenticate` expires lockout, checks the ID, updates the session
  and records the result. Invalid attempts replace any previous session.
- **Transfer:** start at `dispense` or `replenish`; `_transfer` follows immediately.
  Read downward through fault polling, authorization/mode checks, stock validation,
  hardware confirmation, actual stock change, audit and HMS reporting. Partial
  movement changes stock by the confirmed amount but returns `False`.
- **Registration:** Pharmacist/Tester selects **Register medicine**, enters a
  unique numeric ID and nonempty name, then confirms. Controller
  `registerMedication` checks role, Normal mode, available capacity and safe
  closure, provisions a simulated compartment, and adds a zero-stock record.
  It audits the attempt and queues the new medicine's ID/name/quantity/capacity
  for HMS. The new row is selected automatically; use **Add stock** to replenish.
- **Recovery:** `repairHardware`, `restartSoftware` and `closeDrawer` are explicit
  maintenance actions. `fix` clears only resolved conditions and asks ModeManager
  to restore Normal. Clearing a banner alone cannot clear a fault.
- **Background work:** GUI polling calls controller `tick`. It temporarily uses
  System audit identity, checks faults and timers, updates health, exports logs,
  then restores the user identity. CommunicationLink retains messages until a
  matching ACK; local permitted work continues during an outage.

The constructor shows callback wiring. `notifyAlarm` reports alarms to HMS;
`notifyModeChange` reports transitions; `canRecover` supplies permission checks.
Returned snapshots remain independent copies. For compatibility, permission and
remaining-lockout queries can expire lockout; `getStatus` also clears its expired
alarm and feedback. Other display queries do not perform maintenance.

## What changed

Login and transfer checks now use straightforward early exits. The shared transfer
workflow is beside its public entry points, simulation actions make direct calls,
fault support/categories use one table, and heartbeat tracking keeps only its ID
and deadline instead of retaining another full packet. Duplicate commentary was
removed while keeping public contracts and explanations of safety decisions.
Small existing modules were retained where their implementation was already clear.
Configuration and startup fixtures are byte-for-byte copies. The GUI retains its
existing code and adds the registration button and prompts requested afterward.

## Demonstrating registration

The cabinet still has **10 slots**, and the default starting list uses all ten.
To demonstrate successful registration, remove one entry from this version's
`starting_inventory.py` and restart. Register a medicine using Pharmacist `23456`
or Tester `99999`, then replenish it. Keep the removed entry available to restore
the default fixture afterward. A zero-stock medicine still occupies a slot;
dispensing its last unit does not delete its record. Registration is rejected
when all slots are occupied. The tests exercise a nine-medicine startup fixture
without modifying the actual starting file.

Registrations and stock remain in memory and reset on restart. There is no live
medicine-removal workflow or persistence.

## Functions without live GUI callers

`ADCController.getCatalog` and `simulationOptions` are used by tests;
`getLogText` is used by the comparison harness and calls `EventLogger.formatEvents`.
The GUI uses inventory records and formatted display events instead. These public
interfaces were retained for compatibility. `ADCApp.getUserInput` currently has
no callers; registration uses `askstring` directly to distinguish Cancel (`None`)
from an invalid empty field. `resolveSimulatedSoftwareCondition` is reachable via
the controller's `resolve_software` test action, but the GUI uses the authorized
`restartSoftware` maintenance action instead. Inventory `registerMedication` is
now used by the live registration workflow.

## Verification and limitations

```powershell
python -B -m unittest discover -s ADC_simplified/tests -v
python -B ADC_simplified/verification/check_originals.py
```

The original baseline passed **76 tests**; this version now passes **97**, including
the original 76 tests, eight compatibility checks and 13 registration tests. See
[verification/results.md](verification/results.md) for scope and commands.
Existing scenarios match after explicitly allowing the new registration action
and button. Registration is an intentional behavior addition.

Existing limitations remain: all state is in memory; no automatic software
watchdog, session expiry, real hardware or real HMS integration.
The software restart action is simulated. Inventory uncertainty remains blocked
because there is no reconciliation workflow. Tests are not exhaustive, do not
establish hard real-time guarantees, and do not cover physical integration or
every OS/display configuration.
