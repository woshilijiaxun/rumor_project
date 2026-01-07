const LS_KEY = 'app_settings'

export const settingsStore = {
  key: LS_KEY,
  defaults() {
    return {
      uploadDefaultVisibility: 'private',
      filesDefaultFilter: 'all',
      filesPageSize: 20,

      identDefaultTopK: 10,
      identDefaultMaxEdges: 10000,
      identDefaultNonTopKGray: '0',
      identPollIntervalMs: 1000,
      identPollTimeoutMs: 600000
    }
  },
  load() {
    const base = this.defaults()
    try {
      const raw = localStorage.getItem(LS_KEY)
      if (!raw) return base
      const v = JSON.parse(raw)
      return { ...base, ...(v || {}) }
    } catch {
      return base
    }
  },
  save(prefs) {
    localStorage.setItem(LS_KEY, JSON.stringify(prefs || {}))
  }
}

