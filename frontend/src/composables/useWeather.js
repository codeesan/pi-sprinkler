import { reactive, watch } from 'vue'
import { useSettings } from './useSettings'

const WMO_MAP = [
  { codes: [0],             icon: 'mdi-weather-sunny',           label: 'Clear' },
  { codes: [1],             icon: 'mdi-weather-sunny',           label: 'Mostly Clear' },
  { codes: [2],             icon: 'mdi-weather-partly-cloudy',   label: 'Partly Cloudy' },
  { codes: [3],             icon: 'mdi-weather-cloudy',          label: 'Overcast' },
  { codes: [45, 48],        icon: 'mdi-weather-fog',             label: 'Foggy' },
  { codes: [51, 52, 53, 54, 55], icon: 'mdi-weather-rainy',     label: 'Drizzle' },
  { codes: [61, 62, 63, 64, 65], icon: 'mdi-weather-rainy',     label: 'Rain' },
  { codes: [66, 67],        icon: 'mdi-weather-snowy-rainy',     label: 'Freezing Rain' },
  { codes: [71, 72, 73, 74, 75, 77], icon: 'mdi-weather-snowy', label: 'Snow' },
  { codes: [80, 81, 82],   icon: 'mdi-weather-pouring',         label: 'Rain Showers' },
  { codes: [85, 86],        icon: 'mdi-weather-snowy',           label: 'Snow Showers' },
  { codes: [95],            icon: 'mdi-weather-lightning-rainy', label: 'Thunderstorm' },
  { codes: [96, 99],        icon: 'mdi-weather-lightning-rainy', label: 'Severe Thunderstorm' },
]

function resolveWmo(code) {
  const entry = WMO_MAP.find((e) => e.codes.includes(code))
  return entry ?? { icon: 'mdi-weather-cloudy', label: 'Unknown' }
}

const state = reactive({
  temperature: null,
  weatherCode: null,
  condition: null,
  icon: null,
  loading: false,
  error: null,
})

let refreshTimer = null

async function fetchWeather(lat, lon) {
  state.loading = true
  state.error = null
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&temperature_unit=fahrenheit`
    const res = await fetch(url)
    const data = await res.json()
    const cw = data.current_weather
    const wmo = resolveWmo(cw.weathercode)
    state.temperature = Math.round(cw.temperature)
    state.weatherCode = cw.weathercode
    state.condition = wmo.label
    state.icon = wmo.icon
  } catch (e) {
    state.error = 'Could not load weather'
  } finally {
    state.loading = false
  }
}

function startAutoRefresh(lat, lon) {
  if (refreshTimer) clearInterval(refreshTimer)
  refreshTimer = setInterval(() => fetchWeather(lat, lon), 30 * 60 * 1000)
}

const { settings } = useSettings()

function initWeather() {
  const { lat, lon } = settings.location
  if (lat != null && lon != null) {
    fetchWeather(lat, lon)
    startAutoRefresh(lat, lon)
  }
}

initWeather()

watch(
  () => ({ lat: settings.location.lat, lon: settings.location.lon }),
  ({ lat, lon }) => {
    if (lat != null && lon != null) {
      fetchWeather(lat, lon)
      startAutoRefresh(lat, lon)
    }
  }
)

export function useWeather() {
  return state
}
