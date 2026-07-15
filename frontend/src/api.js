const BASE = '/api'

async function req(path, opts) {
  const r = await fetch(BASE + path, opts)
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }))
    const e = new Error(err.detail || r.statusText)
    e.status = r.status
    throw e
  }
  return r.status === 204 ? null : r.json()
}

const jsonPost = (path, body) =>
  req(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })

export const getConfig = () => req('/config')
export const getState = () => req('/state')
export const getBoard = (params = {}) => {
  const q = new URLSearchParams(params).toString()
  return req('/board' + (q ? `?${q}` : ''))
}
export const setup = (body) => jsonPost('/setup', body)
export const pick = (key) => jsonPost('/pick', { key })
export const undo = () => jsonPost('/undo')
export const getRecommendations = (limit = 12) => req(`/recommend?limit=${limit}`)
