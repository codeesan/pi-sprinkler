<template>
  <v-app :theme="'sprinklerLight'">
    <!-- Desktop: Navigation Drawer -->
    <v-navigation-drawer
      v-if="!display.smAndDown.value"
      :model-value="true"
      permanent
      color="primary"
      width="220"
    >
      <!-- App brand -->
      <div class="px-4 pt-6 pb-4">
        <div class="d-flex align-center gap-2 mb-1">
          <v-icon icon="mdi-sprinkler" color="white" size="28" />
          <span class="text-h6 font-weight-bold text-white">Sprinklers</span>
        </div>
        <div class="text-caption" style="color: rgba(255,255,255,0.65)">Smart watering made easy</div>
      </div>

      <v-divider color="rgba(255,255,255,0.2)" class="mb-2" />

      <v-list nav density="compact" class="px-2">
        <v-list-item
          v-for="item in navItems"
          :key="item.view"
          :prepend-icon="item.icon"
          :title="item.label"
          :value="item.view"
          :active="activeView === item.view"
          active-color="white"
          rounded="xl"
          class="mb-1 nav-item"
          @click="activeView = item.view"
        />
      </v-list>

      <template #append>
        <div class="pa-4 text-caption" style="color: rgba(255,255,255,0.45)">
          v1.0 &middot; Mock data
        </div>
      </template>
    </v-navigation-drawer>

    <!-- App bar (mobile only) -->
    <v-app-bar
      v-if="display.smAndDown.value"
      color="primary"
      elevation="0"
      flat
    >
      <template #prepend>
        <v-icon icon="mdi-sprinkler" color="white" size="26" class="ml-2" />
      </template>
      <v-app-bar-title class="text-white font-weight-bold">Sprinklers</v-app-bar-title>
    </v-app-bar>

    <!-- Main content -->
    <v-main style="background-color: #F1F8E9; min-height: 100vh;">
      <v-container
        fluid
        class="pa-4 pa-sm-6"
        style="max-width: 960px; margin: 0 auto;"
      >
        <!-- Page heading -->
        <div class="mb-5">
          <div class="text-h5 font-weight-bold text-primary d-flex align-center gap-2">
            <v-icon :icon="currentNavItem.icon" color="primary" />
            {{ currentNavItem.label }}
          </div>
        </div>

        <!-- Views -->
        <transition name="fade" mode="out-in">
          <component :is="currentView" :key="activeView" />
        </transition>
      </v-container>
    </v-main>

    <!-- Mobile: Bottom Navigation -->
    <v-bottom-navigation
      v-if="display.smAndDown.value"
      v-model="activeView"
      color="primary"
      bg-color="white"
      elevation="8"
      grow
    >
      <v-btn
        v-for="item in navItems"
        :key="item.view"
        :value="item.view"
        height="56"
      >
        <v-icon :icon="item.icon" />
        <span class="text-caption">{{ item.label }}</span>
      </v-btn>
    </v-bottom-navigation>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDisplay } from 'vuetify'
import DailyView from './views/DailyView.vue'
import HistoryView from './views/HistoryView.vue'
import ConfigView from './views/ConfigView.vue'

const display = useDisplay()

const navItems = [
  { view: 'daily',   label: 'Daily Use',     icon: 'mdi-water'       },
  { view: 'history', label: 'History',        icon: 'mdi-history'     },
  { view: 'config',  label: 'Configuration',  icon: 'mdi-cog-outline' },
]

const VIEW_MAP = {
  daily:   DailyView,
  history: HistoryView,
  config:  ConfigView,
}

const activeView = ref('daily')

const currentView = computed(() => VIEW_MAP[activeView.value] ?? DailyView)

const currentNavItem = computed(() =>
  navItems.find((n) => n.view === activeView.value) ?? navItems[0]
)
</script>

<style>
body {
  background-color: #F1F8E9;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<style scoped>
.nav-item {
  color: rgba(255, 255, 255, 0.8) !important;
}
</style>
