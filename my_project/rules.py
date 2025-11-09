# my_project/rules.py
from math import sqrt

def _distance(p1, p2):
    return sqrt((p1["lat"] - p2["lat"])**2 + (p1["lon"] - p2["lon"])**2)

def assign_students_to_bus(buses, students, school=None, strategy="round_robin"):
    """
    Distributes students to buses using a simple rule-based strategy.
    - strategy="round_robin": cycle through buses so distribution looks balanced
    - strategy="nearest_first": sort by distance to school, then fill buses
    """
    if not students or not buses:
        return {bus["id"]: [] for bus in buses}

    # default school center (Delhi) if not provided
    if school is None:
        school = {"lat": 28.7041, "lon": 77.1025}

    allocations = {bus["id"]: [] for bus in buses}

    # sort once for deterministic behavior
    students_sorted = sorted(students, key=lambda s: _distance(s, school))

    if strategy == "nearest_first":
        # fill bus by bus using nearest students
        idx = 0
        for bus in buses:
            cap = int(bus.get("capacity", 20))
            while len(allocations[bus["id"]]) < cap and idx < len(students_sorted):
                allocations[bus["id"]].append(students_sorted[idx])
                idx += 1
        return allocations

    # round-robin distribution across buses (balanced)
    bus_idx = 0
    total_buses = len(buses)
    caps = {bus["id"]: int(bus.get("capacity", 20)) for bus in buses}

    for s in students_sorted:
        # try at most `total_buses` times to find a bus with space
        tried = 0
        placed = False
        while tried < total_buses and not placed:
            bus = buses[bus_idx]
            bid = bus["id"]
            if len(allocations[bid]) < caps[bid]:
                allocations[bid].append(s)
                placed = True
            bus_idx = (bus_idx + 1) % total_buses
            tried += 1
        # if no bus had capacity, student remains unassigned (ignored here)
    return allocations
