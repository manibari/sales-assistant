# Nexus Data Model

Live schema reference for the Nexus PostgreSQL database. Regenerate after schema
changes using the queries at the bottom.

**Connection (local dev):**

| Field | Value |
|-------|-------|
| Host | `localhost` |
| Port | `5433` (Docker maps `5433→5432`, avoids macOS native postgres) |
| Database | `spms` |
| User | `spms_user` |
| Password | `spms_pass` |

---

## Core Entity Map

```
nx_user (業務 / 技術業務 / PM / CSM)
  │
  ├──< nx_deal.owner_id       (業務)
  ├──< nx_deal.presales_id    (技術業務)
  ├──< nx_project.pm_id       (PM)
  ├──< nx_project.csm_id      (CSM)
  └──< nx_project_member.user_id

nx_client
  │
  ├──< nx_contact                                   (key people)
  ├──< nx_deal ──┬──< nx_document  (rfq/quote/sow/po/contract — deal scope)
  │              ├──< nx_deal_partner >── nx_partner
  │              ├──< nx_deal_intel   >── nx_intel
  │              ├──< nx_meeting
  │              ├──< nx_reminder
  │              ├──< nx_tbd_item
  │              ├──< nx_file         (deal attachments)
  │              │
  │              └──< nx_project ──┬──< nx_project_member
  │                                │
  │                                └──< nx_invoice ──> nx_document (sow_doc_id)
  │                                         │               │
  │                                         └─ milestone_index → SOW milestone_json[i]
  │
  ├──< nx_document           (nda/mou — client scope, no deal_id)
  ├──< nx_file               (client-direct files)
  ├──< nx_plan
  └──< nx_subsidy / nx_tender (opportunity sources)

nx_tag >── nx_entity_tag ──< (polymorphic: client / partner / deal)

nx_knowledge ──> nx_file (parsed content chunks for semantic search)
nx_graph_edge (denormalized relationship graph for D3 viz)
nx_audit_log (financial operations audit trail)
```

---

## Sales → Delivery → Billing Flow

The critical three-stage lifecycle:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SALES (nx_deal)                                          │
│    owner_id (業務)  +  presales_id (技術業務)               │
│    stage: L0 → L1 → ... → L7                                │
│    status: active | hold | closed                           │
│    outcome: won | lost (only when status='closed')          │
└─────────────────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                                  ▼
┌───────────────────┐              ┌───────────────────┐
│ nx_document       │              │ nx_project        │
│ (contract flow)   │              │ (delivery)        │
│                   │              │                   │
│ rfq ──────────┐   │              │ pm_id             │
│ quote ────┐   │   │              │ csm_id            │
│ sow ──┐   │   │   │              │ members[]         │
│ po    │   │   │   │              │ status            │
│ contract──┼───┘   │              │                   │
│       │   │       │              └───────────────────┘
│       │   │       │                      │
│       │   └─ amount (quote 金額)          │
│       │                                   │
│       └─ milestone_json (sow 里程碑陣列)  │
│               [0] 需求確認 20%            │
│               [1] 系統交付 50%            │
│               [2] 驗收   30%              │
│                                           │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. BILLING (nx_invoice)                                     │
│    deal_id + client_id + project_id                         │
│    sow_doc_id       → which SOW                             │
│    milestone_index  → which milestone in sow.milestone_json │
│    status: draft → issued → paid (or cancelled)             │
│    currency: TWD (default)                                  │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** SOW is NOT mutated after creation (contract integrity). Invoices
point at the SOW via `sow_doc_id + milestone_index`. To show "is this milestone
billed?" query invoices, don't write back to SOW.

---

## All Foreign Keys (live from DB)

| From table | From col | → | To table | To col |
|------------|----------|---|----------|--------|
| nx_audit_log | changed_by | → | nx_user | id |
| nx_deal | client_id | → | nx_client | id |
| nx_deal | owner_id | → | nx_user | id |
| nx_deal | presales_id | → | nx_user | id |
| nx_deal_intel | deal_id | → | nx_deal | id |
| nx_deal_intel | intel_id | → | nx_intel | id |
| nx_deal_partner | deal_id | → | nx_deal | id |
| nx_deal_partner | partner_id | → | nx_partner | id |
| nx_document | client_id | → | nx_client | id |
| nx_document | deal_id | → | nx_deal | id |
| nx_email_thread | client_id | → | nx_client | id |
| nx_email_thread | contact_id | → | nx_contact | id |
| nx_email_thread | deal_id | → | nx_deal | id |
| nx_entity_tag | tag_id | → | nx_tag | id |
| nx_file | client_id | → | nx_client | id |
| nx_file | deal_id | → | nx_deal | id |
| nx_file | intel_id | → | nx_intel | id |
| nx_intel | source_contact_id | → | nx_contact | id |
| nx_intel_entity | intel_id | → | nx_intel | id |
| nx_intel_field | intel_id | → | nx_intel | id |
| **nx_invoice** | **client_id** | → | **nx_client** | **id** (required) |
| **nx_invoice** | **created_by** | → | **nx_user** | **id** |
| **nx_invoice** | **deal_id** | → | **nx_deal** | **id** (nullable — "⚠ 無商機" warning in UI) |
| **nx_invoice** | **project_id** | → | **nx_project** | **id** (nullable) |
| **nx_invoice** | **sow_doc_id** | → | **nx_document** | **id** (nullable) |
| nx_knowledge | client_id | → | nx_client | id |
| nx_knowledge | file_id | → | nx_file | id |
| nx_meeting | deal_id | → | nx_deal | id |
| nx_plan | client_id | → | nx_client | id |
| nx_plan | deal_id | → | nx_deal | id |
| **nx_project** | **csm_id** | → | **nx_user** | **id** |
| **nx_project** | **deal_id** | → | **nx_deal** | **id** (required — client derived via JOIN) |
| **nx_project** | **pm_id** | → | **nx_user** | **id** |
| **nx_project_member** | **project_id** | → | **nx_project** | **id** |
| **nx_project_member** | **user_id** | → | **nx_user** | **id** |
| nx_reminder | deal_id | → | nx_deal | id |
| nx_subsidy | client_id | → | nx_client | id |
| nx_subsidy | partner_id | → | nx_partner | id |
| nx_subsidy_client | client_id | → | nx_client | id |
| nx_subsidy_client | subsidy_id | → | nx_subsidy | id |
| nx_subsidy_deadline | subsidy_id | → | nx_subsidy | id |
| nx_subsidy_deal | deal_id | → | nx_deal | id |
| nx_subsidy_deal | subsidy_id | → | nx_subsidy | id |
| nx_tender | client_id | → | nx_client | id |
| nx_tender_deal | deal_id | → | nx_deal | id |
| nx_tender_deal | tender_id | → | nx_tender | id |

**Bold rows = sales/delivery/billing core**.

---

## All nx_* Tables

| Table | Purpose |
|-------|---------|
| `nx_user` | Internal team members (業務 / 技術業務 / PM / CSM / admin) |
| `nx_client` | 客戶 |
| `nx_contact` | 客戶方關鍵人物 |
| `nx_partner` | 合作夥伴（系統整合商、代理商等） |
| `nx_deal` | 商機 (pipeline) |
| `nx_deal_partner` | Deal ↔ Partner 多對多 |
| `nx_deal_intel` | Deal ↔ Intel 多對多 |
| `nx_document` | 文件（NDA/MOU + RFQ/Quote/SOW/PO/Contract） |
| `nx_project` | 交付專案（成交後建立） |
| `nx_project_member` | Project ↔ User 多對多（專案成員） |
| `nx_invoice` | 發票 |
| `nx_file` | 檔案上傳（附件） |
| `nx_knowledge` | 文件解析後的知識片段 (semantic search) |
| `nx_intel` | 情報記錄 |
| `nx_intel_entity` | 情報中提到的實體 |
| `nx_intel_field` | 情報的結構化欄位 |
| `nx_meeting` | 會議紀錄 |
| `nx_reminder` | 商機提醒 |
| `nx_tbd_item` | 商機待確認事項 |
| `nx_tag` | 標籤 |
| `nx_entity_tag` | Tag ↔ (client/partner/deal) polymorphic 關聯 |
| `nx_plan` | 策略計畫 |
| `nx_subsidy` | 政府補助案 |
| `nx_subsidy_client` | Subsidy ↔ Client |
| `nx_subsidy_deal` | Subsidy ↔ Deal |
| `nx_subsidy_deadline` | Subsidy 時程 |
| `nx_tender` | 政府標案 |
| `nx_tender_deal` | Tender ↔ Deal |
| `nx_email_thread` | Email 討論串 |
| `nx_graph_edge` | 關係圖邊（D3 viz 用） |
| `nx_audit_log` | 財務操作稽核紀錄 |
| `nx_integration_config` | 第三方整合設定 |
| `nx_oauth_token` | OAuth token vault |

---

## Useful Queries

### 完整 sales → billing 貫穿

```sql
SELECT
  d.name AS deal,
  c.name AS client,
  owner.name AS sales,
  presales.name AS tech_sales,
  doc.doc_no AS sow_no,
  doc.amount AS sow_amount,
  doc.milestone_json,
  p.name AS project,
  pm.name AS pm,
  i.invoice_no,
  i.amount AS inv_amount,
  i.milestone_index,
  i.status AS inv_status
FROM nx_deal d
JOIN nx_client c ON c.id = d.client_id
LEFT JOIN nx_user owner    ON owner.id    = d.owner_id
LEFT JOIN nx_user presales ON presales.id = d.presales_id
LEFT JOIN nx_document doc  ON doc.deal_id = d.id AND doc.doc_type = 'sow'
LEFT JOIN nx_project p     ON p.deal_id   = d.id
LEFT JOIN nx_user pm       ON pm.id       = p.pm_id
LEFT JOIN nx_invoice i     ON i.sow_doc_id = doc.id
ORDER BY d.id, i.milestone_index;
```

### 每個客戶財務健康

```sql
SELECT
  c.name,
  COUNT(DISTINCT d.id)                                          AS deals,
  COUNT(DISTINCT p.id)                                          AS projects,
  COUNT(DISTINCT i.id)                                          AS invoices,
  COALESCE(SUM(i.amount) FILTER (WHERE i.status = 'paid'), 0)   AS paid,
  COALESCE(SUM(i.amount) FILTER (WHERE i.status = 'issued'), 0) AS outstanding
FROM nx_client c
LEFT JOIN nx_deal    d ON d.client_id    = c.id
LEFT JOIN nx_project p ON p.client_id    = c.id
LEFT JOIN nx_invoice i ON i.client_id    = c.id
GROUP BY c.id, c.name
HAVING COUNT(DISTINCT d.id) > 0
ORDER BY paid DESC;
```

### 每個業務的 pipeline 狀況

```sql
SELECT
  u.name AS sales,
  COUNT(*) FILTER (WHERE d.status = 'active')                           AS active,
  COUNT(*) FILTER (WHERE d.status = 'closed' AND d.outcome = 'won')     AS won,
  COUNT(*) FILTER (WHERE d.status = 'closed' AND d.outcome = 'lost')    AS lost,
  COALESCE(SUM(d.budget_amount) FILTER (WHERE d.status = 'active'), 0)  AS pipeline_value
FROM nx_user u
LEFT JOIN nx_deal d ON d.owner_id = u.id
WHERE u.is_active = true
GROUP BY u.id, u.name
ORDER BY pipeline_value DESC;
```

### SOW milestone 開票進度

```sql
SELECT
  d.name AS deal,
  doc.doc_no AS sow,
  doc.amount AS sow_total,
  jsonb_array_length(doc.milestone_json::jsonb) AS milestone_count,
  COUNT(i.id)                                                AS invoiced_count,
  COALESCE(SUM(i.amount), 0)                                 AS invoiced_amount,
  doc.amount - COALESCE(SUM(i.amount), 0)                    AS remaining
FROM nx_document doc
JOIN nx_deal d ON d.id = doc.deal_id
LEFT JOIN nx_invoice i ON i.sow_doc_id = doc.id
WHERE doc.doc_type = 'sow'
GROUP BY d.id, d.name, doc.id, doc.doc_no, doc.amount, doc.milestone_json
ORDER BY remaining DESC;
```

---

## Regenerating This Doc

After schema changes, re-dump FK list:

```bash
docker exec spms-postgres psql -U spms_user -d spms -c "
SELECT tc.table_name, kcu.column_name, ccu.table_name AS ref_table, ccu.column_name AS ref_col
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name LIKE 'nx_%'
ORDER BY tc.table_name, kcu.column_name;
"
```

Table list:

```bash
docker exec spms-postgres psql -U spms_user -d spms -c "
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE 'nx_%'
ORDER BY table_name;
"
```

---

**Last generated:** 2026-04-09 (after S44 — dropped nx_project.client_id, deal_id now required)
**Tables:** 32 · **FKs:** 46 · **Core flow:** deal → document (SOW) → project → invoice
