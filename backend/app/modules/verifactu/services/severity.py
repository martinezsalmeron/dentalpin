"""Map a Verifactu record state + AEAT error code to a generic severity.

The billing module has a country-agnostic ``compliance_severity`` filter
that uses ``compliance_data.<country>.severity`` directly via JSONB.
Verifactu writes this field every time it touches a record so the
filter stays universal: billing never imports verifactu and never
learns about Spain-specific record states (``failed_transient``,
``rejected``, ``accepted_with_errors`` …).

Severity vocabulary (shared across compliance modules):

* ``ok``       — record accepted, nothing to do.
* ``warning``  — accepted with notes (AceptadoConErrores) — review later.
* ``pending``  — sitting in the queue or being retried for transport
                 reasons. No human action required.
* ``error``    — AEAT rejected the data, OR the worker keeps failing
                 with a business-level error code (-2 SOAP fault that
                 wraps a validation error, or any 4xxx). Human must
                 fix data and re-Subsanate.
"""

from __future__ import annotations

from typing import Literal

Severity = Literal["ok", "warning", "pending", "error"]


def severity_for(state: str | None, codigo_error: int | None) -> Severity:
    """Return the severity for a record's current state + last AEAT code."""

    if state == "accepted":
        return "ok"
    if state == "accepted_with_errors":
        return "warning"
    if state in ("rejected", "failed_validation"):
        return "error"
    if state == "failed_transient":
        c = codigo_error or 0
        # -2 = SOAP fault wrapping a per-record rejection; >= 1000 =
        # AEAT business validation. Anything else (-1 transport error,
        # 103/-904 AEAT availability) is a transient blip the worker
        # auto-retries — surface as pending, not error.
        return "error" if (c == -2 or c >= 1000) else "pending"
    # pending, sending, anything unknown.
    return "pending"
