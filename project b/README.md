# Hospital Monitoring System — Run Instructions

1. Extract the project ZIP and open the **project b** folder in VS Code.
2. In the terminal, install dependencies and start the app:

```powershell
py -m pip install -r requirements.txt
py app.py --demo
```

3. Open **http://127.0.0.1:5000/login**.

## Demo logins

| Role | Employee ID | PIN |
|---|---|---|
| Nurse | 101 | 1111 |
| Pharmacist | 102 | 2222 |
| Technician | 103 | 3333 |
| Administrator | 104 | 4444 |

## Run demo scenarios

Keep the first terminal running. In a **second terminal**, use:

```powershell
py app.py --run 01_low_inventory
py app.py --run 02_restock_clears_alarm
py app.py --run 03_health_fault
py app.py --run 04_fault_repaired
py app.py --run 05_offline_dispense
py app.py --run 06_reconnect_sync
py app.py --run 07_invalid_inventory
py app.py --run 08_normal_dispense
```

To stop the server, press **Ctrl+C**. If `py` doesn't work, use `python` instead.
