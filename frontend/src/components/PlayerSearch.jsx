import { useMemo, useState } from 'react'
import { posClass, fmt } from './common.js'

// Fast way to mark ANY pick (yours or an opponent's): type a name, click to draft.
export default function PlayerSearch({ board, onPick, busy }) {
  const [q, setQ] = useState('')
  const query = q.trim().toLowerCase()

  const matches = useMemo(() => {
    if (!query) return []
    return board
      .filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          (p.team || '').toLowerCase().includes(query) ||
          (p.position || '').toLowerCase() === query,
      )
      .slice(0, 8)
  }, [board, query])

  const draft = (key) => {
    onPick(key)
    setQ('')
  }

  return (
    <div className="search">
      <input
        className="search-input"
        placeholder="Mark a pick — search any player by name, team, or position…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      {matches.length > 0 && (
        <ul className="search-results">
          {matches.map((p) => (
            <li key={p.key}>
              <button
                className="search-row"
                disabled={busy}
                onClick={() => draft(p.key)}
              >
                <span className={posClass(p.position)}>
                  {p.position}
                  {p.pos_rank}
                </span>
                <span className="search-name">{p.name}</span>
                <span className="search-team">{p.team}</span>
                <span className="search-meta">
                  ADP {p.adp ? fmt(p.adp, 1) : '—'} · VOR {fmt(p.vor)}
                </span>
                <span className="search-take">Draft</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
