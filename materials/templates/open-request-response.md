# 公開徵求回應書

> 標案名稱：{{ title }}
> 標案案號：{{ job_number }}
> 招標機關：{{ agency }}
> 截止日期：{{ deadline }}

---

## 一、基本資訊

| 項目 | 內容 |
|------|------|
| 回應廠商 | {{ company_name }} |
| 統一編號 | {{ company_id }} |
| 負責人 | {{ company_representative }} |
| 聯絡人 | {{ contact_name }} |
| 聯絡電話 | {{ contact_phone }} |
| 電子信箱 | {{ contact_email }} |
| 公司地址 | {{ company_address }} |

---

## 二、公司簡介

{{ company_intro }}

### 核心能力

{{ capabilities }}

### 差異化優勢

{{ differentiators }}

---

## 三、相關實績

{% for case in case_studies %}
### {{ case.client }} — {{ case.title }}

- **產業**: {{ case.industry }}
- **規模**: {{ case.scale }}
- **期間**: {{ case.duration }}
- **成果**: {{ case.outcome }}
- **相關技術**: {{ case.tags }}

{% endfor %}

---

## 四、技術方案

### 4.1 需求理解

{{ requirement_understanding }}

### 4.2 解決方案架構

{{ solution_architecture }}

### 4.3 技術規格

{{ technical_specs }}

### 4.4 系統整合

{{ system_integration }}

### 4.5 資安規劃

{{ security_plan }}

---

## 五、專案團隊

| 角色 | 姓名 | 學經歷 | 負責工作 |
|------|------|--------|----------|
{% for member in team %}
| {{ member.role }} | {{ member.name }} | {{ member.background }} | {{ member.responsibility }} |
{% endfor %}

---

## 六、時程規劃

| 階段 | 工作項目 | 起迄時間 | 交付物 |
|------|----------|----------|--------|
{% for phase in timeline %}
| {{ phase.name }} | {{ phase.tasks }} | {{ phase.period }} | {{ phase.deliverables }} |
{% endfor %}

### 里程碑

{{ milestones }}

---

## 七、費用估算

| 項目 | 說明 | 金額 |
|------|------|------|
{% for item in budget_items %}
| {{ item.name }} | {{ item.description }} | {{ item.amount }} |
{% endfor %}
| **合計** | | **{{ budget_total }}** |

### 付款方式

{{ payment_terms }}

---

## 八、附件清單

{% for attachment in attachments %}
- [ ] {{ attachment.name }} — {{ attachment.description }}
{% endfor %}

---

*本文件由 AI 輔助產生，請務必人工審閱後再行提交。*
