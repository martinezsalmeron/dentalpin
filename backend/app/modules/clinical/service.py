"""Clinical module services.

All business logic moved out during Fase B: patient logic is in
``app.modules.patients.service``; appointment logic in
``app.modules.agenda.service``; timeline logic in
``app.modules.patient_timeline.service``. Re-exported here so legacy
``from app.modules.clinical.service import ...`` keeps working.
"""

from app.modules.agenda.service import AppointmentService  # noqa: F401
from app.modules.patient_timeline.service import TimelineService  # noqa: F401
from app.modules.patients.service import PatientService  # noqa: F401
