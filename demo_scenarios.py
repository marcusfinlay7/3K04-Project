import json
import secrets
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class DemoADCs:
    def __init__(self, system):
        self.system = system
        self.paused = set()
        self.pending = {"ADC-01": [], "ADC-02": []}
        self.quantities = {
            "ADC-01": {"Paracetamol": 16, "Ibuprofen": 3},
            "ADC-02": {"Paracetamol": 24, "Amoxicillin": 12},
        }
        self.health = {"ADC-01": "HEALTHY", "ADC-02": "HEALTHY"}
        self.lock = Lock()
        for adc in self.quantities:
            previous = system.store.inventory(adc)
            if previous:
                self.quantities[adc] = {item["medication"]: item["quantity"] for item in previous}

    def send(self, adc_id, kind, data):
        return self.system.receive(self.system.make_demo_message(adc_id, kind, data))

    def snapshot(self, adc_id):
        self.send(adc_id, "health", {"status": self.health[adc_id]})
        for name, qty in self.quantities[adc_id].items():
            self.send(adc_id, "inventory", {"medication": name, "quantity": qty})
        self.send(adc_id, "sync_complete", {})

    def seed(self):
        if self.system.store.cabinets():
            for adc in self.pending:
                self.send(adc, "heartbeat", {})
                self.snapshot(adc)
            return
        for adc in self.pending:
            self.send(adc, "heartbeat", {})
            self.snapshot(adc)
        self.send("ADC-02", "alarm", {"alarm_id": "door", "category": "system",
            "description": "Door sensor fault", "state": "ACTIVE"})
        self.send("ADC-01", "event", {"action": "dispense", "medication": "Paracetamol",
            "quantity": 2, "employee_id": "101"})

    def tick(self):
        with self.lock:
            for adc in self.pending:
                if adc not in self.paused:
                    self.send(adc, "heartbeat", {})
        self.system.check_timeouts()

    def pause(self, adc_id):
        with self.lock:
            self.paused.add(adc_id)
            self.system.mark_offline(adc_id)

    def restore(self, adc_id):
        with self.lock:
            self.paused.discard(adc_id)
            self.send(adc_id, "heartbeat", {})
            for event in self.pending[adc_id]:
                self.system.receive(event)
            self.pending[adc_id].clear()
            self.snapshot(adc_id)

    def local_event(self, adc_id, action, medication="Paracetamol", quantity=1):
        with self.lock:
            if adc_id not in self.pending:
                raise ValueError("Unknown demo cabinet")
            if action == "dispense":
                if self.quantities[adc_id].get(medication, 0) < quantity:
                    return False
                self.quantities[adc_id][medication] -= quantity
            elif action == "restock":
                self.quantities[adc_id][medication] = self.quantities[adc_id].get(medication, 0) + quantity
            else:
                raise ValueError("Unsupported demo action")
            event = self.system.make_demo_message(adc_id, "event", {"action": action,
                "medication": medication, "quantity": quantity, "employee_id": "102"})
            if adc_id in self.paused:
                self.pending[adc_id].append(event)
            else:
                self.system.receive(event)
                self.send(adc_id, "inventory", {"medication": medication,
                    "quantity": self.quantities[adc_id][medication]})
            return True

    def set_inventory(self, adc_id, medication, quantity):

        with self.lock:
            if medication not in self.quantities[adc_id] or type(quantity) is not int or quantity < 0:
                raise ValueError("Invalid simulated inventory")
            self.quantities[adc_id][medication] = quantity
            if adc_id not in self.paused:
                self.send(adc_id, "inventory", {"medication": medication, "quantity": quantity})

    def fault(self, adc_id):
        with self.lock:
            self.health[adc_id] = "FAULT"
            if adc_id not in self.paused:
                self.send(adc_id, "health", {"status": "FAULT"})
                self.send(adc_id, "alarm", {"alarm_id": "health", "category": "system",
                    "description": "Cabinet health fault", "state": "ACTIVE"})

    def repair(self, adc_id):
        with self.lock:
            self.health[adc_id] = "HEALTHY"
            if adc_id not in self.paused:
                self.send(adc_id, "health", {"status": "HEALTHY"})
                self.send(adc_id, "alarm", {"alarm_id": "health", "category": "system",
                    "description": "Cabinet health fault", "state": "RESOLVED"})

    def resolve_door(self, adc_id):
        with self.lock:
            if adc_id not in self.paused:
                self.send(adc_id, "alarm", {"alarm_id": "door", "category": "system",
                    "description": "Door sensor fault", "state": "RESOLVED"})


SCENARIO_DIRECTORY = Path(__file__).resolve().parent / "scenarios"
class ScenarioError(ValueError):
    pass

def read_scenario(filename):
    candidates = {p.stem: p for p in SCENARIO_DIRECTORY.glob("*.json") if p.is_file()}
    path = candidates.get(filename)
    if path is None:
        raise ScenarioError("Unknown scenario")
    try:
        scenario = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScenarioError(f"Could not load {path.name}: {exc}") from exc
    if not isinstance(scenario, dict):
        raise ScenarioError("The JSON file must contain an object")
    return {"file": path.name, "slug": path.stem, **scenario}


def run_scenario(name, demo, monitor):
    scenario = read_scenario(name)
    notes = []
    try:
        for index, step in enumerate(scenario["steps"], start=1):
            action = step["action"]
            adc_id = step.get("adc_id", scenario["adc_id"])
            if action == "set_inventory":
                demo.set_inventory(adc_id, step["medication"], step["quantity"])
            elif action in {"restock", "dispense"}:
                if not demo.local_event(adc_id, action, step["medication"], step["quantity"]):
                    raise ScenarioError(f"Step {index}: not enough stock for {step['medication']}")
            elif action == "disconnect":
                demo.pause(adc_id)
            elif action == "reconnect":
                demo.restore(adc_id)
            elif action == "fault":
                demo.fault(adc_id)
            elif action == "repair":
                demo.repair(adc_id)
            elif action == "door_fixed":
                demo.resolve_door(adc_id)
            elif action == "invalid_inventory":
                result = monitor.receive(monitor.make_demo_message(adc_id, "inventory", {
                    "medication": step["medication"], "quantity": step["quantity"]
                }))
                if result["ok"]:
                    raise ScenarioError(f"Step {index}: invalid inventory was unexpectedly accepted")
                notes.append("Invalid message rejected")
            else:
                raise ScenarioError(f"Step {index}: unknown action {action}")
        return {"name": scenario.get("name", name), "adc_id": scenario["adc_id"],
                "steps": len(scenario["steps"]), "notes": notes}
    except ScenarioError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise ScenarioError(f"Invalid scenario step: {error}") from None


TOKEN_PATH = Path(__file__).resolve().parent / "data" / ".scenario_cli_token"


def local_token(create=False):
    if create:
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with TOKEN_PATH.open("x", encoding="utf-8") as file:
                file.write(secrets.token_urlsafe(32))
            try:
                TOKEN_PATH.chmod(0o600)
            except OSError:
                pass
        except FileExistsError:
            pass
    return TOKEN_PATH.read_text(encoding="utf-8").strip()


def send_terminal_request(port, scenario):
    try:
        token = local_token()
    except OSError:
        raise RuntimeError("Start the dashboard first: py app.py --demo") from None

    url = f"http://127.0.0.1:{port}/_local/scenarios"
    headers = {"X-Scenario-Token": token, "Content-Type": "application/json"}
    payload = {"name": scenario.removesuffix(".json")}
    request = Request(url, data=json.dumps(payload).encode("utf-8"),
                      headers=headers, method="POST")

    try:
        with urlopen(request, timeout=10) as response:
            return json.load(response)
    except HTTPError as error:
        try:
            message = json.load(error).get("error", "Request rejected")
        except (ValueError, OSError):
            message = "Access denied or invalid request"
        raise RuntimeError(f"Scenario failed: {message} (HTTP {error.code})") from None
    except (URLError, TimeoutError):
        raise RuntimeError(
            "Cannot connect to the dashboard. Start py app.py --demo in another terminal."
        ) from None
