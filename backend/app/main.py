import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config, models

from .database import Base, engine, SessionLocal
from .seed import seed_if_empty
from .routers import inventory, recipes, recommendations, interactions, preferences, receipts

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    seed_if_empty(db)

app = FastAPI(title="FoodWise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory.router)
app.include_router(recipes.router)
app.include_router(recommendations.router)
app.include_router(interactions.router)
app.include_router(preferences.router)
app.include_router(receipts.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
