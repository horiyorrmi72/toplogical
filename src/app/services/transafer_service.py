import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_model import Account, AccountType
from app.models.transactions_model import (
    Transaction,
    TransactionCategory,
    TransactionStatus,
)
from app.services.notifications_service import NotificationService


class TransferService:
    @staticmethod
    async def execute_transfer(
        db: AsyncSession,
        user_id: uuid.UUID,
        source_account_id: uuid.UUID,
        destination_account_id: uuid.UUID,
        amount: Decimal,
        description: str | None = None,
    ) -> Transaction:
        if amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be positive.",
            )

        if source_account_id == destination_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer to the same account.",
            )

        # Prevent deadlocks by locking accounts in fixed order
        first_id, second_id = sorted([source_account_id, destination_account_id])

        # Fetch accounts with row-level locks
        acct1 = select(Account).where(Account.id == first_id).with_for_update()
        acct2 = select(Account).where(Account.id == second_id).with_for_update()

        res1 = await db.execute(acct1)
        res2 = await db.execute(acct2)

        acc1res = res1.scalar_one_or_none()
        acc2res = res2.scalar_one_or_none()

        accounts_map = {acc.id: acc for acc in [acc1res, acc2res] if acc}

        source_acc = accounts_map.get(source_account_id)
        dest_acc = accounts_map.get(destination_account_id)

        if not source_acc or not dest_acc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both accounts not found.",
            )

        #  ownership of source account
        if source_acc.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to source account.",
            )

        # funds availability
        if source_acc.account_type == AccountType.CREDIT_CARD:
            available = source_acc.credit_limit - source_acc.balance
            if available < amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Credit limit exceeded.",
                )
            source_acc.balance += amount  #card usage increases balance (debt)
        else:
            if source_acc.balance < amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient funds.",
                )
            source_acc.balance -= amount

        # we apply creit to the destiation
        if dest_acc.account_type == AccountType.CREDIT_CARD:
            dest_acc.balance -= amount
        else:
            dest_acc.balance += amount

        ref_no = f"TXN-{uuid.uuid4().hex[:10].upper()}"

        # if it is an external transfer, we categorize it as a payment; otherwise, it's a transfer
        is_external = source_acc.user_id != dest_acc.user_id
        category = TransactionCategory.TRANSFER if not is_external else TransactionCategory.PAYMENT

        transaction = Transaction(
            reference_number=ref_no,
            source_account_id=source_acc.id,
            destination_account_id=dest_acc.id,
            amount=amount,
            category=category,
            status=TransactionStatus.COMPLETED,
            description=description or ("Peer-to-Peer Transfer" if is_external else "Internal Transfer"),
        )

        db.add(transaction)

        # notification
        await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="Transfer Successful",
            message=f"Sent ${amount:,.2f} from your {source_acc.account_type.value} ending in {source_acc.account_number[-4:]}."
        )

        if is_external:
            await NotificationService.create_notification(
                db=db,
                user_id=dest_acc.user_id,
                title="Transfer Received",
                message=f"Received ${amount:,.2f} from your {source_acc.account_type.value} ending in {source_acc.account_number[-4:]}.",
            )

        await db.commit()
        await db.refresh(transaction)
        return transaction
