"""Budget workflow service - state machine and status transitions."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Budget, BudgetItem, BudgetSignature
from .service import BudgetHistoryService, BudgetItemService

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["sent", "cancelled"],
    "sent": ["partially_accepted", "accepted", "rejected", "expired", "cancelled"],
    "partially_accepted": ["accepted", "in_progress", "rejected", "cancelled"],
    "accepted": ["in_progress", "cancelled"],
    "in_progress": ["completed", "cancelled"],
    "completed": ["invoiced"],
    "invoiced": [],  # Terminal state
    "rejected": [],  # Terminal state
    "expired": [],  # Terminal state
    "cancelled": [],  # Terminal state
}


class BudgetWorkflowError(Exception):
    """Exception for workflow validation errors."""

    pass


class BudgetWorkflowService:
    """Service for budget status transitions and workflow operations."""

    @staticmethod
    def can_transition(current_status: str, new_status: str) -> bool:
        """Check if a status transition is valid."""
        allowed = VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed

    @staticmethod
    async def send_budget(
        db: AsyncSession,
        budget: Budget,
        sent_by: UUID,
        send_email: bool = False,
        custom_message: str | None = None,
    ) -> Budget:
        """Mark budget as sent to patient."""
        if not BudgetWorkflowService.can_transition(budget.status, "sent"):
            raise BudgetWorkflowError(f"Cannot send budget from status '{budget.status}'")

        # Check budget has items
        if not budget.items:
            raise BudgetWorkflowError("Cannot send empty budget")

        previous_status = budget.status
        budget.status = "sent"

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="status_changed",
            changed_by=sent_by,
            previous_state={"status": previous_status},
            new_state={"status": "sent", "send_email": send_email},
        )

        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="sent",
            changed_by=sent_by,
            new_state={
                "sent_at": datetime.now(UTC).isoformat(),
                "send_email": send_email,
                "custom_message": custom_message,
            },
        )

        await db.flush()

        # TODO: Publish event for notifications module
        # event_bus.publish("budget.sent", {...})

        return budget

    @staticmethod
    async def accept_budget(
        db: AsyncSession,
        budget: Budget,
        signature_data: dict,
        accepted_by: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Budget:
        """Accept entire budget with signature."""
        if not BudgetWorkflowService.can_transition(budget.status, "accepted"):
            raise BudgetWorkflowError(f"Cannot accept budget from status '{budget.status}'")

        previous_status = budget.status
        budget.status = "accepted"

        # Accept all pending items
        for item in budget.items:
            if item.item_status == "pending":
                await BudgetItemService.accept_item(db, item)

        # Create signature record
        signature = BudgetSignature(
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            signature_type="full_acceptance",
            signed_items=[str(item.id) for item in budget.items],
            signed_by_name=signature_data["signed_by_name"],
            signed_by_email=signature_data.get("signed_by_email"),
            relationship_to_patient=signature_data.get("relationship_to_patient", "patient"),
            signature_method=signature_data.get("signature_method", "click_accept"),
            signature_data=signature_data.get("signature_data"),
            ip_address=ip_address,
            user_agent=user_agent,
            signed_at=datetime.now(UTC),
        )
        db.add(signature)

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="status_changed",
            changed_by=accepted_by,
            previous_state={"status": previous_status},
            new_state={"status": "accepted"},
        )

        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="signed",
            changed_by=accepted_by,
            new_state={
                "signature_type": "full_acceptance",
                "signed_by": signature_data["signed_by_name"],
            },
        )

        await db.flush()

        # TODO: Publish event
        # event_bus.publish("budget.accepted", {...})

        return budget

    @staticmethod
    async def accept_items(
        db: AsyncSession,
        budget: Budget,
        item_ids: list[UUID],
        signature_data: dict,
        accepted_by: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Budget:
        """Accept specific items from a budget (partial acceptance)."""
        valid_from_statuses = ["sent", "partially_accepted"]
        if budget.status not in valid_from_statuses:
            raise BudgetWorkflowError(f"Cannot accept items from status '{budget.status}'")

        # Validate items belong to budget and are pending
        valid_items = [
            item for item in budget.items if item.id in item_ids and item.item_status == "pending"
        ]

        if not valid_items:
            raise BudgetWorkflowError("No valid pending items to accept")

        # Accept selected items
        for item in valid_items:
            await BudgetItemService.accept_item(db, item)

        # Create signature record
        signature = BudgetSignature(
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            signature_type="partial_acceptance",
            signed_items=[str(item_id) for item_id in item_ids],
            signed_by_name=signature_data["signed_by_name"],
            signed_by_email=signature_data.get("signed_by_email"),
            relationship_to_patient=signature_data.get("relationship_to_patient", "patient"),
            signature_method=signature_data.get("signature_method", "click_accept"),
            signature_data=signature_data.get("signature_data"),
            ip_address=ip_address,
            user_agent=user_agent,
            signed_at=datetime.now(UTC),
        )
        db.add(signature)

        # Check if all items are now accepted
        pending_items = [item for item in budget.items if item.item_status == "pending"]

        previous_status = budget.status
        if not pending_items:
            budget.status = "accepted"
        else:
            budget.status = "partially_accepted"

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="status_changed",
            changed_by=accepted_by,
            previous_state={"status": previous_status},
            new_state={"status": budget.status},
        )

        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="signed",
            changed_by=accepted_by,
            new_state={
                "signature_type": "partial_acceptance",
                "signed_by": signature_data["signed_by_name"],
                "items_accepted": [str(item_id) for item_id in item_ids],
            },
        )

        await db.flush()

        # TODO: Publish event
        # event_bus.publish("budget.partially_accepted", {...})

        return budget

    @staticmethod
    async def reject_budget(
        db: AsyncSession,
        budget: Budget,
        rejected_by: UUID,
        reason: str | None = None,
        signature_data: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Budget:
        """Reject a budget."""
        if not BudgetWorkflowService.can_transition(budget.status, "rejected"):
            raise BudgetWorkflowError(f"Cannot reject budget from status '{budget.status}'")

        previous_status = budget.status
        budget.status = "rejected"

        # Reject all pending items
        for item in budget.items:
            if item.item_status == "pending":
                await BudgetItemService.reject_item(db, item)

        # Create signature record if provided
        if signature_data:
            signature = BudgetSignature(
                clinic_id=budget.clinic_id,
                budget_id=budget.id,
                signature_type="rejection",
                signed_by_name=signature_data["signed_by_name"],
                signed_by_email=signature_data.get("signed_by_email"),
                relationship_to_patient=signature_data.get("relationship_to_patient", "patient"),
                signature_method=signature_data.get("signature_method", "click_accept"),
                signature_data=signature_data.get("signature_data"),
                ip_address=ip_address,
                user_agent=user_agent,
                signed_at=datetime.now(UTC),
            )
            db.add(signature)

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="status_changed",
            changed_by=rejected_by,
            previous_state={"status": previous_status},
            new_state={"status": "rejected", "reason": reason},
        )

        await db.flush()

        # TODO: Publish event
        # event_bus.publish("budget.rejected", {...})

        return budget

    @staticmethod
    async def cancel_budget(
        db: AsyncSession,
        budget: Budget,
        cancelled_by: UUID,
        reason: str | None = None,
    ) -> Budget:
        """Cancel a budget."""
        if not BudgetWorkflowService.can_transition(budget.status, "cancelled"):
            raise BudgetWorkflowError(f"Cannot cancel budget from status '{budget.status}'")

        previous_status = budget.status
        budget.status = "cancelled"

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="status_changed",
            changed_by=cancelled_by,
            previous_state={"status": previous_status},
            new_state={"status": "cancelled", "reason": reason},
        )

        await db.flush()

        # TODO: Publish event
        # event_bus.publish("budget.cancelled", {...})

        return budget

    @staticmethod
    async def start_budget(
        db: AsyncSession,
        budget: Budget,
        started_by: UUID,
    ) -> Budget:
        """Mark budget as in progress (treatments started)."""
        if not BudgetWorkflowService.can_transition(budget.status, "in_progress"):
            raise BudgetWorkflowError(f"Cannot start budget from status '{budget.status}'")

        previous_status = budget.status
        budget.status = "in_progress"

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="status_changed",
            changed_by=started_by,
            previous_state={"status": previous_status},
            new_state={"status": "in_progress"},
        )

        await db.flush()

        return budget

    @staticmethod
    async def complete_budget(
        db: AsyncSession,
        budget: Budget,
        completed_by: UUID,
    ) -> Budget:
        """Mark budget as completed (all treatments done)."""
        if not BudgetWorkflowService.can_transition(budget.status, "completed"):
            raise BudgetWorkflowError(f"Cannot complete budget from status '{budget.status}'")

        # Check if all accepted items are completed
        accepted_items = [
            item for item in budget.items if item.item_status in ["accepted", "in_progress"]
        ]
        incomplete_items = [item for item in accepted_items if item.item_status != "completed"]

        if incomplete_items:
            raise BudgetWorkflowError(
                f"{len(incomplete_items)} accepted items are not yet completed"
            )

        previous_status = budget.status
        budget.status = "completed"

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="status_changed",
            changed_by=completed_by,
            previous_state={"status": previous_status},
            new_state={"status": "completed"},
        )

        await db.flush()

        # TODO: Publish event
        # event_bus.publish("budget.completed", {...})

        return budget

    @staticmethod
    async def start_item_treatment(
        db: AsyncSession,
        budget: Budget,
        item: BudgetItem,
        started_by: UUID,
    ) -> BudgetItem:
        """Start treatment for a specific item."""
        if item.item_status not in ["accepted"]:
            raise BudgetWorkflowError(
                f"Cannot start treatment for item with status '{item.item_status}'"
            )

        await BudgetItemService.start_treatment(db, item, started_by)

        # If budget was accepted, transition to in_progress
        if budget.status == "accepted":
            await BudgetWorkflowService.start_budget(db, budget, started_by)
        elif budget.status == "partially_accepted":
            budget.status = "in_progress"
            await db.flush()

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="item_treatment_started",
            changed_by=started_by,
            new_state={
                "item_id": str(item.id),
                "started_at": datetime.now(UTC).isoformat(),
            },
        )

        return item

    @staticmethod
    async def complete_item_treatment(
        db: AsyncSession,
        budget: Budget,
        item: BudgetItem,
        completed_by: UUID,
    ) -> BudgetItem:
        """Complete treatment for a specific item."""
        if item.item_status not in ["accepted", "in_progress"]:
            raise BudgetWorkflowError(
                f"Cannot complete treatment for item with status '{item.item_status}'"
            )

        await BudgetItemService.complete_treatment(db, item, completed_by)

        # Check if all accepted/in_progress items are now completed
        all_completed = all(
            i.item_status == "completed"
            for i in budget.items
            if i.item_status in ["accepted", "in_progress", "completed"]
        )

        # Add history
        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="item_treatment_completed",
            changed_by=completed_by,
            new_state={
                "item_id": str(item.id),
                "completed_at": datetime.now(UTC).isoformat(),
                "all_items_completed": all_completed,
            },
        )

        # TODO: Publish event
        # event_bus.publish("budget.item.treatment_completed", {...})

        return item

    @staticmethod
    async def check_expired_budgets(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[Budget]:
        """Check for and mark expired budgets.

        Should be called periodically (e.g., daily cron job).
        """
        from datetime import date

        from sqlalchemy import select

        today = date.today()

        # Find sent/partially_accepted budgets past their valid_until date
        result = await db.execute(
            select(Budget).where(
                Budget.clinic_id == clinic_id,
                Budget.status.in_(["sent", "partially_accepted"]),
                Budget.valid_until.isnot(None),
                Budget.valid_until < today,
                Budget.deleted_at.is_(None),
            )
        )

        expired_budgets = list(result.scalars().all())

        for budget in expired_budgets:
            previous_status = budget.status
            budget.status = "expired"

            # Add history (use system user ID or admin)
            await BudgetHistoryService.add_entry(
                db,
                clinic_id=budget.clinic_id,
                budget_id=budget.id,
                action="status_changed",
                changed_by=budget.created_by,  # Use creator as fallback
                previous_state={"status": previous_status},
                new_state={"status": "expired", "expired_at": today.isoformat()},
                notes="Automatically expired due to validity period",
            )

        await db.flush()

        return expired_budgets
