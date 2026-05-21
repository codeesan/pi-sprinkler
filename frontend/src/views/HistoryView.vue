<template>
  <div class="history-view">
    <!-- Toolbar row: event count + refresh -->
    <div class="d-flex align-center justify-space-between mb-4">
      <div class="text-body-2 text-medium-emphasis">
        <template v-if="!loading && events.length">
          {{ events.length }} event{{ events.length === 1 ? '' : 's' }}
        </template>
      </div>
      <v-btn
        variant="tonal"
        color="primary"
        size="small"
        prepend-icon="mdi-refresh"
        :loading="loading"
        rounded="xl"
        @click="fetchHistory"
      >
        Refresh
      </v-btn>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="d-flex justify-center align-center py-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <!-- Error state -->
    <v-alert
      v-else-if="error"
      type="error"
      rounded="xl"
      variant="tonal"
      class="mb-4"
      :text="error"
    />

    <!-- Empty state -->
    <v-card
      v-else-if="!events.length"
      rounded="xl"
      elevation="0"
      color="surface"
      class="pa-8 text-center"
    >
      <v-icon icon="mdi-history" size="56" color="secondary" class="mb-3" />
      <div class="text-h6 font-weight-medium text-primary mb-1">No history yet</div>
      <div class="text-body-2 text-medium-emphasis">
        Events will appear here once zones start running.
      </div>
    </v-card>

    <!-- Event list -->
    <div v-else>
      <template v-for="(group, gIdx) in groupedEvents" :key="gIdx">
        <!--
          Schedule group: a schedule_start card that wraps its zone children,
          followed by a schedule_complete entry at the same level.
        -->
        <template v-if="group.type === 'schedule'">
          <!-- Schedule start card -->
          <v-card rounded="xl" elevation="0" color="surface" class="mb-2 event-card">
            <v-card-text class="pa-4">
              <div class="d-flex align-start gap-3">
                <v-avatar :color="typeColor('schedule_start')" size="36" class="mt-1 flex-shrink-0">
                  <v-icon :icon="typeIcon('schedule_start')" size="18" color="white" />
                </v-avatar>
                <div class="flex-grow-1 min-width-0">
                  <div class="text-body-2 font-weight-medium text-on-surface">
                    {{ group.start.message }}
                  </div>
                  <div class="text-caption text-medium-emphasis mt-0-5">
                    {{ formatTimestamp(group.start.timestamp) }}
                  </div>
                </div>
              </div>

              <!-- Indented zone children -->
              <div v-if="group.zones.length" class="mt-3 ml-12">
                <div
                  v-for="(zone, zIdx) in group.zones"
                  :key="zIdx"
                  class="d-flex align-start gap-2 mb-2"
                >
                  <v-avatar :color="typeColor('schedule_zone_start')" size="28" class="mt-0-5 flex-shrink-0">
                    <v-icon :icon="typeIcon('schedule_zone_start')" size="14" color="white" />
                  </v-avatar>
                  <div>
                    <div class="text-body-2 text-on-surface">{{ zone.message }}</div>
                    <div class="text-caption text-medium-emphasis">
                      {{ formatTimestamp(zone.timestamp) }}
                    </div>
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Schedule complete card (same indent level as start) -->
          <v-card
            v-if="group.complete"
            rounded="xl"
            elevation="0"
            color="surface"
            class="mb-3 event-card"
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-start gap-3">
                <v-avatar :color="typeColor('schedule_complete')" size="36" class="mt-1 flex-shrink-0">
                  <v-icon :icon="typeIcon('schedule_complete')" size="18" color="white" />
                </v-avatar>
                <div class="flex-grow-1 min-width-0">
                  <div class="text-body-2 font-weight-medium text-on-surface">
                    {{ group.complete.message }}
                  </div>
                  <div class="text-caption text-medium-emphasis mt-0-5">
                    {{ formatTimestamp(group.complete.timestamp) }}
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </template>

        <!-- Standalone event -->
        <v-card
          v-else
          rounded="xl"
          elevation="0"
          color="surface"
          class="mb-2 event-card"
        >
          <v-card-text class="pa-4">
            <div class="d-flex align-start gap-3">
              <v-avatar :color="typeColor(group.event.type)" size="36" class="mt-1 flex-shrink-0">
                <v-icon :icon="typeIcon(group.event.type)" size="18" color="white" />
              </v-avatar>
              <div class="flex-grow-1 min-width-0">
                <div class="text-body-2 font-weight-medium text-on-surface">
                  {{ group.event.message }}
                </div>
                <div class="text-caption text-medium-emphasis mt-0-5">
                  {{ formatTimestamp(group.event.timestamp) }}
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// --- Data ---
const events = ref([])
const loading = ref(false)
const error = ref(null)

// --- Fetch ---
async function fetchHistory() {
  loading.value = true
  error.value = null
  try {
    const base = `http://${window.location.hostname}:8000`
    const res = await fetch(`${base}/history?limit=200`)
    if (!res.ok) throw new Error(`Server returned ${res.status}`)
    const data = await res.json()
    // Sort newest-first
    events.value = [...data].sort(
      (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
    )
  } catch (err) {
    error.value = `Could not load history: ${err.message}`
  } finally {
    loading.value = false
  }
}

onMounted(fetchHistory)

// --- Grouping ---
// Walk the events (already newest-first) and cluster schedule_zone_start events
// as children of their preceding schedule_start, and pair schedule_complete with
// the same schedule_start.  Everything else is a standalone event.
const groupedEvents = computed(() => {
  const groups = []
  // Work on a copy sorted oldest-first so grouping logic is easier, then reverse.
  const asc = [...events.value].sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
  )

  let scheduleGroup = null

  for (const ev of asc) {
    if (ev.type === 'schedule_start') {
      scheduleGroup = { type: 'schedule', start: ev, zones: [], complete: null }
      groups.push(scheduleGroup)
    } else if (ev.type === 'schedule_zone_start' && scheduleGroup) {
      scheduleGroup.zones.push(ev)
    } else if (ev.type === 'schedule_complete' && scheduleGroup) {
      scheduleGroup.complete = ev
      scheduleGroup = null
    } else {
      scheduleGroup = null
      groups.push({ type: 'standalone', event: ev })
    }
  }

  // Reverse so newest groups appear first
  return groups.reverse()
})

// --- Helpers ---
const TYPE_ICON = {
  system_start:          'mdi-power',
  zone_start:            'mdi-water',
  zone_stop:             'mdi-water-off',
  stop_all:              'mdi-stop-circle',
  schedule_start:        'mdi-calendar-clock',
  schedule_zone_start:   'mdi-sprinkler',
  schedule_complete:     'mdi-calendar-check',
  schedule_skipped_rain: 'mdi-weather-rainy',
}

const TYPE_COLOR = {
  system_start:          '#78909C', // blue-grey
  zone_start:            '#29B6F6', // accent / water blue
  zone_stop:             '#66BB6A', // secondary green
  stop_all:              '#EF5350', // error red
  schedule_start:        '#2E7D32', // primary green
  schedule_zone_start:   '#29B6F6', // accent / water blue
  schedule_complete:     '#A5D6A7', // success mint
  schedule_skipped_rain: '#F9A825', // amber — skipped, not an error
}

function typeIcon(type) {
  return TYPE_ICON[type] ?? 'mdi-circle-small'
}

function typeColor(type) {
  return TYPE_COLOR[type] ?? '#9E9E9E'
}

function formatTimestamp(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    month:  'short',
    day:    'numeric',
    year:   'numeric',
    hour:   'numeric',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.event-card {
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.mt-0-5 {
  margin-top: 2px;
}

.min-width-0 {
  min-width: 0;
}
</style>
