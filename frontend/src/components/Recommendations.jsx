import { posClass, fmt } from './common.js'

export default function Recommendations({ recs, onPick, busy }) {
  if (!recs) return <div className="muted pad">Loading…</div>
  const { recommendations = [], is_my_pick } = recs

  return (
    <section className="recs">
      <div className="recs-head">
        <h2>Best available</h2>
        {is_my_pick ? (
          <span className="tag you">Your pick — draft one below</span>
        ) : (
          <span className="tag subtle">
            Not your pick — targets for your next turn
          </span>
        )}
      </div>

      {recommendations.length === 0 && (
        <div className="muted pad">No players available.</div>
      )}

      <ol className="rec-list">
        {recommendations.map((r, i) => (
          <li key={r.key} className={i === 0 ? 'rec top' : 'rec'}>
            <div className="rec-rank">{i + 1}</div>
            <div className="rec-body">
              <div className="rec-line1">
                <span className={posClass(r.position)}>
                  {r.position}
                  {r.pos_rank}
                </span>
                <span className="rec-name">{r.name}</span>
                <span className="rec-team">{r.team}</span>
                {r.bye && <span className="rec-bye">bye {r.bye}</span>}
                <span className="tier-chip">T{r.tier}</span>
              </div>
              <div className="rec-reason">{r.reason}</div>
              {(r.bye_conflict || (r.flags && r.flags.length > 0)) && (
                <div className="rec-flags">
                  {r.bye_conflict && (
                    <span className="flag bye" title={r.bye_conflict.label}>
                      ⚠ Bye {r.bye_conflict.bye} clash
                    </span>
                  )}
                  {r.flags.map((f) => (
                    <span key={f.code} className={`flag risk-${r.risk}`} title={f.label}>
                      {f.label}
                    </span>
                  ))}
                </div>
              )}
              <div className="rec-stats">
                <span title="Value over replacement">VOR {fmt(r.vor)}</span>
                <span title="Value over next available at your next pick">
                  VONA {fmt(r.vona)}
                </span>
                <span title="Average draft position">
                  ADP {r.adp ? fmt(r.adp, 1) : '—'}
                </span>
                <span title="Projected PPR points">{fmt(r.proj_points)} pts</span>
              </div>
            </div>
            <div className="rec-action">
              <div className="rec-score" title="Recommendation score">
                {fmt(r.score, 1)}
              </div>
              <button
                className="btn primary sm"
                disabled={busy}
                onClick={() => onPick(r.key)}
              >
                Draft
              </button>
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}
