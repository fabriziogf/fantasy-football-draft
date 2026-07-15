import { posClass } from './common.js'

const STARTER_ORDER = ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'K', 'DST']
const FLEX_ELIGIBLE = new Set(['RB', 'WR', 'TE'])

// Greedily assign drafted players to starter slots, then bench.
function assignSlots(roster, benchCount) {
  const players = [...roster]
  const used = new Set()
  const take = (pred) => {
    const idx = players.findIndex((p, i) => !used.has(i) && pred(p))
    if (idx === -1) return null
    used.add(idx)
    return players[idx]
  }

  const starters = STARTER_ORDER.map((slot) => {
    const player =
      slot === 'FLEX'
        ? take((p) => FLEX_ELIGIBLE.has(p.position))
        : take((p) => p.position === slot)
    return { slot, player }
  })

  const bench = players.filter((_, i) => !used.has(i))
  const benchSlots = Array.from({ length: Math.max(benchCount, bench.length) }, (_, i) => ({
    slot: 'BE',
    player: bench[i] || null,
  }))

  return { starters, benchSlots }
}

function SlotRow({ slot, player }) {
  return (
    <div className={player ? 'slot filled' : 'slot empty'}>
      <span className="slot-label">{slot}</span>
      {player ? (
        <span className="slot-player">
          <span className={posClass(player.position)}>{player.position}</span>
          {player.name}
          <span className="slot-team">{player.team}</span>
        </span>
      ) : (
        <span className="slot-need">needed</span>
      )}
    </div>
  )
}

export default function Roster({ config, draft }) {
  const roster = draft.my_roster || []
  const { starters, benchSlots } = assignSlots(roster, config?.bench ?? 6)

  const counts = roster.reduce((acc, p) => {
    acc[p.position] = (acc[p.position] || 0) + 1
    return acc
  }, {})

  return (
    <div className="roster card">
      <div className="roster-head">
        <h2>My roster</h2>
        <span className="muted">{roster.length} picks</span>
      </div>
      <div className="pos-counts">
        {['QB', 'RB', 'WR', 'TE', 'K', 'DST'].map((p) => (
          <span key={p} className="count-chip">
            <span className={posClass(p)}>{p}</span>
            {counts[p] || 0}
          </span>
        ))}
      </div>
      <div className="slots">
        {starters.map((s, i) => (
          <SlotRow key={`s${i}`} {...s} />
        ))}
        <div className="bench-divider">Bench</div>
        {benchSlots.map((s, i) => (
          <SlotRow key={`b${i}`} {...s} />
        ))}
      </div>
    </div>
  )
}
