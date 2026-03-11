description: Research a government subsidy program and add it to the Nexus database
argument-hint: <subsidy name or URL>

Given the user's input "$ARGUMENTS" (a subsidy program name, URL, or description):

## Step 1: Research

- If input is a URL: WebFetch the URL and extract all subsidy details
- If input is text: WebSearch for the program, then WebFetch the most relevant result page
- Extract these fields (Traditional Chinese government subsidy context):
  - name: 計畫全名
  - agency: 主辦機關
  - program_type: one of "sbir", "siir", "local", "other"
  - funding_amount: 補助額度 (keep original text, e.g. "最高1,000萬元")
  - eligibility: 申請資格
  - scope: 申請範疇
  - required_docs: 申請文件
  - deadline: 申請截止說明 (original text)
  - deadline_date: ISO date if parseable (convert 民國年 to 西元, e.g. 115年→2026)
  - reference_url: source URL
  - notes: any extra info (contact, review criteria, etc.)

## Step 2: Confirm with user

- Present findings in a summary table using this format:

| 欄位 | 內容 |
|------|------|
| 計畫名稱 | ... |
| 主辦機關 | ... |
| 類型 | sbir / siir / local / other |
| 補助額度 | ... |
| 申請資格 | ... |
| 申請範疇 | ... |
| 申請文件 | ... |
| 截止說明 | ... |
| 截止日期 | YYYY-MM-DD or N/A |
| 參考連結 | ... |
| 備註 | ... |

- Ask user to confirm or adjust before creating

## Step 3: Create record

- After user confirms, run Python to call `create_subsidy()` from `services/nexus/subsidies.py`:

```python
import sys
sys.path.insert(0, "/Users/manibari/Documents/Projects/sales-assistant")
from services.nexus.subsidies import create_subsidy, update_subsidy

result = create_subsidy(
    name="...",
    program_type="...",
    agency="...",
    funding_amount="...",
    eligibility="...",
    scope="...",
    required_docs="...",
    deadline="...",
    reference_url="...",
    notes="...",
)
subsidy_id = result["id"]

# If deadline_date was extracted, update it separately
# update_subsidy(subsidy_id, deadline_date="YYYY-MM-DD")

print(f"Created subsidy #{subsidy_id}: {result['name']}")
```

- Report the created subsidy ID and name

## Important

- 回覆使用繁體中文
- If info is insufficient or program not found, report what was found and ask user for guidance
- Do NOT fabricate data — only use information found from web sources
- For 民國年 conversion: 民國 + 1911 = 西元 (e.g. 115年 = 2026年)
