"""Seed data for the catalog module.

This script creates the initial treatment categories and catalog items
representing COMMERCIAL/BILLABLE treatments. Odontogram visualization
mapping is OPTIONAL - many treatments (like cleanings, orthodontics packages)
don't need tooth-level visualization.

NOTE: Diagnostic findings (caries, pulpitis, fracture, etc.) and orthodontic
components (brackets, tubes, bands) are NOT included here - they are
visualization-only elements, not billable treatments.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    TreatmentCatalogItem,
    TreatmentCategory,
    TreatmentOdontogramMapping,
    VatType,
)

# ============================================================================
# VAT Type Definitions
# ============================================================================

VAT_TYPES = [
    {
        "key": "exempt",
        "names": {"es": "Exento", "en": "Exempt"},
        "rate": 0.0,
        "is_default": True,
    },
    {
        "key": "reduced",
        "names": {"es": "Reducido (10%)", "en": "Reduced (10%)"},
        "rate": 10.0,
        "is_default": False,
    },
    {
        "key": "standard",
        "names": {"es": "General (21%)", "en": "Standard (21%)"},
        "rate": 21.0,
        "is_default": False,
    },
]

# ============================================================================
# Category Definitions (9 categories)
# ============================================================================

CATEGORIES = [
    {
        "key": "diagnostico",
        "names": {"es": "Diagnóstico", "en": "Diagnostic"},
        "descriptions": {
            "es": "Servicios de diagnóstico y evaluación",
            "en": "Diagnostic and evaluation services",
        },
        "display_order": 1,
        "icon": "i-lucide-stethoscope",
    },
    {
        "key": "preventivo",
        "names": {"es": "Preventivo", "en": "Preventive"},
        "descriptions": {
            "es": "Servicios de prevención e higiene dental",
            "en": "Preventive and dental hygiene services",
        },
        "display_order": 2,
        "icon": "i-lucide-shield-check",
    },
    {
        "key": "restauradora",
        "names": {"es": "Restauradora", "en": "Restorative"},
        "descriptions": {
            "es": "Tratamientos de restauración dental",
            "en": "Dental restoration treatments",
        },
        "display_order": 3,
        "icon": "i-lucide-brush",
    },
    {
        "key": "endodoncia",
        "names": {"es": "Endodoncia", "en": "Endodontics"},
        "descriptions": {
            "es": "Tratamientos de conducto radicular",
            "en": "Root canal treatments",
        },
        "display_order": 4,
        "icon": "i-lucide-activity",
    },
    {
        "key": "periodoncia",
        "names": {"es": "Periodoncia", "en": "Periodontics"},
        "descriptions": {
            "es": "Tratamientos de encías y tejidos de soporte",
            "en": "Gum and supporting tissue treatments",
        },
        "display_order": 5,
        "icon": "i-lucide-heart-pulse",
    },
    {
        "key": "cirugia",
        "names": {"es": "Cirugía", "en": "Surgery"},
        "descriptions": {
            "es": "Procedimientos quirúrgicos dentales",
            "en": "Dental surgical procedures",
        },
        "display_order": 6,
        "icon": "i-lucide-scissors",
    },
    {
        "key": "ortodoncia",
        "names": {"es": "Ortodoncia", "en": "Orthodontics"},
        "descriptions": {
            "es": "Tratamientos de ortodoncia y alineación",
            "en": "Orthodontic and alignment treatments",
        },
        "display_order": 7,
        "icon": "i-lucide-align-center",
    },
    {
        "key": "estetica",
        "names": {"es": "Estética", "en": "Cosmetic"},
        "descriptions": {
            "es": "Tratamientos estéticos dentales",
            "en": "Cosmetic dental treatments",
        },
        "display_order": 8,
        "icon": "i-lucide-sparkles",
    },
    {
        "key": "protesis",
        "names": {"es": "Prótesis", "en": "Prosthetics"},
        "descriptions": {
            "es": "Prótesis dentales removibles y férulas",
            "en": "Removable dental prosthetics and splints",
        },
        "display_order": 9,
        "icon": "i-lucide-puzzle",
    },
]


# ============================================================================
# Treatment Definitions - COMMERCIAL/BILLABLE TREATMENTS
# ============================================================================
#
# Each treatment has:
# - internal_code: Unique code for the treatment
# - names: Localized names
# - treatment_scope: "surface" or "whole_tooth"
# - is_diagnostic: False (these are all billable procedures)
# - requires_surfaces: Whether surface selection is needed
# - default_price: Example price (clinics should customize)
# - default_duration_minutes: Typical duration
# - vat_type: "exempt" for healthcare, "standard" for cosmetic
# - odontogram_treatment_type: OPTIONAL - maps to visualization (None = no viz)
# - visualization_rules: OPTIONAL - how to render in odontogram
# - visualization_config: OPTIONAL - color and style settings

TREATMENTS = {
    "diagnostico": [
        {
            "internal_code": "DX-VISIT",
            "names": {"es": "Primera Visita", "en": "First Visit"},
            "descriptions": {
                "es": "Consulta inicial con exploración y diagnóstico",
                "en": "Initial consultation with examination and diagnosis",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("30.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            # No odontogram mapping - not a tooth-specific treatment
        },
        {
            "internal_code": "DX-RXPA",
            "names": {"es": "Radiografía Periapical", "en": "Periapical X-Ray"},
            "descriptions": {
                "es": "Radiografía de un diente o zona específica",
                "en": "X-ray of a specific tooth or area",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("15.00"),
            "default_duration_minutes": 10,
            "vat_type": "exempt",
        },
        {
            "internal_code": "DX-RXPAN",
            "names": {"es": "Radiografía Panorámica", "en": "Panoramic X-Ray"},
            "descriptions": {
                "es": "Radiografía panorámica de toda la boca",
                "en": "Panoramic x-ray of the entire mouth",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("40.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
        },
        {
            "internal_code": "DX-TAC",
            "names": {"es": "TAC / Scanner 3D", "en": "CT Scan / 3D Scanner"},
            "descriptions": {
                "es": "Tomografía computarizada dental",
                "en": "Dental computed tomography scan",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("80.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
        },
        {
            "internal_code": "DX-ESTORTO",
            "names": {"es": "Estudio Ortodóntico", "en": "Orthodontic Study"},
            "descriptions": {
                "es": "Estudio completo para planificación ortodóntica",
                "en": "Complete study for orthodontic planning",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("50.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
        },
    ],
    "preventivo": [
        {
            "internal_code": "PREV-LIMP",
            "names": {"es": "Limpieza Dental", "en": "Dental Cleaning"},
            "descriptions": {
                "es": "Profilaxis y limpieza dental profesional",
                "en": "Professional dental cleaning and prophylaxis",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("60.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            # No odontogram mapping - applies to whole mouth
        },
        {
            "internal_code": "PREV-FLUOR",
            "names": {"es": "Aplicación de Flúor", "en": "Fluoride Application"},
            "descriptions": {
                "es": "Aplicación tópica de flúor preventivo",
                "en": "Topical preventive fluoride application",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("25.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
        },
        {
            "internal_code": "PREV-SELL",
            "names": {"es": "Sellador de Fisuras", "en": "Pit and Fissure Sealant"},
            "descriptions": {
                "es": "Sellador de fosas y fisuras preventivo",
                "en": "Preventive pit and fissure sealant",
            },
            "treatment_scope": "surface",
            "is_diagnostic": False,
            "requires_surfaces": True,
            "default_price": Decimal("40.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
            "odontogram_treatment_type": "sealant",
            "visualization_rules": ["occlusal_surface"],
            "visualization_config": {
                "color": {"light": "#06B6D4", "dark": "#22D3EE"},
                "occlusal_type": "outline",
            },
        },
    ],
    "restauradora": [
        {
            "internal_code": "REST-COMP",
            "names": {"es": "Obturación Composite", "en": "Composite Filling"},
            "descriptions": {
                "es": "Obturación con resina compuesta",
                "en": "Composite resin filling",
            },
            "treatment_scope": "surface",
            "is_diagnostic": False,
            "requires_surfaces": True,
            "default_price": Decimal("80.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "odontogram_treatment_type": "filling_composite",
            "visualization_rules": ["occlusal_surface"],
            "visualization_config": {
                "color": {"light": "#3B82F6", "dark": "#60A5FA"},
                "occlusal_type": "solid_fill",
            },
        },
        {
            "internal_code": "REST-AMAL",
            "names": {"es": "Obturación Amalgama", "en": "Amalgam Filling"},
            "descriptions": {
                "es": "Obturación con amalgama de plata",
                "en": "Silver amalgam filling",
            },
            "treatment_scope": "surface",
            "is_diagnostic": False,
            "requires_surfaces": True,
            "default_price": Decimal("60.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "odontogram_treatment_type": "filling_amalgam",
            "visualization_rules": ["occlusal_surface"],
            "visualization_config": {
                "color": {"light": "#6B7280", "dark": "#9CA3AF"},
                "occlusal_type": "solid_fill",
            },
        },
        {
            "internal_code": "REST-RECON",
            "names": {"es": "Reconstrucción", "en": "Reconstruction"},
            "descriptions": {
                "es": "Reconstrucción dental amplia con composite",
                "en": "Large dental reconstruction with composite",
            },
            "treatment_scope": "surface",
            "is_diagnostic": False,
            "requires_surfaces": True,
            "default_price": Decimal("120.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "odontogram_treatment_type": "filling_composite",
            "visualization_rules": ["occlusal_surface"],
            "visualization_config": {
                "color": {"light": "#3B82F6", "dark": "#60A5FA"},
                "occlusal_type": "solid_fill",
            },
        },
        {
            "internal_code": "REST-VEN",
            "names": {"es": "Carilla", "en": "Veneer"},
            "descriptions": {
                "es": "Carilla dental estética",
                "en": "Aesthetic dental veneer",
            },
            "treatment_scope": "surface",
            "is_diagnostic": False,
            "requires_surfaces": True,
            "default_price": Decimal("500.00"),
            "default_duration_minutes": 60,
            "vat_type": "standard",
            "vat_rate": 21.0,
            "odontogram_treatment_type": "veneer",
            "visualization_rules": ["occlusal_surface"],
            "visualization_config": {
                "color": {"light": "#EC4899", "dark": "#F472B6"},
                "occlusal_type": "solid_fill",
            },
        },
        {
            "internal_code": "REST-INL",
            "names": {"es": "Inlay/Onlay", "en": "Inlay/Onlay"},
            "descriptions": {
                "es": "Restauración indirecta inlay u onlay",
                "en": "Indirect inlay or onlay restoration",
            },
            "treatment_scope": "surface",
            "is_diagnostic": False,
            "requires_surfaces": True,
            "default_price": Decimal("350.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "odontogram_treatment_type": "inlay",
            "visualization_rules": ["pattern_fill"],
            "visualization_config": {
                "color": {"light": "#3B82F6", "dark": "#60A5FA"},
                "pattern": "dots",
            },
        },
        {
            "internal_code": "REST-CRO",
            "names": {"es": "Corona", "en": "Crown"},
            "descriptions": {
                "es": "Corona dental",
                "en": "Dental crown",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "odontogram_treatment_type": "crown",
            "visualization_rules": ["pattern_fill"],
            "visualization_config": {
                "color": {"light": "#F59E0B", "dark": "#FBBF24"},
                "pattern": "diagonal_stripes",
            },
        },
        {
            "internal_code": "REST-PON",
            "names": {"es": "Póntico", "en": "Pontic"},
            "descriptions": {
                "es": "Póntico de puente dental",
                "en": "Dental bridge pontic",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("500.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "odontogram_treatment_type": "pontic",
            "visualization_rules": ["pattern_fill"],
            "visualization_config": {
                "color": {"light": "#F97316", "dark": "#FB923C"},
                "pattern": "grid",
            },
        },
        {
            "internal_code": "REST-ABUT",
            "names": {"es": "Pilar de Puente", "en": "Bridge Abutment"},
            "descriptions": {
                "es": "Diente pilar para puente dental",
                "en": "Bridge abutment tooth",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("450.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "odontogram_treatment_type": "bridge_abutment",
            "visualization_rules": ["pattern_fill"],
            "visualization_config": {
                "color": {"light": "#FBBF24", "dark": "#FDE68A"},
                "pattern": "vertical_stripes",
            },
        },
    ],
    "endodoncia": [
        {
            "internal_code": "ENDO-UNI",
            "names": {"es": "Endodoncia Unirradicular", "en": "Single-Root Endodontics"},
            "descriptions": {
                "es": "Tratamiento de conducto en diente unirradicular",
                "en": "Root canal treatment for single-rooted tooth",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("150.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": ["pulp_fill"],
            "visualization_config": {
                "color": {"light": "#8B5CF6", "dark": "#A78BFA"},
                "pulp_level": "full",
            },
        },
        {
            "internal_code": "ENDO-BI",
            "names": {"es": "Endodoncia Birradicular", "en": "Two-Root Endodontics"},
            "descriptions": {
                "es": "Tratamiento de conducto en diente birradicular",
                "en": "Root canal treatment for two-rooted tooth",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("200.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": ["pulp_fill"],
            "visualization_config": {
                "color": {"light": "#8B5CF6", "dark": "#A78BFA"},
                "pulp_level": "full",
            },
        },
        {
            "internal_code": "ENDO-MULTI",
            "names": {"es": "Endodoncia Multirradicular", "en": "Multi-Root Endodontics"},
            "descriptions": {
                "es": "Tratamiento de conducto en diente multirradicular",
                "en": "Root canal treatment for multi-rooted tooth",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("280.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": ["pulp_fill"],
            "visualization_config": {
                "color": {"light": "#8B5CF6", "dark": "#A78BFA"},
                "pulp_level": "full",
            },
        },
        {
            "internal_code": "ENDO-RETRAT",
            "names": {"es": "Retratamiento de Conductos", "en": "Root Canal Retreatment"},
            "descriptions": {
                "es": "Retratamiento de endodoncia previa",
                "en": "Retreatment of previous root canal",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("300.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": ["pulp_fill"],
            "visualization_config": {
                "color": {"light": "#8B5CF6", "dark": "#A78BFA"},
                "pulp_level": "full",
            },
        },
    ],
    "periodoncia": [
        {
            "internal_code": "PERIO-RAD",
            "names": {
                "es": "Raspado y Alisado (Cuadrante)",
                "en": "Scaling and Root Planing (Quadrant)",
            },
            "descriptions": {
                "es": "Raspado y alisado radicular por cuadrante",
                "en": "Scaling and root planing per quadrant",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("80.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            # No odontogram mapping - treatment per quadrant, not per tooth
        },
        {
            "internal_code": "PERIO-CIR",
            "names": {"es": "Cirugía Periodontal", "en": "Periodontal Surgery"},
            "descriptions": {
                "es": "Cirugía de encías y tejidos periodontales",
                "en": "Gum and periodontal tissue surgery",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("200.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
        },
        {
            "internal_code": "PERIO-REGEN",
            "names": {"es": "Regeneración Ósea", "en": "Bone Regeneration"},
            "descriptions": {
                "es": "Regeneración ósea guiada",
                "en": "Guided bone regeneration",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("400.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
        },
    ],
    "cirugia": [
        {
            "internal_code": "CIR-EXT-S",
            "names": {"es": "Extracción Simple", "en": "Simple Extraction"},
            "descriptions": {
                "es": "Extracción dental simple",
                "en": "Simple dental extraction",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("60.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": ["lateral_icon"],
            "visualization_config": {
                "color": {"light": "#DC2626", "dark": "#EF4444"},
            },
        },
        {
            "internal_code": "CIR-EXT-Q",
            "names": {"es": "Extracción Quirúrgica", "en": "Surgical Extraction"},
            "descriptions": {
                "es": "Extracción con abordaje quirúrgico",
                "en": "Extraction with surgical approach",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("120.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": ["lateral_icon"],
            "visualization_config": {
                "color": {"light": "#DC2626", "dark": "#EF4444"},
            },
        },
        {
            "internal_code": "CIR-EXT-CORD",
            "names": {"es": "Extracción Cordal", "en": "Wisdom Tooth Extraction"},
            "descriptions": {
                "es": "Extracción de muela del juicio",
                "en": "Wisdom tooth extraction",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("150.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": ["lateral_icon"],
            "visualization_config": {
                "color": {"light": "#DC2626", "dark": "#EF4444"},
            },
        },
        {
            "internal_code": "CIR-IMP",
            "names": {"es": "Implante Dental", "en": "Dental Implant"},
            "descriptions": {
                "es": "Colocación de implante dental",
                "en": "Dental implant placement",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("800.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "odontogram_treatment_type": "implant",
            "visualization_rules": ["lateral_icon"],
            "visualization_config": {
                "color": {"light": "#10B981", "dark": "#34D399"},
            },
        },
        {
            "internal_code": "CIR-CRO-IMP",
            "names": {"es": "Corona sobre Implante", "en": "Crown on Implant"},
            "descriptions": {
                "es": "Corona protésica sobre implante",
                "en": "Prosthetic crown on implant",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "odontogram_treatment_type": "crown",
            "visualization_rules": ["pattern_fill"],
            "visualization_config": {
                "color": {"light": "#F59E0B", "dark": "#FBBF24"},
                "pattern": "diagonal_stripes",
            },
        },
        {
            "internal_code": "CIR-APIC",
            "names": {"es": "Apicectomía", "en": "Apicoectomy"},
            "descriptions": {
                "es": "Resección del ápice radicular",
                "en": "Root apex resection",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("300.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "odontogram_treatment_type": "apicoectomy",
            "visualization_rules": ["lateral_icon"],
            "visualization_config": {
                "color": {"light": "#6366F1", "dark": "#818CF8"},
            },
        },
    ],
    "ortodoncia": [
        {
            "internal_code": "ORTO-MET",
            "names": {"es": "Ortodoncia Metálica", "en": "Metal Braces"},
            "descriptions": {
                "es": "Tratamiento completo con brackets metálicos",
                "en": "Complete treatment with metal brackets",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("2500.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            # No odontogram mapping - full treatment, not per tooth
        },
        {
            "internal_code": "ORTO-EST",
            "names": {"es": "Ortodoncia Estética", "en": "Aesthetic Braces"},
            "descriptions": {
                "es": "Tratamiento completo con brackets estéticos",
                "en": "Complete treatment with aesthetic brackets",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("3500.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
        },
        {
            "internal_code": "ORTO-INVIS",
            "names": {"es": "Invisalign / Alineadores", "en": "Invisalign / Aligners"},
            "descriptions": {
                "es": "Tratamiento con alineadores transparentes",
                "en": "Treatment with clear aligners",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("4000.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
        },
        {
            "internal_code": "ORTO-RET-F",
            "names": {"es": "Retenedor Fijo", "en": "Fixed Retainer"},
            "descriptions": {
                "es": "Retenedor fijo de ortodoncia",
                "en": "Fixed orthodontic retainer",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("150.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "odontogram_treatment_type": "retainer",
            "visualization_rules": ["lateral_icon"],
            "visualization_config": {
                "color": {"light": "#14B8A6", "dark": "#2DD4BF"},
            },
        },
        {
            "internal_code": "ORTO-RET-R",
            "names": {"es": "Retenedor Removible", "en": "Removable Retainer"},
            "descriptions": {
                "es": "Retenedor removible de ortodoncia",
                "en": "Removable orthodontic retainer",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("100.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            # No odontogram mapping - removable, not attached to tooth
        },
    ],
    "estetica": [
        {
            "internal_code": "EST-BLANQ-C",
            "names": {"es": "Blanqueamiento Clínica", "en": "In-Office Whitening"},
            "descriptions": {
                "es": "Blanqueamiento dental en clínica",
                "en": "In-office dental whitening",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("300.00"),
            "default_duration_minutes": 60,
            "vat_type": "standard",
            "vat_rate": 21.0,
            # No odontogram mapping - cosmetic, whole mouth
        },
        {
            "internal_code": "EST-BLANQ-A",
            "names": {"es": "Blanqueamiento Ambulatorio", "en": "Take-Home Whitening"},
            "descriptions": {
                "es": "Kit de blanqueamiento para uso domiciliario",
                "en": "Take-home whitening kit",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("200.00"),
            "default_duration_minutes": 30,
            "vat_type": "standard",
            "vat_rate": 21.0,
        },
        {
            "internal_code": "EST-CONT",
            "names": {"es": "Contorneado Estético", "en": "Cosmetic Contouring"},
            "descriptions": {
                "es": "Contorneado estético del esmalte",
                "en": "Cosmetic enamel contouring",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("100.00"),
            "default_duration_minutes": 30,
            "vat_type": "standard",
            "vat_rate": 21.0,
        },
    ],
    "protesis": [
        {
            "internal_code": "PROT-COMP",
            "names": {"es": "Prótesis Completa", "en": "Complete Denture"},
            "descriptions": {
                "es": "Prótesis dental completa removible",
                "en": "Complete removable dental denture",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("800.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            # No odontogram mapping - applies to whole arch
        },
        {
            "internal_code": "PROT-PARC",
            "names": {"es": "Prótesis Parcial Removible", "en": "Partial Removable Denture"},
            "descriptions": {
                "es": "Prótesis parcial removible metálica o acrílica",
                "en": "Metal or acrylic partial removable denture",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("500.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
        },
        {
            "internal_code": "PROT-FER",
            "names": {"es": "Férula de Descarga", "en": "Occlusal Splint"},
            "descriptions": {
                "es": "Férula de descarga para bruxismo",
                "en": "Occlusal splint for bruxism",
            },
            "treatment_scope": "whole_tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("250.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
        },
    ],
}


async def seed_vat_types(db: AsyncSession, clinic_id: UUID) -> dict[str, UUID]:
    """Seed VAT types for a specific clinic.

    Args:
        db: Database session
        clinic_id: The clinic ID to seed VAT types for

    Returns:
        Mapping of VAT type key to ID: {"exempt": UUID, "reduced": UUID, "standard": UUID}
    """
    vat_type_map: dict[str, UUID] = {}

    for vat_data in VAT_TYPES:
        # Check if VAT type already exists (by rate, since key is not stored)
        existing = await db.execute(
            select(VatType).where(
                VatType.clinic_id == clinic_id,
                VatType.rate == vat_data["rate"],
            )
        )
        vat_type = existing.scalar_one_or_none()

        if not vat_type:
            vat_type = VatType(
                clinic_id=clinic_id,
                names=vat_data["names"],
                rate=vat_data["rate"],
                is_default=vat_data["is_default"],
                is_system=True,
                is_active=True,
            )
            db.add(vat_type)
            await db.flush()

        vat_type_map[vat_data["key"]] = vat_type.id

    return vat_type_map


async def seed_catalog(db: AsyncSession, clinic_id: UUID, lang: str = "en") -> dict:
    """Seed the catalog for a specific clinic.

    Args:
        db: Database session
        clinic_id: The clinic ID to seed data for
        lang: Language for names/descriptions ("en" or "es"). Default: "en"

    Returns:
        Summary of seeded data: {"categories": count, "items": count, "vat_types": count}
    """
    # First, seed VAT types
    vat_type_map = await seed_vat_types(db, clinic_id)

    categories_created = 0
    items_created = 0
    category_map: dict[str, UUID] = {}

    # Create categories
    for cat_data in CATEGORIES:
        # Check if category already exists
        existing = await db.execute(
            select(TreatmentCategory).where(
                TreatmentCategory.clinic_id == clinic_id,
                TreatmentCategory.key == cat_data["key"],
            )
        )
        category = existing.scalar_one_or_none()

        if not category:
            category = TreatmentCategory(
                clinic_id=clinic_id,
                is_system=True,
                **cat_data,
            )
            db.add(category)
            await db.flush()
            categories_created += 1

        category_map[cat_data["key"]] = category.id

    # Create treatments
    for category_key, treatments in TREATMENTS.items():
        category_id = category_map.get(category_key)
        if not category_id:
            continue

        for treatment_data in treatments:
            # Make a copy to avoid modifying original
            treatment_data = dict(treatment_data)

            # Extract odontogram-specific data (OPTIONAL)
            odontogram_type = treatment_data.pop("odontogram_treatment_type", None)
            viz_rules = treatment_data.pop("visualization_rules", None)
            viz_config = treatment_data.pop("visualization_config", None)

            # Extract VAT type and look up the ID
            vat_type_key = treatment_data.pop("vat_type", "exempt")
            treatment_data.pop("vat_rate", None)  # Remove legacy field if present
            vat_type_id = vat_type_map.get(vat_type_key, vat_type_map.get("exempt"))

            # Check if item already exists
            existing = await db.execute(
                select(TreatmentCatalogItem).where(
                    TreatmentCatalogItem.clinic_id == clinic_id,
                    TreatmentCatalogItem.internal_code == treatment_data["internal_code"],
                )
            )
            item = existing.scalar_one_or_none()

            if not item:
                item = TreatmentCatalogItem(
                    clinic_id=clinic_id,
                    category_id=category_id,
                    vat_type_id=vat_type_id,
                    is_system=True,
                    **treatment_data,
                )
                db.add(item)
                await db.flush()

                # Create odontogram mapping ONLY if has visualization
                if odontogram_type and viz_rules and viz_config:
                    mapping = TreatmentOdontogramMapping(
                        clinic_id=clinic_id,
                        catalog_item_id=item.id,
                        odontogram_treatment_type=odontogram_type,
                        visualization_rules=viz_rules,
                        visualization_config=viz_config,
                        clinical_category=category_key,
                    )
                    db.add(mapping)

                items_created += 1

    await db.flush()

    return {
        "categories": categories_created,
        "items": items_created,
        "vat_types": len(vat_type_map),
    }


async def seed_all_clinics(db: AsyncSession) -> dict:
    """Seed catalog for all existing clinics.

    Returns:
        Summary of seeded data per clinic
    """
    from app.core.auth.models import Clinic

    result = await db.execute(select(Clinic))
    clinics = result.scalars().all()

    summary = {}
    for clinic in clinics:
        clinic_summary = await seed_catalog(db, clinic.id)
        summary[str(clinic.id)] = clinic_summary

    return summary
