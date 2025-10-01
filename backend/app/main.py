from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes import router
from app.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    create_db_and_tables()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Pulse News Aggregator",
    description="AI-powered news aggregation with ethical framework mapping",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(router)

