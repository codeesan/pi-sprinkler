import { reactive } from 'vue'

const STORAGE_KEY = 'sprinkler_settings'

const defaultSettings = {
  name: '',
  location: { city: '', lat: null, lon: null },
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

const settings = reactive(loadFromStorage())

function saveSettings(updates) {
  if (updates.location) Object.assign(settings.location, updates.location)
  if ('name' in updates) settings.name = updates.name
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

export function useSettings() {
  return { settings, saveSettings }
}
