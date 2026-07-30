from fastapi import APIRouter

from .endpoints.accounts import router as accounts_router
from .endpoints.auth import router as auth_router
from .endpoints.notifications import router as notifications_router
from .endpoints.profile import router as profile_router
from .endpoints.transactions import router as transactions_router
from .endpoints.transfers import router as transfers_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
router.include_router(transfers_router, prefix="/transfers", tags=["Transfers"])
router.include_router(profile_router, prefix="/profile", tags=["Profile"])
router.include_router(
    transactions_router, prefix="/transactions", tags=["Transactions Ledger"]
)
router.include_router(
    notifications_router, prefix="/notifications", tags=["Notification Center"]
)
