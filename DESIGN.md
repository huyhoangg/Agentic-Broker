---
version: alpha
name: "Prisma"
website: "https://www.prisma.io"
description: >-
  A database-tooling brand whose marketing site rides a white canvas anchored by a teal voltage — the single brand color wired as --primary (#16a394) — that carries CTAs, focus rings, sidebar highlights, and chart series in one unbroken chromatic thread. The hero headline "Postgres, perfectly managed." runs Mona Sans VF at 64px / weight 400, an unusually light-weight moment for a developer-infrastructure brand. Inter at weight 375–500 handles all navigation and body copy. Radii cluster at 6px (92 occurrences) and 10px (48 occurrences), giving the product-UI cards a mid-soft geometry. Prisma's type system has two distinct personality modes — Mona Sans VF for display and section headings, Inter for everything operational.

seo:
  title: "Prisma Design System for React — teal on white, Mona Sans VF, 20 components"
  metaDescription: "Prisma's marketing design system as a DESIGN.md file — teal #16a394 brand voltage, Mona Sans VF at 64px display, Inter body, 6px card rounding, 20 components. Tokens for React, Next.js, and AI tools."
  highlights:
    - "Weight-400 display headline — Mona Sans VF at 64px in weight 400 is lighter than any comparable ORM brand, letting teal CTA voltage carry the page rather than typographic muscle"
    - "Two-family system — Mona Sans VF for all display and section headings, Inter for all nav, body, and button copy; the swap happens at precisely 18px"
    - "Teal-as-primary — #16a394 wired to --primary, --ring, --sidebar-primary, --chart-1 simultaneously; one color carries CTAs, focus states, and data visualizations"
    - "6px dominant radius — 92 occurrences at 6px, the tightest meaningful step for product-UI cards and input fields on a white canvas"
    - "Uppercase small-caps labels — Mona Sans VF at 16px / weight 700 / 1.6px letter-spacing runs the nav badge and product-tier chips, the only tracking-wide tier in the system"
  tags:
    - "Backend, Database & DevOps"
    - "Developer Tools & IDEs"
  lastUpdated: "2026-05-19"
  author:
    name: "Dov Azencot"
    url: "https://x.com/dovazencot"
  opening: |
    Prisma's marketing page is organized around a quiet typographic contradiction — the hero headline "Postgres, perfectly managed." runs Mona Sans VF at 64px in weight 400, the same weight as the body copy, so the display and the paragraph share the same visual mass and the teal CTA button becomes the heaviest element above the fold. Where most ORM and database brands reach for weight 700 or 800 to impose authority, Prisma withholds weight at the display tier and concentrates force in a single saturated color. The overall impression is a white-canvas editorial system that happens to sell infrastructure rather than content.

    The DESIGN.md file packages this into machine-readable tokens for React and AI tools. Inside: 18 color tokens including a teal brand voltage (#16a394) that wires simultaneously into --primary, --ring, --sidebar-primary, and --chart-1; 14 typography tokens spanning Mona Sans VF in four display roles (64px h1, 40px h2, 36px h2, 24px h3) and Inter in seven operational roles (16px body, 12px caption, 11px uppercase label); 7 radius values dominated by a 6px card default; 9 spacing values on an 8px base; and 20 component definitions covering the teal CTA button, hairline-edged feature cards, the dark sidebar, monospace code blocks, and the light nav bar.

    Feed this file to Claude or Cursor and it reproduces Prisma's specific moves: white canvas with near-black ink text, teal-only brand voltage never repeated in secondary accents, Mona Sans VF for display moments with Inter handling everything at 16px and below, and a 6px card geometry that feels like product UI rather than marketing decoration. The one structural decision worth borrowing for any developer-infra brand is the two-family split — reserving Mona Sans VF exclusively for headings creates a clear register shift that Inter's system stack cannot produce alone.
  related:
    - href: "/design"
      title: "Browse all design systems"
      description: "The full directory of DESIGN.md files on shadcn.io, with live mockups for each."
    - href: "https://www.prisma.io"
      title: "Prisma — official site"
      description: "Prisma's public marketing site — the source of truth for the live tokens captured in this file."
    - href: "https://github.com/google-labs-code/design.md"
      title: "The DESIGN.md specification"
      description: "Google Labs' open spec for machine-readable design system files — the format this page is built on."
  questions:
    - id: "primary-color"
      title: "What is Prisma's primary brand color?"
      answer: "Prisma's brand voltage is teal #16a394, wired into CSS as --primary, --sidebar-primary, --sidebar-ring, --ring, --chart-1, and --color-fd-ring. It appears on the hero CTA button ('Create database'), the sidebar active highlight, the focus ring for all interactive elements, and the first chart series. The next closest teal in the system is #0d9488 (64 text occurrences), which handles success states, the Prisma Postgres product color (--color-foreground-ppg), and code-diff add indicators. Using #0d9488 as a primary CTA color would conflict with its semantic success/ppg role — keep #16a394 exclusive to brand CTAs."
    - id: "typography"
      title: "What typefaces does Prisma use, and how do they divide labor?"
      answer: "Prisma runs two families. Mona Sans VF (variable) carries all display moments — the 64px hero h1 at weight 400, 40px and 36px section h2s at weight 900, 24px h3 at weight 700, and the 16px uppercase badge labels at weight 700 with 1.6px letter-spacing. Inter carries everything operational — 16px body at weight 375–500, 14px label at weight 500, 12px caption at weight 400, and button labels at weight 600. The swap point is 18px: anything at or above that size on a heading element uses Mona Sans VF; anything below uses Inter. The closest open-source substitute for Mona Sans VF is DM Sans at variable weights."
    - id: "teal-ppg-difference"
      title: "What is the difference between Prisma's teal shades?"
      answer: "The system has two teal shades in active use: #16a394 (the brand primary) and #0d9488 (the PPG / success token). The distinction is semantic. #16a394 is the brand voltage — it goes on CTAs, sidebar selected states, and chart-1 fills. #0d9488 is the Prisma Postgres Gateway color and the success semantic token; it appears on 64 text elements including success-state labels, the --color-stroke-ppg border, and the 'PostgreSQL' product badge. A third teal, #14b8a6, is used as the light success-reverse background fill (4 background occurrences). Never place all three together — the perceptual gap between #16a394 and #0d9488 is too small for adjacent use."
    - id: "card-rounding"
      title: "What corner-radius does Prisma use on cards?"
      answer: "The dominant radius is 6px (92 occurrences), used on feature cards, input fields, nav dropdown surfaces, and small product-chip badges. The second tier is 10px (48 occurrences), used on the primary CTA button and larger card containers. A 12px tier (22 occurrences) appears on the modal and overlay surfaces, and 8px (21 occurrences) on icon buttons. The system does not use a pill radius on the marketing surface; the maximum is a very large computed value (3.35544e+07px — effectively 9999px) on the circular avatar elements in the testimonial row."
    - id: "use-in-project"
      title: "Can I use this DESIGN.md to build a Prisma-style dashboard or docs site?"
      answer: "Yes — the file is designed to be fed into Claude, Cursor, or any AI tool that reads structured design tokens. The agent will reproduce Prisma's specific moves: white canvas with hairline #e2e8f0 card borders, teal CTA voltage at #16a394, Mona Sans VF for display headings with Inter for body, and a 6px primary card radius. The tokens reference cleanly — {colors.primary} for CTAs, {colors.hairline} for card borders, {typography.display-xl} for the hero. One caution: the system exposes a rich semantic color set (success, error, warning, ORM blues, PPG teals) intended for a docs + dashboard surface rather than a pure marketing page. Filter to the structural tokens if your target is marketing only."

mockups:
  - "marketing-hero"
  - "dashboard-card-grid"

colors:
  primary: "#16a394"
  primary-light: "#14b8a6"
  primary-strong: "#0d9488"
  primary-dark: "#0f766e"
  accent-teal-pale: "#d9f9f6"
  ink: "#111827"
  ink-soft: "#1d242f"
  ink-muted: "#6b7280"
  ink-weaker: "#9ca3af"
  canvas: "#ffffff"
  surface-1: "#f3f4f6"
  surface-2: "#f7fafc"
  hairline: "#e2e8f0"
  hairline-strong: "#d1d5db"
  shadow: "#000000"
  error: "#dc2626"
  warning: "#ea580c"
  disabled: "#4a5568"
  orm-ink: "#4f46e5"
  syntax-green: "#0ac864"

typography:
  display-xl:
    fontFamily: "\"Mona Sans VF\", Inter, Roboto, \"Helvetica Neue\", sans-serif"
    fontSize: 64px
    fontWeight: 400
    lineHeight: 72px
    letterSpacing: 0
  display-lg:
    fontFamily: "\"Mona Sans VF\", Inter, Roboto, \"Helvetica Neue\", sans-serif"
    fontSize: 40px
    fontWeight: 900
    lineHeight: 48px
    letterSpacing: 0
  display-md:
    fontFamily: "\"Mona Sans VF\", Inter, Roboto, \"Helvetica Neue\", sans-serif"
    fontSize: 36px
    fontWeight: 900
    lineHeight: 48px
    letterSpacing: 0
  heading-md:
    fontFamily: "\"Mona Sans VF\", Inter, Roboto, \"Helvetica Neue\", sans-serif"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 32px
    letterSpacing: 0
  heading-sm:
    fontFamily: "\"Mona Sans VF\", Inter, Roboto, \"Helvetica Neue\", sans-serif"
    fontSize: 18px
    fontWeight: 650
    lineHeight: 28px
    letterSpacing: 0
  badge-label:
    fontFamily: "\"Mona Sans VF\", Inter, Roboto, \"Helvetica Neue\", sans-serif"
    fontSize: 16px
    fontWeight: 700
    lineHeight: 24px
    letterSpacing: "1.6px"
  body-lg:
    fontFamily: "Inter, Roboto, \"Helvetica Neue\", \"Arial Nova\", sans-serif"
    fontSize: 16px
    fontWeight: 375
    lineHeight: 24px
    letterSpacing: 0
  body-md:
    fontFamily: "Inter, Roboto, \"Helvetica Neue\", \"Arial Nova\", sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
    letterSpacing: 0
  button-md:
    fontFamily: "Inter, Roboto, \"Helvetica Neue\", \"Arial Nova\", sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 24px
    letterSpacing: 0
  nav-link:
    fontFamily: "Inter, Roboto, \"Helvetica Neue\", \"Arial Nova\", sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 24px
    letterSpacing: 0
  label-md:
    fontFamily: "Inter, Roboto, \"Helvetica Neue\", \"Arial Nova\", sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 20px
    letterSpacing: 0
  body-sm:
    fontFamily: "Inter, Roboto, \"Helvetica Neue\", \"Arial Nova\", sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
    letterSpacing: 0
  caption:
    fontFamily: "Inter, Roboto, \"Helvetica Neue\", \"Arial Nova\", sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 16px
    letterSpacing: 0
  caption-upper:
    fontFamily: "Inter, Roboto, \"Helvetica Neue\", \"Arial Nova\", sans-serif"
    fontSize: 11px
    fontWeight: 400
    lineHeight: 16px
    letterSpacing: "0.36px"
  mono-md:
    fontFamily: "\"Mona Sans Mono VF\", ui-monospace, \"Cascadia Code\", Menlo, Consolas, monospace"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
    letterSpacing: 0

rounded:
  none: "0px"
  xs: "3px"
  sm: "6px"
  md: "10px"
  lg: "12px"
  xl: "16px"
  full: "9999px"

spacing:
  xxs: "4px"
  xs: "6px"
  sm: "8px"
  md: "12px"
  base: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.canvas}"
    typography: "{typography.button-md}"
    rounded: "{rounded.sm}"
    padding: "0px 16px"
    height: "48px"
    border: "0"
  button-primary-hover:
    backgroundColor: "{colors.primary-strong}"
    textColor: "{colors.canvas}"
    typography: "{typography.button-md}"
    rounded: "{rounded.sm}"
    padding: "0px 16px"
    height: "48px"
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.button-md}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
    height: "36px"
    borderColor: "{colors.hairline}"
  top-nav:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.nav-link}"
    rounded: "{rounded.none}"
    padding: "0px 16px"
    height: "64px"
    borderColor: "{colors.hairline}"
  nav-link:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
    typography: "{typography.nav-link}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
  hero-heading:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.display-xl}"
    padding: "0"
  section-heading:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.display-lg}"
  body-paragraph:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-md}"
  card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: "16px"
    borderColor: "{colors.hairline}"
  card-muted:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: "16px"
  badge-label:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
    typography: "{typography.badge-label}"
    rounded: "{rounded.none}"
  badge-teal:
    backgroundColor: "{colors.accent-teal-pale}"
    textColor: "{colors.primary-dark}"
    typography: "{typography.caption}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  text-input:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
    height: "36px"
    borderColor: "{colors.hairline}"
  sidebar:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body-sm}"
    borderColor: "{colors.hairline}"
  sidebar-active:
    backgroundColor: "{colors.accent-teal-pale}"
    textColor: "{colors.primary-dark}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.sm}"
  code-block:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.mono-md}"
    rounded: "{rounded.sm}"
    padding: "12px"
    borderColor: "{colors.hairline}"
  feature-icon-card:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: "16px"
  testimonial-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: "24px"
    borderColor: "{colors.hairline}"
  footer:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-sm}"
    padding: "48px 0px"
    borderColor: "{colors.hairline}"
  modal:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: "24px"
---

## Overview

Prisma's marketing site withholds typographic weight at the display tier — by design. **Weight restraint as brand confidence.** The hero headline "Postgres, perfectly managed." runs Mona Sans VF at 64px in weight 400, the same weight Inter uses for body paragraphs on the same page. Where competitors like PlanetScale and Neon run their hero headlines at weight 700–900, Prisma holds display at weight 400 and lets the single teal CTA button (#16a394) carry all perceptual force above the fold. The button is the heaviest visual object on the page.

The two-family typographic system reinforces the register split. Mona Sans VF handles every heading and badge label — it is the brand voice. Inter handles every body paragraph, nav link, and button label — it is the operational voice. The two families never appear at the same tier; the crossover is at 18px / heading boundary. Unlike most developer-infra brands that commit to a single workhorse family (Vercel uses Geist exclusively, Linear uses Inter exclusively), Prisma explicitly signals "display = product identity, body = developer utility."

Chromatic restraint matches the typographic restraint. The teal voltage (#16a394) is the only chromatic brand moment — it goes on CTAs, sidebar highlights, focus rings, and chart series simultaneously. There is no secondary accent. The large semantic palette (success-teal #0d9488, ORM-indigo #4f46e5, purple/pink/fuchsia/sky) is wired for a docs and dashboard product surface and does not appear in the marketing chrome.

**Key Characteristics:**
- Mona Sans VF at 64px / weight 400 for the hero h1 — lighter than every comparable infrastructure brand.
- Single teal voltage (#16a394) wired to --primary, --ring, --sidebar-primary, --chart-1, and --color-fd-primary simultaneously.
- Two-family system: Mona Sans VF for headings/labels, Inter for body/nav/buttons. Crossover at 18px.
- 6px dominant radius (92 occurrences) — card geometry is tighter than Cloudflare (3–8px binary) but softer than Linear (4px).
- Hairline-only card elevation — #e2e8f0 borders on a white canvas, zero drop shadows on marketing surfaces.
- Uppercase tracked badge labels — Mona Sans VF at 16px / weight 700 / 1.6px tracking, used for nav product badges and feature-tier chips.
- Large semantic palette declared in CSS but invisible in marketing chrome — success, error, ORM-indigo, PPG-teal tiers all exist for product/docs surfaces.

## Colors

### Brand

- **Primary Teal** (`#16a394`): frequency 0 rendered (CSS variable layer only). Wired as --primary, --sidebar-primary, --sidebar-ring, --chart-1, --ring, --color-fd-ring. The brand voltage — every CTA button, sidebar active state, and focus ring resolves through this single token.
- **Primary Strong** (`#0d9488`): frequency 66. Used as text (64), bg (1), gradient (1). The Prisma Postgres Gateway color and success semantic token — wired as --color-foreground-ppg, --color-stroke-success, --color-fd-primary.
- **Primary Light** (`#14b8a6`): frequency 4. Used as background. The pale success reverse — wired as --color-background-success-reverse and --color-foreground-ppg-weak.
- **Primary Dark** (`#0f766e`): declared as --color-foreground-ppg-strong. The darkest teal shade, used for emphasis text over pale teal backgrounds.
- **Accent Teal Pale** (`#d9f9f6`): frequency 0 rendered. Wired as --accent, --color-fd-accent, --sidebar-accent. The pale surface for active sidebar items and accent backgrounds.

### Structural

- **Ink** (`#111827`): frequency 239. Used as text — the near-black primary text color, wired as --color-foreground-neutral and --color-background-neutral-reverse-strong.
- **Ink Soft** (`#1d242f`): frequency 193. Used as text (145) and bg (48). Secondary foreground and popover text — wired as --foreground, --card-foreground, --sidebar-foreground.
- **Ink Muted** (`#6b7280`): frequency 173. Used as text — the workhorse secondary text color for body paragraphs, wired as --color-foreground-neutral-weak.
- **Ink Weaker** (`#9ca3af`): frequency 2. Tertiary text — footer metadata and placeholder labels.
- **Canvas** (`#ffffff`): frequency 198. Used as background (79) and text (105). Pure white page floor and card surfaces, also the reverse text color on teal and dark backgrounds.
- **Surface-1** (`#f3f4f6`): frequency 7. Muted card backgrounds, sidebar hover states, and feature-icon card fills.
- **Surface-2** (`#f7fafc`): wired as --sidebar and --color-fd-secondary. The sidebar background tone — a touch warmer than surface-1.
- **Hairline** (`#e2e8f0`): frequency 758. The dominant border — wired as --border, --color-fd-border, --sidebar-border, --input, --color-border. Card outlines, input borders, dividers.
- **Hairline Strong** (`#d1d5db`): wired as --color-stroke-neutral-strong. A slightly darker border for emphasis contexts.

### Semantic

- **Error** (`#dc2626`): wired as --color-foreground-error, --color-stroke-error. Not rendered on the marketing surface.
- **Warning** (`#ea580c`): wired as --color-foreground-warning. Not rendered on the marketing surface.
- **Disabled** (`#4a5568`): wired as --color-disabled. Form field disabled state.
- **ORM Ink** (`#4f46e5`): wired as --color-foreground-orm, --color-stroke-orm. The ORM product color — appears on the /orm sub-product docs surface.
- **Syntax Green** (`#0ac864`): wired as --color-fd-diff-add-symbol. Code diff addition indicator.

## Typography

### Font Families

The system runs two families. **Mona Sans VF** (GitHub's variable sans-serif) handles every heading, section label, and badge. **Inter** handles every paragraph, nav link, and button. The monospace tier runs **Mona Sans Mono VF** (also variable) for code blocks. Fallbacks walk the usual system-ui stack.

The variable font axes on Mona Sans VF are used actively — the hero h1 at weight 400 and the section h2s at weight 900 are the two poles of the same variable axis, not separate font files.

### Hierarchy

| Token | Family | Size | Weight | Use |
|---|---|---|---|---|
| `{typography.display-xl}` | Mona Sans VF | 64px | 400 | Hero h1 — "Postgres, perfectly managed." |
| `{typography.display-lg}` | Mona Sans VF | 40px | 900 | Primary section h2 headings |
| `{typography.display-md}` | Mona Sans VF | 36px | 900 | Secondary section h2 headings |
| `{typography.heading-md}` | Mona Sans VF | 24px | 700 | h3 — feature card titles |
| `{typography.heading-sm}` | Mona Sans VF | 18px | 650 | Subheadings and feature card labels |
| `{typography.badge-label}` | Mona Sans VF | 16px | 700 | Uppercase nav badges, 1.6px tracking |
| `{typography.body-lg}` | Inter | 16px | 375 | Default body copy — the variable axis at 375 |
| `{typography.body-md}` | Inter | 16px | 400 | Standard paragraph text |
| `{typography.button-md}` | Inter | 16px | 600 | Button labels |
| `{typography.nav-link}` | Inter | 16px | 600 | Top-nav link labels |
| `{typography.label-md}` | Inter | 14px | 500 | Form labels and metadata chips |
| `{typography.body-sm}` | Inter | 14px | 400 | Caption rows and secondary paragraph text |
| `{typography.caption}` | Inter | 12px | 400 | Footer and small labels |
| `{typography.caption-upper}` | Inter | 11px | 400 | Uppercase nano labels, 0.36px tracking |
| `{typography.mono-md}` | Mona Sans Mono VF | 16px | 400 | Code blocks and inline code |

### Principles

The display-to-body weight flip is the defining typographic move. The h1 at weight 400 is lighter than the button labels (Inter 600) on the same screen — a deliberate inversion of the usual hierarchy. Mona Sans VF's 900-weight section headings restore authority at the sub-section level, creating a two-pulse rhythm: quiet hero → loud section → quiet body.

### Note on Font Substitutes

Mona Sans VF is open-source via GitHub's repository. The closest alternative is DM Sans variable for the display tier and Inter (already in the stack) for body. The critical substitution constraint: the hero h1 must stay at weight 400, not bumped to 500 or 600 — the understatement is the point.

## Layout

### Spacing System

- **Base unit:** 8px, appearing 88 times in the extracted spacing data.
- **Tokens:** `{spacing.xxs}` 4px · `{spacing.xs}` 6px · `{spacing.sm}` 8px · `{spacing.md}` 12px · `{spacing.base}` 16px · `{spacing.lg}` 24px · `{spacing.xl}` 32px · `{spacing.2xl}` 48px · `{spacing.3xl}` 64px.
- **Button padding:** 0 vertical, 16px horizontal at 48px height — the height constraint controls vertical rhythm rather than padding.
- **Card internal padding:** 16px (`{spacing.base}`) on standard feature cards; 24px (`{spacing.lg}`) on testimonial and larger hero cards.
- **Section rhythm:** 48px vertical between major sections, consistent with the 2xl spacing token.

### Grid & Container

- **Max content width:** ~1080px for hero and main content columns.
- **Hero layout:** two-column split — headline + CTA left, product UI screenshot right. Headline column is ~60% width.
- **Feature row:** three-column grid of product cards (Serverless Postgres, ORM, Prisma Studio, AI Toolkit), each in a hairline-bordered card with a 10px rounded corner.
- **Testimonial row:** three-column grid of customer quote cards.
- **Below fold:** alternating single-column editorial blocks and two-column feature comparisons.

### Rhythm

The page alternates between a generous white editorial zone (hero, testimonials) and a denser product-card zone (the 4-up feature grid, the stack comparison, the Prisma Postgres architecture diagram). There is no atmospheric background shift between zones — every section runs on the same white canvas, and the product-card zone announces itself through the 6px-rounded hairline card grid rather than a color or gradient change.

## Elevation

The marketing surface has essentially **no shadow tier**. The captured page has only 8 shadow occurrences, all using pure black with low opacity (small box-shadow halos). Card elevation comes entirely from hairline borders — `{colors.hairline}` (#e2e8f0, 758 occurrences) outlines every feature card, modal container, and code block. There is no intermediate surface — cards sit directly on the white canvas floor.

- **Flat (no shadow):** hero, editorial sections, footer — ~95% of surfaces.
- **Hairline-bordered:** feature cards, text inputs, the code comparison panel, the Prisma Studio screenshot frame.
- **Sidebar:** uses `{colors.surface-2}` background tone against `{colors.canvas}` to create the only tonal lift on the page.

## Shapes

The radius scale is **mid-soft with a tight default**:

- `{rounded.none}` 0px — hero and section containers.
- `{rounded.xs}` 3px — computed from --radius-square-low; small chip corners.
- `{rounded.sm}` 6px — the dominant radius (92 occurrences): feature cards, input fields, nav dropdown items, small badges, the primary CTA button.
- `{rounded.md}` 10px — 48 occurrences: the hero CTA button in the screenshot mockup, larger card containers.
- `{rounded.lg}` 12px — 22 occurrences: modals and overlay panels. Matches --radius-square-high.
- `{rounded.xl}` 16px — 1 occurrence: the largest card in the testimonial strip.
- `{rounded.full}` 9999px — avatar circles in the testimonial row. The pill variant does not appear on buttons.

The 6px default is tighter than Cloudflare's 6–8px card rounding and matches the Tailwind `rounded-md` convention exactly. The system skips the 4px tier that Linear and Vercel use as their base — Prisma's smallest meaningful radius is 6px.

## Components

**`button-primary`** — Teal `{colors.primary}` fill, white text, Inter 600, `{rounded.sm}` 6px radius, 0×16px padding at 48px height. "Create database" is the canonical instance. No border — the teal fill is the button's entire identity.

**`button-primary-hover`** — Background deepens to `{colors.primary-strong}` (#0d9488) — a one-step darker teal for the press/hover state.

**`button-secondary`** — White `{colors.canvas}` fill, ink-soft text, 1px `{colors.hairline}` border, 6×10px padding, 36px height. Used for "Read the docs" and feature secondary actions.

**`top-nav`** — White canvas, 64px height, 1px bottom hairline border. Prisma logo left, product nav (Products / Solutions / Docs / Changelog / Blog) center, "Sign in" and "Create database" cluster right.

**`nav-link`** — Transparent background, ink-soft text in `{typography.nav-link}` (Inter 600), 6×10px padding. Hover shows a `{rounded.sm}` hairline-bordered background fill.

**`hero-heading`** — Near-black ink text, Mona Sans VF 64px / weight 400. Zero padding — the headline flows at natural width.

**`section-heading`** — Near-black ink, Mona Sans VF 40px / weight 900. The contrast between the weight-400 hero and the weight-900 sections is the page's primary typographic rhythm.

**`body-paragraph`** — `{colors.ink-muted}` (#6b7280) at Inter 16px / 400. The muted tone keeps body copy subordinate to the headline and CTA button.

**`card`** — White canvas, 1px `{colors.hairline}` border, 10px radius, 16px padding. The default feature card — holds an icon, heading, and 1-2 line description.

**`card-muted`** — `{colors.surface-1}` fill, same radius and padding. Used for the "Build anything. Deploy Instantly." illustration band and the AI workflow card.

**`badge-label`** — Muted ink, Mona Sans VF 16px / weight 700 / 1.6px tracking / uppercase. The nav badge that labels product categories ("POSTGRES," "ORM," "STUDIO").

**`badge-teal`** — Pale teal `{colors.accent-teal-pale}` fill, dark teal text, 6px radius, 2×8px padding. Used for product-category chips inside feature cards.

**`text-input`** — White canvas, 1px hairline border, 6px radius, 6×10px padding, 36px height. The search and signup input fields.

**`sidebar`** — `{colors.surface-2}` background, hairline right border, Inter 14px / 400. The docs/product sidebar navigation surface.

**`sidebar-active`** — `{colors.accent-teal-pale}` fill, dark teal text, 6px radius. The active sidebar link indicator — the teal accent at its most restrained.

**`code-block`** — White canvas, 1px hairline border, 6px radius, 12px padding. Uses `{typography.mono-md}` with Mona Sans Mono VF.

**`feature-icon-card`** — `{colors.surface-1}` fill, 10px radius, 16px padding. The icon + label card units in the "Postgres that fits your stack." technology grid.

**`testimonial-card`** — White canvas, 1px hairline border, 12px radius, 24px padding. Customer quote cards beneath the feature grid.

**`footer`** — White canvas, ink-muted text, 1px top hairline border, 48px vertical padding. Four-column link grid (Summary / Announcements / Contact / Community).

## Do's and Don'ts

**Do** keep the hero headline at weight 400 when using Mona Sans VF. The typographic identity of the system is the weight inversion — a hero lighter than the button. Adding weight to the h1 destroys the relationship that makes the teal CTA the heaviest element above the fold.

**Do** use `{colors.hairline}` (#e2e8f0) for every card border. The system is mono-hairline — 758 of the captured border occurrences use this single tone. Introducing a second border color breaks the structural unity.

**Do** keep Mona Sans VF exclusive to headings and badge labels. Inter handles every element below 18px. Mixing Mona Sans VF into body copy at 14–16px removes the register signal that marks "this is a heading" even before the reader parses the content.

**Do** use `{colors.primary}` (#16a394) for exactly one CTA per section. The system's teal never repeats as a secondary accent — there are no teal body links, no teal hover backgrounds, no teal icon fills. One teal moment per screen is the discipline.

**Don't** use `{colors.primary-strong}` (#0d9488) as a primary CTA color. It is the Prisma Postgres Gateway semantic color (--color-foreground-ppg), used for success states and the PPG product badge; placing it on a CTA button creates a false semantic signal.

**Don't** apply the `{rounded.full}` pill radius to buttons. The system does not use pill-shaped buttons anywhere on the marketing surface — the maximum button radius is `{rounded.md}` 10px. Pill buttons would import a visual convention that belongs to Cloudflare and Stripe, not Prisma.

**Don't** use `{colors.orm-ink}` (#4f46e5) or any other semantic color from the large palette as a brand accent. The ORM indigo, PPG teal, fuchsia, purple, pink, cyan, and sky tokens are all scoped to product-domain diagram nodes in the docs surface — they are not available for marketing decoration.

**Don't** place the section headings at weight 400. The weight-900 section h2 is a deliberate contrast with the weight-400 hero — it creates the two-pulse rhythm of "quiet hero → loud section." Using 400 throughout flattens the hierarchy to a single monotone register.

## Known Gaps

- **Dark mode:** the captured marketing surface is light-only. The CSS exposes a full reverse palette (--color-background-neutral-reverse, --color-foreground-neutral-reverse) wired for a dark theme, likely used in the Prisma Studio product surface. Not represented here.
- **Hover and focus states:** only the button-primary-hover state is documented; the full matrix (input focus ring, nav hover, card hover) is not captured from the static marketing screenshot.
- **Interactive product-UI screenshots:** the hero right column shows a Prisma Studio and a code snippet component. The exact pixel dimensions and internal token structure of these in-product UI panels are not captured.
- **Animation and motion:** the marketing page includes scroll-triggered fade-in animations on the feature grid and testimonial strip. Easing curves and duration values are not captured here.
- **Mona Sans VF variable axes:** the spec uses weight axis values (400, 650, 700, 900) but does not capture any other variable axis (e.g., width, slant) if present. The rendering uses default values for all non-weight axes.
- **The full semantic palette:** 20+ semantic color tokens (error, warning, sky, cyan, fuchsia, lime, pink, violet, purple, ORM-indigo tiers) are declared in CSS but absent from the marketing render. Their full interaction with the docs and dashboard surface is not represented here.
