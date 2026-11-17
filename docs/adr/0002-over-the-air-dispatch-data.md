# ADR 0002 — Over-the-air dispatch data: survey before building

Status: CLOSED 2026-11-17. No receivable dispatch data was found. The system
advertises packet data on three continuously keyed, P25-width channels, but
OP25 could not frame them and their format is unidentified (Evidence, second
run). The live source is
dispatch voice (`mcfrs-dispatch-transcribe` ADR 0001). Frank's read: unit
laptops get CAD over cellular (FirstNet).

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

- **2026-11-17, second run, J-pole back on: control channel locked.**
  20,522 TSBKs in 14 m 46 s (13:36–13:51), NAC `0x8e2`, zero unhandled
  opcodes, no `0x38` service broadcast, no `0x14` data-channel grants.
  - `0x16 sndcp_data_ch` was the most frequent TSBK (5,558). Channel IDs
    decode with the broadcast band plan (`0x3d` iden 0: base 851.00625 MHz,
    6.25 kHz steps). Three were announced every cycle (~1,150 each) and
    never appeared in any of the 1,127 voice grants: `0x125` 852.8375,
    `0x185` 853.4375, `0x1a1` 853.6125 MHz. Others appeared intermittently,
    some of them this site's secondary control channels (853.8875,
    853.9375), so either data shares those channels or OP25 misparses some
    `0x16` messages.
  - RadioReference (`../SYSTEM.md` source) lists all three as site
    frequencies with no flag. It marks nothing as data.
- **Data channels are keyed continuously.** `rtl_power`, 1 s bins for 60 s:
  852.8375 active 60/60 s at about +21.5 dB over the floor; 853.4375 and
  853.6125 active 60/60 s at about +17 dB. Voice channels were bursty
  (853.3625 16/60 s; 853.1125 0/60 s).
- **They are not P25 that OP25 can frame.** OP25 `rx.py` parked on each
  data channel (`-f`, no trunking, `-v 10`), with a temporary patch that
  logged PDU header fields (format, SAP, block count; no payload):
  - 852.8375 `cqpsk` 180 s, `fsk4` 60 s; 853.4375 and 853.6125 `cqpsk` 60 s
    each: **zero PDUs**, zero frames, 0–2 NID errors per run, steady
    `check_timeout`.
  - Positive control, same command on control channel 853.8625 `cqpsk`
    for 30 s: P25 frames decoded at once (NAC `0x8e2`, TDU/LCW). The
    fixed-frequency path works, so the failure is the signal, not the method.
  - **Bandwidth rules out Motorola HPD.** HPD, Motorola's dedicated
    vehicle-data channel, puts four QAM subchannels in 25 kHz
    ([SigIDWiki](https://sigidwiki.com/wiki/Motorola_ASTRO_25_HPD_Air_Interface)).
    `rtl_power` at 1 kHz bins, 20 s each: 852.8375 is 11 kHz wide at
    −10 dB, 853.4375 is 9 kHz, and control channel 853.8625 is the same
    shape (the same ~±5 kHz main lobe). The data carriers are P25-sized,
    not 25 kHz.
  - **What they carry is unidentified.** They are P25-width carriers that
    OP25's Phase I path cannot frame. Untested possibilities: a TDMA
    (Phase II-style) format, which needs scrambling parameters OP25's
    fixed-frequency mode does not take; or something else not public.
    Nothing published links these frequencies to a format. RadioReference
    leaves them unflagged.
  - **Stopped here** (Frank: CAD is most likely on cellular/FirstNet). Going
    further means identifying an unknown signal by trial. The odds that it
    carries CAD text in the clear are low, and if it turned out to be
    encrypted we would stop anyway.
  - The patch was reverted afterwards: OP25 source back to `5b58335`, the
    library restored from a backup and verified by sha256. Patch text and
    logs are kept on the box in `~/cc-survey/`.

## Consequences

- No over-the-air data adapter. The live source is dispatch voice
  transcribed to text (`mcfrs-dispatch-transcribe` ADR 0001).
- The paging survey (Decision, step 2) is not run. Frank's information is
  that CAD reaches the units over cellular, and paging would at best
  duplicate voice dispatch.

## Trigger to revisit

The county publishes a data interface, or a public P25 decoder gains support
for this system's data channels.
