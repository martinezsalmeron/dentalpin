---
module: schedules
last_verified_commit: 0e9a0ac
---

# Agenda y horarios

El módulo de horarios gestiona el horario de funcionamiento de la
clínica y de cada profesional, junto con las excepciones del día a día
(festivos, bajas, jornadas reducidas). También calcula la
disponibilidad para la agenda y registra analíticas de ocupación.

Este módulo **no aporta páginas propias**: su interfaz vive dentro de
**Ajustes → Espacio de trabajo**, registrada a través del registro de
ajustes del host. Además, es un módulo **opcional y desinstalable** —
si lo retiras, la agenda sigue funcionando con un horario por defecto
de 08:00 a 21:00.

## Dónde encontrar cada pantalla

| Sección | Ruta | Para qué sirve |
|---------|------|----------------|
| Horario de la clínica | *Ajustes → Espacio de trabajo → Horario de la clínica* | Editar el horario semanal de apertura y crear excepciones puntuales (cerrado en Nochebuena, mañana solo el viernes, …). |
| Horarios de profesionales | *Ajustes → Espacio de trabajo → Horarios de profesionales* | Editar el horario semanal y las excepciones de cada profesional. |

> Cada pantalla está protegida por un permiso distinto — consulta la
> [referencia de permisos](../../../technical/schedules/permissions.md).

## Horario de la clínica

1. Ve a **Ajustes → Espacio de trabajo → Horario de la clínica**.
2. La tarjeta **Horario semanal** muestra una fila por día. Activa
   *Cerrado* o ajusta las horas de apertura y cierre.
3. La tarjeta **Excepciones** lista las próximas excepciones. Pulsa
   **Nueva excepción** para añadir una — elige fecha(s), define
   horario o marca como cerrado, y guarda.

## Horarios de profesionales

1. Ve a **Ajustes → Espacio de trabajo → Horarios de profesionales**.
2. Elige un profesional en el desplegable. Si tu rol solo permite ver
   tu *propio* horario, el desplegable queda fijado a ti.
3. Edita horarios semanales y excepciones igual que para la clínica.

## Permisos

| Acción | Permiso |
|--------|---------|
| Ver horario / excepciones de clínica | `clinic_hours.read` |
| Editar horario / excepciones de clínica | `clinic_hours.write` |
| Ver el horario de cualquier profesional | `professional.read` |
| Ver solo el horario propio | `professional.own.read` |
| Editar el horario de cualquier profesional | `professional.write` |
| Editar solo el horario propio | `professional.own.write` |
| Ver analíticas de ocupación | `analytics.read` |

## ¿Qué pasa si desinstalo este módulo?

- La agenda sigue funcionando; la disponibilidad cae a una franja fija
  de 08:00 a 21:00 sin restricciones por profesional.
- Las analíticas de ocupación desaparecen del área de informes.
- Todas las tablas de horarios se eliminan. Reinstalar **no**
  restaura los datos — haz backup antes de desinstalar en producción.

## Módulos relacionados

- **Agenda** — usa el resolver de disponibilidad de este módulo para
  pintar la cuadrícula de huecos reservables. Cae a valores por
  defecto si se desinstala.
- **Informes** — muestra las analíticas de ocupación producidas aquí.
