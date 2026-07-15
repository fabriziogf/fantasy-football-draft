import { useCallback, useEffect, useState } from 'react'
import * as api from './api.js'
import Setup from './components/Setup.jsx'
import StatusBar from './components/StatusBar.jsx'
import Recommendations from './components/Recommendations.jsx'
import Roster from './components/Roster.jsx'
import PlayerSearch from './components/PlayerSearch.jsx'
import TierBoard from './components/TierBoard.jsx'

export default function App() {
  const [config, setConfig] = useState(null)
  const [draft, setDraft] = useState(null)
  const [recs, setRecs] = useState(null)
  const [board, setBoard] = useState([])
  const [view, setView] = useState('recommend')
  const [needsSetup, setNeedsSetup] = useState(false)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [initializing, setInitializing] = useState(true)

  const refreshAll = useCallback(async () => {
    const [state, rec, avail] = await Promise.all([
      api.getState(),
      api.getRecommendations(12),
      api.getBoard({ available_only: true, limit: 400 }),
    ])
    setDraft(state)
    setRecs(rec)
    setBoard(avail)
    setNeedsSetup(false)
  }, [])

  useEffect(() => {
    ;(async () => {
      try {
        setConfig(await api.getConfig())
        await refreshAll()
      } catch (e) {
        if (e.status === 409) setNeedsSetup(true)
        else setError(e.message)
      } finally {
        setInitializing(false)
      }
    })()
  }, [refreshAll])

  const withBusy = async (fn) => {
    setBusy(true)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const doSetup = (body) =>
    withBusy(async () => {
      await api.setup(body)
      await refreshAll()
    })
  const doPick = (key) =>
    withBusy(async () => {
      await api.pick(key)
      await refreshAll()
    })
  const doUndo = () =>
    withBusy(async () => {
      await api.undo()
      await refreshAll()
    })

  if (initializing) {
    return (
      <div className="app-center">
        <div className="muted">Loading draft board…</div>
      </div>
    )
  }

  if (error && !draft && !needsSetup) {
    return (
      <div className="app-center">
        <div className="card error-card">
          <h2>Can’t reach the draft server</h2>
          <p>{error}</p>
          <p className="muted">
            Start the backend: <code>uvicorn backend.api.app:app --reload</code>
          </p>
        </div>
      </div>
    )
  }

  if (needsSetup || !draft) {
    return <Setup config={config} onSetup={doSetup} busy={busy} error={error} />
  }

  return (
    <div className="app">
      <StatusBar
        draft={draft}
        onUndo={doUndo}
        onReset={() => setNeedsSetup(true)}
        busy={busy}
      />
      {error && <div className="banner error">{error}</div>}
      <div className="layout">
        <main className="main">
          <div className="tabs">
            <button
              className={view === 'recommend' ? 'tab active' : 'tab'}
              onClick={() => setView('recommend')}
            >
              Recommendations
            </button>
            <button
              className={view === 'board' ? 'tab active' : 'tab'}
              onClick={() => setView('board')}
            >
              Tier Board
            </button>
          </div>
          <PlayerSearch board={board} onPick={doPick} busy={busy} />
          {view === 'recommend' ? (
            <Recommendations recs={recs} onPick={doPick} busy={busy} />
          ) : (
            <TierBoard board={board} onPick={doPick} busy={busy} />
          )}
        </main>
        <aside className="side">
          <Roster config={config} draft={draft} />
        </aside>
      </div>
    </div>
  )
}
