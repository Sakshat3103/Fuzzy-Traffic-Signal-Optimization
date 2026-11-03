# Adaptive Traffic Signal Controller using Fuzzy Logic

CSE3121 Artificial Intelligence and Soft Computing, course project (Jul-Nov 2026)
Sakshat Jain, 2427030801

A 4-way junction where the green time for each road is decided by a Mamdani fuzzy
inference system instead of a fixed timer. The inputs are the number of vehicles waiting
and their average waiting time. The fuzzy engine (fuzzification, rule evaluation,
aggregation, centroid defuzzification) is written by hand in `fuzzy_logic.py`. No fuzzy
library is used.

## Files

```
app.py                  Streamlit UI (4 pages)
fuzzy_logic.py          the fuzzy inference system
controller.py           fixed-time and fuzzy controllers
traffic_simulation.py   junction simulation (1 second steps)
visualization.py        junction drawing and graphs
data/sample_traffic.csv test cases for the dashboard
REPORT.md               project report
VIVA.md                 viva questions and answers
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

It opens at http://localhost:8501. To check only the fuzzy engine from the terminal:

```bash
python fuzzy_logic.py
```

## Pages

- **Dashboard**: enter traffic manually, generate random traffic, or load a test case.
  It shows the green time for every road, the rules that fired, and an animated
  signal cycle.
- **Fuzzy Rule Evaluation**: sliders for both inputs. It shows the membership values
  on the graphs, every rule with its min() calculation, the clipped and aggregated
  output, and the centroid sum.
- **Fixed vs Fuzzy**: runs both controllers on the same random arrivals and compares
  waiting time, queue length and vehicles served.
- **How It Works**: algorithm flow, the rule table and the simulation assumptions.

## Deploy on Streamlit Community Cloud (free)

1. Make a GitHub repo, for example `fuzzy-traffic-signal` (public).
2. Push the project:
   ```bash
   cd fuzzy-traffic-signal
   git init
   git add .
   git commit -m "fuzzy traffic signal project"
   git branch -M main
   git remote add origin https://github.com/<your-username>/fuzzy-traffic-signal.git
   git push -u origin main
   ```
3. Go to https://share.streamlit.io and sign in with GitHub.
4. Click **Create app**, then **Deploy a public app from GitHub**.
5. Pick the repo, branch `main`, main file `app.py`, then click **Deploy**.
6. Wait 2-3 minutes while it installs `requirements.txt`. You get a link like
   `https://<name>.streamlit.app`.

No API keys or secrets are needed. If the app sleeps after a few days of no use,
open the link and click "Yes, get this app back up".
