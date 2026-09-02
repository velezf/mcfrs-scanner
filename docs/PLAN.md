# Plan — phases, each ending at a gate Frank clears

Rules of the road: `../CLAUDE.md`. Open decisions: `BRINGUP.md`.

## Phase 0 — scaffold (DONE 2026-09-02)

Research, decoder choice (`adr/0001-decoder-op25.md`), system facts
(`SYSTEM.md`), talkgroup data (`../config/`), unit files, mode switch.
Nothing on the box.

## Phase 1 — OP25 on the box            (APPROVED 2026-09-02; build running via `bin/op25-build.sh`)

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

## Phase 3 — audio delivery (DECIDED: Icecast + 3.5 mm via USB adapter)

Design and parts: `AUDIO.md`. Pieces written: `bin/mcfrs-audio`,
`systemd/mcfrs-audio.service`, `config/audio.env.example`. Verify: stream
plays on a phone for 10 minutes without underruns; once the USB adapter
arrives, the AUX path plays the same audio.

## Phase 4 — service + mode switch

`bin/install-on-box.sh` installs both units, `bin/sdr-mode` and
`bin/mcfrs-audio` to `/usr/local/bin`, config to `/etc/mcfrs-scanner`,
and sets up Icecast. The reciprocal `Conflicts=mcfrs-scanner.service` in
`aprs-igate.service` is a commit in the `aprs-igate` repo (cross-repo). Verify: switching both ways five times leaves exactly one
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
