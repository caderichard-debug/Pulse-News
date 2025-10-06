import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from .jobs.scheduler import start_scheduler, stop_scheduler
from .routes import admin, auth, preferences, articles, test_email, analytics, feed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    logger.info("Starting Pulse News Aggregator...")
    create_db_and_tables()

    # Start background job scheduler
    start_scheduler()

    yield

    # Shutdown: Stop scheduler gracefully
    logger.info("Shutting down...")
    stop_scheduler()


app = FastAPI(
    title="Pulse News Aggregator",
    description="AI-powered news aggregation with ethical framework mapping",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
            "http://localhost:3000", # Next.js dev server
            "https://pulse-news-ten.vercel.app/", # Next.js production server
        ],  
    allow_origin_regex = r"https://pulse-news-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(preferences.router)
app.include_router(articles.router)  # Merged: includes both /analyzed and /{article_id}
app.include_router(test_email.router)
app.include_router(analytics.router)
app.include_router(feed.router)

@app.get("/")
def root():
    return {
        "name": "Pulse News Aggregator API",
        "version": "0.1.0",
        "docs": "/docs"
    }

# This is important for Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)