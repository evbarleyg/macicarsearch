# Site generator

`data/board.json` is the single source of truth for the CX-5 buyer's-report site.
`tools/build_site.py` turns it into every published file:

| Output | What |
|---|---|
| `index.html` | the report (TL;DR, what changed, top 3, shortlist table + cards, new candidates, watchlist (parked + side-sweep groups), price-vs-miles chart, trim values, monthly cost / compare / calculator, no-haggle, email template, sources) |
| `status.html` | live board: cars in play, dealer inquiries, sold and removed |
| `map.html` | dealership map (Leaflet 1.9.4 inlined from `tools/assets`, OSM tiles), dealer cards, route groupings |
| `trims.html` | trim guide (static text in `tools/templates/trims.html`) with the generated candidates table |
| `ask.html` | "send us a listing" page: submit button (Google Form), the judging rules, and one card per analysed link, from `data/inbox.json` |
| `CX5-Seattle-Buyers-Report.pdf` | Chromium print of `index.html` |
| `CX5-Seattle-Buyers-Report.xlsx` | Board, Quotes, Monthly cost (live PMT formulas), Sold-removed, Watchlist, Trim values, Sources, Read me |
| `cx5_report.docx` | same content order as the page |

## Refresh workflow

1. Edit `data/board.json`: bump `meta.refreshed`, update each car's `status` (`live` / `sold` / `benchmark` / `parked`),
   `miles`, `daysListed`, `price` (`listed`, `advertised`, `docFee`), `deal`, `latest`, and add `quote` / `counter`
   objects as dealers reply; append to `sweeps` and `changelog`; add new cars with the next rank number.
2. Run `python3 tools/build_site.py` (add `--no-pdf` if Node + Playwright are not installed; the PDF is then left as-is).
3. Commit `data/board.json` together with **all** generated files (`index.html status.html map.html trims.html ask.html`
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

## Ask page / listing inbox

`ask.html` lets a non-technical reader submit a listing link from a phone and read the verdict on the public site.
Submissions arrive through a Google Form whose response sheet is link-viewable; `tools/inbox.py` polls the sheet's
CSV export, queues new links in `data/inbox.json`, and `build_site.py` renders every item as a card (nav chip "Ask"
on all pages, plus the "Have a listing you want checked?" link in the report masthead).

`data/inbox.json`:

- `config.formUrl`: the form's "Send → link" URL (the big button on ask.html; while `null` the page shows
  "Submission form not connected yet").
- `config.sheetCsvUrl`: the response sheet, either the CSV export URL
  (`https://docs.google.com/spreadsheets/d/<ID>/export?format=csv&gid=<GID>`) or the ordinary `.../edit#gid=<GID>`
  link (the export URL is derived). The sheet must be shared "Anyone with the link: Viewer".
- `config.pollNote`: free text shown next to the button ("checked hourly").
- `items[]`: `{ id (sha1 of the normalised URL), url, submittedAt, submittedNote, submitter (first name only), status
  queued | analyzing | done | error, analyzedAt, listing {year, make, model, trim, miles, price, docFee, dealer, city,
  state, vin, stock, daysListed, priceHistory[{date, price, note}], history {owners, accidents, rental, cpo},
  deal {cgRating, cgDelta, kbbFpp, kbbDelta}, photos, links {source, cargurus, kbb}}, numbers {taxRate, estOtd,
  monthly0, monthly5k, basis}, verdict {label pursue | benchmark | skip | not a CX-5 | couldn't load, oneLine,
  bullets[], flags[] ("RED: …" / "YELLOW: …" / "GREEN: …" colour the flag), openingMove, targetOtd, slot}, error? }`.
  If `numbers` is missing the page computes the estimate itself from `listing.price`, the dealer-city rate in
  `taxRatesByCity`, the doc fee and the licence constant.

`tools/inbox.py` subcommands (all take `--inbox PATH`, default `data/inbox.json`):

| Command | What |
|---|---|
| `fetch [--csv-file F] [--dry-run]` | GET the sheet CSV (urllib, through the environment's proxy settings) or read a local CSV; match the Timestamp / Link / Notes / Name columns by header keywords (extra columns such as an e-mail address are ignored); pull every http(s) URL out of the link cell (people paste sentences around links; `www.` gets `https://`, `javascript:` / `ftp:` and friends are dropped); normalise (lower-case host, strip `utm_*`, `resultSetId`, `searchUuid`, `srpc`, `ourls`, `sourceId`, `sourceContext`, `searchZip`, `distance`, click ids …; keep listing ids, including CarGurus' `#listing=` hash); de-duplicate against existing items by id; append new ones as `queued`. Prints the newly queued items as JSON on stdout, a one-line summary (and what was skipped) on stderr. |
| `list-queued` | queued / analyzing items (id, url, submittedAt, note) as JSON |
| `start <id>` | optional: mark an item `analyzing` (id prefixes of 6+ characters are accepted) |
| `record <id> analysis.json` | validate the file against the item schema (types, enum, length caps; unknown keys dropped with a warning; HTML tags stripped from every string; links must be http(s)), attach `listing` / `numbers` / `verdict`, set `status` done (or error when the file carries `error` and no listing, or says so) and `analyzedAt` |
| `render [args]` | runs `python3 tools/build_site.py [args]`; the generator already renders the inbox, so this is only a convenience hook |

Everything that comes through the sheet is untrusted text. `fetch` caps notes at 300 characters, reduces names to a
first name, strips tags and control characters and refuses non-http(s) schemes; `record` re-sanitises the analysis;
`build_site.py` HTML-escapes every inbox field again and emits `ask.html` with no script at all. Nothing from the sheet
or from an analysed page is ever executed or rendered as markup.

### Hourly routine

1. `git pull --ff-only`, then `python3 tools/inbox.py fetch`. If stdout is `[]`, stop.
2. For each item from `python3 tools/inbox.py list-queued`, an analyst evaluates the link read-only: load the dealer
   VDP (and the CarGurus / KBB pages for the same VIN), confirm it is actually a CX-5 and which trim, pull price / doc
   fee / miles / days listed / price history / photos / history badges, cross-check the asking price against KBB Fair
   Purchase Price and the CarGurus market value, apply the board filters (years and trims, under 50k mi, no accident /
   rental / lemon flags, real VIN and photos, Select-type trims only at $3k+ under market), estimate out-the-door at
   the dealer-city rate + $200 doc + $600 licence and the monthly payment at `meta.apr` / `meta.termMonths` ($0 and
   $5k down), place it against the live board's cost table, and write a verdict (label, one line, bullets, RED /
   YELLOW / GREEN flags, opening move with a target OTD, where it would slot). The output of this step is one
   `analysis.json` per item and nothing else.
3. `python3 tools/inbox.py record <id> analysis.json` for each, then `python3 tools/build_site.py`, commit
   `data/inbox.json` + the regenerated pages, push `main`.

Public-page rules carry over: the Ask page shows estimates only (dealer-quoted out-the-door figures from private
correspondence stay off it, exactly as on the report), submitter names are first names only, and a "pursue" verdict
never edits `data/board.json`; promoting a car onto the numbered board stays a manual, reviewed change.

**Keep step 2 and step 3 apart.** The links come from a public, anonymous form, so a submitted page can contain text
aimed at whoever (or whatever) is reading it. The analyst step that opens those pages should run without git
credentials or any way to write to this repository: it reads pages and emits `analysis.json`, full stop. The recording
step (`record` → build → commit → push) runs separately, never opens the submitted URLs or ingests raw page content, and
only ever touches `data/inbox.json` and the generated files; anything else showing up in `git status` at that point is
a reason to stop and have Evan look at the diff before it is pushed. `record`'s schema check bounds what can reach the
page, but it is the separation, not the schema, that bounds what a hostile page can do.

## Requirements

Python 3.9+ with `openpyxl` and `python-docx` (`pip install openpyxl python-docx`). The PDF step shells out to
`node` with the `playwright` package and its Chromium build; without them the script prints a warning and skips the PDF.
No network access is needed to build (map tiles load in the reader's browser).
