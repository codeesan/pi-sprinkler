<template>
  <v-card rounded="xl" elevation="2" class="zone-card">
    <!-- Running pulse border -->
    <div v-if="zone.status === STATUS.RUNNING" class="running-border" />

    <v-card-item>
      <template #prepend>
        <v-avatar
          :color="zone.status === STATUS.RUNNING ? 'primary' : 'surface'"
          :class="zone.status === STATUS.RUNNING ? 'running-avatar' : ''"
          size="48"
        >
          <v-icon
            :icon="zone.icon"
            :color="zone.status === STATUS.RUNNING ? 'white' : zone.color"
            size="26"
          />
        </v-avatar>
      </template>

      <v-card-title class="text-body-1 font-weight-bold">{{ zone.name }}</v-card-title>
      <v-card-subtitle class="text-caption">
        Port {{ zone.port }} &middot; {{ effectiveDuration }} min
      </v-card-subtitle>

      <template #append>
        <StatusChip :status="zone.status" />
      </template>
    </v-card-item>

    <!-- Progress bar for running/paused zones -->
    <div v-if="zone.status === STATUS.RUNNING || zone.status === STATUS.PAUSED" class="px-4 pb-2">
      <div class="d-flex justify-space-between text-caption text-medium-emphasis mb-1">
        <span>{{ zone.timeRemaining }} min remaining</span>
        <span>{{ effectiveDuration }} min total</span>
      </div>
      <v-progress-linear
        :model-value="progressPercent"
        :color="zone.status === STATUS.PAUSED ? 'warning' : 'primary'"
        bg-color="surface-variant"
        rounded
        height="6"
      />
    </div>

    <v-card-actions class="px-4 pb-4 pt-1 gap-2">
      <!-- Run / Pause / Stop controls -->
      <template v-if="zone.status === STATUS.IDLE">
        <v-btn
          variant="tonal"
          color="primary"
          prepend-icon="mdi-play"
          size="small"
          rounded="pill"
          @click="$emit('run', zone)"
        >
          Run
        </v-btn>
      </template>

      <template v-else-if="zone.status === STATUS.RUNNING">
        <v-btn
          variant="tonal"
          color="warning"
          prepend-icon="mdi-pause"
          size="small"
          rounded="pill"
          @click="onPause"
        >
          Pause
        </v-btn>
        <v-btn
          variant="text"
          color="error"
          prepend-icon="mdi-stop"
          size="small"
          rounded="pill"
          @click="onStop"
        >
          Stop
        </v-btn>
      </template>

      <template v-else-if="zone.status === STATUS.PAUSED">
        <v-btn
          variant="tonal"
          color="primary"
          prepend-icon="mdi-play"
          size="small"
          rounded="pill"
          @click="onPause"
        >
          Resume
        </v-btn>
        <v-btn
          variant="text"
          color="error"
          prepend-icon="mdi-stop"
          size="small"
          rounded="pill"
          @click="onStop"
        >
          Stop
        </v-btn>
      </template>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import { useSprinklers, STATUS } from '../composables/useSprinklers'
import StatusChip from './StatusChip.vue'

const props = defineProps({
  zone: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['run'])

const { pauseZone, stopZone } = useSprinklers()

const effectiveDuration = computed(() => props.zone.duration)

const progressPercent = computed(() => {
  const total = effectiveDuration.value
  if (!total) return 0
  return ((total - props.zone.timeRemaining) / total) * 100
})

function onPause() {
  pauseZone(props.zone.id)
}

function onStop() {
  stopZone(props.zone.id)
}
</script>

<style scoped>
.zone-card {
  position: relative;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.zone-card:hover {
  box-shadow: 0 4px 16px rgba(46, 125, 50, 0.15) !important;
}

.running-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #2E7D32, #66BB6A, #29B6F6, #66BB6A, #2E7D32);
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}

.running-avatar {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
