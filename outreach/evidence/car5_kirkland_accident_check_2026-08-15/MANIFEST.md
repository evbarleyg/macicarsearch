# Evidence: car #5 accident-history discrepancy

Captured live 2026-08-15 by direct navigation (not from cache/memory) for VIN JM3KFBDM3M0301052, stock O94564A, 2021 Mazda CX-5 Grand Touring, 33,335-33,336 mi, listed $25,192.

| File | Source URL | What it shows |
|---|---|---|
| `01_cargurus_history_section.png` | https://www.cargurus.com/details/451807182 (CarGurus listing 451807182) | CarGurus "History" section: "0 accidents reported — No accidents or damage reported.", "1 previous owner", "Clean title". Footnoted to AutoCheck ("Save 20% on the full AutoCheck vehicle history report"). |
| `02_kbb_vehicle_history_popover.png` | https://www.kbb.com/cars-for-sale/vehicle/782572696 | KBB "Vehicle History" popover: "No Accidents", "Single Owner", "Clean Title". Provider logo shown: Experian / AutoCheck. |
| `03_fordofkirkland_own_vdp_history_badge.png` | https://www.fordofkirkland.com/inventory/JM3KFBDM3M0301052/ | The dealer's own listing page (same VIN and stock #O94564A confirmed on-page). "History Report" section shows only a CARFAX badge ("CARFAX 1-OWNER GOOD VALUE") — the page has NO text claim of "no accidents" anywhere. The badge is a live link to a free full CARFAX report. |
| `04_carfax_report_accident_section.png` | https://www.carfax.com/vehiclehistory/ar20/... (reached by clicking the badge in file 03; long signed URL, not reproduced here — re-derive by clicking the badge on the dealer page, it is dynamically generated) | The free CARFAX report itself, "provided free of charge by Ford of Kirkland." Accident/Damage History section: "Event 1 — 07/31/2021 — Accident reported — Airbags did not deploy." Also shows "CARFAX 1-Owner Vehicle." Report pulled 2026-08-15 11:39 AM CDT per its own footer timestamp. |

## What this establishes (verified by direct observation, same session)

- CarGurus and KBB both cite **AutoCheck** and both show **zero accidents** for this VIN.
- The dealer's own site links a **CARFAX** report for the identical VIN showing **one accident, 07/31/2021, airbags did not deploy**.
- This CARFAX result matches a Carfax pull Evan reported having from 2026-08-11 (same accident date/detail) — not independently re-verified against that earlier document by this agent, but consistent with it.
- All four sources agree: 1 (previous) owner, clean/no-issue title.

## What this does NOT establish (not verified — do not assert as fact)

- Repair quality or whether/how the damage was fixed — no repair record was visible on the CARFAX pages captured.
- Severity beyond "airbags did not deploy" (no photos, no cost estimate, no panel-level detail visible on the free report).
- Whether Evan/Maci already know about this accident from a prior conversation not visible in this repo or in the Gmail threads checked.
- Current status of the Saturday 2026-08-15 ~9:30 AM visit with Ayres Horne (Hyundai of Kirkland) — no message newer than 2026-08-14 19:27 UTC ("See you tomorrow...") was found in the evbarleyg@gmail.com inbox as of this check. Whether the visit has occurred, is in progress, or was cancelled is UNKNOWN.

## Correction to prior repo records

Earlier entries in `outreach_data.json` / `README.md` referred to the Kirkland contact as **"Hamid"** (`hamid@fordofkirkland.com`), sourced from a scraped Dealer.com config value on hyundaiofkirkland.com — that source was always logged as unverified/not-rendered-as-visible-text. The actual, verified, live negotiation (Gmail thread, 2026-08-11 through 2026-08-14) is with **Ayres Horne**, `ayres.horne@drivehyundaikirkland.com` (DriveCentric CRM), reached via the Hyundai of Kirkland website contact form submitted 2026-08-11. The `hamid@` email address was never confirmed to have been read by anyone; no reply was ever received from it. Evan separately referred to this salesperson as "Jonathan Ayres" — no name "Jonathan" appears anywhere in the Gmail correspondence; the verified name on every message is "Ayres Horne." This may be a misremembering, or Evan may have separate information not visible here — flagging the discrepancy rather than asserting either name is wrong.

## Negotiation state as of last message found (verified from Gmail, not independently re-confirmed today)

- Dealer's latest written proposal: **$28,123 out the door** (includes a license-fee refund provision and confirms both key fobs).
- Evan's ask: **$27,600 out the door**.
- Saturday visit confirmed for ~9:30 AM (message thread ends 2026-08-14 19:27 UTC, "See you tomorrow and maybe we can make us the one and only stop").
- The accident-history discrepancy documented in this folder does **not** appear anywhere in the Ayres Horne email thread — it was not mentioned by either party in the messages reviewed.
