import { reactive, computed } from 'vue'

const API_BASE = `http://${window.location.hostname}:8000`

export const STATUS = {
  IDLE: 'idle',
  RUNNING: 'running',
  PAUSED: 'paused',
  ERROR: 'error',
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (res.status === 204) return null
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try { detail = (await res.json()).detail ?? detail } catch {}
    throw new Error(detail)
  }
  return res.json()
}

function hydrateZone(zone) {
  return { ...zone, status: STATUS.IDLE, timeRemaining: 0 }
}

// Shared singleton state — all components share this instance
const state = reactive({
  zones: [],
  schedules: [],
  loading: false,
  error: null,
  activeScheduleId: null,
  activeScheduleZoneIndex: 0,
})

async function initialize() {
  state.loading = true
  state.error = null
  try {
    const [zones, schedules] = await Promise.all([
      apiFetch('/zones'),
      apiFetch('/schedules'),
    ])
    state.zones = zones.map(hydrateZone)
    state.schedules = schedules
  } catch {
    state.error = 'Could not load data from server'
  } finally {
    state.loading = false
  }
}

// --- Status polling ---
let _pollTimer = null

function startStatusPolling() {
  if (_pollTimer) return // already polling
  _pollTimer = setInterval(async () => {
    try {
      const status = await apiFetch('/system/status')
      _applyStatus(status)
    } catch {
      // backend unreachable — leave state as-is
    }
  }, 5000)
}

function stopStatusPolling() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null }
}

function _applyStatus(status) {
  if (!status.any_running) {
    // Nothing running — set all zones to idle
    state.zones.forEach(z => {
      z.status = STATUS.IDLE
      z.timeRemaining = 0
    })
    state.activeScheduleId = null
    state.activeScheduleZoneIndex = 0
    return
  }

  const { running_zone, active_schedule } = status

  // Mark each zone correctly
  state.zones.forEach(z => {
    if (z.id === running_zone.zone_id) {
      z.status = STATUS.RUNNING
      z.timeRemaining = Math.ceil(running_zone.time_remaining_sec / 60)
    } else if (z.status === STATUS.RUNNING) {
      // This zone was running locally but backend says it's not — correct it
      z.status = STATUS.IDLE
      z.timeRemaining = 0
    }
  })

  // Sync active schedule state
  if (active_schedule) {
    state.activeScheduleId = active_schedule.schedule_id
    state.activeScheduleZoneIndex = active_schedule.zone_index
  } else {
    state.activeScheduleId = null
    state.activeScheduleZoneIndex = 0
  }
}

// Load on first import, then begin polling
initialize()
startStatusPolling()

export function useSprinklers() {
  // --- Computed ---
  const anyRunning = computed(() =>
    state.zones.some((z) => z.status === STATUS.RUNNING)
  )

  const anyActive = computed(() =>
    state.zones.some((z) => z.status === STATUS.RUNNING || z.status === STATUS.PAUSED)
  )

  const currentZone = computed(() => {
    if (!state.activeScheduleId) return null
    const schedule = state.schedules.find((s) => s.id === state.activeScheduleId)
    if (!schedule) return null
    const zoneId = schedule.zoneIds[state.activeScheduleZoneIndex]
    return state.zones.find((z) => z.id === zoneId) ?? null
  })

  const DAY_MAP = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }

  const nextScheduledRun = computed(() => {
    const enabled = state.schedules.filter((s) => s.enabled && s.zoneIds.length > 0)
    if (!enabled.length) return null

    const now = new Date()
    let best = null

    for (const schedule of enabled) {
      for (const timeStr of schedule.startTimes) {
        const [h, m] = timeStr.split(':').map(Number)
        for (const dayAbbr of schedule.days) {
          const targetDay = DAY_MAP[dayAbbr]
          if (targetDay === undefined) continue
          let daysAhead = (targetDay - now.getDay() + 7) % 7
          if (
            daysAhead === 0 &&
            (now.getHours() > h || (now.getHours() === h && now.getMinutes() >= m))
          ) {
            daysAhead = 7
          }
          const candidate = new Date(now)
          candidate.setDate(now.getDate() + daysAhead)
          candidate.setHours(h, m, 0, 0)
          if (!best || candidate < best.date) {
            best = { schedule, date: candidate }
          }
        }
      }
    }
    return best
  })

  const nextZone = computed(() => {
    if (!state.activeScheduleId) return null
    const schedule = state.schedules.find((s) => s.id === state.activeScheduleId)
    if (!schedule) return null
    const nextId = schedule.zoneIds[state.activeScheduleZoneIndex + 1]
    if (!nextId) return null
    return state.zones.find((z) => z.id === nextId) ?? null
  })

  // --- Zone CRUD ---
  async function addZone(zone) {
    try {
      const created = await apiFetch('/zones', {
        method: 'POST',
        body: JSON.stringify(zone),
      })
      state.zones.push(hydrateZone(created))
    } catch {
      state.error = 'Failed to add zone'
    }
  }

  async function updateZone(id, updates) {
    const zone = state.zones.find((z) => z.id === id)
    if (!zone) return
    const prev = { ...zone }
    Object.assign(zone, updates)
    try {
      const { id: _id, status: _s, timeRemaining: _tr, ...body } = zone
      const updated = await apiFetch(`/zones/${id}`, {
        method: 'PUT',
        body: JSON.stringify(body),
      })
      Object.assign(zone, updated)
    } catch {
      Object.assign(zone, prev)
      state.error = 'Failed to update zone'
    }
  }

  async function deleteZone(id) {
    try {
      await apiFetch(`/zones/${id}`, { method: 'DELETE' })
      const idx = state.zones.findIndex((z) => z.id === id)
      if (idx !== -1) state.zones.splice(idx, 1)
      state.schedules.forEach((s) => {
        const zIdx = s.zoneIds.indexOf(id)
        if (zIdx !== -1) s.zoneIds.splice(zIdx, 1)
      })
    } catch {
      state.error = 'Failed to delete zone'
    }
  }

  // --- Zone run controls ---
  async function runZone(zoneId, durationOverride) {
    const zone = state.zones.find((z) => z.id === zoneId)
    if (!zone) return
    const path = durationOverride
      ? `/zones/${zoneId}/run?duration_minutes=${durationOverride}`
      : `/zones/${zoneId}/run`
    await apiFetch(path, { method: 'POST' })
    zone.status = STATUS.RUNNING
    zone.timeRemaining = durationOverride ?? zone.duration
  }

  async function stopZone(zoneId) {
    const zone = state.zones.find((z) => z.id === zoneId)
    if (!zone) return
    try {
      await apiFetch(`/zones/${zoneId}/stop`, { method: 'POST' })
      zone.status = STATUS.IDLE
      zone.timeRemaining = 0
    } catch {
      state.error = `Failed to stop zone`
    }
  }

  function pauseZone(zoneId) {
    const zone = state.zones.find((z) => z.id === zoneId)
    if (!zone) return
    if (zone.status === STATUS.RUNNING) zone.status = STATUS.PAUSED
    else if (zone.status === STATUS.PAUSED) zone.status = STATUS.RUNNING
  }

  // --- Schedule run controls ---
  async function runSchedule(scheduleId) {
    const schedule = state.schedules.find((s) => s.id === scheduleId)
    if (!schedule || !schedule.enabled) return
    try {
      await apiFetch(`/schedules/${scheduleId}/run`, { method: 'POST' })
      state.activeScheduleId = scheduleId
      state.activeScheduleZoneIndex = 0
    } catch (e) {
      state.error = e.message || 'Failed to start schedule'
      throw e
    }
  }

  function pauseSchedule() {
    state.zones.forEach((zone) => {
      if (zone.status === STATUS.RUNNING) zone.status = STATUS.PAUSED
    })
  }

  async function stopAll() {
    try {
      await apiFetch('/valves/stop-all', { method: 'POST' })
    } catch {
      state.error = 'Failed to stop all valves'
    } finally {
      state.activeScheduleId = null
      state.activeScheduleZoneIndex = 0
      state.zones.forEach((zone) => {
        zone.status = STATUS.IDLE
        zone.timeRemaining = 0
      })
    }
  }

  function resumeAll() {
    state.zones.forEach((zone) => {
      if (zone.status === STATUS.PAUSED) zone.status = STATUS.RUNNING
    })
  }

  // --- Schedule CRUD ---
  async function addSchedule(schedule) {
    try {
      const created = await apiFetch('/schedules', {
        method: 'POST',
        body: JSON.stringify(schedule),
      })
      state.schedules.push(created)
    } catch {
      state.error = 'Failed to add schedule'
    }
  }

  async function updateSchedule(id, updates) {
    const schedule = state.schedules.find((s) => s.id === id)
    if (!schedule) return
    const prev = {
      ...schedule,
      days: [...schedule.days],
      startTimes: [...schedule.startTimes],
      zoneIds: [...schedule.zoneIds],
    }
    Object.assign(schedule, updates)
    try {
      const { id: _id, ...body } = schedule
      const updated = await apiFetch(`/schedules/${id}`, {
        method: 'PUT',
        body: JSON.stringify(body),
      })
      Object.assign(schedule, updated)
    } catch {
      Object.assign(schedule, prev)
      state.error = 'Failed to update schedule'
    }
  }

  async function deleteSchedule(id) {
    try {
      await apiFetch(`/schedules/${id}`, { method: 'DELETE' })
      const idx = state.schedules.findIndex((s) => s.id === id)
      if (idx !== -1) state.schedules.splice(idx, 1)
      if (state.activeScheduleId === id) state.activeScheduleId = null
    } catch {
      state.error = 'Failed to delete schedule'
    }
  }

  return {
    state,
    anyRunning,
    anyActive,
    currentZone,
    nextZone,
    nextScheduledRun,
    initialize,
    addZone,
    updateZone,
    deleteZone,
    runZone,
    stopZone,
    pauseZone,
    runSchedule,
    pauseSchedule,
    stopAll,
    resumeAll,
    addSchedule,
    updateSchedule,
    deleteSchedule,
    startStatusPolling,
    stopStatusPolling,
    STATUS,
  }
}
