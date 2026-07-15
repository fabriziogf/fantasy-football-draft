import { useState } from 'react'

export default function Setup({ config, onSetup, busy, error }) {
  const [slot, setSlot] = useState(1)
  const teams = config?.num_teams ?? 12

  const submit = (e) => {
    e.preventDefault()
    onSetup({ my_slot: Number(slot) })
  }

  return (
    <div className="app-center">
      <form className="card setup-card" onSubmit={submit}>
        <h1>Draft Assistant</h1>
        <p className="muted">
          {teams}-team · PPR · snake. Set your draft slot to begin.
        </p>
        <label>
          Your draft slot
          <select value={slot} onChange={(e) => setSlot(e.target.value)}>
            {Array.from({ length: teams }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>
                Pick {n}
              </option>
            ))}
          </select>
        </label>
        {error && <div className="banner error">{error}</div>}
        <button className="btn primary" disabled={busy} type="submit">
          {busy ? 'Starting…' : 'Start draft'}
        </button>
      </form>
    </div>
  )
}
