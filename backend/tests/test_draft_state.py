from backend.api.draft_state import DraftState, snake_pick_order


def test_snake_pick_order():
    order = snake_pick_order(num_teams=3, rounds=2)
    assert order == [1, 2, 3, 3, 2, 1]


def test_my_pick_overalls_snake():
    st = DraftState(my_slot=3, num_teams=12, rounds=4)
    # Round 1: pick 3. Round 2 (reversed): pick 10. Round 3: pick 27. Round 4: 34.
    assert st.my_pick_overalls == [3, 22, 27, 46]


def test_on_the_clock_and_my_pick():
    st = DraftState(my_slot=3, num_teams=12, rounds=3)
    assert st.on_the_clock == 1 and not st.is_my_pick
    st.pick("a|WR")
    st.pick("b|WR")
    assert st.on_the_clock == 3 and st.is_my_pick
    assert st.current_overall == 3


def test_next_and_following_overall():
    st = DraftState(my_slot=3, num_teams=12, rounds=4)
    for i in range(2):
        st.pick(f"p{i}|RB")
    assert st.my_next_overall() == 3       # on the clock now
    assert st.my_following_overall() == 22  # next time after this


def test_derived_roster_and_undo():
    st = DraftState(my_slot=1, num_teams=2, rounds=3)
    # slot 1 picks at overall 1 and 4 (snake, 2 teams).
    assert st.my_pick_overalls == [1, 4, 5]
    st.pick("mine1|RB")   # overall 1 -> mine
    st.pick("opp|WR")     # overall 2 -> opponent
    st.pick("opp2|WR")    # overall 3 -> opponent
    st.pick("mine2|WR")   # overall 4 -> mine
    assert st.my_picked_keys == ["mine1|RB", "mine2|WR"]
    assert st.undo() == "mine2|WR"
    assert st.my_picked_keys == ["mine1|RB"]


def test_persistence_round_trip(tmp_path, monkeypatch):
    import backend.api.draft_state as ds

    monkeypatch.setattr(ds, "_STATE_PATH", tmp_path / "state.json")
    st = DraftState(my_slot=5, num_teams=10, rounds=15)
    st.pick("x|RB")
    st.save()
    loaded = DraftState.load()
    assert loaded is not None
    assert loaded.my_slot == 5 and loaded.picked == ["x|RB"]
