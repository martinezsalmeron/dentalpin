# Plan Técnico: Rediseño Tab Clínico

**Documento de diseño:** [clinical-tab-redesign.md](./clinical-tab-redesign.md)

---

## Resumen de Cambios

### Arquitectura Actual
```
ClinicalTab.vue
├── OdontogramChart.vue
│   ├── TreatmentBar.vue (mezcla diagnósticos + tratamientos)
│   ├── TimelineSlider.vue
│   └── ToothQuadrant.vue (x4)
└── Treatment Plans Section (inline)
    ├── TreatmentPlanMiniCard.vue
    └── TreatmentPlanDetail.vue (modal)
```

### Arquitectura Propuesta
```
ClinicalTab.vue
├── ClinicalModeToggle.vue (3 tabs)
│
├── [Modo Histórico] HistoryMode.vue
│   ├── TimelineSlider.vue (existente, reusar)
│   ├── OdontogramChart.vue (mode="view-only")
│   └── ChangesList.vue (nuevo)
│
├── [Modo Diagnóstico] DiagnosisMode.vue
│   ├── OdontogramChart.vue (mode="diagnosis")
│   ├── TreatmentBar.vue (mode="diagnosis") ← REUTILIZADO
│   ├── ConditionsList.vue (nuevo)
│   └── DiagnosisCTA.vue (nuevo, contextual)
│
└── [Modo Planes] PlansMode.vue
    ├── PlansListView.vue (lista de planes)
    │   ├── TreatmentPlanMiniCard.vue (existente)
    │   └── OdontogramMini.vue (nuevo, resumen)
    └── PlanDetailView.vue (vista expandida)
        ├── OdontogramChart.vue (mode="planning", con highlighting)
        ├── PlanTreatmentList.vue (nuevo, con hover linking)
        └── TreatmentBar.vue (mode="planning") ← REUTILIZADO
```

> **Nota:** `TreatmentBar.vue` se reutiliza con prop `mode` en lugar de crear componente separado.

---

## Fase 1: Preparación y Refactoring Base

### 1.1 Separar Catálogo de Tratamientos

**Problema:** `TreatmentBar.vue` usa `useTreatmentCatalog()` que mezcla diagnósticos y tratamientos.

**Solución:** Añadir campo `is_diagnosis` al catálogo o usar categorías existentes.

**Archivo:** `frontend/app/composables/useTreatmentCatalog.ts`

```typescript
// Añadir computed para filtrar
const diagnosticTreatments = computed(() =>
  catalog.value.filter(t => DIAGNOSTIC_CATEGORIES.includes(t.category))
)

const therapeuticTreatments = computed(() =>
  catalog.value.filter(t => !DIAGNOSTIC_CATEGORIES.includes(t.category))
)

const DIAGNOSTIC_CATEGORIES = ['diagnostic', 'existing_condition']
```

**Backend (si necesario):** Verificar que `TreatmentCatalogItem` tenga categoría que distinga diagnósticos.

**Archivos a modificar:**
- `frontend/app/composables/useTreatmentCatalog.ts`
- Posiblemente: `backend/app/modules/treatment_catalog/models.py` (añadir `is_diagnosis` bool)

---

### 1.2 Extender OdontogramChart con Modos

**Archivo:** `frontend/app/components/odontogram/OdontogramChart.vue`

**Cambios:**
```typescript
// Props actuales
mode?: 'full' | 'view-only' | 'planning'

// Props nuevos
mode?: 'full' | 'view-only' | 'diagnosis' | 'planning'
highlightedTeeth?: number[]  // Para hover linking
onToothHover?: (toothNumber: number | null) => void
planId?: string  // Para modo planning, filtrar tratamientos del plan
```

**Comportamiento por modo:**

| Modo | Barra | Editable | Timeline | Highlighting |
|------|-------|----------|----------|--------------|
| `view-only` | No | No | Sí | No |
| `diagnosis` | DiagnosisBar | Sí (solo diagnósticos) | No | No |
| `planning` | TreatmentBar | Sí (solo terapéuticos) | No | Sí |

---

### 1.3 Crear Hook para Draft Plans

**Archivo:** `frontend/app/composables/useTreatmentPlans.ts`

**Añadir:**
```typescript
const draftPlans = computed(() =>
  plans.value.filter(p => p.status === 'draft')
)

async function fetchDraftPlans(patientId: string) {
  return fetchPlans({ patient_id: patientId, status: 'draft' })
}
```

---

## Fase 2: Componentes Nuevos

### 2.1 ClinicalModeToggle.vue

**Path:** `frontend/app/components/clinical/ClinicalModeToggle.vue`

```vue
<script setup lang="ts">
type ClinicalMode = 'history' | 'diagnosis' | 'plans'

const props = defineProps<{
  modelValue: ClinicalMode
}>()

const emit = defineEmits<{
  'update:modelValue': [mode: ClinicalMode]
}>()

const modes = [
  { value: 'history', label: 'clinical.modes.history', icon: 'i-lucide-history' },
  { value: 'diagnosis', label: 'clinical.modes.diagnosis', icon: 'i-lucide-stethoscope' },
  { value: 'plans', label: 'clinical.modes.plans', icon: 'i-lucide-clipboard-list' },
]
</script>

<template>
  <div class="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
    <UButton
      v-for="mode in modes"
      :key="mode.value"
      :variant="modelValue === mode.value ? 'solid' : 'ghost'"
      :icon="mode.icon"
      @click="emit('update:modelValue', mode.value)"
    >
      {{ $t(mode.label) }}
    </UButton>
  </div>
</template>
```

---

### 2.2 HistoryMode.vue

**Path:** `frontend/app/components/clinical/HistoryMode.vue`

```vue
<script setup lang="ts">
const props = defineProps<{
  patientId: string
}>()

const {
  timelineDates,
  viewingDate,
  fetchTimeline,
  fetchOdontogramAtDate,
  historicalTeeth,
  historicalTreatments
} = useOdontogram()

// Cargar timeline al montar
onMounted(() => fetchTimeline(props.patientId))

// Computed para cambios en fecha seleccionada
const changesAtDate = computed(() => {
  // Filtrar tratamientos/cambios de la fecha seleccionada
  return historicalTreatments.value.filter(t =>
    t.recorded_at?.startsWith(viewingDate.value)
  )
})
</script>

<template>
  <div class="space-y-4">
    <!-- Timeline Slider -->
    <UCard>
      <TimelineSlider
        :dates="timelineDates"
        :selected-date="viewingDate"
        @select="fetchOdontogramAtDate(patientId, $event)"
      />
    </UCard>

    <!-- Odontograma (solo lectura) -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span>{{ $t('clinical.history.stateAt') }} {{ viewingDate }}</span>
        </div>
      </template>
      <OdontogramChart
        :patient-id="patientId"
        mode="view-only"
      />
    </UCard>

    <!-- Cambios en esta fecha -->
    <UCard v-if="changesAtDate.length">
      <template #header>
        {{ $t('clinical.history.changesOnDate') }}
      </template>
      <ChangesList :changes="changesAtDate" />
    </UCard>
  </div>
</template>
```

---

### 2.3 DiagnosisMode.vue

**Path:** `frontend/app/components/clinical/DiagnosisMode.vue`

```vue
<script setup lang="ts">
const props = defineProps<{
  patientId: string
}>()

const emit = defineEmits<{
  'create-plan': []
  'continue-plan': [planId: string]
}>()

const { treatments, fetchTreatments } = useOdontogram()
const { plans, fetchPatientPlans } = useTreatmentPlans()

// Filtrar solo diagnósticos (status = 'existing')
const conditions = computed(() =>
  treatments.value.filter(t => t.status === 'existing')
)

// Planes en borrador para CTA contextual
const draftPlans = computed(() =>
  plans.value.filter(p => p.status === 'draft')
)

onMounted(() => {
  fetchTreatments(props.patientId)
  fetchPatientPlans(props.patientId)
})
</script>

<template>
  <div class="space-y-4">
    <!-- Odontograma con barra de diagnósticos -->
    <UCard>
      <OdontogramChart
        :patient-id="patientId"
        mode="diagnosis"
      />
    </UCard>

    <!-- Lista de condiciones registradas -->
    <UCard>
      <template #header>
        {{ $t('clinical.diagnosis.registeredConditions') }}
      </template>
      <ConditionsList :conditions="conditions" />
    </UCard>

    <!-- CTA Contextual -->
    <DiagnosisCTA
      :draft-plans="draftPlans"
      @create="emit('create-plan')"
      @continue="emit('continue-plan', $event)"
    />
  </div>
</template>
```

---

### 2.4 Modificar TreatmentBar.vue (añadir modo)

**Path:** `frontend/app/components/odontogram/TreatmentBar.vue`

**Cambio:** Añadir prop `mode` para reutilizar en diagnóstico y planificación.

```vue
<script setup lang="ts">
// NUEVOS props
const props = defineProps<{
  mode?: 'diagnosis' | 'planning' | 'full'  // NUEVO
  selectedTreatment?: TreatmentType | null
  selectedStatus: TreatmentStatus
  selectedPlanId?: string | null
  patientId?: string
  treatmentPlans?: TreatmentPlan[]
  disabled?: boolean
}>()

// Categorías de diagnóstico
const DIAGNOSTIC_CATEGORIES = ['diagnostic', 'existing_condition', 'caries', 'periodontal']

// Filtrar categorías según modo
const visibleCategories = computed(() => {
  const all = categories.value
  if (props.mode === 'diagnosis') {
    return all.filter(c => DIAGNOSTIC_CATEGORIES.includes(c.id))
  }
  if (props.mode === 'planning') {
    return all.filter(c => !DIAGNOSTIC_CATEGORIES.includes(c.id))
  }
  return all // 'full' = todo (comportamiento actual)
})

// Status forzado en modo diagnóstico
const effectiveStatus = computed(() =>
  props.mode === 'diagnosis' ? 'existing' : props.selectedStatus
)

// Controles visibles según modo
const showStatusToggle = computed(() => props.mode !== 'diagnosis')
const showPlanSelector = computed(() =>
  props.mode !== 'diagnosis' && effectiveStatus.value === 'planned'
)
</script>

<template>
  <div class="treatment-bar">
    <!-- Status toggle: oculto en modo diagnóstico -->
    <div v-if="showStatusToggle" class="status-toggle">
      <!-- ... toggle existing/planned ... -->
    </div>

    <!-- Plan selector: solo en planning con status=planned -->
    <div v-if="showPlanSelector" class="plan-selector">
      <!-- ... dropdown planes ... -->
    </div>

    <!-- Category tabs: filtradas por modo -->
    <div class="category-tabs">
      <UButton
        v-for="cat in visibleCategories"
        :key="cat.id"
        <!-- ... -->
      />
    </div>

    <!-- Treatment grid: sin cambios -->
  </div>
</template>
```

**Uso en DiagnosisMode:**
```vue
<TreatmentBar
  mode="diagnosis"
  :patient-id="patientId"
  @treatment-select="handleDiagnosisSelect"
/>
```

**Uso en PlanDetailView:**
```vue
<TreatmentBar
  mode="planning"
  :patient-id="patientId"
  :plan-id="plan.id"
  :treatment-plans="plans"
  @treatment-select="handleTreatmentSelect"
/>
```

---

### 2.5 DiagnosisCTA.vue

**Path:** `frontend/app/components/clinical/DiagnosisCTA.vue`

```vue
<script setup lang="ts">
const props = defineProps<{
  draftPlans: TreatmentPlan[]
}>()

const emit = defineEmits<{
  'create': []
  'continue': [planId: string]
}>()

const selectedDraftId = ref<string>('')
</script>

<template>
  <UCard class="bg-primary-50 dark:bg-primary-900/20 border-primary-200">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-lightbulb" class="text-primary-500" />
        <span>{{ $t('clinical.diagnosis.readyToCreatePlan') }}</span>
      </div>

      <!-- Sin borradores: Crear plan -->
      <UButton
        v-if="draftPlans.length === 0"
        color="primary"
        @click="emit('create')"
      >
        {{ $t('clinical.diagnosis.createPlan') }}
      </UButton>

      <!-- 1 borrador: Continuar ese plan -->
      <UButton
        v-else-if="draftPlans.length === 1"
        color="primary"
        @click="emit('continue', draftPlans[0].id)"
      >
        {{ $t('clinical.diagnosis.continuePlan', { name: draftPlans[0].title }) }}
      </UButton>

      <!-- N borradores: Dropdown -->
      <div v-else class="flex items-center gap-2">
        <USelectMenu
          v-model="selectedDraftId"
          :options="draftPlans"
          option-attribute="title"
          value-attribute="id"
          :placeholder="$t('clinical.diagnosis.selectPlan')"
        />
        <UButton
          color="primary"
          :disabled="!selectedDraftId"
          @click="emit('continue', selectedDraftId)"
        >
          {{ $t('clinical.diagnosis.continue') }}
        </UButton>
      </div>
    </div>
  </UCard>
</template>
```

---

### 2.6 PlansMode.vue

**Path:** `frontend/app/components/clinical/PlansMode.vue`

```vue
<script setup lang="ts">
const props = defineProps<{
  patientId: string
  initialPlanId?: string  // Para abrir directamente un plan (desde CTA diagnóstico)
}>()

const { plans, fetchPatientPlans, fetchPlan } = useTreatmentPlans()

// Vista: 'list' o 'detail'
const view = ref<'list' | 'detail'>('list')
const selectedPlan = ref<TreatmentPlanDetail | null>(null)

async function openPlanDetail(planId: string) {
  selectedPlan.value = await fetchPlan(planId)
  view.value = 'detail'
}

function backToList() {
  view.value = 'list'
  selectedPlan.value = null
}

onMounted(async () => {
  await fetchPatientPlans(props.patientId)
  if (props.initialPlanId) {
    openPlanDetail(props.initialPlanId)
  }
})

watch(() => props.initialPlanId, (newId) => {
  if (newId) openPlanDetail(newId)
})
</script>

<template>
  <!-- Vista Lista -->
  <PlansListView
    v-if="view === 'list'"
    :plans="plans"
    :patient-id="patientId"
    @view-plan="openPlanDetail"
    @create-plan="showCreateModal = true"
  />

  <!-- Vista Detalle -->
  <PlanDetailView
    v-else
    :plan="selectedPlan"
    :patient-id="patientId"
    @back="backToList"
    @updated="openPlanDetail(selectedPlan.id)"
  />
</template>
```

---

### 2.7 PlanDetailView.vue (Vista Expandida con Hover Linking)

**Path:** `frontend/app/components/clinical/PlanDetailView.vue`

```vue
<script setup lang="ts">
const props = defineProps<{
  plan: TreatmentPlanDetail
  patientId: string
}>()

// Hover linking state
const hoveredToothNumber = ref<number | null>(null)
const hoveredItemId = ref<string | null>(null)

// Teeth que tienen tratamientos en este plan
const planTeeth = computed(() => {
  return [...new Set(
    props.plan.items
      .filter(item => item.tooth_number)
      .map(item => item.tooth_number)
  )]
})

// Items del diente hovered
const highlightedItems = computed(() => {
  if (!hoveredToothNumber.value) return []
  return props.plan.items
    .filter(item => item.tooth_number === hoveredToothNumber.value)
    .map(item => item.id)
})

// Dientes del item hovered
const highlightedTeeth = computed(() => {
  if (!hoveredItemId.value) return []
  const item = props.plan.items.find(i => i.id === hoveredItemId.value)
  return item?.tooth_number ? [item.tooth_number] : []
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header con navegación -->
    <div class="flex items-center justify-between">
      <UButton variant="ghost" icon="i-lucide-arrow-left" @click="emit('back')">
        {{ $t('clinical.plans.backToList') }}
      </UButton>
      <h2 class="text-lg font-semibold">{{ plan.title }}</h2>
      <div class="flex gap-2">
        <UButton v-if="plan.status === 'draft'" @click="activatePlan">
          {{ $t('clinical.plans.activate') }}
        </UButton>
        <UButton @click="generateBudget">
          {{ $t('clinical.plans.generateBudget') }}
        </UButton>
      </div>
    </div>

    <!-- Layout dos columnas -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Columna izquierda: Odontograma -->
      <UCard>
        <OdontogramChart
          :patient-id="patientId"
          mode="planning"
          :plan-id="plan.id"
          :highlighted-teeth="highlightedTeeth"
          @tooth-hover="hoveredToothNumber = $event"
        />
      </UCard>

      <!-- Columna derecha: Lista de tratamientos -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <span>{{ $t('clinical.plans.treatments') }}</span>
            <UButton size="sm" icon="i-lucide-plus">
              {{ $t('clinical.plans.addTreatment') }}
            </UButton>
          </div>
        </template>

        <PlanTreatmentList
          :items="plan.items"
          :highlighted-items="highlightedItems"
          @item-hover="hoveredItemId = $event"
          @item-complete="handleComplete"
          @item-remove="handleRemove"
        />

        <!-- Total -->
        <template #footer>
          <div class="flex justify-between font-semibold">
            <span>{{ $t('clinical.plans.total') }}</span>
            <span>{{ formatCurrency(planTotal) }}</span>
          </div>
        </template>
      </UCard>
    </div>

    <!-- Barra de tratamientos (abajo) -->
    <UCard>
      <TreatmentBar
        :patient-id="patientId"
        :plan-id="plan.id"
        mode="therapeutic-only"
        @treatment-applied="refreshPlan"
      />
    </UCard>
  </div>
</template>
```

---

### 2.8 PlanTreatmentList.vue (con Hover Linking)

**Path:** `frontend/app/components/clinical/PlanTreatmentList.vue`

```vue
<script setup lang="ts">
const props = defineProps<{
  items: PlannedTreatmentItem[]
  highlightedItems: string[]
}>()

const emit = defineEmits<{
  'item-hover': [itemId: string | null]
  'item-complete': [itemId: string]
  'item-remove': [itemId: string]
}>()

const pendingItems = computed(() => props.items.filter(i => i.status === 'pending'))
const completedItems = computed(() => props.items.filter(i => i.status === 'completed'))
</script>

<template>
  <div class="space-y-2">
    <!-- Pendientes -->
    <div
      v-for="(item, index) in pendingItems"
      :key="item.id"
      class="p-3 rounded-lg border transition-colors"
      :class="{
        'bg-yellow-50 border-yellow-300': highlightedItems.includes(item.id),
        'hover:bg-gray-50': !highlightedItems.includes(item.id)
      }"
      @mouseenter="emit('item-hover', item.id)"
      @mouseleave="emit('item-hover', null)"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-gray-400">{{ index + 1 }}.</span>
          <div>
            <div class="font-medium">{{ item.catalog_item?.name || item.description }}</div>
            <div v-if="item.tooth_number" class="text-sm text-gray-500">
              {{ $t('clinical.tooth') }} {{ item.tooth_number }}
              <span v-if="item.surfaces?.length">({{ item.surfaces.join(', ') }})</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="font-medium">{{ formatCurrency(item.price) }}</span>
          <UButton size="xs" variant="ghost" icon="i-lucide-check" @click="emit('item-complete', item.id)" />
          <UButton size="xs" variant="ghost" color="red" icon="i-lucide-trash-2" @click="emit('item-remove', item.id)" />
        </div>
      </div>
    </div>

    <!-- Completados (colapsable) -->
    <UAccordion v-if="completedItems.length" :items="[{ label: `Completados (${completedItems.length})`, slot: 'completed' }]">
      <template #completed>
        <div v-for="item in completedItems" :key="item.id" class="p-2 text-gray-500 line-through">
          {{ item.catalog_item?.name }} - {{ $t('clinical.tooth') }} {{ item.tooth_number }}
        </div>
      </template>
    </UAccordion>
  </div>
</template>
```

---

## Fase 3: Refactoring ClinicalTab Principal

### 3.1 Nuevo ClinicalTab.vue

**Path:** `frontend/app/components/patient/ClinicalTab.vue`

```vue
<script setup lang="ts">
import type { ClinicalMode } from '~/types'

const props = defineProps<{
  patientId: string
  readonly?: boolean
}>()

const route = useRoute()
const router = useRouter()

// Modo actual (sync con query param)
const currentMode = ref<ClinicalMode>('diagnosis')

// Plan a abrir (para transición desde diagnóstico)
const targetPlanId = ref<string | null>(null)

// Sync mode con URL
watch(currentMode, (mode) => {
  router.replace({ query: { ...route.query, clinicalMode: mode } })
})

onMounted(() => {
  const queryMode = route.query.clinicalMode as ClinicalMode
  if (queryMode && ['history', 'diagnosis', 'plans'].includes(queryMode)) {
    currentMode.value = queryMode
  }
})

// Handlers para transiciones entre modos
function handleCreatePlan() {
  // Abrir modal de crear plan, luego ir a planes
  showPlanModal.value = true
}

function handleContinuePlan(planId: string) {
  targetPlanId.value = planId
  currentMode.value = 'plans'
}

function handlePlanCreated(plan: TreatmentPlan) {
  targetPlanId.value = plan.id
  currentMode.value = 'plans'
}
</script>

<template>
  <div class="space-y-4">
    <!-- Toggle de modos -->
    <ClinicalModeToggle v-model="currentMode" />

    <!-- Contenido según modo -->
    <HistoryMode
      v-if="currentMode === 'history'"
      :patient-id="patientId"
    />

    <DiagnosisMode
      v-else-if="currentMode === 'diagnosis'"
      :patient-id="patientId"
      :readonly="readonly"
      @create-plan="handleCreatePlan"
      @continue-plan="handleContinuePlan"
    />

    <PlansMode
      v-else
      :patient-id="patientId"
      :initial-plan-id="targetPlanId"
      :readonly="readonly"
    />

    <!-- Modal crear plan (compartido) -->
    <TreatmentPlanModal
      v-model="showPlanModal"
      :patient-id="patientId"
      @saved="handlePlanCreated"
    />
  </div>
</template>
```

---

## Fase 4: Modificaciones Backend (Mínimas)

### 4.1 Endpoint para Cambios por Fecha

El timeline ya existe pero necesitamos los cambios específicos de una fecha.

**Archivo:** `backend/app/modules/odontogram/router.py`

```python
@router.get("/patients/{patient_id}/odontogram/changes")
async def get_changes_at_date(
    patient_id: UUID,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    ctx: ClinicContext = Depends(get_clinic_context),
    _: None = Depends(require_permission("odontogram.read")),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[HistoryEntryWithUser]]:
    """Get all odontogram changes that occurred on a specific date."""
    changes = await OdontogramService.get_changes_at_date(
        db, ctx.clinic_id, patient_id, date
    )
    return ApiResponse(data=changes)
```

**Archivo:** `backend/app/modules/odontogram/service.py`

```python
@staticmethod
async def get_changes_at_date(
    db: AsyncSession,
    clinic_id: UUID,
    patient_id: UUID,
    date_str: str,
) -> list[OdontogramHistory]:
    """Get all changes that occurred on a specific date."""
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    result = await db.execute(
        select(OdontogramHistory)
        .join(ToothRecord)
        .where(
            ToothRecord.clinic_id == clinic_id,
            ToothRecord.patient_id == patient_id,
            func.date(OdontogramHistory.changed_at) == target_date,
        )
        .order_by(OdontogramHistory.changed_at)
    )
    return result.scalars().all()
```

---

### 4.2 Verificar Catálogo de Tratamientos

**Revisar:** `backend/app/modules/treatment_catalog/models.py`

Asegurar que las categorías permitan distinguir diagnósticos de tratamientos:

```python
class TreatmentCategory(str, Enum):
    # Diagnósticos / Condiciones existentes
    DIAGNOSTIC = "diagnostic"
    EXISTING_CONDITION = "existing_condition"

    # Terapéuticos
    PREVENTIVE = "preventive"
    RESTORATIVE = "restorative"
    ENDODONTIC = "endodontic"
    PROSTHETIC = "prosthetic"
    SURGICAL = "surgical"
    ORTHODONTIC = "orthodontic"
    PERIODONTAL_TREATMENT = "periodontal_treatment"
```

Si no existe esta distinción, añadir campo `is_diagnosis: bool` al modelo.

---

## Fase 5: Internacionalización

### 5.1 Claves de Traducción

**Archivo:** `frontend/i18n/locales/es.json`

```json
{
  "clinical": {
    "modes": {
      "history": "Histórico",
      "diagnosis": "Diagnóstico",
      "plans": "Planes"
    },
    "history": {
      "stateAt": "Estado a fecha",
      "changesOnDate": "Cambios en esta fecha",
      "noChanges": "Sin cambios registrados"
    },
    "diagnosis": {
      "registeredConditions": "Condiciones registradas",
      "readyToCreatePlan": "¿Diagnóstico completo?",
      "createPlan": "Crear Plan de Tratamiento",
      "continuePlan": "Continuar Plan \"{name}\"",
      "selectPlan": "Seleccionar plan",
      "continue": "Continuar"
    },
    "plans": {
      "backToList": "Volver a planes",
      "treatments": "Tratamientos del Plan",
      "addTreatment": "Añadir Tratamiento",
      "total": "Total",
      "activate": "Activar Plan",
      "generateBudget": "Generar Presupuesto"
    },
    "tooth": "Diente"
  }
}
```

---

## Orden de Implementación

### Sprint 1: Base
1. [ ] Separar catálogo (diagnósticos vs terapéuticos) en `useTreatmentCatalog.ts`
2. [ ] Crear `ClinicalModeToggle.vue`
3. [ ] Extender props de `OdontogramChart.vue` (mode, highlightedTeeth, onToothHover)
4. [ ] Modificar `TreatmentBar.vue` (añadir prop mode, filtrar categorías)
5. [ ] Crear `HistoryMode.vue` + `ChangesList.vue`

### Sprint 2: Diagnóstico
6. [ ] Crear `ConditionsList.vue`
7. [ ] Crear `DiagnosisCTA.vue`
8. [ ] Crear `DiagnosisMode.vue`

### Sprint 3: Planes
9. [ ] Crear `PlansListView.vue`
10. [ ] Crear `PlanTreatmentList.vue` (con hover linking)
11. [ ] Crear `PlanDetailView.vue`
12. [ ] Crear `PlansMode.vue`

### Sprint 4: Integración
13. [ ] Refactorizar `ClinicalTab.vue`
14. [ ] Añadir endpoint backend cambios por fecha
15. [ ] Tests e2e
16. [ ] Traducciones

---

## Archivos a Crear (9 componentes)

```
frontend/app/components/clinical/
├── ClinicalModeToggle.vue
├── HistoryMode.vue
├── ChangesList.vue
├── DiagnosisMode.vue
├── ConditionsList.vue
├── DiagnosisCTA.vue
├── PlansMode.vue
├── PlansListView.vue
├── PlanDetailView.vue
└── PlanTreatmentList.vue
```

## Archivos a Modificar

```
frontend/app/components/
├── patient/ClinicalTab.vue (refactor completo)
├── odontogram/OdontogramChart.vue (añadir props: mode, highlightedTeeth, onToothHover)
└── odontogram/TreatmentBar.vue (añadir prop mode, filtrar categorías según modo)

frontend/app/composables/
├── useTreatmentCatalog.ts (añadir filtros)
└── useTreatmentPlans.ts (añadir draftPlans)

backend/app/modules/odontogram/
├── router.py (añadir endpoint changes)
└── service.py (añadir get_changes_at_date)
```

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Catálogo no distingue diagnósticos | Alto | Revisar primero, añadir campo si necesario |
| Performance hover linking | Medio | Debounce en eventos hover |
| Complejidad estado entre modos | Medio | Usar composables compartidos |
| Regresiones en funcionalidad existente | Alto | Tests antes de refactor |

---

## Criterios de Aceptación

1. **Histórico**: Usuario puede navegar timeline y ver estado pasado (solo lectura)
2. **Diagnóstico**: Usuario puede registrar condiciones, ver lista, CTA contextual funciona
3. **Planes**: Vista lista y detalle, hover linking funciona, añadir tratamientos desde odontograma
4. **Transiciones**: Flujo diagnóstico → crear/continuar plan funciona sin fricciones
5. **Responsive**: Funciona en desktop, tablet y móvil
6. **Permisos**: Respeta permisos existentes (odontogram.read/write, treatmentPlans.read/write)
