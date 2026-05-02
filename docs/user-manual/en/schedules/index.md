---
module: schedules
last_verified_commit: 0e9a0ac
---

# Schedules

The schedules module manages the operating hours of the clinic and of
each professional, plus the day-to-day overrides (holidays, sick days,
half-days). It also computes availability for the agenda and tracks
occupancy analytics.

This module ships **no top-level pages**: its UI lives inside the
**Settings → Workspace** section, contributed via the host's settings
registry. The module is also **removable** — you can uninstall it and
the agenda keeps working with a default 08:00–21:00 fallback.

## Where to find each screen

| Section | Path | What it does |
|---------|------|--------------|
| Clinic hours | *Settings → Workspace → Clinic hours* | Edit the weekly opening hours and create one-off overrides (closed Christmas Eve, half-day on a Friday, …). |
| Professional schedules | *Settings → Workspace → Professional schedules* | Edit each professional's working hours and time-off overrides. |

> Each screen is gated by a different permission — see the
> [permissions reference](../../../technical/schedules/permissions.md).

## Clinic hours

1. Go to **Settings → Workspace → Clinic hours**.
2. The **Weekly schedule** card shows one row per weekday. Toggle
   *Closed* or set the open / close times.
3. The **Overrides** card lists upcoming exceptions. Click **New
   override** to add one — pick the date(s), set hours or mark as
   closed, and save.

## Professional schedules

1. Go to **Settings → Workspace → Professional schedules**.
2. Pick a professional from the dropdown. If your role is gated to
   *own* hours only, the dropdown is fixed to you.
3. Edit weekly hours and overrides the same way as for the clinic.

## Permissions

| Action | Permission |
|--------|-----------|
| View clinic hours / overrides | `clinic_hours.read` |
| Edit clinic hours / overrides | `clinic_hours.write` |
| View any professional's schedule | `professional.read` |
| View only own schedule | `professional.own.read` |
| Edit any professional's schedule | `professional.write` |
| Edit only own schedule | `professional.own.write` |
| View occupancy analytics | `analytics.read` |

## What happens if I uninstall this module?

- The agenda continues to work; availability falls back to a fixed
  08:00–21:00 window with no per-professional restrictions.
- Occupancy analytics disappear from the reports area.
- All schedules tables are dropped. Reinstalling does **not** restore
  the data — back up before uninstalling in production.

## Related modules

- **Agenda** — uses schedules' availability resolver to draw the
  bookable grid. Falls back to defaults when schedules is uninstalled.
- **Reports** — surfaces occupancy analytics produced by this module.
