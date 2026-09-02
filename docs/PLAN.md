# Plan — phases, each ending at a gate Frank clears

Rules of the road: `../CLAUDE.md`. Open decisions: `BRINGUP.md`.

## Phase 0 — scaffold (DONE 2026-09-02)

Research, decoder choice (`adr/0001-decoder-op25.md`), system facts
(`SYSTEM.md`), talkgroup data (`../config/`), unit files, mode switch.
Nothing on the box.

## Phase 1 — OP25 on the box            ← NEXT GATE: "APPROVED: install"

1. `ssh apogee-gs`; `sudo apt install gnuradio gr-osmosdr` (packaged,
   3.10.12 / 0.2.6 — measured available).
2. `git clone -b gr310 https://github.com/boatbod/op25 ~/op25 && cd op25
   && ./install.sh`. Note the build time (expect tens of minutes on 4 cores).
3. Confirm `rx.py --help` runs and lists `-2` (Phase II) and the trunk
   options. Record the exact OP25 commit hash in `BRINGUP.md`.

Nothing in this phase touches `aprs-igate`, which keeps the dongle.

## Phase 2 — first decode

1. `sdr-mode scanner` (stops the I-Gate, frees the dongle — I-Gate is down
   for the duration; say so before doing it).
2. Run `rx.py` by hand with `config/mcfrs-trunk.tsv`, gain from the
   I-Gate's measured setting as a starting point, web terminal on the
   port named in the unit file. Verify: control channel lock, NAC reads
   `8E2` (`SYSTEM.md`), talkgroup grants appear, a clear call produces
   audio (UDP sink for now).
3. `sdr-mode igate` to hand the dongle back. Write results, dated, into
   `BRINGUP.md`. If lock fails, the antenna decision (BRINGUP #2) comes
   first, before any software rabbit hole.

## Phase 3 — audio delivery (decision BRINGUP #1)

Implement whichever Frank picks; default recommendation is an Icecast
stream on the box (OP25 UDP audio → ffmpeg → icecast2) so any phone or
laptop on the LAN can listen and OP25's own web page shows what is
being heard. Verify: stream plays on a phone for 10 minutes without
underruns.

## Phase 4 — service + mode switch

Install `systemd/mcfrs-scanner.service`, add the reciprocal
`Conflicts=mcfrs-scanner.service` to `aprs-igate.service` (a commit in
the `aprs-igate` repo — cross-repo, called out at the gate), install
`bin/sdr-mode`. Verify: switching both ways five times leaves exactly one
`rtl_*`/`rx.py` process; a reboot comes up in the mode last selected.

## Phase 5 — tune what we hear

Whitelist pruning (start with dispatch + ops + incidents; add stations by
taste), talkgroup priority, encrypted-call muting confirmed (a 7D call
must produce silence, logged not heard).

## Later, only with a trigger

- Second dongle + 800 MHz antenna → no mode switching, all three jobs
  concurrent. Trigger: Frank misses APRS packets while scanning, or
  wants both during a launch weekend.
- Call recording / browsing (trunk-recorder + rdio-scanner). Trigger:
  "what did I miss last night" comes up more than twice.
- Rocket-box integration (an LED or OLED line for "scanner mode").
  Trigger: someone starts the scanner and forgets the I-Gate is down.
