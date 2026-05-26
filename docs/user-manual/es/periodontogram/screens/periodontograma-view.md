---
module: periodontogram
screen: view
route: /patients/{id}?clinicalMode=diagnosis&diagnosisView=periodontogram
related_endpoints:
  - GET /api/v1/periodontogram/patients/{patient_id}/snapshots
  - GET /api/v1/periodontogram/patients/{patient_id}/timeline
  - GET /api/v1/periodontogram/patients/{patient_id}/draft
  - POST /api/v1/periodontogram/patients/{patient_id}/draft
  - GET /api/v1/periodontogram/snapshots/{snapshot_id}
  - GET /api/v1/periodontogram/snapshots/{snapshot_id}/indices
  - PATCH /api/v1/periodontogram/snapshots/{snapshot_id}/teeth/{tooth_number}
  - PATCH /api/v1/periodontogram/snapshots/{snapshot_id}/teeth/{tn}/sites/{site_code}
  - POST /api/v1/periodontogram/snapshots/{snapshot_id}/close
  - DELETE /api/v1/periodontogram/snapshots/{snapshot_id}
related_permissions:
  - periodontogram.read
  - periodontogram.write
related_paths:
  - backend/app/modules/periodontogram/frontend/components/PeriodontogramView.vue
  - backend/app/modules/periodontogram/frontend/components/PeriodontogramChart.vue
  - backend/app/modules/periodontogram/router.py
last_verified_commit: 411343e
---

# Vista del periodontograma

La sub-pestaña **Periodontograma** vive dentro de *Ficha → Clínica →
Diagnóstico*. Reúne el slider de histórico, el banner de índices y la
representación SEPA de las dos arcadas.

## De un vistazo

```
┌────────────────────────────────────────────────────────────────────┐
│ [Banner ámbar — solo si miras un snapshot pasado] ............... │
│                                                                    │
│ [Slider de fechas]──●──────●──●─────────[Hoy]                      │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ [Pill] Borrador / Cerrada · 23 mar 2026                        │ │
│ │ BoP 18%  ·  PI 12%  ·  CAL 1.8mm  ·  Bolsas ≥5mm: 3            │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ SUPERIOR                                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Tabla SEPA (9 filas × 16 dientes)                            │ │
│  │  Dientes — cara vestibular                                    │ │
│  │  Dientes — cara palatina (flip vertical)                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ INFERIOR                                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Dientes — cara lingual (flip vertical)                       │ │
│  │  Dientes — cara vestibular                                    │ │
│  │  Tabla SEPA                                                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ [Botonera sticky — solo borradores]                                │
│  [⏳ Guardado]      [Descartar borrador]  [Cerrar sesión ✓]       │
└────────────────────────────────────────────────────────────────────┘
```

## Estado vacío

Si el paciente no tiene ningún snapshot ni borrador, la sub-pestaña
muestra una tarjeta con el botón **Iniciar exploración**. Al pulsarlo
se crea un borrador prerelleno y se carga la vista completa.

## Captura por celda

1. **Sitio (sondaje, margen, sangrado, placa, supuración).** Pulsa
   cualquier dot del diente o cualquier sub-celda de las filas
   *Sangrado / Placa / Margen gingival / Sondaje*. Se abre un modal
   con cinco campos.
2. **Diente (movilidad, pronóstico, furca, anchura encía).** Pulsa
   sobre la fila correspondiente del diente. Se abre un modal con
   los campos por diente. Furca solo aparece en molares.

Los cambios se autoguardan con un retardo de 600 ms (debounce). El
indicador inferior izquierdo del periodontograma muestra el estado:
*Guardando…* / *Cambios pendientes* / *Guardado*.

## Heatmap visual

El sondaje pinta cada dot según la profundidad:

| Sondaje | Color |
|---------|-------|
| 0–3 mm | Verde |
| 4 mm | Amarillo |
| 5–6 mm | Naranja |
| ≥ 7 mm | Rojo |

Sangrado y placa añaden indicadores pequeños sobre el dot
(rojo y azul respectivamente).

## Histórico

El slider superior es el mismo componente que usa el odontograma:
cada nodo es un snapshot cerrado. Al seleccionar una fecha pasada
aparece un banner ámbar y todos los inputs quedan deshabilitados.
*Volver al actual* descarga el snapshot más reciente o el borrador
activo si lo hay.

## Cerrar sesión

Desde la botonera inferior, *Cerrar sesión* abre un modal de
confirmación con un campo opcional para una nota clínica. Al
confirmar:

1. Se vuelcan al backend los cambios pendientes en cola.
2. Se calculan los índices SEPA y se persisten en el snapshot.
3. El snapshot pasa a `closed`, aparece en el slider y los inputs
   quedan deshabilitados.

## Descartar borrador

*Descartar borrador* elimina todos los datos del draft activo. No es
reversible — el modal lo advierte antes de confirmar.
