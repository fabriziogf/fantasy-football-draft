import { POS_ORDER, posClass, fmt } from './common.js'

// Available players by position, split into tiers so cliffs are visible (FR-20).
export default function TierBoard({ board, onPick, busy }) {
  const byPos = {}
  for (const p of board) {
    ;(byPos[p.position] ||= []).push(p)
  }
  for (const pos of Object.keys(byPos)) {
    byPos[pos].sort((a, b) => a.pos_rank - b.pos_rank)
  }

  return (
    <section className="tierboard">
      {POS_ORDER.map((pos) => {
        const players = byPos[pos] || []
        return (
          <div className="tier-col" key={pos}>
            <div className="tier-col-head">
              <span className={posClass(pos)}>{pos}</span>
              <span className="muted">{players.length}</span>
            </div>
            <div className="tier-col-body">
              {players.slice(0, 40).map((p, i) => {
                const prev = players[i - 1]
                const cliff = prev && prev.tier !== p.tier
                return (
                  <div key={p.key}>
                    {cliff && <div className="tier-break">Tier {p.tier}</div>}
                    <button
                      className="tier-player"
                      disabled={busy}
                      onClick={() => onPick(p.key)}
                      title="Mark drafted"
                    >
                      <span className="tier-rank">{p.pos_rank}</span>
                      <span className="tier-name">{p.name}</span>
                      <span className="tier-team">{p.team}</span>
                      <span className="tier-vor">{fmt(p.vor)}</span>
                    </button>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </section>
  )
}
