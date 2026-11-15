> **Update:** the primary UI is now the React app in `frontend/` (Tailwind design tokens in
> `frontend/DESIGN_TOKENS.md`; deployment in `docs/DEPLOYMENT.md`). The Jinja templates and
> `theme.css` below still work as a local fallback.

# UI / design system

The interface uses a **dark red** theme driven entirely by CSS custom properties.

## Token source of truth

All color and spacing live in **`app/static/css/theme.css`** (`:root`). No color
literal appears anywhere else in the app's CSS or templates — components reference
`var(--*)` only. To re-skin the whole platform, edit that one file.

Key tokens: `--bg --surface --surface-2 --border --text --text-muted --accent
--accent-text --btn --btn-hover --success --warning --danger`, spacing scale
`--space-1..8`, `--radius`, `--ring` (focus).

Accessibility: body text ≥ 4.5:1, large text/icons ≥ 3:1 (WCAG AA). `--btn`
(#C3262F) is only ever a button **fill** with white text; red **text** on the
dark background always uses `--accent-text` (#F06A6E). Every interactive element
shows a visible `--ring` focus outline.

Difficulty badges: Very Easy = muted, Easy = `--success`, Medium = `--warning`,
Hard = `--danger`, Insane = `--accent` with outline.

## Components

`app/static/css/app.css` defines the reusable classes; `templates/_components.html`
holds Jinja macros (`stat_card`, `diff_badge`, `status_badge`, `progress_bar`,
`empty_state`). Shared pieces: `.btn` (+`.secondary/.ghost/.danger/.sm/.block`),
`.card`, `.badge` (+status/difficulty variants), `.stat`, `table.data`, inputs,
`.alert` (`ok/err/warn/info`), `.toast` (via `toast()` in `app.js`), `.empty-state`,
`.modal`, `.tabs`, `.toggle-group`, `.toolbar`, `.chip-tabs`, `.progress`, `.skill`.

## Layout

`templates/base.html` is the authenticated shell:
- **Left sidebar** (persistent, collapses to a hamburger drawer < 900px): Dashboard,
  Challenges, Scoreboard, Profile, Docs; a *Learn* section (Learning Paths,
  Achievements); and an *Admin* section shown only to administrators. The active
  page is highlighted.
- **Top bar**: hamburger + breadcrumb + page title on the left; a score/rank chip
  and an avatar menu (Profile, Log out) on the right. The chip is fed by read-only
  `nav_score`/`nav_rank` from the context processor in `app/__init__.py`.

Standalone pages (landing, auth, error) link `theme.css` + `app.css` directly.

## Per-page notes

- **Dashboard**: four stat cards (score, rank, solved x/total, day streak),
  a *Continue where you left off* card (running lab → last unsolved → recommended),
  recent solves, and per-category progress bars.
- **Challenges**: toolbar (search + category/difficulty/status filters), uniform
  cards with a status tag (New / In progress / Solved), sorted by category, with an
  empty state when filters match nothing.
- **Play screen**: Brief / Split / Lab view toggle + draggable divider; left brief
  (description, objectives, resources, collapsible hints with point cost) with a
  sticky flag-submission bar (correct = success, wrong = danger, rate-limited =
  warning); right lab pane with a toolbar (status dot, Open in tab, Restart, Stop).
- **Profile**: stats header with avatar, solved-challenges table, category
  breakdown bars, badges.
- **Docs**: sticky table of contents + a ≤75ch readable column.
- **Admin**: tabbed (Challenges, Users, Labs monitor, Audit log, Analytics) over a
  persistent stat row; Analytics loads from `/admin/api/analytics`.

No backend, challenge, or security behavior changed in the redesign. The only
Python touched is read-only presentation data (top-bar chip, dashboard
streak/continue, catalog status, profile category breakdown).
