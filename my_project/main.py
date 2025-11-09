# my_project/main.py
from data import buses, drivers, demands, route_hours
from rules import find_feasible_assignment

def sort_demands(ds):
    # Peak first, then higher passengers first, then earlier start time
    return sorted(
        ds,
        key=lambda d: (
            0 if d.get("peak") else 1,
            -d["expected_passengers"],
            d["time_start"]
        )
    )

def run_allocation():
    assignments = []  # each: {route_id, bus_id, driver_id, start, end}
    used_driver_hours = {}  # driver_id -> hours used

    for d in sort_demands(demands):
        res = find_feasible_assignment(d, buses, drivers, assignments, used_driver_hours, route_hours)
        if res is None:
            print(f"[FAIL] Route {d['route_id']} ({d['time_start']}-{d['time_end']}, {d['expected_passengers']} pax) could NOT be assigned.")
            continue

        bus = res["bus"]; drv = res["driver"]
        assignments.append({
            "route_id": d["route_id"],
            "bus_id": bus["id"],
            "driver_id": drv["id"],
            "start": res["start"], "end": res["end"]
        })
        used_driver_hours[drv["id"]] = used_driver_hours.get(drv["id"], 0.0) + res["r_hours"]

        print(f"[OK] Route {d['route_id']} → Bus {bus['id']} | Driver {drv['id']} | {d['time_start']}-{d['time_end']} | pax={d['expected_passengers']}")

    # Summary
    ok = sum(1 for a in assignments)
    total = len(demands)
    print(f"\nSummary: assigned {ok}/{total} route blocks.")
    # Optional: show driver hours used
    if len(used_driver_hours):
        print("Driver hours used:", used_driver_hours)

if __name__ == "__main__":
    run_allocation()
