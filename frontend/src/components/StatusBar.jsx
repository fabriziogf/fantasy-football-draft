import { posClass } from './common.js'

export default function StatusBar({ draft, onUndo, onReset, busy }) {
  const {
    num_teams,
    current_overall,
    on_the_clock,
    is_my_pick,
    my_slot,
    my_next_overall,
    rounds,
    picks_made,
    recent_picks = [],
  } = draft

  const round = Math.floor((current_overall - 1) / num_teams) + 1
  const draftOver = picks_made >= num_teams * rounds
  const picksAway =
    my_next_overall != null ? my_next_overall - current_overall : null

  return (
    <header className="statusbar">
      <div className="status-left">
        <span className="pill">
          Round <b>{Math.min(round, rounds)}</b>
        </span>
        <span className="pill">
          Pick <b>#{Math.min(current_overall, num_teams * rounds)}</b>
        </span>
        {draftOver ? (
          <span className="clock done">Draft complete</span>
        ) : is_my_pick ? (
          <span className="clock you">🟢 You’re on the clock</span>
        ) : (
          <span className="clock">
            On the clock: Team {on_the_clock}
          </span>
        )}
        {!draftOver && !is_my_pick && (
          <span className="pill subtle">
            Your next: <b>#{my_next_overall}</b>
            {picksAway != null && <> ({picksAway} away)</>}
          </span>
        )}
        <span className="pill subtle">You are Team {my_slot}</span>
      </div>

      <div className="status-right">
        {recent_picks[0] && (
          <span className="last-pick">
            Last:{' '}
            <span className={posClass(recent_picks[0].position)}>
              {recent_picks[0].position}
            </span>{' '}
            {recent_picks[0].name}
          </span>
        )}
        <button className="btn" onClick={onUndo} disabled={busy || picks_made === 0}>
          ↶ Undo
        </button>
        <button className="btn ghost" onClick={onReset} disabled={busy}>
          Reset
        </button>
      </div>
    </header>
  )
}
