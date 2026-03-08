# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Project Nexus (太陽型戰略控制台)
**Generated:** 2026-03-08
**Category:** Mobile-first B2B Sales Intel App
**Theme:** Dark / Light (toggleable, dark default)
**Stack:** Next.js 15 + React 19 + TypeScript + Tailwind CSS

---

## Design Philosophy

**Personal command center** — not an enterprise SaaS.
One operator, moving fast, mostly on phone, sometimes on laptop.

| Principle | Meaning |
|-----------|---------|
| **Mobile-first** | Design for 375px thumb operation, scale up to desktop |
| **Cards, not forms** | One question per screen, tap to answer, swipe to progress |
| **Dark by default** | Dark background, high-contrast text, colored accents for status |
| **Glanceable** | Dashboard shows urgency in 2 seconds — color + number + icon |
| **Touch-friendly** | Minimum 44x44px touch targets, 8px gap between targets |
| **Progressive disclosure** | Show what matters now, reveal details on tap |

---

## Color Palette (Dark / Light)

Implementation: Tailwind `dark:` variant + `class` strategy on `<html>`.
Default = dark. Toggle persisted to `localStorage`.

### Semantic Tokens

| Role | Dark | Light | Tailwind |
|------|------|-------|----------|
| **Background** | `slate-950` | `slate-50` | `bg-slate-50 dark:bg-slate-950` |
| **Surface** | `slate-900` | `white` | `bg-white dark:bg-slate-900` |
| **Surface Raised** | `slate-800` | `slate-100` | `bg-slate-100 dark:bg-slate-800` |
| **Border** | `slate-700` | `slate-200` | `border-slate-200 dark:border-slate-700` |
| **Text Primary** | `slate-50` | `slate-900` | `text-slate-900 dark:text-slate-50` |
| **Text Secondary** | `slate-400` | `slate-500` | `text-slate-500 dark:text-slate-400` |
| **Text Muted** | `slate-500` | `slate-400` | `text-slate-400 dark:text-slate-500` |

### Accent Colors (same in both themes)

| Role | Hex | Tailwind | Usage |
|------|-----|----------|-------|
| **CTA / Primary** | `#3B82F6` | `blue-500` | Primary actions, links |
| **CTA Hover** | `#2563EB` | `blue-600` | Button hover states |
| **Success** | `#22C55E` | `green-500` | Completed, signed, verified |
| **Warning** | `#F59E0B` | `amber-500` | Expiring, needs attention |
| **Danger** | `#EF4444` | `red-500` | Overdue, critical |
| **Info** | `#06B6D4` | `cyan-500` | New intel, informational |

### Status Color System

| Status | Color | Use Case |
|--------|-------|----------|
| Active / On track | `green-500` | MEDDIC complete, NDA signed |
| Needs attention | `amber-500` | TBDs pending, idle 7-14 days |
| Overdue / Critical | `red-500` | Idle >14 days, NDA expiring |
| New / Info | `cyan-500` | Recent intel, new contact |
| Inactive / Closed | `slate-600` | Client declined |

---

## Typography

- **Font:** Inter (single font, all weights)
- **Mood:** Clean, functional, professional
- **Google Fonts:** `Inter:wght@400;500;600;700`

| Element | Size (mobile) | Size (desktop) | Weight | Tailwind |
|---------|---------------|----------------|--------|----------|
| Page title | 20px | 24px | 700 | `text-xl md:text-2xl font-bold` |
| Card title | 16px | 18px | 600 | `text-base md:text-lg font-semibold` |
| Body | 14px | 16px | 400 | `text-sm md:text-base` |
| Label | 12px | 14px | 500 | `text-xs md:text-sm font-medium` |
| Caption | 11px | 12px | 400 | `text-[11px] md:text-xs` |
| Number (stat) | 28px | 32px | 700 | `text-[28px] md:text-[32px] font-bold` |

---

## Spacing & Layout

### Mobile Layout (default)

```
┌──────────────────────────┐
│  Status Bar              │
├──────────────────────────┤
│  Top Bar (page title)    │  h-14, px-4
├──────────────────────────┤
│                          │
│  Content (scrollable)    │  px-4, pb-20
│                          │
│                          │
├──────────────────────────┤
│  Bottom Nav (4 tabs)     │  h-16, fixed bottom
│  Home | Intel | Clients  │
│       | Partners         │
└──────────────────────────┘
        ＋ FAB button (bottom-right, above nav)
```

### Desktop Layout (md+)

```
┌────────┬─────────────────────────────────┐
│ Sidebar│  Top Bar                        │
│  w-64  ├─────────────────────────────────┤
│        │                                 │
│  Nav   │  Content (max-w-4xl mx-auto)    │
│  links │                                 │
│        │                                 │
│        │                                 │
└────────┴─────────────────────────────────┘
```

### Spacing Scale

| Token | Tailwind | Usage |
|-------|----------|-------|
| 4px | `p-1` | Icon internal padding |
| 8px | `p-2, gap-2` | Between touch targets, inline gaps |
| 12px | `p-3` | Card internal padding (compact) |
| 16px | `p-4` | Standard content padding |
| 20px | `p-5` | Card padding |
| 24px | `p-6` | Section spacing |
| 32px | `p-8` | Between sections |

---

## Component Specs

### Theme Toggle

```
Position: Top bar, right side (Sun/Moon icon)
Tailwind: p-2 rounded-lg text-slate-500 dark:text-slate-400
          hover:bg-slate-100 dark:hover:bg-slate-800
          transition-colors duration-200 cursor-pointer
Icon: Sun (dark mode active) / Moon (light mode active)
Persist: localStorage key = "theme", values = "dark" | "light"
Default: "dark"
```

### Cards (primary UI element)

```
Tailwind: bg-white dark:bg-slate-900
          border border-slate-200 dark:border-slate-700
          rounded-xl p-5 transition-colors duration-200 cursor-pointer
          hover:border-slate-300 dark:hover:border-slate-600
          active:bg-slate-50 dark:active:bg-slate-800
```

Card types:
- **Case card** (dashboard): org name, TBD count badge, status color left border
- **Intel card** (feed): title, summary, tags, timestamp
- **Q&A card** (capture flow): question + tappable option buttons, full-width

### Q&A Option Buttons (card-based Q&A)

```
Tailwind: bg-slate-100 dark:bg-slate-800
          border border-slate-200 dark:border-slate-700 rounded-lg
          min-h-[44px] px-4 py-3 text-sm font-medium
          text-slate-900 dark:text-slate-50
          transition-colors duration-200 cursor-pointer
          hover:border-blue-500 hover:bg-slate-200 dark:hover:bg-slate-750
          active:bg-blue-500/20 active:border-blue-500
          selected: border-blue-500 bg-blue-500/10 text-blue-500 dark:text-blue-400
```

Layout: 2-column grid, `grid grid-cols-2 gap-2`
Multi-select: show checkmark icon when selected

### Tags / Badges

```
Tailwind: inline-flex items-center px-2.5 py-1 rounded-full
          text-xs font-medium

Colors by category:
  pain_point:  bg-red-500/10 text-red-400 border border-red-500/20
  capability:  bg-blue-500/10 text-blue-400 border border-blue-500/20
  industry:    bg-amber-500/10 text-amber-400 border border-amber-500/20
  solution:    bg-green-500/10 text-green-400 border border-green-500/20
```

### Status Badges

```
Signed/Complete:  bg-green-500/10 text-green-400
Pending:          bg-amber-500/10 text-amber-400
Overdue:          bg-red-500/10 text-red-400
Not Required:     bg-slate-700 text-slate-400
```

### FAB (Floating Action Button)

```
Tailwind: fixed bottom-20 right-4 md:bottom-8 md:right-8
          w-14 h-14 rounded-full bg-blue-500
          flex items-center justify-center
          shadow-lg shadow-blue-500/25
          active:scale-95 transition-transform duration-150
```

### Bottom Navigation (mobile only)

```
Tailwind: fixed bottom-0 inset-x-0 h-16
          bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm
          border-t border-slate-200 dark:border-slate-800
          grid grid-cols-4

Tab item: flex flex-col items-center justify-center gap-1
          text-[11px] text-slate-400 dark:text-slate-500
          active: text-blue-500 dark:text-blue-400
```

### Inputs

```
Tailwind: w-full bg-slate-100 dark:bg-slate-800
          border border-slate-200 dark:border-slate-700 rounded-lg
          px-4 py-3 text-base text-slate-900 dark:text-slate-50
          placeholder:text-slate-400 dark:placeholder:text-slate-500
          focus:border-blue-500 focus:ring-1 focus:ring-blue-500
          focus:outline-none transition-colors duration-200
```

Font size = 16px minimum (prevents iOS zoom on focus).

### Buttons

```
Primary:   bg-blue-500 hover:bg-blue-600 text-white font-semibold
           px-6 py-3 rounded-lg min-h-[44px]
           active:scale-[0.98] transition-all duration-200

Secondary: bg-slate-100 dark:bg-slate-800
           hover:bg-slate-200 dark:hover:bg-slate-700
           text-slate-700 dark:text-slate-200
           border border-slate-200 dark:border-slate-700 font-medium
           px-6 py-3 rounded-lg min-h-[44px]

Ghost:     text-slate-500 dark:text-slate-400
           hover:text-slate-700 dark:hover:text-slate-200 font-medium
           px-4 py-3 min-h-[44px]

Skip:      text-slate-400 dark:text-slate-500
           hover:text-slate-600 dark:hover:text-slate-300 text-sm
           py-2 (right-aligned, subtle)
```

---

## Icon System

- **Library:** Lucide React (`lucide-react`)
- **Size:** 20px default, 24px for nav, 16px for inline
- **Stroke:** 1.5px
- **No emojis as UI icons**

Key icons:
| Action | Icon |
|--------|------|
| Add intel | `Plus` |
| Camera | `Camera` |
| Client | `Building2` |
| Partner | `Handshake` |
| Intel | `Zap` |
| TBD | `CircleDot` |
| NDA/MOU | `FileCheck` |
| Push reminder | `Clock` |
| Meeting prep | `ClipboardList` |
| Tag | `Tag` |
| Search | `Search` |
| Back | `ChevronLeft` |
| Skip | `ChevronRight` |
| Check | `Check` |
| Warning | `AlertTriangle` |

---

## Motion & Animation

| Interaction | Duration | Easing |
|-------------|----------|--------|
| Button press | 150ms | `ease-out` |
| Card hover/active | 200ms | `ease-in-out` |
| Page transition | 300ms | `ease-out` |
| Skeleton shimmer | 1.5s | `linear` (infinite) |
| Number count-up | 500ms | `ease-out` |

Always respect `prefers-reduced-motion`: disable transforms and use opacity/color only.

---

## Anti-Patterns (Do NOT Use)

- No emojis as icons — use Lucide SVGs
- No purple/pink AI gradients
- No playful/rounded "SaaS" aesthetic
- No layout-shifting hover transforms (scale)
- No forms with 5+ fields on one screen
- No hardcoded dark/light colors — always use `dark:` variant pairs
- No hamburger menu on mobile (use bottom nav)
- No instant state changes — always transition
- No font size < 16px on inputs (iOS zoom)
- No touch targets < 44px

---

## Pre-Delivery Checklist

- [ ] All color classes use `dark:` variant pairs (no hardcoded theme colors)
- [ ] Theme toggle works and persists to localStorage
- [ ] Both themes pass contrast checks (4.5:1 minimum)
- [ ] All icons from Lucide React, consistent 20px size
- [ ] `cursor-pointer` on all clickable elements
- [ ] Touch targets minimum 44x44px, 8px gap between
- [ ] Text contrast minimum 4.5:1 against dark background
- [ ] Focus states visible (ring-2 ring-blue-500)
- [ ] `prefers-reduced-motion` respected
- [ ] Mobile-first: works at 375px, no horizontal scroll
- [ ] Responsive breakpoints: 375px → 768px → 1024px → 1440px
- [ ] No content hidden behind bottom nav (pb-20)
- [ ] Input font-size >= 16px (no iOS zoom)
- [ ] Transitions 150-300ms on interactive elements
- [ ] `overscroll-behavior: contain` on scrollable areas
