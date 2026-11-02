"""Own packet IDs, retained data, ACK matching, retries and heartbeat deadlines.

PUBLIC INTERFACE: CommunicationLink sends data/logs/heartbeats and returns
independent pending, traffic and status snapshots. Transport.receive(packet)
returns a reply or None; OSError is treated as no reply. False delivery means
retained until a matching ACK. Heartbeats have separate response windows."""

__all__ = ["CommunicationLink"]

from copy import deepcopy
import time
from typing import Callable
from uuid import uuid4

from config import MISSED_HEARTBEAT_LIMIT, TIMINGS, Timings
from event_logger import EventLogger


class CommunicationLink:
    def __init__(self, transport, logger: EventLogger, clock: Callable = time.monotonic,
                 timings: Timings = TIMINGS):
        self._transport = transport
        self._logger = logger
        self._clock = clock
        self._timings = timings
        self._pending = {}
        self._status = "Unknown"
        self._misses = 0
        self._heartbeat_id = None
        self._heartbeat_deadline = None
        self._next_heartbeat = clock()
        self._sequence = 0
        self._cabinet_session = uuid4().hex
        self._traffic = []

    def sendMessage(self, messageType: str, payload: dict | str) -> bool:
        """Queue a supported type and copied payload; attempt all pending data.

        Return True only when this new message is acknowledged; False retains
        it. Raise ValueError before queuing an unsupported type. Allowed types:
        log/mode/inventory/alarm/maintenance/health."""
        if messageType not in {"log", "mode", "inventory", "alarm", "maintenance", "health"}:
            raise ValueError("Unsupported outbound message type.")
        message = self._message(messageType, payload)
        self._pending[message["id"]] = {"message": message, "lastAttempt": None, "attempts": 0}
        # FR-COM-08: new information triggers attempts for ALL retained information.
        for message_id in list(self._pending):
            self._attempt(message_id)
        return message["id"] not in self._pending

    def sendLog(self, logData: str) -> bool:
        """D2 interface: True only when acknowledged; False means retained locally."""
        if not isinstance(logData, str):
            raise ValueError("Log data must be a string.")
        return self.sendMessage("log", logData)

    def sendHeartbeat(self) -> bool:
        """Start a heartbeat response window; never count a miss before its deadline."""
        self._expireHeartbeat()
        if self._heartbeat_id is not None:
            return False
        message = self._message("heartbeat", {})
        # Only the ID and deadline are needed after the packet is sent.
        self._heartbeat_id = message["id"]
        self._heartbeat_deadline = self._clock() + self._timings.heartbeat_response
        self._next_heartbeat = self._clock() + self._timings.heartbeat_interval
        response = self._exchange(message)
        return self.receiveHeartbeatResponse(response)

    def receiveHeartbeatResponse(self, response: dict | None) -> bool:
        """Accept only a corresponding response within its live response window."""
        if self._heartbeat_id is None or self._clock() > self._heartbeat_deadline:
            return False
        if not self._matches(response, self._heartbeat_id, "heartbeat_ack"):
            return False
        self._heartbeat_id = None
        self._heartbeat_deadline = None
        self._misses = 0
        self._setStatus("Available")
        return True

    def tick(self) -> None:
        """Nonblocking timer work, driven by tkinter.after or a test clock."""
        self._expireHeartbeat()
        if self._clock() >= self._next_heartbeat:
            self.sendHeartbeat()
        for message_id, item in list(self._pending.items()):
            if self._clock() - item["lastAttempt"] >= self._timings.message_retry:
                self._attempt(message_id)

    def getPending(self) -> list[dict]:
        """Return deep-copy message/lastAttempt/attempts snapshots; no queue mutation."""
        return deepcopy(list(self._pending.values()))

    def getTraffic(self) -> list[dict]:
        """Return deep-copy attempt/timestamp/sent/reply/result records.

        Each is an actual attempt, including retries. No input or state mutation."""
        return deepcopy(self._traffic)

    def getStatus(self) -> dict:
        """Return availability, missedHeartbeats and pendingCount in a fresh dictionary."""
        return {"availability": self._status, "missedHeartbeats": self._misses,
                "pendingCount": len(self._pending)}

    def _message(self, kind: str, payload: dict | str) -> dict:
        # The counter is unique within this link instance. The random session
        # prefix makes collisions across runs unlikely, not mathematically impossible.
        self._sequence += 1
        return {"id": f"{self._cabinet_session}-{self._sequence}",
                "type": kind, "payload": deepcopy(payload)}

    def _exchange(self, message: dict) -> dict | None:
        sent_at = self._logger.timestamp()
        # Give the transport a copy so it cannot edit our queued packet.
        try:
            response = self._transport.receive(deepcopy(message))
        except (OSError, TimeoutError):
            response = None
        # Data and heartbeat replies have different expected types.
        expected_type = "ack"
        event_type = "communication"
        label = message["type"].replace("_", " ").capitalize()
        if message["type"] == "heartbeat":
            expected_type = "heartbeat_ack"
            event_type = "heartbeat"
        if self._matches(response, message["id"], expected_type):
            result = "Reply accepted"
        elif response is None:
            result = "No reply"
        else:
            result = "Reply rejected: wrong type or message ID"
        # Keep evidence of every attempt, including failures and retries of the same ID.
        self._traffic.append({"attempt": len(self._traffic) + 1, "timestamp": sent_at,
                              "sent": deepcopy(message), "reply": deepcopy(response), "result": result})
        self._logger.logEvent(event_type, f"{label} sent to HMS. {result}.",
                              outcome=result.lower(), export=False)
        return response

    # Check that a reply is a dictionary with the expected type and outgoing message ID.
    @staticmethod
    def _matches(response: dict | None, message_id: str, kind: str) -> bool:
        return (isinstance(response, dict) and response.get("type") == kind
                and response.get("messageId") == message_id)

    def _attempt(self, message_id: str) -> None:
        item = self._pending[message_id]
        item["lastAttempt"] = self._clock()
        item["attempts"] += 1
        response = self._exchange(item["message"])
        if self._matches(response, item["message"]["id"], "ack"):
            del self._pending[message_id]
        # Transport events stay local: exporting each ACK would cause an endless
        # log -> ACK -> new log cycle. Application events still go to HMS.

    def _setStatus(self, status: str) -> None:
        if status == self._status:
            return
        previous = self._status
        self._status = status
        self._logger.logEvent("communication", f"HMS communication {status}.",
                              outcome=status.lower(), export=False)
        if previous == "Unavailable" and status == "Available":
            # Recovery retries immediately instead of starting another waiting period.
            for message_id in list(self._pending):
                self._attempt(message_id)

    def _expireHeartbeat(self) -> None:
        if self._heartbeat_id is not None and self._clock() >= self._heartbeat_deadline:
            self._heartbeat_id = None
            self._heartbeat_deadline = None
            self._misses += 1
            self._logger.logEvent("heartbeat", f"HMS did not reply in time. Missed heartbeat {self._misses} of {MISSED_HEARTBEAT_LIMIT}.",
                                  outcome="missed", export=False)
            if self._misses >= MISSED_HEARTBEAT_LIMIT:
                self._setStatus("Unavailable")
