# MyCTF frontend design tokens

Dark-only theme. Tokens live in `tailwind.config.ts`; components use Tailwind classes only.

## Rules
- **Spacing:** 8px grid. Use even Tailwind steps only: `2`=8, `4`=16, `6`=24, `8`=32, `10`=40, `12`=48, `16`=64.
  Never `1/3/5/7` or arbitrary values like `p-[17px]`.
- **Brand:** one color, `brand` (alias of Tailwind `red`). Fill `brand-600` (hover `brand-700`) with white text;
  text/icons on dark `brand-400`; tints `brand-500/10` + ring `brand-500/30`.
- **Neutrals (Tailwind `gray`):** page `gray-950`, surfaces `gray-900`, hover `gray-800`, borders `gray-800`.
- **Text:** headings `gray-50`, body `gray-300`, secondary/meta/labels `gray-400`.
  Do not use `gray-500` or darker for text on dark surfaces (fails WCAG AA).
- **Type:** hierarchy by weight and color. Page title `text-2xl font-semibold tracking-tight`,
  section `text-lg font-semibold`, body `text-sm`, overline `text-xs font-medium uppercase tracking-wider`,
  numbers `font-mono`.
- **Surfaces:** `border-gray-800`, `shadow-sm` (cards), `shadow-md` (menus), radius `rounded-lg` / `rounded-xl`.
- **Interaction:** every clickable element has `transition-colors duration-200`, a hover state, and the shared
  `focusRing` from `src/lib/cn.ts`.
- **Control sizes:** `h-8` (sm), `h-10` (default). Sidebar `w-64`, top bar `h-16`, content `max-w-6xl`.

## Motion & interaction
- **Entrances:** sections fade up 8px (`animate-fade-up`), staggered with `reveal(i)` from `src/lib/motion.ts`.
  Routes fade in (`AppLayout` re-keys the outlet per path). Dialogs use `animate-scale-in`.
- **Hover:** cards that act as links use `interactive` (the `.lift` helper: rise 4px + deeper shadow);
  buttons press in (`active:scale-[0.97]`).
- **Numbers** count up with `AnimatedNumber`; meters (`ProgressBar`, `ProgressRing`) fill in from zero.
- **Feedback:** `useToast()` for confirmations; `celebrate()` (confetti) only for a first-time solve.
- **Loading:** skeletons (`Skeleton`, `PageSkeleton`) instead of spinners for page content.
- **Live data:** the scoreboard refetches every 30s while the tab is visible (`useInterval`).
- **Reduced motion:** `index.css` collapses every animation and transition under
  `prefers-reduced-motion`; `AnimatedNumber`, `TypingTerminal` and `celebrate()` also check it.
- **Keyboard:** `⌘K` / `Ctrl+K` or `/` opens the command palette (pages + challenges).

## Charts (`components/charts/`)
- `ScoreRace` (scoreboard): step lines, categorical slots in fixed order
  `#3987e5 #d95926 #199e70 #c98500 #d55181 #9085e9`, legend + crosshair tooltip + table view.
- `ActivityHeatmap` (dashboard): one-hue sequential ramp `#1f2937 #b91c1c #dc2626 #f87171 #fecaca`.
- Both palettes were validated against the card surface `gray-900` (#111827). Re-validate if either changes.

## Named layout tokens (tailwind.config.ts)
- `h-app` = full height under the 64px top bar (challenge play screen)
- `w-play` = the draggable brief column (set through the `--play-left` CSS variable)
- Placeholders are the only place `gray-500` is used.

## Structure
- `components/ui/` — Button, Card, Badge, ChallengeBadges, Avatar, ScoreChip, Alert, Field (Input/Select/Textarea),
  StatCard, ProgressBar, ProgressRing, AnimatedNumber, Skeleton, SpotlightCard, TypingTerminal, Kbd, Table, Tabs,
  EmptyState, PageLoader, SectionLabel
- `components/feedback/` — Toast (provider + `useToast`), `celebrate()` confetti
- `components/charts/` — ScoreRace, ActivityHeatmap
- `components/layout/` — AppLayout, Sidebar, SidebarBrand, SidebarNavItem, Topbar, UserMenu, PageHeader,
  PageContainer, AuthLayout, RouteGuards, CommandPalette
- `pages/` — one file per route (auth/, admin/ in subfolders)
- `context/` — AuthContext (session), BreadcrumbContext
- `lib/api.ts` — fetch wrapper; `hooks/useApi.ts` — GET + loading/error state
- `config/navigation.ts` — nav sections (same destinations as the Jinja sidebar)
- `types/navigation.ts` — shared interfaces
