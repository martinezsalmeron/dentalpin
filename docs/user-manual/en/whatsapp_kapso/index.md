---
module: whatsapp_kapso
last_verified_commit: 0000000
---

# WhatsApp (Kapso)

This optional module connects the clinic's **WhatsApp number** to DentalPin
through [Kapso](https://kapso.ai), to send reminders and messages over WhatsApp
and to **receive and reply** to patients.

It is the "wire": the communications logic (channels, consent, send queue,
conversation) lives in the Notifications module. WhatsApp is enabled by
installing this module and connecting the Kapso account.

## Screens

- [Connect WhatsApp](./screens/connect.md) — Kapso credentials, webhook URL,
  template sync and test send.

## Before you start

- Each clinic needs its own WhatsApp Business Account (WABA) with Meta billing
  and a Kapso project.
- Proactive messages (reminders) require a Meta-**approved template**. Free-form
  text can only be sent within 24h of a message from the patient.
