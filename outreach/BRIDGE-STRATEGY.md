# Bridge — strategy session to watch session

**Written only by the STRATEGY session** (Evan's work account, no Gmail).
The watch session reads this every hourly cycle and acts on it. See `HANDOFF.md` section 0.

Newest entry at the top. Times are PT. If you have no push access, ignore this file and
tell Evan directly instead — he relays, and that path is reliable.

Useful things to write here:
- a changed target or walk-away on a specific car, with the reasoning in one line
- a car to drop or reopen
- an email you want staged, with the recipient and the ask (the watch session writes it in
  Evan's voice and stages it; do not write the email yourself)
- anything learned in person that the repo does not know: what the sticker actually said,
  what the salesperson conceded verbally, condition notes from the drive

---

## Sat Aug 15, 9:25 AM — READ THE KIRKLAND CARFAX: it is NOT clean. Correct the board.

Evan dropped `FOK CX5.pdf` into my chat (Carfax run 8/11/26 by Hyundai of Kirkland itself,
VIN JM3KFBDM3M0301052). First actual reading by either session. Findings:

- **ACCIDENT REPORTED 07/31/2021**, roughly 4,000 miles, seven months into ownership. Airbags
  did not deploy. No structural damage or total loss reported. No severity, impact point or
  repair record anywhere in the report. Source line is a generic "Damage Report".
- Otherwise strong: 1 owner, personal use, Bellevue WA throughout, lien reported, sold new
  01/01/2021 by Doug's Lynnwood Mazda and serviced there every ~6 months (12 records, last
  05/07/2026 at 32,321 mi, oil changes on schedule, air filter at 19,219). No title brands
  (guaranteed section), no open recalls, odometer consistent: 33,175 on 06/09/2026, 33,335 on
  07/03/2026.
- In-service date 01/01/2021. Basic warranty expired Jan 2024 (Carfax: "Warranty Expired");
  5-yr powertrain expired 01/01/2026 by time. The car has NO factory coverage of any kind.
  That is now a document fact, not an estimate.
- Dealer timeline: WA "vehicle purchase reported" 06/07/2026; Ford of Kirkland "vehicle
  offered for sale" 06/09/2026; serviced 07/03/2026 (hub caps); duplicate title / correction
  to record 07/20/2026. So Kirkland has held it ~67 days as of today, and Ayres's Thursday
  "we have just got this vehicle in" is contradicted by the store's own report.
- The report carries an "Original Window Sticker" link in Detailed History. That is the
  fastest GT Premium verification; Evan is checking it on his phone.

**Corrections for you to make (your files, not mine):**
1. `board.json` car #5: `history.accidents` 0 -> 1, with a note "accident reported 7/31/2021
   at ~4k mi, no airbag deployment, no structural damage reported, severity unknown";
   `verifiedVia` -> "Carfax read 8/15 (dealer-run 8/11)". Add in-service 01/01/2021 and the
   expired-powertrain fact wherever warranty is described. The public cost table / ask page
   language implying every board car has powertrain coverage left is wrong for #5 by time.
   Accident count is a neutral history fact, so the public board should show it; how it
   affects our number is not, and stays off.
2. `README.md`: correct the 2026-08-11 22:0xZ "independently confirms clean history" entry
   and today's 10:55 entry. Robert's cover note was pointing AT the accident, not away from it.
3. `RANKING.md` section 3: #5 is no longer a clean baseline. With an accident line and zero
   warranty, my read is #9 (certified 2023) becomes the value leader unless Kirkland lands at
   or under about $26,500 OTD.

**Negotiating change, decided with Evan live (record it; nothing to stage yet):** anchor at
Kirkland moves to $25,500 OTD ($22,383 selling); $26,500 ($23,285) is treated as today's
ceiling rather than the opener; any Kirkland deal is written subject to an independent
inspection. Evan asks Ayres before numbers whether there is anything on the Carfax, and is
checking whether their CarGurus/site ad claims no accidents. Final say on whether an early
no-airbag accident is acceptable at all rests with Evan and Maci under their no-accident
rule; that call has not been made yet.

**No email asks change yet.** Do not stage anything to Robert. If Kirkland fails, the order
of fallbacks is Puyallup #9, then a fresh look at Titus and Rodland; I will write here if an
ask changes.

## Sat Aug 15, 9:05 AM — strategy side online

- Read HANDOFF (incl. section 0), RANKING, and the log back through Thursday. Working the
  Kirkland visit with Evan in chat from here. No change to any target, disposition or ask.
- Confirmed the split from this side: the Gmail connector on this account is the work
  inbox. Zero dealer threads, no "CX-5 dealers" label, one unrelated draft. I will not
  sweep, read threads or stage drafts, and I will not touch board.json, the site, README
  or RANKING. This file is the only thing I write.
- Push access: this entry landing proves it. If it had not, Evan relays.
- I pull the tracking branch and main hourly and read BRIDGE-WATCH.md plus the README
  tail. If a number lands while Evan is on a lot, I work the implications in chat and put
  any changed ask here for you to stage.
- Housekeeping, one item: your PT labels are running about an hour fast. "10:30 AM channel
  opened" was committed 16:02Z = 9:02 AM PDT, and the "17:0xZ (10:0x AM PT)" re-rank entry
  was committed 16:00Z. Worth correcting, since section 0 tells me to judge staleness off
  the last README timestamp.

