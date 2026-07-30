import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer

from app.models.account_model import AccountType


class AccountCreateSchema(BaseModel):
    account_type: AccountType
    initial_deposit: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))


class AccountResponseSchema(BaseModel):
    id: uuid.UUID
    account_number: str
    account_type: AccountType
    balance: Decimal
    credit_limit: Decimal

    @field_serializer("account_number")
    def mask_account_number(self, account_number: str, _info) -> str:
        if len(account_number) > 8:
            return account_number
        return account_number[:4] + "****" + account_number[-4:]

    class Config:
        from_attributes = True
