"""India GST event handlers.

v1 consumes and emits nothing — GST compliance data is written
synchronously via ``BillingComplianceHook`` (see ``hook.py``), not the
event bus, matching verifactu's "hook, not event bus" rationale for
invoice-issuance-time writes. Kept as an explicit empty module (rather
than omitted) so a future event handler has an obvious home.
"""
