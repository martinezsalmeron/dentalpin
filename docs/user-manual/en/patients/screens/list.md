---
module: patients
screen: list
route: /patients
related_endpoints:
  - GET /api/v1/patients
  - GET /api/v1/patients/recent
  - POST /api/v1/patients
related_permissions:
  - patients.read
  - patients.write
related_paths:
  - backend/app/modules/patients/router.py
  - backend/app/modules/patients/frontend/pages/patients/index.vue
last_verified_commit: 0e9a0ac
screenshots:
  - patients.png
---

# Patient list

Lists every active patient in the clinic. From here you can search,
filter, open a patient's detail page, or create a new patient.

## At a glance

- **Default view:** active patients only. Archived patients are hidden;
  the list endpoint never returns them by default.
- **Recent panel:** the sidebar quick-access list shows the patients you
  opened most recently — backed by the `GET /api/v1/patients/recent`
  endpoint.
- **Pagination:** 20 patients per page. Use the page-size selector to
  raise it; the backend caps at 100.

## How to find a patient

1. Type a name, surname, or ID number into the search box at the top
   of the list. The query filters by exact and partial matches across
   identity fields.
2. Press **Enter** or wait for debounce — results refresh in place.
3. Click any row to open the
   [patient detail](./detail.md) screen.

## How to create a patient

> Requires the `patients.write` permission.

1. Click **New patient** in the top-right toolbar.
2. Fill in the required identity fields (name, surname, date of birth).
   Contact details and demographics can be added now or later from the
   patient detail page.
3. Click **Save**. The new patient appears at the top of the list and
   the system publishes a `patient.created` event so other modules
   (recalls, notifications, …) can react.

## Permissions

| You see / can do | Permission |
|------------------|-----------|
| Browse and search the list | `patients.read` |
| Open the **New patient** button | `patients.write` |

## Troubleshooting

- **The list is empty after a fresh install.** Run `./scripts/seed-demo.sh`
  to load demo data.
- **A patient I just created is missing.** Check the active filter — if
  you accidentally toggled the *Show archived* switch, only archived
  rows appear.
