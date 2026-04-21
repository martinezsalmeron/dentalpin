# Fase C — Multi-especialidad: desinstalar odontograma limpiamente

Documento de diseño para abrir DentalPin más allá del dental: permitir
que clínicas de fisioterapia, estética, veterinaria, medicina general,
etc. usen el mismo software desinstalando el módulo `odontogram` y
dejando operativos el resto de flujos (agenda, pacientes, planes de
tratamiento, presupuestos, facturas, etc.).

**Estado**: borrador inicial, no planificado. Documenta el alcance
para que podamos retomarlo más adelante sin perder contexto.

**Fecha**: 2026-04-21

**Contexto**: tras v2.0.0 (Fase B completa + squash de migraciones),
la arquitectura modular está en su sitio. Es hora de probar que el
"sistema de módulos" es real y no decorativo. El caso de prueba
concreto: desinstalar `odontogram` y que los planes de tratamiento
sigan funcionando añadiendo tratamientos directamente desde el
catálogo (sin odontograma por medio).

---

## 1. Objetivo

Dado un DentalPin recién instalado, ejecutar

```bash
./bin/dentalpin modules uninstall odontogram
```

y que tras reiniciar:

1. El schema no tenga `tooth_records`, `treatments`, `treatment_teeth`,
   `odontogram_history`.
2. Los planes de tratamiento sigan funcionando — crear un plan, añadir
   ítems directamente desde el catálogo (sin diente), completarlos,
   ligarlos a citas.
3. Los presupuestos sigan funcionando — ítems = catalog_item + qty, sin
   tooth_number/surfaces.
4. Las facturas sigan generándose desde presupuestos sin perder ningún
   item.
5. La UI no muestre ni el tab "Clínico/Odontograma" ni ningún picker por
   diente. Todo adaptado al flujo "genérico" (lista plana de
   tratamientos del catálogo).
6. El seed `--profile=medical` crea un escenario demo **sin** datos
   dentales, y el `--profile=dental` sigue funcionando igual que hoy.

Objetivo secundario: dejar el patrón listo para aplicarlo a cualquier
otro módulo `removable: True` (patients_clinical, notifications,
patient_timeline, etc.). Hoy sus manifests dicen `removable: True` pero
en la práctica ninguno es desinstalable limpiamente.

---

## 2. Por qué hoy no funciona

### 2.1 FKs duros apuntan a tablas del odontograma

Del schema post-squash, tres tablas de otros módulos tienen FK a
`treatments` (odontograma):

| Tabla (módulo) | Columna | Destino |
|---|---|---|
| `budget_items` (budget) | `treatment_id` | `treatments.id` |
| `planned_treatment_items` (treatment_plan) | `treatment_id` | `treatments.id` |
| `invoice_items` (billing) | `treatment_id` | `treatments.id` |

Al ejecutar `alembic downgrade` del branch odontograma, el drop de
`treatments` falla porque los FKs todavía existen en tablas de otros
módulos que permanecen instalados.

### 2.2 Lógica de servicio asume que hay odontograma

- `TreatmentPlanService.create_from_odontogram` asume que existe un
  `treatment_id` para cada ítem planificado.
- El sync bidireccional "plan completa → odontograma actualiza
  treatment.status" vive en event handlers.
- `BudgetService` acepta `tooth_number` + `surfaces` en cada línea.
- El catálogo tiene `treatment_scope: tooth|arch|mouth` como concepto
  central; sin odontograma estos valores carecen de sentido pero están
  validados en Pydantic.

### 2.3 Frontend importa odontograma directamente

- `/patients/[id].vue` renderiza `<ClinicalTab>` (patients layer) que a
  su vez importa `OdontogramChart`, `TreatmentPanel`, etc. (odontogram
  layer). Con odontograma desinstalado, esos componentes no se
  auto-importan y la tab da "Failed to resolve component".
- `TreatmentVisualSelector` (shared) asume un picker por diente.
- Presupuesto form tiene tooth picker inline.
- Settings → Catalog ofrece `treatment_scope` + `odontogram_mapping`
  directamente en el form del item.

### 2.4 Seeds son dentales-nativos

`demo_data.py` + `scripts/seed_demo.py` crean tooth_records, treatments
por diente, historial odontograma. No hay ruta alternativa.

### 2.5 Manifest `depends` atan innecesariamente

- `budget.depends = ["patients", "catalog", "odontogram"]`
- `treatment_plan.depends = ["patients", "agenda", "odontogram", "catalog", "budget", "media"]`
- `billing.depends = ["patients", "catalog", "budget"]` (no depende del
  odontograma pero su schema FK-lea igual)

Mientras `budget.depends` liste `odontogram`, no se puede desinstalar
odontograma sin desinstalar budget (el reverse-dep check del processor
lo bloquea).

---

## 3. Decisiones de diseño

### 3.1 FKs cross-module opcionales: patrón "late FK"

Los FKs duros de `budget_items.treatment_id → treatments.id` (y los
dos hermanos) se eliminan de las migraciones de budget/plan/billing.
Se recrean en una **migración secundaria del branch odontograma**
(`odo_0002_link_external_tables.py`) que se aplica después de las
iniciales de budget/plan/billing y crea los FKs cross-module.

Flujo:

- **Install odontograma:** `odo_0001` crea las tablas del odontograma.
  `odo_0002` añade los FKs a budget_items / planned_treatment_items /
  invoice_items. Tablas objetivo ya existen (sus módulos ya estaban
  instalados como dependencia).
- **Uninstall odontograma:** downgrade del branch tira primero
  `odo_0002` (drops FKs) y luego las tablas del odontograma. Las
  columnas `treatment_id` en otros módulos se vuelven plano UUID
  nullable sin constraint. Los registros existentes mantienen sus UUIDs
  pero apuntan a tablas que ya no existen — la lógica de aplicación
  tratará esos registros como "legacy" y los servirá sin resolver.

Decisión: **mantenemos el UUID histórico** en vez de nullear (podría
haber datos históricos que el usuario quiera conservar si reinstala
odontograma más tarde). La app trata el FK como "soft link" — si la
tabla remota no existe, se ignora.

### 3.2 Odontograma pasa a branch alembic propio

Para que el round-trip install/uninstall funcione por módulo, el
odontograma necesita su propio branch alembic (no estar en la cadena
lineal).

```python
# backend/app/modules/odontogram/migrations/versions/odo_0001_initial.py
revision = "odo_0001"
down_revision = None
branch_labels = ("odontogram",)
depends_on = ("pat_0001", "cat_0001")

# backend/app/modules/odontogram/migrations/versions/odo_0002_link_external.py
revision = "odo_0002"
down_revision = "odo_0001"
depends_on = ("bud_0001", "tp_0001", "bil_0001")
```

El processor ejecuta:
- Install: `alembic upgrade odontogram@head`
- Uninstall: `alembic downgrade <base_rev>` (el rev previo al install)

Esto probablemente choque con el bug de Alembic (`KeyError` en
`heads.remove`) que detectamos durante el squash cuando mezclamos
branches + depends_on. La solución es ser cuidadosos con el orden de
install — asegurar que el branch del odontograma se cree siempre
después de sus deps, no en paralelo.

### 3.3 Manifest depends → runtime semántica, no schema

Las dependencias declaradas en `manifest.depends` deben reflejar la
**capacidad funcional** que un módulo ofrece si el otro existe, no el
schema. Propuesta:

- `budget.depends = ["patients", "catalog"]` (no más odontograma)
- `treatment_plan.depends = ["patients", "agenda", "catalog", "budget", "media"]`
  (no más odontograma)
- `odontogram.depends = ["patients", "catalog"]` + nueva propiedad
  `optional_integrations = ["budget", "treatment_plan", "billing"]` —
  declara que *enriquece* esos módulos si están instalados pero no los
  requiere.

El processor lee `optional_integrations` para saber qué migraciones
tardías ejecutar/revertir.

### 3.4 Servicios con guard `is_module_installed(...)`

Nueva helper `app.core.plugins.registry.is_module_installed(name) -> bool`
que consulta `core_module` table. Los servicios lo usan:

```python
class TreatmentPlanService:
    async def create_planned_item(self, db, data):
        if "treatment_id" in data and not is_module_installed("odontogram"):
            raise HTTPException(400, "odontogram not installed")
        ...
```

Event handlers igual — si odontograma no está, el handler
`odontogram.treatment.performed` no existe (el bus nunca lo invoca).

Los endpoints que **sólo tienen sentido con odontograma** (sync plan
↔ treatment) se sirven sólo desde el módulo odontograma. Si está
desinstalado, el endpoint no existe — 404 natural.

### 3.5 Frontend: slots, no imports

Conversión sistemática:

| Antes (import directo) | Después (slot) |
|---|---|
| `<ClinicalTab />` en patient detail | `<ModuleSlot name="patient.detail.tab.clinical" />` |
| `<OdontogramChart />` dentro de `<ClinicalTab>` | componente registrado por odontograma en su propio layer |
| `<TreatmentVisualSelector />` en budget/plan modals | queda si es compatible con catalog puro; añadir `variant: "tooth" \| "flat"` con fallback `"flat"` |
| Catalog settings `treatment_scope` inputs | `<ModuleSlot name="catalog.item.form.extras" />` — odontograma registra tooth/surface inputs ahí |

Cada layer declara en su `slots.ts` qué componentes registra en qué
slots. Patient detail page simplemente llama a `<ModuleSlot>` y recibe
lo que haya disponible. Si odontograma no está instalado, el slot
queda vacío o se renderiza un fallback `"Sin datos clínicos"`.

### 3.6 Catalog: modelo genérico + extras opcionales

`TreatmentCatalogItem` queda como núcleo genérico. Los campos
dental-específicos (`treatment_scope`, `default_surfaces`,
`odontogram_treatment_type`) pasan a una tabla
`odontogram_catalog_extras` propiedad del odontograma, con FK 1:1 a
`treatment_catalog_items.id`. Al desinstalar odontograma se va solo.

`TreatmentOdontogramMapping` se mueve de catalog a odontogram (donde
siempre debió estar).

Validación Pydantic: si el item no tiene extras odontograma, los
campos son `None`. El frontend lo maneja con el slot del formulario.

### 3.7 Perfiles de clínica

Nueva columna `Clinic.specialty: str` — `dental`, `physio`,
`aesthetic`, `vet`, `medical_general`, `custom`. Metadata pura; la app
la usa para:

- Elegir qué módulos instalar por defecto en el primer setup
- Preseleccionar i18n labels ("paciente" vs "cliente" vs "mascota")
- Cargar seed data apropiado (`demo_data_dental.py`,
  `demo_data_physio.py`...)
- Mostrar/ocultar ciertas pestañas UI por defecto

No se añade lógica dura basada en specialty — siempre vence lo que
diga el registry de módulos instalados.

### 3.8 Seeds por perfil

```bash
./scripts/seed-demo.sh --profile dental    # default, como hoy
./scripts/seed-demo.sh --profile medical   # sin odontograma
./scripts/seed-demo.sh --profile physio    # sin odontograma, sesiones en vez de tratamientos
```

Cada perfil tiene su `data_<profile>.yaml` y su Python seed script
(igual de válidos: `seed_demo_medical.py` reutiliza lo que puede y
salta lo que no).

---

## 4. Scope de Fase C

### 4.1 In-scope (caso base: desinstalar odontograma)

**Backend:**
- Promover `odontogram` a branch alembic propio con migración `odo_0002`
  de cross-FKs.
- `optional_integrations` en manifest + lectura en processor.
- Guards `is_module_installed` en servicios de budget, treatment_plan,
  billing que usan treatment_id.
- Extraer `treatment_scope`/`surfaces` fuera del core catalog:
  `odontogram_catalog_extras` tabla propiedad de odontograma.
- Endpoints dental-específicos movidos al módulo odontograma (ya casi
  están).

**Frontend:**
- `<ClinicalTab />` pasa a `<ModuleSlot name="patient.detail.tab.clinical" />`.
- `TreatmentVisualSelector` gana modo `variant: "flat" | "tooth"` con
  fallback seguro.
- Budget item form: tooth picker vuelve slot.
- Catalog settings: campo `treatment_scope` se mueve al slot
  `catalog.item.form.extras`.

**Seeds:**
- `--profile dental|medical|physio` — al menos dos para validar.

**Tests:**
- `test_uninstall_odontogram.py`: install todo, luego uninstall
  odontograma, verifica que el schema no tiene tablas odontograma,
  planes/presupuestos/facturas siguen operando.
- E2E Playwright: un perfil medical, verifica que `/patients/:id` NO
  tiene tab "Clínico" pero SÍ tab planes/presupuestos y se pueden
  crear ítems sin diente.

### 4.2 Out-of-scope

- Generalización completa a N especialidades. Cubrir "clínica física"
  es suficiente para validar el patrón. Añadir vet/aesthetic/etc. es
  trabajo mecánico adicional una vez el patrón está probado.
- Rebranding dinámico ("paciente" → "cliente" / "mascota"). Es un
  ejercicio de i18n profundo que se puede abordar separado.
- Migración de datos existentes entre perfiles (instalar como dental,
  luego cambiar a medical). Overkill; los perfiles son de
  configuración inicial.

---

## 5. Plan de ejecución

Secuencial, cada etapa mergeable a main sin romper nada.

### Etapa C.1 — Backend: branch alembic + FKs tardíos (~2-3 días)

1. Mover `odontogram/migrations/versions/odo_0001_initial.py` a branch
   propio: `branch_labels=('odontogram',)`, `down_revision=None`,
   `depends_on=('pat_0001', 'cat_0001')`.
2. Sacar los FKs de `budget_items.treatment_id`,
   `planned_treatment_items.treatment_id`,
   `invoice_items.treatment_id` de sus migraciones iniciales (dejar la
   columna como UUID plain).
3. Crear `odo_0002_link_external.py` con `op.create_foreign_key` para
   los tres. `depends_on=('bud_0001', 'tp_0001', 'bil_0001')`.
4. Verificar con el test round-trip (instalar todo → uninstall
   odontograma → verificar tablas dropeadas → reinstalar).
5. Actualizar `alembic.ini::version_locations` — sigue listándolos
   todos pero el de odontograma ahora es "branch" independiente.

### Etapa C.2 — Servicios con guards (~1-2 días)

1. `app.core.plugins.registry.is_module_installed(name: str) -> bool`
   (consulta `core_module.state`).
2. Guards en `BudgetService`, `TreatmentPlanService`, `BillingService`
   donde hoy requieren `treatment_id`. Añadir alternativa "sin
   treatment" (sólo `catalog_item_id`).
3. Pydantic schemas: `treatment_id: UUID | None = None`.
4. Unit tests para las dos vías (con odontograma / sin odontograma).

### Etapa C.3 — Catalog: extraer extras odontograma (~1-2 días)

1. Crear tabla `odontogram_catalog_extras(catalog_item_id FK, scope,
   default_surfaces, odontogram_treatment_type)` en migración
   `odo_0001`.
2. Migrar datos de los campos actuales en `treatment_catalog_items` a
   la nueva tabla (backfill en migración).
3. Dropear esos campos del core `treatment_catalog_items` en migración
   de `catalog` (breaking, OK porque no hay prod).
4. Mover `TreatmentOdontogramMapping` de catalog a odontogram.
5. Re-generar catalog/odontogram schemas + services.

### Etapa C.4 — Frontend: slots en lugar de imports (~3-5 días)

1. Patient detail: `<ClinicalTab>` → `<ModuleSlot name="patient.detail.tab.clinical">`.
   Odontograma registra el contenido de la tab en `slots.ts`.
2. Budget/plan forms: `TreatmentVisualSelector` gana dos variantes.
   Odontograma + flat. Selección se hace por `is_module_installed`
   (vía `/api/v1/modules/-/active`).
3. Catalog settings form: campos dental al slot
   `catalog.item.form.extras`.
4. Treatment plan detail: listas de items sin dependencia de
   treatment.
5. E2E Playwright para el caso sin odontograma.

### Etapa C.5 — Perfiles de seed (~1 día)

1. `Clinic.specialty` (migración en core, nullable default `'dental'`).
2. `scripts/seed_demo_medical.py` — pacientes, agenda, catálogo
   médico, planes sin odontograma.
3. `./scripts/seed-demo.sh --profile` acepta argumento.
4. Docs en `README.md`.

### Etapa C.6 — Tests formales (~1-2 días)

1. `test_uninstall_odontogram.py` — install → uninstall → re-install.
   Incluye aserciones de schema y de endpoints.
2. Playwright `medical-smoke.spec.ts` — login, crear paciente, crear
   plan, añadir item de catálogo sin diente, todo verde.

**Total realista: 10-15 días.** Puede recortarse bajando la calidad
del frontend (hacer el slot pattern sólo en los dos sitios más
visibles, el resto queda "installed-only") y saltándose perfiles de
seed.

---

## 6. Decisiones abiertas

Preguntas pendientes que hay que cerrar antes de arrancar C.1:

1. **¿Los UUIDs en `budget_items.treatment_id` al uninstall —
   NULLIFY o leave-as-is?** (§3.1) Propuesta: leave-as-is +
   tratamiento en servicio como soft-ref. Requiere handling explícito
   en cada read path.

2. **¿El `Clinic.specialty` es enum fijo o string libre?** Empezar con
   enum (`'dental'`, `'medical'`, `'physio'`, `'vet'`, `'aesthetic'`)
   y extensible vía PR al core.

3. **¿Qué pasa con los datos históricos si uninstalo odontograma en
   una clínica con años de tratamientos?** Deberíamos:
   (a) Exportar un `.sql` dump de `treatments`/`tooth_records` al
   uninstall, guardarlo en `storage/module_backups/`, y permitir
   reinstall + restore.
   (b) Bloquear uninstall si hay >0 filas a menos que se pase
   `--force`.

   Propuesta: combinar ambas — dump automático, warning en CLI/UI,
   `--force` para no confirmar.

4. **`optional_integrations`: ¿es atributo del manifest o convención
   implícita?** Explícito es más claro; los tests pueden validar que
   las migraciones `odo_0002_link_external` sólo tocan tablas de
   módulos listados en `optional_integrations`.

5. **Catalog sin odontograma: ¿seguimos usando
   `treatment_catalog_items` como nombre?** Sí, por compatibilidad.
   Podría renombrarse a `catalog_items` en un v3 si nos molesta el
   sesgo dental.

6. **Los items de plan/presupuesto sin treatment_id: ¿cómo se
   identifican visualmente?** Hoy el dientePicker da contexto visual
   ("incisivo superior derecho"). Sin él, el item es sólo "Limpieza"
   + qty. Posible: añadir `notes` o `body_location_label` text free.

---

## 7. Riesgos

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Bug de Alembic `heads.remove` al mezclar branch + `depends_on` cíclicos | Alta | Secuencia install cuidada (odo siempre después de bud/tp/bil). Si reaparece, simplificar `depends_on` y hacer el ordering imperativo en el processor. |
| Frontend slots "no aparecen" por bug de timing de hydration | Media | Los slots ya funcionan en prod; bajo riesgo si copiamos patrón de `patient.detail.sidebar` (ya validado). |
| Clínica existente con datos dentales ejecuta uninstall sin backup | Alta | Dump automático pre-uninstall + flag `--force` + warning visual claro en UI. |
| Perfiles de seed divergen y se desincronizan | Media | Cada perfil reutiliza helpers comunes (`create_demo_users`, `create_demo_clinic`) y sólo personaliza lo que difiere. |

---

## 8. Conexión con Fase B

Fase C **valida** Fase B. La modularidad de B.6 (Nuxt layers) +
manifest + registry sólo tiene sentido si realmente se puede
desinstalar un módulo. Hasta que eso no funcione end-to-end, todo es
"una app grande organizada en carpetas". Fase C convierte el sistema
modular en real.

Todo lo que hicimos en B — layers, slots, módulos removables,
`/modules/-/active`, processor — está específicamente diseñado para
soportar este caso. No hace falta rehacer nada; hace falta aplicar
consistentemente el patrón en los 5-10 sitios del frontend/backend
donde hoy hay acoplamiento duro.

---

## 9. Siguientes pasos

1. Revisar y validar este diseño.
2. Cerrar las preguntas abiertas de §6.
3. Arrancar C.1 en branch `feat/fase-c-uninstallable-odontogram`.
4. Cada etapa C.* merge a main con PR propio (patrón Q6 de Fase B).

No hay prisa — v2.0 es estable y cubre el caso dental. Fase C se
aborda cuando haya demanda concreta (partner con interés en una
vertical no-dental) o cuando queramos validar que la arquitectura
modular cumple su promesa.
