---
name: widget-viewer
description: >
  Use when the user asks for charts, diagrams, visualizations, interactive explanations,
  data plots, UI mockups, or any visual content better shown graphically than as text.
  Triggers: "画图", "图表", "可视化", "展示", "visualize", "chart", "diagram", "plot",
  "show me", "draw", "interactive". Renders widget HTML in a native WebView2 window
  via claude-widget-viewer.exe.
---

# Widget Viewer

Write widget HTML to `.claude/widgets/<snake_case_name>.html` — a hook auto-launches a native WebView2 window. Raw fragment only: no `<!DOCTYPE>`, `<html>`, `<head>`, `<body>`. Structure: `<style>` → content → `<script>`.

## Mandatory Rules

- NEVER use fixed pixel widths on containers. All containers: `width: 100%`.
- ALWAYS read colors from CSS variables via `getComputedStyle`. Never hardcode hex values.
- ALWAYS set `responsive: true` on Chart.js. ALWAYS wrap `<canvas>` in `<div class="chart-wrap">`.
- ALWAYS use `onload` + fallback for CDN scripts.
- CDN whitelist: `https://cdnjs.cloudflare.com`, `https://cdn.jsdelivr.net`, `https://unpkg.com`. Fonts: `https://fonts.googleapis.com`.
- SVG: ALWAYS use `viewBox` + `width="100%"`. Never set fixed pixel width on `<svg>`.
- Overwrite same filename when iterating — hot-reload updates without reopening.

## Templates

Read the template file, copy it, then modify `type`, `labels`, `datasets`, title, etc. Do NOT remove tooltip/animation/scale config from Chart.js template.

| Need | Template file | Notes |
|------|--------------|-------|
| Line / bar / doughnut chart | `templates/chartjs.html` | Bar: `type:'bar'`, remove fill/tension, add `borderRadius:4`. Doughnut: `type:'doughnut'`, remove scales, multi-color `backgroundColor`. |
| Flow / architecture diagram | `templates/svg-diagram.html` | SVG text classes: `.t` (14px), `.ts` (12px), `.th` (14px medium). Color classes: `.c-blue`, `.c-teal`, `.c-purple`, `.c-coral`, `.c-pink`, `.c-amber`, `.c-green`, `.c-red`, `.c-gray`. |
| Complex interactive viz | `templates/d3.html` | D3 v7. Tooltip uses `position: fixed` to avoid clipping. |

For CSS variables and design rules, see `reference/css-variables.md`.

## When to Use vs Not

**Use:** data visualization, flow diagrams, interactive sliders/controls, chart comparisons, architecture diagrams, math visualizations, UI prototypes

**Don't use:** pure text answers, code explanations, simple lists, anything where text is clearer
