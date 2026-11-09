import argparse
import hmac
import os
import secrets
import threading
import time
from datetime import datetime, timezone
from functools import wraps
from zoneinfo import ZoneInfo
from cabinet_health import HEARTBEAT_INTERVAL   
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for

from authentication import authenticate, has_permission, role_for
from demo_scenarios import DemoADCs, local_token, run_scenario, send_terminal_request
from monitor import MonitoringSystem
from reporting import detail, generate_report, overview


EASTERN = ZoneInfo("America/Toronto")


def format_dt(value):
    if not value:
        return ""
    try:
        date = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date.astimezone(EASTERN).strftime("%Y-%m-%d %H:%M:%S")


def create_app(db_path=None, start_simulator=False, cli_token=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get("MONITOR_SESSION_SECRET") or secrets.token_hex(32)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        CLI_SCENARIO_TOKEN=cli_token,
    )

    monitor = MonitoringSystem(db_path)
    demo = DemoADCs(monitor)
    demo.seed()
    app.monitor = monitor
    app.demo = demo

    def login_required(permission="view_status"):
        def decorator(page):
            @wraps(page)
            def protected_page(*args, **kwargs):
                employee_id = session.get("employee_id")
                if not employee_id:
                    return redirect(url_for("login"))
                if not has_permission(employee_id, permission):
                    abort(403)
                return page(*args, **kwargs)
            return protected_page
        return decorator

    @app.before_request
    def protect_forms():
        if request.endpoint == "terminal_scenarios":
            return
        if request.method == "POST" and request.form.get("csrf") != session.get("csrf"):
            abort(400, "Invalid form token")

    @app.context_processor
    def template_context():
        return {
            "employee_id": session.get("employee_id"),
            "role": role_for(session.get("employee_id")),
            "can": lambda permission: has_permission(session.get("employee_id"), permission),
            "format_dt": format_dt,
        }

    @app.route("/login", methods=["GET", "POST"])
    def login():
        session.setdefault("csrf", secrets.token_urlsafe(24))
        if request.method == "POST":
            employee_id = request.form.get("employee_id", "")
            pin = request.form.get("pin", "")
            if authenticate(employee_id, pin):
                session.clear()
                session["employee_id"] = employee_id
                session["csrf"] = secrets.token_urlsafe(24)
                return redirect(url_for("home"))
            flash("Invalid employee ID or PIN")
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required()
    def home():
        monitor.check_timeouts()
        return render_template("dashboard.html", cabinets=overview(monitor.store))

    @app.route("/cabinet/<adc_id>")
    @login_required()
    def cabinet(adc_id):
        monitor.check_timeouts()
        info = detail(monitor.store, adc_id)
        if info is None:
            abort(404)
        return render_template("cabinet.html", **info)

    @app.route("/report")
    @login_required("view_reports")
    def report():
        return render_template("report.html", records=generate_report(monitor.store))

    @app.route("/ack/<adc_id>/<alarm_id>", methods=["POST"])
    @login_required("acknowledge_system_alarm")
    def acknowledge(adc_id, alarm_id):
        if monitor.acknowledge(adc_id, alarm_id, session["employee_id"]):
            flash("Alarm acknowledged. It will clear when the ADC reports resolution.")
        else:
            flash("Alarm could not be acknowledged (wrong category or already acknowledged/resolved).")
        return redirect(url_for("cabinet", adc_id=adc_id))

    @app.route("/_local/scenarios", methods=["POST"])
    def terminal_scenarios():
        token = app.config.get("CLI_SCENARIO_TOKEN")
        supplied = request.headers.get("X-Scenario-Token", "")
        if (
            request.remote_addr not in ("127.0.0.1", "::1")
            or not token
            or not hmac.compare_digest(token, supplied)
        ):
            abort(403)

        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {"name"} or not isinstance(data["name"], str):
            return jsonify({"error": "Expected JSON with scenario name"}), 400

        try:
            result = run_scenario(data["name"], demo, monitor)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        return jsonify({
            "result": result,
            "cabinet": monitor.store.cabinet(result["adc_id"]),
            "inventory": monitor.store.inventory(result["adc_id"]),
        })

    if start_simulator:
        def send_heartbeats():
            while True:
                time.sleep(HEARTBEAT_INTERVAL)
                demo.tick()

        threading.Thread(target=send_heartbeats, daemon=True).start()

    return app


def main():
    parser = argparse.ArgumentParser(description="Hospital Monitoring System")
    parser.add_argument("--run", metavar="NAME", help="Run a JSON scenario")
    parser.add_argument("--demo", action="store_true", help="Start the web dashboard")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    if args.demo and args.run:
        parser.error("Use --demo or --run, not both")

    if args.run:
        try:
            result = send_terminal_request(args.port, args.run)
        except RuntimeError as error:
            parser.exit(1, f"Error: {error}\n")

        info = result["result"]
        cabinet = result["cabinet"]
        print(f"Ran: {info['name']} ({info['steps']} steps) on {info['adc_id']}")
        print(f"Cabinet: {cabinet['connection']} / {cabinet['health']}")
        print("Inventory: " + ", ".join(
            f"{item['medication']}={item['quantity']}" for item in result["inventory"]
        ))
        for note in info["notes"]:
            print(note)
        print(f"View: http://127.0.0.1:{args.port}/cabinet/{info['adc_id']}")
        return

    print(f"Local dashboard: http://127.0.0.1:{args.port}/login")
    create_app(start_simulator=True, cli_token=local_token(create=True)).run(
        host="127.0.0.1", port=args.port, debug=False, use_reloader=False
    )


if __name__ == "__main__":
    main()
