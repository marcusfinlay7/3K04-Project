
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class Storage:

    # Database setup

    def __init__(self, path=None):
        self.path = str(path or os.environ.get("MONITOR_DB") or Path(__file__).parent / "data" / "monitoring.db")
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def initialize(self):
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS cabinets (
                    adc_id TEXT PRIMARY KEY,
                    connection TEXT NOT NULL DEFAULT 'UNKNOWN',
                    health TEXT NOT NULL DEFAULT 'UNKNOWN',
                    last_seen TEXT,
                    needs_sync INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS inventory (
                    adc_id TEXT NOT NULL,
                    medication TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0),
                    low_stock INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(adc_id, medication),
                    FOREIGN KEY(adc_id) REFERENCES cabinets(adc_id)
                );
                CREATE TABLE IF NOT EXISTS alarms (
                    adc_id TEXT NOT NULL,
                    alarm_id TEXT NOT NULL,
                    category TEXT NOT NULL CHECK(category IN ('informational','system')),
                    description TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    occurred_at TEXT NOT NULL,
                    acknowledged_by TEXT,
                    acknowledged_at TEXT,
                    resolved_at TEXT,
                    PRIMARY KEY(adc_id, alarm_id),
                    FOREIGN KEY(adc_id) REFERENCES cabinets(adc_id)
                );
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adc_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    medication TEXT,
                    quantity INTEGER,
                    employee_id TEXT,
                    occurred_at TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    UNIQUE(adc_id, event_id),
                    FOREIGN KEY(adc_id) REFERENCES cabinets(adc_id)
                );
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adc_id TEXT, reason TEXT NOT NULL,
                    logged_at TEXT NOT NULL
                );
            """)

    # Cabinet status

    def ensure_cabinet(self, adc_id):
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO cabinets(adc_id) VALUES (?)", (adc_id,))

    def cabinet(self, adc_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM cabinets WHERE adc_id=?", (adc_id,)).fetchone()
            return dict(row) if row else None

    def cabinets(self):
        with self.connect() as db:
            rows = db.execute("""SELECT c.*, (SELECT COUNT(*) FROM alarms a WHERE a.adc_id=c.adc_id AND a.active=1) AS active_alarms,
                        (SELECT COUNT(*) FROM inventory i WHERE i.adc_id=c.adc_id AND i.low_stock=1) AS low_items
                        FROM cabinets c ORDER BY c.adc_id""").fetchall()
            return [dict(r) for r in rows]

    def update_cabinet(self, adc_id, *, connection=None, health=None, last_seen=None, needs_sync=None):
        self.ensure_cabinet(adc_id)
        changes = {k: v for k, v in dict(connection=connection, health=health,
                      last_seen=last_seen, needs_sync=needs_sync).items() if v is not None}
        if not changes:
            return
        with self.connect() as db:
            cols = ", ".join(f"{k}=?" for k in changes)
            db.execute(f"UPDATE cabinets SET {cols} WHERE adc_id=?", (*changes.values(), adc_id))

    # Medication inventory

    def inventory(self, adc_id):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM inventory WHERE adc_id=? ORDER BY medication", (adc_id,))]

    def set_inventory(self, adc_id, medication, quantity, low_stock, occurred_at):
        self.ensure_cabinet(adc_id)
        with self.connect() as db:
            previous = db.execute("SELECT updated_at FROM inventory WHERE adc_id=? AND medication=?",
                                  (adc_id, medication)).fetchone()
            if previous and previous["updated_at"] > occurred_at:
                return False  # Ignore older snapshots after outage replay.
            db.execute("""INSERT INTO inventory(adc_id,medication,quantity,low_stock,updated_at)
                VALUES (?,?,?,?,?) ON CONFLICT(adc_id,medication) DO UPDATE SET
                quantity=excluded.quantity,low_stock=excluded.low_stock,updated_at=excluded.updated_at""",
                (adc_id,medication,quantity,int(low_stock),occurred_at))
            return True

    # Alarm records

    def get_alarm(self, adc_id, alarm_id):
        with self.connect() as db:
            r = db.execute("SELECT * FROM alarms WHERE adc_id=? AND alarm_id=?",
                           (adc_id, alarm_id)).fetchone()
            return dict(r) if r else None

    def alarms(self, adc_id=None, active_only=False):
        sql = "SELECT * FROM alarms WHERE 1=1"
        params = []
        if adc_id:
            sql += " AND adc_id=?"
            params.append(adc_id)
        if active_only:
            sql += " AND active=1"
        sql += " ORDER BY occurred_at DESC"
        with self.connect() as db:
            return [dict(row) for row in db.execute(sql, params)]

    def open_alarm(self, adc_id, alarm_id, category, description, when):
        self.ensure_cabinet(adc_id)
        with self.connect() as db:
            db.execute("""INSERT INTO alarms(adc_id,alarm_id,category,description,occurred_at)
                    VALUES (?,?,?,?,?) ON CONFLICT(adc_id,alarm_id) DO UPDATE SET
                    category=excluded.category, description=excluded.description,
                    occurred_at=excluded.occurred_at, active=1,
                    acknowledged_by=NULL,acknowledged_at=NULL,resolved_at=NULL
                    WHERE alarms.active=0 AND excluded.occurred_at > COALESCE(alarms.resolved_at, alarms.occurred_at)""", (adc_id,alarm_id,category,description,when))

    def resolve_alarm(self, adc_id, alarm_id, when):
        with self.connect() as db:
            cur = db.execute("UPDATE alarms SET active=0,resolved_at=? WHERE adc_id=? AND alarm_id=? AND active=1 AND occurred_at<=?",
                             (when,adc_id,alarm_id,when))
            return cur.rowcount > 0

    def acknowledge_alarm(self, adc_id, alarm_id, employee_id, when):
        with self.connect() as db:
            cur = db.execute("""UPDATE alarms SET acknowledged_by=?,acknowledged_at=?
                WHERE adc_id=? AND alarm_id=? AND active=1 AND category='system' AND acknowledged_at IS NULL""",
                (employee_id,when,adc_id,alarm_id))
            return cur.rowcount > 0

    # Historical events

    def add_event(self, adc_id, event_id, event_type, description, occurred_at,
                  medication=None, quantity=None, employee_id=None):
        """Return False for duplicate event_id (safe for replay)."""
        self.ensure_cabinet(adc_id)
        with self.connect() as db:
            cur = db.execute("""INSERT OR IGNORE INTO history
                (adc_id,event_id,event_type,description,medication,quantity,employee_id,occurred_at,received_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (adc_id,event_id,event_type,description,medication,quantity,employee_id,occurred_at,utc_now()))
            return cur.rowcount == 1

    def history(self, adc_id=None, limit=200):
        # Hide heartbeat rows from older databases too.
        sql = "SELECT * FROM history WHERE event_type != 'heartbeat'"
        params = []
        if adc_id:
            sql += " AND adc_id=?"
            params.append(adc_id)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self.connect() as db:
            return [dict(row) for row in db.execute(sql, params)]

    # Invalid-message logs

    def log_error(self, reason, adc_id=None):
        with self.connect() as db:
            db.execute("INSERT INTO errors(adc_id,reason,logged_at) VALUES (?,?,?)",
                       (adc_id,reason,utc_now()))

    def errors(self, limit=50):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM errors ORDER BY id DESC LIMIT ?", (limit,))]
