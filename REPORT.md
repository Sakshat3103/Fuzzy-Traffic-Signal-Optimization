# Adaptive Traffic Signal Controller Using Fuzzy Logic

**Course:** CSE3121 Artificial Intelligence and Soft Computing
**Semester:** V, July-Nov 2026, Department of CSE, Manipal University Jaipur
**Submitted by:** Sakshat Jain (2427030801)

---

## 1. Abstract

Fixed-time traffic signals give every road the same green time regardless of how many
vehicles are waiting. This project builds a fuzzy logic controller that decides the
green time for each approach of a 4-way junction from two inputs: the number of waiting
vehicles and their average waiting time. A Mamdani inference system with triangular and
trapezoidal membership functions, a 9-rule base and centroid defuzzification was
implemented from scratch in Python. It was tested on a simulated junction against a
30-second fixed-time signal using the same random vehicle arrivals. Averaged over 10
random runs of 30 minutes, the fuzzy controller reduced the average waiting time by
31.6% in balanced traffic and by 59-65% when traffic was uneven between roads. A
Streamlit dashboard shows every step of the inference.

## 2. Problem Statement

Design a controller that changes the green duration of each road of a junction
according to current traffic, so that waiting time and queues are reduced compared to a
fixed-time signal. The controller should handle imprecise descriptions of traffic such
as "heavy" or "waited long".

## 3. Objectives

- Implement fuzzification, rule evaluation, aggregation and defuzzification without a
  fuzzy library.
- Build a simple junction simulation to test the controller.
- Compare the fuzzy controller with a fixed-time controller on identical traffic.
- Make the inference process visible for explanation (membership graphs, rule firing).

## 4. Introduction

Most signals in Indian cities run on fixed cycles. At off-peak hours cars wait at red
on an empty junction, and at peak hours one road keeps backing up while the cross road
gets green it doesn't need. Adaptive systems such as SCOOT and SCATS solve this with
detectors and optimisation. A simpler approach that suits our course is fuzzy control:
the knowledge of a traffic policeman ("lots of cars waiting for long, keep it green
longer") is written as IF-THEN rules over fuzzy sets.

## 5. Why Fuzzy Logic?

- No exact model maps traffic to the "correct" green time, but expert rules are easy to
  state.
- Terms like *heavy* or *long wait* have no sharp boundary. With crisp thresholds,
  29 and 31 vehicles would get very different green times.
- Fuzzy inference gives a smooth output surface and is very cheap to compute.

## 6. System Architecture

```
Traffic simulation ──> queue length, avg waiting time of the road whose turn it is
                                    │
                                    ▼
                     Fuzzy inference system (fuzzy_logic.py)
                                    │ green time (s)
                                    ▼
                     Controller (controller.py) ──> signal phase
                                    │
                                    ▼
          Simulation updates queues ──> metrics ──> Streamlit dashboard
```

Modules: `fuzzy_logic.py` (engine), `controller.py` (fixed and fuzzy controllers),
`traffic_simulation.py` (junction model), `visualization.py` (graphs), `app.py` (UI).

## 7. Fuzzy Logic Methodology

A Mamdani-type system is used:

1. **Fuzzification:** crisp inputs are converted into membership degrees.
2. **Rule evaluation:** firing strength α = min(μ_density, μ_waiting) (AND = min).
3. **Implication:** each consequent set is clipped at α: μ'(x) = min(α, μ_out(x)).
4. **Aggregation:** μ_agg(x) = max over rules of μ'(x) (OR = max).
5. **Defuzzification:** green = Σ x·μ_agg(x) / Σ μ_agg(x), over 501 points from
   10 to 60 s.

## 8. Membership Functions

| Variable | Range | Set | Type | Points |
|---|---|---|---|---|
| Density (vehicles) | 0-60 | LOW | trapezoid | 0, 0, 8, 20 |
| | | MEDIUM | triangle | 12, 25, 38 |
| | | HIGH | trapezoid | 30, 42, 60, 60 |
| Waiting time (s) | 0-120 | SHORT | trapezoid | 0, 0, 15, 35 |
| | | MEDIUM | triangle | 20, 45, 70 |
| | | LONG | trapezoid | 55, 80, 120, 120 |
| Green time (s) | 10-60 | SHORT | trapezoid | 10, 10, 14, 24 |
| | | MEDIUM | triangle | 18, 30, 42 |
| | | LONG | trapezoid | 36, 48, 60, 60 |

Adjacent sets overlap so that every input value belongs to at least one set. The break
points were adjusted by running the simulation and checking that light roads get short
greens and jammed roads get long ones.

*(Insert screenshots of the three membership graphs from the "Fuzzy Rule Evaluation"
page here.)*

## 9. Rule Base

| # | Density | Waiting | Green |
|---|---|---|---|
| R1 | LOW | SHORT | SHORT |
| R2 | LOW | MEDIUM | SHORT |
| R3 | LOW | LONG | MEDIUM |
| R4 | MEDIUM | SHORT | MEDIUM |
| R5 | MEDIUM | MEDIUM | MEDIUM |
| R6 | MEDIUM | LONG | LONG |
| R7 | HIGH | SHORT | MEDIUM |
| R8 | HIGH | MEDIUM | LONG |
| R9 | HIGH | LONG | LONG |

All 9 combinations are covered. R3 prevents a road with few cars from being starved,
and R7 stops a queue that has just formed from taking a very long green.

## 10. Algorithm / Pseudocode

```
function GREEN_TIME(vehicles, wait):
    μD ← fuzzify(vehicles, DENSITY_SETS)
    μW ← fuzzify(wait, WAITING_SETS)
    level[SHORT, MEDIUM, LONG] ← 0
    for each rule (d, w, g):
        α ← min(μD[d], μW[w])
        level[g] ← max(level[g], α)
    for each x in 10..60 step 0.1:
        μagg(x) ← max over g of min(level[g], μ_g(x))
    return round( Σ x·μagg(x) / Σ μagg(x) )

SIMULATION (each phase):
    d ← next road in order N, E, S, W
    g ← controller.GREEN_TIME(queue(d), avg_wait(d))
    for g seconds: one vehicle leaves road d every 2 s, new vehicles arrive randomly
    3 s yellow / all-red
```

**Worked example:** 33 vehicles and 62 s waiting.

- Fuzzification gives μD = {0, 0.38, 0.25} and μW = {0, 0.32, 0.28}.
- Rules R5 = 0.32 (MEDIUM), R6 = 0.28, R8 = 0.25 and R9 = 0.25 (all LONG) fire.
- MEDIUM is clipped at 0.32 and LONG at 0.28.
- Centroid = 4702.15 / 119.65 = **39.30 s**, so the green time is 39 s.

## 11. Implementation

- Python 3, NumPy (output array only), Pandas, Matplotlib, Streamlit. No fuzzy library.
- **Simulation:** 1-second time steps. Arrivals are Bernoulli trials per second
  (approximately Poisson), discharge is 1 vehicle per 2 s on green, and there is a 3 s
  lost time per phase. Arrivals are generated once from a seed and given to both
  controllers.
- **Dashboard pages:**
  - Dashboard: manual, random or CSV input, junction animation and fired rules.
  - Fuzzy Rule Evaluation: every intermediate value.
  - Fixed vs Fuzzy: metrics and charts.
  - How It Works.

*(Insert screenshots of the dashboard and the junction here.)*

## 12. Results

Four traffic scenarios were simulated for 1800 s each. Arrival rates are in
vehicles/min (N, E, S, W):

- Balanced: 4.8 each
- Peak hour: 9.0, 2.4, 7.8, 1.8
- One road congested: 3.0, 10.2, 2.4, 3.0
- Light: 1.8, 1.2, 1.8, 1.2

Values below are the mean of 10 runs (seeds 1-10). The baseline is fixed-time 30 s.

| Scenario | Avg wait fixed (s) | Avg wait fuzzy (s) | Change | Avg queue fixed | Avg queue fuzzy | Served fixed | Served fuzzy |
|---|---|---|---|---|---|---|---|
| Balanced | 50.9 | 34.8 | -31.6% | 16.3 | 11.2 | 564 | 568 |
| Peak hour (N-S heavy) | 166.4 | 68.1 | -59.1% | 60.7 | 23.7 | 525 | 606 |
| One road congested | 178.3 | 62.5 | -64.9% | 64.1 | 19.5 | 448 | 545 |
| Light (night) | 44.4 | 25.2 | -43.2% | 4.5 | 2.5 | 178 | 179 |

The fuzzy controller had a lower average waiting time than the 30 s fixed signal in
all 40 runs.

## 13. Fixed-Time vs Fuzzy Comparison

To check whether the gain only comes from a badly chosen fixed time, the fixed signal
was also run with 15, 20 and 45 s greens. Average waiting time in seconds, mean of 10
runs:

| Scenario | Fixed 15 | Fixed 20 | Fixed 30 | Fixed 45 | Fuzzy |
|---|---|---|---|---|---|
| Balanced | 32.6 | 40.0 | 50.9 | 66.5 | 34.8 |
| Peak hour | 161.7 | 178.7 | 166.4 | 154.7 | 68.1 |
| One road congested | 161.3 | 174.0 | 178.3 | 176.7 | 62.5 |
| Light | 24.5 | 31.7 | 44.4 | 57.8 | 25.2 |

**Observation:** when all roads carry similar traffic, a short fixed green (15 s) does
about as well as the fuzzy controller, slightly better in fact. When traffic is uneven,
no single fixed value works, because a long green wastes time on the empty roads and a
short green cannot clear the busy one. Here the fuzzy controller cuts waiting time to
less than half of the best fixed setting. The main benefit of the fuzzy controller is
adapting to unequal and changing demand, not beating a well-tuned timer on uniform
traffic.

## 14. Limitations

- Membership functions and rules are tuned by hand.
- Only two inputs; no lanes, turning movements, pedestrians or emergency vehicles.
- Fixed phase order; an empty road still gets about 15 s (the centroid output cannot go
  below about 14.9 s).
- Simplified traffic model with constant discharge and one lane per approach.
- Tested only in simulation, not on real traffic counts.

## 15. Future Scope

- Learn the membership function parameters with a genetic algorithm or ANFIS.
- Skip phases with empty queues, and add inputs like the queue on the next road or time
  of day.
- Coordinate neighbouring junctions (green wave).
- Use camera-based vehicle counting as input.

## 16. Conclusion

A fuzzy traffic signal controller was implemented from first principles and tested in
simulation. The project shows each stage of a Mamdani system on a practical problem.
Compared to a 30 s fixed signal it reduced average waiting time by 31-65% depending on
the scenario. Further tests showed that its real advantage is handling uneven traffic,
where it beat every fixed timing that was tried.

## 17. References

1. S. Russell and P. Norvig, *Artificial Intelligence: A Modern Approach*, Prentice Hall.
2. E. Rich, K. Knight and S. B. Nair, *Artificial Intelligence*, 3rd ed., Tata McGraw-Hill, 2009.
3. L. A. Zadeh, "Fuzzy sets," *Information and Control*, vol. 8, pp. 338-353, 1965.
4. E. H. Mamdani and S. Assilian, "An experiment in linguistic synthesis with a fuzzy
   logic controller," *Int. J. Man-Machine Studies*, vol. 7, pp. 1-13, 1975.
5. C. P. Pappis and E. H. Mamdani, "A fuzzy logic controller for a traffic junction,"
   *IEEE Trans. Systems, Man and Cybernetics*, vol. 7, no. 10, pp. 707-717, 1977.
6. Streamlit documentation, https://docs.streamlit.io
