"""USER INTERFACE — presentation only; ADCController is its business boundary.

RESPONSIBILITY: widgets, input parsing, confirmations, separate live windows.
HIDDEN DECISION / ANTICIPATED CHANGE: tkinter widgets, layout, scroll position,
window lifetime and event scheduling. Replacing the UI does not change stock,
role, mode, fault or transport rules.

PUBLIC INTERFACE: main() starts the app; ADCApp exposes displayMessage,
displayAlert, getUserInput and close. LogWindow/HMSWindow are implementation
helpers owned by this same module, not separate business-module interfaces.

BOUNDARY RULE: only import ADCController and config from the application.
Call controller.publicOperation(...); never controller._inventory, _access,
_logger or private helpers. Widget dictionaries and callbacks stay here.
The controller rechecks every protected request; button visibility is not
authorization. Expected input conversion errors are handled locally."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["ADCApp","main"]

import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from adc_controller import ADCController
from config import DEMO_MODE, GUI_POLL_MS, TIMINGS


class LogWindow:
    """Append-only views of the same audit records; never reset the reader's scroll."""

    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    def __init__(self, parent: tk.Tk, controller: ADCController, split: bool):
        self._controller = controller
        self._split = split
        self._last_event = 0
        self.window = tk.Toplevel(parent)
        self.window.title("ADC event log")
        self.window.geometry("1050x600")
        self._follow = tk.BooleanVar(value=True)
        bar = ttk.Frame(self.window, padding=10)
        bar.pack(fill="x")
        ttk.Checkbutton(bar, text="Follow newest entries", variable=self._follow).pack(side="left")
        ttk.Label(bar, text="Local date and time. Uncheck to read older entries.").pack(side="left", padx=20)
        self._texts = {}
        panes = ttk.Panedwindow(self.window, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        if split:
            self.window.title("ADC log - activity and communication side by side")
            sections = (("activity", "Cabinet activity"), ("communication", "Heartbeats and communication"))
        else:
            sections = (("all", "Complete authorized event log"),)
        for key, title in sections:
            frame = ttk.LabelFrame(panes, text=title, padding=5)
            panes.add(frame, weight=1)
            text = ScrolledText(frame, wrap="word", state="disabled", width=45, font=("Segoe UI", 10))
            text.pack(fill="both", expand=True)
            self._texts[key] = text
        self.refresh()

    # PUBLIC INTERFACE: callers use these documented operations.
    def refresh(self) -> None:
        """Refresh presentation through Controller's public read operations; return None."""
        for event in self._controller.getDisplayEvents():
            if event["eventId"] <= self._last_event:
                continue
            key = "all"
            if self._split:
                key = event["section"]
            text = self._texts[key]
            position = text.index("@0,0")
            text.configure(state="normal")
            text.insert("end", event["text"] + "\n")
            text.configure(state="disabled")
            if self._follow.get():
                text.see("end")
            else:
                text.yview(position)
            self._last_event = event["eventId"]


class HMSWindow:
    """Show each actual send attempt and its exact reply, including failed retries."""

    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    def __init__(self, parent: tk.Tk, controller: ADCController):
        self._controller = controller
        self._entries = {}
        self.window = tk.Toplevel(parent)
        self.window.title("HMS messages - sent messages and actual replies")
        self.window.geometry("1100x700")
        self._status = tk.StringVar()
        ttk.Label(self.window, textvariable=self._status, padding=10).pack(fill="x")
        bar = ttk.Frame(self.window, padding=(10, 0, 10, 8))
        bar.pack(fill="x")
        self._follow = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text="Follow newest message", variable=self._follow).pack(side="left")
        ttk.Button(bar, text="Show waiting messages", command=self._showPending).pack(side="left", padx=15)
        ttk.Label(bar, text="Select a row to inspect the complete message and reply.").pack(side="left")
        frame = ttk.Frame(self.window)
        frame.pack(fill="x", padx=10)
        self._table = ttk.Treeview(frame, columns=("time", "number", "type", "result"), show="headings", height=8)
        for name, title, width in (("time", "Local time", 330), ("number", "Message", 85),
                                   ("type", "Sent to HMS", 160), ("result", "Actual result", 350)):
            self._table.heading(name, text=title)
            self._table.column(name, width=width)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self._table.yview)
        self._table.configure(yscrollcommand=scroll.set)
        self._table.pack(side="left", fill="x", expand=True)
        scroll.pack(side="right", fill="y")
        self._table.bind("<<TreeviewSelect>>", self._showSelected)
        self._table.bind("<Button-1>", lambda event: self._follow.set(False))
        self._details = ScrolledText(self.window, wrap="word", state="disabled", font=("Consolas", 10))
        self._details.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh()

    # PUBLIC INTERFACE: callers use these documented operations.
    def refresh(self) -> None:
        """Refresh presentation through Controller's public read operations; return None."""
        status = self._controller.getStatus()["communication"]
        self._status.set(f"HMS: {status['availability']}    |    Waiting messages: {status['pendingCount']}"
                         f"    |    Missed heartbeats in a row: {status['missedHeartbeats']}")
        newest = None
        for entry in self._controller.getTraffic():
            key = str(entry["attempt"])
            values = (entry["displayTime"], entry["sent"]["id"].rsplit("-", 1)[-1],
                      entry["sent"]["type"].capitalize(), entry["result"])
            if key not in self._entries:
                self._table.insert("", "end", iid=key, values=values)
                newest = key
            elif entry != self._entries[key]:
                self._table.item(key, values=values)
            self._entries[key] = entry
        if newest is not None and self._follow.get():
            self._table.selection_set(newest)
            self._table.see(newest)
            self._showSelected()

    # PRIVATE IMPLEMENTATION: only this class calls the helpers below.
    def _showText(self, text: str) -> None:
        self._details.configure(state="normal")
        self._details.delete("1.0", "end")
        self._details.insert("1.0", text)
        self._details.configure(state="disabled")

    def _showSelected(self, event=None) -> None:
        selected = self._table.selection()
        if not selected:
            return
        entry = self._entries[selected[0]]
        text = (entry["displayTime"] + "\n\nEXACT MESSAGE SENT TO HMS\n"
                + json.dumps(entry["sent"], indent=2) + "\n\nACTUAL HMS REPLY\n")
        if entry["reply"] is None:
            text += "No reply was received. This message has not been acknowledged."
        else:
            text += json.dumps(entry["reply"], indent=2)
        text += "\n\nResult: " + entry["result"]
        if entry["sent"]["type"] == "log":
            text += "\n\nLOG PAYLOAD EXPANDED FOR READING\n"
            text += json.dumps(json.loads(entry["sent"]["payload"]), indent=2)
        self._showText(text)

    def _showPending(self) -> None:
        self._follow.set(False)
        pending = self._controller.getPendingMessages()
        if not pending:
            self._showText("Nothing is waiting. All data messages have received matching acknowledgements.")
            return
        parts = ["WAITING FOR A VALID REPLY\nThese messages are retained and will be retried.\n"]
        for item in pending:
            parts.append(f"Send attempts: {item['attempts']}\n" + json.dumps(item["message"], indent=2))
        self._showText("\n\n".join(parts))


class ADCApp:
    """The main window signs in users and performs cabinet operations."""

    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    def __init__(self, root: tk.Tk, controller: ADCController | None = None):
        self._root = root
        if controller is None:
            controller = ADCController()
        self._controller = controller
        self._root.title("ADC - Medication cabinet")
        self._root.geometry("900x670")
        self._root.minsize(800, 620)
        self._root.protocol("WM_DELETE_WINDOW", self.close)
        self._windows = {}
        self._maintenance_window = None
        self._test_window = None
        self._after_id = None

        self._login_frame = ttk.Frame(root, padding=35)
        self._login_frame.pack(fill="both", expand=True)
        ttk.Label(self._login_frame, text="Medication cabinet", font=("Segoe UI", 22)).pack(pady=(40, 20))
        ttk.Label(self._login_frame, text="Enter your user ID. Your role is looked up automatically.").pack(pady=10)
        self._user_id = tk.StringVar()
        self._id_entry = ttk.Entry(self._login_frame, textvariable=self._user_id, width=24, font=("Segoe UI", 16))
        self._id_entry.pack(pady=10)
        self._id_entry.bind("<Return>", lambda event: self._login())
        self._login_button = ttk.Button(self._login_frame, text="Sign in", command=self._login)
        self._login_button.pack(pady=12)
        self._login_message = tk.StringVar()
        self._login_label = tk.Label(self._login_frame, textvariable=self._login_message, wraplength=700,
                                     font=("Segoe UI", 11), padx=15, pady=15)
        self._login_label.pack(fill="x", pady=15)

        self._content = ttk.Frame(root, padding=15)
        top = ttk.Frame(self._content)
        top.pack(fill="x")
        self._status = tk.StringVar()
        ttk.Label(top, textvariable=self._status, font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(top, text="Sign out", command=self._logout).pack(side="right")
        self._connection = tk.StringVar()
        ttk.Label(self._content, textvariable=self._connection).pack(anchor="w", pady=8)
        self._alarm = tk.StringVar()
        self._alarm_label = tk.Label(self._content, textvariable=self._alarm, anchor="w", justify="left",
                                    wraplength=830, font=("Segoe UI", 11, "bold"), padx=10, pady=10)
        self._alarm_label.pack(fill="x", pady=(0, 10))
        ttk.Label(self._content, text="1. Select a medicine").pack(anchor="w")
        self._inventory = ttk.Treeview(self._content, columns=("name", "quantity", "capacity"), show="headings", height=10)
        for name, title, width in (("name", "Medicine", 450), ("quantity", "In stock", 130), ("capacity", "Capacity", 130)):
            self._inventory.heading(name, text=title)
            self._inventory.column(name, width=width)
        self._inventory.pack(fill="x", pady=6)
        self._inventory.bind("<<TreeviewSelect>>", self._selectMedicine)
        self._medication = tk.StringVar(value="001")
        self._selection_label = tk.StringVar()
        self._selection_widget = ttk.Label(self._content, textvariable=self._selection_label)
        self._selection_widget.pack(anchor="w", pady=3)
        self._transfer_frame = ttk.Frame(self._content)
        self._transfer_frame.pack(fill="x", pady=8)
        ttk.Label(self._transfer_frame, text="2. Quantity").pack(side="left")
        self._quantity = tk.StringVar(value="1")
        ttk.Entry(self._transfer_frame, textvariable=self._quantity, width=8).pack(side="left", padx=10)
        self._buttons = {}
        for action, title in (("dispense", "Dispense medicine"), ("replenish", "Add stock")):
            self._buttons[action] = ttk.Button(self._transfer_frame, text=title,
                                               command=lambda operation=action: self._transfer(operation))
        self._notice = tk.StringVar()
        ttk.Label(self._content, textvariable=self._notice, wraplength=830,
                  font=("Segoe UI", 11, "bold")).pack(fill="x", pady=8)
        self._toolbar = ttk.Frame(self._content)
        self._toolbar.pack(fill="x", pady=10)
        for action, title, callback in (
            ("log", "Event log", lambda: self._openLog(False)),
            ("split", "Split log", lambda: self._openLog(True)),
            ("traffic", "HMS messages", self._openHMS),
            ("maintenance", "Maintenance", self._openMaintenance),
            ("simulation", "Test controls", self._openTests),
        ):
            self._buttons[action] = ttk.Button(self._toolbar, text=title, command=callback)
        self._refresh()
        self._after_id = root.after(GUI_POLL_MS, self._poll)
        self._id_entry.focus_set()

    # PUBLIC INTERFACE: callers use these documented operations.
    def displayMessage(self, message: str) -> None:
        """Display supplied feedback text without changing business state; return None."""
        self._notice.set(message)

    def displayAlert(self, message: str) -> None:
        """Display a supplied alarm message; no Python exception is raised."""
        self._alarm.set("ALARM - " + message)
        self._alarm_label.configure(background="#ffe1df", foreground="#9c1c12")

    def getUserInput(self, prompt: str) -> str:
        """Prompt for text; return the entered string or an empty string on cancellation."""
        result = simpledialog.askstring("ADC", prompt, parent=self._root)
        if result is None:
            return ""
        return result

    def close(self) -> None:
        """Cancel this UI's timer, close its windows and request logout; return None."""
        if self._after_id is not None:
            self._root.after_cancel(self._after_id)
        self._closeWindows()
        self._controller.logout()
        self._root.destroy()

    # PRIVATE IMPLEMENTATION: only this class calls the helpers below.
    def _login(self) -> None:
        self._closeWindows()
        self._controller.login(self._user_id.get())
        self._user_id.set("")
        self._refresh()

    def _logout(self) -> None:
        self._closeWindows()
        self._controller.logout()
        self._refresh()

    def _selectMedicine(self, event=None) -> None:
        selected = self._inventory.selection()
        if selected:
            self._medication.set(selected[0])
            name = self._inventory.item(selected[0], "values")[0]
            self._selection_label.set("Selected: " + name)

    def _transfer(self, operation: str) -> None:
        try:
            quantity = int(self._quantity.get())
        except ValueError:
            quantity = None
        if quantity is not None:
            selected = self._selection_label.get()
            if not messagebox.askyesno("Confirm", f"{operation.capitalize()} {quantity} unit(s)?\n{selected}", parent=self._root):
                return
        if operation == "dispense":
            self._controller.dispense(self._medication.get(), quantity)
        else:
            self._controller.replenish(self._medication.get(), quantity)
        self._refresh()

    def _run(self, operation, *args) -> None:
        operation(*args)
        self._refresh()

    def _openLog(self, split: bool) -> None:
        key = "log"
        if split:
            key = "split"
        if key in self._windows and self._windows[key].window.winfo_exists():
            self._windows[key].window.lift()
            return
        self._windows[key] = LogWindow(self._root, self._controller, split)

    def _openHMS(self) -> None:
        if "hms" in self._windows and self._windows["hms"].window.winfo_exists():
            self._windows["hms"].window.lift()
            return
        self._windows["hms"] = HMSWindow(self._root, self._controller)

    def _openMaintenance(self) -> None:
        if self._maintenance_window is not None and self._maintenance_window.winfo_exists():
            self._maintenance_window.lift()
            return
        self._maintenance_window = tk.Toplevel(self._root)
        self._maintenance_window.title("Technician maintenance")
        frame = ttk.Frame(self._maintenance_window, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Repair the problem, then check recovery.", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self._maintenance_status = tk.StringVar()
        ttk.Label(frame, textvariable=self._maintenance_status, wraplength=600, justify="left").pack(fill="x", pady=15)
        actions = (
            ("Start planned maintenance", lambda: self._run(self._controller.setMode, "Maintenance")),
            ("Repair reported hardware", lambda: self._run(self._controller.repairHardware)),
            ("Restart software", lambda: self._run(self._controller.restartSoftware)),
            ("Close and lock drawer", lambda: self._run(self._controller.closeDrawer)),
            ("Check recovery / finish maintenance", lambda: self._run(self._controller.fix)),
        )
        for title, callback in actions:
            ttk.Button(frame, text=title, command=callback).pack(fill="x", pady=4)
        ttk.Label(frame, textvariable=self._notice, wraplength=600).pack(fill="x", pady=15)
        self._refresh()

    def _openTests(self) -> None:
        if self._test_window is not None and self._test_window.winfo_exists():
            self._test_window.lift()
            return
        self._test_window = tk.Toplevel(self._root)
        self._test_window.title("Tester - create demo conditions")
        frame = ttk.Frame(self._test_window, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Testing only", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        timing_label = "D1 timing"
        if DEMO_MODE:
            timing_label = "Short demo timing"
        ttk.Label(frame, text=f"{timing_label}: heartbeat every {TIMINGS.heartbeat_interval}s; retry after {TIMINGS.message_retry}s.").pack(anchor="w", pady=8)
        fault_frame = ttk.LabelFrame(frame, text="Cause a cabinet problem", padding=12)
        fault_frame.pack(fill="x", pady=8)
        fault_names = {
            "Jammed drawer": "drawer_jam", "Broken closure sensor": "closure_sensor",
            "Hardware connection lost": "hardware_interface", "Wrong medicine in compartment": "medication_mismatch",
            "Software self-check failed": "software_error",
        }
        self._fault_choice = tk.StringVar(value="Jammed drawer")
        ttk.Combobox(fault_frame, textvariable=self._fault_choice, values=list(fault_names), state="readonly", width=35).pack(side="left")

        def inject_fault():
            fault = fault_names[self._fault_choice.get()]
            if fault == "software_error":
                self._simulate("software_fault")
            else:
                self._simulate("hardware_fault", fault)

        ttk.Button(fault_frame, text="Cause problem", command=inject_fault).pack(side="left", padx=10)
        physical = ttk.LabelFrame(frame, text="Next medicine operation", padding=12)
        physical.pack(fill="x", pady=8)
        outcome_names = {"Complete normally": "normal", "Fail without moving stock": "fail", "Stop after moving some stock": "partial"}
        self._physical_outcome = tk.StringVar(value="Complete normally")
        ttk.Combobox(physical, textvariable=self._physical_outcome, values=list(outcome_names), state="readonly", width=35).pack(side="left")
        ttk.Button(physical, text="Set next outcome", command=lambda: self._simulate("next_outcome", outcome_names[self._physical_outcome.get()])).pack(side="left", padx=10)
        self._hold_open = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Leave drawer open after use (to demonstrate the closure alarm)", variable=self._hold_open,
                        command=lambda: self._simulate("hold_open", self._hold_open.get())).pack(anchor="w", pady=8)
        hms = ttk.LabelFrame(frame, text="HMS connection", padding=12)
        hms.pack(fill="x", pady=8)
        ttk.Button(hms, text="Disconnect HMS", command=lambda: self._simulate("connected", False)).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Button(hms, text="Restore HMS", command=lambda: self._simulate("restore_hms")).grid(row=0, column=1, padx=15)
        self._missing_heartbeats = tk.BooleanVar()
        ttk.Checkbutton(hms, text="Do not reply to heartbeats", variable=self._missing_heartbeats,
                        command=lambda: self._simulate("missing_heartbeats", self._missing_heartbeats.get())).grid(row=1, column=0, columnspan=2, sticky="w", pady=8)
        failure_names = {"Drop the outgoing message": "drop_message", "Do not acknowledge it": "drop_ack",
                         "Reply with the wrong type": "invalid_ack", "Reply for a different message": "mismatched_ack"}
        self._message_failure = tk.StringVar(value="Do not acknowledge it")
        ttk.Combobox(hms, textvariable=self._message_failure, values=list(failure_names), state="readonly", width=35).grid(row=2, column=0, pady=8)
        ttk.Button(hms, text="Apply to next data message", command=lambda: self._simulate("message_failure", failure_names[self._message_failure.get()])).grid(row=2, column=1, padx=15)
        ttk.Button(hms, text="Send a test message now", command=lambda: self._simulate("probe")).grid(row=3, column=0, sticky="w", pady=8)
        ttk.Button(frame, text="Open HMS messages", command=self._openHMS).pack(anchor="w", pady=8)
        self._test_status = tk.StringVar()
        ttk.Label(frame, textvariable=self._test_status, wraplength=650).pack(fill="x", pady=8)
        self._refresh()

    def _simulate(self, action: str, value: str | bool = "") -> None:
        self._controller.simulate(action, value)
        self._refresh()

    def _refresh(self) -> None:
        status = self._controller.getStatus()
        if status["userId"] is None:
            self._closeWindows()
            self._content.pack_forget()
            self._login_frame.pack(fill="both", expand=True)
            self._inventory.delete(*self._inventory.get_children())
            message = status["message"]
            if status["lockoutRemaining"] > 0:
                message = f"SECURITY ALARM\nThree failed logins. Try again in {status['lockoutRemaining']:.0f} seconds."
                self._login_label.configure(background="#ffe1df", foreground="#9c1c12")
            else:
                self._login_label.configure(background=self._root.cget("background"), foreground="black")
            self._login_message.set(message)
            return
        self._login_frame.pack_forget()
        self._content.pack(fill="both", expand=True)
        self._status.set(f"{status['role']} - ID {status['userId']}    |    Mode: {status['mode']}")
        communication = status["communication"]
        self._connection.set(f"HMS: {communication['availability']}    |    Messages waiting for a reply: {communication['pendingCount']}")
        if status["alarms"]:
            alarm_message = "\n".join(status["alarms"].values())
            if status["mode"] == "Fault":
                alarm_message += "\nMedicine operations are stopped. A technician must repair the cabinet."
            self.displayAlert(alarm_message)
        else:
            self._alarm.set("No active alarms")
            self._alarm_label.configure(background="#e7f0e7", foreground="#244d29")
        for record in self._controller.getInventory():
            item = record["medicationId"]
            values = (record["name"], record["quantity"], record["capacity"])
            if self._inventory.exists(item):
                self._inventory.item(item, values=values)
            else:
                self._inventory.insert("", "end", iid=item, values=values)
        if not self._inventory.selection() and self._inventory.get_children():
            self._inventory.selection_set(self._inventory.get_children()[0])
            self._selectMedicine()
        for action in ("dispense", "replenish"):
            if action in status["actions"]:
                self._buttons[action].pack(side="left", padx=5)
            else:
                self._buttons[action].pack_forget()
        if "dispense" in status["actions"] or "replenish" in status["actions"]:
            self._transfer_frame.pack(after=self._selection_widget, fill="x", pady=8)
        else:
            self._transfer_frame.pack_forget()
        for key in ("log", "split", "traffic", "maintenance", "simulation"):
            permitted = key in status["actions"]
            if key in {"log", "split"}:
                permitted = "logs" in status["actions"] or "history" in status["actions"]
            if permitted:
                self._buttons[key].pack(side="left", padx=(0, 8))
            else:
                self._buttons[key].pack_forget()
        self.displayMessage(status["message"])
        for key, viewer in list(self._windows.items()):
            if viewer.window.winfo_exists():
                viewer.refresh()
            else:
                del self._windows[key]
        if self._maintenance_window is not None and self._maintenance_window.winfo_exists():
            problems = self._controller.getFaults()
            lines = [f"Cabinet mode: {status['mode']}"]
            if problems:
                for description in problems.values():
                    lines.append("Problem: " + description)
            else:
                lines.append("No registered faults.")
            if status["hardware"]["closed"] is True:
                lines.append("Drawer: closed")
            elif status["hardware"]["closed"] is False:
                lines.append("Drawer: open - close it before checking recovery")
            else:
                lines.append("Drawer: sensor cannot confirm closure")
            self._maintenance_status.set("\n".join(lines))
        if self._test_window is not None and self._test_window.winfo_exists():
            state = self._controller.getSimulation()
            self._hold_open.set(state["hardware"]["holdOpen"])
            self._missing_heartbeats.set(state["hms"]["missingHeartbeats"])
            connection = "connected"
            if not state["hms"]["connected"]:
                connection = "disconnected"
            self._test_status.set(f"Simulated cable: {connection}. Use the Maintenance window to repair cabinet problems.")

    def _poll(self) -> None:
        self._controller.tick()
        self._refresh()
        self._after_id = self._root.after(GUI_POLL_MS, self._poll)

    def _closeWindows(self) -> None:
        for viewer in self._windows.values():
            if viewer.window.winfo_exists():
                viewer.window.destroy()
        self._windows.clear()
        for window in (self._maintenance_window, self._test_window):
            if window is not None and window.winfo_exists():
                window.destroy()
        self._maintenance_window = None
        self._test_window = None


def main() -> None:
    """Start Tk; report invalid startup data and exit rather than run with bad records."""
    root = tk.Tk()
    try:
        ADCApp(root)
    except ValueError as error:
        messagebox.showerror("Check the demo data files", str(error), parent=root)
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
