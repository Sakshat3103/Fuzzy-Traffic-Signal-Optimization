# fuzzy_logic.py
# Mamdani fuzzy inference system for deciding green signal time.
# Written without any fuzzy library (no scikit-fuzzy) - only numpy for the
# output universe array.
#
# Inputs : traffic density (no. of vehicles in queue), waiting time (sec)
# Output : green time (sec), between 10 and 60
#
# Steps followed (same order as in class):
#   1. fuzzification
#   2. rule evaluation (AND = min)
#   3. implication (clip output set at firing strength = min)
#   4. aggregation (OR = max)
#   5. defuzzification (centroid)

import numpy as np


# ---------------------------------------------------------------
# membership functions
# ---------------------------------------------------------------

def triangle(x, a, b, c):
    """triangular MF. a = left foot, b = peak, c = right foot"""
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)


def trapezoid(x, a, b, c, d):
    """trapezoidal MF. flat top from b to c.
    if a == b the left side is a vertical edge (used for the first set),
    same for c == d on the right (used for the last set)"""
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (d - x) / (d - c)


# ---------------------------------------------------------------
# fuzzy sets for each variable
# format -> name: (shape, parameters)
# values were picked by trial on the simulation, see report section 9
# ---------------------------------------------------------------

DENSITY_RANGE = (0, 60)      # vehicles waiting in one lane
WAITING_RANGE = (0, 120)     # average waiting time in seconds
GREEN_RANGE = (10, 60)       # green time in seconds

DENSITY_SETS = {
    "LOW":    ("trap", (0, 0, 8, 20)),
    "MEDIUM": ("tri",  (12, 25, 38)),
    "HIGH":   ("trap", (30, 42, 60, 60)),
}

WAITING_SETS = {
    "SHORT":  ("trap", (0, 0, 15, 35)),
    "MEDIUM": ("tri",  (20, 45, 70)),
    "LONG":   ("trap", (55, 80, 120, 120)),
}

GREEN_SETS = {
    "SHORT":  ("trap", (10, 10, 14, 24)),
    "MEDIUM": ("tri",  (18, 30, 42)),
    "LONG":   ("trap", (36, 48, 60, 60)),
}


def membership(x, fuzzy_set):
    shape, params = fuzzy_set
    if shape == "tri":
        return triangle(x, *params)
    return trapezoid(x, *params)


def clamp(x, low, high):
    # inputs outside the universe are treated as the edge value
    return max(low, min(high, x))


# ---------------------------------------------------------------
# rule base
# 3 density sets x 3 waiting sets = 9 rules, every combination covered
# ---------------------------------------------------------------

RULES = [
    # (density,  waiting,  green)
    ("LOW",    "SHORT",  "SHORT"),    # R1  nobody there, nobody waiting
    ("LOW",    "MEDIUM", "SHORT"),    # R2  few cars, quick clear
    ("LOW",    "LONG",   "MEDIUM"),   # R3  few cars but they waited long
    ("MEDIUM", "SHORT",  "MEDIUM"),   # R4
    ("MEDIUM", "MEDIUM", "MEDIUM"),   # R5
    ("MEDIUM", "LONG",   "LONG"),     # R6
    ("HIGH",   "SHORT",  "MEDIUM"),   # R7  long queue but just arrived
    ("HIGH",   "MEDIUM", "LONG"),     # R8
    ("HIGH",   "LONG",   "LONG"),     # R9  worst case
]


# ---------------------------------------------------------------
# step 1 : fuzzification
# ---------------------------------------------------------------

def fuzzify(value, sets, value_range):
    value = clamp(value, *value_range)
    return {name: round(membership(value, s), 4) for name, s in sets.items()}


# ---------------------------------------------------------------
# step 2 : rule evaluation
# ---------------------------------------------------------------

def evaluate_rules(density_mu, waiting_mu):
    fired = []
    for i, (d, w, g) in enumerate(RULES, start=1):
        strength = min(density_mu[d], waiting_mu[w])   # AND = min
        fired.append({
            "rule": i,
            "density": d,
            "waiting": w,
            "green": g,
            "mu_density": density_mu[d],
            "mu_waiting": waiting_mu[w],
            "strength": strength,
        })
    return fired


# ---------------------------------------------------------------
# steps 3 + 4 : implication and aggregation
# ---------------------------------------------------------------

# output universe, 0.1 sec resolution
GREEN_X = np.linspace(GREEN_RANGE[0], GREEN_RANGE[1], 501)


def output_curve(set_name):
    s = GREEN_SETS[set_name]
    return np.array([membership(x, s) for x in GREEN_X])


# precompute the three output shapes once, they never change
OUTPUT_CURVES = {name: output_curve(name) for name in GREEN_SETS}


def aggregate(fired_rules):
    # strongest strength per output set
    # (if 2 rules give the same consequent we take max of them = OR)
    level = {name: 0.0 for name in GREEN_SETS}
    for r in fired_rules:
        level[r["green"]] = max(level[r["green"]], r["strength"])

    # clip each output set at its level (min), then combine with max
    clipped = {name: np.minimum(OUTPUT_CURVES[name], level[name])
               for name in GREEN_SETS}
    aggregated = np.zeros_like(GREEN_X)
    for curve in clipped.values():
        aggregated = np.maximum(aggregated, curve)
    return level, clipped, aggregated


# ---------------------------------------------------------------
# step 5 : defuzzification (centroid / centre of area)
#   green = sum(x * mu(x)) / sum(mu(x))
# ---------------------------------------------------------------

def centroid(x, mu):
    area = np.sum(mu)
    if area == 0:
        # can't happen with full rule coverage, but just in case
        return GREEN_RANGE[0]
    return float(np.sum(x * mu) / area)


# ---------------------------------------------------------------
# full pipeline
# ---------------------------------------------------------------

def compute_green_time(vehicles, avg_wait):
    """returns the crisp green time plus everything calculated on the way,
    so the UI can show each step"""
    density_mu = fuzzify(vehicles, DENSITY_SETS, DENSITY_RANGE)
    waiting_mu = fuzzify(avg_wait, WAITING_SETS, WAITING_RANGE)
    fired = evaluate_rules(density_mu, waiting_mu)
    level, clipped, aggregated = aggregate(fired)
    green = centroid(GREEN_X, aggregated)

    return {
        "vehicles": vehicles,
        "avg_wait": avg_wait,
        "density_mu": density_mu,
        "waiting_mu": waiting_mu,
        "rules": fired,
        "output_level": level,
        "clipped": clipped,
        "aggregated": aggregated,
        "green_exact": green,
        "green_time": int(round(green)),   # signal works in whole seconds
    }


def dominant(mu_dict):
    # label with highest membership, used for the "traffic level" column
    return max(mu_dict, key=mu_dict.get)


if __name__ == "__main__":
    # quick check from terminal: python fuzzy_logic.py
    for v, w in [(5, 10), (25, 45), (45, 90), (45, 10), (8, 100)]:
        r = compute_green_time(v, w)
        print(f"vehicles={v:>3}  wait={w:>3}s  ->  green = {r['green_exact']:.2f}s")
        for rule in r["rules"]:
            if rule["strength"] > 0:
                print(f"     R{rule['rule']}: min({rule['mu_density']}, "
                      f"{rule['mu_waiting']}) = {rule['strength']}  -> {rule['green']}")
