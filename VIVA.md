# Viva preparation

## Basic questions

**1. What is Artificial Intelligence?**
Making machines do tasks that need human-like intelligence, such as reasoning,
learning, planning and decision making. In this course AI is studied through agents
that perceive an environment and act to reach a goal.

**2. What is Soft Computing?**
A group of techniques that accept imprecision, uncertainty and approximate answers in
exchange for being practical and robust. The main members are fuzzy logic, neural
networks and evolutionary algorithms. Hard computing needs exact models and exact
answers.

**3. What is Fuzzy Logic?**
Logic where truth is a degree between 0 and 1 instead of only true or false. It was
proposed by Lotfi Zadeh (1965) to reason with vague terms like "heavy traffic".

**4. How is it different from Boolean logic?**
In Boolean logic, 31 cars is either "heavy" (1) or "not heavy" (0). In fuzzy logic it
can be heavy with degree 0.08 and medium with degree 0.54 at the same time.
AND/OR/NOT become min/max/(1 - μ), and the output changes smoothly instead of jumping
at a threshold.

**5. What is a fuzzy set?**
A set where every element has a membership degree μ(x) in [0, 1]. Example: the set
HIGH density, where 30 cars has μ = 0, 36 cars has μ = 0.5 and 42+ cars has μ = 1.

**6. What is a membership function?**
The function that gives μ(x) for every x. I used triangular and trapezoidal MFs.

**7. What is fuzzification?**
Converting a crisp input into membership degrees for every fuzzy set of that variable.
For example, 33 vehicles becomes LOW 0, MEDIUM 0.38, HIGH 0.25.

**8. What is defuzzification?**
Converting the aggregated fuzzy output back into one crisp number, here the green time
in seconds. I used the centroid method.

## Project questions

**9. Why traffic signals?**
Fixed timers waste green time on empty roads and starve busy roads. Traffic is also
described in vague words ("busy", "waited too long"), which suits fuzzy logic. It is
also easy to simulate without real data or APIs.

**10. Why is fuzzy logic suitable?**
There is no exact mathematical formula for the "right" green time, but a traffic
policeman can easily state rules like "many cars and long wait means give a long
green". Fuzzy logic turns these rules directly into a controller and gives smooth
outputs at the boundaries.

**11. Inputs?**
(1) Traffic density = vehicles in the queue of that road, range 0-60.
(2) Average waiting time of those vehicles, range 0-120 s.

**12. Output?**
Green time for that road, universe 10-60 s.

**13. Which membership functions?**
- Density: LOW trapezoid (0,0,8,20), MEDIUM triangle (12,25,38), HIGH trapezoid (30,42,60,60)
- Waiting: SHORT trapezoid (0,0,15,35), MEDIUM triangle (20,45,70), LONG trapezoid (55,80,120,120)
- Green: SHORT trapezoid (10,10,14,24), MEDIUM triangle (18,30,42), LONG trapezoid (36,48,60,60)

**14. Why these shapes?**
Triangles and trapezoids are simple, fast and easy to explain. Trapezoids are used at
the ends so that, for example, 50 and 60 cars are both fully HIGH. Neighbouring sets
overlap so every input has at least one non-zero membership, and the output changes
smoothly. I tuned the break points by running the simulation.

**15. Explain the rule base.**
There are 9 rules, one for each density × waiting pair (3 × 3), so every input is
covered.

| density \ waiting | SHORT  | MEDIUM | LONG   |
|-------------------|--------|--------|--------|
| LOW               | SHORT  | SHORT  | MEDIUM |
| MEDIUM            | MEDIUM | MEDIUM | LONG   |
| HIGH              | MEDIUM | LONG   | LONG   |

The idea: green time grows with both inputs. A long queue that just formed (HIGH,
SHORT) gets MEDIUM, not LONG. A few cars that waited very long (LOW, LONG) still get
MEDIUM so they are not starved.

**16. How is firing strength calculated?**
The antecedent uses AND, so strength = min(μ_density, μ_waiting). For example, R5 at
(33 cars, 62 s) = min(0.38, 0.32) = 0.32.

**17. What happens in aggregation?**
Each rule's output set is clipped at its firing strength (Mamdani implication = min).
If two rules give the same output set, the larger strength is kept. All the clipped
shapes are then combined with max into one fuzzy output shape.

**18. Why centroid?**
It uses the whole aggregated shape, so every fired rule affects the answer in
proportion to its strength. The output changes smoothly, and it is the standard
method for Mamdani systems. Mean-of-max ignores the weaker rules and can jump.
Drawback: the centroid can never reach the extreme ends, so my output stays between
about 14.9 s and 50.7 s even though the universe is 10-60 s.

**19. HIGH density but SHORT waiting?**
Rule 7 fires, so green is MEDIUM (~30 s). The queue is long but has just formed, so it
gets a fair share without starving the other roads. For 45 cars and 10 s waiting the
output is 30 s.

**20. Two rules fire together?**
Both are used. Each is clipped at its own strength and aggregated with max, so the
centroid lands between their output sets, closer to the stronger one. If both have the
same consequent, max of the two strengths is taken.

## Implementation questions

**21. Explain the algorithm in your code.**
`compute_green_time(vehicles, avg_wait)` in `fuzzy_logic.py` does five steps:
1. `fuzzify()` gets μ for every set of both inputs.
2. `evaluate_rules()` does min of the two μ for each of the 9 rules.
3. `aggregate()` keeps the max strength per output set, clips that set's curve with
   `np.minimum`, and combines the curves with `np.maximum`.
4. `centroid()` computes Σxμ / Σμ over 501 points from 10 to 60 s.
5. Rounds to whole seconds.

**22. Full example (33 vehicles, 62 s waiting)**
- Fuzzification: density LOW 0, MEDIUM 0.38, HIGH 0.25. Waiting SHORT 0, MEDIUM 0.32,
  LONG 0.28.
- Rules fired:
  - R5 (M,M → MEDIUM) = min(0.38, 0.32) = 0.32
  - R6 (M,L → LONG) = min(0.38, 0.28) = 0.28
  - R8 (H,M → LONG) = min(0.25, 0.32) = 0.25
  - R9 (H,L → LONG) = min(0.25, 0.28) = 0.25
- Aggregation: MEDIUM clipped at 0.32. LONG clipped at max(0.28, 0.25, 0.25) = 0.28.
- Centroid: 4702.15 / 119.65 = 39.30 s, so the green time is 39 s.

**23. Complexity?**
One decision is O(R + N), where R = 9 rules and N = 501 output points. The cost is
constant and tiny, so it can run every phase in real time. The simulation is O(T) for T
seconds.

**24. Limitations?**
- MFs and rules are hand-tuned, not learned.
- Only queue length and waiting time are used, with no lanes, turning traffic,
  pedestrians or emergency vehicles.
- Fixed phase order; empty roads still get at least about 15 s.
- The simulation is simplified (one lane per road, constant 2 s discharge).
- Against a well-chosen short fixed time (15 s), fuzzy is only about equal under
  balanced or light traffic. The gain shows when traffic is uneven.

**25. Future scope?**
Tune the MFs automatically (genetic algorithm or ANFIS), add more inputs (queue on the
next road, pedestrians, time of day), skip empty phases, coordinate several junctions,
and use real vehicle counts from cameras or loop detectors.
