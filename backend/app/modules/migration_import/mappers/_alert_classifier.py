"""Robust classifier for free-text Gesdén patient alerts.

Gesdén stores all patient medical history in ``AlertPac`` as a single
free-text column (``Texto``). Different clinics use the field in
wildly different ways — observed patterns include:

- Explicit prefixed lists: ``MEDICACION: ZOCOR 10, METFORMINA``,
  ``ALERGIA: AUGMENTINE``.
- Single-keyword diagnoses: ``HIPERTENSION``, ``DIABETICA``, ``LACTANCIA``.
- Lifestyle notes: ``FUMADORA DE 10/15 CIGARROS AL DIA``.
- Anesthesia contraindications: ``ANESTESIA SIN VASO``.
- Administrative leftovers: ``PRESU. MANT.``, ``COBRAR SOLO GASTOS``,
  ``BUSCAR DESTORNILLADOR KLOCKNER``.

The classifier routes each alert text into one of:

- ``"allergy"``       → ``patients_clinical.Allergy`` rows
- ``"medication"``    → ``patients_clinical.Medication`` rows
- ``"disease"``       → ``patients_clinical.SystemicDisease`` rows
- ``"anesthesia"``    → ``MedicalContext.adverse_reactions_to_anesthesia``
- ``"smoking"``       → ``MedicalContext.is_smoker`` + ``smoking_frequency``
- ``"pregnancy"``     → ``MedicalContext.is_pregnant``
- ``"lactating"``     → ``MedicalContext.is_lactating``
- ``"anticoagulant"`` → ``MedicalContext.is_on_anticoagulants`` + ``anticoagulant_medication``
- ``"bruxism"``       → ``MedicalContext.bruxism``
- ``"administrative"``→ skipped (with warning)
- ``"general"``       → falls back to ``Patient.notes`` append

Rules are evaluated top-down — first match wins. Adding a clinic
convention is a one-line addition to ``_RULES``. Keep matching
case-insensitive; the source text is uppercase ~80% of the time but
clinics with newer staff use mixed-case freely.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class AlertClassification:
    """Outcome of classifying one ``AlertPac.Texto`` entry."""

    category: str
    items: list[str] = field(default_factory=list)
    raw_text: str = ""


def _strip_accents(text: str) -> str:
    """Strip Spanish accents so 'ALÉRGICO' matches the same rule as 'ALERGICO'."""
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def _split_list(payload: str) -> list[str]:
    """Split a list payload (commas, ' y ', semicolons) into trimmed items."""
    parts = re.split(r"[,;]| y |\sy\s", payload, flags=re.IGNORECASE)
    return [p.strip(" .") for p in parts if p.strip(" .")]


# Pattern → category. Evaluated in order — first match wins. Each
# pattern is matched against the *upper, accent-stripped* version of
# the text so authoring stays simple (no need to worry about case or
# tildes). The pattern operates on the FULL text; sub-extraction (the
# list payload after the prefix) is handled by ``_extract_payload``.
_RULES: Final[list[tuple[re.Pattern[str], str]]] = [
    # ---- High-confidence prefixed lists ----
    (re.compile(r"^MEDICACION(?:\s+HABITUAL)?\s*:"), "medication"),
    (re.compile(r"^ALERGIAS?\s*:"), "allergy"),
    # ---- Administrative leftovers ----
    (re.compile(r"^PRESU\b"), "administrative"),
    (re.compile(r"^DTO\b|DESCUENTO|^\d+\s*%"), "administrative"),
    (re.compile(r"\b(?:COBRAR|COBRA|NO\s+SE\s+COBRA|ABONA|PAGAR|PAGA|ENVIAR\s+FACTURA|FACTURA\s+CADA)"), "administrative"),
    (re.compile(r"^BUSCAR\b"), "administrative"),
    (re.compile(r"^VIENE\s+REFERIDO|^REFERIDA?\s+POR\b"), "administrative"),
    (re.compile(r"\bHISTORIAL\s+ALERGICO\s+ESCANEADO\b"), "administrative"),
    # ---- Pregnancy / lactation (must match before generic disease) ----
    (re.compile(r"\b(EMBARAZAD?A|GESTANTE|\d+\s+SEMANAS)\b"), "pregnancy"),
    (re.compile(r"\b(LACTANCIA|LACTANTE|AMAMANT)"), "lactating"),
    # ---- Anesthesia ----
    (re.compile(r"\bANESTESIA\b|\bVASOCONSTRICTOR\b|SIN\s+VASO\b|\bADRENALINA\b"), "anesthesia"),
    # ---- Anticoagulants (medication subset that matters clinically) ----
    (re.compile(r"\b(SINTROM|WARFARIN|ALDOCUMAR|HEPARIN|ADIRO|PRADAXA|XARELTO|ELIQUIS|CLOPIDOGREL|PLAVIX|ANTICOAG)"), "anticoagulant"),
    # ---- Bruxism ----
    (re.compile(r"\bBRUXISM|\bRECHINAR\b|\bAPRIETA\s+(?:LOS\s+)?DIENTES\b"), "bruxism"),
    # ---- Lifestyle: smoking ----
    (re.compile(r"\bFUMAD?O?R?A?\b|\bCIGARR|\bTABACO\b|\bPAQUETE/?\s*DIA?\b"), "smoking"),
    # ---- Single-word allergies (no ALERGIA: prefix) ----
    (re.compile(r"\bALERGIC[OA]\b|\bALERGI[AC]"), "allergy"),
    # ---- Common systemic diseases ----
    # NOTE: only the LEADING ``\b`` is used — the trailing boundary
    # would refuse "HEPATITIS" against the rule "HEPATIT" because the
    # following "IS" suffix doesn't satisfy ``\b``. Prefix-matching is
    # the right semantics for medical term roots.
    (
        re.compile(
            r"\b(?:HIPERTENS|HTA|"
            r"DIABETI?C?|DIABETES|"
            r"COLESTEROL|HIPERLIPI|"
            r"HEPATIT|HIV|VIH|SIDA|CIRROS|"
            r"CANCER|TUMOR|LINFOM|MIELOM|"
            r"ASMA|ASMATIC|BRONQUI[TC]|"
            r"EPILEP|"
            r"CARDIOPATIA|CORONAR|INFART|ANGINA|ARRITMI|MARCAPAS|"
            r"PARKINSON|ALZHEI|DEMENCI|"
            r"HIPOTIROID|HIPERTIROID|TIROIDE|"
            r"DEPRESI|ANSIE|BIPOLAR|ESQUIZOFREN|"
            r"REUMATIC|ARTRITIS|FIBROMIAL|"
            r"INSUFICIENCIA\s+RENAL|"
            r"SINUSIT|"
            r"PSORIASIS|SORIASIS|"
            r"GLAUCOMA|"
            r"OSTEOPOROSIS|"
            r"ANEMIA|"
            r"ANISAKIS|"
            r"TRASTORNO|TRANSTORNO|"
            r"TENSION\s+ALTA|"
            r"SINDROME)"
        ),
        "disease",
    ),
    # ---- Medication patterns ----
    # ``TOMA <drug>`` and ``DOSE`` markers are the cheap wins.
    (re.compile(r"^TOMA\b"), "medication"),
    # Explicit dose tokens — Spanish "MG", "MGS" (mg singular/plural),
    # "MCG", "G", "ML", "UI"; also catches "10 MGS." with optional dot.
    (re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:MGS?|MCG|UI|ML|G)\b\.?"), "medication"),
    # Bare ``<DRUG NAME> <NUMBER>`` heuristic: an ALL-CAPS token (≥4
    # letters) followed by a number is overwhelmingly a drug + dose
    # in this dataset (e.g. ``ENALAPRIL 20``, ``RENITEC 20``,
    # ``ATORRASTATINA 10``). Single CAPS words like ``DIABETES`` are
    # caught by the disease rule above so they don't reach this one.
    (re.compile(r"\b[A-Z]{4,}\s+\d+\b"), "medication"),
]


def classify_alert(text: str | None) -> AlertClassification:
    """Classify a Gesdén ``AlertPac.Texto`` entry into a clinical bucket."""
    if not text:
        return AlertClassification(category="general", raw_text="")
    raw = text.strip()
    if not raw:
        return AlertClassification(category="general", raw_text="")
    normalised = _strip_accents(raw.upper())

    for pattern, category in _RULES:
        if pattern.search(normalised):
            return _extract(category, raw, normalised, pattern)

    return AlertClassification(category="general", raw_text=raw)


def _extract(
    category: str, raw: str, normalised: str, pattern: re.Pattern[str]
) -> AlertClassification:
    """Build the category-specific payload (item list, frequency string, …)."""
    if category in ("medication", "allergy"):
        match = pattern.search(normalised)
        if match and ":" in raw[match.start():]:
            # Strip the "MEDICACION: " / "ALERGIA: " prefix before splitting.
            payload = raw[match.start():].split(":", 1)[1]
        elif raw.upper().startswith("TOMA "):
            payload = raw[5:]
        else:
            payload = raw
        items = _split_list(payload)
        return AlertClassification(category=category, items=items, raw_text=raw)

    if category == "disease":
        # Diseases often appear in a comma-separated list too
        # ("DIABETES, TRAS. CARDIACOS, HIPERTENSIÓN") — split when the
        # whole text looks like a list.
        items = _split_list(raw) if "," in raw else [raw]
        return AlertClassification(category=category, items=items, raw_text=raw)

    # smoking / pregnancy / lactating / anesthesia / bruxism /
    # anticoagulant / administrative / general — these carry no list,
    # just the raw text for downstream context.
    return AlertClassification(category=category, raw_text=raw)
