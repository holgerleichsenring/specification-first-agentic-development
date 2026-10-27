# Coding Principles: website

## Content

- Every claim about the plugin is backed by a skill, hook or template in this repository. A number
  carries where it was counted and when.
- Copy goes through the humanizer before it ships: plain sentences, no em dashes, no headline that
  explains the page.
- Authorship: Holger Leichsenring is author, creator, maintainer and copyright holder (JSON-LD and footer).

## Markup and style

- Colours, fonts and sizes come from the tokens in `src/static/tokens.css`; components never use a
  literal colour that works in one theme only. Light is the default, dark follows `prefers-color-scheme`.
- Product views (spec sheet, verdict, decision file, gate ledger, series board) are HTML, not images.
- The page is complete without JavaScript and without motion; `main.js` adds copy buttons, tabs and
  the board animation, and respects `prefers-reduced-motion`.
- No horizontal scroll at 375 px; grid children that hold text or code get `min-width: 0`.

## Build

- `npm run build` runs the link check; a missing local target fails the build.
- No build step reaches outside `website/`.
