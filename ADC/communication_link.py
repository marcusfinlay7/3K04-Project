"""COMMUNICATION LINK — owns delivery, acknowledgements and heartbeat monitoring.

RESPONSIBILITY: queue/send messages, match replies, retry and monitor availability.
HIDDEN DECISION / ANTICIPATED CHANGE: _pending queue, IDs, retry scheduling,
heartbeat deadlines and _traffic history. A real transport can replace the mock
without Controller managing sockets, acknowledgements or retry state.

PUBLIC INTERFACE: sendLog/sendMessage/sendHeartbeat -> bool;
receiveHeartbeatResponse -> bool; tick -> None;
getPending/getTraffic/getStatus -> independent snapshots.
Pending snapshots: message/lastAttempt/attempts. Traffic: attempt/timestamp/sent/
reply/result. Status: availability/missedHeartbeats/pendingCount.
Mutating a returned packet cannot acknowledge, delete or alter a queued message.

TRANSPORT CONTRACT: receive(message: dict) -> dict or None; may raise OSError
(including TimeoutError). This module catches those errors and retains data.
Unsupported outgoing types/non-string logs raise ValueError. False delivery
means no matching ACK, not that local cabinet work must stop."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["CommunicationLink"]

from copy import deepcopy
import time
from typing import Callable
from uuid import uuid4

from config import MISSED_HEARTBEAT_LIMIT, TIMINGS, Timings
from event_logger import EventLogger


class CommunicationLink:
    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    # Start an empty delivery queue, a new message-ID prefix, and heartbeat monitoring.
    def __init__(self, transport, logger: EventLogger, clock: Callable = time.monotonic,
                 timings: Timings = TIMINGS):
        self._transport = transport
        self._logger = logger
        self._clock = clock
        self._timings = timings
        self._pending = {}
        self._status = "Unknown"
        self._misses = 0
        self._heartbeat = None
        self._next_heartbeat = clock()
        self._sequence = 0
        self._cabinet_session = uuid4().hex
        self._traffic = []

    # PUBLIC INTERFACE: callers use these documented operations.
    # Queue a new data message, retry pending data, and report whether this message got an ACK.
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

    # Send a serialized audit batch through the same reliable data-message path.
    def sendLog(self, logData: str) -> bool:
        """D2 interface: True only when acknowledged; False means retained locally."""
        if not isinstance(logData, str):
            raise ValueError("Log data must be a string.")
        return self.sendMessage("log", logData)

    # Start one heartbeat probe and response deadline if no probe is still waiting.
    def sendHeartbeat(self) -> bool:
        """Start a heartbeat response window; never count a miss before its deadline."""
        self._expireHeartbeat()
        if self._heartbeat is not None:
            return False
        message = self._message("heartbeat", {})
        self._heartbeat = {"message": message,
                           "deadline": self._clock() + self._timings.heartbeat_response}
        self._next_heartbeat = self._clock() + self._timings.heartbeat_interval
        response = self._exchange(message)
        return self.receiveHeartbeatResponse(response)

    # Accept a matching, timely heartbeat reply and reset the missed-heartbeat count.
    def receiveHeartbeatResponse(self, response: dict | None) -> bool:
        """Accept only a corresponding response within its live response window."""
        if self._heartbeat is None or self._clock() > self._heartbeat["deadline"]:
            return False
        if not self._matches(response, self._heartbeat["message"], "heartbeat_ack"):
            return False
        self._heartbeat = None
        self._misses = 0
        self._setStatus("Available")
        return True

    # Process expired heartbeat deadlines and send probes or retries that are due.
    def tick(self) -> None:
        """Nonblocking timer work, driven by tkinter.after or a test clock."""
        self._expireHeartbeat()
        if self._clock() >= self._next_heartbeat:
            self.sendHeartbeat()
        for message_id, item in list(self._pending.items()):
            if self._clock() - item["lastAttempt"] >= self._timings.message_retry:
                self._attempt(message_id)

    # Return copies of the queued data messages and their retry bookkeeping.
    def getPending(self) -> list[dict]:
        """Return deep-copy message/lastAttempt/attempts snapshots; no queue mutation."""
        return deepcopy(list(self._pending.values()))

    # Return copies of every actual transmission attempt and its reply.
    def getTraffic(self) -> list[dict]:
        """Return deep-copy attempt/timestamp/sent/reply/result records.

        Each is an actual attempt, including retries. No input or state mutation."""
        return deepcopy(self._traffic)

    # Return communication availability, consecutive missed heartbeats and queue size.
    def getStatus(self) -> dict:
        """Return availability, missedHeartbeats and pendingCount in a fresh dictionary."""
        return {"availability": self._status, "missedHeartbeats": self._misses,
                "pendingCount": len(self._pending)}

    # PRIVATE IMPLEMENTATION: only this class calls the helpers below.
    # Build a new packet with a session prefix, increasing sequence number and copied payload.
    def _message(self, kind: str, payload: dict | str) -> dict:
        # The counter is unique within this link instance. The random session
        # prefix makes collisions across runs unlikely, not mathematically impossible.
        self._sequence += 1
        return {"id": f"{self._cabinet_session}-{self._sequence}",
                "type": kind, "payload": deepcopy(payload)}

    # Make one transport attempt and record the exact packet, reply and matching result.
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
        if self._matches(response, message, expected_type):
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
    def _matches(response: dict | None, message: dict, kind: str) -> bool:
        # No self is needed: this check depends only on the supplied packet values.
        # All three checks must pass. 'and' stops early, so None never reaches .get().
        return (isinstance(response, dict) and response.get("type") == kind
                and response.get("messageId") == message["id"])

    # Retry one queued data packet and remove it only after a matching ACK.
    def _attempt(self, message_id: str) -> None:
        item = self._pending[message_id]
        item["lastAttempt"] = self._clock()
        item["attempts"] += 1
        response = self._exchange(item["message"])
        if self._matches(response, item["message"], "ack"):
            del self._pending[message_id]
        # Transport events stay local: exporting each ACK would cause an endless
        # log -> ACK -> new log cycle. Application events still go to HMS.

    # Record an availability change and retry queued data immediately when HMS recovers.
    def _setStatus(self, status: str) -> None:
        if status != self._status:
            previous = self._status
            self._status = status
            self._logger.logEvent("communication", f"HMS communication {status}.",
                                  outcome=status.lower(), export=False)
            if previous == "Unavailable" and status == "Available":
                # Recovery must not start another full waiting period for outage data.
                for message_id in list(self._pending):
                    self._attempt(message_id)

    # Count one unanswered probe when its deadline passes; repeated misses mark HMS unavailable.
    def _expireHeartbeat(self) -> None:
        if self._heartbeat is not None and self._clock() >= self._heartbeat["deadline"]:
            self._heartbeat = None
            self._misses += 1
            self._logger.logEvent("heartbeat", f"HMS did not reply in time. Missed heartbeat {self._misses} of {MISSED_HEARTBEAT_LIMIT}.",
                                  outcome="missed", export=False)
            if self._misses >= MISSED_HEARTBEAT_LIMIT:
                self._setStatus("Unavailable")
