"""EVENT LOGGER — owns one audit history and its representations.

RESPONSIBILITY: append audit events, format readable views and queue exports.
HIDDEN DECISION / ANTICIPATED CHANGE: _events storage, timestamp formatting,
display classification and _export_cursor. Callers do not format stored events
or edit the audit history.

PUBLIC INTERFACE: logEvent/exportEvents -> bool; getEvents -> deep-copy records;
formatEvent/formatEvents/readableTime/timestamp -> str;
getDisplayEvents -> copied display records; setUser/setSender -> None.
Event snapshots contain eventId/timestamp/eventType/userId/outcome/medicationId/
quantityChange/description/export. Display records have eventId/section/text.
These schemas are public contracts; the storage container is private.

TRUSTED WIRING: sender(logData: str) -> bool is CommunicationLink.sendLog.
False means retained but not acknowledged; CommunicationLink owns retries.
getEvents never returns _events itself; split views never alter audit records."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["EventLogger"]

from copy import deepcopy
from datetime import datetime, timezone
import json
from typing import Callable


class EventLogger:
    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    def __init__(self, wall_clock: Callable = None):
        self._clock = wall_clock or (lambda: datetime.now(timezone.utc))
        self._events = []
        self._user_id = None
        self._sender = None
        self._export_cursor = 0

    # PUBLIC INTERFACE: callers use these documented operations.
    def setUser(self, userId: str | None) -> None:
        """Set audit context from the authenticated session, never a credential."""
        self._user_id = userId

    def setSender(self, sender: Callable[[str], bool]) -> None:
        """Connect CommunicationLink.sendLog after application composition."""
        self._sender = sender

    def timestamp(self) -> str:
        """Keep an unambiguous timestamp internally, including its timezone."""
        try:
            return self._clock().isoformat()
        except (OSError, ValueError, AttributeError):
            return "unavailable"

    @staticmethod
    def readableTime(timestamp: str) -> str:
        """Display the computer's local clock, with date, AM/PM and UTC offset."""
        try:
            local_time = datetime.fromisoformat(timestamp).astimezone()
        except (ValueError, TypeError):
            return "Time unavailable"
        offset = local_time.strftime("%z")
        offset = offset[:3] + ":" + offset[3:]
        return local_time.strftime("%b %d, %Y  %I:%M:%S %p") + f" (UTC{offset})"

    def logEvent(self, eventType: str, description: str, *,
                 outcome: str = "recorded", medicationId: str | None = None,
                 quantityChange: int = 0, export: bool = True) -> bool:
        """Append one event with time and current audit identity; return bool.

        eventType must be a nonempty string and description a string, otherwise
        return False without appending. Keyword metadata adds outcome/medicine/
        quantity. export=False is reserved for local transport diagnostics."""
        if not isinstance(eventType, str) or not eventType.strip():
            return False
        if not isinstance(description, str):
            return False
        self._events.append({
            "eventId": len(self._events) + 1, "timestamp": self.timestamp(),
            "eventType": eventType, "userId": self._user_id,
            "outcome": outcome, "medicationId": medicationId,
            "quantityChange": quantityChange, "description": description,
            "export": export,
        })
        return True

    def getEvents(self) -> list[dict]:
        """Return independent records so callers cannot alter the audit trail."""
        return deepcopy(self._events)

    def formatEvents(self, events: list[dict]) -> str:
        """Own the readable audit representation as well as the stored representation."""
        lines = []
        for event in events:
            lines.append(self.formatEvent(event))
        return "\n".join(lines)

    def formatEvent(self, event: dict) -> str:
        """Friendly log display; the original event record remains unchanged."""
        actor = "System"
        if event["userId"] is not None:
            actor = "User " + event["userId"]
        title = event["eventType"].replace("_", " ").title()
        text = (f"{self.readableTime(event['timestamp'])}  |  {title}  |  {actor}\n"
                f"{event['description']}  Result: {event['outcome']}.")
        if event["medicationId"] is not None:
            text += f"  Medicine ID: {event['medicationId']}."
        if event["quantityChange"] != 0:
            text += f"  Stock change: {event['quantityChange']:+d}."
        return text + "\n"

    def getDisplayEvents(self, events: list[dict]) -> list[dict]:
        """Convert supplied event snapshots into new display records.

        Each has eventId/section/text. Does not mutate input or stored history;
        section is activity or communication. Input must follow getEvents schema."""
        result = []
        for event in events:
            section = "activity"
            if event["eventType"] in {"heartbeat", "communication"}:
                section = "communication"
            result.append({"eventId": event["eventId"], "section": section,
                           "text": self.formatEvent(event)})
        return result

    def exportEvents(self) -> bool:
        """Queue new records once; Communication Link owns retries until ACK."""
        if self._sender is None:
            return False
        end = len(self._events)
        records = [e for e in self._events[self._export_cursor:end] if e["export"]]
        delivered = True
        if records:
            delivered = self._sender(json.dumps(records))
        # False from sendLog means retained, not rejected. Do not create duplicates.
        self._export_cursor = end
        return delivered
