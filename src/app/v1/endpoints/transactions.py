import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.account_model import Account
from app.models.transactions_model import (
    Transaction,
    TransactionCategory,
    TransactionStatus,
)
from app.models.users_model import User
from app.services.pdf_service import PDFReceiptService
from app.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_transactions(
    account_id: uuid.UUID | None = None,
    category: TransactionCategory | None = None,
    transaction_status: TransactionStatus | None = Query(default=None, alias="status"),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch user accounts to scope security permissions
    user_account_ids = (
        (await db.execute(select(Account.id).where(Account.user_id == current_user.id)))
        .scalars()
        .all()
    )

    if not user_account_ids:
        return {"items": [], "total": 0, "page": page, "limit": limit}

    query = select(Transaction).where(
        or_(
            Transaction.source_account_id.in_(user_account_ids),
            Transaction.destination_account_id.in_(user_account_ids),
        )
    )

    if account_id:
        if account_id not in user_account_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for account transactions.",
            )
        query = query.where(
            or_(
                Transaction.source_account_id == account_id,
                Transaction.destination_account_id == account_id,
            )
        )

    if category:
        query = query.where(Transaction.category == category)

    if transaction_status:
        query = query.where(Transaction.status == transaction_status)

    if search:
        query = query.where(
            or_(
                Transaction.reference_number.ilike(f"%{search}%"),
                Transaction.description.ilike(f"%{search}%"),
            )
        )

    # Offset pagination
    offset = (page - 1) * limit
    paginated_query = (
        query.order_by(desc(Transaction.created_at)).offset(offset).limit(limit)
    )

    result = await db.execute(paginated_query)
    transactions = result.scalars().all()

    return {"items": transactions, "page": page, "limit": limit}


@router.get("/{transaction_id}/receipt/download")
async def download_receipt(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    txn = (
        await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    ).scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    # Secure verification
    user_account_ids = (
        (await db.execute(select(Account.id).where(Account.user_id == current_user.id)))
        .scalars()
        .all()
    )
    if (
        txn.source_account_id not in user_account_ids
        and txn.destination_account_id not in user_account_ids
    ):
        raise HTTPException(status_code=403, detail="Unauthorized.")

    source_acc = (
        (
            await db.execute(select(Account).where(Account.id == txn.source_account_id))
        ).scalar_one_or_none()
        if txn.source_account_id
        else None
    )
    dest_acc = (
        (
            await db.execute(
                select(Account).where(Account.id == txn.destination_account_id)
            )
        ).scalar_one_or_none()
        if txn.destination_account_id
        else None
    )

    pdf_buffer = PDFReceiptService.generate_receipt_pdf(
        transaction=txn,
        source_acc_num=source_acc.account_number if source_acc else "External",
        dest_acc_num=dest_acc.account_number if dest_acc else "External",
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=receipt_{txn.reference_number}.pdf"
        },
    )
