"""Budget workflow service - state machine and status transitions."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import EventType, event_bus

from .models import Budget, BudgetSignature
from .service import BudgetHistoryService

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["sent", "accepted", "rejected", "cancelled"],
    "sent": ["accepted", "rejected", "expired", "cancelled"],
    "accepted": ["completed", "cancelled"],
    "completed": [],  # Terminal state
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
        send_method: str = "manual",  # "manual" or "email"
        recipient_email: str | None = None,
        custom_message: str | None = None,
    ) -> Budget:
        """Mark budget as sent to patient.

        Args:
            db: Database session.
            budget: Budget to send.
            sent_by: User ID who triggered the send.
            send_method: How it was sent ("manual" for printed/handed, "email" for email).
            recipient_email: Email address if sent by email.
        """
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
            new_state={"status": "sent"},
        )

        await BudgetHistoryService.add_entry(
            db,
            clinic_id=budget.clinic_id,
            budget_id=budget.id,
            action="sent",
            changed_by=sent_by,
            new_state={
                "sent_at": datetime.now(UTC).isoformat(),
                "send_method": send_method,
                "recipient_email": recipient_email,
            },
        )

        await db.flush()

        # Publish event for notifications module
        event_bus.publish(
            EventType.BUDGET_SENT,
            {
                "clinic_id": str(budget.clinic_id),
                "budget_id": str(budget.id),
                "patient_id": str(budget.patient_id),
                "send_method": send_method,
                "recipient_email": recipient_email,
                "custom_message": custom_message,
            },
        )

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
        """Accept budget with signature.

        Budget transitions directly from draft to accepted.
        """
        if not BudgetWorkflowService.can_transition(budget.status, "accepted"):
            raise BudgetWorkflowError(f"Cannot accept budget from status '{budget.status}'")

        # Check budget has items
        if not budget.items:
            raise BudgetWorkflowError("Cannot accept empty budget")

        previous_status = budget.status
        budget.status = "accepted"

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
        """Reject a budget.

        Budget transitions to rejected - a terminal state.
        """
        if not BudgetWorkflowService.can_transition(budget.status, "rejected"):
            raise BudgetWorkflowError(f"Cannot reject budget from status '{budget.status}'")

        previous_status = budget.status
        budget.status = "rejected"

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

        return budget

    @staticmethod
    async def complete_budget(
        db: AsyncSession,
        budget: Budget,
        completed_by: UUID,
    ) -> Budget:
        """Mark budget as completed (all work done)."""
        if not BudgetWorkflowService.can_transition(budget.status, "completed"):
            raise BudgetWorkflowError(f"Cannot complete budget from status '{budget.status}'")

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

        return budget

    @staticmethod
    async def check_expired_budgets(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[Budget]:
        """Check for and mark expired budgets.

        Should be called periodically (e.g., daily cron job).
        Draft and sent budgets can expire (accepted budgets don't expire).
        """
        from datetime import date

        from sqlalchemy import select

        today = date.today()

        # Find draft or sent budgets past their valid_until date
        result = await db.execute(
            select(Budget).where(
                Budget.clinic_id == clinic_id,
                Budget.status.in_(["draft", "sent"]),
                Budget.valid_until.isnot(None),
                Budget.valid_until < today,
                Budget.deleted_at.is_(None),
            )
        )

        expired_budgets = list(result.scalars().all())

        for budget in expired_budgets:
            previous_status = budget.status
            budget.status = "expired"

            # Add history (use creator as fallback)
            await BudgetHistoryService.add_entry(
                db,
                clinic_id=budget.clinic_id,
                budget_id=budget.id,
                action="status_changed",
                changed_by=budget.created_by,
                previous_state={"status": previous_status},
                new_state={"status": "expired", "expired_at": today.isoformat()},
                notes="Automatically expired due to validity period",
            )

        await db.flush()

        return expired_budgets
