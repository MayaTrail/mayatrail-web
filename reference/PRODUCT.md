# PRODUCT.md

High-level product & layout blueprint distilled from the existing frontend
(`frontend/UI`). This file defines the **layout boundaries, navigation model,
and structural constraints** that any generated UI must inherit. It intentionally
excludes backend, API, auth-protocol, and infrastructure concerns.

---

## 1. Product Identity

- **Name:** MayaTrail UI — an adversary/APT emulation platform dashboard.
- **Surface:** A single-page web application (SPA) dashboard for managing
  emulations, detection rules, IR playbooks, and guardrails across multiple
  cloud/security platforms (AWS, Azure, GCP, AI, Kubernetes).
- **Character:** Dense, technical, dark-first operator console — closer to an
  IDE or a security operations tool than a marketing site. Information density
  and scan-ability matter more than whitespace or decoration.

---

## 2. Technology Boundaries (fixed)

| Layer        | Choice                              | Constraint |
|--------------|-------------------------------------|------------|
| Framework    | React 18 (function components only) | No class components. Hooks only. |
| Build tool   | Vite 6                              | ES modules; `type: module`. |
| Language     | TypeScript (strict)                 | All components typed; explicit prop interfaces. |
| Styling      | Tailwind CSS 3 + CSS custom properties | Utility-first; theme via CSS vars. No CSS-in-JS libraries. |
| Routing      | React Router v6                     | Nested routes under a shared layout shell. |
| Data viz     | Recharts + Dagre (graph layout)     | Use these before reaching for new chart libs. |
| Markdown     | react-markdown + remark-gfm         | For any rendered long-form content. |
| HTTP         | Axios                               | Confined to the `services/` layer — never call from components directly. |

**Do not add** new UI frameworks, component libraries (MUI, Chakra, shadcn,
Bootstrap), or alternative styling systems. The design system is bespoke and
Tailwind-native.

---

## 3. Application Shell / Layout Architecture

The app is composed as three nested structural layers. Generated screens live
**inside** the content region only — they must never redefine the shell.

```
<ThemeProvider> → <AuthProvider> → <PlatformProvider>   (global context wrappers)
  └── Routes
        ├── /login, /connector           (bare, full-bleed pages — no shell)
        └── AppLayout                     (the persistent shell)
              ├── TopNav                  (fixed, 58px tall)
              └── row
                   ├── Sidebar            (240px, fixed-left, collapsible on mobile)
                   └── <main>             ← ALL page content renders here (<Outlet/>)
```

### Shell rules (boundaries)
- **TopNav:** fixed height `58px`, spans full width, always present inside the shell.
- **Sidebar:** fixed width `240px`, `bg-surface-base`, right border. On `lg+` it is
  static in-flow; below `lg` it becomes an overlay drawer (`translate-x` transition)
  with a `black/60` backdrop. Sidebar closes automatically on route change.
- **Main content region:** the only place page components render. It is the
  scroll container (`overflow-y-auto`), padded `px-6 lg:px-8 py-7`, and wrapped
  in an `animate-fadeIn`. Pages must assume they own this region and nothing outside it.
- **Command palette:** a global `Cmd/Ctrl-K` (or `/`) search overlay lives at the
  shell level. Individual pages do not implement their own global search.

### Constraint for generated layouts
Any new page is a **route element rendered through `<Outlet/>`**. It should:
- Never introduce its own top nav, sidebar, or full-screen chrome.
- Never set `position: fixed` full-screen backgrounds (the shell owns the canvas).
- Assume a constrained, scrollable content column, not the full viewport.

---

## 4. Navigation Model (information architecture)

Navigation is **workflow-first**, grouped by user goal — not platform-first.
Each content type lives in exactly one place; platforms are discovery entry
points, not containers. Preserve this grouping when adding nav items:

- **Dashboard** — Dashboard, Stacks
- **Operations** — Active Runs, Results
- **Security Content** — Emulations, Detections, Playbooks, Guardrails
- **Platforms** — per-platform overview entry points
- **Administration** — Reports, Docs (may be "coming soon" placeholders)

Route conventions already established (follow this shape for new routes):
- Cross-platform hubs: `/emulations`, `/detections`, `/playbooks`, `/guardrails`
- Platform-scoped detail flows: `/:platformId/emulations/:emulationId/...`
- Operational views: `/runs`, `/results`
- Placeholder screens use the shared `ComingSoon` component, never a blank route.

---

## 5. Page Composition Constraints

- **Compose from primitives.** Build screens out of the existing `components/ui`
  vocabulary (see DESIGN.md §Components) rather than hand-rolling one-off markup.
- **Feature folders.** Page-level components are grouped by domain
  (`dashboard/`, `emulations/`, `detections/`, `stacks/`, `playbooks/`,
  `guardrails/`, `operations/`, `platforms/`, `settings/`, `profile/`). New
  screens join the matching folder; shared building blocks go in `common/` or `ui/`.
- **Hubs vs. detail pages.** "Hub" screens list/route into content; "detail"
  screens render a single entity with tabbed sub-views. Keep that two-tier pattern.
- **Data & services separation.** Static/mock data lives in `data/`, network
  access in `services/`, cross-cutting state in `context/`, reusable logic in
  `hooks/`. Components stay presentational and consume these — they do not embed
  fetch/axios logic inline.
- **Modals & overlays** are dedicated components (`components/modals/`), mounted
  conditionally; they are not inlined into page bodies.

---

## 6. Explicit Non-Goals for the Skill

When inheriting this blueprint, the generation skill should **not**:
- Touch, reference, or reason about backend, API endpoints, auth token flow,
  guardrail policy engines, or emulation execution logic.
- Introduce new global chrome, routers, or provider trees.
- Swap the styling system or add component libraries.
- Break the workflow-first navigation grouping.

Its job is to produce **new screens and components that fit inside the existing
shell, using the existing primitives and design tokens.**
