"""Nexus tenders router — markdown SSOT + DB sync + AI response generation."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from services.nexus.tenders import (
    get_all_tenders,
    get_tender,
    get_tenders_expiring,
    enrich_tender,
    enrich_all_active,
    import_from_pcc_url,
    TRACKING_STATUSES,
    TRACKING_STATUS_LABELS,
)
from services.nexus.tender_db import (
    get_tender as get_tender_db,
    get_tender_by_job_number,
    get_all_tenders as get_all_tenders_db,
    update_tender as update_tender_db,
    update_tracking_status as dual_write_tracking,
    link_deal,
    unlink_deal,
    get_tender_deals,
    sync_all_markdown,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Existing markdown-backed endpoints
# ---------------------------------------------------------------------------


@router.get("/")
def list_tenders(
    status: str = "active",
    category: str | None = None,
    tracking_status: str | None = None,
    source: str = "markdown",
):
    """List tenders. source=markdown (default) or source=db."""
    if source == "db":
        return get_all_tenders_db(status, tracking_status, category)
    tenders = get_all_tenders(status, category, tracking_status)
    # Strip body_md from list response (too large)
    return [{k: v for k, v in t.items() if k != "body_md"} for t in tenders]


@router.get("/tracking-statuses")
def list_tracking_statuses():
    """Return available tracking statuses with labels."""
    return [
        {"key": k, "label": v}
        for k, v in TRACKING_STATUS_LABELS.items()
    ]


@router.get("/expiring")
def expiring(within_days: int = 30):
    return get_tenders_expiring(within_days)


class UpdateTrackingStatusRequest(BaseModel):
    tracking_status: str


@router.patch("/{job_number}/tracking-status")
def patch_tracking_status(job_number: str, body: UpdateTrackingStatusRequest):
    """Update a tender's tracking status (dual-write: markdown + DB)."""
    try:
        return dual_write_tracking(job_number, body.tracking_status)
    except FileNotFoundError:
        raise HTTPException(404, f"Tender {job_number} not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


class ImportPccRequest(BaseModel):
    url: str


@router.post("/import-pcc")
def import_pcc(body: ImportPccRequest):
    """Import a tender directly from a pcc.gov.tw URL."""
    try:
        result = import_from_pcc_url(body.url)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/enrich-all")
def enrich_all():
    """Enrich all active tenders with pcc.gov.tw page content + notice documents."""
    results = enrich_all_active()
    return {"results": results}


@router.post("/{job_number}/enrich")
def enrich(job_number: str):
    """Enrich a single tender with full content from pcc.gov.tw."""
    try:
        return enrich_tender(job_number)
    except FileNotFoundError:
        raise HTTPException(404, f"Tender {job_number} not found")
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------------------------------
# DB sync + deal linking
# ---------------------------------------------------------------------------


@router.post("/sync")
def trigger_sync():
    """Sync all markdown tender files → DB."""
    result = sync_all_markdown()
    return result


class LinkDealRequest(BaseModel):
    deal_id: int


@router.post("/by-id/{tender_id}/deals")
def add_deal_link(tender_id: int, body: LinkDealRequest):
    """Link a deal to a tender."""
    tender = get_tender_db(tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")
    return link_deal(tender_id, body.deal_id)


@router.delete("/by-id/{tender_id}/deals/{deal_id}", status_code=204)
def remove_deal_link(tender_id: int, deal_id: int):
    """Unlink a deal from a tender."""
    unlink_deal(tender_id, deal_id)
    return Response(status_code=204)


@router.get("/by-id/{tender_id}/deals")
def list_tender_deals(tender_id: int):
    """List deals linked to a tender."""
    return get_tender_deals(tender_id)


@router.get("/by-id/{tender_id}")
def read_tender_by_id(tender_id: int):
    """Get a tender by DB id."""
    t = get_tender_db(tender_id)
    if not t:
        raise HTTPException(404, "Tender not found")
    t["deals"] = get_tender_deals(tender_id)
    return t


# ---------------------------------------------------------------------------
# AI-assisted response generation (analyze / chat / generate)
# ---------------------------------------------------------------------------

TENDER_ANALYZE_PROMPT = """你是 B2B 業務投標分析師。分析以下標案需求，並根據公司素材進行匹配。

輸出 JSON 格式（繁體中文）：
{
  "fit_score": 0-100 的匹配度分數,
  "summary": "一句話說明此案與我司的匹配度",
  "risks": ["風險1", "風險2"],
  "opportunities": ["機會1", "機會2"],
  "matched_cases": ["case_study_id1"],
  "matched_solutions": ["solution_id1"],
  "key_requirements": ["需求1", "需求2"],
  "questions": ["需要確認的問題1", "需要確認的問題2"]
}

匹配邏輯：
- 比對標案的採購類別、標的分類、廠商資格與我司的能力/案例
- 考慮預算規模是否合理
- 評估時程是否可行
- 識別需要的認證或資格

只輸出 JSON，不要其他文字。"""


TENDER_CHAT_PROMPT = """你是協助準備標案回應的 B2B 業務助手。根據標案資訊和目前已收集的回應內容，繼續問答以補齊回應書所需資訊。

標案資訊：
{tender_info}

目前已收集的回應資料：
{current_response}

{chat_history_section}

使用者訊息：{user_msg}

請根據使用者的回答：
1. 更新回應資料中的相應欄位
2. 繼續追問下一個需要補齊的資訊
3. 優先補齊：技術方案、團隊配置、時程、費用

回覆格式：
(你的回覆文字，繁體中文)
---
(更新後的 JSON 欄位，只包含新增/修改的欄位)"""


TENDER_GENERATE_PROMPT = """你是專業的標案回應書撰寫者。根據以下結構化資料，套用範本格式產生完整的回應書。

標案資訊：
{tender_info}

回應資料：
{response_data}

公司素材：
{company_materials}

範本格式：
{template}

請產生完整的回應書 markdown。使用繁體中文。
保持專業但清晰的語氣。用實際資料填入範本的 placeholder。
如果某些欄位資料不足，用合理的預設內容標記「[待補充]」。"""


class ChatMessage(BaseModel):
    message: str
    current_response: dict | None = None


@router.post("/by-id/{tender_id}/analyze")
def analyze_tender(tender_id: int):
    """AI initial analysis: match tender requirements against company materials."""
    from services.ai_provider import check_ai_available, generate_ai_response

    tender = get_tender_db(tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    available, msg = check_ai_available()
    if not available:
        raise HTTPException(503, f"AI service not available: {msg}")

    # Load tender body from markdown
    tender_body = ""
    md_tender = get_tender(tender["job_number"])
    if md_tender and md_tender.get("body_md"):
        tender_body = md_tender["body_md"][:6000]

    # Load company materials
    materials_root = Path(__file__).resolve().parent.parent.parent.parent / "materials"
    company_text = _load_materials_text(materials_root / "company", max_chars=3000)
    cases_text = _load_materials_text(materials_root / "case-studies", max_chars=3000)
    solutions_text = _load_materials_text(materials_root / "solutions", max_chars=2000)

    user_prompt = f"""## 標案資訊
標案名稱：{tender['title']}
招標機關：{tender.get('agency', '')}
採購類別：{tender.get('category', '')} / {tender.get('category_detail', '')}
預算：{tender.get('budget', '未公開')}
截止日期：{tender.get('deadline', '未知')}
招標方式：{tender.get('tender_type', '')}

### 標案內容
{tender_body}

## 公司素材
### 公司能力
{company_text}

### 過往案例
{cases_text}

### 解決方案
{solutions_text}"""

    ai_raw = generate_ai_response(TENDER_ANALYZE_PROMPT, user_prompt)

    # Parse JSON response
    analysis = {}
    try:
        cleaned = ai_raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        analysis = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Analyze parse failed for tender #%d: %s", tender_id, ai_raw[:200])
        analysis = {"summary": ai_raw.strip(), "fit_score": 0, "questions": []}

    # Save to response_json
    response_json = tender.get("response_json") or {}
    if isinstance(response_json, str):
        try:
            response_json = json.loads(response_json)
        except json.JSONDecodeError:
            response_json = {}
    response_json["analysis"] = analysis

    update_tender_db(tender_id, response_json=response_json)

    return {
        "analysis": analysis,
        "tender_id": tender_id,
        "job_number": tender["job_number"],
    }


@router.post("/by-id/{tender_id}/chat")
def chat_tender(tender_id: int, body: ChatMessage):
    """Conversational followup to build the tender response step by step."""
    from services.ai_provider import check_ai_available, generate_ai_response

    tender = get_tender_db(tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    available, msg = check_ai_available()
    if not available:
        raise HTTPException(503, f"AI service not available: {msg}")

    current_response = body.current_response or {}

    # Load existing response_json for chat history
    response_json = tender.get("response_json") or {}
    if isinstance(response_json, str):
        try:
            response_json = json.loads(response_json)
        except json.JSONDecodeError:
            response_json = {}

    chat_history = response_json.get("chat_history", [])

    # Build chat history section
    chat_history_section = ""
    if chat_history:
        recent = chat_history[-6:]
        lines = []
        for msg_item in recent:
            role = "User" if msg_item["role"] == "user" else "AI"
            lines.append(f"{role}: {msg_item['content']}")
        chat_history_section = (
            "Previous conversation (DO NOT repeat questions already asked):\n"
            + "\n".join(lines)
        )

    tender_info = (
        f"標案：{tender['title']}\n"
        f"機關：{tender.get('agency', '')}\n"
        f"類別：{tender.get('category_detail', '')}\n"
        f"預算：{tender.get('budget', '未公開')}\n"
        f"截止：{tender.get('deadline', '未知')}"
    )

    prompt = TENDER_CHAT_PROMPT.format(
        tender_info=tender_info,
        current_response=json.dumps(current_response, ensure_ascii=False, indent=2),
        chat_history_section=chat_history_section,
        user_msg=body.message,
    )

    ai_raw = generate_ai_response(
        "You are a B2B tender response assistant. Reply in Traditional Chinese.",
        prompt,
    )

    ai_reply = ai_raw.strip()
    new_fields = {}

    if "---" in ai_raw:
        parts = ai_raw.split("---", 1)
        ai_reply = parts[0].strip()
        json_part = parts[1].strip()
        try:
            if json_part.startswith("```"):
                json_part = json_part.split("\n", 1)[1].rsplit("```", 1)[0]
            new_fields = json.loads(json_part)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Chat parse failed for tender #%d: %s", tender_id, json_part[:200])

    # Merge into response
    merged_response = {**current_response}
    for k, v in new_fields.items():
        if v is not None:
            merged_response[k] = v

    # Update chat history
    chat_history.append({"role": "user", "content": body.message})
    chat_history.append({"role": "assistant", "content": ai_reply})

    # Save to DB
    response_json["response"] = merged_response
    response_json["chat_history"] = chat_history
    update_tender_db(tender_id, response_json=response_json)

    return {
        "ai_reply": ai_reply,
        "updated_fields": new_fields,
        "response_json": response_json,
    }


@router.post("/by-id/{tender_id}/generate")
def generate_response(tender_id: int):
    """Generate the final tender response document from collected data."""
    from services.ai_provider import check_ai_available, generate_ai_response

    tender = get_tender_db(tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    available, msg = check_ai_available()
    if not available:
        raise HTTPException(503, f"AI service not available: {msg}")

    response_json = tender.get("response_json") or {}
    if isinstance(response_json, str):
        try:
            response_json = json.loads(response_json)
        except json.JSONDecodeError:
            response_json = {}

    response_data = response_json.get("response", {})
    analysis = response_json.get("analysis", {})

    # Load template
    template_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "materials" / "templates" / "open-request-response.md"
    )
    template = ""
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")

    # Load company materials
    materials_root = Path(__file__).resolve().parent.parent.parent.parent / "materials"
    company_text = _load_materials_text(materials_root / "company", max_chars=3000)

    # Load matched case studies
    matched_cases_text = ""
    matched_cases = analysis.get("matched_cases", [])
    if matched_cases:
        case_dir = materials_root / "case-studies"
        for case_id in matched_cases[:3]:
            for f in case_dir.glob("*.md"):
                if case_id in f.stem:
                    matched_cases_text += f.read_text(encoding="utf-8")[:2000] + "\n\n"
                    break

    # Load tender body
    tender_body = ""
    md_tender = get_tender(tender["job_number"])
    if md_tender and md_tender.get("body_md"):
        tender_body = md_tender["body_md"][:4000]

    tender_info = (
        f"標案名稱：{tender['title']}\n"
        f"標案案號：{tender['job_number']}\n"
        f"招標機關：{tender.get('agency', '')}\n"
        f"類別：{tender.get('category_detail', '')}\n"
        f"預算：{tender.get('budget', '未公開')}\n"
        f"截止：{tender.get('deadline', '未知')}\n\n"
        f"### 標案內容\n{tender_body}"
    )

    prompt = TENDER_GENERATE_PROMPT.format(
        tender_info=tender_info,
        response_data=json.dumps(
            {**response_data, "analysis": analysis},
            ensure_ascii=False, indent=2,
        ),
        company_materials=company_text + "\n\n### 相關案例\n" + matched_cases_text,
        template=template,
    )

    doc = generate_ai_response(
        "You are a professional tender response writer. Output in Traditional Chinese markdown.",
        prompt,
    )

    # Optionally save to file
    responses_dir = materials_root / "tenders" / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)
    output_path = responses_dir / f"{tender['job_number']}-response.md"
    output_path.write_text(doc, encoding="utf-8")

    return {
        "document": doc,
        "tender_id": tender_id,
        "job_number": tender["job_number"],
        "output_path": str(output_path),
    }


# ---------------------------------------------------------------------------
# Markdown-backed single tender (keep at bottom — catch-all path param)
# ---------------------------------------------------------------------------


@router.get("/{job_number}")
def read_tender(job_number: str):
    t = get_tender(job_number)
    if not t:
        raise HTTPException(404, "Tender not found")
    # Enrich with DB id if available
    db_tender = get_tender_by_job_number(job_number)
    if db_tender:
        t["id"] = db_tender["id"]
        t["client_id"] = db_tender.get("client_id")
        t["response_json"] = db_tender.get("response_json")
    return t


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_materials_text(directory: Path, max_chars: int = 3000) -> str:
    """Load all .md files from a directory into a single text block."""
    if not directory.exists():
        return ""
    texts = []
    total = 0
    for f in sorted(directory.glob("*.md")):
        if f.name.startswith("INDEX") or f.name.startswith("README"):
            continue
        content = f.read_text(encoding="utf-8")
        if total + len(content) > max_chars:
            remaining = max_chars - total
            if remaining > 200:
                texts.append(content[:remaining])
            break
        texts.append(content)
        total += len(content)
    return "\n\n---\n\n".join(texts)
