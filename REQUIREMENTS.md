# Requirements — Fantasy Football Draft Model + Draft-Day UI

> **Status:** DRAFT. This is a working document to make sure we build the right
> thing. Items marked ✅ are decided; ⬜ are open for you to fill in or confirm;
> 🔧 are tunable defaults already coded but easily changed.
>
> Each requirement has an ID (e.g. `FR-3`) so we can reference it in issues,
> commits, and the plan.

---

## 1. Vision & problem statement

**One-liner:** A personal draft assistant that tells me the best available pick
in real time during my fantasy football draft, backed by my own projections and
value model.

⬜ **Your take — fill in / edit:**
- The problem I'm solving for myself:
  _(e.g. "I lose value late in drafts by reaching or missing positional runs; I
  want a data-backed recommendation on the clock.")_
- What "success" looks like after this draft:
  _(e.g. "I trust the recommendations, made no panic picks, and my roster's
  projected points beat the league average.")_

---

## 2. Goals & non-goals

### Goals ✅ (confirmed so far)
- **G-1** Generate my own season-long **PPR** point projections per player.
- **G-2** Convert projections into draft value via **VOR** (value over
  replacement) and dynamic **VONA** (value over next available).
- **G-3** Provide a **live best-available recommender** UI usable on the clock.
- **G-4** Keep the model **transparent and tunable** — I can see *why* a player
  is recommended and adjust weights.

### Non-goals ⬜ (confirm these are out of scope)
- **NG-1** In-season lineup/waiver management (draft-day only).
- **NG-2** Multi-league / multi-user support (personal, single draft).
- **NG-3** Trade analysis.
- ⬜ Anything else you explicitly *don't* want: _______________

---

## 3. Users & context

- **Primary user:** me (the drafter), during a live draft.
- ✅ **Draft environment:** **ESPN.** ESPN has no official public draft API, so
  the baseline is **manual pick entry** in our UI (fast mark-drafted). Live
  auto-sync from ESPN is a possible later enhancement but not assumed.
- ⬜ **Device I'll use during the draft:** _(laptop / tablet / phone)_ — affects
  UI layout priorities.
- ⬜ **Time pressure:** how many seconds per pick? _(affects how fast the
  recommendation must render and how scannable the UI must be.)_

---

## 4. Functional requirements

### 4.1 Data & projections
- **FR-1** ✅ Ingest historical NFL stats (nflverse) and produce per-player
  season projections.
- **FR-2** ✅ PPR scoring, fully config-driven.
- **FR-3** 🔧 Use recency-weighted history with sample-size shrinkage
  (currently seasons 2022–2024; 2025 not yet published in the data mirror).
- **FR-4** ✅ **Rookies & incoming players:** must appear on the board. Rookies
  have no NFL history, so they are placed using **public consensus rank / ADP**
  (see §4.5) rather than the historical model.
- **FR-5** ✅ **External projections override:** **No.** We do not import external
  projection sets. Values come from our own model (skill positions) plus market
  rank for players the model can't project. Projection provenance is documented
  in §4.5.
- **FR-6** ✅ **K & DST:** **needed on the board.** They aren't projected from
  nflverse offensive stats, so they are ranked via public consensus rank / ADP
  (see §4.5).

### 4.2 Valuation
- **FR-7** ✅ Compute replacement level per position from league size + starters.
- **FR-8** ✅ Compute **VOR** and assign **tiers** per position.
- **FR-9** ✅ Compute **VONA** live during the draft (marginal value vs. the best
  player likely to survive to my next pick, using ADP).
- **FR-10** ⬜ **Positional need weighting:** how strongly should my current
  roster construction bias recommendations vs. pure best-value?
  _(e.g. "value-first, small need nudge" vs. "hard-fill starters early")_

### 4.3 Draft state & recommender
- **FR-11** ✅ Track picks made (all teams) and my roster.
- **FR-12** ✅ `/recommend` returns ranked best-available with the *why*
  (value, scarcity, need).
- **FR-13** ⬜ **Pick entry:** manual mark-drafted is the baseline. Do you also
  want **undo/correct a mis-entered pick**? _(assume yes)_
- **FR-14** ⬜ **Draft setup:** enter draft slot/position and see when my next
  pick comes up (snake math)? _(assume yes)_
- **FR-15** ⬜ **Queue/targets:** ability to star/queue players I want?
- **FR-16** ⬜ **Bye-week & risk flags:** surface bye conflicts and injury risk
  on the recommendation? _(planned Phase 5 — confirm priority)_

### 4.4 UI
- **FR-17** ✅ Best-available recommendations panel (primary view).
- **FR-18** ✅ My-roster tracker (slots filled / needs).
- **FR-19** 🔧 Full draft board (all teams' picks) — planned as secondary.
- **FR-20** ⬜ **Search/filter** players by name/position/team.
- **FR-21** ⬜ Tier view / visual tier cliffs.

### 4.5 Data sources & projection provenance
Where every number on the board comes from:

- **Historical stats → model projections (QB/RB/WR/TE veterans):**
  [nflverse](https://github.com/nflverse) via the
  [`nfl_data_py`](https://github.com/nflverse/nfl_data_py) package —
  `import_seasonal_data` (per-player season stat totals) joined with
  `import_seasonal_rosters` (name/position/team/age). Free, open, community-
  maintained. Seasons **2022–2024** (the mirror has not yet published 2025).
  These feed our own PPR scoring + recency-weighted, shrinkage-adjusted
  projection model. **No paid/third-party projection service is used.**
- **Rookies, and K/DST:** no usable nflverse offensive history, so these are
  ordered on the board using **public consensus rankings / ADP** (a free,
  scrape-able market source; exact provider TBD in Phase 2). This is *market
  ordering to place players the model can't project* — not an import of someone
  else's projection numbers (see FR-5).
- ⬜ **ADP/consensus provider (TBD):** candidates — FantasyPros ECR, nflverse
  ADP, or similar. Will be pinned in Phase 2 and documented here.

---

## 5. Non-functional requirements

- **NFR-1** ⬜ **Latency:** recommendation must render in < ___ seconds after a
  pick is entered. _(suggest < 1s)_
- **NFR-2** ✅ **Offline resilience:** projections precomputed; the app must work
  during the draft without depending on a live external API.
- **NFR-3** ✅ **Local-only:** runs on my machine (FastAPI + React); no hosting
  required. ⬜ _(Confirm — or do you want it deployed somewhere?)_
- **NFR-4** ⬜ **Reliability during draft:** if the app crashes mid-draft, can I
  recover state? _(e.g. persist draft state to disk so a refresh restores it)_
- **NFR-5** ✅ **Transparency:** every recommendation shows the numbers behind it.
- **NFR-6** ⬜ **Ease of start:** one command to launch backend + frontend?

---

## 6. Constraints & assumptions (league settings) 🔧

Currently coded in `backend/config.py` — change freely:
- **Format:** Redraft, PPR ✅
- **Teams:** 12 🔧
- **Draft type:** Snake 🔧
- **Starters:** 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX (RB/WR/TE), 1 K, 1 DST 🔧
- **Bench:** ~6 🔧
- **Season:** 2026 🔧
- ⬜ **Anything non-standard in your league?** (e.g. 6-pt passing TD, bonuses,
  superflex, PPR variations, roster size): _______________

---

## 7. Open questions (please answer)

1. ✅ **Draft host:** ESPN. No public draft API → manual pick entry baseline.
2. ✅ **Rookies + K/DST:** include all on the board (via consensus rank / ADP).
3. ✅ **External projections:** No — own model only; provenance documented (§4.5).
4. ⬜ How much should roster *need* override raw *value*?
5. ⬜ Must the app recover draft state after a crash/refresh?
6. ⬜ Any non-standard scoring or roster rules in your league?

---

## 8. Out of scope / future ideas

- ⬜ Auction draft support
- ⬜ Keeper/dynasty valuation
- ⬜ Auto-sync with draft platforms via API
- ⬜ Post-draft roster grade / season simulation
- _(add your own)_

---

## 9. Acceptance — "we built the right thing" if…

⬜ Fill in 2–4 concrete checks you'd use to judge success, e.g.:
- [ ] On draft day, I can enter my slot, mark picks as they happen, and always
      see a ranked recommendation in under a second.
- [ ] The recommendations pass my smell test vs. industry consensus, with
      explainable deviations.
- [ ] _______________
