# DESIGN.md

Visual design system distilled from the existing frontend (`tailwind.config.ts`,
`styles/globals.css`, and `components/ui/*`). This is the **single source of
truth for tokens, styling rules, and component constraints** that generated UI
must inherit. Everything here is presentational — no backend or API concerns.

The system is a **Raycast-inspired, dark-first, macOS-native** aesthetic:
cool-neutral near-black surfaces, restrained color used as punctuation,
double-ring containment instead of heavy borders, and opacity/translate hover
shifts instead of hard color swaps.

---

## 1. Theming Model

- **Dark-first, dark-pinned.** The app sets `data-theme="dark"` before paint.
  A light theme exists as CSS-var overrides but dark is the default and primary target.
- **All surface/text/border/accent colors resolve through CSS custom properties**
  defined in `globals.css` and exposed to Tailwind via `tailwind.config.ts`.
  Never hardcode hex values in components — use the semantic Tailwind tokens below.
- Theme switches by overriding CSS vars under `[data-theme='light']`; component
  classes never branch on theme themselves.

---

## 2. Color Tokens

### Surfaces (darkest → lightest)
| Token             | Dark value | Use |
|-------------------|-----------|-----|
| `surface-deep`     | `#07080a` | App canvas / body background |
| `surface-base`     | `#101111` | Sidebar, base panels |
| `surface-card`     | `#101111` | Card interiors |
| `surface-elevated` | `#1b1c1e` | Raised chips, inputs, hover fills |

### Text (brightest → dimmest)
| Token               | Dark value | Use |
|---------------------|-----------|-----|
| `content-primary`    | `#f9f9f9` | Headings, primary text |
| `content-secondary`  | `#cecece` | Body, secondary labels |
| `content-dim`        | `#9c9c9d` | Muted labels, ghost text |
| `content-muted`      | `#6a6b6c` | Least-emphasis captions |

### Borders (intentionally near-invisible)
`border-subtle` / `border` (default) = white @ 6% opacity; `border-active` = white @ 10%.
Borders are structural, not decorative — containment comes from shadow, not border weight.

### Brand & semantic accents
| Token     | Value     | Meaning |
|-----------|-----------|---------|
| `danger`   | `#FF6363` (Raycast Red) | Primary brand accent, errors, critical — **punctuation only, not pervasive** |
| `safe`     | `#5fc992` | Success / safe state |
| `warning`  | `#ffbc33` | Warnings |
| `accent-blue` | `#55b3ff` | Interactive: links, focus, selected |

Each semantic color also has `-glow` (15% alpha) and `-dim` (8% alpha) variants
for translucent surfaces and focus rings.

### Dashboard data-viz accents
`cyan`, `orange`, `purple`, `green`, `yellow`, `blue` — theme-aware, for charts
and category coding. Use these for data series, not for chrome.

> **Rule:** Color is punctuation. The canvas is near-black neutral; a screen
> should read as grayscale with small deliberate hits of red/blue/green.

---

## 3. Typography

- **Primary font:** `Inter` (mapped to `font-sans`, `font-display`, `font-body`).
  OpenType features `calt, kern, liga, ss03` are enabled globally.
- **Monospace:** `Geist Mono` (`font-mono`) — code blocks, terminal output,
  technical labels, status codes, IDs.
- **Body baseline:** weight `500`, letter-spacing `0.2px`.
- **Letter-spacing scale (px-based):**
  `tracking-body` 0.2px · `tracking-btn` 0.3px (buttons/nav) ·
  `tracking-caps` 0.5px (small uppercase tags) · `tracking-label` 1px (uppercase mono section labels).
- **Extra size:** `text-2xs` = 10px — micro mono labels (eyebrows, ID captions).
- Uppercase mono + wide tracking = section labels and technical eyebrows.
  Big tabular numerals over an uppercase mono label = metric tiles.

---

## 4. Shape, Depth & Motion

### Border radius
`rounded-btn` 8px (inputs, secondary buttons, badges) ·
`rounded-card` 16px (cards, screenshots) ·
`rounded-pill` 86px (primary CTAs, nav CTAs).

### Shadows — macOS-native, always multi-layer (never single-layer)
- `shadow-ring` — **double-ring containment**; the primary way cards are bounded
  (replaces a hard border).
- `shadow-button` — macOS button press: white highlight on top edge, dark inset below.
- `shadow-float` — floating panels / command palette, with subtle glow.

### Gradients
- `bg-key` — keyboard key-cap gradient (avatar tiles / key affordances).
- Text gradients: `.text-gradient-danger`, `.text-gradient-safe`, `.text-gradient-blue`.
- Card hover accent line: `.card-hover-accent` (and `-blue`) draws a thin
  gradient rule that fades in on hover.

### Motion
Use the predefined keyframes/animations only:
`animate-fadeIn`, `animate-fadeSlideIn`, `animate-modalIn`, `animate-slideUp`,
`animate-spin`, `animate-travel`, `animate-nodeGlow`.
Transitions are quick (0.25–0.3s ease-out). **Hover = opacity/translate shift,
never a hard color swap** on bordered/ghost elements.

---

## 5. Core Components (compose from these)

The `components/ui` primitives form the required vocabulary. Build screens from
them; do not hand-roll equivalent markup.

- **Button** — variants: `primary` (solid Raycast Red), `cta` (translucent white
  pill on dark text), `secondary` (transparent, bordered), `ghost` (chromeless,
  dim→bright), `danger` (transparent, danger-tinted). Sizes `sm | md | lg`.
  Shared base: inline-flex, `gap-2`, semibold, `tracking-btn`, `active:translate-y-px`,
  disabled = 40% opacity. Optional leading icon slot.
- **Card** — `bg-surface-card` + `rounded-card` + `shadow-ring`. Optional left
  `accent` bar (`red | blue | green | amber`) and `interactive` (pointer + hover
  lift + border brighten). Containment is the ring, not a border.
- **Badge / Tag** — translucent semantic chip; tones `neutral | red | blue | green |
  yellow | purple`. `mono` for codes/status (Geist Mono, uppercase, `text-2xs`),
  optional leading status `dot` with `pulse`.
- **MetricCard** — composed on `Card`: large tabular value, uppercase mono label,
  accent icon chip, optional caption. Accents `red | blue | green | amber | neutral`.
- Domain badges: `SeverityBadge`, `TacticBadge`, `ThreatOriginBadge` — reuse
  rather than re-encoding severity/tactic color logic.
- Other shared primitives: `Breadcrumb`, `SearchInput`, `FilterDropdown`,
  `EmptyState`, `CodeBlock`, `Icons` (inline SVG set), `PlatformIcons`.

### Component rules
- Every component takes an explicit typed props interface, accepts a `className`
  passthrough, and appends it last so callers can extend.
- Semantic tone/accent is passed as a prop mapped to a class record — never
  ad-hoc inline colors.
- Icons are inline SVGs from the shared `Icons` set, sized via a `size` prop.

---

## 6. Styling Conventions (hard constraints)

1. **Tailwind utility classes only** for layout/spacing/color. Semantic tokens
   over raw values (`bg-surface-card`, not `bg-[#101111]`).
2. **No CSS-in-JS, no styled-components, no new UI kit.** Global CSS lives only
   in `globals.css` under `@layer base/components/utilities`.
3. **Containment via `shadow-ring`**, not heavy borders. Borders stay at 6–10% alpha.
4. **Color sparingly** — neutral canvas, accent as punctuation.
5. **Dark-first**; never assume a light background. Text defaults to `content-*`
   tokens on `surface-*` tokens.
6. **Hover/active** = opacity + `translate` (`active:translate-y-px`), matching the
   Raycast interaction feel.
7. **Mono for anything technical** — IDs, codes, terminal output, status labels.
8. Respect the radius scale: pills for primary CTAs, `rounded-card` for cards,
   `rounded-btn` for inputs/badges.
9. Use only the predefined animations; do not introduce new keyframes casually.
10. Custom inputs must survive autofill/extension overrides using the established
    layered `!important` + inset-box-shadow surface technique (see the
    `auth-input-solid` pattern) rather than plain `background-color`.

---

## 7. What the Skill Must NOT Do

- Introduce new fonts, color systems, or component libraries.
- Hardcode hex colors or bypass the CSS-variable token layer.
- Replace `shadow-ring` containment with heavy visible borders.
- Use color pervasively or add decorative gradients beyond the defined set.
- Add full-screen backgrounds or chrome (the app shell owns the canvas — see PRODUCT.md).
- Reference or style anything tied to backend/API/auth logic.

Inherit these tokens and primitives; produce screens that are indistinguishable
in style from the existing MayaTrail UI.
