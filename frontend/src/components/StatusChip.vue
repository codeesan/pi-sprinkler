<template>
  <v-chip
    :color="chipColor"
    :prepend-icon="chipIcon"
    size="small"
    variant="tonal"
    label
  >
    {{ label }}
  </v-chip>
</template>

<script setup>
import { computed } from 'vue'
import { STATUS } from '../composables/useSprinklers'

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
})

const chipColor = computed(() => {
  switch (props.status) {
    case STATUS.RUNNING: return 'primary'
    case STATUS.PAUSED:  return 'warning'
    case STATUS.ERROR:   return 'error'
    default:             return 'secondary'
  }
})

const chipIcon = computed(() => {
  switch (props.status) {
    case STATUS.RUNNING: return 'mdi-water'
    case STATUS.PAUSED:  return 'mdi-pause-circle'
    case STATUS.ERROR:   return 'mdi-alert-circle'
    default:             return 'mdi-circle-outline'
  }
})

const label = computed(() => {
  switch (props.status) {
    case STATUS.RUNNING: return 'Running'
    case STATUS.PAUSED:  return 'Paused'
    case STATUS.ERROR:   return 'Error'
    default:             return 'Idle'
  }
})
</script>
