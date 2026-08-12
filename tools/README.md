# Site generator

`data/board.json` is the single source of truth for the CX-5 buyer's-report site.
`tools/build_site.py` turns it into every published file:

| Output | What |
|---|---|
| `index.html` | the report (TL;DR, what changed, top 3, shortlist table + cards, new candidates, watchlist (parked + side-sweep groups), price-vs-miles chart, trim values, monthly cost / compare / calculator, no-haggle, email template, sources) |
| `status.html` | live board: cars in play, dealer inquiries, sold and removed |
| `map.html` | dealership map (Leaflet 1.9.4 inlined from `tools/assets`, OSM tiles), dealer cards, route groupings |
| `trims.html` | trim guide (static text in `tools/templates/trims.html`) with the generated candidates table |
| `CX5-Seattle-Buyers-Report.pdf` | Chromium print of `index.html` |
| `CX5-Seattle-Buyers-Report.xlsx` | Board, Quotes, Monthly cost (live PMT formulas), Sold-removed, Watchlist, Trim values, Sources, Read me |
| `cx5_report.docx` | same content order as the page |

## Refresh workflow

1. Edit `data/board.json`: bump `meta.refreshed`, update each car's `status` (`live` / `sold` / `benchmark` / `parked`),
   `miles`, `daysListed`, `price` (`listed`, `advertised`, `docFee`), `deal`, `latest`, and add `quote` / `counter`
   objects as dealers reply; append to `sweeps` and `changelog`; add new cars with the next rank number.
2. Run `python3 tools/build_site.py` (add `--no-pdf` if Node + Playwright are not installed; the PDF is then left as-is).
3. Commit `data/board.json` together with **all** generated files (`index.html status.html map.html trims.html`
   + PDF / XLSX / DOCX). Never hand-edit the generated files — the next run overwrites them.

Every section derives from the board file, so nothing can go stale relative to anything else:

- Sold cars appear only in the "Removed as sold" line, the status board's sold table, the Sold sheet and as hollow
  unlabeled chart markers.
- Cost table, compare box, calculator example, top picks, chart labels, trim-table "lowest clean listing", the
  Excel Monthly-cost sheet and the Word tables include live cars only (plus the no-haggle benchmark as a reference row).
- Where a car has a written quote with an out-the-door figure, that OTD replaces the estimate everywhere
  (`est. OTD = advertised × (1 + dealer-city rate) + doc + licence`; Oregon dealers at the 11.05% WA use-tax rate).
- Cheapest solid / stretch and the top-3 fallback are computed by rule (see `SOLID_RULE` / `STRETCH_RULE` in the script);
  the calculator's static example is asserted equal to the cheapest-solid car's cost-table row at build time.
- Prose fields in `board.json` may use `{days}` (that car's days listed) and `{refreshed}` / `{published}` placeholders.
- `watchlist` items are flat; an optional `group` key files an item under a `watchlistGroups` entry (`key`, `title`,
  `intro`). Untagged items belong to the first group ("Screened and parked", compact table); later groups (e.g.
  `"2024 watch"`) render as their own sub-heading with the detail table (year / trim / VIN / miles / price / `estOtd` /
  `monthly` / `history` / `flags` / `whyNot`) on the page, the Watchlist sheet and the Word file. Watchlist cars are never
  numbered board cars and never enter the picks, cost table, chart or trim table.
- `sweeps` entries without a `scope` are board re-checks (newest first; the first one drives the TL;DR and status
  header). An entry with `scope` set to a watchlist group key is a side sweep: it appears in the TL;DR as a one-line
  "watchlist only" note, under its watchlist group, and in the Sources sweep lists, but never counts as a board re-check.

## Requirements

Python 3.9+ with `openpyxl` and `python-docx` (`pip install openpyxl python-docx`). The PDF step shells out to
`node` with the `playwright` package and its Chromium build; without them the script prints a warning and skips the PDF.
No network access is needed to build (map tiles load in the reader's browser).
