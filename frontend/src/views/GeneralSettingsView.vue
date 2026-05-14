<template>
  <div>
    <!-- Display name card -->
    <v-card rounded="xl" elevation="0" class="mb-4 pa-4" color="surface">
      <div class="text-subtitle-1 font-weight-semibold text-primary mb-3 d-flex align-center gap-2">
        <v-icon icon="mdi-account-outline" color="primary" size="20" />
        Your Name
      </div>
      <v-text-field
        v-model="displayName"
        label="Your name"
        placeholder="e.g. Alex"
        variant="outlined"
        density="compact"
        rounded="lg"
        hide-details
        prepend-inner-icon="mdi-account"
        @blur="saveName"
      />
    </v-card>

    <v-card rounded="xl" elevation="0" class="mb-4 pa-4" color="surface">
      <div class="text-subtitle-1 font-weight-semibold text-primary mb-1 d-flex align-center gap-2">
        <v-icon icon="mdi-map-marker-outline" color="primary" size="20" />
        Location
      </div>
      <div v-if="settings.location.city" class="text-body-2 text-medium-emphasis mb-3">
        {{ settings.location.city }}
        <span class="text-caption ml-2">
          ({{ settings.location.lat?.toFixed(4) }}, {{ settings.location.lon?.toFixed(4) }})
        </span>
      </div>
      <div v-else class="text-body-2 text-medium-emphasis mb-3">
        No location saved yet.
      </div>

      <div class="d-flex gap-2 align-start">
        <v-text-field
          v-model="cityQuery"
          label="Search city"
          variant="outlined"
          density="compact"
          rounded="lg"
          hide-details
          prepend-inner-icon="mdi-magnify"
          class="flex-grow-1"
          @keyup.enter="searchCity"
        />
        <v-btn
          color="primary"
          variant="tonal"
          rounded="pill"
          :loading="searching"
          @click="searchCity"
        >
          Search
        </v-btn>
      </div>

      <v-alert
        v-if="searchError"
        type="error"
        variant="tonal"
        rounded="lg"
        density="compact"
        class="mt-3"
      >
        {{ searchError }}
      </v-alert>
    </v-card>

    <v-card
      v-if="results.length > 0"
      rounded="xl"
      elevation="0"
      color="surface"
    >
      <v-list lines="two" rounded="xl">
        <v-list-subheader>Select a location</v-list-subheader>
        <v-list-item
          v-for="(result, i) in results"
          :key="i"
          :title="result.name"
          :subtitle="[result.admin1, result.country].filter(Boolean).join(', ')"
          prepend-icon="mdi-map-marker"
          rounded="lg"
          class="mx-2 mb-1"
          @click="selectResult(result)"
        />
      </v-list>
    </v-card>

    <v-snackbar
      v-model="saved"
      color="primary"
      rounded="pill"
      location="bottom"
      :timeout="2500"
    >
      <v-icon icon="mdi-check" class="mr-2" />
      Location saved
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useSettings } from '../composables/useSettings'

const { settings, saveSettings } = useSettings()

// Display name
const displayName = ref(settings.name)

function saveName() {
  saveSettings({ name: displayName.value.trim() })
}

const cityQuery = ref('')
const results = ref([])
const searching = ref(false)
const searchError = ref(null)
const saved = ref(false)

async function searchCity() {
  const query = cityQuery.value.trim()
  if (!query) return
  searching.value = true
  searchError.value = null
  results.value = []
  try {
    const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=5&language=en&format=json`
    const res = await fetch(url)
    const data = await res.json()
    results.value = data.results ?? []
    if (results.value.length === 0) searchError.value = 'No locations found.'
  } catch {
    searchError.value = 'Search failed. Check your connection.'
  } finally {
    searching.value = false
  }
}

function selectResult(result) {
  saveSettings({
    location: {
      city: [result.name, result.admin1, result.country].filter(Boolean).join(', '),
      lat: result.latitude,
      lon: result.longitude,
    },
  })
  results.value = []
  cityQuery.value = ''
  saved.value = true
}
</script>
