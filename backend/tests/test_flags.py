from backend.api.flags import assess, bye_conflict, risk_flags


def _codes(flags):
    return {f["code"] for f in flags}


def test_rookie_flag():
    row = {"position": "RB", "proj_source": "adp_imputed", "adp": 12}
    assert "rookie" in _codes(risk_flags(row))


def test_age_flag_by_position():
    old_rb = {"position": "RB", "age": 29, "proj_source": "model"}
    young_rb = {"position": "RB", "age": 24, "proj_source": "model"}
    assert "age" in _codes(risk_flags(old_rb))
    assert "age" not in _codes(risk_flags(young_rb))
    # WR threshold is higher than RB.
    wr_28 = {"position": "WR", "age": 28, "proj_source": "model"}
    assert "age" not in _codes(risk_flags(wr_28))


def test_durability_flag():
    fragile = {"position": "RB", "total_games": 18, "seasons_played": 3, "proj_source": "model"}
    durable = {"position": "RB", "total_games": 48, "seasons_played": 3, "proj_source": "model"}
    assert "durability" in _codes(risk_flags(fragile))
    assert "durability" not in _codes(risk_flags(durable))


def test_volatile_adp_flag():
    volatile = {"position": "WR", "adp": 20, "adp_stdev": 12, "proj_source": "model"}
    stable = {"position": "WR", "adp": 20, "adp_stdev": 3, "proj_source": "model"}
    assert "volatile" in _codes(risk_flags(volatile))
    assert "volatile" not in _codes(risk_flags(stable))


def test_nan_values_are_safe():
    row = {"position": "WR", "age": float("nan"), "adp": None, "adp_stdev": float("nan"),
           "total_games": float("nan"), "seasons_played": float("nan"), "proj_source": "model"}
    assert risk_flags(row) == []


def test_bye_conflict_same_position_only():
    roster = [{"name": "My RB", "position": "RB", "bye": 7},
              {"name": "My WR", "position": "WR", "bye": 7}]
    rb = {"position": "RB", "bye": 7, "name": "New RB"}
    wr_diff = {"position": "WR", "bye": 9, "name": "New WR"}
    assert bye_conflict(rb, roster)["with"] == ["My RB"]
    assert bye_conflict(wr_diff, roster) is None


def test_assess_risk_levels():
    two = {"position": "RB", "age": 30, "proj_source": "adp_imputed", "adp": 10}
    assert assess(two, [])["risk"] == "high"       # rookie + age
    one = {"position": "RB", "age": 30, "proj_source": "model"}
    assert assess(one, [])["risk"] == "medium"
    none = {"position": "RB", "age": 24, "proj_source": "model"}
    assert assess(none, [])["risk"] == "low"
