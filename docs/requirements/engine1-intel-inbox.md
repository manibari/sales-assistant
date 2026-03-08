# Requirement: Engine 1 — Intel Inbox & Push Cycle

> **Feature**: engine1-intel-inbox
> **Date**: 2026-03-08
> **Status**: Draft
> **Sprint**: S34 (data model) → S35–S38 (features)

---

## Goal

**Who**: B2B solutions sales (one-person operator), orchestrating deals across clients and partners.

**What**: A mobile-first intel ingestion system that replaces notebook + memory with structured, searchable, cross-linkable intelligence — feeding a 2-week push cycle that never lets a deal go cold.

**Why now**: Current workflow (handwritten notes + memory) causes intel to evaporate, follow-ups to slip, and cross-referencing (client pain × partner capability × subsidy) to be impossible.

---

## User Stories

### US-1: Capture intel via photo or text

**As a** sales operator
**I want to** take a photo (business card) or paste text (meeting notes / voice transcript) into the system
**So that** intel is immediately saved without manual data entry

**Acceptance Criteria:**
- [ ] Given a photo of a business card, when submitted, then OCR extracts name, title, company, phone, email and saves as draft intel
- [ ] Given pasted text (meeting notes), when submitted, then AI parses people, orgs, pain points, timelines and saves as draft intel
- [ ] Given any input, when submitted, then the raw input is preserved alongside parsed results
- [ ] Given a network error during AI parsing, when submitted, then raw input is still saved (parse later)

### US-2: Card-based Q&A to enrich intel

**As a** sales operator
**I want to** answer one question at a time via tappable cards (not forms) after initial capture
**So that** I can quickly categorize intel with my thumbs

**Acceptance Criteria:**
- [ ] Given saved intel, when Q&A starts, then system asks "role?" with tap options: client / partner / SI / other
- [ ] Given role = partner, when continuing, then system asks: capabilities (multi-select), industry experience (multi-select)
- [ ] Given role = client, when continuing, then system asks: industry, pain points (AI-suggested based on industry), NDA/MOU status
- [ ] Given any question, when user taps "skip for now", then the question becomes a TBD item linked to this contact/org
- [ ] Given all questions answered or skipped, when flow ends, then intel status changes from draft to confirmed

### US-3: TBD tracking from skipped questions

**As a** sales operator
**I want to** skipped Q&A items to automatically become "must ask next meeting" items
**So that** nothing falls through the cracks

**Acceptance Criteria:**
- [ ] Given a skipped question, when saved, then a TBD item is created linked to the relevant contact/org
- [ ] Given a TBD item exists, when viewing pre-meeting prep, then TBD items appear in the suggested questions list
- [ ] Given a TBD item is resolved (answered), when updated, then it is marked complete and removed from active list

### US-4: 2-week push cycle reminders

**As a** sales operator
**I want to** be reminded which cases need pushing based on a 2-week rhythm
**So that** no active case goes cold

**Acceptance Criteria:**
- [ ] Given an active case with last activity > 14 days, when viewing dashboard, then it appears in "needs pushing" section
- [ ] Given an active case, when longer idle, then reminder priority increases (never auto-closes)
- [ ] Given a case, when client explicitly declines, then case status = closed (only way to close)

### US-5: Pre-meeting preparation pack

**As a** sales operator
**I want to** see a consolidated prep pack before each meeting
**So that** I walk in prepared with context, open items, and suggested questions

**Acceptance Criteria:**
- [ ] Given a client/partner, when viewing prep pack, then it shows: all TBD items, MEDDIC progress, NDA/MOU status, recent intel history
- [ ] Given TBD items from skipped questions, when viewing prep pack, then they appear as "suggested questions"
- [ ] Given NDA/MOU approaching expiry, when viewing prep pack, then a warning is shown

### US-6: NDA / MOU document tracking

**As a** sales operator
**I want to** track NDA and MOU with sign date, expiry date, and file attachment
**So that** I know the legal status of every client relationship

**Acceptance Criteria:**
- [ ] Given a new client, when created, then NDA and MOU tracking entries are auto-created with status = pending
- [ ] Given NDA/MOU, when user uploads signed doc, then sign date is recorded and file is stored
- [ ] Given NDA/MOU with expiry date, when expiry is within 30 days, then system shows warning
- [ ] Given a client who says NDA/MOU not needed, when user marks "not required", then tracking stops for that item

### US-7: Partner management with trust verification

**As a** sales operator
**I want to** track partners separately from clients, with capability tags and trust levels
**So that** I can quickly find the right partner for a deal

**Acceptance Criteria:**
- [ ] Given a new partner, when created, then trust level defaults to "unverified"
- [ ] Given a partner, when trust level is updated (unverified → testing → verified → core team), then it is recorded with date
- [ ] Given a partner, when viewing their profile, then capabilities, strengths, weaknesses, industry experience, and collaboration history are visible
- [ ] Given a deal that needs specific capabilities, when searching partners, then system filters by capability tags + trust level

### US-8: Tag system for cross-referencing

**As a** sales operator
**I want to** tag entities (clients, partners, intel) with categories (pain point, capability, industry, solution)
**So that** the system can cross-reference and surface matches

**Acceptance Criteria:**
- [ ] Given any entity, when tagging, then user can select from existing tags or create new ones
- [ ] Given AI-parsed intel, when saved, then AI suggests relevant tags
- [ ] Given a tag search (e.g., "pain_point:energy efficiency"), when queried, then all entities with that tag are returned
- [ ] Given tags accumulate over time, when AI parses new intel, then tag suggestions improve

### US-9: Push dashboard ("this week's pushes")

**As a** sales operator
**I want to** see a single dashboard showing what needs attention this week
**So that** I start each day knowing exactly what to do

**Acceptance Criteria:**
- [ ] Given active cases, when viewing dashboard, then cases are sorted by urgency (days since last activity, TBD count, document warnings)
- [ ] Given recent intel entries, when viewing dashboard, then they appear in a "recent intel" feed
- [ ] Given items needing supplementation (skipped Q&A), when viewing dashboard, then they appear in "needs your input" section

### US-10: Deal (商機) lifecycle management

**As a** sales operator
**I want to** create, view, update, and close deals that connect clients + partners + intel
**So that** I have a single place to track every opportunity end-to-end

**Acceptance Criteria:**
- [ ] Given an intel entry about a client, when tapping "建立商機", then a deal is created pre-filled with client + pain points
- [ ] Given a new deal, when created, then it defaults to stage L0 (潛在) and appears in the pipeline
- [ ] Given the pipeline view, when toggling view mode, then user can switch between urgency sort (by idle days) and stage grouping (collapsible sections)
- [ ] Given a deal, when advancing stage, then MEDDIC gate check runs — missing items block advancement with clear feedback
- [ ] Given a deal, when client explicitly declines, then deal can be closed with reason + notes (only closure path)
- [ ] Given a closed deal, when viewing pipeline, then it appears greyed out and filterable

### US-11: Calendar integration

**As a** sales operator
**I want to** manage meetings and reminders in an in-app calendar linked to deals
**So that** I don't need to context-switch to external apps

**Acceptance Criteria:**
- [ ] Given the calendar tab, when opened, then a month view shows dates with dot indicators for events
- [ ] Given a date with events, when tapped, then a day view shows: meetings (blue), push reminders (amber), expiry warnings (red)
- [ ] Given a new meeting, when created, then it must be linked to a deal and can include participants from contacts
- [ ] Given a scheduled meeting, when tapped, then it shows a pre-meeting prep pack (TBDs, MEDDIC, documents, suggested questions, intel history)
- [ ] Given a completed meeting, when tapping "記錄會議結果", then intel entry flow starts (same as Flow 1) and results auto-update TBDs + MEDDIC

### US-12: File upload with AI parsing

**As a** sales operator
**I want to** upload proposal decks and documents to a deal via Google Drive link or device file
**So that** the system archives files AND extracts key info (solution, pricing, ROI) automatically

**Acceptance Criteria:**
- [ ] Given a deal detail page, when tapping "+ 新增文件", then user can choose: paste Google Drive URL or pick file from device
- [ ] Given a Google Drive URL, when submitted, then system fetches the file via API; shows error if permission denied or invalid link
- [ ] Given a device file (PDF/PPT/PPTX/DOCX), when selected, then file is uploaded and stored
- [ ] Given an uploaded PPT/PDF, when processed, then AI parses: solution summary, pricing (if present), expected ROI, key specs/timeline
- [ ] Given AI parse results, when shown, then user can edit/confirm before saving
- [ ] Given a parsed file, when viewing deal detail or pre-meeting prep, then parsed summary is visible with "已解析" badge
- [ ] Given a contract file (NDA/MOU), when uploaded, then it auto-links to document tracking and updates sign status

### US-13: Global search

**As a** sales operator
**I want to** search across deals, intel, and contacts from any screen
**So that** I can quickly find relevant information without navigating through tabs

**Acceptance Criteria:**
- [ ] Given any screen, when tapping the search bar, then a search overlay appears
- [ ] Given a search query, when submitted, then results are grouped by: deals, intel, contacts
- [ ] Given a search result, when tapped, then user navigates to the detail page of that entity

### US-14: Intel-to-deal association

**As a** sales operator
**I want to** link intel entries to existing deals (or create new ones)
**So that** all intelligence is organized around the deals they support

**Acceptance Criteria:**
- [ ] Given a new intel entry, when Q&A is complete, then AI suggests 1-3 potentially related deals
- [ ] Given suggested deals, when user selects one, then the intel is linked and appears in that deal's detail page
- [ ] Given no matching deal, when user chooses "建立新商機", then deal creation flow starts pre-filled
- [ ] Given unlinked intel, when viewing intel feed, then it shows an "unlinked" indicator; user can manually link later

---

## Scope Boundary

| In Scope | Out of Scope |
|----------|-------------|
| Intel ingestion (photo + text) | Voice recording / Whisper integration |
| AI parsing (text → structured data) | AI training / fine-tuning |
| Card-based Q&A (mobile-first) | Native iOS/Android app (PWA is fine) |
| Client & partner management (separate) | Merging with legacy CRM tables |
| Tag system (pain points, capabilities, industry) | Full ontology / knowledge graph |
| TBD tracking | External calendar sync (Google/Apple) |
| In-app calendar (meetings + reminders) | Push notifications (app-only for now) |
| File upload (Google Drive + device) | Video file processing |
| AI parsing of presentations (PPT/PDF) | Contract clause analysis |
| Global search across entities | Full-text search in file contents |
| 2-week push reminders | Email/SMS notifications (dashboard only) |
| NDA/MOU tracking (date, expiry, file) | Contract clause analysis |
| Pre-meeting prep pack | Auto-generated slide decks |
| Push dashboard | Engine 2 (new business radar, subsidy matching) |
| New clean schema | Backward compatibility with Streamlit/legacy services |
| FastAPI + Next.js | Streamlit new features |

---

## Data Model (S34 Deliverable)

Core entities to design in S34:

| Entity | Purpose |
|--------|---------|
| `client` | Client orgs — industry, pain points, budget range |
| `partner` | Partner orgs — capabilities, trust level, strengths/weaknesses |
| `contact` | People — linked to client or partner, with role |
| `intel` | Raw + parsed intelligence entries |
| `tag` | Universal tags with categories |
| `tbd_item` | Skipped questions + meeting action items |
| `document` | NDA/MOU tracking with dates and files |
| `deal` | Where client + partner(s) come together — the core entity |
| `deal_partner` | Many-to-many: deal × partner |
| `deal_intel` | Many-to-many: deal × intel |
| `meeting` | Calendar events linked to deals |
| `reminder` | Push/follow-up reminders on calendar |
| `file` | Uploaded files (proposals, contracts) with AI parse results |

---

## Sprint Mapping

| Sprint | Scope |
|--------|-------|
| **S34** | Schema design (all entities) + FastAPI routes + basic CRUD |
| **S35** | Intel inbox MVP (capture → AI parse → card Q&A → save) |
| **S36** | Deal pipeline (CRUD + views + MEDDIC gating + partner matching) |
| **S37** | Calendar (meetings + reminders + prep pack + post-meeting flow) |
| **S38** | File upload (Google Drive + device) + AI parse + document tracking |
| **S39** | Push dashboard + auto-reminders + global search |
