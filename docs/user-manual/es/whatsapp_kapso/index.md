---
module: whatsapp_kapso
last_verified_commit: 0000000
---

# WhatsApp (Kapso)

Este módulo opcional conecta el **número de WhatsApp de la clínica** con
DentalPin a través de [Kapso](https://kapso.ai), para enviar recordatorios y
mensajes por WhatsApp y **recibir y responder** a los pacientes.

Es el "cable": la lógica de comunicaciones (canales, consentimiento, cola de
envío, conversación) vive en el módulo de Notificaciones. WhatsApp se activa
instalando este módulo y conectando la cuenta de Kapso.

## Pantallas

- [Conectar WhatsApp](./screens/connect.md) — credenciales de Kapso, URL del
  webhook, sincronización de plantillas y prueba de envío.

## Antes de empezar

- Cada clínica necesita su cuenta de WhatsApp Business (WABA) con facturación de
  Meta y un proyecto en Kapso.
- Los mensajes proactivos (recordatorios) requieren una **plantilla aprobada**
  por Meta. El texto libre solo se puede enviar dentro de las 24h posteriores a
  un mensaje del paciente.
