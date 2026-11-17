# ADR 0002 — Over-the-air dispatch data: survey before building

Status: CLOSED 2026-11-17, after the DATCH capture. **No CAD text was
found on the air.** The three continuously keyed channels are Motorola P25
Phase 2 TDMA data channels (DATCH). Their traffic does not change around
dispatches, and their bytes show no readable text above chance. The standard
P25 data channel carries mostly LRRP location reports. Details are in the
Correction (identification) and "DATCH capture results" (outcome) sections.
The live source is dispatch voice (`mcfrs-dispatch-transcribe` ADR 0001).
(Closed once earlier the same day on a misreading, then reopened; see
Correction.)

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

## Correction (2026-11-17, later the same day)

The second run's reading of the `0x16` messages was wrong. OP25's
single-receiver trunking code (`apps/trunking.py`, boatbod gr310 @
`5b58335`) labels every TSBK with opcode `0x16` as `sndcp_data_ch` without
checking the manufacturer ID (MFID). Two different messages share that
opcode. Evidence: a 2-minute capture with the raw TSBK added to that log line
(a temporary Python-only patch, reverted by `git checkout`; the OP25 tree
shows no changes afterwards). Log: `~/cc-survey/cc-raw.log` on the box.

| MFID (raw byte 2) | Message | Channels referenced |
|---|---|---|
| `0x90` Motorola | **Motorola TDMA data channel announcement**, the Motorola opcode 22 in SDRTrunk's table ([`Opcode.java`](https://github.com/DSheirer/sdrtrunk/blob/master/src/main/java/io/github/dsheirer/module/decode/p25/phase1/message/tsbk/Opcode.java), `MOTOROLA_OSP_TDMA_DATA_CHANNEL`; parser [`MotorolaExplicitTDMADataChannelAnnouncement.java`](https://github.com/DSheirer/sdrtrunk/blob/master/src/main/java/io/github/dsheirer/module/decode/p25/phase1/message/tsbk/motorola/osp/MotorolaExplicitTDMADataChannelAnnouncement.java)) | `0x125` 852.8375, `0x185` 853.4375, `0x1a1` 853.6125. Raw example: `1690c23f0185ffff00000000` |
| `0x00` standard | **SNDCP data channel announcement, explicit** (TIA standard opcode 22, `OSP_SNDCP_DATA_CHANNEL_ANNOUNCEMENT_EXPLICIT` in the same table) | `0x131` 852.9125, `0x1cd` 853.8875, `0x1d5` 853.9375. Raw example: `160000c00131ffff00010000` |

Further evidence:

- **The band plan says these are 12.5 kHz channels.** The data channels'
  channel IDs use identifier 0, an FDMA `iden_up` (`0x3d`) entry: base
  851.00625 MHz, 6.25 kHz steps, `bw 0x64` (100 × 125 Hz = 12.5 kHz).
- **SDRTrunk identifies the Motorola channels.** Issue
  [#2089](https://github.com/DSheirer/sdrtrunk/issues/2089) and PR
  [#2090](https://github.com/DSheirer/sdrtrunk/pull/2090) (merged
  2024-11-12, "Motorola P25P2 TDMA data channel support") add the
  announcement above, the Phase 2 MAC equivalent
  ([`MotorolaTDMADataChannel.java`](https://github.com/DSheirer/sdrtrunk/blob/master/src/main/java/io/github/dsheirer/module/decode/p25/phase2/message/mac/structure/motorola/MotorolaTDMADataChannel.java),
  MAC opcode 139), and a DATCH timeslot type that follows the channel
  ([`DatchTimeslot.java`](https://github.com/DSheirer/sdrtrunk/blob/master/src/main/java/io/github/dsheirer/module/decode/p25/phase2/timeslot/DatchTimeslot.java)).
  SDRTrunk prints the payload only as hex.
- **The SDRTrunk author's analysis** (comment in `DatchTimeslot.java`;
  quoted, not verified by us):
  - the channel is "probably used with APX-NEXT and MDT equipment";
  - it "seems to use the standard P25 Phase 2 scrambling sequence";
  - "the overall signalling doesn't appear to be encrypted because the data
    does not appear randomized. There's a lot of repeated messaging with just
    a few bits changing";
  - the payload is not Reed-Solomon coded in an obvious way, and its structure
    is unknown.
- **This explains our measurements.** The carriers are P25-width (~10 kHz at
  −10 dB), continuously keyed, and TDMA, so OP25's Phase I fixed-frequency
  path (`-f`, no `-2`) could not frame them. It also rules out Motorola HPD
  (25 kHz, four QAM subchannels:
  [SigIDWiki](https://sigidwiki.com/wiki/Motorola_ASTRO_25_HPD_Air_Interface)).
- **The standard SNDCP channel is ordinary P25 Phase I.** Stock OP25 on
  852.9125 (`cqpsk`, 60 s) framed hundreds of frames with NAC `0x8e2`:
  terminators with link control (RFSS status; a Motorola group regroup). No
  data PDUs in that minute. 853.8875 and 853.9375 are this site's secondary
  control channels.

### Documentation search: does the MDC use these channels? (2026-11-17)

Frank's hypothesis: PremierOne Mobile on the MDC listens to the LMR data
channels as a fallback when FirstNet is unavailable.

- **The MDC software is PremierOne Mobile.** Frank confirmed it on
  2026-11-17. A 2017 MCFRS general order announced PremierOne CAD, with
  PremierOne Mobile on the MDCs and in-station remote CADs. The PSCC operates
  CAD and the MDCs ([PSCC page](https://www.montgomerycountymd.gov/frs-ql/pscc/),
  from web search; returned 404 when checked on 2026-11-17).
- **Supporting it:** Motorola's
  [ASTRO 25 Mission Critical Data brochure](https://aem-cloud-prod-cdn.motorolasolutions.com/content/dam/msi/docs/astro-25/astro-25-mission-critical-data-brochure.pdf)
  (undated):
  - "Vehicles are equipped with computers … This information exchange is
    often happening over commercial carrier networks … In times of
    disaster … they can get overloaded or even fail." It pitches ASTRO 25
    data as the resilient alternative.
  - It offers to "Dedicate channels to data-only to preserve data capacity"
    (ASTRO 25 Enhanced Data), which matches our three continuously keyed
    channels.
- **Against it, or undocumented:**
  - The same brochure sizes LMR data for "short data messages such as
    location, text, presence, identity and status", with "large file
    transfers … best served by broadband". The headline use of Enhanced
    Data is "Support more GPS users at a higher cadence".
  - No public document found says PremierOne Mobile uses LMR data, as a
    fallback or otherwise. Its
    [data sheet](https://aem-cloud-prod-cdn.motorolasolutions.com/content/dam/msi/docs/products/smart-public-safety-solutions/integrated-command-control/premierone-mobile/PremierOne-Mobile-Data-Sheet.pdf)
    mentions only "connected or disconnected mode", and only for its records
    reporting client. An
    [ASTRO 25 data solutions brief](https://www.airwavecommunication.com/downloads/motorola/solutions_brief/astro_25_data_solutions.pdf)
    says PremierOne Mobile can start database queries alongside
    data-enabled radios. That is queries, not CAD dispatch.
  - Station alerting is not on these channels. The brochure lists MACH Alert
    station alerting ("alert firefighters in the station to incident
    details") as an ASTRO 25 data application, but MCFRS uses PURVIS, an
    IP-based system installed from 2016
    ([MCFRS blog, 2016-06-24](https://mcfrs.blogspot.com/2016/06/installation-begins-on-new-fire-station.html);
    [county CRC agenda, 2023-10-12](https://montgomerycountymd.gov/PRO/Resources/Files/CRC/crcAgenda-10-12-23_0942.pdf),
    from web search; returned 404 when checked on 2026-11-17).
    A RadioReference forum post reports the radio-based MOSCAD alerting
    decommissioned.
- **Assessment:** the MDC-fallback reading is plausible but undocumented.
  Going by Motorola's own materials, location, text messaging and
  radio-management traffic (OTAR, programming over P25) are at least as
  likely occupants. The DATCH capture decides it.

What is established, and what is not:

- **Established:** the system runs three Motorola TDMA data channels
  continuously, and MCFRS is on this system.
- **Not established:**
  - that MCFRS MDTs use them (the "MDT" reading is the SDRTrunk author's
    "probably");
  - that CAD dispatch text travels on them, rather than location, status
    or radio-management traffic;
  - that the payload is unencrypted. "Doesn't appear randomized" is an
    observation about the signalling; it is not an encryption analysis of
    any user data.

## DATCH capture results (2026-11-17)

Method: `../DATCH-CAPTURE.md` (deviations are in its run log). Two 5-minute
I/Q takes were recorded on the box at 19:36–19:46 UTC (14:36–14:46 local) on
the roof J-pole. Take 1 was decoded in SDRTrunk v1.0.0 on the Mac and
analysed. Take 2 was not, because a stop rule was reached on take 1.

- **Recording validity (a check that could fail).** Level over the noise
  floor in take 1: DATCH channels +26 to +32 dB, control channel 853.8625
  +32.6 dB, empty reference frequency 853.000 +0.5 dB. SDRTrunk decoded the
  control channel from the file and followed voice, SNDCP and DATCH
  channels on its own.
- **(a) Traffic.** 24,815 DATCH timeslot messages in 297 s, spread evenly
  over the three channels and both timeslots (~14 messages/s per timeslot).
- **(b) Encrypted? Inconclusive, so no stop at (b).**
  - Unique messages: 7.77 bits/byte (a same-size uniform random sample:
    8.00; readable English text: about 4.5).
  - 36% of messages are exact repeats; the five most common repeat 260–292
    times each.
  - Median bit difference between consecutive messages: 45–46%. No byte
    position has entropy below 4 bits.
  - Too structured to be uniform ciphertext and too random to be text:
    consistent with compact binary data plus periodic repeated messages.
- **(c) Tracks dispatch? No. Stop rule (c).** The control channel showed
  grants to the dispatch talkgroup (7A2, TG 4005) in 39 distinct seconds.
  New unique DATCH messages per second: 53.5 baseline, 50.3 in the 30 s
  after a dispatch grant. A CAD feed to MDCs should burst when dispatches go
  out.
- **(d) Readable text? At chance.** 4.6% of messages contain a printable
  ASCII run of 6+ characters, against 5.2% for the random sample. Street
  suffix hits: 5 observed against about 4 random. (The analysis script's
  first baseline note, "<1%", was wrong; the correct random rate is about
  5–6%. These numbers use the empirical random comparison.)
- **(e) Standard P25 packet data on 853.9375.** The control channel issued
  `SNDCP_DCH_GRANT … CHAN:0-469` (853.9375) to individual radio IDs.
  SDRTrunk decoded 34 IP packets there: 21 LRRP (Motorola location), 10
  other UDP, 3 incomplete. Every packet whose header decoded carried
  `SAP:UNENCRYPTED_USER_DATA`. This matches Motorola's description of LMR
  data (location, status).

**Conclusion.** Neither data path showed CAD text. DATCH traffic is
steady machine-to-machine data that does not respond to dispatches. The
standard data channel is mostly location reports. This supports Frank's
read that CAD reaches the MDCs over cellular (FirstNet).

**Limits.**
- One 5-minute take, 39 dispatch moments.
- The DATCH format is undocumented, so "no text" is about the bytes as
  SDRTrunk descrambles them. Compressed or differently framed text would
  not show up.
- The repeats suggest the descrambling is at least consistent.
- Nothing was decrypted, and no payload content is recorded here.

## Consequences

- No over-the-air data adapter. The live source is dispatch voice
  transcribed to text (`mcfrs-dispatch-transcribe` ADR 0001).
- The paging survey (Decision, step 2) stays unrun.
- Raw recordings, converted WAVs and SDRTrunk event logs were deleted on
  2026-11-17 at Frank's instruction (runbook handling rules), from the box
  and the Mac. Only the aggregates above remain.
- OP25 caveat for anyone reading these logs: in `apps/trunking.py`,
  `tsbk(0x16) sndcp_data_ch` lines mix the Motorola and standard messages.
  Check the MFID before trusting them. (A possible upstream report to
  boatbod/op25.)

## Trigger to revisit

- The county publishes a data interface.
- The DATCH payload format gets documented, or a public decoder parses it.
- A future question needs the LRRP location data. That would need its own
  ADR, under the privacy limits above.
