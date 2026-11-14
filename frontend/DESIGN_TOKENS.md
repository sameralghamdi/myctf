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

## Named layout tokens (tailwind.config.ts)
- `h-app` = full height under the 64px top bar (challenge play screen)
- `w-play` = the draggable brief column (set through the `--play-left` CSS variable)
- Placeholders are the only place `gray-500` is used.

## Structure
- `components/ui/` — Button, Card, Badge, ChallengeBadges, Avatar, ScoreChip, Alert, Field (Input/Select/Textarea),
  StatCard, ProgressBar, Table, Tabs, EmptyState, PageLoader, SectionLabel
- `components/layout/` — AppLayout, Sidebar, SidebarBrand, SidebarNavItem, Topbar, UserMenu, PageHeader,
  PageContainer, AuthLayout, RouteGuards
- `pages/` — one file per route (auth/, admin/ in subfolders)
- `context/` — AuthContext (session), BreadcrumbContext
- `lib/api.ts` — fetch wrapper; `hooks/useApi.ts` — GET + loading/error state
- `config/navigation.ts` — nav sections (same destinations as the Jinja sidebar)
- `types/navigation.ts` — shared interfaces
