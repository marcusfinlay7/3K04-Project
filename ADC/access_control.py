"""ACCESS CONTROL — owns authentication and role permissions.

RESPONSIBILITY: ID lookup, current session, permission checks and login lockout.
HIDDEN DECISION / ANTICIPATED CHANGE: _accounts/_permissions, the session and
failure counters. Replace the credential source or role rules here; callers
still use Authenticate and hasPermission.

PUBLIC INTERFACE: Authenticate(userId) -> frozen AuthResult;
hasPermission(user, operation) -> bool; currentUser -> frozen User or None;
logout/tick -> None; lockoutRemaining -> seconds.
User(userId, role) and AuthResult(success, user, reason) are immutable values.
Callers cannot set the current user, role, failure count or lockout deadline.

TRUSTED WIRING: optional alarm(id, description) -> None is a public callback
supplied by Controller. This module never calls a controller private method.
Bad startup ID lists raise ValueError. Invalid logins return an AuthResult,
not an exception. GUI never reads _accounts or _permissions."""

# Exported module interface (a declaration, not Python access enforcement).
__all__ = ["AccessControl","User","AuthResult"]

from dataclasses import dataclass
import time
from typing import Callable

from config import FAILED_LOGIN_LIMIT, TIMINGS, Timings
from event_logger import EventLogger
from valid_logins import VALID_LOGINS


@dataclass(frozen=True)
class User:
    userId: str
    role: str


@dataclass(frozen=True)
class AuthResult:
    success: bool
    user: User | None
    reason: str


class AccessControl:
    # CONSTRUCTION / PRIVATE STATE: these fields belong to this class only.
    # Load valid IDs and role permissions, then start with no signed-in user.
    def __init__(self, logger: EventLogger, clock: Callable = time.monotonic,
                 timings: Timings = TIMINGS, alarm: Callable = None):
        self._logger = logger
        self._clock = clock
        self._timings = timings
        self._alarm = alarm
        self._permissions = {
            "Nurse": {"dispense", "catalog", "inventory"},
            "Pharmacist": {"replenish", "catalog", "inventory", "history"},
            "Technician": {"fix", "maintenance", "faults", "logs", "catalog", "inventory", "traffic", "close_drawer"},
            "Tester": {"dispense", "replenish", "catalog", "inventory", "history",
                       "fix", "maintenance", "faults", "logs", "traffic", "close_drawer", "simulation"},
        }
        self._accounts = {}
        for role, user_ids in VALID_LOGINS.items():
            if role not in self._permissions:
                raise ValueError(f"Unknown role in valid_logins.py: {role}")
            for user_id in user_ids:
                if not isinstance(user_id, str) or not user_id.isdecimal():
                    raise ValueError("Login IDs must be quoted numbers in valid_logins.py.")
                if user_id in self._accounts:
                    raise ValueError(f"Duplicate login ID in valid_logins.py: {user_id}")
                self._accounts[user_id] = role
        self._user = None
        self._failures = 0
        self._locked_until = None

    # PUBLIC INTERFACE: callers use these documented operations.
    # End an expired login lockout and reset the failed-attempt count.
    def tick(self) -> None:
        """Expire the cabinet-wide lockout without depending on HMS availability."""
        if self._locked_until is not None and self._clock() >= self._locked_until:
            self._locked_until = None
            self._failures = 0
            self._logger.logEvent("lockout_cleared", "Login lockout expired.")

    # Look up an ID, create a session if valid, or count the failed login.
    def Authenticate(self, userId: str) -> AuthResult:
        """Authenticate a numeric string ID and return immutable AuthResult.

        Replaces any old session; logs the attempt. Success sets the mapped role
        and resets failures. Failure grants no session and may start lockout.
        Unknown IDs return success=False; startup configuration errors are raised."""
        # Start every attempt without carrying over an earlier user's privileges.
        self.logout(record=False)
        self.tick()
        if self._locked_until is not None:
            # Trying again during lockout neither grants access nor extends its timer.
            reason = "Cabinet login lockout is active."
        else:
            role = None
            if isinstance(userId, str):
                userId = userId.strip()
                role = self._accounts.get(userId)
            if role is not None:
                self._user = User(userId, role)
                self._failures = 0
                self._logger.setUser(userId)
                self._logger.logEvent("authentication", f"Signed in as {role}.", outcome="success")
                return AuthResult(True, self._user, f"Signed in as {role}.")
            # An unknown ID counts toward the next cabinet-wide lockout.
            self._failures += 1
            reason = "ID not recognised. Check your ID and try again."
            if self._failures >= FAILED_LOGIN_LIMIT:
                self._locked_until = self._clock() + self._timings.lockout
                self._logger.logEvent("lockout", "Three consecutive failed login attempts.",
                                      outcome="activated")
                if self._alarm:
                    self._alarm("login_lockout", "Cabinet login lockout activated.")
                reason = "Three failed attempts: cabinet login lockout activated."
        # Do not log arbitrary submitted text: it could contain a badge or secret.
        self._logger.logEvent("authentication", reason, outcome="denied")
        return AuthResult(False, None, reason)

    # Check that this is the current session and its role allows the action.
    def hasPermission(self, user: User | None, operation: str) -> bool:
        """Only the current session object is trusted; stale/forged users fail."""
        self.tick()
        return (user is not None and user is self._user and self._locked_until is None
                and operation in self._permissions.get(user.role, set()))

    # Return the signed-in user's identity, or None when logged out.
    def currentUser(self) -> User | None:
        """Return the immutable current User, or None; no session mutation."""
        return self._user

    # Return how many seconds remain before another login is allowed.
    def lockoutRemaining(self) -> float:
        """Return nonnegative seconds remaining; expire a completed lockout."""
        self.tick()
        if self._locked_until is not None:
            return max(0.0, self._locked_until - self._clock())
        return 0.0

    # Remove the active session and stop attributing new log entries to that user.
    def logout(self, record: bool = True) -> None:
        """Invalidate the current session and clear audit identity.

        record=True logs logout when a session exists. Returns None."""
        if self._user is not None and record:
            self._logger.logEvent("logout", "Session ended.", outcome="success")
        self._user = None
        self._logger.setUser(None)
