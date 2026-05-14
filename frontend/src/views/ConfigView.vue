<template>
  <div>
    <v-tabs
      v-model="activeTab"
      color="primary"
      bg-color="transparent"
      class="mb-5"
      grow
    >
      <v-tab value="general" prepend-icon="mdi-cog-outline" rounded="pill">
        General
      </v-tab>
      <v-tab value="zones" prepend-icon="mdi-water" rounded="pill">
        Zones
      </v-tab>
      <v-tab value="schedules" prepend-icon="mdi-calendar-clock" rounded="pill">
        Schedules
      </v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <v-window-item value="general">
        <GeneralSettingsView />
      </v-window-item>
      <v-window-item value="zones">
        <ZoneConfigView />
      </v-window-item>
      <v-window-item value="schedules">
        <ScheduleConfigView />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import GeneralSettingsView from './GeneralSettingsView.vue'
import ZoneConfigView from './ZoneConfigView.vue'
import ScheduleConfigView from './ScheduleConfigView.vue'

const activeTab = ref('general')
</script>
