# ADR 0002 — Over-the-air dispatch data: survey before building

Status: OPEN 2026-11-17. The first survey heard nothing (antenna, see
Evidence); it must be rerun before anything is decided.

## Context

The incident dashboard (`mcfrs-incidents`, its ADR 0001) lost its planned
source: the Everbridge request capture cannot be supplied. Unit laptops
(MDCs) receive dispatches, and the question is whether that dispatch *data*
(call type, address, units as text) travels over the county radio system in
a form this receiver can lawfully decode.

What we know without measuring:

- The system is P25 Phase II (`../SYSTEM.md`). P25 carries voice plus a
  small amount of packet data (location reports, short messages, SNDCP
  packet data). Its data rate is far below what a CAD-to-MDC feed needs.
- Agencies of this kind usually run MDC traffic over commercial LTE
  (often FirstNet) inside an encrypted VPN. If MCFRS does, there is nothing
  on the air to receive. This is the industry pattern, not a measured fact
  about MCFRS.
- Alphanumeric paging (POCSAG/FLEX) sometimes carries call type and address
  to volunteers. MCFRS may have replaced it with phone alerting (Everbridge
  is a likely candidate).

## Legal and privacy limits (not legal advice)

- 18 U.S.C. §2511(2)(g)(ii) permits receiving radio "readily accessible to
  the general public". §2510(16) excludes encrypted or scrambled traffic and,
  with exceptions, traffic carried by a common carrier.
- 47 U.S.C. §605 separately restricts *divulging* what is received. A public
  web page is divulging; receiving for a personal display is a different
  question.
- Dispatch text often contains patient detail. The county encrypts the
  hospital talkgroups for that reason (`../SYSTEM.md`). Anything derived from
  dispatch data goes through `mcfrs-incidents`' server-side privacy
  transforms before display, and nothing medical is published.
- Encrypted traffic is never decoded (`../../CLAUDE.md`, "What must never
  happen"). That rule covers data as well as voice.

## Decision

Measure before building anything. The method:

1. **Control-channel survey (P25).** Run OP25 parked on the control channel
   with every control message logged, and count what appears:
   - `tsbk(0x16) sndcp_data_ch`: data-channel announcements. Any of these
     means packet data is on the system.
   - `tsbk(0x38) sys_srv_bcst`: the services the system advertises
     (available/supported bitmasks), which includes data service bits.
   - `tsbk(0x..) unhandled`: opcodes OP25 does not parse, kept for later
     decoding.

   With a working antenna this is a 15-minute run.
2. **Paging survey (only if 1 shows no dispatch data).** A short sweep of
   the local paging allocations with the same dongle, decoding with
   `multimon-ng`, to see whether any fire paging traffic exists.

### Survey procedure (reproducible)

Keep the unit files untouched. With the dongle freed by `sdr-mode off` (the
sanctioned "neither" mode, `../../bin/sdr-mode`):

- Build a throwaway trunk file: a copy of the installed
  `/etc/mcfrs-scanner/mcfrs-trunk.tsv` whose whitelist column points at a
  file containing only talkgroup `1`. OP25 then ignores every voice grant
  and stays on the control channel instead of following calls.
- Run `rx.py` from the OP25 apps directory with the unit file's radio
  arguments (`../../systemd/mcfrs-scanner.service`) but without `-V` and
  `-w/-W/-u` (no voice decode, no audio), adding `-v 10`. At OP25 verbosity
  10, `tk_p25.py` logs every TSBK, including unhandled opcodes. Use the web
  terminal port from the unit file on `127.0.0.1`.
- Bound it with `timeout 900`, send stderr to a log, then return the dongle
  with `sdr-mode igate`.
- Summarise with `grep -o 'tsbk(0x[0-9a-f]*) [a-z_]*' | sort | uniq -c`.

Before trusting the result, confirm the control channel is actually being
received (a check that could fail). The log must show TSBKs, and the OP25
status must show NAC `0x8e2`. Zero TSBKs means the survey heard nothing,
not that the system carries no data.

## Evidence

- **2026-11-17, first run: no reception.** A small antenna was on the
  dongle instead of the roof J-pole. OP25 cycled through all four control
  channels with `control channel timeout` and never decoded a TSBK. An
  `rtl_power` sweep across 853.4–854.2 MHz (gain 40) was flat: every
  control channel was within 0.7 dB of the median noise floor. A continuous
  P25 control channel normally stands well above the floor. Inconclusive;
  rerun on the J-pole, which locked first try on 2026-09-02
  (`../BRINGUP.md`).
- Found while preparing: OP25 itself has a Phase II AMBE+2 decoder
  (`lib/ambe.c`, used by `lib/p25p2_tdma.cc`) and an encoder
  (`lib/ambe_encoder.cc`). Relevant to `mcfrs-dispatch-transcribe` ADR 0002.
- Found while preparing: the comment in `../../systemd/mcfrs-scanner.service`
  says `-V` is the "verbose trunking log". In this OP25 build `-V` is
  `--vocoder` and verbosity is `-v`. The comment needs a fix; the flags
  themselves are right.

## Consequences

- If dispatch data is on the air in the clear: a new ADR scopes a data
  decoder feeding `mcfrs-incidents`, with the privacy limits above.
- If not (the expected outcome): the live source becomes dispatch voice
  transcribed to text (`mcfrs-dispatch-transcribe` ADR 0001).

## Trigger to revisit

The roof J-pole (or an 800 MHz antenna) is back on the dongle. Rerun step 1.
