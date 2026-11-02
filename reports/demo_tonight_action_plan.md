# Deliverable 2: detailed action plan for the simplified ADC

**Assumed assignments:** I assume **Marcus** is responsible for the runnable simplified application, demo preparation, technical verification and HMS explanation; **Deborah** is responsible for the module guide, public interfaces and traceability; and **Emma** is responsible for the precise specification, four-variable model, assumptions and introduction. These are suggested assignments based on the existing checklist, not confirmed commitments. Everyone needs to understand the overall application and be able to answer questions about modules they did not write.

**Demo:** Monday, November 2, 2026. **Document submission:** Friday, November 6, 2026.

**Writing status: complete.** The [progress checklist](demo_plan_progress.md) records completion of this planning document. Task checkboxes below remain unchecked because they are work for the group to carry out.

**How to use this detailed file:** start with the master checklist in section 3, then read your assigned section: Deborah in section 4, Emma in section 5, Marcus in section 6. Section 7 is the page-by-page editor's checklist; section 8 is the shared rehearsal. Sections 9 and 14 are reference material, not extra material everyone must memorize tonight. Section 10 explicitly separates work that can wait.

## 1. What the priorities mean

| Priority | Meaning | What to do tonight |
|---|---|---|
| **P0 — demo essential** | Needed to run the demonstration or explain a central design decision accurately. | Complete and rehearse before the demo. A short correct explanation is enough; polished prose is not the goal. |
| **P1 — important before the demo** | A visible mismatch or missing detail the TA could reasonably ask about. | Correct the main table/diagram or prepare a clear note beside it. Do this after the runnable demo is secure. |
| **P2 — final-document work** | Required documentation or completeness work that need not take priority over rehearsal tonight. | Finish before submission; do tonight only if the higher priorities are ready. |
| **P3 — optional polish / future work** | Formatting refinements or additional implementation beyond this preparation task. | Do not let this displace the demo or core explanations. |

These are preparation priorities, not predicted marks or official exemptions. The D2 instructions ask for a document about 95% ready at the demo. Your requested triage is to defer the **written introduction and written implementation notes** if necessary. That is reasonable as a work-order decision: everyone still needs to give a short introduction and point from the design to the code verbally.

**Tonight's objective:** the three of you can run the same version, show normal and off-normal behavior, point to the modules involved, and explain why the implementation behaves that way.

## 2. Important current facts

- The application to demonstrate is `ADC_simplified/`, launched from the repository root with `python ADC_simplified/gui.py`.
- Live medicine registration is already implemented. It is not an outstanding coding task.
- The actual simplified `starting_inventory.py` currently contains **nine medicines, IDs 001–009**. The cabinet limit is still **ten medication types**. One registration slot is already free; do not remove another medicine just because an older README says all ten are occupied.
- The current default is `DEMO_MODE = True`. Demo timings are lockout 10 seconds, drawer closure 10 seconds, heartbeat interval 5 seconds, response window 1 second and data retry 10 seconds.
- Hardware and HMS are simulated in the same Python process. Registration, inventory, audit history and pending messages are in memory.
- A previous version passed 97 tests. The nine-medicine fixture change makes some ten-medicine assertions and original-versus-simplified comparisons stale. This plan does not claim the current fixture has a fresh passing full-suite result.
- This file specifies work to do. Creating it does not itself complete the listed document edits, test adaptations or rehearsal.

## 3. Master checklist and assumed owners

| ID | Priority | Owner | Task | Minimum useful result before the demo |
|---|---|---|---|---|
| M1 | **P0** | **Marcus** | Agree on one version and launch it on the demo machine. | Everyone uses `ADC_simplified`; the GUI is open and usable. |
| M2 | **P0** | **Marcus**, all rehearse | Rehearse login, dispensing, rejection, registration and replenishment. | A repeatable demonstration with known IDs and stock values. |
| M3 | **P0** | **Marcus**, all rehearse | Rehearse fault detection, blocked transfers and technician recovery. | Explain repair versus Check recovery and show both. |
| M4 | **P0** | **Marcus**, all understand | Prepare HMS outage/reconnection and packet explanation. | Show retained messages and explain matching ACKs and continued local operation. |
| D1 | **P0 explanation / P1 table edit** | **Deborah** | Correct the module hierarchy on page 8. | Real modules and their responsibilities match the files. |
| D2 | **P1** | **Deborah**, Marcus checks | Correct interfaces on pages 9–13, including registration and hardware. | The demonstrated method names, inputs, results and failure behavior are accurate. |
| E1 | **P0 explanation / P1 figure edit** | **Emma** | Correct the four-variable model on page 3. | Explain one concrete monitored/input/output/controlled example. |
| E2 | **P1** | **Emma**, Marcus checks | Correct the safety specifications on pages 3–7. | Stock, exact/partial completion, role checks and mode restrictions match the demo. |
| E3 | **P1** | **Emma** | Replace the outdated assumptions on page 16. | Inventory visibility, timings, roles, capacity, simulation and reset behavior are correct. |
| M5 | **P1** | **Marcus** | Fill the HMS interface and degraded-behavior tables on page 13. | A small accurate table covering messages, replies, retries and outages. |
| D3 | **P1 demonstrated paths / P2 complete table** | **Deborah** | Finish traceability on pages 14–16. | Demonstrated requirements map to actual modules and methods; complete remaining rows before submission. |
| M6 | **P1** | **Marcus** | Reconcile nine-medicine startup, tests and README claims. | Correct fixture-dependent expectations and report the actual verification result. |
| A1 | **P0** | **Marcus, Deborah and Emma** | Practise explaining other people's modules. | Each person can trace a transfer, a fault and an outage without prompting. |
| E4 | **P2 — can wait for the demo** | **Emma** | Write the introduction and context. | A one-sentence verbal introduction is enough for rehearsal; write the section before submission. |
| M7 | **P2 — can wait for the demo** | **Marcus** | Write implementation notes. | Be ready to point to source verbally; the written section can follow. |
| E5 | **P2** | **Emma**, Deborah cross-checks | Reconcile older D1 diagrams and requirement differences. | Identify intentional differences; finish consistent written mappings before submission. |
| D4 | **P2/P3** | **Deborah**, Emma edits prose | Clean up names, placeholders, checklist status and formatting. | Remove misleading placeholders on pages you will show; cosmetic polish can wait. |
| A2 | **P3 — do not add tonight** | **Marcus**, group agrees | Keep missing future features separate. | Clearly describe limits; do not rush persistence, a watchdog or real integration into the demo. |

## 4. Deborah: module guide, interfaces and traceability

### D1 — Correct the module hierarchy — P0 to explain, P1 to edit — Deborah

**Where:** page 8, "Modular Design and Interfaces."

**What is wrong:** the table lists role classes, operation submodules and mode submodules that are not separate classes/modules in the implementation. It also uses descriptions such as "All secrets" and "Secrets for Access Control Class," which do not tell the reader what is hidden. HardwareInterface is absent even though the later traceability table refers to it.

**Make these edits:**

- [ ] Replace "Whole System / All secrets" with an application overview, rather than presenting the entire ADC as a module that owns every decision.
- [ ] Remove the claim that Nurse, Pharmacist and Technician are separate role classes. Explain that `AccessControl` stores a permission table and an immutable `User` value identifies the current session. Include Tester.
- [ ] Show `dispense`, `replenish`, `registerMedication` and `fix` as operations of `ADCController`, not separate process-step modules.
- [ ] Show Normal, Maintenance and Fault as values managed by `ModeManager`, not separate mode classes.
- [ ] Remove separate "Fault Manager" and "CommunicationSend" implementation boxes unless clearly labeled as conceptual responsibilities within the actual modules.
- [ ] Add `HardwareInterface`, including simulated compartment provisioning for registration.
- [ ] Show `SimulatedHMS` as the in-process stand-in for an external partner, reached through `CommunicationLink`. It does not control ADC inventory, permissions or recovery.
- [ ] List configuration and startup data separately from the behavior modules.
- [ ] Replace "implantation from code" with a concrete GUI responsibility such as "collects input, displays results and requests controller operations."

Use this replacement content:

| Module/file | What it owns | Decision hidden from other modules | Simple explanation for the TA |
|---|---|---|---|
| `gui.py` / `ADCApp` | Widgets, prompts, confirmations, window lifetime and polling | How requests and results are presented | "The GUI collects input; the controller decides whether it is allowed." |
| `access_control.py` / `AccessControl` | ID lookup, sessions, role permissions and lockout | Account lookup and permission/failure-counter representation | "Other modules ask whether the current user may perform an action." |
| `adc_controller.py` / `ADCController` | Coordination and protected request entry points | Workflow ordering and module wiring | "It checks the request and calls each module through its public interface." |
| `inventory_manager.py` / `InventoryManager` | Medicine records, validation, stock and capacity | Record storage and quantity/registration rules | "It owns stock; callers do not edit its dictionary directly." |
| `hardware_interface.py` / `HardwareInterface` | Compartments, closure sensor, locks and movement simulation | How hardware reports movement or failure | "A requested quantity is not proof that it moved." |
| `mode_manager.py` / `ModeManager` | Current mode, permitted transitions and operation restrictions | Transition and mode-operation rules | "Role permission and operating-mode permission are separate checks." |
| `fault_handler.py` / `FaultHandler` | Fault registration, categories, alarms and recovery conditions | Fault classification, closure deadline and recovery rules | "Repair resolves the condition; recovery checks whether operation can resume." |
| `event_logger.py` / `EventLogger` | Audit storage, timestamps, formatting and export progress | Stored/display representations and export position | "One audit history supplies the log views and exported batches." |
| `communication_link.py` / `CommunicationLink` | IDs, delivery attempts, ACK checks, retries and heartbeats | Queue and protocol bookkeeping | "It keeps data until the correct acknowledgement arrives." |
| `simulated_hms.py` / `SimulatedHMS` | Mock connection and controlled responses | How simulated drops or invalid replies are produced | "It is the test partner, not a real HMS connection." |
| `config.py` | Immutable timings and limits | Choice of demo versus D1 timing values | "Change timing settings here and restart." |
| `valid_logins.py` | Startup ID lists by role | Demo account input data | "AccessControl validates these IDs and builds its own lookup." |
| `starting_inventory.py` | Startup medicine records | Initial medicine choices, stock and per-record capacities | "InventoryManager copies this data; dispensing does not rewrite the file." |

**Information-hiding example to practise:** `controller` calls `inventory.getStock("001")`; it does not read `inventory._records`. Returned lists/dictionaries are independent snapshots. `User`, `AuthResult`, `HardwareOutcome` and `Timings` are frozen values. Explain that underscores and `__all__` express Python conventions/interfaces; they are not a security sandbox.

**Done when:** Deborah can locate each major module and say what it owns in one sentence, and the table no longer describes nonexistent implementation classes.

### D2 — Correct public interfaces and their meaning — P1 — Deborah; Marcus verifies behavior

**Where:** pages 9–13. Keep the existing responsibility/secret/operations/semantics format. Replace incorrect statements rather than rewriting every paragraph.

| Location | Existing problem | Exact correction |
|---|---|---|
| Page 9, UI | `getUserInput` is presented as though all live requests necessarily use it; `displayAler` is misspelled. | Correct `displayAlert`. Say `getUserInput` is a retained public helper, currently unused by the live GUI. Login and transfer callbacks use widgets; registration uses two `askstring` dialogs and a confirmation. |
| Pages 9–10, Access Control | `Authenticate(usedId, credential)` does not match the code. | Use `Authenticate(userId: str) -> AuthResult`; no password or role selector. Result fields are `success`, `user`, `reason`. A failed attempt invalidates the prior session. |
| Pages 9–10, permissions | The description is too vague about which user object is trusted. | `hasPermission(user, operation) -> bool` checks the current session object and role rule. A new or stale `User` object does not grant access. Controller also checks operating mode. |
| Page 10, controller | Registration and explicit maintenance operations are missing. | Add `registerMedication(medicationId: str, name: str) -> bool`, `setMode`, `repairHardware`, `closeDrawer` and `restartSoftware`. Keep the existing dispense/replenish/fix entries. |
| Page 10, `fix` | Described as initiating the appropriate fixing procedure. | Describe it as **checking recovery** after repair/restart/closure. It does not automatically repair hardware or resolve an injected software problem. |
| Page 10, effects | "LOGS?" is unresolved. | Replace with: "Records controller attempts and results, updates user feedback, and exports relevant audit information through CommunicationLink." |
| Page 10, failures | Communication failure appears to prevent local transfer completion. | Safe authorized local work can complete while HMS is unavailable. The outgoing data is retained for retry. A missing ACK does not undo confirmed movement. |
| Page 11, inventory quantities | "Quantities are non-negative" confuses stored stock with requested changes. | Stored stock may be zero. Dispense/replenish amounts must be **positive integers**; zero, negative, fractional and boolean amounts are rejected. |
| Page 11, registration | Inventory registration is omitted. | Add `validateRegistration(...) -> str` and `registerMedication(...) -> bool`. The first returns a reason or empty text; the second creates a zero-stock record. Controller handles authorization and hardware provisioning. |
| Page 11, lookup failure | Failure semantics are nonspecific. | Unknown `getStock`/`getName` lookup raises `ValueError`. Invalid stock-changing requests return `False` without changing inventory. Invalid startup data raises `ValueError`. |
| Page 11, mode | Transition constraints are not explicit. | Normal → Maintenance/Fault; Maintenance → Normal/Fault; Fault → Normal. Returning to permissive operation is guarded by safety. Requesting the existing mode is accepted; unknown or unsafe transitions fail. |
| Page 12, faults | "Fault is sufficient enough" and "Alert failures" are vague. | Name the supported faults and the actual recovery checks. `raiseAlarm` displays/records a notification; it is not Python exception raising. Clearing an alarm alone does not clear an active safety fault. |
| Page 12, logging | Only the two simplest method signatures are shown. | Retain them and document optional event metadata: outcome, medicine ID, signed quantity change and export flag; identity/time are added by the logger. Include snapshot/display methods used by the GUI. |
| Page 13, communication | "Remain in local ADC log" confuses the queue with audit storage. | Unacknowledged **data packets remain in CommunicationLink's pending queue**. Audit events separately remain in EventLogger. Both are memory-only. |
| Page 13, communication | `sendHeartbeat` is described as only alerting HMS that ADC is connected. | It starts a matching-response window and helps the ADC assess HMS availability. An invalid/missing response is not successful contact. |
| Missing module interface | HardwareInterface and its outcome contract are absent. | Add the hardware contract below, including tri-state closure and actual confirmed movement. |
| Missing external mock contract | The receiver's operations and reply schema are absent. | Add `SimulatedHMS.receive(message: dict) -> dict | None` and describe its test controls as mock behavior. |

**Hardware contract to add:**

- [ ] `perform(operation, medicationId, quantity) -> HardwareOutcome`; fields: `completed`, `medicationId`, `confirmedQuantity`, `description`.
- [ ] `isClosed() -> bool | None`: `True` means confirmed closed, `False` means open, `None` means the sensor cannot be trusted.
- [ ] `lock`, `unlock`, `repair`, `closeDrawer` return whether the action succeeded; a lock request is not closure evidence.
- [ ] `registerCompartment(medicationId) -> bool` provisions an empty simulated compartment when safe. Inventory capacity and role checks belong upstream.
- [ ] `discardCompartment(medicationId) -> None` rolls back a newly provisioned unused compartment after registration fails. This does not provide a GUI medicine-deletion feature.
- [ ] `getFaults` and `getStatus` return snapshots; `supportedFaults`, `injectFault`, `setNextOutcome` and `setHoldOpen` support simulation.

**Contract details to keep explicit throughout:**

- `None` return means no result value, not an operation failure. Boolean outcomes and exceptions must not be described interchangeably.
- Public snapshots are copies; they are not permission to mutate internal state.
- `getStatus` and AccessControl's lockout-related queries can expire a completed lockout. Do not describe every query as having absolutely no state effect.
- Public wiring callbacks `notifyAlarm`, `notifyModeChange` and `canRecover` connect modules; they are not alternative GUI permission bypasses.
- Existing names and input/result types should be copied from the source. The interface inventory at the end of this plan can be used as a checklist.

**Done when:** the methods the team points to during the demo exist with the stated arguments and return meanings, and the missing registration/hardware interfaces have a place in the document.

### D3 — Finish traceability without restarting the table — P1 for demo paths, P2 for all remaining rows — Deborah

**Where:** pages 14–16. Some authentication, I/O, fault and mode rows are already populated. Keep that work.

- [ ] Fix `login_fixture.py` in FR-AUT-03 to `valid_logins.py`.
- [ ] Use consistent class names: `AccessControl`, `ADCController`, `InventoryManager`, `ModeManager`, `FaultHandler`, `EventLogger`, `CommunicationLink`, `HardwareInterface`, `SimulatedHMS`. File names remain lowercase with underscores.
- [ ] For FR-INV-01, add controller registration and hardware provisioning alongside inventory storage; live registration now crosses those boundaries.
- [ ] Add method names to the key demo rows, rather than only naming a file. Example: FR-IO-03 → `ADCController.dispense/_transfer` → `HardwareInterface.perform` → `InventoryManager.removeStock` → `EventLogger.logEvent`.
- [ ] Make the demo's lockout, registration/replenishment, logging and outage paths traceable before the demo. The family mapping later in this plan gives the starting points.
- [ ] Fill the remaining Module and Code columns before final submission. A row with "N/A" under a separately written precise specification can still require module/code traceability.
- [ ] Do not copy a requirement sentence into the "Precise Specification" column and claim that it adds detail. Reference the relevant pre/postcondition table or add a short specific condition/result statement.
- [ ] Mark partial or unimplemented requirement coverage honestly, particularly the automatic software timeout and restart/power persistence claims.

**Done when:** a TA can choose a demonstrated requirement and Deborah can point to its implementation without searching randomly through files.

## 5. Emma: model, specifications and assumptions

### E1 — Make the four-variable diagram concrete — P0 to explain, P1 to edit — Emma

**Where:** page 3. The current M box includes session and operating mode; the C box lists authentication/dispensing/fault-handling logic. Those are mostly software state or responsibilities, rather than environmental quantities.

Choose a consistent boundary: **the ADC software**, with physical cabinet behavior represented by the simulator during this demo. Update the labels using a few simple examples:

| Part | Meaning | Suitable examples |
|---|---|---|
| **M: monitored variables** | Things in the environment the software needs to know | Credential presented by the user; requested medicine/amount; actual drawer position; actual medicine movement; HMS response behavior. |
| **I: software inputs** | Values the software receives about those things | Entered ID/request fields; closure reading `True/False/None`; `HardwareOutcome`; received reply packet. |
| **O: software outputs** | Values/commands the software sends | Compartment unlock/lock/transfer commands; GUI messages and alarm display requests; outgoing HMS packets. |
| **C: controlled variables** | Environmental effects the software is intended to influence | Which compartment is accessible; medicine movement resulting from the approved action; visible feedback/alarm indication. |
| **IN** | How environmental observations become input values | A sensor represents actual closure as a reading; the simulator supplies that reading in this implementation. |
| **OUT** | How output values/commands produce effects | A compartment command causes the simulated access/movement; a display request becomes visible feedback. |
| **NAT** | Assumptions/relations about the environment | Physical capacity is finite; a command can fail; a sensor may provide unknown information. |
| **REQ** | Required relationships between conditions and outcomes | Unauthorized requests must not provide medicine access; success requires exact confirmed movement; unconfirmed closure prevents another transfer. |

- [ ] Move "user session" and "operating mode" inside the software box or explain them as internal state.
- [ ] Replace software-process names in C with effects such as compartment access and actual movement.
- [ ] Keep inventory records distinct from physical stock. The software stores its recorded quantity; physical medicine quantity is the environmental concept.
- [ ] Explain one complete M → I → software → O → C example, such as drawer closure or dispensing.
- [ ] Add a short NAT/REQ example in prose if the diagram alone remains too compressed.

**Simple explanation:** "The drawer is physically open or closed. The software sees a sensor value. It uses that information to decide whether it may issue the next compartment command. In our demo, the hardware module simulates those observations and actions."

**Done when:** Emma can distinguish a real/simulated physical condition from the variable or message representing it in software.

### E2 — Correct the safety specification tables — P1 — Emma; Marcus checks against the running code

**Where:** pages 3–7. Keep the existing precondition/program/postcondition/invariant structure. Most changes are clarifications, not a complete rewrite.

| Requirement/table | What to change or confirm |
|---|---|
| FR-AUT-01/02 | State that authentication uses one ID in this simulation. Invalid authentication creates no session and replaces any prior session. Protected controller actions still reject unauthenticated callers. |
| FR-AUT-03 | Role comes from configured ID lookup. It is not randomly assigned and the user does not select a role. Add Tester as a demo role. |
| FR-AUT-04 | Require both role permission and the operation's current mode permission. GUI button visibility is presentation, not the only authorization check. |
| FR-INV-01 | Specify registration through the controller: Pharmacist/Tester, Normal mode, safe closed hardware, numeric-string unused ID, nonempty trimmed name and a free slot. Create zero stock and a simulated compartment. Registration is limited to ten types and is memory-only. |
| FR-IO-01 | Preserve the requested medicine/compartment check. A wrong medicine ID in hardware confirmation makes the result untrusted and leads to an inventory-uncertainty fault, not successful stock recording. |
| FR-IO-02 | Distinguish unknown medicine, invalid amount and insufficient stock. Rejected requests do not move medicine or change stock. Insufficient stock also generates an alarm notification. |
| FR-IO-03 | Keep exact completion as the success condition. Explicitly state that partial confirmed movement changes stock by that actual amount but returns `False` and is logged as incomplete. Zero confirmed movement changes no stock. |
| FR-FLT-02 | Name the supported simulated hardware reports: drawer jam, closure sensor, hardware interface and medication mismatch. A failed sensor is unknown closure, not confirmed closure. |
| FR-FLT-03 | Explain reported/injected software faults. Do not imply there is an automatic two-second software-component watchdog; that remains unimplemented. |
| FR-MOD-03 | Safety faults enter Fault mode and block medicine transfers and registration. Hardware/Software/Closure are fault categories, not three independent operating-mode classes. |
| FR-MOD-04 | Explain which operations remain available in Maintenance: permitted diagnostics, inventory/catalog viewing, logs/HMS traffic, closure and recovery-related actions. Ordinary dispensing, replenishment and registration are blocked. Do not describe Maintenance as making every button or every view unavailable. |
| FR-MOD-05 | Preserve the transfer block in Fault mode. A technician or Tester repairs/restarts/closes as needed and separately checks recovery before Normal is restored. A successful login alone does not clear Fault mode. |

**Short additional rules to cover for the demo:**

- [ ] Stock is between zero and the medicine's capacity. Transfer amount is a positive integer. Capacity for existing records comes from their own `capacity` field; newly registered medicines use `LOCATION_CAPACITY` (currently 50).
- [ ] Login lockout begins after three consecutive failures. Blocked attempts do not extend it. Successful login and completed lockout reset the failure count.
- [ ] Lockout is separate from cabinet Fault mode and expires without HMS being available.
- [ ] A successful transfer that leaves the drawer open starts closure monitoring; another transfer is denied immediately while closure is unconfirmed. The alarm is raised when the closure deadline expires.
- [ ] HMS loss alone does not put the cabinet in Fault mode. Communication availability and health are separate from operating mode.
- [ ] Registration requests are audited once submitted to the controller. Cancelling the GUI prompts/confirmation does not submit a registration attempt.

**Done when:** the team's stated invariants match a normal, denied and partial/fault example. Do not add new code merely to make an old sentence true.

### E3 — Replace the assumptions section — P1 — Emma

**Where:** page 16. The existing statement that users cannot see inventory is outdated.

Use the following factual content; it can be condensed into a short table or bullets in D2:

| Topic | Correct statement for this version |
|---|---|
| Inventory visibility | All authenticated roles can inspect inventory. Logged-out users see the login screen. |
| Authentication | IDs act as simulated credentials. No password or physical badge integration is implemented. Roles are looked up locally. |
| Role separation | Nurse dispenses; Pharmacist registers/replenishes and views medication history; Technician performs maintenance/recovery and sees full logs/HMS traffic; Tester has all role actions and simulation controls. |
| Tester limits | Tester does not bypass stock limits, unsafe hardware, operating-mode restrictions or lockout. |
| Cabinet size | Ten possible medicine types. The current demo starts with nine, leaving one slot for registration. Zero stock still occupies a slot. |
| New registration | New medicines start at zero; replenishment is separate. There is no live deletion/replacement workflow. |
| Timing | Accelerated demo timers are enabled. D1 timing values are still available through configuration; use the timing table in this plan. |
| Hardware and HMS | Both are simulated in process. This demonstrates module/protocol behavior, not physical or partner-system integration. |
| Audit | Events record time, actor where appropriate, outcome and medicine/quantity metadata. Autonomous polling events use System identity. |
| Outages | Stock, logs and pending data survive temporary communication loss while the application process remains running. |
| Restart | Exiting/restarting reloads startup data and clears live state. The maintenance "Restart software" button simulates recovery; it is not a restart/persistence test. |
| Session end | Explicit sign-out ends the session. No inactivity expiry or user-presence detection is implemented. |
| Software faults | Reported/injected faults are handled. Automatically detecting an unresponsive software component is not implemented. |
| Inventory uncertainty | There is no reconciliation workflow; this fault cannot simply be cleared by the normal repair/recovery controls. |
| User information | Demo IDs and medication records are used; patient medical records are not managed by this application. Do not claim production credential protection based on this simulation. |

**Done when:** nobody reads an old assumption aloud that contradicts the screen, and the team can briefly state the simulation/reset limitations without a long disclaimer.

### E4 — Introduction and context — P2, explicitly deferrable for tomorrow — Emma

**Where:** page 3, blank Introduction, plus the corresponding checklist items on pages 1–2.

The written introduction does **not** need to be the first task tonight. Prepare this short verbal version:

> "This is our simulated medication cabinet. We are demonstrating the simplified version, which keeps the module boundaries and adds live medicine registration. We will show authorized operations, fault recovery and behavior when HMS is unavailable."

For final submission, write one or two paragraphs covering purpose, scope, the relationship to D1, the simplified implementation and the intentional changes. Mention ID-only login, Tester, demo timing, live registration and the current simulation limits. Refer to relevant requirement IDs instead of describing the change as a totally unrelated new system.

**Done before submission when:** a reader can understand which version the document describes and what changed since D1.

### E5 — Older diagrams and requirement alignment — P1 verbal differences, P2 written reconciliation — Emma; Deborah updates links

- [ ] Explain that the D1 diagram's technician-login-to-Maintenance path is not automatic in the application: login establishes the role; starting planned maintenance is a separate action.
- [ ] Explain that login lockout is not the same state as cabinet Fault mode.
- [ ] Describe dispensing and replenishment as workflows while the cabinet's operating mode is managed separately.
- [ ] Include the registration path in any activity diagram used to explain the new functionality.
- [ ] Distinguish intended requirements, implemented behavior and outstanding acceptance criteria. In particular, AC-FLT-03-02's automatic component timeout is not demonstrated by pressing the software-fault injection button.
- [ ] Keep power/restart recovery claims separate from network-outage retention. The latter works in memory; persistence across restart does not exist.
- [ ] If an older assumption says eight medicines, align it with the actual ten-slot limit and nine starting medicines.

For tomorrow, knowing and explaining these differences is more useful than redrawing every historical diagram. Complete the consistent document/traceability references before submission.

## 6. Marcus: running version, communication and verification

### M1 — Prepare one reproducible demo version — P0 — Marcus

- [ ] Share the exact `ADC_simplified/` directory the group will use. Do not mix files from `ADC/` and `ADC_simplified/` in one Python process or copy only the changed controller without its supporting modules.
- [ ] On the demonstration machine, launch from the repository root:

```powershell
python ADC_simplified/gui.py
```

- [ ] Confirm that Python has Tkinter and the GUI opens. No third-party application dependencies or separate HMS process are required.
- [ ] Confirm the nine starting medicines are visible after login, and `MAX_MEDICATION_TYPES` remains 10.
- [ ] Keep a fresh-start procedure: close the application and run it again. This resets demo stock, registrations, faults, mock settings, logs and queued messages.
- [ ] Have the four role IDs available: Nurse `12345`, Pharmacist `23456`, Technician `34567`, Tester `99999`.
- [ ] Keep the source editor open at `adc_controller.py`, with quick access to inventory, hardware, fault and communication modules.
- [ ] Open the updated D2 document and the simplified README before the demo. Have the GUI already running when the TA arrives.
- [ ] Rehearse the current code, not just a screen recording or a remembered result from an earlier version.

**Done when:** another group member can launch the same version and perform the opening scenario without Marcus fixing their setup.

### M2/M3 — Practise normal operations and recovery — P0 — Marcus leads; Deborah and Emma repeat

Use the exact rehearsal sequence in section 8. Ensure the team knows the following distinctions:

- Registration creates a zero-stock record and an empty simulated compartment; it does not add physical units. Add stock is a separate confirmed transfer.
- The newly registered row is selected automatically. Verify its ID/name before replenishing.
- A successful transfer needs both completion and the exact confirmed amount. Partial movement is neither a zero-stock-change failure nor a successful full transaction.
- Changing to Fault mode happens through detected safety faults. The user cannot arbitrarily request Fault mode through the ordinary mode command.
- In Fault mode, use the available maintenance actions directly. Do not assume you must first change Fault to Maintenance; that transition is not allowed.
- `repairHardware` repairs reported simulated hardware faults. `restartSoftware` resolves the simulated software condition. `closeDrawer` attempts closure/locking. `fix` then checks recovery.
- A visible maintenance button does not mean every action is currently allowed. The controller checks permissions and mode again.
- The GUI uses `after` polling; all work is in the Tk event loop. Do not describe it as a separate real-time watchdog process.

**Done when:** both a denied request and a failed recovery attempt produce the expected explanation, and the group knows the action that actually resolves the condition.

### M4/M5 — Explain HMS and complete page 13 — P0 to demonstrate/explain, P1 to write the tables — Marcus; Deborah aligns interface names

**What to replace:** the incomplete Event log/Heartbeat table and the blank degraded-behavior rows. Include all actual message families rather than implying only logs and heartbeats are sent.

#### Message table to use

| Direction/type | Contents and meaning | When sent | Reply/delivery rule |
|---|---|---|---|
| ADC → HMS: `mode` | Current operating mode | Startup and confirmed mode changes | Data `ack` must match packet ID. |
| ADC → HMS: `inventory` | After transfers: medicine ID and current quantity. At registration: ID, name, zero quantity and capacity. | Confirmed recorded stock changes or successful registration | Same matching data ACK rule; offline packets remain queued. |
| ADC → HMS: `alarm` | Alarm ID and description | Alarm notification, including lockout/insufficient stock/safety fault reporting | Same matching data ACK rule. Alarm-clear events are recorded in audit; do not invent a separate implemented alarm-clear packet type. |
| ADC → HMS: `maintenance` | Previous and current mode | Entry to or exit from Maintenance | Same matching data ACK rule. Individual repair actions also appear in audit. |
| ADC → HMS: `health` | `Normal` or `Degraded` summary | Summary changes; a Tester probe can also send a health packet | Same matching data ACK rule. Degraded health is not a fourth operating mode. |
| ADC → HMS: `log` | A JSON string containing a batch of exportable audit records | Controller exports new application events | Same matching data ACK rule. CommunicationLink owns retries once the batch is handed over. |
| ADC → HMS: `heartbeat` | Empty payload with a unique packet ID | At monitoring startup and periodically | Matching `heartbeat_ack` within the live response window; heartbeat probes are not retained like data messages. |
| HMS → ADC: `ack` | `messageId` of the data packet | In response to received data in the simulator | Accept only a dictionary with the correct reply type and exact message ID. |
| HMS → ADC: `heartbeat_ack` | `messageId` of the heartbeat packet | In response to a heartbeat unless a simulated failure suppresses it | Valid current response clears consecutive misses and marks Available. |

**Concrete packet example:**

```json
{"id": "session-prefix-12", "type": "inventory", "payload": {"medicationId": "001", "quantity": 15}}
```

**Matching reply:**

```json
{"type": "ack", "messageId": "session-prefix-12"}
```

The example ID is illustrative. Actual IDs use a random session prefix and increasing sequence number. Retrying a packet preserves its original ID. The application treats delivery as confirmed only after a matching reply; the mock receiver can record repeated receipts if a previous ACK was lost. Do not claim exactly-once delivery or deduplication by a real partner.

#### Timing table to use

| Setting | Current demo profile | D1 profile | Owner of behavior |
|---|---:|---:|---|
| Failed-login threshold | 3 attempts | 3 attempts | AccessControl |
| Login lockout duration | 10 s | 60 s | AccessControl |
| Closure deadline after successful transfer | 10 s | 30 s | FaultHandler |
| Heartbeat interval | 5 s | 60 s | CommunicationLink |
| Heartbeat response window | 1 s | 3 s | CommunicationLink |
| Consecutive expired probes before Unavailable | 3 | 3 | CommunicationLink |
| Scheduled data retry since last attempt | 10 s | 60 s | CommunicationLink |
| GUI polling interval | 100 ms | 100 ms | GUI/configuration |

`DEMO_MODE = True` selects the current profile. Changing the setting requires restarting. A retry can occur sooner than its scheduled interval when new information triggers retrying all pending data, or when heartbeat recovery from Unavailable flushes pending data. Do not describe the configured retry interval as a minimum delay that always applies.

#### Degraded-behavior table to use

| Condition | What actually happens | What to show/explain |
|---|---|---|
| Cable/mock connection disconnected | Sends get no reply. Data is retained. Availability changes only according to heartbeat monitoring. | "Disconnected" mock setting and "Unavailable" monitored status are different facts. |
| One or two heartbeat deadlines missed | Miss count increases; an already Available link does not become Unavailable yet. | Missing one reply does not instantly declare the partner unavailable. |
| Three consecutive heartbeat deadlines missed | Availability becomes Unavailable; overall health becomes Degraded. | Cabinet can remain in Normal mode. |
| Safe user transaction during outage | Valid local movement and inventory update continue; events and outbound data are kept in memory. | Stock/logs change even though pending-message count grows. |
| Wrong ACK type or wrong ID | Reply is rejected and data remains pending. | Inspect the actual packet and reply in HMS messages. |
| Message dropped before receiver | Attempt is recorded locally but the mock receiver does not record a receipt. | A send attempt is not proof the partner received it. |
| ACK dropped after receipt | Receiver history contains the packet, but ADC cannot confirm delivery and retains it. | The same message ID can be retransmitted. |
| Connection restored | Subsequent valid communication/retries deliver retained data. A valid heartbeat restores Available and clears misses; transition from Unavailable immediately retries pending data. | Do not promise that clicking Restore instantly updates every indicator before the next poll/probe. |
| Partner never successfully seen | Availability starts Unknown, then follows the heartbeat outcome/miss rules. Safe local authorization still works. | Do not claim the controller refuses to start until HMS connects. |

**Audit detail:** transport/heartbeat diagnostics are logged locally with `export=False`, avoiding an endless log → ACK → new exported log cycle. Application events are still exported. Controller timer work uses System identity rather than falsely assigning background events to the signed-in user.

**Done when:** Marcus can show a matching reply and a retained packet, and explain why an offline dispense can succeed without claiming its HMS delivery already succeeded.

### M6 — Align the nine-medicine setup with verification and supporting text — P1 — Marcus

**This is a newly relevant preparation task, not a request to change the cabinet back to ten occupied slots.** The current file already gives the registration demo room to work.

Observed mismatches to resolve:

| File/test area | Current stale assumption | How to update without losing coverage |
|---|---|---|
| `ADC_simplified/README.md` | Says the current startup uses all ten slots and the startup fixtures are byte-identical to the original. | State nine starting medicines, ten-slot limit, one free registration slot, and the intentional demo-fixture difference. Keep reset/non-persistence notes. |
| `tests/test_gui.py` in the simplified folder | Expects ten inventory rows. | Check the configured startup count and actual records; preserve the row-content/privacy checks. |
| `tests/test_adc.py` in the simplified folder | Startup/catalog tests expect ten and refer to medicine `010`, which is no longer in the current simplified fixture. | Use a deliberately supplied full fixture where testing ten-slot behavior; for startup-copy tests select an actual startup medicine and compare its original quantity after mutation. Retain tests of the ten-slot maximum separately. |
| `tests/test_registration.py` | `STARTING_INVENTORY[:-1]` used to mean nine records; it now means eight. Several expectations assume nine and that one addition fills the cabinet. | Make the free-slot fixture explicitly contain `MAX_MEDICATION_TYPES - 1` records; separately test the actual nine-record startup. Build a full ten-record fixture for full-cabinet rejection. |
| `test_current_default_cabinet_reports_full` | The current default is no longer full. | Rename/rewrite around an explicit full fixture, and add/retain successful registration with the actual demo setup. |
| `test_settings_are_byte_identical` | Includes the changed startup inventory file. | Keep byte comparisons for unchanged settings/login data; assert the deliberate startup difference precisely instead of deleting configuration checks. |
| Original-versus-simplified scenario comparisons | The versions now start with different inventories. | Compare the implementations with the same explicit input fixture, or isolate and assert the deliberate startup difference. Do not discard all inventory/log/packet comparisons to hide the mismatch. |
| Test-copy fidelity assertion | Requires the three copied tests to differ only in import paths. | If copied tests are adapted for the new fixture, document those exact adaptations and preserve their behavioral assertions. Leave repository-root original tests untouched. |
| `verification/results.md` and any "97 tests pass" wording | Results describe a prior configuration. | Label historical results clearly and record fresh results for the final demo fixture. Do not claim a new passing result before running it. |

Useful verification commands from the repository root:

```powershell
python -B -m unittest discover -s ADC_simplified/tests -v
python -B ADC_simplified/verification/launch_check.py
python -B ADC_simplified/verification/check_originals.py
```

The standalone launch check is Windows-specific. In this workspace, the existing interpreter can also be invoked as `tests/.venv/Scripts/python.exe`. Tk GUI tests need an available display.

- [ ] Keep authorization, safety, partial movement, queue retention and snapshot-copy assertions intact.
- [ ] Keep the original `ADC/` and root `tests/` unchanged; only adapt simplified verification where the new setup requires it.
- [ ] Check any original-file integrity warning against deliberate document work. The historical manifest also includes existing reports/documents; a later authorized edit to one of those is different from accidentally changing the original application.
- [ ] After the final fixture is chosen, manually rehearse the actual launch and registration path. A historical test count is not a substitute for running the current setup.

**Done when:** the README, chosen startup fixture and latest test results describe the same version. This planning pass inspected these assumptions but did not run or modify the tests.

### M7 — Written implementation notes — P2, explicitly deferrable for tomorrow — Marcus

**Where:** blank section on page 14.

You do not need to spend tonight writing a long implementation report. You do need to point to the code and explain the workflow. Use this verbal summary:

> "The GUI sends requests to ADCController. AccessControl and ModeManager decide whether the action is allowed. InventoryManager validates the requested change. HardwareInterface returns the confirmed movement. The controller records that amount, logs the result and sends updates through CommunicationLink. FaultHandler blocks unsafe operations and checks recovery."

For final submission, a compact section should cover:

- [ ] The real files/classes and how public calls connect them.
- [ ] Why dispense/replenish share `_transfer` and why checks occur before movement.
- [ ] Registration validation, compartment provisioning, zero-stock creation and rollback on record failure.
- [ ] Explicit repair/restart/closure followed by guarded recovery.
- [ ] Tk polling, injected clocks for tests, System audit attribution and timer-profile selection.
- [ ] In-memory storage and simulated external components.
- [ ] How the implemented states/workflows correspond to, and intentionally differ from, the older diagrams.
- [ ] Readability changes: simpler login branches, adjacent transfer workflow, explicit simulation calls, one fault-category table and heartbeat ID/deadline state.
- [ ] Registration is a functional addition after the refactor, so do not describe the entire current version as behavior-identical to the original.

**Done before submission when:** the section helps a reader find the implementation; it does not need to repeat every method body.

## 7. Page-by-page change tracker

Use this for editing the PDF's source document. Page references are to the **16-page `Deliverabel_2_3K04 (1).pdf`**, not the earlier 15-page draft. Pagination may change after editing.

| PDF page(s) | Priority and owner | Required change | Can the written work wait until after the demo? |
|---|---|---|---|
| 1–2 | **P2 — Deborah**, each owner confirms status | Update checklist marks after work is actually completed. Keep assignments consistent. Do not treat the existing tick on the four-variable model as proof that its labels are correct. | Yes, except misleading status you intend to show prominently. |
| 3, Introduction | **P2 — Emma** | Add context and implementation changes before submission. | **Yes.** Prepare only a short verbal introduction tonight if time is limited. |
| 3, four-variable diagram | **P0 understanding / P1 edit — Emma** | Replace internal-state/process labels in M/C; explain inputs/outputs, IN/OUT and one NAT/REQ relationship. | Know the correction before the demo; a simple corrected figure or note is preferable to postponing all correction. |
| 3–4, authentication | **P1 — Emma** | ID-only login, fixed role lookup, failed-session invalidation and controller role/mode checks. | Correct the explanations used during the demo tonight. |
| 4, registration specification | **P1 — Emma**, Deborah cross-references | Add the current authorized zero-stock registration behavior and capacity/duplicate validation. | Important if registration will be demonstrated. |
| 5–6, medication I/O | **P1 — Emma** | Positive amounts, confirmed movement, exact success, partial stock changes and invalid outcome handling. | Important before demonstrating transfer failures. |
| 6, fault detection | **P1 — Emma** | Supported hardware reports; reported/injected software fault versus unimplemented automatic watchdog. | Explain accurately before the demo; detailed acceptance-gap prose can follow. |
| 6–7, modes | **P1 — Emma** | Real mode restrictions, allowed diagnostic views and repair-versus-recovery distinction. | Important before the fault demo. |
| 8, module hierarchy | **P0 understanding / P1 edit — Deborah** | Actual modules, meaningful hidden decisions, hardware boundary and external HMS mock. Remove misleading separate role/workflow/mode classes. | Core table should be corrected before showing code. |
| 9, GUI/access interfaces | **P1 — Deborah** | Correct `Authenticate`, `displayAlert`, current GUI request path and retained unused helper explanation. | Correct the signatures being demonstrated tonight. |
| 10, controller | **P1 — Deborah**, Marcus verifies | Registration and maintenance methods; `fix` semantics; logging effects; offline behavior. Remove "LOGS?". | Core behavior should be correct before the demo. |
| 11, inventory/mode | **P1 — Deborah** | Positive transfer quantities, registration methods, copied records and actual transitions. | Core behavior should be correct before the demo. |
| 12, faults/logger | **P1 — Deborah** | Concrete fault/notification semantics; audit metadata, export and views. | Core explanation tonight; exhaustive interface formatting can follow. |
| 13, communication/external interface | **P0 explanation / P1 table — Marcus**, Deborah verifies names | Complete packets/replies/timings/outage behavior and distinguish audit from pending queue. | At least a small accurate table or note before the outage demo. |
| New placement near interfaces | **P1 — Deborah** | Add HardwareInterface and the simulated partner contract. | Yes for polish, no for understanding the missing boundary. |
| 14, implementation notes | **P2 — Marcus** | Add concise design-to-code explanation before submission. | **Yes.** The spoken code walkthrough still needs rehearsal. |
| 14–16, traceability | **P1 demo rows / P2 remainder — Deborah** | Correct filenames, add current registration path and methods, complete remaining mappings. | Complete demonstrated paths tonight; remaining rows before submission. |
| 16, assumptions | **P1 — Emma** | Replace the false inventory-visibility statement; add actual roles, simulation, timing, capacity and reset behavior. | Core factual corrections should be made tonight. |
| Whole document | **P2/P3 — Deborah and Emma** | Consistent capitalization, spelling, table layout, numbering and terminology. | Yes, unless a typo changes an interface name or meaning. |

## 8. Rehearsal script and expected results

**Priority: P0 for normal operations plus one off-normal path; P1 for the additional alternatives. Owner: Marcus leads; Deborah and Emma each repeat the core steps.**

This is a rehearsal menu, not a requirement to run every scenario unprompted during the TA's demonstration. Be ready to switch to the behavior the TA requests.

### R1 — Login, normal dispense and rejection — P0 — Marcus; everyone explains

1. Start a fresh application so medicine `001` has 20 units.
2. Sign in as Nurse `12345`. Point out inventory visibility and the role-appropriate controls.
3. Select medicine `001`, enter 5, press Dispense medicine and confirm.
4. Verify stock is **15**, with confirmation feedback.
5. Request 16. Verify rejection for insufficient stock and stock remains **15**.
6. Explain that controller authorization/mode/stock/safety checks occur before requesting hardware movement. The hardware result determines the actual change.
7. Sign out. Confirm inventory is no longer visible on the login screen.

**Code to point at:** `gui.py` transfer callback; `ADCController.dispense/_transfer`; `InventoryManager.validateChange`; `HardwareInterface.perform`; `EventLogger.logEvent`.

### R2 — Registration and replenishment — P0 for the chosen registration demo — Marcus; Deborah explains the interfaces

1. Continue from R1 or start fresh; either way there should be nine registered medicine types before this scenario.
2. Sign in as Pharmacist `23456`.
3. Press Register medicine; use ID `011` and a clear demo name such as `Demo medicine`; confirm.
4. Verify the new row appears, is selected, and has **zero stock** with capacity **50**.
5. Add 5 units to that medicine and confirm; verify stock becomes **5**.
6. Try registering ID `011` again; expect duplicate-ID rejection without another record.
7. Try a different new ID `012`; expect a full-cabinet rejection because all ten slots are now occupied.
8. Sign in as Nurse `12345` and dispense 2 from `011`; verify **3** remain.
9. Explain that no file was rewritten; restarting will remove this live registration and reload the startup list.

**Optional validation examples:** empty name, nonnumeric ID, cancelling either prompt, cancelling confirmation, or replenishing above capacity. Cancelling is not an application transaction.

**Code to point at:** `ADCController.registerMedication`; `InventoryManager.validateRegistration/registerMedication`; `HardwareInterface.registerCompartment/discardCompartment`.

### R3 — Fault, denied transfer and technician recovery — P0 — Marcus; Emma explains the safety condition

1. Sign in as Tester `99999`; open Test controls.
2. Cause a Jammed drawer problem.
3. Show Fault mode and the alarm. Try a transfer and show it is blocked.
4. Sign out and sign in as Technician `34567`. Tester-only controls should not be available.
5. Open Maintenance. Try Check recovery before repairing; expect failure.
6. Press Repair reported hardware, then Close and lock drawer, then Check recovery / finish maintenance.
7. Verify Normal mode and cleared resolved fault alarms.
8. Explain that hardware repair does not itself remove the registered fault or automatically restore Normal mode.

**Code to point at:** `FaultHandler.handleFault/poll/clearFault/isSafe`; `ModeManager.setMode`; controller maintenance methods.

### R4 — HMS outage and reconnection — P0 to prepare as an off-normal alternative — Marcus; everyone understands

1. Start fresh or recover to Normal. Sign in as Tester and open HMS messages and Split log.
2. In Test controls, press Disconnect HMS.
3. Perform a safe dispense, for example 2 units of medicine `001`. Stock should decrease even though outgoing messages receive no reply.
4. Show pending messages and audit history. Explain that the physical/local result and communication delivery are separate.
5. If showing monitored unavailability, wait for three expired heartbeat response windows. With demo timing, this is roughly **11–16 seconds** depending on when disconnection occurs relative to the next heartbeat, plus normal polling delay.
6. Point out that the mode may still be Normal while communication is Unavailable and health is Degraded.
7. Restore HMS. Allow subsequent polling/heartbeat/retry activity to occur.
8. Verify queued data is acknowledged and the pending queue drains; stock and previous audit records are retained.
9. Select a packet/reply and show matching `id` and `messageId`. Retries of an existing packet use the same ID.

**Reset note:** use the Maintenance controls to resolve cabinet faults; Restore HMS fixes mock communication settings only.

### R5 — Login lockout — P1 alternative — Marcus; Emma explains the rule

1. Sign out and enter an invalid ID such as `00000` three times.
2. Show the security alarm and rejection of even a valid ID during lockout.
3. Wait 10 seconds in the demo profile. Show that the lockout ends and a valid login works.
4. Explain that blocked attempts do not extend the deadline, and lockout does not require HMS connectivity to expire.
5. Do not describe this as cabinet Fault mode or technician repair.

### R6 — Partial movement — P1 alternative — Marcus; Deborah explains return semantics

1. Start fresh or use a known stock value. Sign in as Tester.
2. In Test controls, set the next operation to Stop after moving some stock.
3. Request 5 units of medicine `001`, initially 20.
4. The simulator confirms **4**, so stock becomes **16**. The operation is incomplete and returns failure; a hardware fault is reported.
5. Show the signed quantity change and incomplete outcome in the audit.
6. Repair the reported hardware, close the drawer if needed, and check recovery.

**Key sentence:** "False means the whole requested operation did not complete; it does not necessarily mean zero medicine moved."

### R7 — Open drawer and software fault — P1 alternatives — Marcus; Emma explains recovery

**Open drawer:** enable Leave drawer open after use, complete a transfer, and show that another transfer is blocked while the drawer is open. After the 10-second demo closure deadline, show the closure fault. Close and lock the drawer, then check recovery. Turn off the hold-open test setting before the next normal transfer.

**Software fault:** inject Software self-check failed. Show that Check recovery alone fails. Use Restart software in Maintenance, then Check recovery. State that the button simulates a successful service restart/self-check; it does not prove automatic detection of an unresponsive component or persistence across a real restart.

### A1 — Everyone's short explanation practice — P0 — Marcus, Deborah and Emma

Take turns answering these without the person assigned to that document section helping immediately:

| TA question | Plain answer to practise |
|---|---|
| What does the controller do? | "It checks and coordinates the request. Each specialist module still owns its own data and rules." |
| Why is this modular? | "Stock representation, login rules, hardware simulation, fault policy, communication and UI can change behind their interfaces." |
| Why are role checks in the controller if the GUI hides buttons? | "A caller could invoke a controller method directly; the protected operation must enforce authorization itself." |
| When does stock change? | "After hardware reports a trusted confirmed amount. We record partial movement accurately but do not call the whole operation successful." |
| What is the difference between repairing and recovering? | "Repair resolves the cause. Recovery verifies the condition is safe and allows Normal mode again." |
| What happens if HMS disappears? | "Allowed safe local work continues. We retain outgoing data and retry until the matching acknowledgement arrives." |
| How does registration work? | "It checks permission, mode, ID/name and free capacity, provisions a simulated compartment and creates a zero-stock record. Replenishment adds units afterward." |
| Does registration survive restart? | "No. This demo keeps state in memory and reloads the startup file on a fresh run." |
| What is monitored versus input? | "The physical drawer position is monitored; the software receives a sensor value representing it." |
| Where would you change a timeout? | "The timing profiles in config.py. Then update the stated timing and retest just before and at the deadline." |
| Where would you change role permissions? | "AccessControl's permission table, then verify the controller decisions and GUI visibility for each role." |
| How would you change medicine capacity? | "Existing medicines have capacities in starting_inventory.py. New registrations use LOCATION_CAPACITY. Those are different settings, and both need boundary tests if changed." |

Practise pointing to the relevant source while answering. The aim is a short accurate explanation, not memorizing method bodies or speaking in formal terminology.

## 9. Traceability completion guide

**Priority: P1 for requirements used in the demo, P2 for the remaining final-document rows. Owner: Deborah; Emma confirms specification/acceptance meaning; Marcus confirms code references.**

The table below covers the requirement groups in the current D2 traceability table. Expand grouped ranges into the existing individual rows. Keep the formal wording tied to D1; this table supplies implementation guidance, not permission to silently redefine a requirement.

| Requirement(s) | Main implementation to map | Detail to include in the row or linked explanation |
|---|---|---|
| FR-AUT-01, 02 | `AccessControl.Authenticate`; controller `login` and protected-operation checks | Authentication required; failure denies access and leaves no active session. |
| FR-AUT-03 | `valid_logins.py`; `AccessControl.Authenticate`, `User` | Configured ID → role; replace the nonexistent `login_fixture.py` reference. |
| FR-AUT-04 | `AccessControl.hasPermission`; `ADCController._rejection/_authorized`; `ModeManager.isOperationAllowed` | Role and mode checks are distinct. Include registration permissions. |
| FR-AUT-05, 06 | `AccessControl.Authenticate`; `FAILED_LOGIN_LIMIT` | Third consecutive failure activates lockout; all attempts blocked during it. |
| FR-AUT-07 | `AccessControl.Authenticate` | Successful login resets the consecutive failure count. |
| FR-AUT-08 | `AccessControl.Authenticate` → `ADCController.notifyAlarm` → `FaultHandler.raiseAlarm` and `CommunicationLink.sendMessage` | Lockout alarm is recorded and reported even while communication is lost. |
| FR-AUT-09, 10 | `AccessControl.tick/lockoutRemaining`; `ADCController._refreshLockout`; configured timings | Expiry clears lockout/failure count and updates stale login feedback. State the active profile. |
| FR-INV-01 | `ADCController.registerMedication`; `InventoryManager.validateRegistration/registerMedication`; `HardwareInterface.registerCompartment/discardCompartment` | Unique ID, authorization, available slot, provisioning and rollback. Startup loading also validates IDs. |
| FR-INV-02 | `starting_inventory.py`; inventory constructor, `registerMedication/getName` | Names stored at startup and on live registration; empty names rejected. |
| FR-INV-03 | `InventoryManager.getStock/getRecords`; `ADCController.getInventory`; GUI inventory table | Stored current quantities and authorized visible snapshots. |
| FR-INV-04 | Controller `_transfer`; `InventoryManager.removeStock`; `HardwareInterface.perform` | Subtract actual confirmed movement, including an incomplete partial transfer. |
| FR-INV-05 | Controller `_transfer`; `InventoryManager.addStock`; `HardwareInterface.perform` | Add actual confirmed movement within capacity. |
| FR-IO-01 | Controller `_transfer`; hardware `unlock/perform`; inventory validation | Only the requested known compartment/medicine; reject untrusted outcome identity. |
| FR-IO-02 | `InventoryManager.validateChange`; controller `_transfer/notifyAlarm` | Insufficient stock rejects before movement and leaves stock unchanged. |
| FR-IO-03 | `HardwareOutcome`; controller `_transfer`; EventLogger | Exact confirmed completed quantity required for success; partial amount is recorded as incomplete. |
| FR-IO-04 | `AccessControl.hasPermission`; controller `replenish/_transfer` | Replenishment authorization; Nurse and Technician are not replenishment roles. |
| FR-IO-05 | `InventoryManager.validateChange/addStock`; per-record capacity | Reject exceeding capacity; exact capacity is allowed. Normalize any `FR-IO-5` spelling to the chosen ID consistently. |
| FR-LOG-01, 02 | Controller `_finish/_transfer`; `EventLogger.logEvent` | Audit successful, rejected and incomplete dispensing/replenishment attempts. |
| FR-LOG-03 | `AccessControl.Authenticate`; EventLogger | Authentication attempts without storing arbitrary invalid submitted text. |
| FR-LOG-04 | `FaultHandler.handleFault`; EventLogger | Record a newly registered fault once per occurrence, not every poll. |
| FR-LOG-05 | `ModeManager.setMode`; EventLogger | Actual confirmed mode transitions are logged. |
| FR-LOG-06 | `EventLogger.timestamp/logEvent/readableTime` | Stored timestamp retains timezone information; display is local readable time; clock failure uses an explicit unavailable value. |
| FR-LOG-07, 08 | Controller `_finish/_transfer`; EventLogger | Result/outcome retained for successful, denied and incomplete transfers. |
| FR-LOG-09 | `AccessControl.Authenticate`; EventLogger | Authentication result recorded as success/denied. |
| FR-LOG-10 | `EventLogger.setUser/logEvent`; AccessControl login/logout; controller `tick` | User attribution for user actions; System context for autonomous polling. |
| FR-LOG-11 | Controller `_transfer`; EventLogger `quantityChange` | Signed actual stock change; registration creates zero stock, not a fictitious replenishment. |
| FR-LOG-12 | `AccessControl.Authenticate/tick`; EventLogger | Lockout activation and expiry events. |
| FR-FLT-01 | `FaultHandler.operationCompleted/poll`; `HardwareInterface.isClosed` | Closure timer starts after successful completion; unknown closure is not safe. |
| FR-FLT-02 | Hardware `getFaults`; fault handler `poll/handleFault` | Supported reported hardware conditions detected and registered. |
| FR-FLT-03 | Fault handler `handleFault/restartSoftware`; controller `simulate` | Reported/injected software faults handled. Separately mark automatic component-timeout acceptance coverage incomplete. |
| FR-MOD-01, 02 | `ModeManager`; controller `setMode` | Normal/planned Maintenance supported with role and safety guards. Technician login alone does not change mode. |
| FR-MOD-03 | Fault handler `handleFault`; mode manager `setMode`; controller | Detected safety faults enter Fault and restrict operations. |
| FR-MOD-04 | `ModeManager.isOperationAllowed`; controller `_rejection` | Maintenance operation restrictions; permitted views and maintenance actions remain. |
| FR-MOD-05 | Controller `_transfer`; mode restrictions; guarded recovery | No dispensing in Fault; role privilege alone cannot override it. |
| FR-COM-01 | `ADCController.notifyModeChange`; CommunicationLink | Startup/current mode reporting and confirmed mode changes. |
| FR-COM-02 | Controller `_transfer/registerMedication`; CommunicationLink | Current inventory quantity updates; registration also sends identifying metadata. |
| FR-COM-03 | Controller `notifyAlarm`; FaultHandler; CommunicationLink | Alarm packets retained if not acknowledged. |
| FR-COM-04 | Controller `notifyModeChange`; CommunicationLink | Maintenance entry/exit, including transition to Fault from Maintenance. |
| FR-COM-05 | Controller `_updateHealth`; faults and communication status | Health summary changes; independent from cabinet mode. |
| FR-COM-06, 07 | CommunicationLink `_matches/_attempt`, `getPending` | Matching type/ID required; unacknowledged data retained. |
| FR-COM-08 | `CommunicationLink.sendMessage` | New information triggers attempts for all pending data. |
| FR-COM-09 | `CommunicationLink.tick`; `_attempt`; timing configuration | Scheduled retries relative to most recent attempt, with same packet ID. |
| FR-COM-10 | `CommunicationLink.sendHeartbeat/tick` | Periodic heartbeat scheduling and response window. |
| FR-COM-11 | `CommunicationLink.receiveHeartbeatResponse` | Valid corresponding live reply marks Available and resets misses. |
| FR-COM-12 | CommunicationLink `_expireHeartbeat/_setStatus` | Three consecutive expired response windows mark Unavailable. |
| NFR-SAF-01 | Controller checks; inventory validation; hardware; FaultHandler; ModeManager | No unsafe transfer; unknown sensing and unresolved faults block operation. |
| NFR-SEC-01 | AccessControl; controller authorized views; GUI logout behavior | Simulated access restrictions and no echoing arbitrary invalid credentials in audit. Do not claim production credential storage/security. |
| NFR-REL-01 | InventoryManager local storage; controller transfer workflow | Inventory survives temporary network loss in the running process, not process restart. |
| NFR-REL-02 | EventLogger; CommunicationLink queue | Local audit and unsent data survive temporary network loss in memory. |
| NFR-AVL-01 | Local controller operations; communication separation | Safe permitted local operations continue while HMS is unavailable. |
| NFR-PERF-01 | AccessControl/controller/GUI; timing measurements in tests | Authentication responsiveness evidence; do not turn a short measured test into a hard real-time guarantee. |
| NFR-PERF-02 | FaultHandler/controller/GUI polling; timing measurements | Prompt response to detected faults; not proof of the unimplemented automatic watchdog. |
| NFR-AUD-01 | EventLogger timestamp and formatting methods | Time attached to events and preserved in snapshots. |
| NFR-AUD-02 | Audit identity wiring; controller System context | Correct user identity or System/unauthenticated context. |
| NFR-AUD-03 | EventLogger; controller result handling; AccessControl | Accurate outcomes, especially partial versus exact completion. |
| NFR-USA-01 | Controller feedback; GUI notices/alarms/confirmations | Rejection reason visible to the user; cancellations and invalid input handled. |

For every row used in the demo, add a short verification example, such as "Nurse requests 16 when stock is 15: rejected, stock unchanged." For the final document, link the row to the appropriate test/scenario rather than writing an essay inside the table.

## 10. What can wait, and what is not a task to add tonight

### Written work that can follow the demo — P2 — named owners

| Work | Owner | What still needs to be ready verbally tomorrow |
|---|---|---|
| Polished introduction/context | Emma | One sentence describing the cabinet, simplified version and simulation. |
| Written implementation notes | Marcus | Trace a request through the actual files and explain why the boundaries exist. |
| Exhaustive traceability completion beyond the demonstrated paths | Deborah | Locate the main authentication, transfer, registration, fault and communication code. |
| Comprehensive public-interface formatting | Deborah | Accurate signatures and contracts for the operations the group demonstrates. |
| Full rewrite of historical diagrams | Emma | Explain the actual current modes and any important difference from D1. |
| Expanded accessibility/ethical discussion | Emma | Confirmations, clear feedback, role restrictions and audit attribution are implemented examples; avoid claiming accessibility testing not performed. |
| Final checklist, typography, page breaks and table consistency | Deborah and Emma | No knowingly misleading diagram/table on the pages being explained. |

These sections should still be completed for the final deliverable. Deferring the prose does not remove the need to understand the content at the demo.

### Future implementation, not tonight's preparation scope — P3 — Marcus; Emma labels limits; Deborah marks traceability

- [ ] Do not rush persistence into the demo. State that restart resets the current in-memory data.
- [ ] Do not build a software watchdog just to hide the current acceptance gap. Distinguish automatic timeout detection from injected/reported faults.
- [ ] Do not add session expiry, physical badge authentication, live medicine deletion, inventory reconciliation or real HMS/hardware integration as last-minute extras.
- [ ] Do not rewrite the working GUI, add architectural layers or refactor more code just to make it look different.
- [ ] Do not delete test-only public methods only because they lack a live GUI caller. Their removal is not necessary for the demo and can break compatibility/tests.
- [ ] Do not claim the simplified version is entirely equivalent to the original now: registration and the nine-medicine demo setup are intentional changes.

Whether outstanding features are required later should be handled as a separate requirement/scope decision. This plan identifies them; it does not declare them permanently exempt from course requirements.

## 11. Suggested work order tonight

**Owners and priorities are in the task labels below. The time blocks are suggestions, not deadlines.**

1. **P0 — all three, about 10 minutes:** agree on the shared code version, demo machine, role IDs and which scenarios you will practise. Confirm the nine-medicine startup and the free slot.
2. **P0/P1 — work in parallel, roughly 45–60 minutes:** Marcus checks setup and prepares HMS/demo steps; Deborah corrects the module guide and main interfaces; Emma corrects the model, key specs and assumptions. This is a division of group work, not a request to redesign the application.
3. **P1 — all three, about 10–15 minutes:** exchange the edits and check terminology. In particular, agree on registration, partial transfers, repair versus recovery, demo timings and the HMS simulation.
4. **P0 — all three, about 20–30 minutes:** rehearse. Rotate who drives the GUI and who explains the modules. Include one successful request, one rejection and one fault/outage path; prepare the other alternatives.
5. **P1 — Marcus:** record the current verification status, resolve fixture-related test assumptions and retain any remaining gap honestly. Focus on failures affecting the demonstration first.
6. **P2 — assigned owners, only if time remains:** write the introduction, implementation notes and remaining final-document detail. Do not sacrifice the shared rehearsal to polish these sections.

## 12. Stop point for tonight

**P0/P1 — Marcus, Deborah and Emma: use this as the final check, not as a demand for perfect documentation.**

- [ ] The correct GUI launches on the demo machine and will already be open for the TA.
- [ ] The group can repeat a normal transfer, a rejected request and a safe recovery/outage scenario.
- [ ] Registration uses the free slot, creates zero stock and supports subsequent replenishment/dispensing.
- [ ] Everyone can explain the main workflow, the actual module boundaries and one information-hiding example.
- [ ] The four-variable example is concrete and correctly distinguishes environment from software representation.
- [ ] The displayed module/interfaces/specification/assumption pages have their main factual mismatches corrected or clearly annotated.
- [ ] Everyone states the actual timing profile and knows HMS/hardware are simulated.
- [ ] Test evidence is described for the configuration actually tested; older results are labeled historical.
- [ ] Introduction, implementation notes and any remaining final-document work have an owner and are explicitly scheduled for completion before November 6.

## 13. Sources and how to use this plan

This plan is based on the updated 16-page [Deliverabel_2_3K04 (1).pdf](<C:/Users/marcu/Downloads/Deliverabel_2_3K04 (1).pdf>), the local [D2 instructions](../docs/D2-instructions.pdf), [demo rubric](../docs/Demo-Rubric.pdf), [D1](../docs/D1.pdf), and the current simplified source. The updated PDF's page references are intentionally used instead of the earlier draft's pagination.

Useful local references:

- [Simplified application README](../ADC_simplified/README.md) — workflow/module guide; see M6 for the current startup/test-result wording that needs updating.
- [Controller](../ADC_simplified/adc_controller.py) — authorization, transfers, registration, maintenance, views and callback wiring.
- [Inventory](../ADC_simplified/inventory_manager.py), [hardware](../ADC_simplified/hardware_interface.py), [fault handling](../ADC_simplified/fault_handler.py), [mode rules](../ADC_simplified/mode_manager.py).
- [Access control](../ADC_simplified/access_control.py), [communication](../ADC_simplified/communication_link.py), [logger](../ADC_simplified/event_logger.py), [mock HMS](../ADC_simplified/simulated_hms.py).
- [Configuration](../ADC_simplified/config.py), [current starting inventory](../ADC_simplified/starting_inventory.py), [demo IDs](../ADC_simplified/valid_logins.py).
- [Verification report](../ADC_simplified/verification/results.md) — historical results and follow-up scope; recheck against the chosen demo fixture before claiming a current passing run.

Only this plan and its progress file are being authored for this request. The source PDF, application, existing tests and existing project reports have not been edited as part of writing the plan.


## 14. Public interface reference for document edits

**Priority: P1 for correcting demonstrated interfaces; P2 for the complete written inventory. Owner: Deborah; Marcus checks behavior.** All entries in this section inherit that owner and priority.

These signatures were extracted from the current simplified source without importing or changing the application. They are a completeness checklist, not a script to memorize. Keep the method contracts from the source and the explanations above alongside the signatures. Private workflow helpers such as _transfer may appear in implementation/traceability discussion but are not public operations.

### access_control.py — Deborah

Source: [access_control.py](../ADC_simplified/access_control.py). Exported names: AccessControl, User, AuthResult.

```python
class User:
    userId: str
    role: str

class AuthResult:
    success: bool
    user: User | None
    reason: str

class AccessControl:
    __init__(logger: EventLogger, clock: Callable=time.monotonic, timings: Timings=TIMINGS, alarm: Callable=None)
    tick() -> None
    Authenticate(userId: str) -> AuthResult
    hasPermission(user: User | None, operation: str) -> bool
    currentUser() -> User | None
    lockoutRemaining() -> float
    logout(record: bool=True) -> None

```

### adc_controller.py — Deborah

Source: [adc_controller.py](../ADC_simplified/adc_controller.py). Exported names: ADCController.

```python
class ADCController:
    __init__(clock: Callable=time.monotonic, timings: Timings=TIMINGS, wall_clock: Callable=None)
    notifyAlarm(alarmId: str, description: str) -> None
    notifyModeChange(previous: str, current: str) -> None
    canRecover() -> bool
    login(userId: str) -> bool
    logout() -> None
    dispense(medicationId: str, quantity: int) -> bool
    replenish(medicationId: str, quantity: int) -> bool
    registerMedication(medicationId: str, name: str) -> bool
    setMode(mode: str) -> bool
    repairHardware() -> bool
    closeDrawer() -> bool
    restartSoftware() -> bool
    fix() -> bool
    getCatalog() -> list[dict]
    getInventory() -> list[dict]
    getLogs() -> list[dict]
    getFaults() -> dict[str, str]
    getLogText() -> str
    getDisplayEvents() -> list[dict]
    getTraffic() -> list[dict]
    getPendingMessages() -> list[dict]
    getStatus() -> dict
    tick() -> None
    getSimulation() -> dict
    simulationOptions() -> dict
    simulate(action: str, value: str | bool='') -> None

```

### communication_link.py — Deborah

Source: [communication_link.py](../ADC_simplified/communication_link.py). Exported names: CommunicationLink.

```python
class CommunicationLink:
    __init__(transport, logger: EventLogger, clock: Callable=time.monotonic, timings: Timings=TIMINGS)
    sendMessage(messageType: str, payload: dict | str) -> bool
    sendLog(logData: str) -> bool
    sendHeartbeat() -> bool
    receiveHeartbeatResponse(response: dict | None) -> bool
    tick() -> None
    getPending() -> list[dict]
    getTraffic() -> list[dict]
    getStatus() -> dict

```

### config.py — Deborah

Source: [config.py](../ADC_simplified/config.py). Exported names: Timings, DEMO_MODE, D1_TIMINGS, DEMO_TIMINGS, TIMINGS, FAILED_LOGIN_LIMIT, MISSED_HEARTBEAT_LIMIT, MAX_MEDICATION_TYPES, LOCATION_CAPACITY, GUI_POLL_MS.

```python
class Timings:
    lockout: float
    cabinet_closure: float
    heartbeat_interval: float
    heartbeat_response: float
    message_retry: float

```

This module exports settings/startup data rather than workflow methods. Describe the data schema, validation owner and restart requirement in the module guide.

### event_logger.py — Deborah

Source: [event_logger.py](../ADC_simplified/event_logger.py). Exported names: EventLogger.

```python
class EventLogger:
    __init__(wall_clock: Callable=None)
    setUser(userId: str | None) -> None
    setSender(sender: Callable[[str], bool]) -> None
    timestamp() -> str
    readableTime(timestamp: str) -> str
    logEvent(eventType: str, description: str, *, outcome: str='recorded', medicationId: str | None=None, quantityChange: int=0, export: bool=True) -> bool
    getEvents() -> list[dict]
    formatEvents(events: list[dict]) -> str
    formatEvent(event: dict) -> str
    getDisplayEvents(events: list[dict]) -> list[dict]
    exportEvents() -> bool

```

### fault_handler.py — Deborah

Source: [fault_handler.py](../ADC_simplified/fault_handler.py). Exported names: FaultHandler.

```python
class FaultHandler:
    __init__(mode: ModeManager, logger: EventLogger, hardware: HardwareInterface, can_recover: Callable[[], bool], notify: Callable, clock: Callable=time.monotonic, timings: Timings=TIMINGS)
    raiseAlarm(alarmId: str, description: str) -> None
    clearAlarm(alarmId: str) -> None
    getAlarms() -> dict[str, str]
    handleFault(faultId: str, description: str) -> bool
    reportFault(faultId: str) -> None
    clearFault(faultId: str) -> bool
    operationCompleted() -> None
    poll() -> None
    resolveSimulatedSoftwareCondition() -> None
    restartSoftware() -> bool
    getFaults() -> dict[str, str]
    getCategories() -> tuple[str, ...]
    isSafe() -> bool

```

### gui.py — Deborah

Source: [gui.py](../ADC_simplified/gui.py). Exported names: ADCApp, main.

```python
class ADCApp:
    __init__(root: tk.Tk, controller: ADCController | None=None)
    displayMessage(message: str) -> None
    displayAlert(message: str) -> None
    getUserInput(prompt: str) -> str
    close() -> None

main() -> None
```

### hardware_interface.py — Deborah

Source: [hardware_interface.py](../ADC_simplified/hardware_interface.py). Exported names: HardwareInterface, HardwareOutcome.

```python
class HardwareOutcome:
    completed: bool
    medicationId: str
    confirmedQuantity: int
    description: str

class HardwareInterface:
    __init__(medicationIds: list[str])
    supportedFaults() -> tuple[str, ...]
    registerCompartment(medicationId: str) -> bool
    discardCompartment(medicationId: str) -> None
    injectFault(faultId: str) -> None
    repair(faultId: str) -> bool
    getFaults() -> dict[str, str]
    isClosed() -> bool | None
    lock() -> bool
    unlock(medicationId: str) -> bool
    perform(operation: str, medicationId: str, quantity: int) -> HardwareOutcome
    setNextOutcome(outcome: str) -> None
    setHoldOpen(enabled: bool) -> None
    closeDrawer() -> bool
    getStatus() -> dict

```

### inventory_manager.py — Deborah

Source: [inventory_manager.py](../ADC_simplified/inventory_manager.py). Exported names: InventoryManager.

```python
class InventoryManager:
    __init__(records: list[dict] | None=None)
    getStock(medicationId: str) -> int
    getName(medicationId: str) -> str
    validateChange(medicationId: str, quantity: int, operation: str) -> str
    addStock(medicationId: str, quantity: int) -> bool
    removeStock(medicationId: str, quantity: int) -> bool
    getRecords() -> list[dict]
    validateRegistration(medicationId: str, name: str) -> str
    registerMedication(medicationId: str, name: str) -> bool

```

### mode_manager.py — Deborah

Source: [mode_manager.py](../ADC_simplified/mode_manager.py). Exported names: ModeManager.

```python
class ModeManager:
    __init__(logger: EventLogger, on_change: Callable=None)
    setSafetyCheck(check: Callable[[], bool]) -> None
    getMode() -> str
    setMode(mode: str) -> bool
    isOperationAllowed(operation: str) -> bool

```

### simulated_hms.py — Deborah

Source: [simulated_hms.py](../ADC_simplified/simulated_hms.py). Exported names: SimulatedHMS.

```python
class SimulatedHMS:
    __init__()
    receive(message: dict) -> dict | None
    setConnected(connected: bool) -> None
    failNextMessage(failure: str) -> None
    setMissingHeartbeats(enabled: bool) -> None
    restore() -> None
    getReceived() -> list[dict]
    getStatus() -> dict

```

### starting_inventory.py — Deborah

Source: [starting_inventory.py](../ADC_simplified/starting_inventory.py). Exported names: STARTING_INVENTORY.

`STARTING_INVENTORY` is a list of dictionaries with `medicationId`, `name`, `quantity` and `capacity`. It currently has nine records. InventoryManager validates and copies the data on startup. IDs are unique numeric strings, names are nonempty, capacities are positive integers and stored quantities are integers between zero and capacity. Editing the file requires restarting to load the change.

### valid_logins.py — Deborah

Source: [valid_logins.py](../ADC_simplified/valid_logins.py). Exported names: VALID_LOGINS.

`VALID_LOGINS` maps existing role names to lists of unique numeric-string IDs. AccessControl validates the input and creates its own account lookup at startup. Editing the file requires restarting. Adding a role name alone is insufficient; its permission rules must also be defined in AccessControl.

### Additional interface documentation notes — P1 for explanation, P2 for full table detail — Deborah

- The signature blocks are reference notation, not runnable Python examples; they omit method bodies and the implicit `self` parameter.
- `User`, `AuthResult`, `HardwareOutcome` and `Timings` are frozen dataclasses. Their listed fields also determine the generated constructor arguments.
- `LogWindow` and `HMSWindow` are helpers within `gui.py`; they are not exported business modules and should not be added as new architectural layers.
- `simulationOptions`, `getCatalog` and `getLogText` do not currently drive live GUI screens. Tests/comparison scenarios use them. `getLogText` calls `EventLogger.formatEvents`. `getUserInput` has no current callers. Retaining these public methods does not mean every one needs a separate live demo.
- `resolveSimulatedSoftwareCondition` is exposed through the controller's `resolve_software` test action. The GUI recovery action is `restartSoftware`, with its own authorization and separate recovery check.
- Fault/transport test controls are still called from the live Tester workflow where wired. Do not confuse the Test controls window with code that can only execute under the unit-test runner.
- A real replacement transport would need to respect `receive(message) -> reply or None`; `OSError`/timeout failures are treated as no reply and data is retained. The current implementation does not supply a network connection.

| Returned value | Public shape / meaning to document |
|---|---|
| Inventory record | `medicationId`, `name`, `quantity`, `capacity`; independent copy. |
| Audit event | `eventId`, `timestamp`, `eventType`, `userId`, `outcome`, `medicationId`, `quantityChange`, `description`, `export`; snapshots do not expose the stored list. |
| Log display record | `eventId`, `section`, `text`; section is activity or communication. Combined/split views use the same underlying audit history. |
| Pending message item | `message`, `lastAttempt`, `attempts`; nested `message` has `id`, `type`, `payload`. Editing the returned copy cannot acknowledge or remove a message. |
| Traffic entry | `attempt`, `timestamp`, `sent`, `reply`, `result`; the controller adds readable `displayTime` for authorized viewers. One entry represents an actual send attempt, including retries. |
| Communication status | `availability`, `missedHeartbeats`, `pendingCount`; availability is Unknown/Available/Unavailable. |
| Hardware status | `selectedMedication`, `closed`, `locked`, `holdOpen`, `nextOutcome`; `closed` can be unknown. |
| Fault/alarm views | Copies mapping IDs to descriptions; categories are an immutable tuple. Alarms and registered faults are separate. |
| Logged-out controller status | Login feedback, identity fields set to None, lockout time and empty action lists; cabinet diagnostics are not exposed through this view. |
| Logged-in controller status | Role, mode, health, alarms, hardware/communication snapshots and action lists. `actions` reflects role permissions for visibility; `allowed` also applies current mode restrictions. Execution still checks stock and safety. |

**Final-document acceptance for this appendix — Deborah:** every exported operation should either be documented in the module's interface table or clearly classified as a supporting query, callback, test control or retained compatibility helper. For tomorrow, prioritize accurate explanations of the operations actually demonstrated.
