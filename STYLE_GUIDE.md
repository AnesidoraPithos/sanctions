# ClearView — Style Guide

> Entity Due Diligence Portal for Government Staff

---

## 1. Design Philosophy

ClearView is built for **trust, clarity, and authority**. Every design decision serves government compliance analysts who need to make high-stakes decisions quickly and accurately. The interface prioritizes **information density without clutter**, **clear visual hierarchy**, and **unambiguous risk communication**.

**Core Principles:**
- **Institutional confidence** — The UI should feel like a tool built by and for professionals. No playful flourishes.
- **Scanability** — Analysts review dozens of entities daily. Key data must be extractable at a glance.
- **Risk-first communication** — Risk levels must be the most visually prominent data point on any screen.
- **Restraint** — Color is used sparingly and purposefully. When color appears, it carries meaning.

---

## 2. Color System

All colors are defined as HSL values in CSS custom properties. Components must **never** use raw color values — always reference design tokens.

### 2.1 Core Palette

| Token                  | HSL Value          | Usage                                      |
|------------------------|--------------------|---------------------------------------------|
| `--background`         | `220 20% 97%`     | Page background. Light warm gray.           |
| `--foreground`         | `220 30% 12%`     | Primary text. Near-black with blue undertone.|
| `--surface-elevated`   | `0 0% 100%`       | Cards, panels, table backgrounds.           |
| `--header-bg`          | `220 60% 15%`     | Top navigation bar. Deep navy.              |
| `--header-foreground`  | `210 40% 98%`     | Text/icons on the header.                   |

### 2.2 Brand Colors

| Token                      | HSL Value          | Usage                                  |
|----------------------------|--------------------|----------------------------------------|
| `--primary`                | `220 60% 22%`     | Primary actions, links, active states. Dark navy. |
| `--primary-foreground`     | `210 40% 98%`     | Text on primary-colored surfaces.      |
| `--secondary`              | `220 14% 92%`     | Secondary surfaces, subtle backgrounds.|
| `--secondary-foreground`   | `220 30% 18%`     | Text on secondary surfaces.            |
| `--accent`                 | `38 92% 50%`      | Amber/gold. Used sparingly for emphasis.|
| `--accent-foreground`      | `38 95% 14%`      | Text on accent surfaces.               |

### 2.3 Risk Colors

These are the most critical colors in the system. They must **only** be used to communicate risk levels — never for decorative purposes.

| Token                      | HSL Value          | Visual       | Usage                              |
|----------------------------|--------------------|--------------|-------------------------------------|
| `--risk-high`              | `0 72% 51%`       | 🔴 Red       | High risk. Sanctions matches, PEP flags, critical findings. |
| `--risk-high-foreground`   | `0 0% 100%`       | White        | Text on high-risk badges.          |
| `--risk-medium`            | `38 92% 50%`      | 🟡 Amber     | Medium risk. Partial matches, minor flags, enhanced due diligence. |
| `--risk-medium-foreground` | `38 95% 14%`      | Dark amber   | Text on medium-risk badges.        |
| `--risk-low`               | `142 64% 36%`     | 🟢 Green     | Low risk. Cleared entities, no findings. |
| `--risk-low-foreground`    | `0 0% 100%`       | White        | Text on low-risk badges.           |
| `--risk-unknown`           | `220 10% 58%`     | ⚪ Gray      | Pending/unknown. Screening in progress. |
| `--risk-unknown-foreground`| `0 0% 100%`       | White        | Text on unknown-risk badges.       |

### 2.4 Utility Colors

| Token                      | HSL Value          | Usage                                  |
|----------------------------|--------------------|----------------------------------------|
| `--muted`                  | `220 14% 94%`     | Muted backgrounds, table header rows.  |
| `--muted-foreground`       | `220 10% 46%`     | Secondary text, labels, metadata.      |
| `--border`                 | `220 16% 88%`     | All borders — cards, tables, dividers. |
| `--input`                  | `220 16% 88%`     | Input field borders.                   |
| `--ring`                   | `220 60% 22%`     | Focus rings on interactive elements.   |
| `--destructive`            | `0 84.2% 60.2%`   | Destructive actions (delete, remove).  |

---

## 3. Typography

### 3.1 Font Families

| Role       | Font                         | CSS Variable       | Usage                                      |
|------------|------------------------------|---------------------|--------------------------------------------|
| **Display**| Source Serif 4 (600, 700)    | `--font-display`    | Page titles, section headings, stat values. |
| **Body**   | Inter (400, 500, 600, 700)   | `--font-body`       | Body text, labels, buttons, table content.  |

The serif display font establishes **institutional gravitas** — reminiscent of government documents and legal filings. The sans-serif body font ensures **readability** in data-dense contexts.

### 3.2 Type Scale

| Element              | Size    | Weight    | Font     | Tailwind Class                          |
|----------------------|---------|-----------|----------|-----------------------------------------|
| Page title (H1)      | 2rem–2.5rem | Bold (700) | Display | `text-3xl md:text-4xl font-display font-bold` |
| Section heading (H2) | 1.25rem | Semibold (600) | Display | `text-xl font-display font-semibold`   |
| Card heading (H3)    | 0.875rem| Semibold (600) | Body    | `text-sm font-semibold`                |
| Body text             | 0.875rem| Regular (400) | Body   | `text-sm`                               |
| Table header          | 0.75rem | Medium (500) | Body   | `text-xs font-medium uppercase tracking-wider` |
| Badge text            | 0.75rem | Semibold (600) | Body  | `text-xs font-semibold uppercase tracking-wide` |
| Caption / metadata    | 0.75rem | Regular (400) | Body   | `text-xs text-muted-foreground`         |
| Stat value            | 1.5rem  | Semibold (600) | Display | `text-2xl font-semibold font-display`  |

### 3.3 Typography Rules

- **Never use font sizes below `text-xs` (0.75rem).** Accessibility minimum.
- **Uppercase is reserved for:** table headers, badge labels, and status indicators.
- **Letter spacing (`tracking-wider`)** accompanies all uppercase text for legibility.
- **Line height:** Use `leading-relaxed` for paragraph text in report sections.

---

## 4. Spacing & Layout

### 4.1 Grid System

- **Max content width:** `max-w-7xl` (80rem / 1280px)
- **Horizontal padding:** `px-6` (1.5rem) on all main containers
- **Centered layout:** `mx-auto` on all content containers

### 4.2 Spacing Scale

| Context                    | Value     | Tailwind    |
|----------------------------|-----------|-------------|
| Between major sections     | 2.5rem    | `py-10`     |
| Between cards in a grid    | 1rem      | `gap-4`     |
| Card internal padding      | 1.25rem–1.5rem | `p-5` or `p-6` |
| Between heading and content| 0.75rem   | `mb-3`      |
| Table cell padding         | 1.25rem h / 0.875rem v | `px-5 py-3.5` |
| Icon-to-text gap           | 0.5rem–0.625rem | `gap-2` or `gap-2.5` |

### 4.3 Responsive Breakpoints

| Breakpoint | Width   | Behavior                                           |
|------------|---------|-----------------------------------------------------|
| Mobile     | < 640px | Single column. Hide jurisdiction, analyst columns.  |
| Tablet (sm)| 640px+  | Show "last checked" column.                         |
| Desktop (md)| 768px+ | Two-column grid for screening cards. Show jurisdiction. |
| Large (lg) | 1024px+ | Show analyst column in table.                       |

---

## 5. Components

### 5.1 Risk Badge

The most important component in the system. Communicates entity risk level.

```
┌──────────────┐
│  HIGH RISK   │  ← Red background, white text, rounded-md
└──────────────┘
```

**Specifications:**
- Border radius: `rounded-md`
- Padding: `px-2.5 py-1`
- Text: `text-xs font-semibold uppercase tracking-wide`
- Colors: Determined by `risk-badge-{level}` utility classes

**Variants:** `high` | `medium` | `low` | `unknown`

**Usage rules:**
- Always use the `<RiskBadge>` component — never construct manually.
- Never modify risk badge colors for "aesthetic" reasons.
- Risk badges are **read-only indicators**, never interactive.

### 5.2 Cards (Surface Elevated)

All content panels use the elevated surface pattern:

```
┌─────────────────────────────────────┐
│  🔒 Section Title                   │  ← Icon + semibold heading
│                                     │
│  Status badge                       │  ← Risk-colored status
│  Description text in muted color... │
└─────────────────────────────────────┘
```

**Specifications:**
- Background: `bg-surface-elevated`
- Border: `border border-border` (default) or `border-risk-high/30` (alert state)
- Border radius: `rounded-lg`
- Shadow: `shadow-sm`
- Padding: `p-5` (standard) or `p-6` (hero cards)

### 5.3 Data Table

Used for entity listings with sortable, scannable rows.

**Header row:**
- Background: `bg-muted/50`
- Text: `text-xs font-medium text-muted-foreground uppercase tracking-wider`
- Padding: `px-5 py-3`

**Body rows:**
- Hover state: `hover:bg-muted/30`
- Cursor: `cursor-pointer` (when clickable)
- Border: `border-b border-border` between rows, none on last
- Transition: `transition-colors`

### 5.4 Search Bar

Full-width search input with icon prefix.

**Specifications:**
- Height: `h-12`
- Background: `bg-surface-elevated`
- Border: `border border-input`
- Focus: `focus:ring-2 focus:ring-ring focus:shadow-md`
- Icon: `Search` from lucide-react, positioned `left-4`, colored `text-muted-foreground`
- Text: `text-sm font-body`
- Placeholder: `text-muted-foreground`

### 5.5 Stat Cards

Dashboard statistics with icon + number + label.

```
┌─────────────────────┐
│  📄  24              │  ← Icon in muted bg + large number
│      Active Cases    │  ← Small label
└─────────────────────┘
```

- Icon container: `bg-muted rounded-lg p-2.5`
- Number: `text-2xl font-semibold font-display`
- Label: `text-xs text-muted-foreground`

### 5.6 Risk Score Gauge

Semi-circular gauge visualization for entity risk scores (0–100).

- **0–39:** Green arc
- **40–69:** Amber arc  
- **70–100:** Red arc
- Needle rotates proportionally
- Score displayed as large number below gauge

### 5.7 Buttons

| Variant   | Usage                                    | Style                                        |
|-----------|------------------------------------------|----------------------------------------------|
| `default` | Primary actions                          | Navy background, white text                  |
| `outline` | Secondary actions (Print, Export)         | Border only, background on hover             |
| `ghost`   | Tertiary/icon-only actions (header icons)| No border, subtle hover background           |
| `link`    | Navigation within text                   | Underline on hover, primary color            |

**Sizes:** `default` (h-10), `sm` (h-9), `lg` (h-11), `icon` (h-10 w-10)

---

## 6. Iconography

**Library:** Lucide React (`lucide-react`)

### 6.1 Icon Assignments

| Icon             | Usage                                    |
|------------------|------------------------------------------|
| `Shield`         | App logo / brand mark                    |
| `Building2`      | Corporation entity type                  |
| `User`           | Individual entity type                   |
| `Search`         | Search input                             |
| `Clock`          | Timestamps, "last checked"               |
| `ArrowLeft`      | Back navigation                          |
| `ArrowRight`     | Row navigation indicator                 |
| `AlertTriangle`  | PEP screening, warnings                  |
| `ShieldAlert`    | Sanctions screening                      |
| `ShieldCheck`    | Recommendations, clearance               |
| `Newspaper`      | Adverse media                            |
| `DollarSign`     | Financial records                        |
| `Database`       | Database hits section                    |
| `FileText`       | Active cases / reports                   |
| `CheckCircle`    | Cleared / approved                       |
| `Download`       | Export actions                           |
| `Printer`        | Print actions                            |
| `Bell`           | Notifications                            |

### 6.2 Icon Sizing

| Context                | Size         | Tailwind        |
|------------------------|--------------|-----------------|
| Header / brand         | 24px         | `h-6 w-6`       |
| Card section icon      | 18px         | `h-4.5 w-4.5`   |
| Table row icon         | 16px         | `h-4 w-4`       |
| Inline metadata icon   | 14px         | `h-3.5 w-3.5`   |

---

## 7. Interaction Patterns

### 7.1 Hover States

- **Table rows:** `bg-muted/30` background transition
- **Header buttons:** `bg-header-foreground/10`
- **Links/back navigation:** `text-muted-foreground → text-foreground`
- **All transitions:** `transition-colors` (default 150ms)

### 7.2 Focus States

- **Inputs:** `ring-2 ring-ring` + `shadow-md`
- **Buttons:** `ring-2 ring-ring ring-offset-2`

### 7.3 Navigation

- **Search → Report:** Form submission navigates to `/report/:entityName`
- **Table row → Report:** Click navigates to `/report/:entityName`
- **Back button:** Returns to dashboard (`/`)

---

## 8. Content Guidelines

### 8.1 Voice & Tone

- **Formal and precise.** No colloquialisms.
- **Actionable.** Recommendations use imperative mood: "DO NOT PROCEED", "PROCEED WITH CAUTION", "CLEARED FOR ENGAGEMENT".
- **Objective.** Report language avoids judgment — states facts and matches.

### 8.2 Risk Language

| Risk Level | Recommendation Prefix    | Tone                   |
|------------|--------------------------|------------------------|
| High       | `DO NOT PROCEED`         | Urgent, directive      |
| Medium     | `PROCEED WITH CAUTION`   | Advisory, measured     |
| Low        | `CLEARED FOR ENGAGEMENT` | Confirmatory, routine  |
| Unknown    | `PENDING`                | Neutral, informational |

### 8.3 Database Match Types

Always display match type alongside source:
- **Exact match** — Direct name/ID correspondence
- **Partial match** — Substring or fuzzy match requiring verification
- **Alias match** — Match via known alias or alternate name

---

## 9. Accessibility

- **Minimum contrast ratio:** 4.5:1 for body text, 3:1 for large text
- **Risk communication:** Never rely on color alone — risk badges include text labels ("HIGH RISK", "LOW RISK")
- **Focus indicators:** Visible ring on all interactive elements
- **Semantic HTML:** `<table>` for tabular data, `<header>` for navigation, `<section>` for content regions
- **Font minimum:** 12px (0.75rem) — no smaller text anywhere
- **Touch targets:** Minimum 40px height on interactive elements

---

## 10. File Structure

```
src/
├── components/
│   ├── AppHeader.tsx        # Top navigation bar
│   ├── SearchBar.tsx        # Entity search input
│   ├── RiskBadge.tsx        # Risk level indicator
│   └── ui/                  # shadcn/ui primitives
├── data/
│   └── mockData.ts          # Mock entities and report data
├── pages/
│   ├── Index.tsx            # Dashboard with search + recent entities
│   └── Report.tsx           # Entity due diligence report
├── index.css                # Design tokens (single source of truth)
└── App.tsx                  # Router configuration
```

---

## 11. Anti-Patterns (Do NOT)

- ❌ Use raw color values (`text-red-500`, `bg-blue-900`) in components
- ❌ Use risk colors for non-risk-related UI elements
- ❌ Create custom one-off styles — extend the design system instead
- ❌ Use decorative animations — motion is reserved for state transitions
- ❌ Add dark mode toggle — not a priority for internal government tools
- ❌ Use placeholder images or stock photography
- ❌ Display risk scores without accompanying text labels
- ❌ Use informal language in report content
