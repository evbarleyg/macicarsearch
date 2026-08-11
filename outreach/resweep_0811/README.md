> **Note (Aug 11, 2026 evening).** Independent Aug 11 re-sweep (AutoTempest 125 · CarGurus VDPs 47 · KBB 45 · CarMax 72 · Carvana-via-AutoTempest 58 · Craigslist 13). Rank numbers inside this folder refer to the ORIGINAL Aug 7 #1–#11 only; for #12+ use the numbering in [`../outreach_data.json`](../outreach_data.json) (this sweep's "additions" were NOT renumbered into that scheme, and several of them — CarMax Renton, Rodland Toyota, Titus-Will Olympia — were picked up independently there under their own numbers).
>
> Items here that were **not** in `../outreach_data.json` / `../README.md` when this was written:
>
> - **(a)** Carvana 2023 CX-5 2.5 Turbo, 35,396 mi, **$26,990**, VIN `JM3KFBAY1P0224760`, <https://www.carvana.com/vehicle/4463370> — cheapest 2023 Turbo seen anywhere in either sweep; Carvana shows no owner/accident history, so pull a Carfax before treating it as a real #2 replacement. (The only Carvana reference in `../outreach_data.json` is the older 2023 Preferred $24,590 anchor.)
> - **(b)** Market-movement stats: 91 new VINs since Aug 7, of which only 3 are local franchise-dealer cars (the rest is Carvana/CarMax nationwide churn); 29 VINs gone; across 107 VINs seen both days the median price change is $0, with 26 drops (avg −$483) and 7 rises (avg +$467).
> - **(c)** #9 (Puyallup Mazda 2023 Carbon CPO) shows **$27,499 on KBB** vs $27,699 on CarGurus — that KBB figure is not in `../outreach_data.json`. The matching $200 KBB-vs-CarGurus gaps on #1 ($27,999) and #6 ($24,998) *are* already recorded there, where they are explained as Puyallup Mazda's price shown without its $200 doc fee (CarGurus displays fees-included). The #9 gap is most likely the same presentation difference rather than a fresh cut, so this sweep's "KBB-only $200 cut" wording for #1/#6/#9 should be read that way.
> - **(d)** #10 (Columbia Sales & Service 2023 Preferred) is now cross-listed on CarGurus — <https://www.cargurus.com/Cars/listing/453316571>, VIN `JM3KFBCM9P0119426`, stock 2468, $23,995, 28 days — and the CarGurus payload reports **2 owners / 0 accidents** (no fleet/rental/lemon/frame flags). `../outreach_data.json` still has this car as VIN unknown / "history unverified".
>
> Already reflected in `../outreach_data.json` (listed here only so nobody double-counts): #2 Acura of Seattle removed, #7 Lee Johnson +$540, #11 CarMax Sacramento sold, CarMax Renton 2023 Premium $27,998 as the new no-haggle floor (their #15), Rodland Toyota Everett 2023 Premium at $28,487 (their #14), and the Rodland 2023 Carbon / Titus-Will Olympia 2023 Carbon (their watchlist). Minor extras only here: the CarMax Fremont/Santa Rosa CA alternates and two more Carvana turbo "bench" units in section 2. Note also that `../outreach_data.json` marks #3 (BMW Seattle) **sold — dealer confirmed Aug 11**, which supersedes this sweep's "active (still on Cars.com/AT)" read below.
>
> Files in this folder: `resweep.json` (structured diff), `shortlist_recheck_0811.json` (per-listing VDP rechecks of the Aug 7 #1–#11). The raw per-source capture `listings_0811.json` (~270 KB) plus `cg_vdp_0811.json`, `carmax_items_0811.json`, `at_parsed_0811.json` referenced at the bottom were kept locally only and are not committed.

---

# CX-5 resweep — Aug 11 vs Aug 7 baseline

_Captured 2026-08-11 · 360 raw records → 198 unique VINs today · Aug 7 baseline: 153 VINs (102 with-VIN passed filter)_

**Source counts (today):** AutoTempest 125 · CarGurus VDPs 47 · KBB 45 · CarMax 72 · Carvana(via AT) 58 · Craigslist 13 · iSeeCars blocked (0)

---

## 1 · Existing shortlist — status

| # | Car | Dealer | Aug 7 | Aug 11 (primary) | Δ | Best cross-source | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | 2023 2.5 Turbo | Puyallup Mazda | $28,199 | $28,199 | = | KBB $27,999 (**−$200**) | active | 88d aged; KBB shows a $200 cut CG hasn't picked up |
| 2 | 2022 2.5 Turbo | Acura of Seattle | $27,300 | **SOLD/REMOVED** | — | — | **removed** | CG listingStatus=CLOSED, "that one got away"; absent from AT/KBB |
| 3 | 2021 GT Reserve (2.5T) | BMW Seattle | $24,999 | $24,999 | = | Cars.com $24,999 | active | Still on Cars.com/AT; dropped off KBB SRP (feed churn, not sold) |
| 4 | 2021 Carbon Edition | Ron Tonkin Honda | $26,512 | $26,512 (KBB) | = | **CG $26,302 (−$210)** | active | Same VIN now on CarGurus at $26,302. Task's "~$660 drop" **not confirmed** — freshest price is −$210 |
| 5 | 2021 Grand Touring | Hyundai of Kirkland | $25,192 | $25,192 | = | KBB $25,192 | active | KBB FPP delta improved to $3,338 under (was $3,048) |
| 6 | 2021 Carbon Ed Turbo | Puyallup Mazda | $25,198 | $25,198 (CG) | = | **KBB $24,998 (−$200)** | active | KBB shows $200 cut |
| 7 | 2022 2.5 S Carbon (CPO) | Lee Johnson Mazda | $26,972 | **$27,512** | **+$540** | KBB $27,512 | active | Confirmed on CG + KBB. FPP delta flipped from $978 under → **$72 over**. No longer a below-market deal |
| 8 | 2023 2.5 S Preferred | Royal Moore Mazda | $26,900 | $26,900 | = | KBB $26,900 | active | Unchanged |
| 9 | 2023 2.5 S Carbon (CPO) | Puyallup Mazda | $27,699 | $27,699 (CG) | = | **KBB $27,499 (−$200)** | active | KBB shows $200 cut |
| 10 | 2023 2.5 S Preferred | Columbia Sales & Svc | $24,095 | **$23,995** | **−$100** | CG $23,995 | active | **Now on CarGurus** — history confirmed **2-own / 0-acc** (was "unverified"). Upgrades this pick |
| 11 | 2022 Carbon Edition | CarMax Sacramento | $24,998 | **SOLD** | — | — | **removed** | VDP shows "Sold" badge; absent from CarMax API |

**Net:** 2 sold (#2, #11) · 1 raised (#7 +$540) · 1 confirmed drop (#10 −$100) · 1 CG cross-list drop (#4 −$210 on CG) · 3 with $200 KBB-only cuts pending (#1/#6/#9) · 3 unchanged (#3/#5/#8).

---

## 2 · New candidates worth adding

_91 VINs appeared since Aug 7 → 59 disqualified → **32 pass filter**. Honest read: **no new local franchise-dealer listing beats the current top 5**. The useful additions are all no-haggle (CarMax/Carvana) that plug the two holes left by #2 and #11._

### Recommended additions (ranked)

| Add as | Source | Year | Trim | Miles | Price | Dealer · City | Deal | Hist | VIN | Rationale | Link |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **replaces #11** (no-haggle floor) | **CarMax** | 2023 | 2.5 S Premium | 31,166 | **$27,998** | CarMax **Renton, WA** · $0 xfer | CG "Good", $298 below | 1-own / 0-acc | JM3KFBDM0P0215315 | Only new **in-WA** CarMax unit; zero transfer; Premium trim > old #11's Carbon; also cross-listed on CG (455754266) so history verified 1-own/0-acc | [carmax](https://www.carmax.com/car/70134808) |
| **replaces #2** (turbo slot) | **Carvana** | 2023 | 2.5 Turbo | 35,396 | **$26,990** | Carvana · San Antonio TX (delivers) | — | ?-own / ? | JM3KFBAY1P0224760 | Cheapest 2023 Turbo anywhere — **$1,209 under #1** and a full model-year newer than the sold #2. No history data (Carvana), pull Carfax | [carvana](https://www.carvana.com/vehicle/4463370) |
| alt for #2 | **CarMax** | 2022 | Turbo | 31,699 | $27,998 | CarMax Fremont, CA · +$449 xfer | — | — / — | JM3KFBAY5N0633535 | Direct like-for-like #2 replacement (2022 Turbo, ~same miles/price); no-haggle | [carmax](https://www.carmax.com/car/70070314) |
| bench | **Carvana** | 2021 | Carbon Ed Turbo | 26,610 | $26,990 | Carvana · Greenfield IN (delivers) | — | ?-own / ? | JM3KFACYXM0382310 | Low-mile 2021 turbo; alt to #6 (16k fewer miles, +$1,792) | [carvana](https://www.carvana.com/vehicle/4610436) |
| bench | **Carvana** | 2022 | 2.5 Turbo | 42,903 | $26,990 | Carvana · Tooele UT (delivers) | — | ?-own / ? | JM3KFBAY7N0639532 | Second 2022 turbo option under $27k; higher miles | [carvana](https://www.carvana.com/vehicle/4580675) |
| bench | CarMax | 2022 | 2.5 S Premium Plus | 44,686 | $25,998 | CarMax Santa Rosa, CA · +$449 xfer | — | — / — | JM3KFBEM3N0628406 | Cheapest Premium Plus (wanted trim) in dataset; alt no-haggle floor | [carmax](https://www.carmax.com/car/28707351) |
| bench | KBB | 2023 | Carbon Edition | 23,182 | $28,998 | Rodland Toyota · Everett, WA | $548 **over** FPP | 1-own / 0-acc | JM3KFBCMXP0160065 | Only new local franchise-dealer listing that passes filter — but priced over FPP; not competitive with #9 | [kbb](https://www.kbb.com/cars-for-sale/vehicle/787184706) |

### New dealers introduced

- **CarMax Renton** — Renton, WA (was previously nationwide-only CarMax picks; this is the first zero-transfer WA unit)
- **Rodland Toyota** — Everett, WA
- **CarMax Fremont / Santa Rosa** — CA (transfer $449)

### New-VIN disqualifications (59)

57× unwanted trim (Select / base 2.5 S / Sport / Touring, not >$3k under year-avg — almost entirely Carvana/CarMax nationwide inventory), 2× accident. Notable DQs: 2023 Carbon $25,696 EchoPark Nashville (accident); 2021 GT $26,975 Kia of Portland (accident, newly listed); 2021 Touring $27,999 Mazda of Everett (unwanted trim, $4k+ over threshold).

### Not-new but moved into contention (existing VINs, price cuts since Aug 7)

Not "new candidates" per the diff rule, but worth noting for the orchestrator:

- **2023 2.5 S Premium · Rodland Toyota Everett · $28,999 → $28,487 (−$512)** · 17,505 mi · 1-own/0-acc · CG "Good" $790 below · VIN JM3KFBDM7P0281828 · [CG 453332129](https://www.cargurus.com/Cars/listing/453332129). **Lowest-mile Premium in the local set** — would slot near #8.
- **2023 2.5 S Carbon · Titus-Will Olympia · $27,760 → $27,260 (−$500)** · 28,928 mi · 2-own/0-acc · CG "Good" $757 below · VIN JM3KFBCM2P0174560 · [CG 453420840](https://www.cargurus.com/Cars/listing/453420840). Cheaper than #9 by $439 with 4k fewer miles (but 2-owner, not CPO).

---

## 3 · Market movement summary

- **New VINs since Aug 7:** 91 (32 pass filter, 59 disqualified). Breakdown by primary source: Carvana 52, CarMax 24, CarGurus 4 (3 are CarMax cross-lists + 1 EchoPark), KBB 3 local, CarSoup 2, Cars.com/other 6. **Net-new local franchise-dealer inventory: 3 VINs** (2 pass, 1 accident).
- **Gone from Aug 7 passed set:** 29 VINs no longer listed anywhere — 24 CarMax nationwide churn, 3 CarGurus local (Olympia Mazda '23 Premium Plus $28,988; Mazda of Salem '21 Signature $28,199; CarMax Boise cross-list), 1 Cars.com (Ron Tonkin Acura '22 Carbon $28,245), 1 CarSoup MN. Plus shortlist #2 (Acura) and #11 (CarMax Sacramento) confirmed sold via VDP.
- **Price movement on 107 VINs seen both days:** median **$0** · **26 dropped** (avg −$483) · **7 rose** (avg +$467) · 74 unchanged.
- **Shortlist net:** 2 sold, 1 raised +$540, 1 dropped −$100, 3 with $200 KBB-leading cuts, 1 with −$210 CG cross-list, 3 flat.
- **Market read:** local dealer inventory is basically static over 4 days — same cars, small drift downward. The turbo-slot loss (#2) is best backfilled from Carvana/CarMax; nothing local replaced it. #7's price hike + FPP flip makes it the weakest surviving pick.

**Gone (informational, non-CarMax-churn):**
- JM3KFBAY6N0592364 — 2022 2.5 Turbo $27,300 @ Acura of Seattle (shortlist #2, sold)
- JM3KFBCM0N1599511 — 2022 Carbon $24,998 @ CarMax Sacramento (shortlist #11, sold)
- JM3KFBEM6P0273606 — 2023 2.5 S Premium Plus $28,988 @ Olympia Mazda (was in R2 top-30)
- JM3KFBEY8M0387654 — 2021 Signature $28,199 @ Mazda of Salem
- JM3KFBCM3N0649064 — 2022 2.5 S Carbon $28,245 @ Ron Tonkin Acura
- (+ 24 CarMax nationwide units cycled out)

_Files: `listings_0811.json` (raw per-source), `resweep.json` (structured diff), `shortlist_recheck_0811.json` (VDP rechecks), `cg_vdp_0811.json`, `carmax_items_0811.json`, `at_parsed_0811.json`._
