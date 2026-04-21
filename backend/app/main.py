import asyncio
import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from .jobs.scheduler import start_scheduler, stop_scheduler
from .routes import admin, auth, preferences, articles, test_email, analytics, feed, sources, admin_panel, password_reset, analyze, favorites, oauth, challenge, newsletter_links
import logging
from .config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _run_initial_population_in_background():
    """
    Run first-time seed/scrape work without blocking app startup.
    This allows health checks to succeed while heavy initialization runs.
    """
    try:
        from .seed_data import seed_database, run_initial_scraping
        from sqlmodel import Session, select
        from .models import Article
        from .database import engine

        def _populate_if_needed():
            with Session(engine) as session:
                existing_articles = session.exec(select(Article)).first()
                if not existing_articles:
                    logger.info("No articles found - running initial data population in background...")
                    seed_database()  # Ensure sources/topics/frameworks exist
                    run_initial_scraping()  # Scrape initial articles
                    logger.info("Initial data population complete")
                else:
                    logger.info("Articles exist - skipping initial scraping")

        await asyncio.to_thread(_populate_if_needed)
    except Exception as e:
        logger.warning(f"Could not run initial scraping: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    logger.info("Starting Pulse News Aggregator...")
    create_db_and_tables()

    # Run seed/scrape in background so startup health checks are not blocked.
    app.state.initial_population_task = asyncio.create_task(
        _run_initial_population_in_background()
    )

    # Start background job scheduler
    start_scheduler()

    yield

    # Shutdown: Stop scheduler gracefully
    logger.info("Shutting down...")
    population_task = getattr(app.state, "initial_population_task", None)
    if population_task and not population_task.done():
        population_task.cancel()
    stop_scheduler()


app = FastAPI(
    title="Pulse News Aggregator",
    description="AI-powered news aggregation with ethical framework mapping",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for frontend
frontend_url = settings.frontend_url
frontend_custom_url = settings.frontend_custom_url

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, frontend_custom_url],  # Local dev
    allow_origin_regex=r"^https:\/\/[\w\-]+\.onrender\.com$",  # Any *.onrender.com
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router)
app.include_router(admin_panel.router)  # Admin panel (requires admin token + JWT)
app.include_router(auth.router)
app.include_router(oauth.router)  # OAuth authentication endpoints
app.include_router(password_reset.router)  # Password reset endpoints
app.include_router(preferences.router)
app.include_router(articles.router)  # Merged: includes both /analyzed and /{article_id}
app.include_router(test_email.router)
app.include_router(analytics.router)
app.include_router(feed.router)
app.include_router(sources.router)
app.include_router(analyze.router)  # Article URL analysis
app.include_router(favorites.router)  # Favorites/bookmarking
app.include_router(challenge.router)  # Weekly challenge system
app.include_router(newsletter_links.router)  # Signed newsletter unsubscribe / preferences links


@app.get("/")
def root():
    return {
        "name": "Pulse News Aggregator API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

# Expose port for render
if __name__ == "__main__":
    port = os.getenv(PORT, default=8000)
    uvicorn.run(app, host="0.0.0.0", port=port) # Example port 10000
