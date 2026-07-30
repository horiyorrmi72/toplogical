import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.transactions_model import TransactionCategory, TransactionStatus


class TransactionResponseSchema(BaseModel):
    id: uuid.UUID
    reference_number: str
    source_account_id: uuid.UUID | None = None
    destination_account_id: uuid.UUID | None = None
    amount: Decimal
    category: TransactionCategory
    status: TransactionStatus
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedTransactionResponseSchema(BaseModel):
    items: list[TransactionResponseSchema]
    page: int
    limit: int
