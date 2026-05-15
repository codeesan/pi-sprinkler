<template>
  <div class="daily-view">
    <!-- Hero status card -->
    <v-card rounded="xl" elevation="0" color="primary" class="mb-4 pa-4">
      <!-- Greeting row: name + weather -->
      <v-row align="center" no-gutters class="mb-3">
        <!-- Left: greeting + date -->
        <v-col cols="12" sm="7">
          <div class="text-h5 font-weight-bold text-white">
            {{ greeting }}, {{ settings.name || 'there' }}!
          </div>
          <div class="text-caption mt-1" style="color: rgba(255,255,255,0.75)">
            {{ currentDate }}
          </div>
        </v-col>

        <!-- Right: compact weather -->
        <v-col cols="12" sm="5" class="d-flex justify-sm-end justify-start mt-3 mt-sm-0">
          <!-- No location set -->
          <div
            v-if="!settings.location.lat"
            class="d-flex align-center gap-2"
            style="color: rgba(255,255,255,0.6)"
          >
            <v-icon icon="mdi-map-marker-off" size="22" />
            <span class="text-caption">No location set</span>
          </div>

          <!-- Loading -->
          <div v-else-if="weather.loading" class="d-flex align-center gap-2">
            <v-progress-circular indeterminate color="white" size="20" width="2" />
            <span class="text-caption text-white" style="opacity: 0.75">Loading…</span>
          </div>

          <!-- Error -->
          <div
            v-else-if="weather.error"
            class="d-flex align-center gap-2"
            style="color: rgba(255,255,255,0.7)"
          >
            <v-icon icon="mdi-weather-cloudy-alert" size="24" />
            <span class="text-caption">Weather unavailable</span>
          </div>

          <!-- Weather data -->
          <div v-else class="d-flex align-center gap-2">
            <v-icon :icon="weather.icon" color="white" size="40" />
            <div>
              <div class="text-h6 font-weight-bold text-white">{{ weather.temperature }}°F</div>
              <div class="text-caption" style="color: rgba(255,255,255,0.75)">
                {{ weather.condition }}
              </div>
            </div>
          </div>
        </v-col>
      </v-row>

      <!-- Divider -->
      <v-divider style="border-color: rgba(255,255,255,0.2)" class="mb-3" />

      <!-- Status row -->
      <div class="mb-3">
        <!-- Actively running a schedule -->
        <template v-if="anyActive">
          <div class="text-caption font-weight-medium mb-2" style="color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 0.05em;">
            Running Schedule
          </div>
          <div class="text-subtitle-1 font-weight-bold text-white mb-2">
            {{ activeScheduleName }}
          </div>
          <div class="d-flex align-center gap-2 flex-wrap">
            <v-chip
              v-if="currentZone"
              color="white"
              variant="flat"
              size="small"
              style="color: #2E7D32;"
            >
              <v-icon start :icon="currentZone.icon" size="14" />
              Now: {{ currentZone.name }}
            </v-chip>
            <span
              v-if="currentZone"
              class="text-caption text-white"
              style="opacity: 0.85"
            >
              {{ currentZone.timeRemaining }} min left
            </span>
            <v-chip
              v-if="nextZone"
              color="white"
              variant="tonal"
              size="small"
              style="color: rgba(255,255,255,0.9)"
            >
              <v-icon start icon="mdi-arrow-right" size="14" />
              Next: {{ nextZone.name }}
            </v-chip>
          </div>
        </template>

        <!-- Idle: show next scheduled run -->
        <template v-else-if="nextScheduledRun">
          <div class="d-flex align-center gap-2 flex-wrap">
            <v-icon icon="mdi-calendar-clock" color="white" size="18" style="opacity: 0.8" />
            <span class="text-body-2 text-white">
              Next:
              <span class="font-weight-bold">{{ nextScheduledRun.schedule.name }}</span>
              at {{ formatTime(nextScheduledRun.date) }}
              &middot; {{ formatWeekday(nextScheduledRun.date) }}
            </span>
          </div>
        </template>

        <!-- Nothing scheduled -->
        <template v-else>
          <div class="d-flex align-center gap-2" style="color: rgba(255,255,255,0.7)">
            <v-icon icon="mdi-calendar-remove" size="18" />
            <span class="text-body-2">No upcoming schedules</span>
          </div>
        </template>
      </div>

      <!-- Action buttons -->
      <div class="d-flex gap-2 flex-wrap">
        <!-- Idle state -->
        <template v-if="!anyActive">
          <!-- Multiple schedules: show menu -->
          <v-menu v-if="schedules.length > 1">
            <template #activator="{ props: menuProps }">
              <v-btn
                color="white"
                variant="elevated"
                prepend-icon="mdi-play"
                rounded="pill"
                style="color: #2E7D32;"
                v-bind="menuProps"
              >
                Run Schedule
              </v-btn>
            </template>
            <v-list rounded="xl" elevation="4" min-width="200">
              <v-list-subheader>Choose a schedule</v-list-subheader>
              <v-list-item
                v-for="schedule in schedules"
                :key="schedule.id"
                :title="schedule.name"
                :subtitle="`${schedule.zoneIds.length} zones`"
                prepend-icon="mdi-calendar-clock"
                rounded="lg"
                @click="handleRunSchedule(schedule.id)"
              />
            </v-list>
          </v-menu>

          <!-- Single schedule: direct run button -->
          <v-btn
            v-else-if="schedules.length === 1"
            color="white"
            variant="elevated"
            prepend-icon="mdi-play"
            rounded="pill"
            style="color: #2E7D32;"
            @click="handleRunSchedule(schedules[0].id)"
          >
            Run {{ schedules[0].name }}
          </v-btn>

          <!-- No schedules -->
          <v-btn
            v-else
            color="white"
            variant="tonal"
            rounded="pill"
            disabled
          >
            No Schedules
          </v-btn>
        </template>

        <!-- Active state: pause/resume + stop -->
        <template v-else>
          <v-btn
            v-if="anyRunning"
            color="warning"
            variant="elevated"
            prepend-icon="mdi-pause"
            rounded="pill"
            size="small"
            @click="handlePauseSchedule"
          >
            Pause
          </v-btn>
          <v-btn
            v-else
            color="white"
            variant="elevated"
            prepend-icon="mdi-play"
            rounded="pill"
            size="small"
            style="color: #2E7D32;"
            @click="handleResumeAll"
          >
            Resume
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            prepend-icon="mdi-stop"
            rounded="pill"
            size="small"
            @click="handleStopAll"
          >
            Stop
          </v-btn>
        </template>
      </div>
    </v-card>

    <!-- Zone grid -->
    <div class="text-overline text-medium-emphasis mb-3 px-1">
      Zones ({{ zones.length }})
    </div>

    <v-row>
      <v-col
        v-for="zone in zones"
        :key="zone.id"
        cols="12"
        sm="6"
        lg="4"
      >
        <ZoneCard :zone="zone" @run="openRunDialog" />
      </v-col>
    </v-row>

    <div v-if="zones.length === 0" class="text-center py-16">
      <v-icon icon="mdi-water-off" size="64" color="secondary" class="mb-4" />
      <div class="text-h6 text-medium-emphasis">No zones configured yet</div>
      <div class="text-body-2 text-medium-emphasis mb-4">
        Head to Configuration to add your first zone.
      </div>
    </div>

    <ManualRunDialog
      v-model="runDialogOpen"
      :zone="selectedZone"
      @confirm="onManualRunConfirm"
    />

    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      rounded="pill"
      location="bottom"
      :timeout="3000"
    >
      <v-icon :icon="snackbar.icon" class="mr-2" />
      {{ snackbar.message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSprinklers, STATUS } from '../composables/useSprinklers'
import { useWeather } from '../composables/useWeather'
import { useSettings } from '../composables/useSettings'
import ZoneCard from '../components/ZoneCard.vue'
import ManualRunDialog from '../components/ManualRunDialog.vue'

const {
  state,
  anyRunning,
  anyActive,
  currentZone,
  nextZone,
  nextScheduledRun,
  runZone,
  runSchedule,
  pauseSchedule,
  resumeAll,
  stopAll,
} = useSprinklers()

const weather = useWeather()
const { settings } = useSettings()

const zones = computed(() => state.zones)
const schedules = computed(() => state.schedules.filter((s) => s.enabled))

const activeScheduleName = computed(() => {
  if (!state.activeScheduleId) return null
  return state.schedules.find((s) => s.id === state.activeScheduleId)?.name ?? null
})

// Greeting based on time of day
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
})

// Current date string (no live clock — date doesn't change mid-session)
const currentDate = new Date().toLocaleDateString('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
})

// Format helpers for next scheduled run
function formatTime(date) {
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

function formatWeekday(date) {
  return date.toLocaleDateString('en-US', { weekday: 'long' })
}

// Manual run dialog
const runDialogOpen = ref(false)
const selectedZone = ref(null)

function openRunDialog(zone) {
  selectedZone.value = zone
  runDialogOpen.value = true
}

async function onManualRunConfirm({ zone, duration }) {
  await runZone(zone.id, duration)
  if (state.error) {
    showSnack(state.error, 'error', 'mdi-alert')
    state.error = null
    return
  }
  showSnack(`${zone.name} started`, 'primary', 'mdi-water')
}

function handleRunSchedule(scheduleId) {
  const schedule = state.schedules.find((s) => s.id === scheduleId)
  runSchedule(scheduleId)
  showSnack(`Running "${schedule?.name}"`, 'primary', 'mdi-play')
}

function handlePauseSchedule() {
  pauseSchedule()
  showSnack('Schedule paused', 'warning', 'mdi-pause')
}

function handleResumeAll() {
  resumeAll()
  showSnack('All zones resumed', 'primary', 'mdi-play')
}

async function handleStopAll() {
  await stopAll()
  showSnack('All zones stopped', 'error', 'mdi-stop')
}

const snackbar = ref({ show: false, message: '', color: 'primary', icon: 'mdi-check' })

function showSnack(message, color = 'primary', icon = 'mdi-check') {
  snackbar.value = { show: true, message, color, icon }
}
</script>

<style scoped>
.daily-view {
  padding-bottom: 24px;
}
</style>
