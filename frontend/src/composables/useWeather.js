import { reactive, watch } from 'vue'
import { useSettings } from './useSettings'

const API_BASE = `http://${window.location.hostname}:8000`

const state = reactive({
  temperature: null,
  weatherCode: null,
  condition: null,
  icon: null,
  precipitationToday: null,   // inches
  precipProbability: null,    // %
  rainLikely: false,
  loading: false,
  error: null,
})

let refreshTimer = null

async function fetchWeather() {
  state.loading = true
  state.error = null
  try {
    const res = await fetch(`${API_BASE}/weather`)
    if (res.status === 404) {
      // No location configured yet — not an error, just no data
      state.loading = false
      return
    }
    if (!res.ok) throw new Error(`Weather unavailable (${res.status})`)
    const d = await res.json()
    state.temperature        = d.temperature
    state.weatherCode        = d.weather_code
    state.condition          = d.condition
    state.icon               = d.icon
    state.precipitationToday = d.precipitation_today
    state.precipProbability  = d.precip_probability
    state.rainLikely         = d.rain_likely
  } catch (e) {
    state.error = e.message || 'Could not load weather'
  } finally {
    state.loading = false
  }
}

function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer)
  // Backend caches for 30 min — poll every 20 min so we're never stale by more than 50 min
  refreshTimer = setInterval(fetchWeather, 20 * 60 * 1000)
}

const { settings } = useSettings()

// Fetch once on load
fetchWeather()
startAutoRefresh()

// Re-fetch immediately when location changes (user just saved settings)
watch(
  () => ({ lat: settings.location.lat, lon: settings.location.lon }),
  ({ lat, lon }) => {
    if (lat != null && lon != null) fetchWeather()
  }
)

export function useWeather() {
  return state
}
