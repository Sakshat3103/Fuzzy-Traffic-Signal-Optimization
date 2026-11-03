# traffic_simulation.py
# Simple 1-second-step simulation of a 4-way junction.
#
# Assumptions (kept simple on purpose):
#   - one queue per approach (N, E, S, W), only one approach green at a time
#   - vehicles arrive randomly (Bernoulli trial every second = approx Poisson)
#   - while green, one vehicle leaves every 2 sec (saturation flow 0.5 veh/s)
#   - 3 sec yellow + all-red between phases, nobody moves during it
#   - phase order N -> E -> S -> W -> N ...
#
# Same arrival list is given to both controllers so the comparison is fair.

import random

DIRECTIONS = ["North", "East", "South", "West"]
DISCHARGE_HEADWAY = 2      # seconds per vehicle while green
YELLOW_TIME = 3            # lost time between phases

# arrival rate in vehicles / second for each direction
SCENARIOS = {
    "Balanced (moderate)": {"North": 0.08, "East": 0.08, "South": 0.08, "West": 0.08},
    "Peak hour (N-S heavy)": {"North": 0.15, "East": 0.04, "South": 0.13, "West": 0.03},
    "One road congested": {"North": 0.05, "East": 0.17, "South": 0.04, "West": 0.05},
    "Light traffic (night)": {"North": 0.03, "East": 0.02, "South": 0.03, "West": 0.02},
}


def generate_arrivals(rates, duration, seed=7):
    """list of arrival times (sec) for every direction"""
    rng = random.Random(seed)
    arrivals = {d: [] for d in DIRECTIONS}
    for t in range(duration):
        for d in DIRECTIONS:
            if rng.random() < rates[d]:
                arrivals[d].append(t)
    return arrivals


def random_snapshot(rng=None):
    """random traffic state for the 'simulation mode' on the dashboard"""
    rng = rng or random
    snap = {}
    for d in DIRECTIONS:
        vehicles = rng.randint(0, 55)
        # more cars usually means they have waited longer, plus some noise
        wait = int(min(120, max(0, vehicles * 1.6 + rng.randint(-15, 25))))
        snap[d] = {"vehicles": vehicles, "wait": wait}
    return snap


def run_simulation(controller, arrivals, duration):
    """
    controller : object with get_green_time(direction, queue_len, avg_wait)
    arrivals   : output of generate_arrivals()
    duration   : seconds to simulate (vehicles still queued at the end are
                 counted in the final queue, not in served)
    """
    pending = {d: list(arrivals[d]) for d in DIRECTIONS}   # not yet arrived
    queues = {d: [] for d in DIRECTIONS}                   # arrival times of cars waiting

    waits = []                 # waiting time of every served vehicle
    queue_trace = []           # (time, total queue) for the chart
    phase_log = []             # what the controller decided each phase

    t = 0
    phase = 0

    def tick():
        # one second passes: new cars join their queue
        nonlocal t
        for d in DIRECTIONS:
            while pending[d] and pending[d][0] <= t:
                queues[d].append(pending[d].pop(0))
        queue_trace.append((t, sum(len(q) for q in queues.values())))
        t += 1

    while t < duration:
        d = DIRECTIONS[phase % 4]
        # bring queues up to date before the controller looks at them
        for x in DIRECTIONS:
            while pending[x] and pending[x][0] <= t:
                queues[x].append(pending[x].pop(0))

        q = queues[d]
        avg_wait = (sum(t - a for a in q) / len(q)) if q else 0.0
        green = controller.get_green_time(d, len(q), avg_wait)
        phase_log.append({"time": t, "direction": d, "queue": len(q),
                          "avg_wait": round(avg_wait, 1), "green": green})

        # green period
        for s in range(green):
            if t >= duration:
                break
            if s % DISCHARGE_HEADWAY == 0 and queues[d]:
                arrived = queues[d].pop(0)
                waits.append(t - arrived)
            tick()

        # yellow / all-red
        for _ in range(YELLOW_TIME):
            if t >= duration:
                break
            tick()

        phase += 1

    left_in_queue = sum(len(q) for q in queues.values())
    left_waits = [duration - a for q in queues.values() for a in q]

    total_vehicles = sum(len(a) for a in arrivals.values())
    return {
        "controller": controller.name,
        "served": len(waits),
        "arrived": total_vehicles,
        "left_in_queue": left_in_queue,
        "avg_wait": sum(waits) / len(waits) if waits else 0.0,
        # max includes cars still stuck at the end, otherwise a bad
        # controller could look good by never serving them
        "max_wait": max(waits + left_waits) if (waits or left_waits) else 0,
        "avg_queue": sum(q for _, q in queue_trace) / len(queue_trace),
        "max_queue": max(q for _, q in queue_trace),
        "cycles": phase / 4,
        "sim_time": duration,
        "queue_trace": queue_trace,
        "phase_log": phase_log,
    }
