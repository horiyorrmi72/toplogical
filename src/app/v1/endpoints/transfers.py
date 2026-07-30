from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.idempotency import verify_idempotency_key
from app.db.session import get_db
from app.models.users_model import User
from app.schemas.transfer_schema import TransferRequestSchema
from app.services.transafer_service import TransferService
from app.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.post("/", status_code=status.HTTP_200_OK)
async def transfer_funds(
    payload: TransferRequestSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Depends(verify_idempotency_key),
):
    transaction = await TransferService.execute_transfer(
        db=db,
        user_id=current_user.id,
        source_account_id=payload.source_account_id,
        destination_account_id=payload.destination_account_id,
        amount=payload.amount,
        description=payload.description,
    )
    return {
        "message": "Transfer executed successfully",
        "reference_number": transaction.reference_number,
        "status": transaction.status,
        "amount": transaction.amount,
    }
