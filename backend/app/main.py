from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="News Aggregator MVP")

app.include_router(router)

