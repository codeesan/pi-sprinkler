<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-5">
      <div>
        <div class="text-h6 font-weight-bold">Zones</div>
        <div class="text-caption text-medium-emphasis">Configure sprinkler zones and their defaults</div>
      </div>
      <v-btn
        color="primary"
        variant="elevated"
        prepend-icon="mdi-plus"
        rounded="pill"
        @click="openAddDialog"
      >
        Add Zone
      </v-btn>
    </div>

    <!-- Zone list -->
    <v-card rounded="xl" elevation="1" class="overflow-hidden">
      <v-list lines="two" class="pa-0">
        <template v-for="(zone, idx) in zones" :key="zone.id">
          <v-divider v-if="idx > 0" />
          <v-list-item
            :subtitle="`Port ${zone.port} · Default ${zone.duration} min`"
            min-height="72"
          >
            <template #prepend>
              <v-avatar :color="zone.color" size="42" class="mr-3">
                <v-icon :icon="zone.icon" color="white" size="22" />
              </v-avatar>
            </template>

            <template #title>
              <span class="font-weight-medium">{{ zone.name }}</span>
            </template>

            <template #append>
              <div class="d-flex gap-1">
                <v-btn
                  icon="mdi-pencil"
                  variant="text"
                  size="small"
                  color="primary"
                  aria-label="Edit zone"
                  @click="openEditDialog(zone)"
                />
                <v-btn
                  icon="mdi-delete"
                  variant="text"
                  size="small"
                  color="error"
                  aria-label="Delete zone"
                  @click="confirmDelete(zone)"
                />
              </div>
            </template>
          </v-list-item>
        </template>
      </v-list>

      <!-- Empty state -->
      <div v-if="zones.length === 0" class="text-center py-12 px-4">
        <v-icon icon="mdi-sprinkler" size="52" color="secondary" class="mb-3" />
        <div class="text-body-1 font-weight-medium">No zones yet</div>
        <div class="text-body-2 text-medium-emphasis">Add your first zone to get started.</div>
      </div>
    </v-card>

    <!-- Add / Edit Zone Dialog -->
    <v-dialog
      v-model="formDialogOpen"
      :fullscreen="display.xs.value"
      max-width="480"
      rounded="xl"
    >
      <v-card rounded="xl">
        <v-card-item class="pt-5">
          <template #prepend>
            <v-avatar color="primary" size="44">
              <v-icon :icon="editingZone ? 'mdi-pencil' : 'mdi-plus'" color="white" />
            </v-avatar>
          </template>
          <v-card-title>{{ editingZone ? 'Edit Zone' : 'Add Zone' }}</v-card-title>
          <v-card-subtitle>{{ editingZone ? editingZone.name : 'New sprinkler zone' }}</v-card-subtitle>
          <template #append>
            <v-btn
              icon="mdi-close"
              variant="text"
              size="small"
              aria-label="Close"
              @click="formDialogOpen = false"
            />
          </template>
        </v-card-item>

        <v-divider />

        <v-card-text class="pt-5">
          <v-form ref="formRef" @submit.prevent="submitForm">
            <v-text-field
              v-model="form.name"
              label="Zone Name"
              placeholder="e.g. Front Lawn"
              prepend-inner-icon="mdi-tag"
              variant="outlined"
              rounded="lg"
              :rules="[v => !!v || 'Name is required']"
              class="mb-3"
            />

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model.number="form.port"
                  label="Port Number"
                  type="number"
                  :min="1"
                  :max="16"
                  prepend-inner-icon="mdi-numeric"
                  variant="outlined"
                  rounded="lg"
                  :rules="[
                    v => !!v || 'Required',
                    v => (v >= 1 && v <= 16) || 'Port must be 1–16',
                    v => !state.zones.some(z => z.port === v && z.id !== editingZone?.id) || 'Port already in use',
                  ]"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="form.duration"
                  label="Duration (min)"
                  type="number"
                  :min="1"
                  :max="120"
                  prepend-inner-icon="mdi-clock-outline"
                  variant="outlined"
                  rounded="lg"
                  :rules="[
                    v => !!v || 'Required',
                    v => v >= 1 || 'Min 1 minute',
                  ]"
                />
              </v-col>
            </v-row>

            <!-- Icon picker -->
            <div class="text-caption text-medium-emphasis mb-2 mt-1">Zone Icon</div>
            <div class="d-flex gap-2 flex-wrap mb-4">
              <v-btn
                v-for="opt in iconOptions"
                :key="opt.icon"
                :icon="opt.icon"
                :color="form.icon === opt.icon ? 'primary' : 'default'"
                :variant="form.icon === opt.icon ? 'elevated' : 'tonal'"
                size="40"
                :aria-label="opt.label"
                rounded
                @click="form.icon = opt.icon"
              />
            </div>
          </v-form>
        </v-card-text>

        <v-card-actions class="px-5 pb-5">
          <v-btn variant="text" @click="formDialogOpen = false">Cancel</v-btn>
          <v-spacer />
          <v-btn
            color="primary"
            variant="elevated"
            rounded="pill"
            prepend-icon="mdi-check"
            @click="submitForm"
          >
            {{ editingZone ? 'Save Changes' : 'Add Zone' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete confirmation dialog -->
    <v-dialog v-model="deleteDialogOpen" max-width="380" rounded="xl">
      <v-card rounded="xl">
        <v-card-item class="pt-5">
          <template #prepend>
            <v-avatar color="error" size="44">
              <v-icon icon="mdi-delete" color="white" />
            </v-avatar>
          </template>
          <v-card-title>Delete Zone</v-card-title>
        </v-card-item>
        <v-card-text>
          Are you sure you want to delete <strong>{{ deletingZone?.name }}</strong>?
          It will be removed from any schedules that reference it.
        </v-card-text>
        <v-card-actions class="pb-4 px-4">
          <v-btn variant="text" @click="deleteDialogOpen = false">Cancel</v-btn>
          <v-spacer />
          <v-btn color="error" variant="elevated" rounded="pill" @click="doDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snack.show" :color="snack.color" rounded="pill" :timeout="2500">
      {{ snack.message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useDisplay } from 'vuetify'
import { useSprinklers } from '../composables/useSprinklers'

const display = useDisplay()
const { state, addZone, updateZone, deleteZone } = useSprinklers()

const zones = computed(() => state.zones)

const iconOptions = [
  { icon: 'mdi-grass', label: 'Grass' },
  { icon: 'mdi-leaf', label: 'Leaf' },
  { icon: 'mdi-flower', label: 'Flower' },
  { icon: 'mdi-water', label: 'Water' },
  { icon: 'mdi-tree', label: 'Tree' },
  { icon: 'mdi-sprout', label: 'Sprout' },
]

// Form dialog
const formDialogOpen = ref(false)
const editingZone = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  port: 1,
  duration: 15,
  icon: 'mdi-water',
})

function openAddDialog() {
  editingZone.value = null
  form.name = ''
  form.port = 1
  form.duration = 15
  form.icon = 'mdi-water'
  formDialogOpen.value = true
}

function openEditDialog(zone) {
  editingZone.value = zone
  form.name = zone.name
  form.port = zone.port
  form.duration = zone.duration
  form.icon = zone.icon
  formDialogOpen.value = true
}

async function submitForm() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  if (editingZone.value) {
    await updateZone(editingZone.value.id, {
      name: form.name,
      port: form.port,
      duration: form.duration,
      icon: form.icon,
    })
    if (state.error) { showSnack(state.error, 'error'); state.error = null; return }
    showSnack(`${form.name} updated`, 'primary')
  } else {
    await addZone({ name: form.name, port: form.port, duration: form.duration, icon: form.icon })
    if (state.error) { showSnack(state.error, 'error'); state.error = null; return }
    showSnack(`${form.name} added`, 'success')
  }
  formDialogOpen.value = false
}

// Delete dialog
const deleteDialogOpen = ref(false)
const deletingZone = ref(null)

function confirmDelete(zone) {
  deletingZone.value = zone
  deleteDialogOpen.value = true
}

async function doDelete() {
  if (deletingZone.value) {
    const name = deletingZone.value.name
    await deleteZone(deletingZone.value.id)
    showSnack(`${name} deleted`, 'error')
  }
  deleteDialogOpen.value = false
  deletingZone.value = null
}

// Snackbar
const snack = reactive({ show: false, message: '', color: 'primary' })
function showSnack(message, color = 'primary') {
  snack.show = true
  snack.message = message
  snack.color = color
}
</script>
