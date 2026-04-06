"""FastAPI entry point — wraps existing services layer as REST API."""

import logging
import sys
import threading
import time
from pathlib import Path

# Add project root to sys.path so we can import services/database
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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
    settings as nx_settings,
    outlook as nx_outlook,
    outreach as nx_outreach,
    tenders as nx_tenders,
    memory as nx_memory,
    assistant as nx_assistant,
    plans as nx_plans,
    agent as nx_agent,
)

app = FastAPI(title="Project Nexus API", version="0.2.0", redirect_slashes=False)


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """Normalize paths to always have trailing slash without HTTP redirect.

    Next.js rewrites strip trailing slashes before proxying. FastAPI routes are
    defined with trailing slashes, so this middleware adds the slash in-place
    to avoid 404s when the proxy omits it.
    """
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.endswith("/"):
            scope = request.scope
            scope["path"] = scope["path"] + "/"
            if scope.get("raw_path"):
                scope["raw_path"] = scope["raw_path"] + b"/"
        return await call_next(request)


app.add_middleware(TrailingSlashMiddleware)
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
app.include_router(nx_outreach.router, prefix="/api/nx/outreach", tags=["Outreach"])
app.include_router(nx_tenders.router, prefix="/api/nx/tenders", tags=["Tenders"])
app.include_router(nx_memory.router, prefix="/api/nx/memory", tags=["Memory"])
app.include_router(nx_assistant.router, prefix="/api/nx/assistant", tags=["Assistant"])
app.include_router(nx_plans.router, prefix="/api/nx/plans", tags=["Plans"])
app.include_router(nx_agent.router, prefix="/api/nx/agent", tags=["Agent"])


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

            # Auto-sync to memory md
            try:
                from services.nexus.memory import sync_from_file_knowledge
                sync_from_file_knowledge(file_id)
            except Exception as e:
                _logger.warning("Memory sync for file #%d failed: %s", file_id, e)

        except Exception as e:
            _logger.error("Knowledge worker error: %s", e)
            time.sleep(10)


def _backfill_parse_queue():
    """Enqueue parseable files that were uploaded before auto-enqueue existed."""
    from database.connection import get_connection
    from services.nexus.knowledge import enqueue_parse

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT f.id FROM nx_file f
                    WHERE f.parse_status = 'pending'
                      AND (f.file_name ILIKE '%.pdf'
                        OR f.file_name ILIKE '%.pptx'
                        OR f.file_name ILIKE '%.docx')
                      AND f.file_path NOT LIKE 'link://%%'
                      AND NOT EXISTS (
                          SELECT 1 FROM knowledge_parse_queue q
                          WHERE q.file_id = f.id
                      )
                """)
                rows = cur.fetchall()
        for (file_id,) in rows:
            enqueue_parse(file_id)
            _logger.info("Backfilled parse queue: file #%d", file_id)
        if rows:
            _logger.info("Backfill complete: %d files enqueued.", len(rows))
    except Exception as e:
        _logger.warning("Backfill parse queue failed: %s", e)


def _auto_close_expired_subsidies():
    """Auto-close subsidies whose deadline has passed."""
    from database.connection import get_connection

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE nx_subsidy
                    SET status = 'closed', updated_at = NOW()
                    WHERE status = 'active'
                      AND deadline_date IS NOT NULL
                      AND deadline_date < CURRENT_DATE
                    RETURNING id, name
                """)
                rows = cur.fetchall()
        if rows:
            for row in rows:
                _logger.info("Auto-closed expired subsidy #%d: %s", row[0], row[1])
            _logger.info("Auto-closed %d expired subsidies.", len(rows))
    except Exception as e:
        _logger.warning("Auto-close expired subsidies failed: %s", e)


@app.on_event("startup")
def startup():
    try:
        init_db()
    except Exception as e:
        _logger.warning("DB init skipped: %s", e)

    # Auto-close expired subsidies
    _auto_close_expired_subsidies()

    # Initial memory sync (generate missing md files)
    try:
        from services.nexus.memory import sync_all as memory_sync_all
        stats = memory_sync_all()
        _logger.info("Memory sync on startup: %s", stats)
    except Exception as e:
        _logger.warning("Memory sync on startup failed: %s", e)

    # Backfill any parseable files missing from queue
    _backfill_parse_queue()

    # Start knowledge worker as daemon thread
    t = threading.Thread(target=_knowledge_worker_loop, daemon=True)
    t.start()
    _logger.info("Knowledge worker thread launched.")


@app.get("/api/health")
def health():
    return {"status": "ok"}
