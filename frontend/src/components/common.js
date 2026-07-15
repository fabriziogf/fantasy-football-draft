// Shared position styling used across components.
export const POS_ORDER = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']

export const posClass = (pos) => `pos pos-${(pos || '').toLowerCase()}`

export const fmt = (v, digits = 0) =>
  v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(digits)
