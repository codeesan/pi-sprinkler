import { reactive, computed, watch } from 'vue'

// Status constants
export const STATUS = {
  IDLE: 'idle',
  RUNNING: 'running',
  PAUSED: 'paused',
  ERROR: 'error',
}

// Shared singleton state — all components share this instance
const state = reactive({
  zones: [
    {
      id: 'zone-1',
      name: 'Front Lawn Left',
      port: 1,
      duration: 15,
      status: STATUS.IDLE,
      timeRemaining: 0,
      icon: 'mdi-grass',
      color: 'secondary',
    },
    {
      id: 'zone-2',
      name: 'Front Lawn Right',
      port: 2,
      duration: 15,
      status: STATUS.IDLE,
      timeRemaining: 0,
      icon: 'mdi-grass',
      color: 'secondary',
    },
    {
      id: 'zone-3',
      name: 'Front Lawn Drip',
      port: 3,
      duration: 20,
      status: STATUS.RUNNING,
      timeRemaining: 12,
      icon: 'mdi-water',
      color: 'accent',
    },
    {
      id: 'zone-4',
      name: 'Back Yard',
      port: 4,
      duration: 20,
      status: STATUS.IDLE,
      timeRemaining: 0,
      icon: 'mdi-leaf',
      color: 'primary',
    },
    {
      id: 'zone-5',
      name: 'Rose Garden',
      port: 5,
      duration: 10,
      status: STATUS.PAUSED,
      timeRemaining: 7,
      icon: 'mdi-flower',
      color: 'error',
    },
  ],

  schedules: [
    {
      id: 'sched-1',
      name: 'Front Yard',
      days: ['Mon', 'Wed', 'Fri'],
      startTimes: ['06:00'],
      zoneIds: ['zone-1', 'zone-2', 'zone-3'],
      enabled: true,
    },
    {
      id: 'sched-2',
      name: 'Back Yard',
      days: ['Tue', 'Thu', 'Sat'],
      startTimes: ['07:00'],
      zoneIds: ['zone-4', 'zone-5'],
      enabled: true,
    },
  ],

  activeScheduleId: null,
  activeScheduleZoneIndex: 0,
  nextZoneNum: 6,
  nextSchedNum: 3,
})

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
          // If it's today but the time has already passed, skip to next week
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
    return best // { schedule, date }
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
  function addZone(zone) {
    const id = `zone-${state.nextZoneNum++}`
    state.zones.push({
      id,
      name: zone.name,
      port: zone.port,
      duration: zone.duration,
      status: STATUS.IDLE,
      timeRemaining: 0,
      icon: zone.icon || 'mdi-water',
      color: zone.color || 'primary',
    })
  }

  function updateZone(id, updates) {
    const zone = state.zones.find((z) => z.id === id)
    if (zone) Object.assign(zone, updates)
  }

  function deleteZone(id) {
    const idx = state.zones.findIndex((z) => z.id === id)
    if (idx !== -1) state.zones.splice(idx, 1)
    // Remove this zone from any schedules that reference it
    state.schedules.forEach((s) => {
      const zIdx = s.zoneIds.indexOf(id)
      if (zIdx !== -1) s.zoneIds.splice(zIdx, 1)
    })
  }

  // --- Zone run controls ---
  function runZone(zoneId, durationOverride) {
    const zone = state.zones.find((z) => z.id === zoneId)
    if (!zone) return
    zone.status = STATUS.RUNNING
    zone.timeRemaining = durationOverride ?? zone.duration
  }

  function stopZone(zoneId) {
    const zone = state.zones.find((z) => z.id === zoneId)
    if (!zone) return
    zone.status = STATUS.IDLE
    zone.timeRemaining = 0
  }

  function pauseZone(zoneId) {
    const zone = state.zones.find((z) => z.id === zoneId)
    if (!zone) return
    if (zone.status === STATUS.RUNNING) zone.status = STATUS.PAUSED
    else if (zone.status === STATUS.PAUSED) zone.status = STATUS.RUNNING
  }

  // --- Schedule run controls ---
  function runSchedule(scheduleId) {
    const schedule = state.schedules.find((s) => s.id === scheduleId)
    if (!schedule || !schedule.enabled) return
    state.activeScheduleId = scheduleId
    state.activeScheduleZoneIndex = 0
    const firstZoneId = schedule.zoneIds[0]
    if (firstZoneId) {
      const zone = state.zones.find((z) => z.id === firstZoneId)
      if (zone) {
        zone.status = STATUS.RUNNING
        zone.timeRemaining = zone.duration
      }
    }
  }

  function pauseSchedule() {
    state.zones.forEach((zone) => {
      if (zone.status === STATUS.RUNNING) zone.status = STATUS.PAUSED
    })
  }

  function stopAll() {
    state.activeScheduleId = null
    state.activeScheduleZoneIndex = 0
    state.zones.forEach((zone) => {
      zone.status = STATUS.IDLE
      zone.timeRemaining = 0
    })
  }

  function resumeAll() {
    state.zones.forEach((zone) => {
      if (zone.status === STATUS.PAUSED) zone.status = STATUS.RUNNING
    })
  }

  // --- Schedule CRUD ---
  function addSchedule(schedule) {
    const id = `sched-${state.nextSchedNum++}`
    state.schedules.push({
      id,
      name: schedule.name,
      days: [...schedule.days],
      startTimes: [...schedule.startTimes],
      zoneIds: [...schedule.zoneIds],
      enabled: schedule.enabled ?? true,
    })
  }

  function updateSchedule(id, updates) {
    const schedule = state.schedules.find((s) => s.id === id)
    if (schedule) Object.assign(schedule, updates)
  }

  function deleteSchedule(id) {
    const idx = state.schedules.findIndex((s) => s.id === id)
    if (idx !== -1) state.schedules.splice(idx, 1)
    if (state.activeScheduleId === id) state.activeScheduleId = null
  }

  return {
    state,
    anyRunning,
    anyActive,
    currentZone,
    nextZone,
    nextScheduledRun,
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
    STATUS,
  }
}
