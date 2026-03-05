"""FastAPI entry point — wraps existing services layer as REST API."""

import sys
from pathlib import Path

# Add project root to sys.path so we can import services/database
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.connection import init_db
from backend.routers import crm, projects, network

app = FastAPI(title="Project Nexus API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crm.router, prefix="/api/crm", tags=["CRM"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(network.router, prefix="/api/network", tags=["Network"])


@app.on_event("startup")
def startup():
    try:
        init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("DB init skipped: %s", e)


@app.get("/api/health")
def health():
    return {"status": "ok"}
