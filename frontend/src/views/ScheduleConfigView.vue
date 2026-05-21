<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-5">
      <div>
        <div class="text-h6 font-weight-bold">Schedules</div>
        <div class="text-caption text-medium-emphasis">Named watering schedules with multiple zones</div>
      </div>
      <v-btn
        color="primary"
        variant="elevated"
        prepend-icon="mdi-plus"
        rounded="pill"
        @click="openAddDialog"
      >
        Add Schedule
      </v-btn>
    </div>

    <!-- Schedule list -->
    <div class="d-flex flex-column gap-3">
      <v-card
        v-for="schedule in schedules"
        :key="schedule.id"
        rounded="xl"
        elevation="1"
        class="schedule-card mb-3"
      >
        <v-card-item>
          <template #prepend>
            <v-avatar color="primary" size="44">
              <v-icon icon="mdi-calendar-clock" color="white" size="22" />
            </v-avatar>
          </template>

          <v-card-title class="text-body-1 font-weight-bold">{{ schedule.name }}</v-card-title>
          <v-card-subtitle class="text-caption">
            {{ scheduleSummary(schedule) }}
          </v-card-subtitle>

          <template #append>
            <div class="d-flex align-center gap-1">
              <v-switch
                :model-value="schedule.enabled"
                color="primary"
                hide-details
                density="compact"
                aria-label="Enable schedule"
                @update:model-value="(v) => updateSchedule(schedule.id, { enabled: v })"
              />
              <v-btn
                icon="mdi-pencil"
                variant="text"
                size="small"
                color="primary"
                aria-label="Edit schedule"
                @click="openEditDialog(schedule)"
              />
              <v-btn
                icon="mdi-delete"
                variant="text"
                size="small"
                color="error"
                aria-label="Delete schedule"
                @click="confirmDelete(schedule)"
              />
            </div>
          </template>
        </v-card-item>

        <!-- Zone chips -->
        <div class="px-4 pb-4">
          <div class="text-caption text-medium-emphasis mb-2">
            {{ schedule.zoneIds.length }} zone{{ schedule.zoneIds.length !== 1 ? 's' : '' }} — run in order
          </div>
          <div class="d-flex flex-wrap gap-2">
            <v-chip
              v-for="(zoneId, idx) in schedule.zoneIds"
              :key="zoneId"
              size="small"
              :color="getZone(zoneId) ? 'secondary' : 'error'"
              variant="tonal"
              :prepend-icon="getZone(zoneId)?.icon ?? 'mdi-alert'"
            >
              {{ idx + 1 }}. {{ getZone(zoneId)?.name ?? 'Unknown zone' }}
            </v-chip>
            <v-chip v-if="schedule.zoneIds.length === 0" size="small" color="warning" variant="tonal">
              No zones assigned
            </v-chip>
          </div>
        </div>
      </v-card>
    </div>

    <!-- Empty state -->
    <div v-if="schedules.length === 0" class="text-center py-16">
      <v-icon icon="mdi-calendar-blank" size="52" color="secondary" class="mb-3" />
      <div class="text-body-1 font-weight-medium">No schedules yet</div>
      <div class="text-body-2 text-medium-emphasis">Create a schedule to automate your watering.</div>
    </div>

    <!-- Add / Edit Schedule Dialog -->
    <v-dialog
      v-model="formDialogOpen"
      :fullscreen="display.xs.value"
      max-width="540"
      scrollable
    >
      <v-card rounded="xl">
        <v-card-item class="pt-5">
          <template #prepend>
            <v-avatar color="primary" size="44">
              <v-icon :icon="editingSchedule ? 'mdi-pencil' : 'mdi-plus'" color="white" />
            </v-avatar>
          </template>
          <v-card-title>{{ editingSchedule ? 'Edit Schedule' : 'New Schedule' }}</v-card-title>
          <v-card-subtitle>{{ editingSchedule ? editingSchedule.name : 'Set name, days, times, and zones' }}</v-card-subtitle>
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
          <v-form ref="formRef">
            <!-- Step 1: Name -->
            <div class="text-caption font-weight-medium text-medium-emphasis mb-1">Schedule Name</div>
            <v-text-field
              v-model="form.name"
              placeholder="e.g. Front Yard"
              prepend-inner-icon="mdi-tag"
              variant="outlined"
              rounded="lg"
              density="comfortable"
              :rules="[v => !!v || 'Name is required']"
              class="mb-5"
            />

            <!-- Step 2: Days of week -->
            <div class="text-caption font-weight-medium text-medium-emphasis mb-2">Days of Week</div>
            <div class="d-flex flex-wrap gap-2 mb-1">
              <v-chip
                v-for="day in daysOfWeek"
                :key="day"
                :color="form.days.includes(day) ? 'primary' : 'default'"
                :variant="form.days.includes(day) ? 'elevated' : 'tonal'"
                size="default"
                class="day-chip"
                clickable
                @click="toggleDay(day)"
              >
                {{ day }}
              </v-chip>
            </div>
            <div v-if="daysError" class="text-caption text-error mb-3 mt-1">{{ daysError }}</div>
            <div v-else class="mb-5" />

            <!-- Step 3: Start times -->
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

            <div
              v-if="form.startTimes.length === 0"
              class="text-caption text-medium-emphasis mb-1 pa-3 rounded-lg bg-surface-variant"
            >
              No start times. Click "Add Time" above.
            </div>

            <div class="d-flex flex-column gap-2">
              <div
                v-for="(time, idx) in form.startTimes"
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
            <div v-if="timesError" class="text-caption text-error mb-3 mt-1">{{ timesError }}</div>
            <div v-else class="mb-5" />

            <!-- Step 4: Zone selector and ordering -->
            <div class="d-flex align-center justify-space-between mb-2">
              <div class="text-caption font-weight-medium text-medium-emphasis">Zones (run in order)</div>
            </div>

            <!-- Available zones to add -->
            <div class="d-flex flex-wrap gap-2 mb-3">
              <v-chip
                v-for="zone in availableZones"
                :key="zone.id"
                :color="form.zoneIds.includes(zone.id) ? 'secondary' : 'default'"
                :variant="form.zoneIds.includes(zone.id) ? 'elevated' : 'tonal'"
                :prepend-icon="zone.icon"
                size="default"
                clickable
                @click="toggleZone(zone.id)"
              >
                {{ zone.name }}
              </v-chip>
              <div v-if="availableZones.length === 0" class="text-caption text-medium-emphasis pa-2">
                No zones configured. Add zones in the Zones tab first.
              </div>
            </div>

            <div v-if="zonesError" class="text-caption text-error mb-2">{{ zonesError }}</div>

            <!-- Ordered zone list with up/down reordering -->
            <div v-if="form.zoneIds.length > 0" class="mb-4">
              <div class="text-caption text-medium-emphasis mb-2">Run order:</div>
              <div class="d-flex flex-column gap-1">
                <div
                  v-for="(zoneId, idx) in form.zoneIds"
                  :key="zoneId"
                  class="d-flex align-center gap-2 pa-2 rounded-lg bg-surface-variant"
                >
                  <span class="text-caption font-weight-bold text-medium-emphasis" style="min-width: 20px;">
                    {{ idx + 1 }}.
                  </span>
                  <v-icon :icon="getZone(zoneId)?.icon ?? 'mdi-water'" size="18" color="secondary" />
                  <span class="text-body-2 flex-grow-1">{{ getZone(zoneId)?.name ?? zoneId }}</span>
                  <span class="text-caption text-medium-emphasis">{{ getZone(zoneId)?.duration }} min</span>
                  <v-btn
                    icon="mdi-chevron-up"
                    variant="text"
                    size="x-small"
                    :disabled="idx === 0"
                    aria-label="Move zone up"
                    @click="moveZone(idx, -1)"
                  />
                  <v-btn
                    icon="mdi-chevron-down"
                    variant="text"
                    size="x-small"
                    :disabled="idx === form.zoneIds.length - 1"
                    aria-label="Move zone down"
                    @click="moveZone(idx, 1)"
                  />
                  <v-btn
                    icon="mdi-close"
                    variant="text"
                    size="x-small"
                    color="error"
                    aria-label="Remove zone from schedule"
                    @click="removeZone(zoneId)"
                  />
                </div>
              </div>
            </div>
          </v-form>
        </v-card-text>

        <v-divider />

        <v-card-actions class="px-5 py-4">
          <v-btn variant="text" @click="formDialogOpen = false">Cancel</v-btn>
          <v-spacer />
          <v-btn
            color="primary"
            variant="elevated"
            rounded="pill"
            prepend-icon="mdi-check"
            @click="submitForm"
          >
            {{ editingSchedule ? 'Save Changes' : 'Create Schedule' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete confirmation dialog -->
    <v-dialog v-model="deleteDialogOpen" max-width="380">
      <v-card rounded="xl">
        <v-card-item class="pt-5">
          <template #prepend>
            <v-avatar color="error" size="44">
              <v-icon icon="mdi-delete" color="white" />
            </v-avatar>
          </template>
          <v-card-title>Delete Schedule</v-card-title>
        </v-card-item>
        <v-card-text>
          Are you sure you want to delete <strong>{{ deletingSchedule?.name }}</strong>?
          Zones will not be affected.
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
const { state, addSchedule, updateSchedule, deleteSchedule } = useSprinklers()

const schedules = computed(() => state.schedules)
const availableZones = computed(() => state.zones)

const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function getZone(id) {
  return state.zones.find((z) => z.id === id) ?? null
}

function scheduleSummary(schedule) {
  const days = schedule.days.length > 0 ? schedule.days.join(', ') : 'No days'
  const times = schedule.startTimes.length > 0 ? schedule.startTimes.join(', ') : 'No times'
  return `${days} at ${times}`
}

// --- Form state ---
const formDialogOpen = ref(false)
const editingSchedule = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  days: [],
  startTimes: [],
  zoneIds: [],
})

const daysError = ref('')
const timesError = ref('')
const zonesError = ref('')

function resetForm() {
  form.name = ''
  form.days = []
  form.startTimes = []
  form.zoneIds = []
  daysError.value = ''
  timesError.value = ''
  zonesError.value = ''
}

function openAddDialog() {
  editingSchedule.value = null
  resetForm()
  formDialogOpen.value = true
}

function openEditDialog(schedule) {
  editingSchedule.value = schedule
  form.name = schedule.name
  form.days = [...schedule.days]
  form.startTimes = [...schedule.startTimes]
  form.zoneIds = [...schedule.zoneIds]
  formDialogOpen.value = true
}

// Days
function toggleDay(day) {
  const idx = form.days.indexOf(day)
  if (idx === -1) form.days.push(day)
  else form.days.splice(idx, 1)
  daysError.value = ''
}

// Times
function addTime() {
  form.startTimes.push('06:00')
  timesError.value = ''
}

function removeTime(idx) {
  form.startTimes.splice(idx, 1)
}

function updateTime(idx, val) {
  form.startTimes[idx] = val
}

// Zone ordering
function toggleZone(zoneId) {
  const idx = form.zoneIds.indexOf(zoneId)
  if (idx === -1) form.zoneIds.push(zoneId)
  else form.zoneIds.splice(idx, 1)
  zonesError.value = ''
}

function moveZone(idx, direction) {
  const newIdx = idx + direction
  if (newIdx < 0 || newIdx >= form.zoneIds.length) return
  const item = form.zoneIds.splice(idx, 1)[0]
  form.zoneIds.splice(newIdx, 0, item)
}

function removeZone(zoneId) {
  const idx = form.zoneIds.indexOf(zoneId)
  if (idx !== -1) form.zoneIds.splice(idx, 1)
}

async function submitForm() {
  const { valid } = await formRef.value.validate()

  daysError.value = form.days.length === 0 ? 'Select at least one day' : ''
  timesError.value = form.startTimes.length === 0 ? 'Add at least one start time' : ''
  zonesError.value = form.zoneIds.length === 0 ? 'Select at least one zone' : ''

  if (!valid || daysError.value || timesError.value || zonesError.value) return

  const payload = {
    name: form.name,
    days: [...form.days],
    startTimes: [...form.startTimes],
    zoneIds: [...form.zoneIds],
  }

  if (editingSchedule.value) {
    await updateSchedule(editingSchedule.value.id, payload)
    if (state.error) { showSnack(state.error, 'error'); state.error = null; return }
    showSnack(`"${form.name}" updated`, 'primary')
  } else {
    await addSchedule(payload)
    if (state.error) { showSnack(state.error, 'error'); state.error = null; return }
    showSnack(`"${form.name}" created`, 'success')
  }
  formDialogOpen.value = false
}

// --- Delete ---
const deleteDialogOpen = ref(false)
const deletingSchedule = ref(null)

function confirmDelete(schedule) {
  deletingSchedule.value = schedule
  deleteDialogOpen.value = true
}

async function doDelete() {
  if (deletingSchedule.value) {
    const name = deletingSchedule.value.name
    await deleteSchedule(deletingSchedule.value.id)
    showSnack(`"${name}" deleted`, 'error')
  }
  deleteDialogOpen.value = false
  deletingSchedule.value = null
}

// --- Snackbar ---
const snack = reactive({ show: false, message: '', color: 'primary' })
function showSnack(message, color = 'primary') {
  snack.show = true
  snack.message = message
  snack.color = color
}
</script>

<style scoped>
.schedule-card {
  transition: box-shadow 0.2s ease;
}

.schedule-card:hover {
  box-shadow: 0 4px 16px rgba(46, 125, 50, 0.12) !important;
}

.day-chip {
  min-width: 52px;
  justify-content: center;
  font-weight: 500;
}
</style>
