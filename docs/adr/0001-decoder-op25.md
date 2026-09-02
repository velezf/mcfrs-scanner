# ADR 0001 — Decoder: OP25 (boatbod, `gr310`) on a single RTL-SDR

Status: ACCEPTED 2026-09-02 (pending first decode on the box, which is the
only thing that could overturn it).

## Context

One RTL-SDR Blog V4, shared with the APRS I-Gate. The target system is
P25 Phase II with a 2.725 MHz channel span (`../SYSTEM.md`). Host is a Pi 5
on Debian 13 with `gnuradio` 3.10.12 in apt. Headless.

## Options

| | one dongle, full system? | Phase II | Pi 5 / Debian 13 | notes |
|---|---|---|---|---|
| **OP25 (boatbod)** | **yes** — retunes the dongle to follow grants | yes (`-2`) | `gr310` branch is master since 2024-12; Debian bookworm tested, trixie has GR 3.10.12 | web UI on a port, UDP/ALSA audio, tags/whitelist TSVs |
| trunk-recorder | **no** — needs the whole span inside one dongle's bandwidth; would need a 2nd dongle | yes | builds fine | records every call to files; overkill for "listen" |
| SDRTrunk | **no** — same span constraint | yes | Java GUI; headless is awkward | best on a laptop, not an appliance |

## Decision

OP25, `gr310` branch, built from source on the box via its `install.sh`
(which pulls the packaged GNU Radio). Run `rx.py` single-dongle with the
system defined in `config/mcfrs-trunk.tsv` (columns per OP25: sysname,
control-channel list, offset, NAC, modulation `CQPSK`, tags file,
whitelist, blacklist, center frequency).

## Consequences

- We miss a voice call only when two clear whitelisted talkgroups are
  active at once (single receiver). Acceptable for one-listener use.
- If Frank later wants "every call recorded and browsable", the upgrade
  path is trunk-recorder + a second dongle — revisit then, not now.
- Rate-limiting hazard: `install.sh` runs `apt` and `sudo make install` on
  a box with live services. That is the phase-1 gate in `../PLAN.md`.

## Trigger to revisit

First decode fails to lock the control channel after antenna and gain are
ruled out (`../BRINGUP.md` verification bar, items 2–3).
