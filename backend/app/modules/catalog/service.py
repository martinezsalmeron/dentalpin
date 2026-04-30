"""Catalog module service layer - business logic."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.billing.models import InvoiceItem
from app.modules.budget.models import BudgetItem

from .models import TreatmentCatalogItem, TreatmentCategory, TreatmentOdontogramMapping, VatType

# Default VAT types to seed for new clinics
DEFAULT_VAT_TYPES = [
    {
        "names": {"es": "Exento", "en": "Exempt"},
        "rate": 0.0,
        "is_default": True,
        "is_system": True,
    },
    {
        "names": {"es": "Reducido (10%)", "en": "Reduced (10%)"},
        "rate": 10.0,
        "is_default": False,
        "is_system": True,
    },
    {
        "names": {"es": "General (21%)", "en": "Standard (21%)"},
        "rate": 21.0,
        "is_default": False,
        "is_system": True,
    },
]


class VatTypeService:
    """Service for VAT type operations."""

    @staticmethod
    async def list_vat_types(
        db: AsyncSession,
        clinic_id: UUID,
        include_inactive: bool = False,
    ) -> list[VatType]:
        """List all VAT types for a clinic."""
        query = select(VatType).where(VatType.clinic_id == clinic_id)

        if not include_inactive:
            query = query.where(VatType.is_active.is_(True))

        query = query.order_by(VatType.rate, VatType.created_at)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_vat_type(
        db: AsyncSession,
        clinic_id: UUID,
        vat_type_id: UUID,
    ) -> VatType | None:
        """Get a VAT type by ID."""
        result = await db.execute(
            select(VatType).where(
                VatType.id == vat_type_id,
                VatType.clinic_id == clinic_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_default_vat_type(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> VatType | None:
        """Get the default VAT type for a clinic."""
        result = await db.execute(
            select(VatType).where(
                VatType.clinic_id == clinic_id,
                VatType.is_default.is_(True),
                VatType.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_vat_type(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> VatType:
        """Create a new VAT type."""
        # If setting as default, unset existing default
        if data.get("is_default"):
            await VatTypeService._unset_default(db, clinic_id)

        vat_type = VatType(clinic_id=clinic_id, **data)
        db.add(vat_type)
        await db.flush()
        return vat_type

    @staticmethod
    async def update_vat_type(
        db: AsyncSession,
        clinic_id: UUID,
        vat_type: VatType,
        data: dict,
    ) -> VatType:
        """Update a VAT type."""
        # If setting as default, unset existing default first
        if data.get("is_default") and not vat_type.is_default:
            await VatTypeService._unset_default(db, clinic_id)

        for key, value in data.items():
            if value is not None:
                setattr(vat_type, key, value)

        await db.flush()
        return vat_type

    @staticmethod
    async def delete_vat_type(
        db: AsyncSession,
        vat_type: VatType,
    ) -> None:
        """Soft-delete a VAT type (set inactive)."""
        vat_type.is_active = False
        await db.flush()

    @staticmethod
    async def ensure_default_vat_types(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[VatType]:
        """Ensure default VAT types exist for a clinic. Creates them if missing."""
        existing = await VatTypeService.list_vat_types(db, clinic_id, include_inactive=True)

        if existing:
            return existing

        # Create default VAT types
        created = []
        for vat_config in DEFAULT_VAT_TYPES:
            vat_type = VatType(clinic_id=clinic_id, **vat_config)
            db.add(vat_type)
            created.append(vat_type)

        await db.flush()
        return created

    @staticmethod
    async def _unset_default(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> None:
        """Unset the current default VAT type for a clinic."""
        result = await db.execute(
            select(VatType).where(
                VatType.clinic_id == clinic_id,
                VatType.is_default.is_(True),
            )
        )
        current_default = result.scalar_one_or_none()
        if current_default:
            current_default.is_default = False


class CategoryService:
    """Service for treatment category operations."""

    @staticmethod
    async def list_categories(
        db: AsyncSession,
        clinic_id: UUID,
        include_inactive: bool = False,
    ) -> list[TreatmentCategory]:
        """List all categories for a clinic."""
        query = select(TreatmentCategory).where(TreatmentCategory.clinic_id == clinic_id)

        if not include_inactive:
            query = query.where(TreatmentCategory.is_active.is_(True))

        query = query.order_by(TreatmentCategory.display_order, TreatmentCategory.key)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_category_tree(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[TreatmentCategory]:
        """Get categories as a tree structure (top-level categories only).

        Children are loaded via relationship.
        """
        query = (
            select(TreatmentCategory)
            .where(
                TreatmentCategory.clinic_id == clinic_id,
                TreatmentCategory.parent_id.is_(None),
                TreatmentCategory.is_active.is_(True),
            )
            .order_by(TreatmentCategory.display_order)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_category(
        db: AsyncSession,
        clinic_id: UUID,
        category_id: UUID,
        include_inactive: bool = False,
    ) -> TreatmentCategory | None:
        """Get a category by ID."""
        query = select(TreatmentCategory).where(
            TreatmentCategory.id == category_id,
            TreatmentCategory.clinic_id == clinic_id,
        )
        if not include_inactive:
            query = query.where(TreatmentCategory.is_active.is_(True))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_category_by_key(
        db: AsyncSession,
        clinic_id: UUID,
        key: str,
    ) -> TreatmentCategory | None:
        """Get a category by its key."""
        result = await db.execute(
            select(TreatmentCategory).where(
                TreatmentCategory.clinic_id == clinic_id,
                TreatmentCategory.key == key,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_category(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> TreatmentCategory:
        """Create a new category."""
        category = TreatmentCategory(clinic_id=clinic_id, **data)
        db.add(category)
        await db.flush()
        return category

    @staticmethod
    async def update_category(
        db: AsyncSession,
        category: TreatmentCategory,
        data: dict,
    ) -> TreatmentCategory:
        """Update a category."""
        for key, value in data.items():
            if value is not None:
                setattr(category, key, value)
        await db.flush()
        return category

    @staticmethod
    async def delete_category(
        db: AsyncSession,
        category: TreatmentCategory,
        soft: bool = True,
    ) -> None:
        """Delete a category (soft delete by default)."""
        if soft:
            category.is_active = False
            await db.flush()
        else:
            await db.delete(category)
            await db.flush()


class CatalogService:
    """Service for catalog item operations."""

    @staticmethod
    async def list_items(
        db: AsyncSession,
        clinic_id: UUID,
        page: int = 1,
        page_size: int = 20,
        category_id: UUID | None = None,
        is_active: bool | None = True,
        treatment_scope: str | None = None,
        has_odontogram_mapping: bool | None = None,
        search_query: str | None = None,
    ) -> tuple[list[TreatmentCatalogItem], int]:
        """List catalog items with filtering and pagination."""
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        # Base query with eager loading
        query = (
            select(TreatmentCatalogItem)
            .where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.deleted_at.is_(None),
            )
            .options(
                joinedload(TreatmentCatalogItem.category),
                joinedload(TreatmentCatalogItem.odontogram_mapping),
                joinedload(TreatmentCatalogItem.vat_type_rel),
            )
        )

        # Apply filters
        if is_active is not None:
            query = query.where(TreatmentCatalogItem.is_active == is_active)

        if category_id:
            query = query.where(TreatmentCatalogItem.category_id == category_id)

        if treatment_scope:
            query = query.where(TreatmentCatalogItem.treatment_scope == treatment_scope)

        if has_odontogram_mapping is not None:
            if has_odontogram_mapping:
                query = query.where(TreatmentCatalogItem.odontogram_mapping.has())
            else:
                query = query.where(~TreatmentCatalogItem.odontogram_mapping.has())

        if search_query:
            # Search in internal_code and names (JSONB)
            from sqlalchemy.dialects.postgresql import TEXT

            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    TreatmentCatalogItem.internal_code.ilike(search_pattern),
                    # Cast JSONB to text for searching
                    func.cast(TreatmentCatalogItem.names, TEXT).ilike(search_pattern),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Apply pagination and ordering
        query = (
            query.order_by(
                TreatmentCatalogItem.category_id,
                TreatmentCatalogItem.internal_code,
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(query)
        items = result.unique().scalars().all()

        return list(items), total

    @staticmethod
    async def get_item(
        db: AsyncSession,
        clinic_id: UUID,
        item_id: UUID,
    ) -> TreatmentCatalogItem | None:
        """Get a catalog item by ID with related data."""
        result = await db.execute(
            select(TreatmentCatalogItem)
            .where(
                TreatmentCatalogItem.id == item_id,
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.deleted_at.is_(None),
            )
            .options(
                joinedload(TreatmentCatalogItem.category),
                joinedload(TreatmentCatalogItem.odontogram_mapping),
                joinedload(TreatmentCatalogItem.vat_type_rel),
            )
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_item_by_code(
        db: AsyncSession,
        clinic_id: UUID,
        internal_code: str,
    ) -> TreatmentCatalogItem | None:
        """Get a catalog item by its internal code."""
        result = await db.execute(
            select(TreatmentCatalogItem)
            .where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.internal_code == internal_code,
                TreatmentCatalogItem.deleted_at.is_(None),
            )
            .options(
                joinedload(TreatmentCatalogItem.category),
                joinedload(TreatmentCatalogItem.odontogram_mapping),
                joinedload(TreatmentCatalogItem.vat_type_rel),
            )
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def create_item(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> TreatmentCatalogItem:
        """Create a new catalog item."""
        # Extract odontogram mapping if present
        odontogram_data = data.pop("odontogram_mapping", None)

        # If no vat_type_id provided, use clinic default
        if not data.get("vat_type_id"):
            default_vat = await VatTypeService.get_default_vat_type(db, clinic_id)
            if default_vat:
                data["vat_type_id"] = default_vat.id

        item = TreatmentCatalogItem(clinic_id=clinic_id, **data)
        db.add(item)
        await db.flush()

        # Create odontogram mapping if provided
        if odontogram_data:
            mapping = TreatmentOdontogramMapping(
                clinic_id=clinic_id,
                catalog_item_id=item.id,
                **odontogram_data,
            )
            db.add(mapping)
            await db.flush()

        return item

    @staticmethod
    async def update_item(
        db: AsyncSession,
        clinic_id: UUID,
        item: TreatmentCatalogItem,
        data: dict,
    ) -> TreatmentCatalogItem:
        """Update a catalog item."""
        # Handle odontogram mapping separately
        odontogram_data = data.pop("odontogram_mapping", None)

        # Update main item fields
        for key, value in data.items():
            if value is not None:
                setattr(item, key, value)

        # Update or create odontogram mapping
        if odontogram_data:
            if item.odontogram_mapping:
                for key, value in odontogram_data.items():
                    setattr(item.odontogram_mapping, key, value)
            else:
                mapping = TreatmentOdontogramMapping(
                    clinic_id=clinic_id,
                    catalog_item_id=item.id,
                    **odontogram_data,
                )
                db.add(mapping)

        await db.flush()
        return item

    @staticmethod
    async def delete_item(
        db: AsyncSession,
        item: TreatmentCatalogItem,
        hard: bool = False,
    ) -> None:
        """Delete a catalog item (soft delete by default)."""
        if hard:
            await db.delete(item)
        else:
            from datetime import UTC, datetime

            item.deleted_at = datetime.now(UTC)
            item.is_active = False

        await db.flush()

    @staticmethod
    async def search_items(
        db: AsyncSession,
        clinic_id: UUID,
        query: str,
        limit: int = 20,
    ) -> list[TreatmentCatalogItem]:
        """Search catalog items by name or code."""
        from sqlalchemy.dialects.postgresql import TEXT

        search_pattern = f"%{query}%"

        result = await db.execute(
            select(TreatmentCatalogItem)
            .where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.is_active.is_(True),
                TreatmentCatalogItem.deleted_at.is_(None),
                or_(
                    TreatmentCatalogItem.internal_code.ilike(search_pattern),
                    # Cast JSONB to text for searching
                    func.cast(TreatmentCatalogItem.names, TEXT).ilike(search_pattern),
                ),
            )
            .options(
                joinedload(TreatmentCatalogItem.category),
                joinedload(TreatmentCatalogItem.vat_type_rel),
            )
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    @staticmethod
    async def get_popular_items(
        db: AsyncSession,
        clinic_id: UUID,
        limit: int = 8,
    ) -> list[TreatmentCatalogItem]:
        """Get popular catalog items by usage count in budgets and invoices."""
        # Count usage in budget_items
        budget_count = (
            select(
                BudgetItem.catalog_item_id,
                func.count(BudgetItem.id).label("budget_count"),
            )
            .where(BudgetItem.clinic_id == clinic_id)
            .group_by(BudgetItem.catalog_item_id)
            .subquery()
        )

        # Count usage in invoice_items
        invoice_count = (
            select(
                InvoiceItem.catalog_item_id,
                func.count(InvoiceItem.id).label("invoice_count"),
            )
            .where(
                InvoiceItem.clinic_id == clinic_id,
                InvoiceItem.catalog_item_id.isnot(None),
            )
            .group_by(InvoiceItem.catalog_item_id)
            .subquery()
        )

        # Join and sum counts
        query = (
            select(TreatmentCatalogItem)
            .outerjoin(budget_count, TreatmentCatalogItem.id == budget_count.c.catalog_item_id)
            .outerjoin(invoice_count, TreatmentCatalogItem.id == invoice_count.c.catalog_item_id)
            .where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.is_active.is_(True),
                TreatmentCatalogItem.deleted_at.is_(None),
            )
            .options(
                joinedload(TreatmentCatalogItem.category),
                joinedload(TreatmentCatalogItem.vat_type_rel),
            )
            .order_by(
                (
                    func.coalesce(budget_count.c.budget_count, 0)
                    + func.coalesce(invoice_count.c.invoice_count, 0)
                ).desc(),
                TreatmentCatalogItem.internal_code,
            )
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.unique().scalars().all())


class OdontogramCatalogService:
    """Service for odontogram-catalog integration."""

    @staticmethod
    async def get_odontogram_treatments(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[dict]:
        """Get catalog items with odontogram mappings for the TreatmentBar.

        Returns a list of treatments grouped by clinical category.
        """
        result = await db.execute(
            select(TreatmentCatalogItem)
            .where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.is_active.is_(True),
                TreatmentCatalogItem.deleted_at.is_(None),
            )
            .options(
                joinedload(TreatmentCatalogItem.category),
                joinedload(TreatmentCatalogItem.odontogram_mapping),
            )
        )

        items = result.unique().scalars().all()

        # Filter items with odontogram mapping and transform
        treatments = []
        for item in items:
            if item.odontogram_mapping:
                treatments.append(
                    {
                        "id": str(item.id),
                        "internal_code": item.internal_code,
                        "names": item.names,
                        "default_price": float(item.default_price) if item.default_price else None,
                        "treatment_scope": item.treatment_scope,
                        "requires_surfaces": item.requires_surfaces,
                        "is_diagnostic": item.is_diagnostic,
                        "pricing_strategy": item.pricing_strategy or "flat",
                        "pricing_config": item.pricing_config,
                        "surface_prices": item.surface_prices,
                        "odontogram_treatment_type": item.odontogram_mapping.odontogram_treatment_type,
                        "visualization_rules": item.odontogram_mapping.visualization_rules,
                        "visualization_config": item.odontogram_mapping.visualization_config,
                        "clinical_category": item.odontogram_mapping.clinical_category,
                        "category_key": item.category.key if item.category else None,
                        "category_names": item.category.names if item.category else {},
                    }
                )

        return treatments

    @staticmethod
    async def get_treatments_by_category(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> dict[str, list[dict]]:
        """Get odontogram treatments grouped by clinical category."""
        treatments = await OdontogramCatalogService.get_odontogram_treatments(db, clinic_id)

        # Group by clinical category
        grouped: dict[str, list[dict]] = {}
        for treatment in treatments:
            category = treatment["clinical_category"]
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(treatment)

        return grouped
