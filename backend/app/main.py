from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.auth_routes import router as auth_router
from app.api.admin_routes import router as admin_router
from app.api.notification_routes import router as notif_router
from app.api.admin_config_routes import router as admin_config_router
from app.api.export_routes import router as export_router
from app.api.kg_routes import router as kg_router
from app.api.problem_profile_routes import router as problem_profile_router
from app.api.flow_routes import router as flow_router
from app.database import engine, Base
from app import models
from app.logger import logger
from app.scheduler import start_scheduler, stop_scheduler
from app.middleware import ActivityLogMiddleware

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Opportunity Discovery Platform")
    start_scheduler()
    yield
    logger.info("Shutting down — stopping scheduler")
    stop_scheduler()


app = FastAPI(
    title="AI Opportunity Discovery & Innovation Intelligence Platform",
    description="Multi-source AI platform for discovering startup and research opportunities",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(ActivityLogMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(admin_config_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(notif_router, prefix="/api")
app.include_router(kg_router, prefix="/api")
app.include_router(problem_profile_router, prefix="/api")
app.include_router(flow_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "AI Opportunity Discovery Platform API",
        "docs": "/docs",
        "health": "/api/health",
    }
