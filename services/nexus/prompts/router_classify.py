"""Intent classification prompt — used by LLM-based router."""

from services.nexus.prompts._base import JSON_ONLY_INSTRUCTION

INTENT_CLASSIFY_PROMPT = f"""你是 B2B 業務助理的意圖分類器。根據使用者輸入，判斷他想做什麼。

可能的意圖：
- CAPTURE_VISIT: 回報拜訪筆記（"今天去了XX公司"、"拜訪現場"）
- CAPTURE_MEETING: 回報會議內容（"跟XX開會，談了..."）
- CAPTURE_LEAD: 回報商機線索（"XX想做..."、"XX需要..."）
- CAPTURE_CARD: 名片辨識（照片）
- CAPTURE_SUBSIDY: 補助資訊回報
- CAPTURE_GENERAL: 其他情報回報
- QUERY_CLIENT: 查詢客戶資料（"查 XX"、"XX 怎樣"、"XX 最近如何"）
- QUERY_DEAL: 查詢商機（"案子進度"、"XX 的商機"）
- QUERY_TENDER: 查詢標案（"最近有什麼標案"）
- QUERY_SUBSIDY: 查詢補助（"有什麼補助"）
- QUERY_SCHEDULE: 查看行程（"今天有什麼行程"、"這週會議"、"明天的行程"）
- QUERY_GENERAL: 其他查詢
- ACTION_CREATE_MEETING: 要新增/建立行程或會議（"增加行程"、"排會議"、"約XX開會"、"加一個行程"、"新增會議"）
- ACTION_CREATE_DEAL: 要建立商機（"幫XX建案子"）
- ACTION_CREATE_REMINDER: 設提醒（"提醒我..."）
- ACTION_UPDATE_DEAL: 更新商機資訊（"改預算"、"更新時程"）
- ACTION_GENERATE_PITCH: 產生說帖（"幫我寫說帖"）

關鍵區分規則：
- "今天有什麼行程" → QUERY_SCHEDULE（查看既有行程）
- "我要增加今天的行程" → ACTION_CREATE_MEETING（新增行程）
- "查 美珍香" → QUERY_CLIENT（查詢客戶）
- "美珍香想做 AOI" → CAPTURE_LEAD（回報線索）
- "跟台積電開會談了預算" → CAPTURE_MEETING（回報會議結果）
- "排明天下午兩點跟台積電開會" → ACTION_CREATE_MEETING（安排新會議）

判斷「查看」vs「新增」的關鍵：
- 含有「有什麼」「有哪些」「列出」→ 查看（QUERY）
- 含有「增加」「加」「新增」「排」「安排」「約」「建」→ 新增（ACTION）

{JSON_ONLY_INSTRUCTION}

回覆格式：
{{"intent": "INTENT_NAME", "entities": {{"company": "公司名(若有)", "date": "日期(若有)", "time": "時間(若有)", "title": "標題/描述(若有)"}}}}

entities 中只放你有信心提取到的欄位，沒有的不要放。
"""
