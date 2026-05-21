import { reactive } from 'vue'

const API_BASE = `http://${window.location.hostname}:8000`
const STORAGE_KEY = 'sprinkler_settings'

const defaultSettings = {
  name: '',
  location: { city: '', lat: null, lon: null },
  rain_delay_enabled: false,
  rain_delay_threshold: 50,
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { ...defaultSettings, ...JSON.parse(raw) }
  } catch {
    // ignore
  }
  return { ...defaultSettings }
}

// Initialise from localStorage immediately so UI has values on first render
const settings = reactive(loadFromStorage())

// Then sync from the API and keep localStorage as a cache
async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/settings`)
    if (!res.ok) return
    const data = await res.json()
    settings.name = data.name ?? ''
    Object.assign(settings.location, data.location ?? {})
    settings.rain_delay_enabled = data.rain_delay_enabled ?? false
    settings.rain_delay_threshold = data.rain_delay_threshold ?? 50
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch {
    // API unreachable — localStorage values remain
  }
}

async function saveSettings(updates) {
  if (updates.location) Object.assign(settings.location, updates.location)
  if ('name' in updates) settings.name = updates.name

  // Persist to localStorage immediately (fast)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))

  // Then persist to backend (survives across browsers/devices)
  try {
    await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: settings.name,
        location: { ...settings.location },
      }),
    })
  } catch {
    // Backend unreachable — localStorage copy still saved
  }
}

// Load from API on module init
loadSettings()

export function useSettings() {
  return { settings, saveSettings }
}
