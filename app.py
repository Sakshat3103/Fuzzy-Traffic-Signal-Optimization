# app.py
# Streamlit front end.  run with:  streamlit run app.py

import random
import time

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from fuzzy_logic import (compute_green_time, dominant, RULES, GREEN_X,
                         DENSITY_SETS, WAITING_SETS, GREEN_SETS)
from traffic_simulation import (DIRECTIONS, SCENARIOS, DISCHARGE_HEADWAY,
                                generate_arrivals, random_snapshot, run_simulation)
from controller import FixedTimeController, FuzzyController
import visualization as viz

st.set_page_config(page_title="Fuzzy Traffic Signal", layout="wide")


def show(fig):
    st.pyplot(fig)
    plt.close(fig)


def load_samples():
    return pd.read_csv("data/sample_traffic.csv")


# ---------------------------------------------------------------
# sidebar
# ---------------------------------------------------------------
st.sidebar.title("Fuzzy Traffic Signal")
st.sidebar.caption("CSE3121 AISC project")
page = st.sidebar.radio("Go to", ["Dashboard", "Fuzzy Rule Evaluation",
                                  "Fixed vs Fuzzy", "How It Works"])


# ===============================================================
# DASHBOARD
# ===============================================================
if page == "Dashboard":
    st.title("Adaptive Traffic Signal Controller")
    st.write("Green time for each road is decided by a fuzzy inference system "
             "using the number of waiting vehicles and their average waiting time.")

    mode = st.radio("Input mode", ["Manual", "Simulation", "Sample data (CSV)"],
                    horizontal=True)

    traffic = {}
    if mode == "Manual":
        cols = st.columns(4)
        defaults = {"North": (35, 40), "East": (25, 28), "South": (12, 15), "West": (8, 10)}
        for col, d in zip(cols, DIRECTIONS):
            with col:
                st.markdown(f"**{d}**")
                v = st.number_input("vehicles", 0, 60, defaults[d][0], key=f"v_{d}")
                w = st.number_input("avg wait (s)", 0, 120, defaults[d][1], key=f"w_{d}")
                traffic[d] = {"vehicles": int(v), "wait": int(w)}

    elif mode == "Simulation":
        if "snap_seed" not in st.session_state:
            st.session_state.snap_seed = 1
        if st.button("Generate new traffic"):
            st.session_state.snap_seed += 1
        traffic = random_snapshot(random.Random(st.session_state.snap_seed))
        st.caption(f"random traffic state #{st.session_state.snap_seed}")

    else:
        df = load_samples()
        case = st.selectbox("Test case", df["case"].tolist())
        row = df[df["case"] == case].iloc[0]
        st.caption(row["note"])
        for d in DIRECTIONS:
            k = d[0]   # N / E / S / W
            traffic[d] = {"vehicles": int(row[f"{k}_vehicles"]), "wait": int(row[f"{k}_wait"])}

    # run fuzzy system for every road
    results = {d: compute_green_time(traffic[d]["vehicles"], traffic[d]["wait"])
               for d in DIRECTIONS}
    green_times = {d: results[d]["green_time"] for d in DIRECTIONS}

    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("Traffic status")
        table = pd.DataFrame([{
            "Direction": d,
            "Vehicles": traffic[d]["vehicles"],
            "Avg wait (s)": traffic[d]["wait"],
            "Traffic level": dominant(results[d]["density_mu"]),
            "Waiting level": dominant(results[d]["waiting_mu"]),
            "Green time (s)": green_times[d],
        } for d in DIRECTIONS])
        st.dataframe(table, hide_index=True, width="stretch")
        st.caption(f"one full cycle = {sum(green_times.values())}s green "
                   f"+ 12s yellow  (fixed 30s signal = 132s)")

        st.subheader("Fuzzy decision")
        sel = st.selectbox("Direction", DIRECTIONS)
        r = results[sel]
        c1, c2, c3 = st.columns(3)
        c1.metric("Traffic density", dominant(r["density_mu"]))
        c2.metric("Waiting time", dominant(r["waiting_mu"]))
        c3.metric("Final green time", f"{r['green_time']} s")

        fired = [x for x in r["rules"] if x["strength"] > 0]
        for x in fired:
            st.write(f"**R{x['rule']}**: IF density is {x['density']} AND waiting is "
                     f"{x['waiting']} THEN green is {x['green']}  →  "
                     f"min({x['mu_density']:.2f}, {x['mu_waiting']:.2f}) = "
                     f"**{x['strength']:.2f}**")
        st.caption("Full working of each step is on the 'Fuzzy Rule Evaluation' page.")

    with right:
        st.subheader("Junction")
        speed = st.select_slider("Animation speed", ["slow", "normal", "fast"], value="fast")
        delay = {"slow": 0.5, "normal": 0.2, "fast": 0.05}[speed]
        frame = st.empty()
        with frame.container():
            show(viz.draw_intersection(traffic, green_times=green_times))

        if st.button("Run one signal cycle"):
            live = {d: dict(traffic[d]) for d in DIRECTIONS}
            for d in DIRECTIONS:
                g = green_times[d]
                # redraw every 2 seconds (one car leaves per 2 s)
                for left_s in range(g, 0, -DISCHARGE_HEADWAY):
                    if live[d]["vehicles"] > 0:
                        live[d]["vehicles"] -= 1
                    with frame.container():
                        show(viz.draw_intersection(live, d, left_s, green_times))
                    time.sleep(delay)
            with frame.container():
                show(viz.draw_intersection(live, green_times=green_times))
            st.success("Cycle finished. Remaining cars: " +
                       ", ".join(f"{d} {live[d]['vehicles']}" for d in DIRECTIONS))


# ===============================================================
# FUZZY RULE EVALUATION / INSPECTOR
# ===============================================================
elif page == "Fuzzy Rule Evaluation":
    st.title("Fuzzy Rule Evaluation")
    st.write("Move the sliders and every step of the inference is recalculated.")

    c1, c2 = st.columns(2)
    vehicles = c1.slider("Crisp input 1: vehicles in queue", 0, 60, 33)
    wait = c2.slider("Crisp input 2: average waiting time (s)", 0, 120, 62)
    r = compute_green_time(vehicles, wait)

    # step 1
    st.header("1. Fuzzification")
    c1, c2 = st.columns(2)
    with c1:
        show(viz.plot_density_mf(vehicles))
        st.write(", ".join(f"μ_{k}({vehicles}) = {v:.2f}" for k, v in r["density_mu"].items()))
    with c2:
        show(viz.plot_waiting_mf(wait))
        st.write(", ".join(f"μ_{k}({wait}) = {v:.2f}" for k, v in r["waiting_mu"].items()))

    with st.expander("Membership function parameters"):
        rows = []
        for var, sets in [("Density (vehicles)", DENSITY_SETS),
                          ("Waiting (s)", WAITING_SETS), ("Green (s)", GREEN_SETS)]:
            for name, (shape, p) in sets.items():
                rows.append({"Variable": var, "Set": name,
                             "Shape": "triangle" if shape == "tri" else "trapezoid",
                             "Points": str(p)})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    # step 2
    st.header("2. Rule evaluation (AND = min)")
    show_all = st.checkbox("show rules that did not fire", value=False)
    for x in r["rules"]:
        if x["strength"] == 0 and not show_all:
            continue
        text =(f"**Rule {x['rule']}:** IF Traffic = {x['density']} AND Waiting = "
                f"{x['waiting']} THEN Green = {x['green']}  \n"
                f"Traffic membership: {x['mu_density']:.2f}  |  "
                f"Waiting membership: {x['mu_waiting']:.2f}  \n"
                f"Firing strength = min({x['mu_density']:.2f}, {x['mu_waiting']:.2f}) "
                f"= **{x['strength']:.2f}**")
        if x["strength"] > 0:
            st.success(text)
        else:
            st.info(text)

    # step 3/4
    st.header("3. Implication and aggregation")
    st.write("Each output set is cut (clipped) at the strength of its rule. If two "
             "rules point to the same output set, the larger strength is kept (max). "
             "Then the clipped shapes are joined with max.")
    lv = r["output_level"]
    st.write("  |  ".join(f"Green {k}: clipped at **{v:.2f}**" for k, v in lv.items()))
    show(viz.plot_output(r))

    # step 5
    st.header("4. Defuzzification (centroid)")
    num = float((GREEN_X * r["aggregated"]).sum())
    den = float(r["aggregated"].sum())
    st.latex(r"\text{green} = \frac{\sum x\,\mu(x)}{\sum \mu(x)} = "
             rf"\frac{{{num:.2f}}}{{{den:.2f}}} = {r['green_exact']:.2f}\ \text{{s}}")
    st.write(f"Sum taken over {len(GREEN_X)} points from 10 s to 60 s (step 0.1 s). "
             f"Rounded crisp output: **{r['green_time']} seconds**.")

    with st.expander("Control surface (output for every input pair)"):
        show(viz.plot_control_surface())
        st.caption("Smooth change in colour = small change in input gives small change "
                   "in green time, no sudden jumps like an if-else table would give.")


# ===============================================================
# FIXED vs FUZZY
# ===============================================================
elif page == "Fixed vs Fuzzy":
    st.title("Fixed-time signal vs fuzzy signal")
    st.write("Both controllers get exactly the same vehicle arrivals (same random seed).")

    c1, c2, c3, c4 = st.columns(4)
    scen = c1.selectbox("Scenario", list(SCENARIOS))
    duration = c2.slider("Simulation time (s)", 600, 3600, 1800, step=300)
    fixed_g = c3.slider("Fixed green time (s)", 10, 60, 30, step=5)
    seed = c4.number_input("Random seed", 1, 9999, 7)

    rates = SCENARIOS[scen]
    st.caption("Arrival rate (vehicles/min): " +
               ", ".join(f"{d} {rates[d] * 60:.1f}" for d in DIRECTIONS))

    arrivals = generate_arrivals(rates, duration, seed=int(seed))
    fixed = run_simulation(FixedTimeController(fixed_g), arrivals, duration)
    fuzzy = run_simulation(FuzzyController(), arrivals, duration)

    def change(a, b, lower_better=True):
        if a == 0:
            return "-"
        pct = (b - a) / a * 100
        better = pct < 0 if lower_better else pct > 0
        return f"{pct:+.1f}% ({'better' if better else 'worse' if pct != 0 else 'same'})"

    rows = [
        ("Average waiting time (s)", fixed["avg_wait"], fuzzy["avg_wait"], True),
        ("Maximum waiting time (s)", fixed["max_wait"], fuzzy["max_wait"], True),
        ("Average queue length (cars)", fixed["avg_queue"], fuzzy["avg_queue"], True),
        ("Maximum queue length (cars)", fixed["max_queue"], fuzzy["max_queue"], True),
        ("Vehicles served", fixed["served"], fuzzy["served"], False),
        ("Left in queue at end", fixed["left_in_queue"], fuzzy["left_in_queue"], True),
        ("Signal cycles completed", fixed["cycles"], fuzzy["cycles"], None),
    ]
    table = pd.DataFrame([{
        "Metric": m,
        "Fixed": round(a, 1),
        "Fuzzy": round(b, 1),
        "Change": change(a, b, lb) if lb is not None else "-",
    } for m, a, b, lb in rows])
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption(f"Total arrivals: {fixed['arrived']} vehicles in {duration} s. "
               "All numbers above are calculated from this run, change the seed to "
               "check they hold for other random traffic.")

    show(viz.plot_comparison_bars(fixed, fuzzy))
    show(viz.plot_queue_over_time(fixed, fuzzy))

    with st.expander("Green times chosen by the fuzzy controller (first 20 phases)"):
        st.dataframe(pd.DataFrame(fuzzy["phase_log"][:20]), hide_index=True,
                     width="stretch")

    with st.expander("Run all scenarios"):
        out = []
        for name, rt in SCENARIOS.items():
            arr = generate_arrivals(rt, duration, seed=int(seed))
            a = run_simulation(FixedTimeController(fixed_g), arr, duration)
            b = run_simulation(FuzzyController(), arr, duration)
            out.append({"Scenario": name,
                        "Fixed avg wait": round(a["avg_wait"], 1),
                        "Fuzzy avg wait": round(b["avg_wait"], 1),
                        "Fixed served": a["served"], "Fuzzy served": b["served"],
                        "Fixed avg queue": round(a["avg_queue"], 1),
                        "Fuzzy avg queue": round(b["avg_queue"], 1)})
        st.dataframe(pd.DataFrame(out), hide_index=True, width="stretch")


# ===============================================================
# HOW IT WORKS
# ===============================================================
else:
    st.title("How it works")

    st.graphviz_chart("""
    digraph {
        rankdir=TB; node [shape=box, style="rounded,filled", fillcolor="#eef3f8", fontname="Helvetica"];
        a [label="Input traffic data\\n(vehicles, avg waiting time)"];
        b [label="Fuzzification"];
        c [label="Membership values\\nμ_LOW, μ_MEDIUM, μ_HIGH ..."];
        d [label="Evaluate 9 fuzzy rules"];
        e [label="Firing strength = min(μ1, μ2)"];
        f [label="Clip output sets + aggregate with max"];
        g [label="Defuzzification (centroid)"];
        h [label="Crisp green time (10-60 s)"];
        i [label="Signal decision\\n(next road goes green)", fillcolor="#d7f0dc"];
        a -> b -> c -> d -> e -> f -> g -> h -> i;
    }
    """)

    st.subheader("Why fuzzy logic here")
    st.write("""
A normal signal uses the same green time no matter how many cars are waiting.
A simple if-else controller ("if cars > 30 give 50 s") jumps suddenly at the threshold:
29 cars and 31 cars get very different green times. Words like *heavy traffic* or
*waited long* don't have sharp boundaries, so fuzzy sets fit them better. 31 cars is
partly MEDIUM and partly HIGH, and the output changes smoothly.
""")

    st.subheader("Rule base")
    grid = pd.DataFrame(index=["LOW", "MEDIUM", "HIGH"], columns=["SHORT", "MEDIUM", "LONG"])
    for d, w, g in RULES:
        grid.loc[d, w] = g
    grid.index.name = "density \\ waiting"
    st.table(grid)

    st.subheader("Simulation assumptions")
    st.write("""
- 4 approaches, one green at a time, order North → East → South → West
- random arrivals every second (Bernoulli trials, so roughly Poisson)
- one vehicle leaves every 2 s while green, 3 s yellow/all-red between phases
- the fuzzy controller looks at the queue only when that road's turn comes
""")
