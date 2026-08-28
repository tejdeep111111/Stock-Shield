from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.dashboard import router as dashboard_router
from .api.disruptions import router as disruptions_router
from .api.products import router as products_router
from .api.recovery import router as recovery_router
from .api.suppliers import router as suppliers_router
from .database import Base, SessionLocal, engine
from .seed import seed_data

app = FastAPI(title="StockShield API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(products_router)
app.include_router(suppliers_router)
app.include_router(disruptions_router)
app.include_router(recovery_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
