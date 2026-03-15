"""FastAPI entry point — wraps existing services layer as REST API."""

import logging
import sys
import threading
import time
from pathlib import Path

# Add project root to sys.path so we can import services/database
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    settings as nx_settings,
    outlook as nx_outlook,
)

app = FastAPI(title="Project Nexus API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3002",
        "http://localhost:3333",
        "http://127.0.0.1:3002",
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
app.include_router(nx_settings.router, prefix="/api/nx/settings", tags=["Settings"])
app.include_router(nx_outlook.router, prefix="/api/nx/outlook", tags=["Outlook"])


_logger = logging.getLogger(__name__)


def _knowledge_worker_loop():
    """Background thread: poll knowledge_parse_queue every 10s."""
    from services.nexus.knowledge import (
        get_next_parse_task,
        update_parse_status,
        update_file_parse_status,
        delete_knowledge_by_file,
        extract_text_from_file,
        summarize_chunk,
        create_knowledge_chunk,
        PARSEABLE_EXTENSIONS,
        _get_file_extension,
    )
    from services.nexus.documents import get_file

    _logger.info("Knowledge worker thread started.")
    while True:
        try:
            task = get_next_parse_task()
            if not task:
                time.sleep(10)
                continue

            queue_id = task["id"]
            file_id = task["file_id"]
            _logger.info("Knowledge worker: processing file #%d", file_id)

            file_record = get_file(file_id)
            if not file_record:
                update_parse_status(queue_id, "failed", "File record not found")
                continue

            ext = _get_file_extension(file_record["file_name"])
            if ext not in PARSEABLE_EXTENSIONS:
                update_parse_status(queue_id, "skipped", f"Unsupported: {ext}")
                update_file_parse_status(file_id, "skipped")
                continue

            update_file_parse_status(file_id, "parsing")
            delete_knowledge_by_file(file_id)

            try:
                chunks = extract_text_from_file(
                    file_record["file_path"], file_record["file_name"]
                )
            except FileNotFoundError as e:
                update_parse_status(queue_id, "failed", str(e))
                update_file_parse_status(file_id, "failed")
                continue

            if not chunks:
                update_parse_status(queue_id, "done", "Empty file")
                update_file_parse_status(file_id, "empty")
                continue

            ai_failures = 0
            for i, chunk in enumerate(chunks):
                ai_result = summarize_chunk(chunk["content"])
                if ai_result["summary"] is None:
                    ai_failures += 1
                create_knowledge_chunk(
                    file_id=file_id,
                    client_id=file_record.get("client_id"),
                    chunk_index=i,
                    content=chunk["content"],
                    summary=ai_result["summary"],
                    tags=ai_result["tags"],
                    metadata=chunk.get("metadata"),
                )

            final = "done" if ai_failures == 0 else "partial"
            update_parse_status(queue_id, "done")
            update_file_parse_status(file_id, final)
            _logger.info(
                "Knowledge worker: file #%d done (%d chunks, %d AI failures)",
                file_id, len(chunks), ai_failures,
            )

        except Exception as e:
            _logger.error("Knowledge worker error: %s", e)
            time.sleep(10)


@app.on_event("startup")
def startup():
    try:
        init_db()
    except Exception as e:
        _logger.warning("DB init skipped: %s", e)

    # Start knowledge worker as daemon thread
    t = threading.Thread(target=_knowledge_worker_loop, daemon=True)
    t.start()
    _logger.info("Knowledge worker thread launched.")


@app.get("/api/health")
def health():
    return {"status": "ok"}
