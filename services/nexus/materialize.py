"""Intel materialization engine — auto-create/match entities from parsed intel."""

import json
import logging
import re

from opencc import OpenCC

_cc_t2s = OpenCC("t2s")  # Traditional → Simplified
_cc_s2t = OpenCC("s2t")  # Simplified → Traditional

from database.connection import get_connection, rows_to_dicts
from services.nexus.clients import create_client, find_client_by_name, update_client
from services.nexus.contacts import create_contact, find_contact, update_contact
from services.nexus.intel import (
    get_intel,
    link_intel_entity,
    materialize_intel_fields,
)
from services.nexus.deals import get_deals_by_client, get_deal, update_deal, MEDDIC_KEYS
from services.nexus.partners import create_partner, find_partner_by_name
from services.nexus.subsidies import create_subsidy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------

_COMPANY_SUFFIXES = re.compile(
    r"(股份有限公司|有限公司|股份公司|集團|Corporation|Corp\.?|Incorporated|Inc\.?|Limited|Ltd\.?|Co\.?,?\s*Ltd\.?|LLC|L\.L\.C\.)\s*$",
    re.IGNORECASE,
)


def _normalize_company_name(name: str) -> str:
    """Strip common corporate suffixes for matching."""
    name = name.strip()
    name = _COMPANY_SUFFIXES.sub("", name).strip()
    return name


# ---------------------------------------------------------------------------
# Entity scanning from raw_input
# ---------------------------------------------------------------------------


def scan_raw_for_entities(raw_input: str) -> dict:
    """Scan raw_input text against existing clients, partners, and contacts.

    Returns dict with matched entity names to be merged into parsed_json.
    Matches are based on name or alias substring found in the raw text.
    """
    matches: dict = {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Scan clients (name + aliases)
            cur.execute("SELECT id, name, aliases FROM nx_client WHERE status = 'active'")
            clients = rows_to_dicts(cur)
            for c in clients:
                names_to_check = [c["name"], _normalize_company_name(c["name"])]
                if c.get("aliases"):
                    names_to_check.extend(
                        a.strip() for a in c["aliases"].split(",") if a.strip()
                    )
                for n in names_to_check:
                    if len(n) >= 2 and n in raw_input:
                        matches["company_name"] = c["name"]
                        break
                if "company_name" in matches:
                    break

            # Scan partners (name + aliases)
            cur.execute("SELECT id, name, aliases FROM nx_partner")
            partners = rows_to_dicts(cur)
            for p in partners:
                names_to_check = [p["name"], _normalize_company_name(p["name"])]
                if p.get("aliases"):
                    names_to_check.extend(
                        a.strip() for a in p["aliases"].split(",") if a.strip()
                    )
                for n in names_to_check:
                    if len(n) >= 2 and n in raw_input:
                        matches["partner_name"] = p["name"]
                        break
                if "partner_name" in matches:
                    break

            # Scan contacts
            cur.execute("SELECT id, name FROM nx_contact")
            contacts = rows_to_dicts(cur)
            for ct in contacts:
                if ct["name"] and len(ct["name"]) >= 2 and ct["name"] in raw_input:
                    # Determine if client or partner contact
                    if not matches.get("contact_name"):
                        matches["contact_name"] = ct["name"]
                    elif not matches.get("partner_contact_name"):
                        matches["partner_contact_name"] = ct["name"]

    return matches


# ---------------------------------------------------------------------------
# Core materialization
# ---------------------------------------------------------------------------


def materialize_intel(intel_id: int) -> dict:
    """Materialize entities from a confirmed intel's parsed_json.

    Returns a summary dict of actions taken.
    """
    intel = get_intel(intel_id)
    if not intel:
        return {"error": "Intel not found"}

    parsed_raw = intel.get("parsed_json")
    if not parsed_raw:
        return {"error": "No parsed_json"}

    try:
        parsed = json.loads(parsed_raw) if isinstance(parsed_raw, str) else parsed_raw
    except (json.JSONDecodeError, TypeError):
        return {"error": "Invalid parsed_json"}

    # Auto-scan raw_input for known entities if not already in parsed
    raw_input = intel.get("raw_input", "")
    if raw_input:
        scanned = scan_raw_for_entities(raw_input)
        for key, val in scanned.items():
            if not parsed.get(key):
                parsed[key] = val
                logger.info("Auto-matched %s = %s from raw_input", key, val)

    # Remap company_name → partner_name when role is partner
    role = parsed.get("role")
    if role == "partner" and parsed.get("company_name") and not parsed.get("partner_name"):
        parsed["partner_name"] = parsed["company_name"]
        logger.info("Remapped company_name → partner_name for role=partner")

    result: dict = {
        "intel_id": intel_id,
        "client": None,
        "partner": None,
        "contacts": [],
        "subsidy": None,
        "tags_applied": [],
        "fields_indexed": 0,
    }

    # 1. Company → client matching/creation
    client_id = _materialize_client(intel_id, parsed, result)

    # 2. Partner → partner matching/creation
    partner_id = _materialize_partner(intel_id, parsed, result)

    # 3. Contact matching/creation (primary contact → linked to client)
    _materialize_contacts(intel_id, parsed, client_id, result)

    # 4. Partner contact matching/creation (linked to partner)
    _materialize_partner_contacts(intel_id, parsed, partner_id, result)

    # 5. Decision maker as separate contact
    _materialize_decision_maker(intel_id, parsed, client_id, result)

    # 6. Subsidy → create if role == "subsidy"
    _materialize_subsidy(intel_id, parsed, client_id, partner_id, result)

    # 7. Budget → update client
    if client_id and parsed.get("budget"):
        _update_client_budget(client_id, parsed["budget"])

    # 8. MEDDIC auto-fill on linked deals
    if client_id:
        _apply_meddic_to_deals(client_id, parsed, result)

    # 9. Flatten all fields into nx_intel_field
    count = materialize_intel_fields(intel_id, parsed)
    result["fields_indexed"] = count

    logger.info("Materialized intel #%d: %s", intel_id, result)
    return result


# ---------------------------------------------------------------------------
# Sub-steps
# ---------------------------------------------------------------------------


def _materialize_client(intel_id: int, parsed: dict, result: dict) -> int | None:
    """Match or create client from company_name. Returns client_id or None."""
    # Skip client creation when the primary entity is a partner
    if parsed.get("role") == "partner":
        return None
    company_name = parsed.get("company_name")
    if not company_name:
        return None

    normalized = _normalize_company_name(company_name)
    # Try original, then simplified, then traditional variants
    candidates = find_client_by_name(normalized)
    if not candidates:
        candidates = find_client_by_name(_cc_t2s.convert(normalized))
    if not candidates:
        candidates = find_client_by_name(_cc_s2t.convert(normalized))

    if candidates:
        client = candidates[0]
        link_intel_entity(intel_id, "client", client["id"], "mentioned")
        # Update industry if missing
        if not client.get("industry") and parsed.get("industry"):
            update_client(client["id"], industry=parsed["industry"])
        result["client"] = {"id": client["id"], "name": client["name"], "action": "matched"}
        return client["id"]

    # No match — create new client
    industry = parsed.get("industry")
    client = create_client(name=company_name, industry=industry)
    link_intel_entity(intel_id, "client", client["id"], "created_from")
    result["client"] = {"id": client["id"], "name": client["name"], "action": "created"}
    return client["id"]


def _materialize_partner(intel_id: int, parsed: dict, result: dict) -> int | None:
    """Match or create partner from partner_name. Returns partner_id or None."""
    partner_name = parsed.get("partner_name")
    if not partner_name:
        return None

    normalized = _normalize_company_name(partner_name)
    candidates = find_partner_by_name(normalized)
    if not candidates:
        candidates = find_partner_by_name(_cc_t2s.convert(normalized))
    if not candidates:
        candidates = find_partner_by_name(_cc_s2t.convert(normalized))

    if candidates:
        partner = candidates[0]
        link_intel_entity(intel_id, "partner", partner["id"], "mentioned")
        result["partner"] = {"id": partner["id"], "name": partner["name"], "action": "matched"}
        return partner["id"]

    # No match — create new partner
    partner = create_partner(name=partner_name)
    link_intel_entity(intel_id, "partner", partner["id"], "created_from")
    result["partner"] = {"id": partner["id"], "name": partner["name"], "action": "created"}
    return partner["id"]


def _materialize_contacts(
    intel_id: int, parsed: dict, client_id: int | None, result: dict
) -> None:
    """Match or create primary contact(s) from parsed fields."""
    contact_name = parsed.get("contact_name")
    contact_email = parsed.get("contact_email")
    if not contact_name and not contact_email:
        return

    # Handle list of contact names (e.g. ["張俊彥", "林靜怡"])
    if isinstance(contact_name, list):
        for i, name in enumerate(contact_name):
            sub_parsed = {**parsed, "contact_name": name}
            # Only first contact gets email/phone/title
            if i > 0:
                sub_parsed.pop("contact_email", None)
                sub_parsed.pop("contact_phone", None)
                sub_parsed.pop("contact_title", None)
            _materialize_contacts(intel_id, sub_parsed, client_id, result)
        return

    candidates = find_contact(name=contact_name, email=contact_email)
    if not candidates and contact_name:
        candidates = find_contact(name=_cc_t2s.convert(contact_name), email=contact_email)
    if not candidates and contact_name:
        candidates = find_contact(name=_cc_s2t.convert(contact_name), email=contact_email)

    if candidates:
        contact = candidates[0]
        # Update missing fields
        updates = {}
        if not contact.get("title") and parsed.get("contact_title"):
            updates["title"] = parsed["contact_title"]
        if not contact.get("email") and contact_email:
            updates["email"] = contact_email
        if not contact.get("phone") and parsed.get("contact_phone"):
            updates["phone"] = parsed["contact_phone"]
        if not contact.get("org_id") and client_id:
            updates["org_type"] = "client"
            updates["org_id"] = client_id
        if updates:
            update_contact(contact["id"], **updates)
        link_intel_entity(intel_id, "contact", contact["id"], "mentioned")
        result["contacts"].append(
            {"id": contact["id"], "name": contact["name"], "action": "matched"}
        )
    else:
        # Create new contact
        contact = create_contact(
            name=contact_name or contact_email,
            title=parsed.get("contact_title"),
            email=contact_email,
            phone=parsed.get("contact_phone"),
            org_type="client" if client_id else None,
            org_id=client_id,
        )
        link_intel_entity(intel_id, "contact", contact["id"], "created_from")
        result["contacts"].append(
            {"id": contact["id"], "name": contact["name"], "action": "created"}
        )


def _materialize_partner_contacts(
    intel_id: int, parsed: dict, partner_id: int | None, result: dict
) -> None:
    """Match or create partner contact from partner_contact_* fields."""
    contact_name = parsed.get("partner_contact_name")
    contact_email = parsed.get("partner_contact_email")
    if not contact_name and not contact_email:
        return

    candidates = find_contact(name=contact_name, email=contact_email)

    if candidates:
        contact = candidates[0]
        updates = {}
        if not contact.get("title") and parsed.get("partner_contact_title"):
            updates["title"] = parsed["partner_contact_title"]
        if not contact.get("email") and contact_email:
            updates["email"] = contact_email
        if not contact.get("phone") and parsed.get("partner_contact_phone"):
            updates["phone"] = parsed["partner_contact_phone"]
        if not contact.get("org_id") and partner_id:
            updates["org_type"] = "partner"
            updates["org_id"] = partner_id
        if updates:
            update_contact(contact["id"], **updates)
        link_intel_entity(intel_id, "contact", contact["id"], "mentioned")
        result["contacts"].append(
            {"id": contact["id"], "name": contact["name"], "action": "matched"}
        )
    else:
        contact = create_contact(
            name=contact_name or contact_email,
            title=parsed.get("partner_contact_title"),
            email=contact_email,
            phone=parsed.get("partner_contact_phone"),
            org_type="partner" if partner_id else None,
            org_id=partner_id,
        )
        link_intel_entity(intel_id, "contact", contact["id"], "created_from")
        result["contacts"].append(
            {"id": contact["id"], "name": contact["name"], "action": "created"}
        )


def _materialize_decision_maker(
    intel_id: int, parsed: dict, client_id: int | None, result: dict
) -> None:
    """Create decision_maker as contact if distinct from primary contact."""
    dm = parsed.get("decision_maker")
    if not dm:
        return

    # Skip if same as primary contact
    contact_name = parsed.get("contact_name", "")
    if dm.strip() == contact_name.strip():
        return

    candidates = find_contact(name=dm)
    if candidates:
        contact = candidates[0]
        # Ensure role is set
        if not contact.get("role") or "decision" not in (contact.get("role") or "").lower():
            update_contact(contact["id"], role="decision_maker")
        link_intel_entity(intel_id, "contact", contact["id"], "mentioned")
        result["contacts"].append(
            {"id": contact["id"], "name": contact["name"], "action": "matched"}
        )
    else:
        contact = create_contact(
            name=dm,
            role="decision_maker",
            org_type="client" if client_id else None,
            org_id=client_id,
        )
        link_intel_entity(intel_id, "contact", contact["id"], "created_from")
        result["contacts"].append(
            {"id": contact["id"], "name": contact["name"], "action": "created"}
        )


def _materialize_subsidy(
    intel_id: int, parsed: dict, client_id: int | None, partner_id: int | None, result: dict
) -> None:
    """Create a subsidy record when role == 'subsidy'."""
    if parsed.get("role") != "subsidy":
        return

    name = (
        parsed.get("subsidy_name")
        or parsed.get("company_name")
        or parsed.get("notes", "")[:50]
        or "未命名補助案"
    )
    subsidy = create_subsidy(
        name=name,
        agency=parsed.get("agency"),
        funding_amount=parsed.get("funding_amount"),
        deadline=parsed.get("deadline"),
        eligibility=parsed.get("eligibility"),
        scope=parsed.get("scope"),
        client_id=client_id,
        partner_id=partner_id,
        notes=parsed.get("notes"),
    )
    link_intel_entity(intel_id, "subsidy", subsidy["id"], "created_from")
    result["subsidy"] = {"id": subsidy["id"], "name": subsidy["name"], "action": "created"}


def _update_client_budget(client_id: int, budget: int | str) -> None:
    """Update client budget_range from parsed budget amount."""
    try:
        amount = int(budget)
    except (ValueError, TypeError):
        return

    if amount < 100_000:
        budget_range = "<100K"
    elif amount < 500_000:
        budget_range = "100-500K"
    elif amount < 1_000_000:
        budget_range = "500K-1M"
    else:
        budget_range = "1M+"

    update_client(client_id, budget_range=budget_range)


# ---------------------------------------------------------------------------
# MEDDIC auto-fill from parsed intel fields
# ---------------------------------------------------------------------------

# Map parsed_json keys → MEDDIC keys with value formatters
_PAIN_LABELS = {
    "automation": "產線自動化",
    "aoi": "AOI 瑕疵檢測",
    "energy": "能源管理",
    "safety": "工安監控",
    "erp": "ERP 系統",
    "iot": "IoT 數據整合",
}


def _meddic_from_parsed(parsed: dict) -> dict[str, str]:
    """Extract MEDDIC field values from parsed intel JSON (deterministic mapping)."""
    updates: dict[str, str] = {}

    # identify_pain ← pain_points
    pains = parsed.get("pain_points")
    if pains:
        if isinstance(pains, list):
            labels = [_PAIN_LABELS.get(p, p) for p in pains]
            updates["identify_pain"] = "、".join(labels)
        elif isinstance(pains, str):
            updates["identify_pain"] = pains

    # economic_buyer ← decision_maker
    dm = parsed.get("decision_maker")
    if dm:
        updates["economic_buyer"] = dm

    # metrics ← budget (quantifiable)
    budget = parsed.get("budget")
    if budget:
        try:
            amount = int(budget)
            wan = amount / 10000
            updates["metrics"] = f"預算約 {wan:.0f} 萬"
        except (ValueError, TypeError):
            updates["metrics"] = str(budget)

    # champion ← contact with internal advocacy signals
    contact = parsed.get("contact_name")
    title = parsed.get("contact_title")
    if contact and title:
        updates.setdefault("champion", f"{contact}（{title}）")

    # decision_criteria / decision_process ← direct fields if AI extracted them
    if parsed.get("decision_criteria"):
        updates["decision_criteria"] = str(parsed["decision_criteria"])
    if parsed.get("decision_process"):
        updates["decision_process"] = str(parsed["decision_process"])

    return updates


def _apply_meddic_to_deals(client_id: int, parsed: dict, result: dict) -> None:
    """Auto-fill MEDDIC fields on all deals linked to this client."""
    new_fields = _meddic_from_parsed(parsed)
    if not new_fields:
        return

    deals = get_deals_by_client(client_id)
    if not deals:
        return

    meddic_updates = []
    for deal in deals:
        if deal.get("status") == "closed":
            continue
        meddic_raw = deal.get("meddic_json")
        try:
            meddic = json.loads(meddic_raw) if meddic_raw else {}
        except (json.JSONDecodeError, TypeError):
            meddic = {}

        changed = False
        for k, v in new_fields.items():
            if k in MEDDIC_KEYS and not meddic.get(k):
                meddic[k] = v
                changed = True

        if changed:
            update_deal(deal["id"], meddic_json=json.dumps(meddic, ensure_ascii=False))
            meddic_updates.append(deal["name"])

    if meddic_updates:
        result["meddic_updated"] = meddic_updates
        logger.info("Auto-filled MEDDIC for deals: %s", meddic_updates)
