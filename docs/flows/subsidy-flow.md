# User Flow: 補助案模組

## Flow 1: 瀏覽 + 建立補助案 (US-1, US-2)

```mermaid
flowchart TD
    A[Sidebar: 點擊「補助案」] --> B[補助案列表頁]
    B --> C{選擇 View}
    C -->|階段| D[按階段分組顯示]
    C -->|截止日| E[按截止日排序]
    D --> F{使用者動作}
    E --> F
    F -->|點擊卡片| G[補助案詳情頁]
    F -->|點擊「+ 新增」| H[新增補助案頁]
    H --> I[填寫表單]
    I --> J{計畫名稱已填?}
    J -->|否| K[顯示必填提示]
    K --> I
    J -->|是| L[POST /api/nx/subsidies/]
    L --> M{API 成功?}
    M -->|是| G
    M -->|否| N[顯示錯誤訊息]
    N --> I
```

## Flow 2: 編輯 + 階段管理 (US-3, US-4)

```mermaid
flowchart TD
    A[補助案詳情頁] --> B{使用者動作}
    B -->|點擊可編輯欄位| C[切換為 input/textarea]
    C --> D{按鍵}
    D -->|Enter / 點擊 ✓| E[PATCH /api/nx/subsidies/:id]
    D -->|Escape / 點擊 ✕| F[取消, 恢復原值]
    E --> G{API 成功?}
    G -->|是| H[刷新頁面資料]
    G -->|否| I[顯示錯誤]
    I --> C
    F --> A
    H --> A

    B -->|點擊 Pipeline Bar 階段| J{目標階段合法?}
    J -->|是| K[POST /api/nx/subsidies/:id/advance]
    J -->|否| L[無動作]
    K --> M{當前在「審查中」?}
    M -->|是, 選核定| N[stage = approved]
    M -->|是, 選未通過| O[stage = rejected]
    M -->|否| P[推進到下一階段]
    N --> H
    O --> H
    P --> H
```

## Flow 3: 連結商機 + 客戶 + 夥伴 (US-5, US-6)

```mermaid
flowchart TD
    A[補助案詳情頁] --> B{使用者動作}

    B -->|點擊「+ 連結商機」| C[顯示商機選擇 dropdown]
    C --> D[選擇商機]
    D --> E[POST /api/nx/subsidies/:id/deals]
    E --> F{API 成功?}
    F -->|是| G[刷新已連結商機列表]
    F -->|否| H[顯示錯誤]

    B -->|點擊已連結商機名稱| I[導向 /deals/:dealId]

    B -->|點擊已連結商機的 ✕| J[DELETE /api/nx/subsidies/:id/deals/:dealId]
    J --> G

    B -->|設定申請客戶| K[選擇客戶 dropdown]
    K --> L[PATCH client_id]
    L --> G

    B -->|設定合作夥伴| M[選擇夥伴 dropdown]
    M --> N[PATCH partner_id]
    N --> G

    B -->|點擊客戶/夥伴名稱| O[導向 /contacts/clients/:id 或 partners/:id]
```

## Flow 4: Telegram 情報自動建立 (US-7)

```mermaid
flowchart TD
    A[Telegram: 使用者傳送補助案情報] --> B[AI 解析 parsed_json, role=subsidy]
    B --> C[使用者回覆 /done]
    C --> D[confirm_intel]
    D --> E[materialize_intel]
    E --> F{parsed.role == subsidy?}
    F -->|否| G[跳過補助案建立]
    F -->|是| H[搜尋同名 nx_subsidy]
    H --> I{找到匹配?}
    I -->|是| J[link_intel_entity, relation=mentioned]
    I -->|否| K[create_subsidy 建立記錄]
    K --> L[link_intel_entity, relation=created_from]
    J --> M[回覆 Telegram: 已匹配/建立補助案 XXX]
    L --> M
    M --> N{詢問是否建立商機?}
    N -->|是| O[進入 deal creation flow]
    N -->|否| P((結束))
```

## Flow 5: 文件管理 (US-8)

```mermaid
flowchart TD
    A[補助案詳情頁] --> B{使用者動作}
    B -->|點擊「+ 新增文件」| C[開啟 FileUploadModal]
    C --> D{選擇上傳方式}
    D -->|貼連結| E[填入 URL + 文件名稱]
    D -->|選擇檔案| F[選擇本地檔案 + 填文件名稱]
    E --> G[POST /api/nx/documents/files]
    F --> H[POST /api/nx/documents/files/upload]
    G --> I{成功?}
    H --> I
    I -->|是| J[關閉 modal, 刷新文件列表]
    I -->|否| K[顯示錯誤]
    K --> C

    B -->|點擊文件名稱| L{外部連結?}
    L -->|是| M[新分頁開啟 URL]
    L -->|否| N[下載檔案]

    B -->|點擊文件 ✏️ 改名| O[inline 編輯名稱]
    O --> P[PATCH /api/nx/documents/files/:id]
    P --> J
```

## Flow 6: 全域搜尋 (US-9)

```mermaid
flowchart TD
    A[任何頁面: 搜尋列] --> B[輸入關鍵字]
    B --> C[GET /api/nx/search?q=...]
    C --> D[搜尋結果頁]
    D --> E{結果包含補助案?}
    E -->|是| F[顯示補助案區塊]
    E -->|否| G[不顯示補助案區塊]
    F --> H{點擊補助案項目}
    H --> I[導向 /subsidies/:id]
```

## Screen Inventory

| # | Screen | Route | Purpose | Key Elements |
|---|--------|-------|---------|-------------|
| 1 | 補助案列表 | `/subsidies` | 瀏覽所有補助案 | View 切換 (stage/deadline), SubsidyCard, + 新增按鈕, 到期警示 |
| 2 | 新增補助案 | `/subsidies/new` | 建立新補助案 | 表單: name(必填), agency, program_type, deadline, funding_amount, eligibility, scope, required_docs, reference_url, client selector, partner selector |
| 3 | 補助案詳情 | `/subsidies/[id]` | 查看/編輯補助案 | Pipeline bar, inline edit fields, linked deals, linked client/partner, files, related intel |
| 4 | 商機詳情 (修改) | `/deals/[id]` | 顯示關聯補助案 | 新增「補助案」區塊在右欄 |
| 5 | 客戶詳情 (修改) | `/contacts/clients/[id]` | 顯示關聯補助案 | 新增「相關補助案」區塊在右欄 |
| 6 | 搜尋結果 (修改) | `/search` or inline | 包含補助案結果 | 新增 subsidies 結果區塊 |

### Reusable Components

| Component | Reuse From | Used In |
|-----------|-----------|---------|
| TopBar | existing | 列表, 詳情, 新增 |
| FileUploadModal | existing | 詳情頁 |
| Inline edit (editField/editValue) | deals/[id] pattern | 詳情頁 |
| Pipeline bar | deals/[id] stage bar | 詳情頁 |
| SubsidyCard | new (similar to DealCard) | 列表頁 |
