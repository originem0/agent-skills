# CSS Variables & Design Rules

## Available CSS Variables

**Text:** `--color-text-primary`, `--color-text-secondary`
**Background:** `--color-bg-primary`, `--color-bg-secondary`
**Border:** `--color-border`, `--color-border-light`
**Semantic:** `--color-blue` (info), `--color-green` (success), `--color-amber` (warning), `--color-red` (error)
**Category:** `--color-purple`, `--color-teal`, `--color-coral`, `--color-pink`, `--color-gray`
**Spacing:** `--spacing-xs` (4), `--spacing-sm` (8), `--spacing-md` (16), `--spacing-lg` (24), `--spacing-xl` (32)
**Radius:** `--border-radius-sm` (4), `--border-radius-md` (8), `--border-radius-lg` (12)
**Fonts:** `--font-sans`, `--font-mono`

## Design Rules

- Flat: no gradients, mesh backgrounds, decorative effects
- Borders 0.5px, generous whitespace, no shadows (except focus rings)
- Font-weight 400 and 500 only. h1=22px, h2=18px, h3=16px, body=16px, line-height 1.7
- Sentence case always, never Title Case or ALL CAPS
- Category colors: purple, teal, coral, pink. Semantic reserved: blue=info, green=success, amber=warning, red=error
- Tooltips: use `position: fixed` + `z-index: 1000` to avoid clipping
- All content vertical stack, container auto-sizes to content height

## SVG Text Classes

- `.t` — 14px primary
- `.ts` — 12px secondary
- `.th` — 14px medium weight

## SVG Color Classes

`.c-blue`, `.c-teal`, `.c-purple`, `.c-coral`, `.c-pink`, `.c-amber`, `.c-green`, `.c-red`, `.c-gray`
