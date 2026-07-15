# Fantasy Football Draft Model + Draft-Day UI

A projections-driven draft assistant for **redraft PPR**, with a live
best-available recommender UI for use during the draft.

## League settings (defaults)

- 12 teams, snake draft
- Starters: 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, 1 K, 1 DST, ~6 bench
- Season: 2026
- Scoring: PPR (1 pt per reception)

These live in a single config file so they can be changed without touching model code.

## Architecture

```
data ingest ──► projections ──► valuation ──► FastAPI ──► React draft UI
(nflverse,      (season pts)    (VOR/VONA,     (live state,  (best-available
 ADP/ECR)                        tiers)         who's gone)   recommender)
```

```
backend/
  data/        raw + processed player data
  ingest/      nflverse stats, ADP/ECR
  projections/ project season fantasy points (PPR)
  valuation/   replacement levels, VOR, tiers, dynamic VONA
  api/         FastAPI app: draft state + recommendations
  tests/
frontend/      React (Vite) draft-day board
```

## The model

1. **Ingest** — `nfl_data_py` (nflverse) for historical stats; FantasyPros ADP/ECR
   for a market baseline and replacement-level calibration.
2. **Projections** — season-long PPR point projections per player. Transparent
   baseline first (recent-seasons weighted average + role/games adjustment), with
   a clean seam to swap in a better model or import external projection CSVs.
3. **Valuation**
   - **VOR** (value over replacement): replacement level = the ~Nth-best player at
     each position given league size & starters. Static → tiers.
   - **VONA** (value over next available): dynamic during the draft — marginal value
     of a player vs. the best at that position likely to survive to your next pick
     (ADP-based). Drives run-awareness.

## Recommender (UI core)

On each pick, for every available player: projected pts → VOR → VONA adjusted for
current roster needs and bye conflicts, then ranked. UI shows top recommendations
with the *why* (value, scarcity, need), tier cliffs, and mark-drafted controls to
keep state synced with the real draft.

## Build phases

1. **Data + projections** — ingest pipeline, PPR projection baseline → processed files.
2. **Valuation** — replacement levels, VOR, tiers.
3. **API** — FastAPI: players, draft state, `/recommend` with live VONA.
4. **UI** — React board: recommendations, mark-drafted, roster tracker, tiers.
5. **Polish** — bye/risk flags, tuning knobs, config.

## Status

- [x] Repo created, plan written
- [x] Phase 1: data + projections
- [x] Phase 2: valuation (ADP merge, VOR, tiers, unified board)
- [x] Phase 3: API (draft state, snake math, persistence, VONA recommender)
- [ ] Phase 4: UI
- [ ] Phase 5: polish
