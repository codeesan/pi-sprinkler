<template>
  <div class="schedule-editor pa-2">
    <!-- Days of week -->
    <div class="text-caption font-weight-medium text-medium-emphasis mb-2">Days of Week</div>
    <div class="d-flex flex-wrap gap-2 mb-5">
      <v-chip
        v-for="day in daysOfWeek"
        :key="day"
        :color="localDays.includes(day) ? 'primary' : 'default'"
        :variant="localDays.includes(day) ? 'elevated' : 'tonal'"
        size="default"
        class="day-chip"
        clickable
        @click="toggleDay(day)"
      >
        {{ day }}
      </v-chip>
    </div>

    <!-- Start Times -->
    <div class="d-flex align-center justify-space-between mb-2">
      <div class="text-caption font-weight-medium text-medium-emphasis">Start Times</div>
      <v-btn
        size="x-small"
        variant="tonal"
        color="primary"
        prepend-icon="mdi-plus"
        rounded="pill"
        @click="addTime"
      >
        Add Time
      </v-btn>
    </div>

    <div v-if="localTimes.length === 0" class="text-caption text-medium-emphasis mb-4 pa-3 rounded-lg bg-surface-variant">
      No start times. Click "Add Time" to schedule a watering time.
    </div>

    <div class="d-flex flex-column gap-2 mb-5">
      <div
        v-for="(time, idx) in localTimes"
        :key="idx"
        class="d-flex align-center gap-2"
      >
        <v-text-field
          :model-value="time"
          type="time"
          variant="outlined"
          density="compact"
          rounded="lg"
          hide-details
          class="flex-grow-1"
          @update:model-value="(v) => updateTime(idx, v)"
        />
        <v-btn
          icon="mdi-delete"
          variant="text"
          size="small"
          color="error"
          :aria-label="`Remove time ${time}`"
          @click="removeTime(idx)"
        />
      </div>
    </div>

    <!-- Duration override -->
    <div class="text-caption font-weight-medium text-medium-emphasis mb-2">Duration Override</div>
    <div class="d-flex align-center gap-3 mb-2">
      <v-switch
        v-model="useDurationOverride"
        color="primary"
        hide-details
        density="compact"
        :label="useDurationOverride ? `Override: ${localDuration} min` : `Zone default (${zone.duration} min)`"
        @update:model-value="onOverrideToggle"
      />
    </div>

    <v-expand-transition>
      <div v-if="useDurationOverride" class="mt-2 mb-4">
        <v-slider
          v-model="localDuration"
          :min="1"
          :max="60"
          :step="1"
          color="primary"
          track-color="success"
          thumb-label="always"
          hide-details
          @update:model-value="emitUpdate"
        >
          <template #thumb-label="{ modelValue }">
            {{ modelValue }}m
          </template>
        </v-slider>
      </div>
    </v-expand-transition>

    <!-- Save confirmation chip -->
    <div class="d-flex justify-end">
      <v-btn
        color="primary"
        variant="tonal"
        prepend-icon="mdi-check"
        size="small"
        rounded="pill"
        @click="emitUpdate"
      >
        Save Schedule
      </v-btn>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  zone: {
    type: Object,
    required: true,
  },
  schedule: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update'])

const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

// Local copies of schedule state
const localDays = ref([...(props.schedule?.days ?? [])])
const localTimes = ref([...(props.schedule?.startTimes ?? [])])
const useDurationOverride = ref(props.schedule?.durationOverride != null)
const localDuration = ref(props.schedule?.durationOverride ?? props.zone.duration)

// Sync when zone changes
watch(
  () => props.schedule,
  (s) => {
    if (!s) return
    localDays.value = [...s.days]
    localTimes.value = [...s.startTimes]
    useDurationOverride.value = s.durationOverride != null
    localDuration.value = s.durationOverride ?? props.zone.duration
  },
  { immediate: false }
)

function toggleDay(day) {
  const idx = localDays.value.indexOf(day)
  if (idx === -1) localDays.value.push(day)
  else localDays.value.splice(idx, 1)
}

function addTime() {
  localTimes.value.push('06:00')
}

function removeTime(idx) {
  localTimes.value.splice(idx, 1)
}

function updateTime(idx, val) {
  localTimes.value[idx] = val
}

function onOverrideToggle(val) {
  if (!val) emitUpdate()
}

function emitUpdate() {
  emit('update', {
    days: [...localDays.value],
    startTimes: [...localTimes.value],
    durationOverride: useDurationOverride.value ? localDuration.value : null,
  })
}
</script>

<style scoped>
.day-chip {
  min-width: 52px;
  justify-content: center;
  font-weight: 500;
}
</style>
