"""Nexus memory service — md-centric knowledge management system.

Manages markdown files in knowledge/ directory with YAML frontmatter.
Provides CRUD + full-text search + auto-sync hooks from DB entities.
Supports inbox/domain/deals zones with promote workflow.
"""

import json
import logging
import os
import re
import shutil
from datetime import date
from pathlib import Path

import yaml

from database.connection import get_connection, row_to_dict, rows_to_dicts

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(name: str) -> str:
    """Create a filesystem-safe slug from a name (Chinese-friendly)."""
    slug = re.sub(r"[\s/\\:*?\"<>|]+", "-", name.strip())
    slug = slug.strip("-")
    return slug or "unnamed"


def _parse_frontmatter(path: Path) -> dict | None:
    """Parse YAML frontmatter from a markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
        if not match:
            return None
        meta = yaml.safe_load(match.group(1)) or {}
        meta["_body"] = match.group(2).strip()
        meta["_path"] = str(path.relative_to(KNOWLEDGE_DIR))
        return meta
    except Exception as e:
        logger.warning("Failed to parse %s: %s", path, e)
        return None


def _write_md(path: Path, frontmatter: dict, body: str) -> None:
    """Write a markdown file with YAML frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = {k: v for k, v in frontmatter.items() if not k.startswith("_")}
    content = f"---\n{yaml.dump(fm, allow_unicode=True, default_flow_style=False).strip()}\n---\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def _today() -> str:
    return date.today().isoformat()


def _detect_zone(rel_path: str) -> str:
    """Detect zone from relative path: inbox, domain, deals, or templates."""
    parts = rel_path.split("/")
    if parts[0] in ("inbox", "domain", "deals", "templates"):
        return parts[0]
    # Legacy paths (clients, general, reference) → treat as inbox
    return "inbox"


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def list_memories(
    scope: str | None = None,
    client_id: int | None = None,
    deal_id: int | None = None,
    type_: str | None = None,
    status: str | None = None,
    category: str | None = None,
    zone: str | None = None,
) -> list[dict]:
    """Scan knowledge/ directory, parse frontmatter, filter by criteria."""
    results = []
    if not KNOWLEDGE_DIR.exists():
        return results

    for md_path in KNOWLEDGE_DIR.rglob("*.md"):
        meta = _parse_frontmatter(md_path)
        if not meta:
            continue
        # Apply filters
        if scope and meta.get("scope") != scope:
            continue
        if client_id is not None and meta.get("client_id") != client_id:
            continue
        if deal_id is not None and meta.get("deal_id") != deal_id:
            continue
        if type_ and meta.get("type") != type_:
            continue
        if status and meta.get("status") != status:
            continue
        if category and meta.get("category") != category:
            continue
        if zone:
            detected = _detect_zone(meta.get("_path", ""))
            if detected != zone:
                continue
        # Promote _path to path, strip body for list view
        meta["path"] = meta.pop("_path", "")
        meta.pop("_body", None)
        results.append(meta)

    results.sort(key=lambda m: m.get("updated", ""), reverse=True)
    return results


def get_memory(rel_path: str) -> dict | None:
    """Read a single md file by relative path within knowledge/."""
    full_path = KNOWLEDGE_DIR / rel_path
    if not full_path.exists() or not full_path.is_file():
        return None
    meta = _parse_frontmatter(full_path)
    if meta:
        meta["path"] = meta.pop("_path", rel_path)
    return meta


def create_memory(
    folder: str, filename: str, frontmatter: dict, body: str
) -> dict:
    """Create a new memory md file."""
    rel_path = f"{folder}/{filename}"
    full_path = KNOWLEDGE_DIR / rel_path
    if full_path.exists():
        raise FileExistsError(f"Memory already exists: {rel_path}")
    frontmatter.setdefault("created", _today())
    frontmatter.setdefault("updated", _today())
    frontmatter.setdefault("status", "draft")
    _write_md(full_path, frontmatter, body)
    return {"path": rel_path, **frontmatter}


def update_memory(rel_path: str, frontmatter: dict, body: str) -> dict:
    """Update an existing memory md file."""
    full_path = KNOWLEDGE_DIR / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Memory not found: {rel_path}")
    frontmatter["updated"] = _today()
    _write_md(full_path, frontmatter, body)
    return {"path": rel_path, **frontmatter}


def delete_memory(rel_path: str) -> bool:
    """Delete a memory md file."""
    full_path = KNOWLEDGE_DIR / rel_path
    if not full_path.exists():
        return False
    full_path.unlink()
    # Clean up empty parent directories
    parent = full_path.parent
    while parent != KNOWLEDGE_DIR and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent
    return True


def search_memories(query: str) -> list[dict]:
    """Full-text search across frontmatter + body."""
    if not query or not KNOWLEDGE_DIR.exists():
        return []

    query_lower = query.lower()
    results = []

    for md_path in KNOWLEDGE_DIR.rglob("*.md"):
        try:
            text = md_path.read_text(encoding="utf-8").lower()
            if query_lower in text:
                meta = _parse_frontmatter(md_path)
                if meta:
                    meta["path"] = meta.pop("_path", "")
                    body = meta.pop("_body", "")
                    idx = body.lower().find(query_lower)
                    if idx >= 0:
                        start = max(0, idx - 50)
                        end = min(len(body), idx + len(query) + 50)
                        meta["snippet"] = body[start:end]
                    results.append(meta)
        except Exception:
            continue

    results.sort(key=lambda m: m.get("updated", ""), reverse=True)
    return results


# ---------------------------------------------------------------------------
# Knowledge management — promote, status, categories, templates
# ---------------------------------------------------------------------------


def promote_memory(
    source_path: str,
    target_zone: str,
    category: str,
    new_title: str,
    new_body: str,
    tags: list[str] | None = None,
) -> dict:
    """Promote an inbox item to domain or deals knowledge."""
    source_full = KNOWLEDGE_DIR / source_path
    if not source_full.exists():
        raise FileNotFoundError(f"Source not found: {source_path}")

    source_meta = _parse_frontmatter(source_full)
    if not source_meta:
        raise ValueError(f"Cannot parse source: {source_path}")

    # Determine target path
    cat_slug = _slugify(category)
    filename = f"{_slugify(new_title)}.md"
    if target_zone == "domain":
        target_rel = f"domain/{cat_slug}/{filename}"
    elif target_zone == "deals":
        target_rel = f"deals/{cat_slug}/{filename}"
    else:
        raise ValueError(f"Invalid target zone: {target_zone}")

    target_full = KNOWLEDGE_DIR / target_rel
    if target_full.exists():
        raise FileExistsError(f"Target already exists: {target_rel}")

    # Build frontmatter
    scope = "long-term" if target_zone == "domain" else "short-term"
    fm_type = "domain-insight" if target_zone == "domain" else "deal-note"
    frontmatter = {
        "title": new_title,
        "type": fm_type,
        "scope": scope,
        "status": "draft",
        "category": category,
        "tags": tags or source_meta.get("tags", []),
        "source": "promoted",
        "promoted_from": source_path,
        "created": _today(),
        "updated": _today(),
    }
    # Carry over client/deal references
    if source_meta.get("client"):
        frontmatter["client"] = source_meta["client"]
    if source_meta.get("client_id"):
        frontmatter["client_id"] = source_meta["client_id"]
    if source_meta.get("deal_id"):
        frontmatter["deal_id"] = source_meta["deal_id"]

    _write_md(target_full, frontmatter, new_body)

    # Mark source as archived
    source_meta["status"] = "archived"
    source_meta["updated"] = _today()
    source_body = source_meta.pop("_body", "")
    source_meta.pop("_path", None)
    _write_md(source_full, source_meta, source_body)

    logger.info("Promoted %s → %s", source_path, target_rel)
    return {"path": target_rel, **frontmatter}


def update_status(rel_path: str, new_status: str) -> dict:
    """Update lifecycle status of a memory (inbox→draft→published→archived)."""
    valid = {"inbox", "draft", "published", "archived"}
    if new_status not in valid:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {valid}")

    full_path = KNOWLEDGE_DIR / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Memory not found: {rel_path}")

    meta = _parse_frontmatter(full_path)
    if not meta:
        raise ValueError(f"Cannot parse: {rel_path}")

    body = meta.pop("_body", "")
    meta.pop("_path", None)
    meta["status"] = new_status
    meta["updated"] = _today()

    _write_md(full_path, meta, body)
    return {"path": rel_path, "status": new_status}


def list_categories() -> list[dict]:
    """Return all categories with counts."""
    cats: dict[str, int] = {}
    if not KNOWLEDGE_DIR.exists():
        return []

    for md_path in KNOWLEDGE_DIR.rglob("*.md"):
        meta = _parse_frontmatter(md_path)
        if not meta:
            continue
        cat = meta.get("category")
        if cat:
            cats[cat] = cats.get(cat, 0) + 1

    return [{"name": k, "count": v} for k, v in sorted(cats.items())]


def create_from_template(
    template_name: str,
    target_zone: str,
    category: str,
    title: str,
) -> dict:
    """Create a new knowledge item from a template."""
    template_path = KNOWLEDGE_DIR / "templates" / f"{template_name}.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    tmpl_meta = _parse_frontmatter(template_path)
    if not tmpl_meta:
        raise ValueError(f"Cannot parse template: {template_name}")

    body = tmpl_meta.get("_body", "")
    # Replace placeholders
    body = body.replace("{{title}}", title)
    body = body.replace("{{category}}", category)
    body = body.replace("{{date}}", _today())

    cat_slug = _slugify(category)
    filename = f"{_slugify(title)}.md"
    if target_zone == "domain":
        folder = f"domain/{cat_slug}"
    elif target_zone == "deals":
        folder = f"deals/{cat_slug}"
    else:
        raise ValueError(f"Invalid target zone: {target_zone}")

    scope = "long-term" if target_zone == "domain" else "short-term"
    fm_type = "domain-insight" if target_zone == "domain" else "deal-note"
    frontmatter = {
        "title": title,
        "type": fm_type,
        "scope": scope,
        "status": "draft",
        "category": category,
        "tags": [],
        "source": "template",
        "created": _today(),
        "updated": _today(),
    }

    return create_memory(folder, filename, frontmatter, body)


def list_templates() -> list[dict]:
    """List available templates."""
    templates_dir = KNOWLEDGE_DIR / "templates"
    if not templates_dir.exists():
        return []
    results = []
    for md_path in templates_dir.glob("*.md"):
        meta = _parse_frontmatter(md_path)
        if meta:
            results.append({
                "name": md_path.stem,
                "title": meta.get("title", md_path.stem),
                "description": meta.get("description", ""),
            })
    return results


# ---------------------------------------------------------------------------
# Migration — move existing files to inbox/
# ---------------------------------------------------------------------------


def migrate_to_inbox() -> dict:
    """One-time migration: move clients/, deals/, general/ → inbox/."""
    stats = {"moved": 0, "skipped": 0, "errors": 0}

    mapping = {
        "clients": "inbox/clients",
        "deals": "inbox/deals",
        "general": "inbox/uncategorized",
    }

    for old_dir, new_dir in mapping.items():
        old_path = KNOWLEDGE_DIR / old_dir
        if not old_path.exists():
            continue
        for md_path in old_path.rglob("*.md"):
            try:
                rel = md_path.relative_to(old_path)
                new_md_path = KNOWLEDGE_DIR / new_dir / rel

                # Read, add status: inbox, write to new location
                meta = _parse_frontmatter(md_path)
                if not meta:
                    stats["skipped"] += 1
                    continue

                body = meta.pop("_body", "")
                meta.pop("_path", None)
                meta["status"] = "inbox"

                new_md_path.parent.mkdir(parents=True, exist_ok=True)
                _write_md(new_md_path, meta, body)

                # Remove original
                md_path.unlink()
                stats["moved"] += 1
            except Exception as e:
                logger.warning("migrate error for %s: %s", md_path, e)
                stats["errors"] += 1

    # Clean up empty old directories
    for old_dir in mapping:
        old_path = KNOWLEDGE_DIR / old_dir
        if old_path.exists():
            try:
                shutil.rmtree(old_path, ignore_errors=True)
            except Exception:
                pass

    # Also remove reference/ if empty
    ref_path = KNOWLEDGE_DIR / "reference"
    if ref_path.exists() and not any(ref_path.iterdir()):
        ref_path.rmdir()

    logger.info("migrate_to_inbox: %s", stats)
    return stats


# ---------------------------------------------------------------------------
# Auto-sync hooks — write to inbox/
# ---------------------------------------------------------------------------


def sync_from_client(client_id: int) -> str | None:
    """Generate/update inbox/clients/{slug}/profile.md from nx_client."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_client WHERE id = %s", (client_id,))
            client = row_to_dict(cur)
    if not client:
        return None

    slug = _slugify(client["name"])
    rel_path = f"inbox/clients/{slug}/profile.md"
    full_path = KNOWLEDGE_DIR / rel_path

    frontmatter = {
        "title": f"{client['name']} — 客戶概覽",
        "type": "client-profile",
        "scope": "long-term",
        "status": "inbox",
        "client": client["name"],
        "client_id": client["id"],
        "tags": [t for t in [client.get("industry")] if t],
        "source": "auto",
        "source_type": "nx_client",
        "source_id": client["id"],
        "created": str(client.get("created_at", _today()))[:10],
        "updated": _today(),
    }

    lines = [f"# {client['name']}\n"]
    if client.get("industry"):
        lines.append(f"- **產業**: {client['industry']}")
    if client.get("budget_range"):
        lines.append(f"- **預算範圍**: {client['budget_range']}")
    if client.get("status"):
        lines.append(f"- **狀態**: {client['status']}")
    if client.get("notes"):
        lines.append(f"\n## 備註\n\n{client['notes']}")

    body = "\n".join(lines)
    _write_md(full_path, frontmatter, body)
    logger.info("Synced client #%d → %s", client_id, rel_path)
    return rel_path


def sync_from_deal(deal_id: int) -> str | None:
    """Generate/update inbox/deals/{slug}/overview.md from nx_deal."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.*, c.name AS client_name
                   FROM nx_deal d JOIN nx_client c ON d.client_id = c.id
                   WHERE d.id = %s""",
                (deal_id,),
            )
            deal = row_to_dict(cur)
    if not deal:
        return None

    slug = _slugify(deal["name"])
    rel_path = f"inbox/deals/{slug}/overview.md"
    full_path = KNOWLEDGE_DIR / rel_path

    frontmatter = {
        "title": deal["name"],
        "type": "deal-overview",
        "scope": "short-term",
        "status": "inbox",
        "client": deal.get("client_name"),
        "client_id": deal["client_id"],
        "deal_id": deal["id"],
        "tags": [deal.get("stage", ""), deal.get("status", "")],
        "source": "auto",
        "source_type": "nx_deal",
        "source_id": deal["id"],
        "created": str(deal.get("created_at", _today()))[:10],
        "updated": _today(),
    }

    lines = [f"# {deal['name']}\n"]
    lines.append(f"- **客戶**: {deal.get('client_name', 'N/A')}")
    lines.append(f"- **階段**: {deal.get('stage', 'N/A')}")
    lines.append(f"- **狀態**: {deal.get('status', 'N/A')}")
    if deal.get("budget_range"):
        lines.append(f"- **預算範圍**: {deal['budget_range']}")
    if deal.get("budget_amount"):
        lines.append(f"- **預算金額**: {deal['budget_amount']}")
    if deal.get("timeline"):
        lines.append(f"- **時程**: {deal['timeline']}")

    meddic = deal.get("meddic_json")
    if meddic:
        if isinstance(meddic, str):
            meddic = json.loads(meddic)
        filled = {k: v for k, v in meddic.items() if v}
        if filled:
            lines.append("\n## MEDDIC\n")
            for k, v in filled.items():
                lines.append(f"- **{k}**: {v}")

    if deal.get("close_notes"):
        lines.append(f"\n## 結案備註\n\n{deal['close_notes']}")

    body = "\n".join(lines)
    _write_md(full_path, frontmatter, body)
    logger.info("Synced deal #%d → %s", deal_id, rel_path)
    return rel_path


def sync_from_intel(intel_id: int) -> str | None:
    """Generate/update inbox/clients/{client}/intel-{id}.md from nx_intel."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM nx_intel WHERE id = %s", (intel_id,))
            intel = row_to_dict(cur)
            if not intel:
                return None

            cur.execute(
                """SELECT c.id, c.name FROM nx_intel_entity ie
                   JOIN nx_client c ON ie.entity_id = c.id
                   WHERE ie.intel_id = %s AND ie.entity_type = 'client'
                   LIMIT 1""",
                (intel_id,),
            )
            client_row = cur.fetchone()

    client_name = client_row[1] if client_row else None
    client_id = client_row[0] if client_row else None

    if client_name:
        slug = _slugify(client_name)
        rel_path = f"inbox/clients/{slug}/intel-{intel_id}.md"
    else:
        rel_path = f"inbox/uncategorized/intel-{intel_id}.md"

    full_path = KNOWLEDGE_DIR / rel_path

    title = intel.get("title") or f"情報 #{intel_id}"
    frontmatter = {
        "title": title,
        "type": "intel",
        "scope": "short-term",
        "status": "inbox",
        "tags": [],
        "source": "auto",
        "source_type": "nx_intel",
        "source_id": intel_id,
        "created": str(intel.get("created_at", _today()))[:10],
        "updated": _today(),
    }
    if client_name:
        frontmatter["client"] = client_name
        frontmatter["client_id"] = client_id

    parsed = intel.get("parsed_json")
    if parsed:
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except Exception:
                parsed = None
        if isinstance(parsed, dict):
            tags = parsed.get("tags") or parsed.get("keywords") or []
            if isinstance(tags, list):
                frontmatter["tags"] = tags

    lines = [f"# {title}\n"]
    lines.append(f"**狀態**: {intel.get('status', 'draft')}\n")
    if intel.get("raw_input"):
        lines.append("## 原始輸入\n")
        lines.append(intel["raw_input"])

    if parsed and isinstance(parsed, dict):
        lines.append("\n## 解析結果\n")
        for k, v in parsed.items():
            if v and k not in ("tags", "keywords"):
                lines.append(f"- **{k}**: {v}")

    body = "\n".join(lines)
    _write_md(full_path, frontmatter, body)
    logger.info("Synced intel #%d → %s", intel_id, rel_path)
    return rel_path


def sync_from_meeting(meeting_id: int) -> str | None:
    """Generate inbox/clients/{client}/meeting-{date}-{id}.md from nx_meeting."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT m.*, d.name AS deal_name, c.name AS client_name, c.id AS cid
                   FROM nx_meeting m
                   LEFT JOIN nx_deal d ON m.deal_id = d.id
                   LEFT JOIN nx_client c ON d.client_id = c.id
                   WHERE m.id = %s""",
                (meeting_id,),
            )
            meeting = row_to_dict(cur)
    if not meeting:
        return None

    client_name = meeting.get("client_name")
    meeting_date = str(meeting.get("meeting_date", _today()))[:10]

    if client_name:
        slug = _slugify(client_name)
        rel_path = f"inbox/clients/{slug}/meeting-{meeting_date}-{meeting_id}.md"
    else:
        rel_path = f"inbox/uncategorized/meeting-{meeting_date}-{meeting_id}.md"

    full_path = KNOWLEDGE_DIR / rel_path

    frontmatter = {
        "title": meeting.get("title", f"會議 {meeting_date}"),
        "type": "meeting",
        "scope": "short-term",
        "status": "inbox",
        "tags": [],
        "source": "auto",
        "source_type": "nx_meeting",
        "source_id": meeting_id,
        "created": meeting_date,
        "updated": _today(),
    }
    if client_name:
        frontmatter["client"] = client_name
        frontmatter["client_id"] = meeting.get("cid")
    if meeting.get("deal_id"):
        frontmatter["deal_id"] = meeting["deal_id"]

    lines = [f"# {meeting.get('title', '會議')}\n"]
    lines.append(f"- **日期**: {meeting_date}")
    if meeting.get("deal_name"):
        lines.append(f"- **案件**: {meeting['deal_name']}")
    if meeting.get("duration_minutes"):
        lines.append(f"- **時長**: {meeting['duration_minutes']} 分鐘")
    if meeting.get("participants_json"):
        try:
            participants = json.loads(meeting["participants_json"]) if isinstance(meeting["participants_json"], str) else meeting["participants_json"]
            if isinstance(participants, list):
                lines.append(f"- **參與者**: {', '.join(str(p) for p in participants)}")
        except Exception:
            pass

    body = "\n".join(lines)
    _write_md(full_path, frontmatter, body)
    logger.info("Synced meeting #%d → %s", meeting_id, rel_path)
    return rel_path


def sync_from_file_knowledge(file_id: int) -> str | None:
    """Consolidate nx_knowledge chunks for a file into inbox/deals/{deal}/file-{id}.md."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT f.*, d.name AS deal_name, c.name AS client_name, c.id AS cid
                   FROM nx_file f
                   LEFT JOIN nx_deal d ON f.deal_id = d.id
                   LEFT JOIN nx_client c ON d.client_id = c.id
                   WHERE f.id = %s""",
                (file_id,),
            )
            file_rec = row_to_dict(cur)
            if not file_rec:
                return None

            cur.execute(
                """SELECT * FROM nx_knowledge
                   WHERE file_id = %s ORDER BY chunk_index""",
                (file_id,),
            )
            chunks = rows_to_dicts(cur)

    if not chunks:
        return None

    deal_name = file_rec.get("deal_name")
    client_name = file_rec.get("client_name")

    if deal_name:
        slug = _slugify(deal_name)
        rel_path = f"inbox/deals/{slug}/file-{file_id}.md"
    elif client_name:
        slug = _slugify(client_name)
        rel_path = f"inbox/clients/{slug}/file-{file_id}.md"
    else:
        rel_path = f"inbox/uncategorized/file-{file_id}.md"

    full_path = KNOWLEDGE_DIR / rel_path

    all_tags = list({t for c in chunks for t in (c.get("tags") or [])})

    frontmatter = {
        "title": f"文件摘要：{file_rec.get('file_name', f'File #{file_id}')}",
        "type": "file-summary",
        "scope": "short-term",
        "status": "inbox",
        "tags": all_tags[:10],
        "source": "auto",
        "source_type": "nx_knowledge",
        "source_id": file_id,
        "created": str(file_rec.get("created_at", _today()))[:10],
        "updated": _today(),
    }
    if client_name:
        frontmatter["client"] = client_name
        frontmatter["client_id"] = file_rec.get("cid")
    if file_rec.get("deal_id"):
        frontmatter["deal_id"] = file_rec["deal_id"]

    lines = [f"# {file_rec.get('file_name', 'File')}\n"]

    for chunk in chunks:
        if chunk.get("summary"):
            lines.append(f"## Chunk {chunk['chunk_index'] + 1}\n")
            lines.append(f"**摘要**: {chunk['summary']}\n")
            if chunk.get("tags"):
                lines.append(f"**標籤**: {', '.join(chunk['tags'])}\n")
            content_preview = chunk["content"][:500]
            if len(chunk["content"]) > 500:
                content_preview += "..."
            lines.append(f"```\n{content_preview}\n```\n")

    body = "\n".join(lines)
    _write_md(full_path, frontmatter, body)
    logger.info("Synced file knowledge #%d → %s", file_id, rel_path)
    return rel_path


# ---------------------------------------------------------------------------
# Full sync — generate all missing md files from DB
# ---------------------------------------------------------------------------


def sync_all() -> dict:
    """Scan DB and generate md for all entities that don't have one yet."""
    stats = {"clients": 0, "deals": 0, "intel": 0, "meetings": 0, "files": 0}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM nx_client")
            for (cid,) in cur.fetchall():
                try:
                    if sync_from_client(cid):
                        stats["clients"] += 1
                except Exception as e:
                    logger.warning("sync_from_client(%d) failed: %s", cid, e)

            cur.execute("SELECT id FROM nx_deal")
            for (did,) in cur.fetchall():
                try:
                    if sync_from_deal(did):
                        stats["deals"] += 1
                except Exception as e:
                    logger.warning("sync_from_deal(%d) failed: %s", did, e)

            cur.execute("SELECT id FROM nx_intel WHERE status = 'confirmed'")
            for (iid,) in cur.fetchall():
                try:
                    if sync_from_intel(iid):
                        stats["intel"] += 1
                except Exception as e:
                    logger.warning("sync_from_intel(%d) failed: %s", iid, e)

            cur.execute("SELECT id FROM nx_meeting")
            for (mid,) in cur.fetchall():
                try:
                    if sync_from_meeting(mid):
                        stats["meetings"] += 1
                except Exception as e:
                    logger.warning("sync_from_meeting(%d) failed: %s", mid, e)

            cur.execute(
                "SELECT DISTINCT file_id FROM nx_knowledge"
            )
            for (fid,) in cur.fetchall():
                try:
                    if sync_from_file_knowledge(fid):
                        stats["files"] += 1
                except Exception as e:
                    logger.warning("sync_from_file_knowledge(%d) failed: %s", fid, e)

    logger.info("sync_all complete: %s", stats)
    return stats
