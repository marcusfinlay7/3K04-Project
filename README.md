# ADC demo — group quick guide

## Open the application

Use **Python 3.11 with Tkinter**. Keep all 13 application `.py` files together. Open a terminal in this project folder and run:

```powershell
python gui.py
```

On Windows, `py -3.11 gui.py` also works if Python is installed through the launcher. No third-party packages or separate HMS program are needed. `Emma's Starter Code.py` is the preserved original; `gui.py` starts the new application.

**Tester login: `99999`. This is the only Tester ID.** Enter just the ID; there is no password or role selection. Tester can use every role's actions and the fault/HMS test controls, while still obeying safety checks, stock limits and login lockout.

| Role | Example ID | Access |
|---|---|---|
| Nurse | `12345` | View inventory and dispense |
| Pharmacist | `23456` | View inventory, replenish and review medication history |
| Technician | `34567` | Inventory, full logs, HMS traffic and maintenance/recovery |
| Tester | **`99999`** | All the above plus simulation controls |

For a quick demo, use Tester and open **Split log**, **HMS messages** and **Test controls**. Select an HMS entry to inspect the actual sent packet and reply. The split log separates heartbeat/communication entries from cabinet activity; both log views use the same audit history. Red alarm banners explain problems. Use **Maintenance** to repair hardware, restart software or close the drawer, then **Check recovery**.

## Files you can edit to change the demo

These are data/settings files, separate from the main behaviour modules. **Restart the application after editing them.**

| File | What to edit |
|---|---|
| [valid_logins.py](valid_logins.py) | IDs under the existing Nurse, Pharmacist, Technician and Tester roles. IDs must be unique numeric strings, e.g. `"12345"`. Adding a new role also requires permission changes in AccessControl. |
| [starting_inventory.py](starting_inventory.py) | Medicine IDs, names, starting quantities and each medicine's capacity. IDs must be unique numeric strings; quantity must be between zero and its positive capacity. Currently contains ten medicines. |
| [config.py](config.py) | `DEMO_MODE`, timing profiles, failed-login/missed-heartbeat limits, maximum medicine count and GUI polling interval. `LOCATION_CAPACITY` is the default for newly registered medicines; existing starting medicines use their own `capacity` field. |

Current timer settings, in seconds:

| Timer | Demo (`DEMO_MODE = True`) | Original D1 (`False`) |
|---|---:|---:|
| Login lockout | 10 | 60 |
| Drawer closure | 10 | 30 |
| Heartbeat interval | 5 | 60 |
| Heartbeat response window | 1 | 3 |
| Message retry | 10 | 60 |

Stock, logs, faults and queued messages are in memory. **Restarting resets the demo**, including reloading the starting inventory. Dispensing does not rewrite the data file.

## Modules and their interfaces

The table lists public operations by name; use the linked source for their arguments, return types and failure rules. Each file begins with its responsibility, hidden decisions and interface. `PUBLIC INTERFACE` and `PRIVATE IMPLEMENTATION` sections separate caller operations from internal helpers.

| Module | Owns / hides | Public operations |
|---|---|---|
| [gui.py](gui.py) — `ADCApp` | Layout, input and window state | `main`, `displayMessage`, `displayAlert`, `getUserInput`, `close`. Log/HMS window helpers stay within this GUI module. |
| [access_control.py](access_control.py) — `AccessControl` | ID lookup, session, permissions and lockout | `Authenticate`, `hasPermission`, `currentUser`, `logout`, `lockoutRemaining`, `tick`. Exports immutable `User` and `AuthResult` values. |
| [adc_controller.py](adc_controller.py) — `ADCController` | Workflow order and module coordination | `login`, `logout`, `dispense`, `replenish`, `setMode`, `repairHardware`, `closeDrawer`, `restartSoftware`, `fix`, `tick`; data retrieval: `getCatalog`, `getInventory`, `getLogs`, `getFaults`, `getLogText`, `getDisplayEvents`, `getTraffic`, `getPendingMessages`, `getStatus`; testing: `simulate`, `getSimulation`, `simulationOptions`; internal wiring callbacks: `notifyAlarm`, `notifyModeChange`, `canRecover`. |
| [inventory_manager.py](inventory_manager.py) — `InventoryManager` | Stock records and quantity/capacity validation | `getStock`, `getName`, `validateChange`, `addStock`, `removeStock`, `getRecords`, `registerMedication`. |
| [mode_manager.py](mode_manager.py) — `ModeManager` | Mode state, transition rules and permitted operations | `getMode`, `setMode`, `isOperationAllowed`, `setSafetyCheck`. |
| [fault_handler.py](fault_handler.py) — `FaultHandler` | Registered faults, alarms, closure deadlines and recovery rules | `handleFault`, `reportFault`, `clearFault`, `raiseAlarm`, `clearAlarm`, `getAlarms`, `operationCompleted`, `poll`, `restartSoftware`, `getFaults`, `getCategories`, `isSafe`; test input: `resolveSimulatedSoftwareCondition`. |
| [event_logger.py](event_logger.py) — `EventLogger` | Audit storage, timestamp formatting and export progress | `logEvent`, `exportEvents`, `getEvents`, `formatEvent`, `formatEvents`, `getDisplayEvents`, `timestamp`, `readableTime`, `setUser`, `setSender`. |
| [communication_link.py](communication_link.py) — `CommunicationLink` | Message IDs, pending queue, ACK matching, retries and heartbeats | `sendMessage`, `sendLog`, `sendHeartbeat`, `receiveHeartbeatResponse`, `tick`, `getPending`, `getTraffic`, `getStatus`. |
| [hardware_interface.py](hardware_interface.py) — `HardwareInterface` | Simulated compartments, sensors, locks and confirmed movement | `perform`, `lock`, `unlock`, `isClosed`, `repair`, `closeDrawer`, `getFaults`, `getStatus`; test controls: `supportedFaults`, `injectFault`, `setNextOutcome`, `setHoldOpen`. Exports immutable `HardwareOutcome`. |
| [simulated_hms.py](simulated_hms.py) — `SimulatedHMS` | External mock receiver and controlled communication failures | `receive`, `getReceived`, `getStatus`, `setConnected`, `failNextMessage`, `setMissingHeartbeats`, `restore`. |

**Data retrieval** means returning information for display, such as inventory, logs or status. These methods are not separate windows; the GUI uses their results to populate its windows.

`registerMedication(id, name)` creates a new medicine record with zero stock. It is currently used by module tests, not by the GUI/controller. The app loads medicines from `starting_inventory.py`; registration through the running app still needs to be connected to the controller, GUI and simulated compartments. To change the demo medicines now, edit the starting file and restart (up to `MAX_MEDICATION_TYPES`).

**Information hiding:** GUI requests go through ADCController. Other modules call public operations such as `inventory.getStock(...)`; they do not access another module's `_records` or private helpers. Returned records are copies, and public session/outcome values are immutable. `_` marks internal members by convention; `__all__` declares exports. Neither is a Python security barrier.

## What needs updating in D2

Most original core operation names remain. Update the module guide, interface tables, diagrams and traceability around these design changes:

- **Roles and permissions:** Nurse/Pharmacist/Technician permissions are stored as rules rather than separate role classes. All authenticated roles can view inventory, superseding D2 p.15's restriction; logged-out users see only the login page.
- **Decomposition:** Dispense/Replenish/Fix are controller methods; Normal/Maintenance/Fault are states. Fault management stays in FaultHandler and sending/retries stay in CommunicationLink, without separate classes for each named submodule. Add HardwareInterface and show HMS as an external partner reached through CommunicationLink. Describe concrete hidden decisions using the table above.
- **Safety and recovery:** Fault has Hardware, Software and Closure categories. HMS outages and login lockout are separate conditions. Technician performs explicit repair/restart/closure actions before `fix()` verifies recovery. Document positive transfer quantities, confirmed movement and partial transfers: actual movement changes stock, but incomplete operations return `False`.
- **GUI and logging:** Document the inventory, log, HMS-message and maintenance screens and visual alarms. Audit entries include identity, timestamp, outcome and quantity changes beyond the basic `logEvent(eventType, description)` inputs. Displays use local readable time; stored timestamps retain timezone information. `raiseAlarm` activates a notification; it is not Python exception raising.
- **HMS interface:** Document the current simulated `receive(message) -> reply or None` contract: packets carry `id/type/payload`; replies carry matching `messageId` and `ack` or `heartbeat_ack`. CommunicationLink owns retention/retry decisions. Safe local operation continues during outages. Health (`Normal`/`Degraded`) is a condition summary, separate from operating mode.
- **Persistence — incomplete:** Stock and logs currently reset on restart; saving and restoring them is not implemented.
- **Medicine registration — incomplete:** The inventory method exists, but users cannot yet add a new medicine through the running GUI.
- **Software watchdog — incomplete:** Our D1 acceptance criterion AC-FLT-03-02 specifies detecting unresponsive software within two seconds. Injecting a software fault works, but automatically detecting software that has stopped responding is not implemented.
