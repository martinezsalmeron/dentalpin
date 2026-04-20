"""Clinical module database models.

Post Fase B.3 the clinical package no longer owns any domain model.
Patient lives in ``app.modules.patients.models``; Appointment +
AppointmentTreatment in ``app.modules.agenda.models``; PatientTimeline
in ``app.modules.patient_timeline.models``.

Re-exports keep legacy imports resolving during the B.* transition.
"""

# Re-export models for legacy imports.
from app.modules.agenda.models import Appointment, AppointmentTreatment  # noqa: F401
from app.modules.patient_timeline.models import PatientTimeline  # noqa: F401
from app.modules.patients.models import Patient  # noqa: F401
