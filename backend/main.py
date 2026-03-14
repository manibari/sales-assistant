"""FastAPI entry point — wraps existing services layer as REST API."""

import sys
from pathlib import Path

# Add project root to sys.path so we can import services/database
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from database.connection import init_db
from backend.routers import crm, projects, network
from backend.routers.nexus import (
    clients as nx_clients,
    partners as nx_partners,
    contacts as nx_contacts,
    intel as nx_intel,
    deals as nx_deals,
    calendar as nx_calendar,
    documents as nx_documents,
    tags as nx_tags,
    tbd as nx_tbd,
    search as nx_search,
    telegram as nx_telegram,
    subsidies as nx_subsidies,
)

app = FastAPI(title="Project Nexus API", version="0.2.0", redirect_slashes=False)


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """Internally add trailing slash so routes match without 307 redirect."""
    async def dispatch(self, request: Request, call_next):
        path = request.scope["path"]
        if path.startswith("/api/") and not path.endswith("/") and "." not in path.split("/")[-1]:
            request.scope["path"] = path + "/"
        return await call_next(request)


app.add_middleware(TrailingSlashMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3333",
        "http://localhost:8503",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3333",
        "https://sales.phyra.uk",
        "https://api.phyra.uk",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy SPMS routers
app.include_router(crm.router, prefix="/api/crm", tags=["CRM (Legacy)"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects (Legacy)"])
app.include_router(network.router, prefix="/api/network", tags=["Network (Legacy)"])

# Nexus Engine 1 routers
app.include_router(nx_clients.router, prefix="/api/nx/clients", tags=["Clients"])
app.include_router(nx_partners.router, prefix="/api/nx/partners", tags=["Partners"])
app.include_router(nx_contacts.router, prefix="/api/nx/contacts", tags=["Contacts"])
app.include_router(nx_intel.router, prefix="/api/nx/intel", tags=["Intel"])
app.include_router(nx_deals.router, prefix="/api/nx/deals", tags=["Deals"])
app.include_router(nx_calendar.router, prefix="/api/nx/calendar", tags=["Calendar"])
app.include_router(nx_documents.router, prefix="/api/nx/documents", tags=["Documents"])
app.include_router(nx_tags.router, prefix="/api/nx/tags", tags=["Tags"])
app.include_router(nx_tbd.router, prefix="/api/nx/tbd", tags=["TBD"])
app.include_router(nx_search.router, prefix="/api/nx/search", tags=["Search"])
app.include_router(nx_telegram.router, prefix="/api/nx/telegram", tags=["Telegram"])
app.include_router(nx_subsidies.router, prefix="/api/nx/subsidies", tags=["Subsidies"])


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
