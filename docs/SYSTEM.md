# The radio system — authority for every identifier in this repo

Source: RadioReference system 11160
(<https://www.radioreference.com/db/sid/11160>), captured 2026-09-02.
Re-check against the source when something stops decoding; talkgroups get
added and re-labelled by the county from time to time.

## System

| Field | Value |
|---|---|
| Name | Montgomery County, MD |
| Type | Project 25 Phase II (TDMA voice; control channel Phase I FDMA) |
| Band | 800 MHz — voice 851.2125 … 853.6375 MHz |
| System ID | `8E0` |
| NAC | `8E2` |
| WACN | `BEE00` |
| Sites | one simulcast site, RFSS 1 site 002, 20 frequencies |
| Control channels | `853.6875`, `853.8625`, `853.8875`, `853.9375` MHz |

**Span consequence:** lowest voice channel to highest control channel is
2.725 MHz, wider than an RTL-SDR's usable ~2.4 MHz. A single dongle
therefore cannot hold the control channel and every voice channel at once.
That fact selects the decoder — `adr/0001-decoder-op25.md`.

## Talkgroups

The machine-readable copy the decoder loads is `../config/mcfrs.tsv`
(every MCFRS talkgroup, encrypted ones tagged `[ENC]`) and the starting
whitelist is `../config/mcfrs-whitelist.tsv`. Do not maintain a third copy
here; this section only explains the county's naming.

- **7A/7B/7C series (4000–4175)** — the working channels. `7A2 Disp`
  (4005) is county-wide fire/EMS dispatch. `Ops`, `Inc NN` (incident) and
  `Annc NN` (announcement) talkgroups are assigned to incidents by
  battalion/area. These are the clear channels worth hearing first.
- **7D / 7E series** — secure fireground and special ops. Encrypted.
  Muted, never decoded.
- **7G series** — training academy, code compliance, LFRD (the volunteer
  departments), CERT, ops admin. Clear but low traffic.
- **7H series** — hospital consults. `EMRC`, `CNSLT 1/2`, `All Hosp` are
  clear; the individual hospital talkgroups are encrypted (patient info).
- **Batt N Annc / Trng (4485–4535)** and **Station NN (4545–4810)** —
  per-battalion and per-station talkgroups. Clear, mostly quiet.
- **Marine / Great Falls (5250–5292)** — river ops, incl. Fairfax
  interop. `7 Marine 2` is encrypted.

Mode `T` on all of them = TDMA (Phase II) voice — OP25 needs `-2`.
