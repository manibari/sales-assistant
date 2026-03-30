"""Nexus Graph Agentic — tool-calling agent that queries the knowledge graph.

The agent runs a loop (max MAX_ROUNDS rounds) calling registered tools,
then synthesizes a final answer from collected context.
"""

import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MAX_ROUNDS = 5

# ---------------------------------------------------------------------------
# Tool definitions (OpenAI-style function schema)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "function": {
            "name": "get_client_graph",
            "description": (
                "Get the knowledge graph subgraph for a specific client: "
                "all linked deals, intel, plans, and knowledge chunks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "The nx_client.id of the client.",
                    }
                },
                "required": ["client_id"],
            },
        }
    },
    {
        "function": {
            "name": "semantic_search",
            "description": (
                "Search intel and knowledge chunks by semantic similarity. "
                "Use this when looking for relevant information by topic or keyword."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The natural language query to search for.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default 5, max 10).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }
    },
    {
        "function": {
            "name": "get_deal_context",
            "description": "Get full context for a deal: details, MEDDIC, and linked intel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deal_id": {
                        "type": "integer",
                        "description": "The nx_deal.id of the deal.",
                    }
                },
                "required": ["deal_id"],
            },
        }
    },
    {
        "function": {
            "name": "list_recent_intel",
            "description": "List recent intelligence entries, optionally filtered by client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Look back this many days (default 30).",
                        "default": 30,
                    },
                    "client_id": {
                        "type": "integer",
                        "description": "Optional: filter by nx_client.id.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 10).",
                        "default": 10,
                    },
                },
                "required": [],
            },
        }
    },
]

# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def _handle_get_client_graph(client_id: int) -> dict:
    from services.nexus.graph import get_client_subgraph
    from database.connection import get_connection

    subgraph = get_client_subgraph(client_id)

    # Enrich with deal names
    deal_ids = [e["to_id"] for e in subgraph["deals"]]
    deals = []
    if deal_ids:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, stage, status, budget_range FROM nx_deal WHERE id = ANY(%s)",
                    (deal_ids,),
                )
                cols = [d[0] for d in cur.description]
                deals = [dict(zip(cols, row)) for row in cur.fetchall()]

    # Enrich with intel titles
    intel_ids = [e["to_id"] for e in subgraph["intel"]]
    intels = []
    if intel_ids:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, status, created_at FROM nx_intel WHERE id = ANY(%s)",
                    (intel_ids,),
                )
                cols = [d[0] for d in cur.description]
                intels = [dict(zip(cols, row)) for row in cur.fetchall()]

    return {
        "client_id": client_id,
        "deals": deals,
        "intel": intels,
        "plan_count": len(subgraph["plans"]),
        "knowledge_count": len(subgraph["knowledge"]),
    }


def _handle_semantic_search(query: str, top_k: int = 5) -> list[dict]:
    from services.nexus.embedding import semantic_search
    from database.connection import get_connection

    top_k = min(top_k, 10)

    # Fetch intel with embeddings
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, raw_input, status, embedding
                   FROM nx_intel
                   WHERE embedding IS NOT NULL
                   ORDER BY created_at DESC
                   LIMIT 200"""
            )
            cols = [d[0] for d in cur.description]
            intel_rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    # Fetch knowledge with embeddings
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT k.id, k.content, k.summary, k.client_id, k.embedding,
                          f.file_name
                   FROM nx_knowledge k
                   LEFT JOIN nx_file f ON k.file_id = f.id
                   WHERE k.embedding IS NOT NULL
                   ORDER BY k.created_at DESC
                   LIMIT 200"""
            )
            cols = [d[0] for d in cur.description]
            knowledge_rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    # Tag source type
    for r in intel_rows:
        r["_source_type"] = "intel"
        r["_text"] = r.get("title") or r.get("raw_input", "")[:200]
    for r in knowledge_rows:
        r["_source_type"] = "knowledge"
        r["_text"] = r.get("summary") or r.get("content", "")[:200]

    candidates = intel_rows + knowledge_rows
    if not candidates:
        return []

    results = semantic_search(query, candidates, top_k=top_k)
    # Return lightweight version
    return [
        {
            "source_type": r["_source_type"],
            "id": r["id"],
            "text": r["_text"],
            "score": round(r.get("_score", 0), 4),
        }
        for r in results
    ]


def _handle_get_deal_context(deal_id: int) -> dict:
    from services.nexus.deals import get_deal, get_deal_intel

    deal = get_deal(deal_id)
    if not deal:
        return {"error": f"Deal #{deal_id} not found"}

    intels = get_deal_intel(deal_id)
    return {
        "deal": {
            "id": deal["id"],
            "name": deal["name"],
            "stage": deal["stage"],
            "status": deal["status"],
            "budget_range": deal.get("budget_range"),
            "timeline": deal.get("timeline"),
            "meddic": deal.get("meddic_json"),
            "client_name": deal.get("client_name"),
        },
        "intel": [
            {
                "id": i["intel_id"],
                "title": i.get("title"),
                "raw_input": (i.get("raw_input") or "")[:500],
                "status": i.get("status"),
            }
            for i in intels
        ],
    }


def _handle_list_recent_intel(
    days: int = 30,
    client_id: int | None = None,
    limit: int = 10,
) -> list[dict]:
    from database.connection import get_connection

    limit = min(limit, 50)
    params: list = [days, limit]
    client_clause = ""
    if client_id:
        client_clause = """
            AND EXISTS (
                SELECT 1 FROM nx_intel_entity ie
                WHERE ie.intel_id = i.id
                  AND ie.entity_type = 'client'
                  AND ie.entity_id = %s
            )"""
        params.insert(1, client_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT id, title, raw_input, status, created_at
                    FROM nx_intel i
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    {client_clause}
                    ORDER BY created_at DESC
                    LIMIT %s""",
                params,
            )
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    return [
        {
            "id": r["id"],
            "title": r.get("title"),
            "snippet": (r.get("raw_input") or "")[:200],
            "status": r.get("status"),
            "created_at": str(r.get("created_at", "")),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

_HANDLERS = {
    "get_client_graph": lambda args: _handle_get_client_graph(**args),
    "semantic_search": lambda args: _handle_semantic_search(**args),
    "get_deal_context": lambda args: _handle_get_deal_context(**args),
    "list_recent_intel": lambda args: _handle_list_recent_intel(**args),
}


def _dispatch(tool_name: str, arguments: dict):
    handler = _HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return handler(arguments)
    except Exception as e:
        logger.warning("Tool %s failed: %s", tool_name, e)
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Agent result
# ---------------------------------------------------------------------------


@dataclass
class AgentResult:
    answer: str
    sources: list[dict] = field(default_factory=list)
    tool_calls_log: list[dict] = field(default_factory=list)
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """你是 Project Nexus 的 AI 銷售顧問。
你有工具可以查詢知識圖譜、情報資料庫、和案件資訊。
回答問題時，請先使用工具查詢相關資料，再根據查到的資料給出具體、有證據的回答。
請使用繁體中文回答。若沒有相關資料，請坦誠說明。"""


def run_agent(
    question: str,
    session_id: str | None = None,
) -> AgentResult:
    """Run the graph-agentic loop.

    Args:
        question: User's natural language question.
        session_id: Optional session identifier for logging.

    Returns:
        AgentResult with answer, sources, and tool call log.
    """
    import time
    from services.ai_provider import generate_ai_with_tools

    start = time.time()
    messages = [{"role": "user", "content": question}]
    tool_calls_log: list[dict] = []
    sources: list[dict] = []

    for round_num in range(MAX_ROUNDS):
        try:
            resp = generate_ai_with_tools(
                system_prompt=SYSTEM_PROMPT,
                messages=messages,
                tools=TOOL_SCHEMAS,
            )
        except Exception as e:
            logger.error("Agent AI call failed (round %d): %s", round_num, e)
            return AgentResult(
                answer=f"AI 呼叫失敗：{e}",
                tool_calls_log=tool_calls_log,
                duration_ms=int((time.time() - start) * 1000),
            )

        tool_calls = resp.get("tool_calls", [])
        text_content = resp.get("content")

        if not tool_calls:
            # No more tool calls — final answer
            answer = text_content or "（無法生成回答）"
            break

        # Execute each tool call and append results to messages
        tool_results = []
        for tc in tool_calls:
            name = tc["name"]
            args = tc["arguments"]
            logger.info("Agent tool call: %s(%s)", name, args)
            result = _dispatch(name, args)
            tool_calls_log.append({"tool": name, "args": args, "result_summary": str(result)[:300]})

            # Collect sources from semantic_search results
            if name == "semantic_search" and isinstance(result, list):
                sources.extend(result[:5])

            tool_results.append({"tool": name, "result": result})

        # Append assistant's tool call message and tool results
        tool_result_text = json.dumps(tool_results, ensure_ascii=False, indent=2)
        messages.append({"role": "assistant", "content": text_content or ""})
        messages.append({
            "role": "user",
            "content": f"工具查詢結果：\n{tool_result_text}\n\n請根據以上資料回答原始問題。",
        })

    else:
        # Reached max rounds without a final text answer
        answer = text_content or "已達最大工具呼叫輪數，無法完成回答。"

    duration_ms = int((time.time() - start) * 1000)
    return AgentResult(
        answer=answer,
        sources=sources,
        tool_calls_log=tool_calls_log,
        duration_ms=duration_ms,
    )
