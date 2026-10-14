from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from database import engine
from models import Base
from routers.auth import router as auth_router
from routers.assets import router as asset_router
from routers.dashboard import router as dashboard_router
from routers.logs import router as logs_router
from routers.discovery import router as discovery_router
from routers.alerts import router as alert_router
from routers.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on application startup
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[Warning] Failed to connect/initialize database on startup: {e}")
    yield


app = FastAPI(
    title="XDR Platform",
    version="1.0.0",
    description="Enterprise Extended Detection and Response (XDR) Platform",
    lifespan=lifespan
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

# Register API Routers
app.include_router(auth_router)
app.include_router(asset_router)
app.include_router(dashboard_router)
app.include_router(logs_router)
app.include_router(discovery_router)
app.include_router(alert_router)
app.include_router(analytics_router)

# Mount Frontend static files
frontend_dir = Path(__file__).parent / "frontend"
if not frontend_dir.exists():
    frontend_dir = Path(__file__).parent.parent / "frontend"

if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


@app.get("/")
def home():
    if frontend_dir.exists():
        return RedirectResponse(url="/app/login.html")
    return {
        "application": "XDR Platform",
        "status": "Running",
        "version": "1.0.0"
    }