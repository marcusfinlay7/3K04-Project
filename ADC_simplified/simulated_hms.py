"""Simulate an external HMS receiver and controlled communication failures.

PUBLIC INTERFACE: SimulatedHMS.receive returns an ack/heartbeat_ack with matching
messageId, a deliberately invalid reply, or None. Test setters configure failures;
getReceived/getStatus return independent snapshots. No ADC modules are imported."""

__all__ = ["SimulatedHMS"]

from copy import deepcopy


class SimulatedHMS:
    def __init__(self):
        self._connected = True
        self._next_failure = "none"
        self._miss_heartbeats = False
        self._received = []

    def receive(self, message: dict) -> dict | None:
        """Provisional in-process transport: return a typed, matching ACK or None."""
        if not self._connected:
            return None
        if not isinstance(message, dict) or not all(k in message for k in ("id", "type", "payload")):
            return None
        heartbeat = message["type"] == "heartbeat"
        # One-shot controls target data messages so periodic heartbeats do not consume them.
        if heartbeat:
            failure = "none"
        else:
            failure = self._next_failure
            self._next_failure = "none"
        if failure == "drop_message":
            return None
        # A dropped message never reaches this history. A dropped ACK still does,
        # because HMS received the packet even though ADC did not receive confirmation.
        self._received.append(deepcopy(message))
        if failure == "drop_ack" or (heartbeat and self._miss_heartbeats):
            return None
        if failure == "invalid_ack":
            return {"type": "invalid", "messageId": message["id"]}
        if failure == "mismatched_ack":
            return {"type": "ack", "messageId": "different-message"}
        if heartbeat:
            return {"type": "heartbeat_ack", "messageId": message["id"]}
        return {"type": "ack", "messageId": message["id"]}

    def setConnected(self, connected: bool) -> None:
        """Set the mock transport connection state; does not change ADC availability directly."""
        self._connected = bool(connected)

    def failNextMessage(self, failure: str) -> None:
        """Arm one supported data-message failure; return None.

        Allowed: none/drop_message/drop_ack/invalid_ack/mismatched_ack.
        Unsupported settings raise ValueError before changing the fixture."""
        if failure not in {"none", "drop_message", "drop_ack", "invalid_ack", "mismatched_ack"}:
            raise ValueError("Unsupported communication simulation.")
        self._next_failure = failure

    def setMissingHeartbeats(self, enabled: bool) -> None:
        """Enable/disable missing mock heartbeat replies; data traffic is unaffected."""
        self._miss_heartbeats = bool(enabled)

    def restore(self) -> None:
        """Restore mock connection and normal replies; does not fabricate ADC acknowledgements."""
        self._connected = True
        self._next_failure = "none"
        self._miss_heartbeats = False

    def getReceived(self) -> list[dict]:
        """Return deep copies of received packets; editing them cannot change receipt history."""
        return deepcopy(self._received)

    def getStatus(self) -> dict:
        """Return a fresh connected/nextFailure/missingHeartbeats snapshot."""
        return {"connected": self._connected, "nextFailure": self._next_failure,
                "missingHeartbeats": self._miss_heartbeats}
