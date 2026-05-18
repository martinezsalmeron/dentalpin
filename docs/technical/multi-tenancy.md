# Multi-tenancy en DentalPin

Documento de arquitectura. Define el modelo de aislamiento actual (self-hosted) y las costuras que permitirán un módulo externo `dentalpin-saas` con DB-per-tenant sin tocar core.

**Estado**: diseño aprobado, Fase 1 pendiente de ejecución. Las fases 2–7 se ejecutarán cuando exista un segundo cliente real que justifique el SaaS.

**Documento padre**: [`docs/adr/0012-multi-tenancy-brief.md`](../adr/0012-multi-tenancy-brief.md) (brief de implementación por fases).

---

## 1. Modelo de aislamiento

DentalPin usa **dos capas de aislamiento** complementarias:

| Capa | Unidad | Aislamiento | Vive en |
|------|--------|-------------|---------|
| Físico (DB) | Tenant | Connection string distinto. En self-hosted hay uno (`"default"`); en SaaS habrá N | `TenantContext` |
| Lógico (fila) | Clinic | Filtro `WHERE clinic_id = ...` obligatorio en cada query | `ClinicContext` |

### Por qué dos capas

Un tenant puede contener **una o varias clínicas**. Modelo actual `Clinic` + `ClinicMembership` permite que un usuario pertenezca a N clínicas con roles distintos. Si tenant=clínica, se rompería ese caso de uso. Por eso:

- **Tenant** = unidad de aislamiento de DB. Concepto técnico/comercial (subscripción SaaS).
- **Clinic** = unidad clínica con datos clínicos propios. Concepto de negocio.

Aislamiento entre clínicas dentro del mismo tenant es por fila (shared-schema). Aislamiento entre tenants es por DB.

### Self-hosted vs SaaS

| Aspecto | Self-hosted | SaaS (futuro) |
|---------|-------------|---------------|
| Tenants | 1 (`"default"`) | N |
| DB por tenant | 1 compartida | 1 por tenant |
| Clínicas por tenant | 1+ | 1+ |
| `modules_enabled` | Todos los del registry | Subset según plan |
| Storage prefix | `""` | `"tenants/<slug>/"` |
| Resolver | `SingleTenantResolver` | `SaasTenantResolver` (módulo externo) |

El self-hoster configura `DATABASE_URL` y obtiene exactamente lo de hoy: un tenant lógico que contiene N clínicas filtradas por `clinic_id`.

---

## 2. Contratos de interfaz (post-Fase 1)

### `TenantContext`

Dataclass inmutable que describe un tenant. Se inyecta en endpoints, jobs y CLI cuando se necesita decidir a qué DB conectar.

```python
@dataclass(frozen=True, slots=True)
class TenantContext:
    slug: str                         # "default" en self-hosted
    db_url: str                       # postgresql+asyncpg://...
    storage_prefix: str               # "" en self-hosted
    modules_enabled: frozenset[str]   # subset visible para el tenant
    metadata: Mapping[str, Any]       # libre, para extensión SaaS
```

**Invariantes:**
- Inmutable (frozen). Cualquier "modificación" devuelve una copia (`with_metadata(**kwargs)`).
- `clinic_id` **NO** vive aquí — sigue en `ClinicContext`.
- `metadata` es `MappingProxyType` para garantizar inmutabilidad incluso del campo libre.
- Core trata `metadata` como `Mapping[str, Any]`. Módulos externos pueden definir su propio TypedDict y castar al leer.

### `TenantResolver`

Protocol async con dos métodos:

```python
@runtime_checkable
class TenantResolver(Protocol):
    async def resolve(self, request: Request) -> TenantContext: ...
    async def resolve_by_slug(self, slug: str) -> TenantContext: ...
```

- `resolve(request)` — hot path HTTP. Inspecciona el request (host, header, JWT, etc.) y devuelve el tenant.
- `resolve_by_slug(slug)` — contextos sin request: jobs background, CLI, tests.
- No lanza excepciones HTTP. Devuelve `LookupError` si no existe. Cada implementación (o capa middleware) decide cómo envolverlo.

### `SingleTenantResolver`

Implementación default para self-hosted. Lee de settings y del `ModuleRegistry` una sola vez al construirse y devuelve siempre el mismo `TenantContext`:

- `slug` = `settings.TENANT_SLUG` (default `"default"`, añadido en Fase 2a)
- `db_url` = `settings.DATABASE_URL`
- `storage_prefix` = `""`
- `modules_enabled` = `frozenset(registry.list_modules())` — todos los módulos cargados
- `metadata` = `MappingProxyType({})`

O(1), sin red, sin cache (precomputa). Ignora el `request`.

---

## 3. Eventos publicados (post-Fase 1+2)

El event bus existente (`backend/app/core/events/bus.py`) gana las siguientes constantes en `EventType`:

| Evento | Cuándo | Payload | Publicado en |
|--------|--------|---------|--------------|
| `tenant.resolved` | Tras `resolver.resolve()` con éxito | `{"tenant_slug": str}` | Fase 2a (no en Fase 1) |
| `app.startup` | Lifespan startup | `{}` | Fase 2a |
| `app.shutdown` | Lifespan shutdown | `{}` | Fase 2a |
| `module.installed` | Tras instalación de módulo desde admin UI | `{"module_name": str, "tenant_slug": str}` | Diferido (Fase 5 original, plegada) |
| `module.uninstalled` | Tras desinstalación | `{"module_name": str, "tenant_slug": str}` | Diferido |

En Fase 1 solo se **declara** `TENANT_RESOLVED` como constante; no se publica hasta que `get_db` use el resolver.

---

## 4. Punto de extensión SaaS

Un futuro módulo `dentalpin-saas` no toca core. Implementa:

1. **`SaasTenantResolver(TenantResolver)`**: resuelve por host/header/JWT, consulta su control plane (DB propia con tenants y planes), devuelve `TenantContext` con `db_url` y `modules_enabled` por suscripción.
2. **Hook en lifespan**: sustituye `app.state.tenant_resolver` por el suyo.
3. **(Fase 3) `S3CompatibleStorage`**: implementa la interfaz `StorageBackend` existente.
4. **(Fase 5) Subscriber a `tenant.resolved`**: opcional, para auditoría / billing.

Core nunca importa código del módulo SaaS. SaaS importa contratos de core.

---

## 5. Auditoría arquitectónica — qué se reutiliza, qué se añade

| Pieza | Estado pre-Fase 1 | Cambio Fase 1 |
|-------|-------------------|---------------|
| `Clinic` + `ClinicMembership` | Existe (`backend/app/core/auth/models.py`) | No se toca |
| `ClinicContext` + `get_clinic_context` | Existe (`backend/app/core/auth/dependencies.py`) | No se toca |
| Engine global + `get_db` | Existe (`backend/app/database.py`) | No se toca (cambia en Fase 2a) |
| Event bus | Existe (`backend/app/core/events/bus.py`, 184 EventTypes) | Solo añade constante `TENANT_RESOLVED` |
| Storage abstraction | Existe (`backend/app/modules/media/storage/`) | No se toca (extiende y mueve en Fase 3) |
| Module registry | Existe (`backend/app/core/plugins/registry.py`) | Se lee desde `SingleTenantResolver` |
| Alembic multi-branch | Existe (`backend/alembic/env.py`) | No se toca (cambia en Fase 4) |
| Settings | Plano (`backend/app/config.py`) | No se toca en Fase 1 (cambia en Fase 2a) |
| `TenantContext` | No existe | **Se crea** |
| `TenantResolver` Protocol | No existe | **Se crea** |
| `SingleTenantResolver` | No existe | **Se crea** |

Tras Fase 1 el árbol `backend/app/core/tenancy/` queda definido. Nadie lo llama todavía: Fase 2a engancha el resolver al lifespan y al `get_db`.

---

## 6. Reglas para código de core

Estas reglas entran en `CLAUDE.md` tras Fase 1 ejecutada.

- **Nunca importar una sesión DB global.** Usar siempre `Depends(get_db)` en endpoints o recibir `AsyncSession` como parámetro en services/jobs.
- **`clinic_id` sigue siendo obligatorio en queries.** Esto no cambia. `TenantContext` aísla DB; `ClinicContext` aísla filas.
- **No asumir un solo tenant.** Código que itere "todos los tenants" pertenece al módulo SaaS, no a core.
- **`modules_enabled` se lee del `TenantContext`**, no del `ModuleRegistry`, cuando se quiere saber qué módulos ve un tenant. El registry es la lista de módulos *cargados en la instancia*; el tenant es la lista de módulos *visibles para ese tenant*.
- **`TenantContext.metadata` es opaco para core.** Si un módulo necesita información estructurada, define su propio TypedDict y castea al leer.

---

## 7. Glosario

- **Tenant**: unidad de aislamiento de DB. En self-hosted hay uno (`"default"`); en SaaS hay N.
- **Clinic**: unidad clínica con su `clinic_id`. Un tenant puede contener una o varias.
- **Control plane**: DB del módulo SaaS que guarda la lista de tenants y sus planes. Vive en el módulo SaaS.
- **Data plane**: DBs de cada tenant con datos clínicos. Una por tenant en SaaS, una única en self-hosted.
- **Resolver**: componente que dado un request (o un slug) devuelve el `TenantContext` correspondiente.
- **`modules_enabled`**: subset de módulos visibles para un tenant. Self-hosted = todo el registry. SaaS = lo que dicte el plan.
- **Costura** (seam): punto de extensión vía interfaz que permite sustituir implementación sin tocar consumidores.
