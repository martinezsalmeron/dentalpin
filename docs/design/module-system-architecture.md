# Sistema de módulos DentalPin — Arquitectura v1

Documento de diseño para refactorizar el sistema modular actual hacia una arquitectura tipo Odoo moderna, preparada para un ecosistema open source sano (oficial + community) y sostenible a 5 años.

**Estado**: propuesta para validación. Plan técnico detallado se redacta después de aprobar este documento.

**Fecha**: 2026-04-19

**Contexto**: el core de DentalPin está casi listo. Antes de construir módulos opcionales (facturación, odontograma, presupuestos, planes de tratamiento, etc.) se refactoriza la plataforma modular para que módulos oficiales y comunitarios funcionen bajo el mismo contrato, con instalación/desinstalación limpia y reinicio explícito.

**Scope v1 (Fase A)**: se construye toda la infraestructura modular (backend + frontend slots + Nuxt layers + CLI) sin refactorizar el módulo `clinical` existente. Clinical queda como **módulo legacy especial** (modelos Patient/Appointment/AppointmentTreatment/PatientTimeline en su sitio actual, migraciones en main linear de Alembic, componentes frontend en sus carpetas actuales). Funciona bajo el contrato nuevo pero no se extrae ni se parte.

**Fase B diferida**: split de `clinical` en core (Patient mínimo) + módulos `patients_clinical` + `agenda`, con reorganización de migraciones, rutas API, permisos y componentes frontend. Se aborda cuando aparezca motivo concreto (cliente laboratorio dental, auditoría GDPR específica, reorganización para billing v2). No bloquea nada en Fase A.

---

## 1. Objetivos y no-objetivos

### Objetivos v1

- Cada módulo es una unidad autocontenida con manifiesto, modelos, migraciones, routers, eventos, UI y ciclo de vida propios.
- Instalación y desinstalación por CLI y UI, con confirmación de reinicio.
- Dependencias entre módulos resueltas con topological sort. Fallo limpio si hay ciclos o dependencias ausentes.
- Uninstall limpio: DB vuelve a estado previo a la instalación (schema + seed data), con backup automático de las tablas del módulo antes de tocar nada.
- Recuperación automática de fallos a mitad de operación (idempotencia + log de pasos).
- Core no importa módulos. Nunca. Comunicación vía event bus, slots UI y hooks.
- Módulos oficiales viven en el monorepo y se distribuyen como paquetes Python internos. Módulos comunitarios se distribuyen por PyPI (o equivalente) como paquetes externos.
- Community contributor puede shippear un módulo completo (backend + UI) sin tocar el repo principal.
- Sistema preparado para SaaS multi-tenant en futuro (toggle de activación por tenant dentro del set pre-aprobado de módulos).

### No-objetivos v1 (explícito para evitar scope creep)

- Hot-install sin reinicio del backend.
- Module federation frontend (bundles runtime separados). Reevaluable v2+.
- Tool Registry / integración LLM en el manifiesto. Separado.
- Marketplace, firmas digitales, enforcement real de permisos declarativos.
- Versionado SemVer formal de la Core API (se documenta, no se versiona formalmente hasta primer consumidor externo real).
- SaaS multi-tenant con sets de módulos distintos por cliente sin rebuild (requiere federation).
- Internationalization del propio sistema de módulos (mensajes de error, metadata) más allá de lo existente.

---

## 2. Decisiones arquitectónicas clave

Síntesis de las 8 decisiones que condicionan el resto del diseño.

### 2.1 Frontera core / módulo (decisión Q1)

**Core** (no es un módulo, no se desinstala, vive en `backend/app/core/`):

- Plataforma modular: `ModuleRegistry`, `BaseModule`, event bus, slots API, lifecycle orchestration.
- Auth y RBAC: `User`, `Clinic`, `ClinicMembership`, JWT, permisos namespaced.
- Infraestructura: DB base, Alembic multi-branch orchestrator, logging, config.

**Módulo legacy especial (Fase A)**:

- `clinical`: contiene Patient, Appointment, AppointmentTreatment, PatientTimeline, endpoint professionals. Se mantiene en su ubicación actual (`backend/app/modules/clinical/`). Se registra en el nuevo sistema como módulo `official`, `removable: False`, `auto_install: True`, pero con flag interno `legacy: True`. Sus migraciones siguen en la main linear de Alembic, no en branch propio. Su frontend sigue en `frontend/app/components/clinical/` y `frontend/app/pages/` — no se empaqueta como Nuxt layer.

**Módulos oficiales nuevos** (viven en `backend/app/modules/`, contrato completo desde día uno, `category: "official"`, `removable: False`, `auto_install: True`):

- `catalog`: catálogo de tratamientos, VAT types, categorías.
- `odontogram`: extensión odontograma más allá de lo que ya hay.
- `treatment_plans`: planes de tratamiento, scope arcadas/piezas.
- `quotes` (presupuestos): generación, aceptación, versionado.
- `billing`: facturación, recibos, pagos.
- `notifications`: emails, plantillas, eventos transaccionales.

Nota: algunos de estos (`catalog`, `budget`, `billing`, `notifications`, `treatment_plan`) ya existen en el código actual. En Fase A se refactorizan al contrato nuevo (manifest declarativo, branch Alembic propio, layer frontend, lifecycle hooks) — no se crean desde cero. Lo que se difiere es tocar `clinical`.

**Fase B diferida — split de clinical**:

- Core absorbería Patient mínimo (id, clinic_id, first_name, last_name, email, phone, date_of_birth, status, timestamps).
- Módulo `patients_clinical`: medical_history, emergency_contact, legal_guardian, alergias, consentimientos. GDPR auditable aparte.
- Módulo `agenda`: Appointment, AppointmentTreatment, PatientTimeline, validación professionals, calendar views.

**Razón para diferir**: mover modelos, API paths, permisos y componentes frontend de clinical son ~10-14 días de refactor con riesgo de regresiones en flujos funcionando (citas, pacientes, odontograma). La infraestructura modular no lo necesita. Cuando se aborde Fase B, el split es mecánico (mover archivos + migraciones de datos + actualizar manifest), no rediseño.

**Razón futura para Patient-en-core**: es raíz universal de 100% de módulos dentales. Si fuera módulo, cada módulo declararía `depends: ["patients"]` — ruido permanente. Laboratorio dental usando DentalPin con entidad "cliente" en vez de "paciente" es caso <1% que no justifica la fricción diaria del 99%. GDPR se resuelve con el módulo `patients_clinical` separado que contiene los datos sensibles reales.

### 2.2 Distribución: entry points fase 1, workspace fase 2 (Q2)

**Fase 1 (este plan)**:
- Un único `backend/pyproject.toml` que declara entry points Python para todos los módulos internos.
- Módulos oficiales viven como subpackages: `backend/app/modules/<name>/` con su `manifest.py`.
- Discovery principal: `importlib.metadata.entry_points(group="dentalpin.modules")`.
- Discovery secundario (modo dev): escaneo de `backend/app/modules/` para módulos no registrados como entry point pero con manifest válido. Útil mientras se desarrolla un módulo nuevo.
- Comunidad publica su módulo como paquete en PyPI con su propio `pyproject.toml` declarando entry point `dentalpin.modules`.

**Fase 2 (futuro, no en este plan)**:
- Split cada módulo oficial en su propio `pyproject.toml` dentro del monorepo.
- Workspace gestionado con `uv`.
- Meta-paquete `dentalpin-standard` agrupa core + módulos oficiales para instalación single-command.
- Refactor build system + Docker + CI aislado, no mezclado con este trabajo.

**Razón**: el mecanismo de discovery correcto desde el principio es innegociable. El build system en workspace es refactor opcional que no cambia contratos.

### 2.3 Reinicio explícito manual (Q3)

- Instalación/desinstalación/upgrade de módulo marca estado `to_*` en `core_module` y responde al usuario "Reinicio requerido".
- UI muestra badge persistente "N módulos pendientes de reinicio. [Reiniciar ahora]".
- Botón llama a endpoint `POST /api/modules/restart` → el proceso llama `sys.exit(0)` controlado → Docker `restart: unless-stopped` respawna en 3-5 segundos.
- Al arrancar, el `lifespan` del FastAPI procesa todos los `to_*` antes de aceptar tráfico. Si falla un módulo, se loguea, se marca en `core_module.error_message`, y el resto arranca sin él.
- Modo dev: `uvicorn --reload` detecta cambios en archivos y reinicia automáticamente. Mismo flujo.
- Sin graceful restart vía señales (SIGHUP, SIGUSR2) en v1. Complejidad innecesaria.

### 2.4 Alembic multi-branch per-módulo (Q4)

**Scope Fase A — mixto linear + branches**:
- Las 28 migraciones existentes **permanecen en main linear** tal cual. Incluye core auth + clinical (Patient, Appointment, etc.) + migraciones existentes de catalog, budget, billing, notifications, treatment_plan.
- Los módulos existentes que se refactoran al contrato nuevo (catalog, budget, billing, notifications, treatment_plan) **no migran sus revisions históricas** a un branch propio. Sus migraciones históricas siguen en main linear. Sus migraciones nuevas (desde Fase A en adelante) van a un branch propio con su label.
- Los módulos completamente nuevos (`quotes`, odontogram expansion) nacen directamente con branch propio desde la primera migración.
- `core_module.base_revision` de los módulos legacy-linear se marca con la revision de main linear previa al switch — su uninstall con downgrade está limitado por esto (ver más abajo).
- Configuración Alembic: `version_locations` incluye main linear (`backend/alembic/versions/`) + branches de módulos nuevos.

**Limitación explícita de Fase A**: el uninstall clean con downgrade completo solo funciona para módulos nacidos con branch propio y para migraciones nuevas de módulos refactorizados. El contenido legacy (schema de clinical, schema histórico de catalog/billing/etc.) no se desinstala completamente — es tratado como "schema permanente" de la app. Es aceptable porque en Fase A ningún módulo legacy es realmente desinstalable (`removable: False`).

**Fase B (diferida)**: refactor total. Todas las migraciones históricas se clasifican en branches por módulo. `clinical` se parte en core (Patient mínimo) + `patients_clinical` + `agenda`, cada uno con su branch limpio y `base_revision` al arranque de su branch. Downgrade completo operativo para todos.

**Dependencias entre branches**: una migración nueva puede declarar `depends_on=["billing_<revid>"]` si referencia tablas de otro módulo. Si referencia tablas del schema legacy, no hace falta `depends_on` — están siempre presentes.

**Decisión política sobre FKs cross-module**: permitidas **solo** hacia módulos declarados en `depends` del manifest, o hacia el schema legacy (tablas de clinical). Test de CI valida que no hay FKs a tablas de módulos fuera de `depends`. Si `billing` referencia `patient.id` (tabla legacy de clinical), `clinical` debe estar en `billing.depends`.

### 2.5 Frontend: Opción A + Nuxt Layers + CLI orchestration + slots (Q5)

Piedra angular del ecosistema open source.

**Mecánica**:
- Cada módulo (oficial o comunitario) incluye una carpeta `frontend/` dentro de su paquete Python, estructurada como Nuxt Layer: `pages/`, `components/`, `composables/`, `i18n/`, `nuxt.config.ts` propio.
- CLI `dentalpin modules install <name>` hace:
  1. `pip install` del paquete (si es community) o activación (si es interno).
  2. Detecta la carpeta `frontend/` dentro del paquete instalado.
  3. Patchea `nuxt.config.ts` del frontend añadiendo el path al array `extends`.
  4. Marca el estado `to_install` y solicita reinicio.
  5. Tras el reinicio del backend, orquesta rebuild del contenedor frontend (`docker-compose build frontend && up -d frontend`).
- Backend expone `GET /api/modules/active` con navigation items, permissions, metadata. Frontend construye menú dinámico al login leyendo esta respuesta.
- Sistema de **slots UI** para extension points dentro de páginas del core/otros módulos: `<ModuleSlot name="patient.detail.sidebar" :ctx="patient" />`. Los módulos registran componentes a slots vía composable `registerSlot(name, { component, order, condition })`.

**Qué permite al community contributor**:
- Shippear un módulo completo (backend + UI) como paquete único en PyPI.
- NO hacer PR al repo principal.
- La clínica self-hosted instala con un comando, acepta rebuild de 30-60s, y el módulo aparece.

**Qué NO permite v1**:
- Hot-install UI sin rebuild del contenedor frontend.
- SaaS multi-tenant con módulos distintos por cliente sin rebuild. Solución SaaS: pre-bundlear todos los módulos aprobados por el provider, los tenants togglean visibilidad — no "instalan" paquetes nuevos. Community modules fuera del set aprobado del SaaS no están disponibles para ese SaaS (patrón Shopify).

**Migración futura a federation**: si se necesita, el contrato de los módulos no cambia (mismos manifest, slots, API backend). Solo cambia cómo se carga el bundle del frontend. Diseño sobrevive la migración.

### 2.6 Tool Registry / LLM fuera del plan (Q6)

- No se añaden campos `provides.tools` al manifest hoy.
- Cuando exista Tool Registry, se añade al `BaseModule` un hook opcional `get_tools() -> list[Tool]` análogo al actual `get_event_handlers()`. Los módulos lo declaran en código, no en manifest.

### 2.7 Trust tiers mínimo declarativo (Q7)

- Manifest: `category: "official" | "community"`. Punto.
- UI muestra badge verde "Oficial" o ámbar "Comunidad" en la lista de módulos.
- Sin marketplace, sin firmas, sin permisos declarativos, sin enforcement. Todo eso = v2+ cuando exista ecosistema comunitario real.

### 2.8 CLI `python -m app.cli modules ...` (Q8)

- Comandos: `list`, `install`, `uninstall`, `upgrade`, `activate`, `deactivate`, `status`, `doctor` (diagnóstico).
- Vive dentro del contenedor backend. Uso típico: `docker-compose exec backend python -m app.cli modules list`.
- Lógica en `ModuleService`. CLI y API HTTP consumen el mismo servicio — un único punto de verdad.
- Entry point `dentalpin-admin` (console script) se añade en fase 2 cuando exista distribución CLI real.

---

## 3. Estructura de un módulo

Contrato estándar, idéntico para oficial y comunitario.

```
dentalpin-billing/                         # repo community o directorio interno
├── pyproject.toml                         # declara entry point "dentalpin.modules"
├── dentalpin_billing/
│   ├── __init__.py                        # exporta MANIFEST y clase Module
│   ├── manifest.py                        # metadata declarativa
│   ├── lifecycle.py                       # install(), uninstall(), post_upgrade()
│   ├── models.py                          # SQLAlchemy ORM
│   ├── schemas.py                         # Pydantic
│   ├── router.py                          # FastAPI APIRouter
│   ├── service.py                         # lógica de negocio
│   ├── events.py                          # handlers event bus
│   ├── permissions.py                     # permisos del módulo
│   ├── migrations/                        # Alembic versions, branch label="billing"
│   │   └── versions/
│   ├── data/                              # seed declarativo
│   │   ├── default_tax_rates.yaml
│   │   └── invoice_series.yaml
│   └── frontend/                          # Nuxt Layer
│       ├── nuxt.config.ts                 # layer config
│       ├── pages/billing/
│       ├── components/
│       ├── composables/
│       ├── i18n/
│       └── slots.ts                       # registerSlot() calls
├── tests/
└── README.md
```

### 3.1 Manifest

```python
# dentalpin_billing/manifest.py
MANIFEST = {
    # Identidad
    "name": "billing",
    "version": "1.0.0",
    "summary": "Facturación, recibos y pagos",
    "author": "DentalPin Core Team",
    "license": "BSL-1.1",
    "category": "official",                 # "official" | "community"

    # Compatibilidad
    "min_core_version": "1.0.0",
    "max_core_version": "2.0.0",            # opcional, upper bound

    # Dependencias
    "depends": ["patients_clinical", "catalog"],   # módulos DentalPin
    "external_dependencies": {
        "python": ["weasyprint>=60"],       # validado en discover
    },

    # Políticas
    "installable": True,
    "auto_install": True,                   # oficiales auto-instalan en bootstrap
    "removable": False,                     # oficiales no se desinstalan por UI

    # Datos
    "data_files": [
        "data/default_tax_rates.yaml",
        "data/invoice_series.yaml",
    ],

    # Frontend
    "frontend": {
        "layer_path": "frontend",           # relativa al paquete
        "navigation": [                     # nav items, filtrados por permiso
            {
                "label": "nav.billing",
                "to": "/billing/invoices",
                "icon": "i-lucide-receipt",
                "permission": "billing.invoices.read",
                "order": 40,
            }
        ],
    },
}
```

### 3.2 Clase `Module`

```python
# dentalpin_billing/__init__.py
from dentalpin.core.plugins import BaseModule
from .manifest import MANIFEST
from .router import router
from .models import Invoice, InvoiceLine
from .events import on_appointment_completed
from . import lifecycle

class BillingModule(BaseModule):
    manifest = MANIFEST

    def get_models(self):
        return [Invoice, InvoiceLine]

    def get_router(self):
        return router

    def get_event_handlers(self):
        return {"appointment.completed": on_appointment_completed}

    def get_permissions(self):
        return ["invoices.read", "invoices.write", "payments.read", "payments.write"]

    def install(self, ctx):
        lifecycle.install(ctx)

    def uninstall(self, ctx):
        lifecycle.uninstall(ctx)

    def post_upgrade(self, ctx, from_version):
        lifecycle.post_upgrade(ctx, from_version)
```

### 3.3 Entry point en `pyproject.toml`

```toml
[project.entry-points."dentalpin.modules"]
billing = "dentalpin_billing:BillingModule"
```

---

## 4. Estados y ciclo de vida

### 4.1 Estados (tabla `core_module`)

```
uninstalled  ──install──►  to_install ──restart──►  installed
installed    ──upgrade──►  to_upgrade ──restart──►  installed
installed    ──uninstall──►  to_remove ──restart──►  uninstalled
installed    ◄────toggle────►  disabled          (sin reinicio, sin tocar DB)
```

**Invariantes**:
- Solo los estados `to_*` son transitorios. Tras cada reinicio, el registry los resuelve.
- Un módulo en `disabled` tiene migraciones aplicadas y datos intactos, pero su router/handlers no están montados en el proceso actual.
- `error` no es un estado: fallos se guardan en `core_module.error_message` pero el estado lógico se mantiene. Ejemplo: si `to_install` falla, queda `to_install` con error → admin lo resuelve o marca `to_remove`.

### 4.2 Tabla `core_module`

```sql
CREATE TABLE core_module (
    name              VARCHAR PRIMARY KEY,
    version           VARCHAR NOT NULL,
    state             VARCHAR NOT NULL,     -- enum
    category          VARCHAR NOT NULL,     -- official | community
    removable         BOOLEAN NOT NULL,
    auto_install      BOOLEAN NOT NULL,
    legacy            BOOLEAN NOT NULL DEFAULT false,  -- Fase A: schema en main linear
    installed_at      TIMESTAMPTZ,
    last_state_change TIMESTAMPTZ NOT NULL DEFAULT now(),
    base_revision     VARCHAR,              -- Alembic rev previa a instalar (null para legacy)
    applied_revision  VARCHAR,              -- Alembic head del módulo (null para legacy)
    manifest_snapshot JSONB NOT NULL,       -- manifest en el momento de install
    error_message     TEXT,
    error_at          TIMESTAMPTZ
);
```

**Nota sobre `legacy`**: un módulo con `legacy=true` no tiene branch Alembic propio. Sus migraciones viven en main linear. Uninstall con downgrade está bloqueado para módulos legacy (en Fase A todos son `removable: False` de todos modos). Desaparece el flag cuando se aborde Fase B y se splittee clinical.

### 4.3 Tabla `core_module_operation_log`

Atomicidad y retomabilidad. Cada paso de una operación se loguea antes de ejecutarse. Si el proceso muere, al reiniciar el registry puede retomar desde el último paso completado.

```sql
CREATE TABLE core_module_operation_log (
    id           BIGSERIAL PRIMARY KEY,
    module_name  VARCHAR NOT NULL,
    operation    VARCHAR NOT NULL,         -- install | uninstall | upgrade
    step         VARCHAR NOT NULL,         -- backup | migrate | seed | finalize
    status       VARCHAR NOT NULL,         -- started | completed | failed
    details      JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 4.4 Flujo de `install`

1. Resolver dependencias recursivamente. Si alguna no está instalada, marcar también `to_install`.
2. Validar compatibilidad: `min_core_version`, `external_dependencies` Python.
3. Escribir estado `to_install` + snapshot del manifest.
4. Responder "Reinicio requerido".

Al reiniciar, el `lifespan` procesa los `to_*` antes de aceptar tráfico. Para cada módulo en `to_install`, en orden topológico:

5. `core_module_operation_log`: step="backup" started → volcar tablas relevantes (si re-install sobre datos existentes; primera install no aplica) → completed.
6. step="migrate" started → Alembic upgrade hasta head del módulo → guardar `base_revision` y `applied_revision` → completed.
7. step="seed" started → ejecutar `lifecycle.install(ctx)` que carga `data_files` vía external IDs → completed.
8. step="finalize" started → actualizar state a `installed`, montar router, suscribir handlers → completed.

Si algún step falla: step=failed, error_message guardado, estado queda en `to_install`. Admin decide: reintentar tras arreglar, o rollback manual.

### 4.5 Flujo de `uninstall`

Dado la sensibilidad, regla estricta:

1. Resolver reverse dependencies. Si algún módulo instalado depende del que se quiere quitar, bloquear con mensaje explícito.
2. Si `removable: False` y no viene flag `--force`, bloquear.
3. Escribir estado `to_remove`.
4. Responder "Reinicio requerido. Se hará backup automático antes de borrar datos."

Al reiniciar:

5. step="backup" → dump de todas las tablas del módulo a `backups/module_<name>_<timestamp>.sql` dentro del volumen persistente. Loggear ruta.
6. step="delete_data" → borrar todos los registros con `external_id` del módulo (orden inverso a FKs).
7. step="migrate_down" → Alembic downgrade hasta `base_revision` del módulo.
8. step="clean_state" → limpiar subscripciones persistidas (si las hubiera), permisos del módulo.
9. step="finalize" → state = `uninstalled`.

**Política de datos de usuario**: hard uninstall + backup automático + confirmación explícita en UI ("escribe el nombre del módulo para confirmar"). Modelo honesto.

---

## 5. Discovery y bootstrap

### 5.1 Fuentes de discovery

1. **Entry points Python** (principal): `importlib.metadata.entry_points(group="dentalpin.modules")`. Cubre módulos oficiales e instalados desde PyPI.
2. **Filesystem scan** (modo dev): escaneo de `backend/app/modules/` buscando paquetes con `manifest.py`. Se incluye en discover si no hay entry point equivalente. Controlado por env var `DENTALPIN_DEV_MODULE_SCAN=true`.

### 5.2 Secuencia bootstrap

En el `lifespan` de FastAPI, antes de aceptar tráfico:

1. **Discover**: cargar todos los manifests (sin ejecutar código del módulo). Validar schema, `min_core_version`, que todas las `depends` existan como manifests descubiertos.
2. **Reconciliar con DB**:
   - Módulo en disk y no en DB → insert como `uninstalled`.
   - Módulo en DB como `installed` pero no en disk → **error crítico, no arrancar**. Log explícito. Admin debe restaurar el paquete o marcar manualmente `uninstalled` con `python -m app.cli modules orphan <name>`.
   - Módulo en DB con versión distinta a la del manifest en disk → marcar `to_upgrade` automáticamente.
3. **Detectar ciclos**: topo-sort. Si hay ciclo, fail-loud.
4. **Bootstrap inicial** (solo primera vez, DB vacía): marcar todos los módulos con `auto_install: True` como `to_install`.
5. **Procesar `to_*` pendientes**: en orden topológico. Si falla uno, continúa con los independientes y marca el fallido con error.
6. **Montar en runtime**: para cada módulo `installed` y no `disabled`, montar router en `/api/v1/<name>/`, suscribir event handlers, registrar permisos.
7. FastAPI ready.

---

## 6. Alembic: main linear + branches per módulo

### 6.1 Estructura Fase A (mixta)

```
backend/alembic/
├── alembic.ini
├── env.py                                 # lee version_locations dinámicamente
└── versions/                              # MAIN LINEAR — histórico + módulos legacy
    ├── 0001_initial.py
    ├── 0002_soft_delete.py
    ├── ... (28 migraciones existentes)
    └── t0u1v2w3x4y5_add_scope_arch_to_treatments.py

backend/app/modules/quotes/migrations/       # módulo NUEVO con branch propio
└── versions/
    └── qu_0001_initial.py                    # down_revision=None, branch_labels=('quotes',)

backend/app/modules/billing/migrations/       # módulo REFACTORIZADO — branch desde Fase A en adelante
└── versions/
    └── bi_0010_new_invoice_fields.py         # branch_labels=('billing',), depends_on=('<last_main_linear_rev>',)
```

**Reglas Fase A**:
- Migraciones existentes en `backend/alembic/versions/` se mantienen tal cual — no se mueven.
- Un módulo refactorizado (ej. `billing`) tiene sus migraciones históricas en main linear **y** crea un branch propio cuyo primer commit tiene `depends_on` al último commit linear que toca sus tablas. De ahí en adelante, nuevas migraciones del módulo van al branch.
- Un módulo completamente nuevo (ej. `quotes`) nace con branch propio desde la primera migración.
- `clinical` (legacy) nunca crea branch en Fase A — todas sus migraciones siguen siendo linear.

### 6.2 `env.py` dinámico

El `env.py` de Alembic construye `version_locations` iterando los módulos instalados con branch propio (leídos desde `core_module`). Main linear siempre incluido:

```python
# pseudocódigo
branch_paths = module_registry.get_alembic_paths_for_installed_modules_with_branch()
context.configure(
    ...,
    version_locations=[CORE_MAIN_LINEAR_PATH, *branch_paths],
)
```

Módulos con `legacy=True` no aportan path — su schema está en main linear, ya incluida.

### 6.3 Branch labels y depends_on

- Cada módulo con branch declara `branch_labels=('<module_name>',)` en su primera revision de branch.
- Migraciones nuevas que referencian tablas de otros módulos usan `depends_on=('<other_module>@head',)`. Si referencian tablas legacy (clinical, schema core histórico), no hace falta `depends_on` — siempre presentes.
- Test CI: para cada módulo con branch, parsear migraciones y comprobar que `depends_on` solo referencia módulos en `manifest.depends` o tablas legacy.

### 6.4 Uninstall clean (solo módulos con branch)

- Al registrar un módulo con branch por primera vez, guardar `core_module.base_revision` = revision linear previa al primer commit de su branch.
- Al desinstalar, `alembic downgrade <module_branch>@base` → ejecuta downgrades hasta la base. El schema histórico legacy del módulo (migraciones en main linear anteriores a la creación del branch) permanece.
- Módulos con `legacy=True`: uninstall con downgrade bloqueado. En Fase A son `removable: False`, irrelevante.
- Tests comparan schema dumps pre-install vs post-uninstall **para módulos con branch limpio** (nacidos nuevos): deben ser idénticos. Para módulos legacy-refactorizados, solo se valida que las migraciones del branch se revierten correctamente.

### 6.5 Fase B — refactor total

Cuando se aborde la Fase B:
- Partir clinical → core Patient mínimo + `patients_clinical` + `agenda`, cada uno con branch limpio.
- Extraer migraciones históricas de catalog/billing/notifications/etc. de main linear a sus branches respectivos (reescribiendo chain de revisions).
- Eliminar flag `legacy` de `core_module`.
- Tests de round-trip completo activos para todos los módulos.

---

## 7. External IDs y seed data

### 7.1 Tabla `core_external_id`

Cada registro seed o dato maestro creado por un módulo se referencia con un identificador estable.

```sql
CREATE TABLE core_external_id (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_name  VARCHAR NOT NULL,
    xml_id       VARCHAR NOT NULL,           -- ej: "billing.default_tax_21"
    table_name   VARCHAR NOT NULL,           -- ej: "billing_tax"
    record_id    UUID NOT NULL,              -- FK lógica al registro real
    noupdate     BOOLEAN NOT NULL DEFAULT false,  -- si true, upgrade no pisa
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (module_name, xml_id)
);
CREATE INDEX idx_external_id_module ON core_external_id (module_name);
CREATE INDEX idx_external_id_table ON core_external_id (table_name, record_id);
```

### 7.2 Formato de archivo seed

YAML declarativo en `data/*.yaml`:

```yaml
# dentalpin_billing/data/default_tax_rates.yaml
- xml_id: billing.tax_iva_21
  table: billing_tax
  noupdate: false
  values:
    name: "IVA 21%"
    rate: 21.00
    country: "ES"

- xml_id: billing.tax_iva_10
  table: billing_tax
  noupdate: false
  values:
    name: "IVA 10%"
    rate: 10.00
    country: "ES"
```

### 7.3 Comportamiento

- **Install**: cargar archivos, crear registros, registrar en `core_external_id`.
- **Upgrade**: re-cargar archivos. Para cada xml_id existente: si `noupdate=false`, actualizar campos; si `true`, respetar cambios del usuario.
- **Uninstall**: iterar `core_external_id WHERE module_name=<name>`, borrar registros en orden inverso de FKs.
- **Idempotencia**: si xml_id ya existe, la operación es update, no insert. `install()` puede ejecutarse dos veces sin romper nada.

### 7.4 Referencias cross-module

Un xml_id puede referenciar otro: `parent_category: billing.category_services`. El loader resuelve tras cargar todos los archivos del módulo.

---

## 8. Frontend: Nuxt Layers + slots + backend-driven nav

### 8.1 Nuxt Layer por módulo

Cada módulo lleva una carpeta `frontend/` estructurada como Nuxt Layer autónomo:

```
dentalpin_billing/frontend/
├── nuxt.config.ts                         # config del layer
├── pages/
│   ├── billing/
│   │   ├── index.vue                      # /billing
│   │   └── invoices/
│   │       └── [id].vue                   # /billing/invoices/:id
├── components/
│   ├── InvoiceCard.vue
│   └── PatientInvoicesSidebar.vue
├── composables/
│   └── useInvoices.ts
├── i18n/
│   ├── es.json
│   └── en.json
└── slots.ts                               # registerSlot() calls
```

Cuando el layer se añade a `extends` del `nuxt.config.ts` del frontend principal, Nuxt auto-descubre pages (merge con file-based routing), components (auto-import), composables (auto-import), i18n files.

### 8.2 Orquestación del layer por la CLI

Flujo `dentalpin modules install <name>`:

1. Resolver el path de la carpeta `frontend/` dentro del paquete Python instalado (`importlib.resources`).
2. Editar `frontend/nuxt.config.ts` del contenedor frontend: añadir el path al array `extends`. Persistir en un archivo auxiliar `frontend/modules.json` que el `nuxt.config.ts` lee al iniciar.
3. Trigger rebuild del contenedor frontend: `docker-compose build frontend && docker-compose up -d frontend`. Duración estimada 30-60s.
4. Durante el rebuild, UI muestra "Aplicando cambios..."; el backend sigue operativo.

Al desinstalar: quitar del array `extends`, rebuild.

### 8.3 Sistema de slots (extension points)

Permite a un módulo inyectar UI dentro de páginas de otros módulos sin tocar su código.

**Core declara slots** en sus páginas:

```vue
<!-- backend/modules/patients_clinical/frontend/pages/patients/[id].vue -->
<template>
  <div class="patient-detail">
    <PatientHeader :patient="patient" />
    <ModuleSlot name="patient.detail.tabs" :ctx="{ patient }" />
    <ModuleSlot name="patient.detail.sidebar" :ctx="{ patient }" />
  </div>
</template>
```

**Módulos registran componentes** al slot:

```ts
// dentalpin_billing/frontend/slots.ts
import { registerSlot } from '~/composables/useSlots'

registerSlot('patient.detail.sidebar', {
  component: defineAsyncComponent(() => import('./components/PatientInvoicesSidebar.vue')),
  order: 20,
  condition: (ctx) => ctx.patient.status === 'active',
  permission: 'billing.invoices.read',
})
```

`<ModuleSlot>` renderiza todos los componentes registrados para ese nombre, en orden, filtrados por permission y condition.

**Naming convention**: `<entity>.<view>.<location>`. Ejemplos:
- `patient.detail.sidebar`
- `patient.detail.tabs`
- `appointment.detail.actions`
- `dashboard.widgets`
- `settings.sections`

El contrato de nombres se documenta como parte de la Core API — módulos dependen de estos nombres.

### 8.4 Backend-driven navigation

`GET /api/modules/active` responde:

```json
{
  "modules": [
    {
      "name": "billing",
      "version": "1.0.0",
      "category": "official",
      "navigation": [
        {
          "label": "nav.billing",
          "to": "/billing/invoices",
          "icon": "i-lucide-receipt",
          "permission": "billing.invoices.read",
          "order": 40
        }
      ]
    }
  ]
}
```

Frontend al login:
1. Llama `/me` (permisos).
2. Llama `/api/modules/active`.
3. Construye menú lateral fusionando navigation items de todos los módulos activos, ordenados por `order`, filtrados por `can(item.permission)`.
4. Localiza labels vía i18n (`t(item.label)`).

### 8.5 SaaS multi-tenant

Para un futuro SaaS operado por el core team o un partner:

- El provider decide el set de módulos incluidos en el bundle del SaaS. Todos se compilan en el frontend.
- Cada tenant tiene en `core_module_tenant_activation` (tabla añadida solo en modo SaaS) una fila por (tenant_id, module_name, enabled).
- `GET /api/modules/active` filtra por tenant → devuelve solo los activos para ese tenant.
- Navegación, slots y permisos se filtran en consecuencia.
- Activar/desactivar = toggle en DB, sin reinicio, sin rebuild.

Community modules fuera del set aprobado del SaaS = no disponibles en ese SaaS. Patrón Shopify. Self-hosters conservan flexibilidad total.

---

## 9. Core API: contrato público

Documento aparte describirá la Core API completa. Elementos principales:

- `BaseModule` (clase abstracta).
- `ModuleContext` (pasado a `lifecycle.install/uninstall`): `db`, `clinic_id` (si aplica), `logger`, `external_id_helper`.
- `event_bus`: `publish`, `subscribe`.
- `register_permission`, `require_permission`.
- `<ModuleSlot>`, `registerSlot` (frontend).
- Modelos core accesibles: `User`, `Clinic`, `ClinicMembership`, `Patient` (mínimo).
- Eventos core publicados: `patient.created`, `patient.updated`, `clinic.member.added`, etc. Catálogo estable.

**Política de cambios**: cambios incompatibles en Core API se anuncian con deprecation warning durante al menos un ciclo de release antes de romper. Se documenta en `CHANGELOG.md` de core. Sin SemVer formal en v1 (no hay consumidores externos todavía), pero disciplina de deprecation desde el primer día.

---

## 10. CLI

Entrada: `python -m app.cli modules <command> [args]`.

| Comando | Acción |
|---------|--------|
| `list` | Lista todos los módulos con estado, versión, categoría. |
| `info <name>` | Detalle completo del módulo (manifest, dependencias, estado, últimas operaciones). |
| `install <name> [--force]` | Marca `to_install`, resuelve dependencias. `--force` ignora warnings. |
| `uninstall <name> [--force]` | Marca `to_remove`. `--force` requerido para `removable: False`. |
| `upgrade <name> [--version X]` | Marca `to_upgrade`. |
| `activate <name>` | Activa un módulo `disabled` (sin tocar DB). |
| `deactivate <name>` | Desactiva (mantiene DB, quita runtime). No requiere reinicio. |
| `restart` | Fuerza reinicio controlado del proceso. |
| `status` | Muestra pendientes (`to_*`), errores, operaciones en curso. |
| `doctor` | Diagnóstico: manifiestos inválidos, módulos huérfanos, dependencias rotas, migraciones inconsistentes. |
| `orphan <name>` | Marca un módulo desaparecido del disk como `uninstalled` (recuperación manual). |

Todos los comandos son thin wrappers sobre `ModuleService`.

---

## 11. Tests imprescindibles

No son opcionales. Son la diferencia entre "funciona" y "funciona en producción".

### Backend

1. **Round-trip schema**: `install(A) → uninstall(A)` → schema DB idéntico al estado inicial (diff de `pg_dump --schema-only`).
2. **Dependencia reverse**: `install(A) → install(B depends A) → uninstall(A)` debe fallar con mensaje claro.
3. **Crash mid-install**: matar proceso durante step="migrate" → reiniciar → operación retomada o estado consistente.
4. **Upgrade preserva datos**: `install(v1)` + crear datos usuario + `upgrade(v2)` → datos intactos.
5. **Seed idempotente**: `install(A)` dos veces seguidas → sin errores, sin duplicados.
6. **External IDs limpios**: `install + uninstall` → `core_external_id WHERE module_name=A` está vacío.
7. **FK cross-module válida**: parsear migraciones, validar que FKs a otros módulos están declaradas en `manifest.depends`.
8. **Core sin módulos**: suite completa del core pasa con cero módulos instalados. Guardián contra erosión de capas.
9. **Topological sort**: ciclos detectados en discover, no en install.
10. **Event bus sin módulo**: `patient.created` emitido cuando `billing` no está instalado → sin error, sin warning.
11. **Discover fail-loud**: módulo en DB como `installed` pero no en disk → bootstrap falla con mensaje explícito.

### Frontend

12. **Nav dinámico**: instalar módulo → `/api/modules/active` incluye sus nav items → menú los muestra.
13. **Slots**: componente registrado a slot aparece en página host. Componente con `condition` falso no aparece.
14. **Permisos en nav**: item con `permission: "X"` no visible para usuario sin ese permiso.

### End-to-end

15. **Install community module simulado**: crear paquete de prueba `dentalpin-foo` en fixture, `pip install -e`, `cli modules install foo`, reinicio, verificar router montado, migración aplicada, nav item presente.

---

## 12. Etapas de desarrollo

**Fase A** (este plan): toda la infraestructura modular + refactor de módulos existentes al contrato nuevo **excepto clinical**.

**Fase B** (diferida, sin fecha): split de clinical.

Cada etapa de Fase A es independientemente shippeable y deja el sistema estable.

### Etapa 0 — Preparación (1 día)
- Documentar plan técnico detallado (sucesor de este documento).
- Crear branch `feat/module-system-v1`.
- Inventario: qué módulos existentes se refactoran al contrato nuevo (catalog, budget, billing, notifications, treatment_plan). Qué queda como legacy (clinical).

### Etapa 1 — Core: estados, registry, CLI (3-5 días)
- Tabla `core_module` (con flag `legacy`) + `core_module_operation_log`.
- Refactor `BaseModule`: añadir lifecycle hooks (`install`, `uninstall`, `post_upgrade`), `manifest` como dict declarativo.
- `ModuleRegistry` con estados, topo-sort, resolver de dependencias, reconciliación con DB al arranque.
- Discover vía entry points + fallback filesystem.
- CLI `python -m app.cli modules {list, info, status, doctor}`.
- Registrar clinical en `core_module` con `legacy=true`, `removable=false`, `auto_install=true`. Resto de módulos existentes registrarse como no-legacy para preparar etapa 4.
- Tests: discover, topo-sort, estados básicos.

**No toca módulos existentes todavía**. Sistema coexiste con el flow actual.

### Etapa 2 — Alembic mixto linear + branches (1-2 días)
- Configurar `env.py` con `version_locations` dinámico (main linear + branches activos).
- **Main linear se mantiene intacta** (28 migraciones existentes, incluyendo clinical).
- Definir convención para nuevas migraciones de módulos refactorizados (catalog/billing/etc.): primer commit de su branch con `depends_on` al último rev linear que toca sus tablas.
- Módulos completamente nuevos (quotes, odontogram expansion) nacen con branch propio directo.
- Tests: downgrade/upgrade funciona en branch; main linear sigue funcional; crear migración nueva en branch y validar que se aplica tras un linear head.

Nota: ahorro vs plan original ~1-2 días porque no se reorganizan 28 migraciones históricas.

### Etapa 3 — Install/uninstall/upgrade lifecycle (4-6 días)
- Flujos de `to_install`, `to_remove`, `to_upgrade` en `lifespan`.
- External IDs: tabla + loader YAML + ejecución en install/upgrade/uninstall.
- Backup automático de tablas del módulo antes de uninstall (solo módulos con branch).
- Uninstall bloqueado para módulos `legacy=true`.
- CLI `install`, `uninstall`, `upgrade`, `restart`.
- Endpoint API para triggerear desde frontend.
- Tests: round-trip schema (módulos nuevos), crash mid-install, idempotencia, backup+restore, bloqueo de uninstall legacy.

### Etapa 4 — Refactor módulos existentes no-clinical al contrato nuevo (3-5 días)
Módulos que ya existen pero adoptan el contrato nuevo (`catalog`, `budget`, `billing`, `notifications`, `treatment_plan`):
- Añadir `manifest.py` a cada uno con metadata completa.
- Añadir `lifecycle.py` con install/uninstall/post_upgrade (aunque sean no-ops iniciales).
- Crear branch Alembic propio: primer commit con `depends_on` al último rev linear que tocaba sus tablas. Migraciones nuevas van al branch desde aquí.
- Declarar entry points en `backend/pyproject.toml`.
- Mover sus componentes frontend a una carpeta `frontend/` dentro del módulo (preparación para Nuxt layers).
- Marcar como `legacy=false` en `core_module` (ya son parte plena del sistema nuevo).
- `clinical` se queda tal cual — `legacy=true`, no se toca.

Nota: ahorro vs plan original ~2-4 días porque no se toca clinical (split Patient, mover Appointment, etc.).

### Etapa 5 — Frontend: nav dinámico + slots (4-5 días)
- Endpoint `GET /api/modules/active` con navigation + metadata (incluye clinical con su nav declarado en su manifest).
- `useModules` lee de backend en lugar de registry estático.
- Sistema `<ModuleSlot>` + `registerSlot` + `useSlots` composable.
- Mover nav items actuales del `moduleRegistry.ts` estático al manifest de cada módulo (incluido clinical).
- Definir slots core iniciales. Añadir `<ModuleSlot>` a páginas clinical (patient detail tabs/sidebar, appointment actions, dashboard widgets, settings sections). **Solo edits puntuales en páginas clinical**, no refactor.
- Tests frontend de nav y slots.

### Etapa 6 — Nuxt Layers + CLI orchestration (3-4 días)
- Estructura `frontend/` como Nuxt layer para módulos refactorizados en Etapa 4 (catalog/billing/etc.).
- **Clinical NO se convierte en layer**: sus componentes y páginas siguen en `frontend/app/components/clinical/` y `frontend/app/pages/` tal cual.
- Configurar `nuxt.config.ts` para leer `extends` desde `modules.json` generado por backend. El frontend principal sigue siendo el host; clinical vive en el host; el resto de módulos son layers.
- CLI: al `install/uninstall`, patchear `modules.json` y triggerear rebuild frontend.
- Documentación para community contributors: cómo estructurar un módulo externo.

### Etapa 7 — Hardening y documentación (3-4 días)
- Test end-to-end con módulo community simulado.
- Documentar Core API pública con ejemplos.
- Guía "tu primer módulo DentalPin" en `docs/creating-modules.md` (refactor del actual).
- CI: test del sistema modular con y sin módulos no-legacy instalados. Clinical siempre instalado (es legacy, no removible).
- CI: validador de manifiestos + FKs cross-module.

**Total Fase A**: 15-22 días de trabajo enfocado. Ahorro ~10-13 días vs plan original, conservando toda la infraestructura modular.

### Fase B diferida — split de clinical (sin fecha, 10-14 días estimados)

Se aborda cuando aparezca motivo concreto. No bloquea nada en Fase A.

- Etapa B.1: crear Patient mínimo en core; migración de datos desde clinical.patients.
- Etapa B.2: crear módulo `patients_clinical` con medical_history, emergency_contact, legal_guardian; migrar datos.
- Etapa B.3: crear módulo `agenda` con Appointment, AppointmentTreatment, PatientTimeline, endpoint professionals; migrar datos + rutas API + permisos.
- Etapa B.4: mover componentes frontend de clinical a sus módulos respectivos, convertirlos en Nuxt layers.
- Etapa B.5: eliminar flag `legacy` del registro clinical (o retirar clinical). Extraer sus migraciones históricas de main linear a branches dedicadas (reescribir chains).
- Etapa B.6: retirar `<ModuleSlot>` específicos que ya no tengan sentido; consolidar.

**Condición para iniciar Fase B**: cliente laboratorio dental real, auditoría GDPR que exija separación, o refactor forzado por billing v2. Hasta entonces, la deuda técnica de tener clinical como módulo "gordo" es aceptable.

---

## 13. Implicaciones y riesgos

### 13.1 Impacto en código existente (Fase A)

- **Modelos y migraciones**: main linear se mantiene intacta. Módulos no-clinical que se refactoran (catalog/billing/etc.) crean su branch Alembic con `depends_on` al último rev linear que les corresponde; migraciones históricas permanecen en main linear. Clinical no se toca.
- **Rutas API**: prefijos actuales se mantienen. `/api/v1/clinical/patients`, `/api/v1/clinical/appointments`, etc. siguen funcionando igual. Los módulos refactorizados (catalog, billing, etc.) mantienen sus prefijos actuales — no se cambian para evitar tocar frontend y tests. Nuevos módulos nacen con su prefijo limpio.
- **Permisos**: namespacing actual se mantiene. `clinical.*` permanece. Módulos refactorizados conservan sus permisos actuales. Solo módulos nuevos añaden namespaces nuevos.
- **Frontend**: componentes de clinical permanecen en `frontend/app/components/clinical/` y pages en `frontend/app/pages/`. Solo se añaden `<ModuleSlot>` como extension points (edits puntuales). Módulos refactorizados mueven su frontend a carpeta propia dentro del módulo backend para convertirse en Nuxt layer.
- **i18n frontend**: keys actuales se mantienen. Módulos nuevos declaran las suyas en sus layers.

**Consecuencia**: Fase A = impacto muy acotado en código de usuario final. Flujos actuales (citas, pacientes, odontograma) siguen intactos. Riesgo de regresiones mínimo.

### 13.1b Impacto diferido en Fase B

Cuando se aborde Fase B:
- API rutas cambian: `/api/v1/clinical/patients` → `/api/v1/patients/*` (core) + `/api/v1/patients_clinical/*` + `/api/v1/agenda/*`.
- Permisos re-namespaced: `clinical.patients.read` → `patients.read` + `patients_clinical.medical.read` + `agenda.appointments.read`.
- Frontend components + pages se mueven a sus layers respectivos.
- Tests se reorganizan por módulo.
- Migraciones históricas se extraen de main linear a branches.

Todo esto es costoso (10-14 días) pero mecánico cuando la infraestructura de Fase A esté asentada.

### 13.2 Riesgos técnicos

| Riesgo | Mitigación |
|--------|------------|
| Alembic multi-branch más complejo de debuggear | Tests extensivos, CLI `doctor`, logs verbosos. |
| `sys.exit()` dentro de request HTTP puede no reiniciar limpio bajo todos los workers | Usar signal + flag de shutdown, no exit inmediato. Test en staging Docker. |
| Carga dinámica de paquetes instalados post-boot no funciona hasta reinicio | Explícito en UX. "Reinicio requerido" banner. |
| FK cross-module no declarada rompe uninstall | Test CI que valida. Falla rápido. |
| `nuxt.config.ts` concurrente escrito por varias CLIs en paralelo | Lock de filesystem al modificar. |
| Rebuild frontend puede fallar y dejar UI rota | Mantener bundle anterior; rollback automático si rebuild falla. |
| Módulos community con código malicioso | No cubierto v1. Documentado como riesgo del self-hoster. Badge "Comunidad" avisa. Firma y revisión = v2+. |

### 13.3 Costes operacionales

- Reinicio backend 3-5s → pérdida de WebSocket connections activas (si las hay). Aceptable para operación de instalar módulo.
- Rebuild frontend 30-60s → la UI no está disponible ese tiempo si es el único contenedor. Mitigable con blue-green deploy en setups avanzados (v2).

### 13.4 Implicaciones de governance

- **PRs de módulos comunitarios no se aceptan en el repo principal**. Cada community contributor mantiene su propio repo + publica en PyPI. Se mantiene un registro mínimo (v1 = sección en docs) con enlaces a módulos conocidos.
- **Módulos oficiales viven en el monorepo DentalPin** y son mantenidos por el core team.
- El core team marca un módulo como "official" solo si lo va a mantener. El ecosistema comunitario es responsable de sus propios módulos.

---

## 14. Fuera de alcance v1 (explícito)

Para evitar scope creep y mantener foco.

- **Tool Registry / LLM manifest fields**: fuera.
- **Marketplace, firma, trust tiers más allá de `category`**: fuera.
- **Permisos declarativos con enforcement real**: fuera. Solo `get_permissions()` en código + badges en manifest.
- **Module federation frontend**: fuera. Opción A + layers cubre 95%.
- **SaaS multi-tenant con módulos por cliente sin rebuild**: fuera. Patrón pre-bundle + toggle por tenant descrito, implementación cuando haya cliente SaaS real.
- **Hot-install sin reinicio**: fuera. Reevaluable v2 con tests muy sólidos.
- **Versionado SemVer formal de Core API**: se documenta CHANGELOG + deprecation discipline, sin release cycle formal.
- **CLI como `dentalpin-admin` console script global**: fuera, `python -m app.cli` suficiente.
- **Workspace monorepo con `uv`**: fuera, un `pyproject.toml` único con entry points.
- **i18n del sistema de módulos**: mensajes de error en inglés/español ya soportados; no se amplía.
- **Backup incremental o diferencial**: uninstall hace dump completo por simplicidad.

---

## 15. Preguntas abiertas para plan técnico

Para resolver al redactar el plan técnico detallado tras aprobar este documento:

1. **Profesionales**: actualmente `professional_id` en `Appointment` apunta a `users.id`. Con `agenda` como módulo y `User` en core, ¿el módulo `agenda` se queda con `Professional` como entidad propia o sigue siendo lookup a `User` con role? (Recomendación inicial: mantener lookup a User con role dentist/hygienist; `agenda` no necesita tabla propia de Professional.)
2. **Endpoint `/api/modules/restart`**: mecánica exacta de shutdown controlado. `os.kill(os.getpid(), SIGTERM)` dentro de request vs worker lifecycle de uvicorn con gunicorn manager. Probar en staging.
3. **Estructura del `nuxt.config.ts` patchable**: cómo mantener `extends` limpio tras instalaciones/desinstalaciones múltiples. `modules.json` auxiliar es opción; alternativas.
4. **Política de versiones de módulos oficiales**: ¿todos los módulos oficiales comparten versión con el core o cada uno tiene la suya? (Recomendación: cada uno la suya, para poder evolucionarlos independiente.)
5. **Qué hacer si un módulo en `auto_install: True` falla al instalar en bootstrap inicial de una DB vacía**: abortar todo, o continuar con los que pueden instalarse.
6. **Internationalization de manifiestos**: `summary` y `description` del manifest ¿soportan i18n desde v1 o texto fijo?
7. **Validación de `external_dependencies.python`**: comprobar en discover con `importlib.metadata`, o solo advertir y dejar que Python falle naturalmente.
8. **`core_module_tenant_activation` (SaaS)**: dejar la tabla prevista en la migración de `core_module` o crearla solo cuando se habilite modo SaaS.

---

## 16. Resumen ejecutivo

**Qué se construye (Fase A)**: plataforma modular tipo Odoo moderna, con módulos oficiales y comunitarios bajo el mismo contrato, distribuidos como paquetes Python con entry points, instalables con reinicio explícito, con Alembic mixto (main linear para histórico + branches por módulo nuevo) para uninstall limpio de módulos con branch, UI extensible vía Nuxt Layers + sistema de slots, nav backend-driven, y CLI como cliente primario. **Clinical se mantiene como módulo legacy** registrado en el sistema nuevo pero sin mover su código ni sus migraciones.

**Qué NO se construye en Fase A**: split de clinical en core (Patient mínimo) + `patients_clinical` + `agenda`. Se difiere a Fase B sin fecha.

**Por qué así**:
- Core y módulos bajo mismo contrato → el core team es primer consumidor de su Core API → ecosistema sano.
- Reinicio explícito v1 → elimina el 80% de bugs de hot-install → simple, robusto, defendible.
- Entry points desde día 1 → evita refactor costoso futuro del discovery.
- Alembic mixto (main linear + branches) → aprovecha ventana sin prod para módulos nuevos, sin coste de reorganizar 28 migraciones históricas.
- Nuxt Layers → community ships módulo completo (backend + UI) sin PR al core.
- Slots UI → modularidad real intra-página, funciona sobre clinical sin moverlo.
- Dejar clinical intacto → ahorra 10-14 días, riesgo regresiones ~cero, split futuro mecánico no rediseño.
- Slim manifest v1 → sin Tool Registry, sin permisos declarativos, sin marketplace, sin firma. Foco en lo que crea valor inmediato.

**Resultado esperado tras Fase A**:
- Cualquier desarrollador externo puede crear `dentalpin-mi-modulo`, publicarlo en PyPI, y una clínica self-hosted lo instala con un comando.
- Nuevos módulos oficiales (quotes, billing v2, odontogram expansion) nacen bien estructurados desde día 1.
- Módulos existentes refactorizados (catalog/billing/notifications/treatment_plan/budget) conviven con el contrato nuevo.
- Ningún módulo no-legacy corrompe el core al desinstalarse. Backup automático. DB vuelve al estado anterior.
- Flujos actuales (citas, pacientes, odontograma) siguen funcionando igual — riesgo de regresión mínimo.
- Sistema sostenible a 5 años sin rediseños mayores.

**Tiempo estimado Fase A**: 15-22 días de trabajo enfocado, shippeable por etapas independientes.

**Tiempo estimado Fase B** (diferida): 10-14 días cuando se aborde.

**Próximo paso**: validar este documento (tú + verificación ChatGPT), abordar las 8 preguntas abiertas, y redactar plan técnico detallado con código, schemas y tests para Fase A.
