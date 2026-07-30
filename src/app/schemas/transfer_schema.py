import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class TransferRequestSchema(BaseModel):
    source_account_id: uuid.UUID
    destination_account_id: uuid.UUID
    amount: Decimal = Field(
        ..., gt=Decimal("0.00"), description="Transfer amount must be greater than 0"
    )
    description: str | None = Field(default=None, max_length=255)


class TransferResponseSchema(BaseModel):
    message: str
    reference_number: str
    status: str
    amount: Decimal
