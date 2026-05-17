---
module: migration_import
last_verified_commit: HEAD
---

# migration_import — events

## Emitted

| Event                       | When                                              | Payload                                                 |
|-----------------------------|---------------------------------------------------|---------------------------------------------------------|
| `migration.job.started`     | BackgroundTask enters `executing`                 | `job_id`, `clinic_id`                                   |
| `migration.job.completed`   | Pipeline ran to the end                           | `job_id`, `clinic_id`, `total_entities`, `warnings_count` |
| `migration.job.failed`      | Unhandled exception in the pipeline               | `job_id`, `clinic_id`, `error`                          |
| `migration.binary.resolved` | Sync agent uploaded a binary that matched a staging row | `job_id`, `staging_id`, `document_id`              |

Plus every event published naturally by the mapped target services —
`patient.created`, `payment.recorded`, `document.uploaded`, etc. The
importer **does not** suppress them: downstream modules
(`patient_timeline`, `recalls`, …) get the same signal they would for
a manually-created entity. This is intentional.

### Internal

| Event                          | Producer       | Consumer            | Purpose                                              |
|--------------------------------|----------------|---------------------|------------------------------------------------------|
| `migration.entity.persisted`   | every mapper   | `events.on_appointment_created_for_progress` | Bumps `processed_entities` for the progress UI. |

## Consumed

None outside the internal `migration.entity.persisted` signal above.
