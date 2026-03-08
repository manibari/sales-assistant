# User Flow: Engine 1 — Intel Inbox & Push Cycle

> **Date**: 2026-03-08
> **Requirement**: `docs/requirements/engine1-intel-inbox.md`

---

## Flow 1: Intel Capture (情報收件)

The primary daily action — dump intel, system structures it.

```mermaid
flowchart TD
    A["📱 Open App"] --> B["Home Dashboard"]
    B --> C["Tap ＋ (FAB button)"]
    C --> D{"Input Method"}

    D -->|"Camera"| E["Take Photo (business card)"]
    D -->|"Text"| F["Paste / Type text"]

    E --> G["AI OCR + Parse"]
    F --> G

    G --> H{"Parse OK?"}
    H -->|"Yes"| I["Show parsed result card\n(name, org, phone, email)"]
    H -->|"No / Partial"| J["Show raw input\n+ partial parse\n+ Edit button"]

    J --> K["User edits manually"]
    K --> I

    I --> L["✅ Auto-saved as draft"]
    L --> M["Q&A Card 1:\nRole?\n[Client] [Partner] [SI] [Other]"]

    M -->|"Client"| N["CLIENT BRANCH"]
    M -->|"Partner"| O["PARTNER BRANCH"]
    M -->|"SI / Other"| P["Tag only → Done"]
    M -->|"Skip"| Q["Create TBD:\n'Confirm role'\n→ Done"]

    %% === CLIENT BRANCH ===
    N --> N1["Q&A Card 2:\nIndustry?\n[Food] [Petrochem] [Semi] [Mfg] [+Custom]"]
    N1 -->|"Selected"| N2["Q&A Card 3:\nKnown pain points?\n(AI suggests based on industry)\n[Select multiple] [+Custom]"]
    N1 -->|"Skip"| N1S["TBD: 'Ask industry'"]
    N1S --> N2

    N2 -->|"Selected"| N3["Q&A Card 4:\nNDA status?\n[Not started] [In progress] [Signed] [Not needed]"]
    N2 -->|"Skip"| N2S["TBD: 'Identify pain points'"]
    N2S --> N3

    N3 --> N4["Q&A Card 5:\nMOU status?\n[Not started] [In progress] [Signed] [Not needed]"]
    N4 --> N5["Q&A Card 6:\nBudget range?\n[<100K] [100K-500K] [500K-1M] [1M+] [Unknown]"]
    N5 --> DONE["✅ Confirmed\nIntel + Contact + Client saved"]

    %% === PARTNER BRANCH ===
    O --> O1["Q&A Card 2:\nCapabilities?\n(multi-select)\n[IoT] [Vision] [ERP] [AutoCtrl] [Security] [ML/AI] [+Custom]"]
    O1 -->|"Selected"| O2["Q&A Card 3:\nIndustry experience?\n(multi-select)\n[Food] [Petrochem] [Semi] [Mfg] [+Custom]"]
    O1 -->|"Skip"| O1S["TBD: 'Confirm capabilities'"]
    O1S --> O2

    O2 -->|"Selected"| O3["Q&A Card 4:\nTeam size?\n[1-10] [10-50] [50-200] [200+]"]
    O2 -->|"Skip"| O2S["TBD: 'Ask industry experience'"]
    O2S --> O3

    O3 --> O4["Q&A Card 5:\nFirst impression / notes?\n(free text, optional)"]
    O4 --> DONE2["✅ Confirmed\nIntel + Contact + Partner saved\nTrust = Unverified"]

    %% Styling
    style L fill:#2d5a3d,stroke:#4ade80
    style DONE fill:#2d5a3d,stroke:#4ade80
    style DONE2 fill:#2d5a3d,stroke:#4ade80
    style Q fill:#5a4a2d,stroke:#fbbf24
    style N1S fill:#5a4a2d,stroke:#fbbf24
    style N2S fill:#5a4a2d,stroke:#fbbf24
    style O1S fill:#5a4a2d,stroke:#fbbf24
    style O2S fill:#5a4a2d,stroke:#fbbf24
```

---

## Flow 2: Two-Week Push Cycle (推進循環)

The recurring rhythm — system drives, user executes.

```mermaid
flowchart TD
    A["📱 Open App"] --> B["Home Dashboard"]

    B --> C{"Any cases\n> 14 days idle?"}
    C -->|"Yes"| D["🔴 'Needs Pushing' section\nCases sorted by idle days"]
    C -->|"No"| E["🟢 All on track"]

    D --> F["Tap a case card"]
    F --> G["Pre-Meeting Prep Pack"]

    G --> G1["📋 TBD Items\n(from skipped Q&A +\nprevious meetings)"]
    G --> G2["📊 MEDDIC Progress\n3/6 completed"]
    G --> G3["📄 NDA/MOU Status\nNDA: Signed ✓\nMOU: Pending ⚠️"]
    G --> G4["💡 Suggested Questions\n(auto-generated from TBDs\n+ MEDDIC gaps)"]
    G --> G5["📝 Intel History\n(all past notes for\nthis client)"]

    G1 --> H["User reviews prep"]
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H

    H --> I["Go to meeting"]
    I --> J["Post-meeting:\nTap ＋ → enter new intel"]
    J --> K["AI parses meeting notes"]

    K --> L{"TBDs resolved?"}
    L -->|"Yes"| M["Mark TBDs complete"]
    L -->|"Partial"| N["Keep open TBDs\n+ add new ones"]
    L -->|"No"| O["All TBDs carry forward"]

    M --> P{"Client says\nnot interested?"}
    N --> P
    O --> P

    P -->|"Yes"| R["Close case ⚫\n(only way to close)"]
    P -->|"No"| S["Case stays active\n→ Next 2-week cycle"]
    S --> B

    style D fill:#5a2d2d,stroke:#f87171
    style E fill:#2d5a3d,stroke:#4ade80
    style R fill:#3d3d3d,stroke:#9ca3af
    style S fill:#2d4a5a,stroke:#60a5fa
```

---

## Flow 3: Partner Trust Progression (夥伴信任升級)

```mermaid
flowchart LR
    A["Unverified\n(剛認識)"] -->|"Assign small\ntest project"| B["Testing\n(小案驗證中)"]
    B -->|"Delivered well"| C["Verified\n(已驗證)"]
    B -->|"Failed / unreliable"| D["Demoted\n(不推薦)"]
    C -->|"Multiple successful\ncollaborations"| E["Core Team\n(核心班底)"]

    A -->|"Bind under\nlarge SI"| F["SI-Backed\n(SI 擔保)"]
    F -->|"Direct collaboration\nproven"| C

    style A fill:#5a4a2d,stroke:#fbbf24
    style B fill:#2d4a5a,stroke:#60a5fa
    style C fill:#2d5a3d,stroke:#4ade80
    style D fill:#5a2d2d,stroke:#f87171
    style E fill:#1a4a1a,stroke:#22c55e
    style F fill:#3d3d5a,stroke:#a78bfa
```

---

## Flow 4: NDA/MOU Lifecycle (文件追蹤)

```mermaid
flowchart TD
    A["New Client Created"] --> B["Auto-create:\nNDA = Pending\nMOU = Pending"]

    B --> C{"Client says\nnot needed?"}
    C -->|"Yes"| D["Mark: Not Required"]
    C -->|"No"| E["Status: Pending"]

    E --> F["User uploads\nsigned doc"]
    F --> G["Status: Signed\nRecord sign date\n+ expiry date"]

    G --> H{"Expiry within\n30 days?"}
    H -->|"Yes"| I["⚠️ Warning on\ndashboard + prep pack"]
    H -->|"No"| J["✅ Valid"]

    I --> K["User renews\nor extends"]
    K --> G

    style D fill:#3d3d3d,stroke:#9ca3af
    style G fill:#2d5a3d,stroke:#4ade80
    style I fill:#5a4a2d,stroke:#fbbf24
```

---

## Screen Inventory

| # | Screen | Purpose | Key Elements |
|---|--------|---------|-------------|
| 1 | **Home Dashboard** | Daily command center | Needs-pushing cards, recent intel feed, needs-input section, FAB (+) button |
| 2 | **Intel Capture** | Input raw intel | Camera button, text area, submit |
| 3 | **Parse Result** | Show AI-parsed output | Parsed card (editable), edit button, auto-save indicator |
| 4 | **Q&A Cards** | Step-by-step enrichment | One question per screen, tappable options, skip button, progress dots |
| 5 | **Client Detail** | Client profile & history | Industry, pain points, NDA/MOU status, intel history, TBD list, MEDDIC |
| 6 | **Partner Detail** | Partner profile & trust | Capabilities, trust level, strengths/weaknesses, collaboration history |
| 7 | **Pre-Meeting Prep** | Consolidated meeting prep | TBDs, MEDDIC progress, NDA/MOU, suggested questions, intel history |
| 8 | **Client List** | Browse/search clients | Filter by industry, tag, idle days; sort by urgency |
| 9 | **Partner List** | Browse/search partners | Filter by capability, trust level, industry |
| 10 | **Intel Feed** | Chronological intel history | All intel entries, filterable by client/partner/tag |
| 11 | **TBD List** | All open action items | Grouped by client/partner, sortable by age |
| 12 | **Document Tracker** | NDA/MOU overview | Status badges, expiry warnings, upload buttons |
