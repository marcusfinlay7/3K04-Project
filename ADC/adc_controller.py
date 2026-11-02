"""ADC CONTROLLER — coordinates modules exclusively through their public interfaces.

RESPONSIBILITY: authenticate/authorize requests and sequence inventory checks,
hardware confirmation, stock changes, logging and communication.
HIDDEN DECISION / ANTICIPATED CHANGE: workflow order and module composition.
It does NOT own credentials, stock records, mode, faults, audit or delivery state.

PUBLIC INTERFACE: login/logout; dispense/replenish/fix; setMode and named
maintenance actions; read-only get* views; tick; Tester-only simulate controls.
notifyAlarm/notifyModeChange/canRecover are public wiring callbacks, not GUI
permission shortcuts. Detailed input/result/failure contracts are on methods.

INFORMATION-HIDING EXAMPLE:
    self._inventory.getStock(medicationId)
Here _inventory is THIS controller's private reference. getStock is the OTHER
module's public operation. Reading self._inventory._records is forbidden.
All imported modules follow this same rule; GUI only talks to this controller.

Expected operation rejection returns False and a reason in getStatus.
Unauthorized simulation access raises PermissionError; invalid test choices
raise ValueError. User authorization is enforced here, not by hidden buttons."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["ADCController"]

import time
from typing import Callable

from access_control import AccessControl
from communication_link import CommunicationLink
from config import TIMINGS, Timings
from event_logger import EventLogger
from fault_handler import FaultHandler
from hardware_interface import HardwareInterface
from inventory_manager import InventoryManager
from mode_manager import ModeManager
from simulated_hms import SimulatedHMS


class ADCController:
    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    # Create the modules and connect their public callbacks into one working cabinet.
    def __init__(self, clock: Callable = time.monotonic, timings: Timings = TIMINGS,
                 wall_clock: Callable = None):
        self._logger = EventLogger(wall_clock)
        self._hms = SimulatedHMS()
        self._communication = CommunicationLink(self._hms, self._logger, clock, timings)
        self._logger.setSender(self._communication.sendLog)
        self._inventory = InventoryManager()
        self._hardware = HardwareInterface([r["medicationId"] for r in self._inventory.getRecords()])
        self._access = AccessControl(self._logger, clock, timings, self.notifyAlarm)
        self._mode = ModeManager(self._logger, self.notifyModeChange)
        self._faults = FaultHandler(self._mode, self._logger, self._hardware,
                                   self.canRecover, self.notifyAlarm, clock, timings)
        self._mode.setSafetyCheck(self._faults.isSafe)
        self._message = "Enter your user ID to sign in."
        self._health = None
        self._communication.sendMessage("mode", {"mode": self._mode.getMode()})
        self.tick()

    # PUBLIC INTERFACE: callers use these documented operations.
    # Record an alarm locally and send its description to HMS.
    def notifyAlarm(self, alarmId: str, description: str) -> None:
        """Wiring callback: register a visible alarm and queue its HMS notification.

        Trusted modules receive this public callable at construction. No private
        controller helper is handed to another module. This raises no exception.
        """
        self._faults.raiseAlarm(alarmId, description)
        self._communication.sendMessage("alarm", {"alarmId": alarmId, "description": description})

    # Tell HMS about a mode change and any entry into or exit from maintenance.
    def notifyModeChange(self, previous: str, current: str) -> None:
        """Wiring callback: queue confirmed mode and maintenance transitions.

        ModeManager owns/changes the mode; this callback only communicates it.
        """
        self._communication.sendMessage("mode", {"mode": current})
        if "Maintenance" in {previous, current}:
            self._communication.sendMessage("maintenance", {"previous": previous, "current": current})

    # Check whether the current user and cabinet mode allow a recovery attempt.
    def canRecover(self) -> bool:
        """Wiring callback: True only if current role and mode permit recovery."""
        return self._authorized("fix")

    # Submit an ID to AccessControl and save the result for the login screen.
    def login(self, userId: str) -> bool:
        """Accept one user ID; return True on authentication, False on rejection.

        Delegate identity/lockout to AccessControl, update feedback, and export
        audit events. Invalid login is an ordinary result, not an exception."""
        self._refreshLockout()
        result = self._access.Authenticate(userId)
        self._message = result.reason
        self._logger.exportEvents()
        return result.success

    # Request a drawer lock, end the user session, and record the sign-out.
    def logout(self) -> None:
        """Lock if safely possible, invalidate the session and export logout; return None."""
        self._hardware.lock()
        self._access.logout()
        self._message = "Logged out."
        self._logger.exportEvents()

    # Run the shared transfer workflow to remove the requested medicine quantity.
    def dispense(self, medicationId: str, quantity: int) -> bool:
        """Request a medication ID and positive integer quantity; return bool.

        Require authenticated dispensing permission, Normal mode, enough stock
        and safe hardware. True requires the exact confirmed quantity. Denied
        zero-movement requests leave stock unchanged. A confirmed partial amount
        is recorded but returns False. Every attempt is logged."""
        return self._transfer("dispense", medicationId, quantity)

    # Run the shared transfer workflow to add the requested medicine quantity.
    def replenish(self, medicationId: str, quantity: int) -> bool:
        """Request a medication ID and positive integer quantity; return bool.

        Check replenishment permission, Normal mode, capacity and confirmed
        hardware movement. Return False for a denied/incomplete attempt; record
        only the actual confirmed addition. Every attempt is logged."""
        return self._transfer("replenish", medicationId, quantity)

    # Handle an authorized request to enter or leave planned maintenance.
    def setMode(self, mode: str) -> bool:
        """User-facing transitions require a technician; recovery cannot be bypassed."""
        reason = self._rejection("maintenance")
        if not reason and mode not in {"Normal", "Maintenance"}:
            reason = "Fault mode is entered only by detected faults."
        if reason:
            return self._finish("maintenance", False, reason)
        success = self._mode.setMode(mode)
        if success:
            message = f"Mode changed to {mode}."
        else:
            message = "Cannot change mode: close the drawer and resolve active faults first."
        return self._finish("maintenance", success, message)

    # Ask the hardware simulator to repair its reported faults; recovery comes later.
    def repairHardware(self) -> bool:
        """Technician repairs the reported hardware; recovery is checked separately."""
        reason = self._rejection("fix")
        if reason:
            return self._finish("maintenance", False, reason)
        faults = self._hardware.getFaults()
        if not faults:
            return self._finish("maintenance", True, "No hardware repairs are needed.")
        for fault_id in faults:
            self._hardware.repair(fault_id)
        return self._finish("maintenance", True, "Hardware repaired. Close the drawer, then check recovery.")

    # Handle an authorized request to close and lock the simulated drawer.
    def closeDrawer(self) -> bool:
        """Real maintenance action, separate from fault injection controls."""
        reason = self._rejection("close_drawer")
        if reason:
            return self._finish("maintenance", False, reason)
        success = self._hardware.closeDrawer()
        if success:
            message = "Drawer closed and locked."
        else:
            message = "Closure could not be confirmed. Repair the jam or sensor first."
        return self._finish("maintenance", success, message)

    # Handle an authorized software restart without automatically clearing Fault mode.
    def restartSoftware(self) -> bool:
        """Request an authorized maintenance restart; return bool and update feedback.

        Does not bypass closure checks or automatically leave Fault mode."""
        reason = self._rejection("fix")
        if reason:
            return self._finish("maintenance", False, reason)
        success = self._faults.restartSoftware()
        if success:
            message = "Software restarted. Run Check recovery to return to Normal."
        else:
            message = "Software restart was not permitted."
        return self._finish("maintenance", success, message)

    # Verify repairs and closure, clear resolved faults, and restore Normal mode if safe.
    def fix(self) -> bool:
        """Verify repairs and closure before clearing faults and restoring Normal mode."""
        reason = self._rejection("fix")
        if reason:
            return self._finish("fix", False, reason)
        self._hardware.lock()
        for fault_id in list(self._faults.getFaults()):
            self._faults.clearFault(fault_id)
        success = self._faults.isSafe() and self._mode.setMode("Normal")
        if success:
            message = "Recovery complete. Cabinet is ready to use."
        else:
            message = "Recovery incomplete. Repair hardware, restart software if needed, and close the drawer."
        result = self._finish("fix", success, message)
        self._updateHealth()
        return result

    # Return the medicine IDs and names this user is allowed to see.
    def getCatalog(self) -> list[dict]:
        """Return copied medicationId/name entries for authorized users, otherwise []."""
        if not self._authorized("catalog"):
            return []
        return [{"medicationId": r["medicationId"], "name": r["name"]}
                for r in self._inventory.getRecords()]

    # Return a copy of stock records for an authorized user.
    def getInventory(self) -> list[dict]:
        """User clarification: all authenticated roles may inspect inventory."""
        if self._authorized("inventory"):
            return self._inventory.getRecords()
        return []

    # Return the full audit or medication history allowed for the current role.
    def getLogs(self) -> list[dict]:
        """Return copied authorized audit records; never expose EventLogger storage.

        Technician/Tester see the full log; pharmacist sees medication history;
        users without a permitted log operation get []."""
        if self._authorized("logs"):
            return self._logger.getEvents()
        if self._authorized("history"):
            return [e for e in self._logger.getEvents()
                    if e["eventType"] in {"dispense", "replenish", "inventory"}]
        return []

    # Return a copy of active faults if this user may inspect them.
    def getFaults(self) -> dict[str, str]:
        """Return copied fault descriptions when fault inspection is authorized; otherwise {}."""
        if self._authorized("faults"):
            return self._faults.getFaults()
        return {}

    # Turn the user's permitted audit records into readable text.
    def getLogText(self) -> str:
        """Return readable authorized audit text via EventLogger's public formatter."""
        return self._logger.formatEvents(self.getLogs())

    # Prepare the user's permitted log entries for the combined and split windows.
    def getDisplayEvents(self) -> list[dict]:
        """Return authorized eventId/section/text snapshots for log windows."""
        return self._logger.getDisplayEvents(self.getLogs())

    # Return permitted HMS transmission records with readable display times.
    def getTraffic(self) -> list[dict]:
        """Return authorized copied transport attempts with readable displayTime; otherwise []."""
        if not self._authorized("traffic"):
            return []
        entries = self._communication.getTraffic()
        for entry in entries:
            entry["displayTime"] = self._logger.readableTime(entry["timestamp"])
        return entries

    # Return permitted copies of messages still waiting for acknowledgement.
    def getPendingMessages(self) -> list[dict]:
        """Return authorized copies of queued packets; otherwise []."""
        if self._authorized("traffic"):
            return self._communication.getPending()
        return []

    # Collect the login or cabinet information and available actions needed by the GUI.
    def getStatus(self) -> dict:
        """Return a fresh GUI snapshot; no mutable module state is exposed.

        Unauthenticated sessions receive only login feedback and lockout time.
        Authenticated snapshots add role/mode/health/alarms/hardware/communication
        and action lists. Queries may expire a completed authentication lockout."""
        lockout_remaining = self._refreshLockout()
        user = self._access.currentUser()
        if user is None:
            return {"userId": None, "role": None, "message": self._message,
                    "lockoutRemaining": lockout_remaining, "allowed": [], "actions": []}
        operations = ("dispense", "replenish", "inventory", "history", "logs", "faults", "fix", "maintenance", "close_drawer", "traffic")
        return {"userId": user.userId, "role": user.role,
                "mode": self._mode.getMode(), "message": self._message,
                "lockoutRemaining": lockout_remaining,
                "communication": self._communication.getStatus(),
                "health": self._health, "hardware": self._hardware.getStatus(),
                "faultCategories": self._faults.getCategories(),
                "alarms": self._faults.getAlarms(),
                "actions": [op for op in (*operations, "simulation")
                            if self._access.hasPermission(user, op)],
                "allowed": [op for op in operations if self._authorized(op)]}

    # Run timer and fault checks, refresh health, and export new audit entries.
    def tick(self) -> None:
        """Poll autonomous work without falsely attributing it to the logged-in user."""
        user = self._access.currentUser()
        self._logger.setUser(None)
        try:
            self._refreshLockout()
            self._faults.poll()
            self._communication.tick()
            self._updateHealth()
            self._logger.exportEvents()
        finally:
            if user is not None:
                self._logger.setUser(user.userId)
            else:
                self._logger.setUser(None)

    # Return test diagnostics only when the signed-in user has Tester permission.
    def getSimulation(self) -> dict:
        """Return copied academic test diagnostics for an authenticated Tester.

        Raises PermissionError before disclosing data if simulation is denied."""
        if not self._access.hasPermission(self._access.currentUser(), "simulation"):
            raise PermissionError("Tester login required for simulation diagnostics.")
        return {"hms": self._hms.getStatus(), "pending": self._communication.getPending(),
                "received": self._hms.getReceived(), "hardware": self._hardware.getStatus(),
                "faults": self._faults.getFaults(), "inventory": self._inventory.getRecords()}

    # List the fault, reply-failure and movement choices supported by the simulator.
    def simulationOptions(self) -> dict:
        """Return supported test-choice values; no fixture or cabinet state changes."""
        return {"faults": self._hardware.supportedFaults(),
                "communication": ("drop_message", "drop_ack", "invalid_ack", "mismatched_ack"),
                "outcomes": ("normal", "fail", "partial")}

    # Apply an authorized test setting, then process the resulting cabinet state.
    def simulate(self, action: str, value: str | bool = "") -> None:
        """Apply one named test input, then poll the controller; return None.

        Raises PermissionError without Tester authorization and ValueError for
        unsupported choices. Never directly assigns stock, operating mode or
        an authenticated role. Real maintenance uses separate checked operations."""
        if not self._access.hasPermission(self._access.currentUser(), "simulation"):
            raise PermissionError("Tester login required for simulation controls.")
        actions = {
            "hardware_fault": self._hardware.injectFault,
            "next_outcome": self._hardware.setNextOutcome,
            "hold_open": self._hardware.setHoldOpen,
            "connected": self._hms.setConnected,
            "message_failure": self._hms.failNextMessage,
            "missing_heartbeats": self._hms.setMissingHeartbeats,
        }
        if action in actions:
            actions[action](value)
        elif action == "close_drawer":
            self._hardware.closeDrawer()
        elif action == "restore_hms":
            self._hms.restore()
        elif action == "probe":
            self._communication.sendMessage("health", {"health": self._health, "testProbe": True})
        elif action == "software_fault":
            self._faults.handleFault("software_error", "Injected software self-check failure.")
        elif action == "resolve_software":
            self._faults.resolveSimulatedSoftwareCondition()
        else:
            raise ValueError("Unsupported simulation action.")
        self.tick()

    # PRIVATE IMPLEMENTATION: only this class calls the helpers below.
    # Clear an ended lockout alarm and replace its stale login-screen message once.
    def _refreshLockout(self) -> float:
        """End the lockout notification once, before displaying or replacing feedback."""
        remaining = self._access.lockoutRemaining()
        if remaining == 0 and "login_lockout" in self._faults.getAlarms():
            self._faults.clearAlarm("login_lockout")
            if self._access.currentUser() is None:
                self._message = "Lockout ended. Enter your user ID to sign in."
        return remaining

    # Combine role permission and current-mode permission into one yes/no result.
    def _authorized(self, operation: str) -> bool:
        return (self._access.hasPermission(self._access.currentUser(), operation)
                and self._mode.isOperationAllowed(operation))

    # Explain why a role or mode blocks an action; empty text means neither blocks it.
    def _rejection(self, operation: str) -> str:
        if not self._access.hasPermission(self._access.currentUser(), operation):
            return "Authentication and the appropriate role are required."
        if not self._mode.isOperationAllowed(operation):
            return f"{operation.capitalize()} is unavailable in {self._mode.getMode()} mode."
        return ""

    # Coordinate dispensing or replenishing and report whether the full request completed.
    def _transfer(self, operation: str, medicationId: str, quantity: int) -> bool:
        # 1. Check for new faults before deciding whether the request is allowed.
        # Each validation gives a rejection reason, or empty text when it passes.
        self._faults.poll()
        reason = self._rejection(operation)
        if not reason:
            reason = self._inventory.validateChange(medicationId, quantity, operation)
        if not reason and not self._faults.isSafe():
            reason = "Cabinet is not confirmed closed and safe. Close it before another operation."
        if reason:
            # Reject before requesting any movement. Still record the failed attempt.
            if reason == "Insufficient stock.":
                self.notifyAlarm("insufficient_stock", f"Request exceeds stock for {medicationId}.")
            return self._finish(operation, False, reason, medicationId)

        # 2. Request movement from the simulator. Its confirmed quantity may be
        # smaller than requested, so the request alone cannot determine stock changes.
        outcome = self._hardware.perform(operation, medicationId, quantity)
        medicine_name = self._inventory.getName(medicationId)
        confirmed = outcome.confirmedQuantity
        # A different medicine or impossible count means we cannot trust the result.
        if outcome.medicationId != medicationId or not 0 <= confirmed <= quantity:
            self._faults.handleFault("inventory_uncertain", "Invalid hardware outcome; reconciliation required.")
            return self._finish(operation, False, "Untrusted hardware outcome; operation not confirmed.", medicationId)
        # 3. Record only confirmed movement, even if the overall request was partial.
        # delta is the signed audit change: negative for dispensing, positive for adding.
        # Zero confirmed movement skips the inventory update entirely.
        delta = 0
        if confirmed:
            if operation == "dispense":
                updated = self._inventory.removeStock(medicationId, confirmed)
                delta = -confirmed
            else:
                updated = self._inventory.addStock(medicationId, confirmed)
                delta = confirmed
            if not updated:
                # Movement already occurred, but its inventory update failed.
                # Stop further operations instead of reporting a successful transfer.
                self._faults.handleFault("inventory_uncertain", "Confirmed movement could not be recorded; reconciliation required.")
                return self._finish(operation, False, "Inventory reconciliation required.", medicationId)
            # 4. Log the new stock and send it to HMS. A missing ACK leaves the
            # message queued; it does not undo medicine movement or the stock update.
            stock = self._inventory.getStock(medicationId)
            self._logger.logEvent("inventory", f"{medicine_name}: stock is now {stock} units after confirmed movement.", outcome="success",
                                  medicationId=medicationId, quantityChange=delta)
            self._communication.sendMessage("inventory", {
                "medicationId": medicationId, "quantity": self._inventory.getStock(medicationId)})

        # 5. Full success requires both completion and the exact requested quantity.
        # For example, moving 3 of 5 units changes stock by 3 but still returns False.
        success = outcome.completed and confirmed == quantity
        if success:
            # Completion starts closure monitoring; it does not assert the drawer is closed.
            self._faults.operationCompleted()
            log_outcome = "success"
            self._faults.clearAlarm("insufficient_stock")
            if operation == "dispense":
                description = f"Dispensed {confirmed} units of {medicine_name}. Quantity confirmed."
            else:
                description = f"Added {confirmed} units of {medicine_name}. Quantity confirmed."
        else:
            log_outcome = "incomplete"
            description = f"Incomplete {operation}: only {confirmed} of {quantity} units of {medicine_name} moved."
            # Hardware normally reports the cause itself. Record a software fault
            # if an incomplete outcome arrived without any reported hardware problem.
            if not self._hardware.getFaults():
                self._faults.handleFault("software_error", "Physical operation was not completed.")
        # 6. Detect problems caused by this transfer, then record its final result
        # and update the overall health summary sent to HMS.
        self._faults.poll()
        result = self._finish(operation, success, description, medicationId, delta,
                              log_outcome)
        self._updateHealth()
        return result

    # Save user feedback, log the operation result, export new events, and return success.
    def _finish(self, operation: str, success: bool, description: str,
                medicationId: str | None = None, delta: int = 0,
                outcome: str = "denied") -> bool:
        self._message = description
        if success:
            outcome = "success"
        self._logger.logEvent(operation, description, outcome=outcome,
                              medicationId=medicationId, quantityChange=delta)
        self._logger.exportEvents()
        return success

    # Send a health update only when faults or HMS availability change the summary.
    def _updateHealth(self) -> None:
        health = "Normal"
        if self._faults.getFaults():
            health = "Degraded"
        if self._communication.getStatus()["availability"] == "Unavailable":
            health = "Degraded"
        if health != self._health:
            self._health = health
            self._communication.sendMessage("health", {"health": health})
