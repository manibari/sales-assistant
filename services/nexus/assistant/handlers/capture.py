"""Capture handler — intel input flow (parse, followup, done, card handling).

Extracted from telegram.py. Transport-agnostic — returns AssistantResponse.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from services.ai_provider import (
    check_ai_available,
    generate_ai_response,
    generate_ai_vision_response,
)
from services.nexus.intel import confirm_intel, create_intel, update_intel
from services.nexus.deals import get_deals_by_client, link_intel_to_deal
from services.nexus.prompts import INTEL_PARSE_PROMPT, BUSINESS_CARD_PROMPT
from services.nexus.prompts.strategy import build_dynamic_followup_prompt
from services.nexus.assistant.intents import Intent
from services.nexus.assistant.display import (
    ROLE_LABELS,
    FIELD_LABELS,
    PAIN_LABELS,
    custom_industries,
    KNOWN_INDUSTRIES,
    missing_fields,
    check_new_industry,
    format_summary,
    format_initial_reply,
    format_card_raw,
    get_industry_label,
)

if TYPE_CHECKING:
    from services.nexus.assistant.engine import AssistantEngine, AssistantResponse

logger = logging.getLogger(__name__)

# OCR correction map for commonly misrecognized characters/names
_OCR_CORRECTIONS: dict[str, str] = {
    "聖暘": "聖暉",
    "先鋒資訊系統": "先啟資訊系統",
}


def _apply_ocr_corrections(card: dict) -> dict:
    """Fix known OCR misrecognitions in parsed card fields."""
    for field in ("company_name", "contact_name", "department", "notes"):
        val = card.get(field)
        if val:
            for wrong, correct in _OCR_CORRECTIONS.items():
                if wrong in val:
                    card[field] = val.replace(wrong, correct)
                    val = card[field]
    return card


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences from AI response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    return text.strip()


# ---------------------------------------------------------------------------
# AI helpers
# ---------------------------------------------------------------------------


async def _auto_parse(raw_input: str) -> dict | None:
    """Initial parse — extract structured fields from first message."""
    available, info = check_ai_available()
    if not available:
        logger.warning("AI not available for auto-parse: %s", info)
        return None
    try:
        response = await asyncio.to_thread(
            generate_ai_response, INTEL_PARSE_PROMPT, raw_input
        )
        return json.loads(_strip_json_fences(response))
    except Exception as e:
        logger.error("AI parse failed: %s", e)
        return None


async def _parse_business_card(image_bytes: bytes, caption: str = "") -> list[dict]:
    """Parse business card image(s) using vision AI."""
    available, info = check_ai_available()
    if not available:
        logger.warning("AI not available for business card parse: %s", info)
        return []
    try:
        user_text = (
            caption
            or "請辨識這張圖片中所有名片的資訊，每張名片各自回傳一個 JSON object"
        )
        response = await asyncio.to_thread(
            generate_ai_vision_response,
            BUSINESS_CARD_PROMPT
            + "\n\nIMPORTANT: If the image contains MULTIPLE business cards, return a JSON ARRAY of objects, one per card. If only one card, still return a single JSON object (not an array).",
            user_text,
            image_bytes,
            "image/jpeg",
        )
        result = json.loads(_strip_json_fences(response))
        if isinstance(result, list):
            return [_apply_ocr_corrections(c) for c in result]
        if isinstance(result, dict):
            return [_apply_ocr_corrections(result)]
        return []
    except Exception as e:
        logger.error("Business card parse failed: %s", e)
        return []


async def _followup_parse(
    current_parsed: dict,
    user_msg: str,
    chat_history: list | None = None,
    intent: Intent | None = None,
) -> tuple[str, dict]:
    """Follow-up parse — returns (reply_text, new_fields)."""
    available, info = check_ai_available()
    if not available:
        return "⚠️ AI 暫時不可用，請稍後再試", {}

    if intent is not None:
        prompt = build_dynamic_followup_prompt(
            intent=intent,
            parsed=current_parsed,
            chat_history=chat_history or [],
            user_msg=user_msg,
        )
    else:
        from services.nexus.prompts import FOLLOWUP_PROMPT

        chat_history_section = ""
        if chat_history:
            recent = chat_history[-6:]
            lines = []
            for msg in recent:
                role = "User" if msg.get("role") == "user" else "AI"
                lines.append(f"{role}: {msg.get('text', '')}")
            chat_history_section = (
                "Previous conversation (DO NOT repeat questions already asked):\n"
                + "\n".join(lines)
            )
        prompt = FOLLOWUP_PROMPT.format(
            current_json=json.dumps(current_parsed, ensure_ascii=False, indent=2),
            user_msg=user_msg,
            chat_history_section=chat_history_section or "(First message.)",
        )

    try:
        response = await asyncio.to_thread(
            generate_ai_response,
            "You are a helpful B2B sales assistant.",
            prompt,
        )
        if "---" in response:
            reply_part, json_part = response.split("---", 1)
            reply_text = reply_part.strip()
            new_fields = json.loads(_strip_json_fences(json_part))
        else:
            reply_text = response.strip()
            new_fields = {}
        return reply_text, new_fields
    except json.JSONDecodeError:
        return reply_part.strip() if "---" in response else response.strip(), {}
    except Exception as e:
        logger.error("Follow-up parse failed: %s", e)
        return f"⚠️ 解析失敗：{e}", {}


# ---------------------------------------------------------------------------
# Deal creation helper
# ---------------------------------------------------------------------------


async def auto_create_deal(
    intel_id: int, client_id: int, client_name: str, parsed: dict
) -> dict | None:
    """Auto-create a deal from parsed intel. Returns deal dict or None."""
    from services.nexus.deals import create_deal

    pains = parsed.get("pain_points", [])
    pain_labels = [PAIN_LABELS.get(p, p) for p in pains[:2]] if pains else []
    deal_name = client_name
    if pain_labels:
        deal_name += f" — {'、'.join(pain_labels)}"

    budget_amount = None
    budget_range = None
    if parsed.get("budget"):
        try:
            budget_amount = float(parsed["budget"])
            if budget_amount < 100_000:
                budget_range = "<100K"
            elif budget_amount < 500_000:
                budget_range = "100-500K"
            elif budget_amount < 1_000_000:
                budget_range = "500K-1M"
            else:
                budget_range = "1M+"
        except (ValueError, TypeError):
            pass

    try:
        deal = await asyncio.to_thread(
            create_deal,
            name=deal_name,
            client_id=client_id,
            budget_range=budget_range,
            budget_amount=budget_amount,
        )
        await asyncio.to_thread(link_intel_to_deal, deal["id"], intel_id)
        return {"id": deal["id"], "name": deal_name}
    except Exception as e:
        logger.error("Auto-create deal failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Main handlers
# ---------------------------------------------------------------------------


async def handle_capture(
    engine: AssistantEngine,
    session_id: str,
    text: str,
    intent: Intent,
    input_type: str,
    image_bytes: bytes | None = None,
) -> AssistantResponse:
    """Create a new intel and start capture conversation."""
    from services.nexus.assistant.engine import AssistantResponse

    # If there's an active session, auto-done it first
    if engine.sessions.has_active(session_id):
        old_session = engine.sessions.get(session_id)
        if old_session and "role" not in old_session.parsed:
            old_session.parsed["role"] = "client"
        await _finalize_intel(engine, session_id, silent=True)

    has_photo = input_type == "photo"
    raw = text or ("(名片/照片)" if has_photo else "(file)")

    intel = await asyncio.to_thread(create_intel, raw_input=raw, input_type=input_type)
    intel_id = intel["id"]

    # Pre-fill from conversation memory (e.g. company mentioned in prior turn)
    memory_entities = engine.memory.get_recent_entities(session_id, n=6)

    # AI initial parse — vision for photos, text for text
    parsed: dict = {}
    if image_bytes:
        cards = await _parse_business_card(image_bytes, text or "")

        if len(cards) > 1:
            # Multiple cards — create separate intel for extras
            raw_parts = []
            for i, card in enumerate(cards):
                card_label = format_card_raw(card)
                raw_parts.append(f"--- 名片 {i+1} ---\n{card_label}")
            raw = "📇 名片辨識（共 {} 張）\n\n{}".format(
                len(cards), "\n\n".join(raw_parts)
            )
            await asyncio.to_thread(update_intel, intel_id, raw_input=raw)
            parsed = cards[0]

            extra_lines = []
            for card in cards[1:]:
                card_raw = "📇 名片辨識\n" + format_card_raw(card)
                extra_intel = await asyncio.to_thread(
                    create_intel, raw_input=card_raw, input_type="photo"
                )
                await asyncio.to_thread(
                    update_intel,
                    extra_intel["id"],
                    parsed_json=json.dumps(card, ensure_ascii=False),
                )
                name = card.get("contact_name", "?")
                company = card.get("company_name", "")
                extra_lines.append(
                    f"  #{extra_intel['id']} {name}"
                    + (f"（{company}）" if company else "")
                )
        elif len(cards) == 1:
            parsed = cards[0]
            raw = "📇 名片辨識\n" + format_card_raw(parsed)
            await asyncio.to_thread(update_intel, intel_id, raw_input=raw)
    elif text:
        parsed = await _auto_parse(text) or {}

    if parsed:
        _apply_ocr_corrections(parsed)

    # Merge conversation memory entities (only fill gaps, don't overwrite)
    if memory_entities and parsed:
        for key in ("company", "company_name"):
            mem_val = memory_entities.get(key)
            if mem_val and "company_name" not in parsed:
                parsed["company_name"] = mem_val
                break

    # Save parsed to DB
    if parsed:
        await asyncio.to_thread(
            update_intel,
            intel_id,
            parsed_json=json.dumps(parsed, ensure_ascii=False),
        )

    # Check for new industry
    industry_prompt = check_new_industry(parsed) if parsed else None

    # Detect card flow
    is_card = intent == Intent.CAPTURE_CARD and bool(parsed.get("contact_name"))
    card_base = dict(parsed) if is_card else {}

    # Create session
    session = engine.sessions.create(
        session_id,
        intel_id=intel_id,
        parsed=parsed,
        card_base=card_base,
        raw_history=[raw] if text else [],
        input_type=input_type,
        intent=intent,
        pending_industry_confirm=bool(industry_prompt),
        pending_role_confirm=is_card,
    )

    # Build reply
    if is_card:
        reply = (
            f"📇 名片辨識完成！情報 #{intel_id}\n"
            f"📋 {format_summary(parsed)}\n\n"
            f"這位是「客戶」還是「夥伴」？\n"
            f"回覆：客戶 / 夥伴 / 其他"
        )
    else:
        has_missing = bool(missing_fields(parsed))
        reply = format_initial_reply(intel_id, parsed if parsed else None, has_missing)

    if industry_prompt:
        reply += "\n\n" + industry_prompt

    return AssistantResponse(
        text=reply,
        intent=intent,
        parsed_update=parsed,
        intel_id=intel_id,
        card_data=parsed if is_card else None,
    )


async def handle_followup(
    engine: AssistantEngine,
    session_id: str,
    text: str,
) -> AssistantResponse:
    """Process a follow-up message in an active conversation."""
    from services.nexus.assistant.engine import AssistantResponse

    session = engine.sessions.get(session_id)
    if not session or not session.is_active:
        return AssistantResponse(
            text="目前沒有進行中的情報，傳訊息開始新的紀錄！",
            intent=Intent.FOLLOWUP,
        )

    intel_id = session.intel_id

    # --- Handle pending role confirmation (business card flow) ---
    if session.pending_role_confirm:
        low = text.strip().lower()
        role_map = {
            "客戶": "client", "client": "client",
            "夥伴": "partner", "partner": "partner", "合作夥伴": "partner",
            "其他": "other", "other": "other",
            "si": "si", "補助": "subsidy", "subsidy": "subsidy",
        }
        matched_role = role_map.get(low)
        if matched_role:
            session.parsed["role"] = matched_role
            session.pending_role_confirm = False
            await asyncio.to_thread(
                update_intel,
                intel_id,
                parsed_json=json.dumps(session.parsed, ensure_ascii=False),
            )
            role_label = ROLE_LABELS.get(matched_role, matched_role)
            missing = missing_fields(session.parsed)
            missing_labels = [FIELD_LABELS.get(f, f) for f in missing[:3]]
            reply = f"✅ 已設定為「{role_label}」\n📋 {format_summary(session.parsed)}"
            if missing_labels:
                reply += f"\n\n還缺少：{' / '.join(missing_labels)}\n繼續補充或輸入 /done 結束"
            else:
                reply += "\n\n資訊已很完整！輸入 /done 確認，或繼續補充"
            return AssistantResponse(
                text=reply,
                intent=Intent.FOLLOWUP,
                parsed_update={"role": matched_role},
                intel_id=intel_id,
            )
        # Not a recognized role — fall through to normal followup

    # --- Handle pending industry confirmation ---
    if session.pending_industry_confirm:
        low = text.lower().strip()
        current_ind = session.parsed.get("industry", "")
        if low in ("是", "yes", "ok", "確認", "對"):
            session.pending_industry_confirm = False
            await asyncio.to_thread(
                update_intel,
                intel_id,
                parsed_json=json.dumps(session.parsed, ensure_ascii=False),
            )
            return AssistantResponse(
                text=(
                    f"✅ 已確認產業：{get_industry_label(current_ind)}\n\n"
                    f"📋 目前：{format_summary(session.parsed)}\n"
                    f"繼續補充或輸入 /done 結束"
                ),
                intent=Intent.FOLLOWUP,
                intel_id=intel_id,
            )
        elif low in ("否", "no", "不是", "不對"):
            session.parsed.pop("industry", None)
            custom_industries.pop(current_ind, None)
            session.pending_industry_confirm = False
            return AssistantResponse(
                text="好的，請告訴我正確的產業是什麼？",
                intent=Intent.FOLLOWUP,
                intel_id=intel_id,
            )
        else:
            new_key = text.strip().lower().replace(" ", "_")
            custom_industries[new_key] = text.strip()
            session.parsed["industry"] = new_key
            session.pending_industry_confirm = False
            await asyncio.to_thread(
                update_intel,
                intel_id,
                parsed_json=json.dumps(session.parsed, ensure_ascii=False),
            )
            return AssistantResponse(
                text=(
                    f"✅ 已設定產業：{text.strip()}（{new_key}）\n\n"
                    f"📋 目前：{format_summary(session.parsed)}\n"
                    f"繼續補充或輸入 /done 結束"
                ),
                intent=Intent.FOLLOWUP,
                intel_id=intel_id,
            )

    # --- Normal followup ---
    session.raw_history.append(text)

    # Append to raw_input in DB
    full_raw = "\n---\n".join(session.raw_history)
    await asyncio.to_thread(update_intel, intel_id, raw_input=full_raw)

    # AI follow-up parse
    reply_text, new_fields = await _followup_parse(
        session.parsed, text,
        chat_history=session.chat_history,
        intent=session.intent,
    )

    # Track conversation history
    session.chat_history.append({"role": "user", "text": text})
    session.chat_history.append({"role": "ai", "text": reply_text})

    # Merge new fields
    if new_fields:
        _apply_ocr_corrections(new_fields)
        session.merge_fields(new_fields)
    elif session.card_base:
        # Re-merge card_base even without new fields
        session.merge_fields({})

    if new_fields or session.card_base:
        await asyncio.to_thread(
            update_intel,
            intel_id,
            parsed_json=json.dumps(session.parsed, ensure_ascii=False),
        )

    # Check for new industry from follow-up
    industry_prompt = check_new_industry(session.parsed)
    if industry_prompt:
        session.pending_industry_confirm = True

    # Build reply
    lines = [reply_text]
    if session.parsed:
        lines.append(f"\n📋 目前：{format_summary(session.parsed)}")
    if industry_prompt:
        lines.append("\n" + industry_prompt)
    if session.pending_role_confirm:
        lines.append("\n請問這位是「客戶」還是「夥伴」？（客戶 / 夥伴 / 其他）")

    return AssistantResponse(
        text="\n".join(lines),
        intent=Intent.FOLLOWUP,
        parsed_update=new_fields,
        intel_id=intel_id,
    )


async def handle_done(
    engine: AssistantEngine,
    session_id: str,
    silent: bool = False,
) -> AssistantResponse:
    """Finalize the active conversation."""
    from services.nexus.assistant.engine import AssistantResponse

    return await _finalize_intel(engine, session_id, silent=silent)


async def handle_status(
    engine: AssistantEngine,
    session_id: str,
) -> AssistantResponse:
    """Show current conversation status."""
    from services.nexus.assistant.engine import AssistantResponse

    session = engine.sessions.get(session_id)
    if not session or not session.is_active:
        return AssistantResponse(
            text="目前沒有進行中的情報，傳訊息開始新的紀錄！",
            intent=Intent.COMMAND,
        )

    parsed = session.parsed
    missing = missing_fields(parsed)
    missing_labels = [FIELD_LABELS.get(f, f) for f in missing]

    lines = [
        f"📝 情報 #{session.intel_id} 進行中",
        f"📋 {format_summary(parsed)}",
    ]
    if missing_labels:
        lines.append(f"❓ 還缺少：{' / '.join(missing_labels)}")
    else:
        lines.append("✅ 資訊已完整，輸入 /done 確認")

    return AssistantResponse(
        text="\n".join(lines),
        intent=Intent.COMMAND,
        intel_id=session.intel_id,
    )


# ---------------------------------------------------------------------------
# Internal: finalize intel (done flow)
# ---------------------------------------------------------------------------


async def _finalize_intel(
    engine: AssistantEngine,
    session_id: str,
    silent: bool = False,
) -> AssistantResponse:
    """Core done logic — materialize entities, link deals, close session."""
    from services.nexus.assistant.engine import AssistantResponse, _pending_deal
    from services.nexus.materialize import materialize_intel

    session = engine.sessions.close(session_id)
    if not session:
        return AssistantResponse(
            text="目前沒有進行中的情報，傳訊息開始新的紀錄！",
            intent=Intent.COMMAND,
        )

    intel_id = session.intel_id
    parsed = session.parsed

    # Re-merge card_base
    for k, v in session.card_base.items():
        if k not in parsed:
            parsed[k] = v

    parsed_json = json.dumps(parsed, ensure_ascii=False) if parsed else None
    await asyncio.to_thread(confirm_intel, intel_id, parsed_json)

    # Auto-materialize entities
    mat_result = await asyncio.to_thread(materialize_intel, intel_id)

    lines = [
        f"✅ 情報 #{intel_id} 已確認！",
        f"📋 {format_summary(parsed)}" if parsed else "",
    ]
    actions_taken = []

    if mat_result.get("client"):
        c = mat_result["client"]
        action_label = "已建立" if c["action"] == "created" else "已匹配"
        lines.append(f"🔗 {action_label}客戶「{c['name']}」")
    if mat_result.get("partner"):
        p = mat_result["partner"]
        action_label = "已建立" if p["action"] == "created" else "已匹配"
        lines.append(f"🤝 {action_label}夥伴「{p['name']}」")
    if mat_result.get("subsidy"):
        s = mat_result["subsidy"]
        action_label = "已建立" if s["action"] == "created" else "已匹配"
        lines.append(f"📋 {action_label}補助案「{s['name']}」")
    for c in mat_result.get("contacts", []):
        action_label = "已建立" if c["action"] == "created" else "已匹配"
        lines.append(f"👤 {action_label}聯絡人「{c['name']}」")
    if mat_result.get("fields_indexed", 0) > 0:
        lines.append(f"📊 已索引 {mat_result['fields_indexed']} 個欄位")

    # Auto-link to existing deals
    client_info = mat_result.get("client")
    role = parsed.get("role")

    existing_deals = []
    if client_info:
        existing_deals = await asyncio.to_thread(get_deals_by_client, client_info["id"])
    if existing_deals:
        for d in existing_deals:
            try:
                await asyncio.to_thread(link_intel_to_deal, d["id"], intel_id)
            except Exception:
                pass
        deal_names = "、".join(f"「{d['name']}」" for d in existing_deals[:3])
        suffix = f"等 {len(existing_deals)} 筆" if len(existing_deals) > 3 else ""
        lines.append(f"🔗 已自動關聯商機：{deal_names}{suffix}")

    # Deal creation based on deal_potential
    if role == "client" and client_info:
        dp = parsed.get("deal_potential", "")
        if dp in ("high", "medium"):
            deal_result = await auto_create_deal(
                intel_id=intel_id,
                client_id=client_info["id"],
                client_name=client_info["name"],
                parsed=parsed,
            )
            if deal_result:
                lines.append(
                    f"💼 已自動建立商機「{deal_result['name']}」(#{deal_result['id']})"
                )
                lines.append(
                    f"   階段：L0 | 開案潛力：{'高' if dp == 'high' else '中'}"
                )
                actions_taken.append({"type": "create_deal", **deal_result})
        elif dp == "low":
            _pending_deal[session_id] = {
                "intel_id": intel_id,
                "client_id": client_info["id"],
                "client_name": client_info["name"],
                "parsed": parsed,
            }
            lines.append("")
            lines.append(
                f"💼 開案潛力偏低，仍要為「{client_info['name']}」建立新商機嗎？"
            )
            lines.append("回覆「是」建立，或傳新訊息開始下一筆情報")
        elif dp != "none":
            _pending_deal[session_id] = {
                "intel_id": intel_id,
                "client_id": client_info["id"],
                "client_name": client_info["name"],
                "parsed": parsed,
            }
            if not existing_deals:
                lines.append("")
                lines.append(f"💼 要為「{client_info['name']}」建立商機嗎？")
                lines.append("回覆「是」建立，或傳新訊息開始下一筆情報")
            else:
                lines.append("")
                lines.append(
                    "💼 要另外建立新商機嗎？回覆「是」建立，或傳新訊息開始下一筆"
                )
        else:
            lines.append("")
            lines.append("傳新訊息可開始下一筆情報")
    else:
        lines.append("")
        lines.append("傳新訊息可開始下一筆情報")

    if silent:
        contact = parsed.get("contact_name", "")
        company = parsed.get("company_name", "")
        parts = [f"✅ #{intel_id}"]
        if contact:
            parts.append(contact)
        if company:
            parts.append(f"({company})")
        client_info = mat_result.get("client")
        if client_info:
            action = "建立" if client_info["action"] == "created" else "匹配"
            parts.append(f"→ {action}客戶")
        contacts_created = mat_result.get("contacts", [])
        if contacts_created:
            parts.append(f"+ {len(contacts_created)} 聯絡人")
        return AssistantResponse(
            text=" ".join(parts),
            intent=Intent.COMMAND,
            actions_taken=actions_taken,
            intel_id=intel_id,
            session_closed=True,
        )

    return AssistantResponse(
        text="\n".join(line for line in lines if line or line == ""),
        intent=Intent.COMMAND,
        actions_taken=actions_taken,
        intel_id=intel_id,
        session_closed=True,
    )
