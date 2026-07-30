from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.v1.endpoints.auth import limiter

from .v1.router import router as v1_router

app = FastAPI(title="FinBank Digital Banking API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to the FinBank API"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "FinBank API Core"}
