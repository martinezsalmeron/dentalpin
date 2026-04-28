// Treatment-plan slot registrations.
//
// Clinical-notes-related slots (patient.timeline.treatments,
// patient.summary.feed, odontogram.diagnosis.sidebar,
// odontogram.condition.actions) are owned by the ``clinical_notes``
// module since issue #60. Nothing to register here today; the file is
// kept so the plugin auto-discovery has a stable entry point for
// future treatment_plan-only slots.

export default defineNuxtPlugin(() => {})
