"""Own ID lookup, the current session, role permissions and cabinet-wide lockout.

PUBLIC INTERFACE: AccessControl; immutable User and AuthResult values.
Invalid login returns AuthResult(False, None, reason); invalid startup IDs raise
ValueError. Permission and remaining-time queries also expire a finished lockout."""

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
    def __init__(self, logger: EventLogger, clock: Callable = time.monotonic,
                 timings: Timings = TIMINGS, alarm: Callable = None):
        self._logger = logger
        self._clock = clock
        self._timings = timings
        self._alarm = alarm
        self._permissions = {
            "Nurse": {"dispense", "catalog", "inventory"},
            "Pharmacist": {"replenish", "register", "catalog", "inventory", "history"},
            "Technician": {"fix", "maintenance", "faults", "logs", "catalog", "inventory", "traffic", "close_drawer"},
            "Tester": {"dispense", "replenish", "register", "catalog", "inventory", "history",
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

    def tick(self) -> None:
        """Expire the cabinet-wide lockout without depending on HMS availability."""
        if self._locked_until is not None and self._clock() >= self._locked_until:
            self._locked_until = None
            self._failures = 0
            self._logger.logEvent("lockout_cleared", "Login lockout expired.")

    def Authenticate(self, userId: str) -> AuthResult:
        """Replace the session, audit the attempt and return an immutable result.

        Unknown IDs count toward lockout; attempts during lockout do not extend it.
        Submitted invalid IDs are never included in the audit.
        """
        # Start every attempt without carrying over an earlier user's privileges.
        self.logout(record=False)
        self.tick()
        if self._locked_until is not None:
            reason = "Cabinet login lockout is active."
            self._logger.logEvent("authentication", reason, outcome="denied")
            return AuthResult(False, None, reason)

        role = None
        if isinstance(userId, str):
            userId = userId.strip()
            role = self._accounts.get(userId)
        if role is not None:
            self._user = User(userId, role)
            self._failures = 0
            self._logger.setUser(userId)
            reason = f"Signed in as {role}."
            self._logger.logEvent("authentication", reason, outcome="success")
            return AuthResult(True, self._user, reason)

        self._failures += 1
        reason = "ID not recognised. Check your ID and try again."
        if self._failures >= FAILED_LOGIN_LIMIT:
            self._locked_until = self._clock() + self._timings.lockout
            self._logger.logEvent("lockout", "Three consecutive failed login attempts.",
                                  outcome="activated")
            if self._alarm:
                self._alarm("login_lockout", "Cabinet login lockout activated.")
            reason = "Three failed attempts: cabinet login lockout activated."
        self._logger.logEvent("authentication", reason, outcome="denied")
        return AuthResult(False, None, reason)

    def hasPermission(self, user: User | None, operation: str) -> bool:
        """Expire lockout, then check this exact session; stale/forged users fail."""
        self.tick()
        return (user is not None and user is self._user and self._locked_until is None
                and operation in self._permissions.get(user.role, set()))

    def currentUser(self) -> User | None:
        """Return the immutable current User, or None; no session mutation."""
        return self._user

    def lockoutRemaining(self) -> float:
        """Return nonnegative seconds remaining; expire a completed lockout."""
        self.tick()
        if self._locked_until is not None:
            return max(0.0, self._locked_until - self._clock())
        return 0.0

    def logout(self, record: bool = True) -> None:
        """Invalidate the current session and clear audit identity.

        record=True logs logout when a session exists. Returns None."""
        if self._user is not None and record:
            self._logger.logEvent("logout", "Session ended.", outcome="success")
        self._user = None
        self._logger.setUser(None)
