# CX-5 re-sweep — Wed Aug 12, 2026 (read-only)

_Captured 2026-08-12T00:11:53.832Z. 386 raw records → 223 unique VINs (+14 no-VIN). Prior universes: Aug 7 153 VINs, Aug 11 198 VINs._

**Sources today:** AutoTempest 125 · CarGurus VDPs 47 (VDPs via AutoTempest IDs + board ids: 50/50 ok, 3 CLOSED/removed) · KBB 45 · CarMax 96 · Carvana via AT 59 · Craigslist 14. Read-only page loads / JSON GETs; no forms, no availability clicks.

Precedence used for the board: dealer comms logged in the repo (sold confirmations, quotes, confirmed trim) > today's scrape > older scrapes. A repo-recorded SOLD is never overridden by a lagging syndicated listing.

## 1 · Board status (#1–#20)

| # | Car · dealer | Recorded | Today (listed) | Δ | DOM | Deal today | Verdict | Signals | Latest known (comms) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2023 2.5 Turbo AWD · Puyallup Mazda (WA) | $28,199 | $28,199 <br>cg $28,199 · kbb $27,999 · kbb_vdp $27,999 · at $28,199 | = | 89 | CG Great · $1,945 vs IMV | active (3 src) | CG active $28,199 · 89d; KBB SRP $27,999; KBB VDP $27,999 · 88d on site; AT: CarGurus $28,199 | Awaiting written OTD: form lead Aug 11 + phone promise, nothing received yet |
| 2 | 2022 2.5 Turbo AWD · Acura of Seattle (WA) | $27,300 | **sold** | — | — | — | SOLD (repo-confirmed; not overridden) | CG closed | Sold (confirmed Aug 11 PM) |
| 3 | 2021 Grand Touring Reserve AWD (2.5T) · BMW Seattle (WA) | $24,999 | **sold** <br>cg $24,999 · at $24,999 | — | — | — | SOLD (repo-confirmed; not overridden) | CG closed; KBB VDP removed/expired; AT: Cars.com $24,999 | Sold (dealer-confirmed by phone Aug 11) |
| 4 | 2021 Carbon Edition Turbo AWD (turbo confirmed by dealer) · Ron Tonkin Honda (OR) | $26,102 | $26,302 <br>cg $26,302 · kbb $26,512 · kbb_vdp $26,512 · at $26,302 | = | 64 | CG Fair · $149 vs IMV | active (3 src) | CG active $26,302 · 64d; KBB SRP $26,512; KBB VDP $26,512 · 63d on site; AT: CarGurus $26,302; dealer VDP http 200 VIN present | Quote in preparation (Aug 11 3:57 PM); Evan’s counter $28,500 OTD sent; OR: email-only leverage |
| 5 | 2021 Grand Touring AWD (GT Premium pkg) · Hyundai / Ford of Kirkland (WA) | $25,192 | $25,192 <br>cg $25,192 · kbb $25,192 · kbb_vdp $25,192 · at $25,192 | = | 48 | CG Good · $1,088 vs IMV | active (3 src) | CG active $25,192 · 48d; KBB SRP $25,192; KBB VDP $25,192 · 63d on site; AT: CarGurus $25,192 | Written quote Aug 11 4:21 PM: $24,992 selling / $28,591.14 OTD, zero add-ons; accept + deposit hold staged |
| 6 | 2021 Carbon Edition Turbo AWD · Puyallup Mazda (WA) | $25,198 | $25,198 <br>cg $25,198 · kbb $24,998 · kbb_vdp $24,998 · at $25,198 | = | 69 | CG Great · $1,939 vs IMV | active (3 src) | CG active $25,198 · 69d; KBB SRP $24,998; KBB VDP $24,998 · 61d on site; AT: CarGurus $25,198 | Awaiting written OTD: same Puyallup lead as #1 (Aug 11), phone promise only |
| 7 | 2022 2.5 S Carbon Edition AWD · Mazda CPO · Lee Johnson Mazda of Seattle (WA) | $27,512 | $27,512 <br>cg $27,512 · kbb $27,512 · kbb_vdp $27,512 · at $27,512 | = | 30 | CG Good · $349 vs IMV | active (3 src) | CG active $27,512 · 30d; KBB SRP $27,512; KBB VDP $27,512 · 30d on site; AT: CarGurus $27,512 | Awaiting: two-car OTD request (#7 + #12) emailed Aug 11 3:50 PM, no reply yet |
| 8 | 2023 2.5 S Preferred AWD · Royal Moore Mazda (OR) | $26,900 | $26,900 <br>cg $26,900 · kbb $26,900 · at $26,900 | = | 15 | CG Good · $469 vs IMV | active (3 src) | CG active $26,900 · 15d; KBB SRP $26,900; AT: Cars.com $26,900 | Written quote Aug 11 (PDF, figures not yet transcribed; lists Courtesy Guard + Forever Start add-ons); countered $29,600 OTD; OR: email-only |
| 9 | 2023 2.5 S Carbon Edition AWD · Mazda CPO · Puyallup Mazda (WA) | $27,699 | $27,699 <br>cg $27,699 · kbb $27,499 · kbb_vdp $27,499 · at $27,699 | = | 58 | CG Good · $518 vs IMV | active (3 src) | CG active $27,699 · 58d; KBB SRP $27,499; KBB VDP $27,499 · 57d on site; AT: CarGurus $27,699 | Awaiting: folded into the Puyallup #1/#6 inquiry; no written numbers yet |
| 10 | 2023 2.5 S Preferred AWD · Columbia Sales & Service (independent) (OR) | $24,095 | $23,995 <br>cg $23,995 · at $23,995 | = | 29 | — | active (2 src) | CG active $23,995 · 29d; AT: CarGurus $23,995 | Emailed Aug 11, no reply; OR indie: Carfax + inspection before any visit |
| 11 | 2022 Carbon Edition · CarMax Sacramento South (CA) | $24,998 | **sold** | — | — | — | SOLD (repo-confirmed; not overridden) | CarMax absent from CarMax API results (98101, ≤$29k, ≤50k mi) | Sold (Aug 11 PM) |
| 12 | 2023 2.5 S Preferred AWD · Mazda CPO · Lee Johnson Mazda of Seattle (WA) | $26,348 | — | — | — | — | unverified today (Cars.com-only listing; Cars.com VDP bot-blocked (403) from this environment; never in the AutoTempest feed) | — | Awaiting: in the Lee Johnson two-car request (Aug 11 3:50 PM), no reply yet |
| 13 | 2022 2.5 S Premium Plus AWD · Titus-Will Chevrolet GMC Cadillac (WA) | $27,389 | $27,389 <br>kbb $27,389 · kbb_vdp $27,389 · at $27,789 | = | 45 | KBB Good $-389 under FPP | active (2 src) | KBB SRP $27,389; KBB VDP $27,389 · 45d on site; AT: Cars.com $27,789 | Revised written quote Aug 11 4:43 PM: $27,268.60 selling / $31,000 OTD, KARR add-on struck (first sheet was $32,229.17); Evan holding at $30,200 |
| 14 | 2023 2.5 S Premium AWD · Rodland Toyota of Everett (WA) | $28,487 | $28,487 <br>cg $28,487 · kbb $28,287 · kbb_vdp $28,287 · at $28,487 | = | 29 | CG Good · $873 vs IMV | active (3 src) | CG active $28,487 · 29d; KBB SRP $28,287; KBB VDP $28,287 · 28d on site; AT: CarGurus $28,487 | Quote $31,957.24 OTD Aug 11 (clean: $0 add-ons, $200 doc, tax + licence lumped $3,470.24); countered $31,100; ask for itemized tax/licence |
| 15 | 2023 2.5 S Premium AWD · CarMax Renton (no-haggle) (WA) | $27,998 | $27,998 <br>cg $27,998 · carmax $27,998 · at $27,998 | = | 3 | CG Fair · $222 vs IMV | active (3 src) | CG active $27,998 · 3d; AT: CarGurus $27,998; CarMax API $27,998 | No-haggle benchmark, fixed $27,998, no transfer fee; nothing to request |
| 16 | 2021 Grand Touring AWD · Doug’s Lynnwood Mazda (WA) | $28,700 | **sold** | — | — | — | SOLD (repo-confirmed; not overridden) | AT: Cars.com $28,700 | Sold (dealer email Aug 11) |
| 17 | 2021 Grand Touring w/ GT Premium Pkg AWD · Auto 206 (independent) (WA) | $25,799 | $25,999 <br>cg $25,999 · kbb $25,799 · kbb_vdp $25,799 · at $25,999 | = | 5 | KBB  $3,281 under FPP | active (3 src) | CG active $25,999 · 5d; KBB SRP $25,799; KBB VDP $25,799 · 5d on site; AT: CarGurus $25,999 | Quote $28,718.60 OTD ($25,400 selling, clean sheet) valid to Aug 12 7 PM; $27,000 + PPI counter declined; Carfax 06/2024 accident |
| 18 | 2023 2.5 S Preferred AWD · Auto Connections of Bellevue (independent) (WA) | $26,495 | **sold** <br>cg $26,495 · kbb $26,495 · at $26,495 | — | 61 | CG Good · $1,200 vs IMV | SOLD (repo-confirmed; not overridden) | CG active $26,495 · 61d; KBB SRP $26,495; AT: Cars.com $26,495 | Sold (GM email Aug 11) |
| 19 | 2021 Signature AWD (2.5T) · Tonkin Gresham Honda (OR) | $26,712 | $26,712 <br>cg $26,712 · kbb $26,462 · at $26,712 | = | 18 | CG Good · $700 vs IMV | active (3 src) | CG active $26,712 · 18d; KBB SRP $26,462; AT: CarGurus $26,712 | Not contacted (OR fallback: email-only per Evan’s rule) |
| 20 | 2023 2.5 S Preferred AWD · Royal Moore Toyota (same group as #8) (OR) | $26,500 | $26,500 | = | — | — | active (1 src) | AT: Cars.com $26,500 | Folded into the #8 thread: $29,400 OTD counter sent Aug 11 3:35 PM, no separate quote yet |

### Sold list (with evidence)

- **#2 Acura of Seattle 2022 2.5 Turbo AWD** — sold Aug 11 (repo): CarGurus closed-listing page + KBB expired + dealer VIN search empty (Aug 11). Today: CG closed.
- **#3 BMW Seattle 2021 Grand Touring Reserve AWD (2.5T)** — sold Aug 11 (repo): Dealer told Evan by phone Aug 11 10:18 AM PT; KBB listing expired; CarGurus syndication lagged. Today: CG closed; KBB VDP removed/expired; AT: Cars.com $24,999.
- **#11 CarMax Sacramento South 2022 Carbon Edition** — sold Aug 11 (repo): CarMax VDP Sold badge; absent from CarMax API (Aug 11). Today: CarMax absent from CarMax API results (98101, ≤$29k, ≤50k mi).
- **#16 Doug’s Lynnwood Mazda 2021 Grand Touring AWD** — sold Aug 11 (repo): Dealer email Aug 11 17:59Z: sold the day before. Today: AT: Cars.com $28,700.
- **#18 Auto Connections of Bellevue (independent) 2023 2.5 S Preferred AWD** — sold Aug 11 (repo): GM email Aug 11 18:51Z: just sold. Today: CG active $26,495 · 61d; KBB SRP $26,495; AT: Cars.com $26,495.
- No additional car met the two-source SOLD-LIKELY bar today.

**Single-source / unverified (“check”):**
- #12 Lee Johnson Mazda of Seattle: unverified today (Cars.com-only listing; Cars.com VDP bot-blocked (403) from this environment; never in the AutoTempest feed) — no source reachable from this environment (Cars.com/Autotrader are bot-blocked)

## 2 · Price moves today (board)

No listed-price change on any live board car vs the recorded figure, compared source-by-source (CarGurus shows several WA cars $200 higher than KBB/Autotrader because CG folds the $200 doc fee into 'price includes fees'; those are not moves).

**Watchlist (parked) cars — price moves ≥$250 flagged:**

| Car | Dealer | Was | Now | Δ | Src | Note |
|---|---|---|---|---|---|---|
| 2022 2.5 S Carbon Edition, 47,333 mi, $26,998+$200 | Doug's Lynnwood Mazda | $27,198 | $27,198 | = | CG | 15d Fair  |
| Mazda CPO 2022 2.5 S Select, 48,468 mi, $24,081+$299 | West Hills Mazda, Bremerton | $24,081 | $24,081 | = | KBB(VDP via AT id) |   active |
| 2023 2.5 S Carbon Edition, 28,928 mi, $27,060+$200 | Titus-Will Used Cars - Olympia | $27,260 | $27,260 | = | CG | 28d Good  |
| 2023 2.5 S Carbon Edition, 23K mi, $28,998 | Rodland Toyota of Everett | $28,998 | $28,998 | = | KBB(VDP via AT id) |   active |
| 2.5 S Preferred AWD (year unverified), 33,261 mi, $25,695+$200 | GoldBoyz Auto Sales, Puyallup (indie) | $25,895 | $25,895 | = | CG | 71d Good  |
| 2022 2.5 S Select, 28,548 mi, $24,995+$200 | Pacific Coast Auto Center, Burlington (indie) | $25,195 | $25,195 | = | CG | 77d Fair  |
| 2021 Touring, 21,391 mi, $27,999-$28,199 | Mazda of Everett | $27,999 | $27,999 | = | KBB(VDP via AT id) |   active |
| 2021 Carbon Edition Turbo, 39,412 mi, $27,722 | Tonkin Gresham Honda | $27,722 | $27,722 | = | AT/Cars.com |    |
| 2023 2.5 S Carbon Edition, 32,594 mi, $27,400 | Lexus of Portland | $27,400 | not seen today | — | — |    |
| 2023 2.5 S Select, 13,555 mi, $25,950 | Lexus of Portland | $25,950 | $25,950 | = | AT/Cars.com |    |

## 3 · New candidates (strict screen)

_26 VINs not seen on Aug 7 or Aug 11 and not on the board/watchlist → 25 disqualified → **1 pass**._

| Proposed # | Year · trim | Miles | Price | Dealer · city | VIN | Value signal | History | Days listed | URL | Why it ranks |
|---|---|---|---|---|---|---|---|---|---|---|
| #21 | 2021 Signature | 35,589 | $25,999 | Cortes Auto Center · Burlington, WA | JM3KFBEY0M0417715 | CG Good; $-789 under KBB FPP $25,410; wanted trim < $27,998 & ≤40k mi | 1-owner / 0 acc | 0 | https://www.kbb.com/cars-for-sale/vehicle/787933636 | WA dealer; CG Good; $-789 under KBB FPP $25,410; wanted trim < $27,998 & ≤40k mi |

**Seen but not eligible:** Craigslist Camas WA post: 2023 2.5 S Premium AWD, ~32,968 mi, $24,900, "clean title" — already in the Aug 11 CL pull and carries no VIN (fails VIN-present rule); seller type not exposed on the search card. Not added; worth a manual look only if Evan wants a private-party option.

**Disqualified new VINs (25):**

20× no value signal · 5× unwanted trim · 1× fleet/rental

- 2023 2.5 S Premium Plus Sport Utility 4D · $27,990 · 40,702 mi · null (Akron, NY) · Carvana · JM3KFBEMXP0193564 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Carbon Edition Sport Utility 4D · $27,990 · 41,253 mi · null (Manville, NJ) · Carvana · JM3KFBCM7P0237037 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Premium Plus Sport Utility 4D · $28,590 · 27,491 mi · null (Framingham, MA) · Carvana · JM3KFBEM1P0117702 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2021 Touring · $23,998 · 35,971 mi · CarMax Texas Stadium (Irving) (Irving, TX) · CarMax · JM3KFACM0M0460364 — unwanted trim (2021 Touring w/o Preferred pkg)
- 2021 Carbon Edition Turbo · $25,998 · 41,437 mi · CarMax Bakersfield (Bakersfield, CA) · CarMax · JM3KFBCY1M0463217 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Select Package · $27,998 · 17,590 mi · CarMax Nashville (Nashville, TN) · CarMax · JM3KFBBM4P0287587 — unwanted trim (Sport/Select)
- 2023 Carbon Edition · $27,998 · 21,750 mi · CarMax Huntsville (Huntsville, AL) · CarMax · JM3KFBCM0P0127382 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Premium Package · $27,998 · 36,494 mi · CarMax Brandywine (Brandywine, MD) · CarMax · JM3KFBDM2P0248851 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Preferred Package · $27,998 · 25,987 mi · CarMax Albany (Albany, NY) · CarMax · JM3KFBCM4P0161759 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 Carbon Edition · $27,998 · 26,908 mi · CarMax Wayne (Wayne, NJ) · CarMax · JM3KFBCM8P0117957 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Premium Package · $27,998 · 24,241 mi · CarMax Mays Landing (Mays Landing, NJ) · CarMax · JM3KFBDM4P0124404 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 Carbon Edition · $27,998 · 31,828 mi · CarMax Sample Rd (Pompano Beach) (Pompano Beach, FL) · CarMax · JM3KFBCM6P0255660 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 Carbon Edition · $27,998 · 22,278 mi · CarMax Miami Lakes (Miami Lakes, FL) · CarMax · JM3KFBCM8P0253571 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 Carbon Edition · $28,998 · 11,955 mi · CarMax Henderson (Henderson, NV) · CarMax · JM3KFBCMXP0163998 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Premium Package · $28,998 · 11,585 mi · CarMax Buena Park (Buena Park, CA) · CarMax · JM3KFBDM6P0248576 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2022 2.5 Turbo Signature · $28,998 · 39,357 mi · CarMax Garland (Garland, TX) · CarMax · JM3KFBXYXN0559505 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 Carbon Edition · $28,998 · 26,888 mi · CarMax Gastonia (Gastonia, NC) · CarMax · JM3KFBCM4P0247959 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 Carbon Edition · $28,998 · 35,372 mi · CarMax Lynchburg (Lynchburg, VA) · CarMax · JM3KFBCM7P0213286 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Premium Plus Package · $28,998 · 27,445 mi · CarMax King of Prussia (King of Prussia, PA) · CarMax · JM3KFBEM6P0223353 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2022 2.5 S Premium Package · $28,998 · 17,202 mi · CarMax Norwood (Norwood, MA) · CarMax · JM3KFBDM0N0613122 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Preferred Package · $28,998 · 4,940 mi · CarMax Naples (Naples, FL) · CarMax · JM3KFBCM1P0285200 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2022 2.5 S Select Package · $22,998 · 29,590 mi · CarMax Kansas City (Merriam, KS) · CarMax · JM3KFBBM5N0626208 — unwanted trim (Sport/Select)
- 2021 Carbon Edition Turbo · $23,998 · 42,272 mi · CarMax Bakersfield (Bakersfield, CA) · CarMax · JM3KFACY4M0385803 — no value signal (not CG Good/Great, not ≥$500 under KBB FPP, not under $27,998 with ≤40k mi)
- 2023 2.5 S Select Package · $23,998 · 33,998 mi · CarMax LAX (Inglewood, CA) · CarMax · JM3KFBBM1P0231770 — unwanted trim (Sport/Select); fleet/rental
- 2021 Touring · $23,998 · 36,711 mi · CarMax Tampa (Tampa, FL) · CarMax · JM3KFACM2M1332105 — unwanted trim (2021 Touring w/o Preferred pkg)

## 4 · Market movement

- 197 VINs seen both Aug 11/7 and today: median =, 17 down, 2 up.

_Files: listings_0812.json (raw per source), cg_vdp_0812.json, kbb_vdp_0812.json, carmax_items_0812.json, resweep_0812.json (this analysis, structured)._
