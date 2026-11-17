# DATCH capture — runbook

Status: RAN 2026-11-17 (stream COMPLETED: no CAD text found). Results:
`adr/0002-over-the-air-dispatch-data.md`, "DATCH capture results". Why we
did it: same ADR, Correction. Deviations and lessons: "Run log" at the end
of this file.

**Goal.** Find out whether the three Motorola TDMA data channels (DATCH)
carry CAD dispatch text in the clear. This is not a control-channel
capture: the control channel is fully decoded already and carries only
signalling. It is in the recording only as a shared clock, because its voice
grants mark when dispatches happen.

**Targets.**
- The data channels, listed with their channel IDs in ADR 0002's
  Correction table (852.8375, 853.4375, 853.6125 MHz).
- The control channels (`SYSTEM.md`), for dispatch timing.

## Gates (Frank clears each)

1. **Recording:** the I-Gate is down for about 15 minutes (`sdr-mode off`).
2. **SDRTrunk on the Mac:** installs a desktop app (SDRTrunk release zips
   bundle their own Java runtime).
3. **Each analysis stop rule below** ends the work. No step resumes after a
   stop without a new decision.

## Handling rules

- Raw I/Q, converted WAVs and DATCH hex dumps stay in
  `~/cc-survey/datch/` on the box and `~/Documents/datch-capture/` on the
  Mac, outside every repo. They are never committed.
- They are **deleted once the analysis is written up**. ADR 0002 gets
  aggregate findings only (counts, entropy, timing correlation), never
  payload excerpts that contain text.
- No decryption, ever (`../CLAUDE.md`, "What must never happen"). Phase 2
  *scrambling* is not encryption; SDRTrunk descrambles it with the system
  identifiers in `SYSTEM.md`.
- Personal analysis only. Nothing derived from it is published
  (ADR 0002, legal and privacy limits).

## 1. Record on the box (`rtl_sdr`, no decoding)

Choose the recording parameters from these constraints:

| Parameter | Value | Why |
|---|---|---|
| Sample rate | 1.8 Msps | Covers 852.8375–853.9375 MHz with margin, and keeps each 5-minute WAV under the 4 GB RIFF limit (1.8 M frames/s × 4 bytes × 300 s ≈ 2.2 GB) |
| Center | 853.500 MHz | Not a site frequency, 62.5 kHz from the nearest (853.4375), so the dongle's DC spike lands in an empty gap. Usable span ≈ ±0.75 MHz = 852.75–854.25 |
| Gain | 40 dB (`-g 40`), the setting of the 2026-11-17 sweeps | Confirm there is no clipping before the real take (step 1b) |
| Length | 2 × 5 min, at a busy hour | More dispatch grants to correlate against |

1. `sdr-mode off` and confirm nothing holds the dongle.
2. Test take (20 s), then check clipping. The fraction of 8-bit samples at
   0 or 255 must be below 0.1 %; otherwise drop the gain one step and
   repeat. Delete the test take.
3. Two 5-minute takes:
   `rtl_sdr -f 853500000 -s 1800000 -g 40 -n 540000000 ~/cc-survey/datch/take1.u8`
   (540,000,000 samples = 300 s; same for `take2`). Write the wall-clock
   start time of each take next to it.
4. `sdr-mode igate`. The dongle work on the box is done.

## 2. Convert for SDRTrunk

The SDRTrunk releases (v0.6.1, v1.0.0) play back only **2-channel 16-bit
PCM WAV** (`ComplexWaveSource`). The rtl_tcp network tuner and `.iq`
playback exist only on SDRTrunk's development branch, so this plan does not
use them.

- Convert unsigned 8-bit interleaved I/Q to signed 16-bit:
  `s16 = (u8 − 127.5) × 256`, written as a 2-channel WAV at a 1,800,000 Hz
  sample rate. A ~20-line Python script with only the standard library
  (`wave`, `array`); do it on the box, then `scp` the WAVs to the Mac.
- Check: the WAV duration is 300 s, and the header says 2 channels, 16 bits,
  1,800,000 Hz.

## 3. Decode with SDRTrunk on the Mac

1. Install a release that has DATCH support: v0.6.1 (2024-12-03) or later.
   PR #2090 merged 2024-11-12; `DatchTimeslot.java` is present in the
   v0.6.1 and v1.0.0 tags.
2. Add a **Recording tuner** pointed at the WAV, with center frequency
   853.500 MHz.
3. Add a P25 Phase 1 control channel on the current control channel
   (`SYSTEM.md`). Enable decoded-message event logging for the channel.
   (Exact UI labels to be confirmed in the installed version.)
4. **Validity check (could fail):** SDRTrunk must decode the control channel
   from the file. Look for TSBKs, NAC `8E2`, and grants matching what OP25
   saw on 2026-11-17. If it does not decode, the recording is bad. Fix it
   before going on; do not read anything into DATCH silence.
5. DATCH: SDRTrunk's traffic-channel manager follows the Motorola DATCH
   announcement (PR #2090). If it does not start the data channels on its
   own, add P25 Phase 2 channels on the three DATCH frequencies by hand,
   with WACN, system ID and NAC from `SYSTEM.md`.
6. Export the event logs. DATCH timeslots appear as
   `DATCH-SC TDMA DATA TIMESLOT MSG:<hex>`.

## 4. Analyse, in order, and stop at the first stop rule

| # | Question | Method | Outcome |
|---|---|---|---|
| a | Is anything there? | Count DATCH timeslots per channel and per timeslot | None on any channel → **stop**: record "no DATCH traffic decodable", with the validity check result |
| b | Encrypted? | Byte entropy per message; repetition (SDRTrunk's author reports a lot of near-identical repeats); look for an algorithm or key-ID-like field | Uniformly random-looking payloads → **stop: treat as encrypted** |
| c | Does it track dispatch? | Line DATCH bursts up against control-channel grants to the dispatch talkgroup (7A2, tag in `../config/mcfrs.tsv`) in the same file timeline | No change around dispatches → likely location/status/management traffic → **stop**, record it |
| d | Readable text? | Printable-ASCII runs of 6+ characters; street-suffix and call-type words; unit designators | Text present in the clear → write a **new ADR** scoping a decoder (personal display only). Absent → **stop**, record "structured binary, no clear text" |

Then write up the aggregate results in ADR 0002, delete the raw data
(Handling rules), and record the stream's end state (COMPLETED or
ABANDONED) in `PLAN.md`.

## Risks and unknowns

- Whether SDRTrunk's DATCH support follows these specific channels from a
  recording is untested. Step 3.5 is the fallback.
- The DATCH payload format is undocumented. SDRTrunk prints hex only, so
  step 4 is pattern analysis, not decoding.
- The roof J-pole is not resonant at 853 MHz. The data channels measured
  +17 to +22 dB over the floor on 2026-11-17, which should be enough, but
  the step 3.4 check is what proves the recording is good.

## Run log (2026-11-17)

Deviations from the plan above, and what to do next time:

- **Gain: automatic, not 40 dB.** At `-g 40` the test take used about 1 bit
  of the 8-bit range (sample standard deviation 1.3). At the maximum manual
  gain of 49.6 dB it was 3.3. Tuner AGC (`-g 0`) gave 8.9, with peaks at
  78/174 and no clipping. Both takes used `-g 0`.
- **SDRTrunk v1.0.0, not v0.6.1.** v1.0.0 publishes SHA-256 checksums
  (verified against `SHA256SUMS` and the GitHub API digest); v0.6.1 does
  not. Both have DATCH support. The release zip is a launcher script plus a
  bundled Java runtime (`bin/sdr-trunk`), not a `.app`.
- **The Add Recording Tuner frequency field is in Hz.** Type `853500000`. A
  mistyped value fell back to 853.000 MHz. Editing the tuner's frequency
  digits afterwards did not apply (the log said "Can't set frequency"), so
  remove and re-add the tuner instead. Confirm with the `CF:` line in
  `~/SDRTrunk/logs/sdrtrunk_app.log`.
- **JMBE (voice codec) is not needed.** Answer No to its setup prompt.
- **DATCH followed automatically.** With Max Traffic Channels 10 and Ignore
  Data Calls off, SDRTrunk opened the three DATCH channels and the SNDCP
  channel without manual setup (step 3.5 was not needed).
- **The recording tuner loops.** Stop the channel after one pass, or cut the
  analysis at 300 s from the first message (done).
- **Remote over UniFi Teleport, the copy is slow.** Copying the takes to the
  Mac ran at about 2.6 MB/s. When remote, process on the box where possible
  (papercuts 2026-11-17).
- **Analysis.** Done with throwaway scripts, which printed aggregates only.
  Conversion: `s16 = round((u8 − 127.5) × 256)`, tested on a known 6-byte
  input. Spectrum: 4096-point FFT averaged over 3,000 blocks. Statistics:
  per-channel and per-timeslot byte entropy, duplicate rate, consecutive
  Hamming distance, per-position entropy, new-unique-messages per second
  around grants to the dispatch talkgroup, and printable runs against a
  same-size `os.urandom` sample.
