<template>
  <v-dialog
    :model-value="modelValue"
    :fullscreen="display.xs.value"
    max-width="420"
    rounded="xl"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card rounded="xl">
      <v-card-item class="pt-5">
        <template #prepend>
          <v-avatar color="primary" size="44">
            <v-icon icon="mdi-water" color="white" />
          </v-avatar>
        </template>
        <v-card-title>Run Zone Manually</v-card-title>
        <v-card-subtitle v-if="zone">{{ zone.name }} &middot; Port {{ zone.port }}</v-card-subtitle>
        <template #append>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            aria-label="Close dialog"
            @click="$emit('update:modelValue', false)"
          />
        </template>
      </v-card-item>

      <v-divider />

      <v-card-text class="pt-5">
        <p class="text-body-2 text-medium-emphasis mb-4">
          Start <strong>{{ zone?.name }}</strong> now. You can use the zone's default duration
          or override it for this run only.
        </p>

        <v-radio-group v-model="durationMode" color="primary">
          <v-radio
            label="Use default duration"
            value="default"
          />
          <v-radio
            label="Override duration for this run"
            value="override"
          />
        </v-radio-group>

        <v-expand-transition>
          <div v-if="durationMode === 'override'" class="mt-2">
            <v-slider
              v-model="overrideDuration"
              :min="1"
              :max="60"
              :step="1"
              color="primary"
              track-color="success"
              thumb-label="always"
              label="Duration (minutes)"
            >
              <template #thumb-label="{ modelValue }">
                {{ modelValue }}m
              </template>
            </v-slider>
            <div class="text-center text-h6 font-weight-bold text-primary mt-n2 mb-2">
              {{ overrideDuration }} minutes
            </div>
          </div>
        </v-expand-transition>

        <v-alert
          v-if="durationMode === 'default' && zone"
          type="info"
          variant="tonal"
          density="compact"
          icon="mdi-clock-outline"
          class="mt-2"
        >
          Will run for <strong>{{ zone.duration }} minutes</strong>
          (zone default)
        </v-alert>
      </v-card-text>

      <v-card-actions class="px-5 pb-5 gap-3">
        <v-btn
          variant="text"
          color="secondary"
          @click="$emit('update:modelValue', false)"
        >
          Cancel
        </v-btn>
        <v-spacer />
        <v-btn
          color="primary"
          variant="elevated"
          prepend-icon="mdi-play"
          rounded="pill"
          size="large"
          @click="confirm"
        >
          Start Now
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useDisplay } from 'vuetify'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  zone: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'confirm'])
const display = useDisplay()

const durationMode = ref('default')
const overrideDuration = ref(15)

// Reset state when dialog opens
watch(() => props.modelValue, (open) => {
  if (open && props.zone) {
    durationMode.value = 'default'
    overrideDuration.value = props.zone.duration
  }
})

function confirm() {
  const duration = durationMode.value === 'override' ? overrideDuration.value : null
  emit('confirm', { zone: props.zone, duration })
  emit('update:modelValue', false)
}
</script>
