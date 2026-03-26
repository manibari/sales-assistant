"""TENDER_GENERATE_PROMPT — generate complete tender response documents.

Originally defined in backend/routers/nexus/tenders.py:215.
Template variables: {tender_info}, {response_data}, {company_materials}, {template}
"""

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
