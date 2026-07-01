import pandas as pd

from backend.projections.scoring import fantasy_points


def test_ppr_scoring_known_line():
    # A clean stat line with an easy hand-computed PPR total.
    row = pd.DataFrame(
        [
            {
                "passing_yards": 0,
                "passing_tds": 0,
                "interceptions": 0,
                "rushing_yards": 100,   # 10.0
                "rushing_tds": 1,       # 6.0
                "receptions": 5,        # 5.0
                "receiving_yards": 50,  # 5.0
                "receiving_tds": 0,
                "rushing_fumbles_lost": 1,  # -2.0
            }
        ]
    )
    # 10 + 6 + 5 + 5 - 2 = 24.0
    assert fantasy_points(row).iloc[0] == 24.0


def test_missing_columns_treated_as_zero():
    row = pd.DataFrame([{"receptions": 3}])  # 3.0, everything else absent
    assert fantasy_points(row).iloc[0] == 3.0


def test_passing_yards_and_td():
    row = pd.DataFrame([{"passing_yards": 300, "passing_tds": 2, "interceptions": 1}])
    # 300*0.04 + 2*4 - 1*2 = 12 + 8 - 2 = 18.0
    assert fantasy_points(row).iloc[0] == 18.0
