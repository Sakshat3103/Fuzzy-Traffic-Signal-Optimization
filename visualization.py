# visualization.py
# All the matplotlib drawing: junction, membership graphs, output graph,
# comparison charts. Kept separate so app.py stays readable.

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import numpy as np

from fuzzy_logic import (DENSITY_SETS, WAITING_SETS, GREEN_SETS, DENSITY_RANGE,
                         WAITING_RANGE, GREEN_RANGE, GREEN_X, membership)

SET_COLORS = ["#4C9BE8", "#F2A541", "#E2565B"]   # low / medium / high
ROAD = "#555b61"
GRASS = "#cfe3c3"


# ---------------------------------------------------------------
# junction drawing
# ---------------------------------------------------------------

def draw_intersection(traffic, green_dir=None, countdown=None, green_times=None):
    """
    traffic     : {direction: {"vehicles": n, "wait": s}}
    green_dir   : which direction is green right now (others red)
    countdown   : seconds left, shown in the middle
    green_times : {direction: seconds} shown next to each light
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(Rectangle((0, 0), 100, 100, color=GRASS))
    ax.add_patch(Rectangle((40, 0), 20, 100, color=ROAD))   # N-S road
    ax.add_patch(Rectangle((0, 40), 100, 20, color=ROAD))   # E-W road

    # dashed centre lines (stop before the box)
    for seg in [((50, 50), (0, 38)), ((50, 50), (62, 100))]:
        ax.plot(*seg, color="white", ls="--", lw=1)
    for seg in [((0, 38), (50, 50)), ((62, 100), (50, 50))]:
        ax.plot(*seg, color="white", ls="--", lw=1)

    # each approach: where cars queue, which way the queue grows, light position
    # (left-hand traffic like in India, so e.g. cars coming from North queue
    #  on the east half of the north road)
    layout = {
        "North": {"start": (52.6, 63), "step": (0, 4.2), "car": (3.4, 3), "light": (64, 64), "label": (50, 97)},
        "South": {"start": (44, 34), "step": (0, -4.2), "car": (3.4, 3), "light": (36, 36), "label": (50, 3)},
        "East":  {"start": (63, 44), "step": (4.2, 0), "car": (3, 3.4), "light": (64, 36), "label": (90, 30)},
        "West":  {"start": (34, 52.6), "step": (-4.2, 0), "car": (3, 3.4), "light": (36, 64), "label": (10, 70)},
    }

    for d, cfg in layout.items():
        n = traffic[d]["vehicles"]
        shown = min(n, 8)        # only 8 fit on screen
        for i in range(shown):
            x = cfg["start"][0] + cfg["step"][0] * i
            y = cfg["start"][1] + cfg["step"][1] * i
            ax.add_patch(Rectangle((x, y), *cfg["car"], color="#2b2d42", ec="white", lw=0.5))

        is_green = (d == green_dir)
        lx, ly = cfg["light"]
        ax.add_patch(Rectangle((lx - 2.5, ly - 2.5), 5, 5, color="#222", zorder=3))
        ax.add_patch(Circle((lx, ly), 1.8, zorder=4,
                            color="#2ecc40" if is_green else "#ff4136"))

        text = f"{d}\n{n} cars"
        if green_times:
            text += f"\ngreen {green_times[d]}s"
        ax.text(*cfg["label"], text, ha="center", va="center", fontsize=8.5,
                bbox=dict(boxstyle="round", fc="white", ec="#999", alpha=0.9))

    if green_dir is not None:
        msg = f"{green_dir.upper()}\nGREEN"
        if countdown is not None:
            msg += f"\n{countdown}s"
        ax.text(50, 50, msg, ha="center", va="center", fontsize=10,
                color="white", fontweight="bold")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------
# membership function graphs
# ---------------------------------------------------------------

def plot_input_mf(sets, value_range, current_value, title, xlabel):
    xs = np.linspace(value_range[0], value_range[1], 400)
    fig, ax = plt.subplots(figsize=(6, 2.8))
    for (name, s), c in zip(sets.items(), SET_COLORS):
        ax.plot(xs, [membership(x, s) for x in xs], color=c, lw=2, label=name)

    if current_value is not None:
        v = max(value_range[0], min(value_range[1], current_value))
        ax.axvline(v, color="black", ls="--", lw=1)
        for (name, s), c in zip(sets.items(), SET_COLORS):
            mu = membership(v, s)
            if mu > 0:
                ax.plot(v, mu, "o", color=c)
                ax.annotate(f"{mu:.2f}", (v, mu), textcoords="offset points",
                            xytext=(6, 4), fontsize=8, color=c)

    ax.set_ylim(-0.05, 1.4)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("membership μ")
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8, loc="upper right", ncol=3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_output(result=None):
    """output sets; if a result is given also shows the clipped areas,
    aggregated shape and the centroid line"""
    fig, ax = plt.subplots(figsize=(6, 2.8))
    for (name, s), c in zip(GREEN_SETS.items(), SET_COLORS):
        ys = [membership(x, s) for x in GREEN_X]
        ax.plot(GREEN_X, ys, color=c, lw=1.2, ls=":" if result else "-", label=name)
        if result is not None:
            ax.fill_between(GREEN_X, result["clipped"][name], color=c, alpha=0.35)

    if result is not None:
        ax.plot(GREEN_X, result["aggregated"], color="black", lw=1.6, label="aggregated")
        g = result["green_exact"]
        ax.axvline(g, color="purple", lw=2)
        ax.text(g + 0.6, 0.72, f"centroid\n= {g:.2f}s", color="purple", fontsize=8)

    ax.set_xlim(*GREEN_RANGE)
    ax.set_ylim(-0.05, 1.4)
    ax.set_xlabel("green time (seconds)")
    ax.set_ylabel("membership μ")
    ax.set_title("Output: green duration", fontsize=10)
    ax.legend(fontsize=8, loc="upper left", ncol=4)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_density_mf(value=None):
    return plot_input_mf(DENSITY_SETS, DENSITY_RANGE, value,
                         "Input 1: traffic density", "vehicles in queue")


def plot_waiting_mf(value=None):
    return plot_input_mf(WAITING_SETS, WAITING_RANGE, value,
                         "Input 2: average waiting time", "seconds")


def plot_control_surface():
    """green time for every (vehicles, wait) pair - shows the whole system at once"""
    from fuzzy_logic import compute_green_time
    v = np.arange(0, 61, 3)
    w = np.arange(0, 121, 6)
    Z = np.array([[compute_green_time(a, b)["green_exact"] for a in v] for b in w])
    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.contourf(v, w, Z, levels=15, cmap="RdYlGn_r")
    fig.colorbar(im, ax=ax, label="green time (s)")
    ax.set_xlabel("vehicles in queue")
    ax.set_ylabel("average waiting time (s)")
    ax.set_title("Control surface", fontsize=10)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------
# comparison charts
# ---------------------------------------------------------------

def plot_comparison_bars(fixed, fuzzy):
    metrics = [("avg_wait", "Avg waiting (s)"), ("max_wait", "Max waiting (s)"),
               ("avg_queue", "Avg queue (cars)"), ("served", "Vehicles served")]
    fig, axes = plt.subplots(1, 4, figsize=(11, 2.8))
    for ax, (key, label) in zip(axes, metrics):
        vals = [fixed[key], fuzzy[key]]
        bars = ax.bar(["Fixed", "Fuzzy"], vals, color=["#9aa5b1", "#3d9970"])
        for b, val in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                    f"{val:.1f}" if isinstance(val, float) else str(val),
                    ha="center", va="bottom", fontsize=8)
        ax.set_title(label, fontsize=9)
        ax.set_ylim(0, max(vals) * 1.2 + 1)
        ax.tick_params(labelsize=8)
    fig.tight_layout()
    return fig


def plot_queue_over_time(fixed, fuzzy):
    fig, ax = plt.subplots(figsize=(11, 3))
    for res, c in [(fixed, "#9aa5b1"), (fuzzy, "#3d9970")]:
        t, q = zip(*res["queue_trace"])
        ax.plot(t, q, color=c, lw=1.2, label=res["controller"])
    ax.set_xlabel("time (s)")
    ax.set_ylabel("total cars waiting")
    ax.set_title("Total queue at the junction over time", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig
