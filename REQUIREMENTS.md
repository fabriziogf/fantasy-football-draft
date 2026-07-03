# Requirements — Fantasy Football Draft Model + Draft-Day UI

> **Status:** DRAFT. This is a working document to make sure we build the right
> thing. Items marked ✅ are decided; ⬜ are open for you to fill in or confirm;
> 🔧 are tunable defaults already coded but easily changed.
>
> Each requirement has an ID (e.g. `FR-3`) so we can reference it in issues,
> commits, and the plan.

---

## 1. Vision & problem statement ✅ (confirmed)

**One-liner:** A personal draft assistant that tells me the best available pick
in real time during my fantasy football draft, backed by my own projections and
value model.

✅ **Your take — fill in / edit:**
- The problem I'm solving for myself: I want to have a clear strategy going into my fantasy football draft and a UI that will help me keep track of players already selected and what is the next best option given my strategy.
- What "success" looks like after this draft: I have the team that balances both players that will certainly perform and others that have high upside.

---

## 2. Goals & non-goals

### Goals ✅ (confirmed)
- **G-1** Generate my own season-long **PPR** point projections per player.
- **G-2** Convert projections into draft value via **VOR** (value over
  replacement) and dynamic **VONA** (value over next available).
- **G-3** Provide a **live best-available recommender** UI usable on the clock.
- **G-4** Keep the model **transparent and tunable** — I can see *why* a player
  is recommended and adjust weights.

### Non-goals ✅ (confirmed)
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
- ✅ **Device I'll use during the draft:** **laptop**
- ✅ **Time pressure:** **30secs**

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
- **FR-10** ✅ **Positional need weighting:** value-first on RB/WR early —
  prioritize accumulating **3 strong WRs and 2 strong RBs** before shifting to
  roster-need filling for other slots. **Carve-out:** deviate to a **top-3 TE or
  top-3 QB only when that player is projected to outscore the best available WR
  or RB.** Low-value positions (K, D/ST) come near the end unless there is a
  clearly dominant candidate.

### 4.3 Draft state & recommender
- **FR-11** ✅ Track picks made (all teams) and my roster.
- **FR-12** ✅ `/recommend` returns ranked best-available with the *why*
  (value, scarcity, need).
- **FR-13** ✅ **Pick entry:** manual mark-drafted is the baseline, with ability to undo/correct a mis-entered pick.
- **FR-14** ✅ **Draft setup:** enter draft slot/position and see when my next
  pick comes up given a snake draft
- **FR-15** ✅ **Bye-week & risk flags:** surface bye conflicts and injury risk
  on the recommendation (Phase 5)

### 4.4 UI
- **FR-16** ✅ Best-available recommendations panel (primary view).
- **FR-17** ✅ My-roster tracker (slots filled / needs).
- **FR-18** 🔧 Full draft board (all teams' picks) — planned as secondary.
- **FR-19** ✅ **Search/filter** players by name/position/team.
- **FR-20** ✅ Tier view / visual tier cliffs.

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
  ordered on the board using **public consensus rank / ADP**. This is *market
  ordering to place players the model can't project* — not an import of someone
  else's projection numbers (see FR-5).
- ✅ **ADP/consensus provider:** **Fantasy Football Calculator (FFC) ADP API** —
  free, public JSON, no auth, parameterized to our league:
  `https://fantasyfootballcalculator.com/api/v1/adp/ppr?teams=12&year=2026`.
  Provides ADP, position, team, bye week, and std-dev; covers rookies, K, and
  DST. **Normalization caveat:** FFC uses `PK`/`DEF` for positions and team codes
  like `LAR`, while nflverse uses `K`/`DST` and `LA` — a small mapping layer
  joins FFC to our projections in Phase 2.

---

## 5. Non-functional requirements

- **NFR-1** ✅ **Latency:** recommendation must render in < 1 second after a
  pick is entered.
- **NFR-2** ✅ **Offline resilience:** projections precomputed; the app must work
  during the draft without depending on a live external API.
- **NFR-3** ✅ **Local-only:** runs on my machine (FastAPI + React); no hosting
  required.
- **NFR-4** ✅ **Reliability during draft:** if the app crashes mid-draft, I can
  recover state
- **NFR-5** ✅ **Transparency:** every recommendation shows the numbers behind it.
- **NFR-6** ✅ **Ease of start:** one command to launch backend + frontend

---

## 6. Constraints & assumptions (league settings) 🔧

Currently coded in `backend/config.py` — change freely:
- **Format:** Redraft, PPR ✅
- **Teams:** 12 🔧
- **Draft type:** Snake 🔧
- **Starters:** 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX (RB/WR/TE), 1 K, 1 DST 🔧
- **Bench:** ~6 🔧
- **Season:** 2026 🔧
- ✅ **Anything non-standard in your league?** No

---

## 7. Open questions (please answer)

1. ✅ **Draft host:** ESPN. No public draft API → manual pick entry baseline.
2. ✅ **Rookies + K/DST:** include all on the board (via consensus rank / ADP).
3. ✅ **External projections:** No — own model only; provenance documented (§4.5).
4. ✅ **How much should roster *need* override raw *value*?** After I have three strong WRs and two strong RBs, go for roster need
5. ✅ **Must the app recover draft state after a crash/refresh?** Yes
6. ✅ **Any non-standard scoring or roster rules in your league?** No

---

## 8. Out of scope / future ideas

- ✅ Auction draft support
- ✅ Keeper/dynasty valuation
- ✅ Auto-sync with draft platforms via API
- ✅ Post-draft roster grade / season simulation

---

## 9. Acceptance — "we built the right thing" if…

- [ ] On draft day, I can enter my slot, mark picks as they happen, and always see a ranked recommendation in under a second.
- [ ] The recommendations pass my smell test vs. industry consensus, with explainable deviations.
- [ ] At the end, I have a complete roster and a bench with at least two additional RBs and two additional WRs
