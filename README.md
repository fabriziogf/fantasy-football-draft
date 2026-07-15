# fantasy-football-draft

A personal fantasy-football draft assistant: your own PPR projections turned into
value (VOR/VONA), served through a live, best-available **draft-day UI**.

Built for a 12-team PPR snake draft on ESPN (manual pick entry). See
[`REQUIREMENTS.md`](REQUIREMENTS.md) for the spec and [`PLAN.md`](PLAN.md) for the
roadmap.

## How it works

```
nflverse stats ─► projections ─► valuation ─► FastAPI ─► React draft cockpit
   + FFC ADP       (PPR pts)     (VOR, VONA,   (draft state,  (recommendations,
                                  tiers)        recommend)     roster, tiers)
```

- **Projections** — recency-weighted, shrinkage-adjusted PPR points from nflverse
  (2022–2024). Rookies and K/DST placed via Fantasy Football Calculator ADP.
- **Valuation** — replacement level → VOR, per-position tiers, ADP-anchored K/DST.
- **Recommender** — blends VOR with VONA (scarcity to your next pick) and applies
  a roster strategy (RB/WR core first, QB/TE value carve-out, K/DST late).
- **UI** — recommendations panel, roster tracker, search-to-mark, tier board,
  undo. Draft state persists to disk so a refresh recovers it.

## Setup

**Backend** (Python 3.11):
```bash
python3.11 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python -m backend.run_pipeline   # build projections + board
```

**Frontend** (Node):
```bash
cd frontend && npm install
```

## Run

One command (starts backend on :8000 and frontend on :5173):
```bash
./scripts/dev.sh
```
Then open <http://localhost:5173> and set your draft slot.

Or run them separately:
```bash
backend/.venv/bin/uvicorn backend.api.app:app --reload   # API on :8000
cd frontend && npm run dev                               # UI on :5173
```

## Tests

```bash
backend/.venv/bin/python -m pytest backend/tests -q
```

## Config

League settings, scoring, and model/recommender knobs live in
[`backend/config.py`](backend/config.py) — change them to re-target a different
league.
