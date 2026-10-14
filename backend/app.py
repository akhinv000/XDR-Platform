from fastapi import FastAPI

from database import engine
from models import Base

from routers.auth import router as auth_router
from routers.assets import router as asset_router
from routers.dashboard import router as dashboard_router
from routers.logs import router as logs_router
from fastapi.middleware.cors import CORSMiddleware
from routers.discovery import router as discovery_router
from routers.alerts import router as alert_router
from routers.analytics import router as analytics_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="XDR Platform",
    version="1.0.0",
    description="XDR Platform MVP"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:9000",
        "http://localhost:9000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routersdir services
app.include_router(auth_router)
app.include_router(asset_router)
app.include_router(dashboard_router)
app.include_router(logs_router)
app.include_router(discovery_router)
app.include_router(alert_router)
app.include_router(analytics_router)


@app.get("/")
def home():
    return {
        "application": "XDR Platform",
        "status": "Running"
    }