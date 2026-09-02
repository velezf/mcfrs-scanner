# mcfrs-scanner — Montgomery County (MD) Fire/Rescue on the project box

Third job for the radio rocket project box (`apogee-gs`, the Pi 5 with the
RFM95 LoRa breakout and the RTL-SDR Blog V4): when it is neither receiving
rocket telemetry nor gating APRS, it listens to **Montgomery County
Fire/Rescue Service (MCFRS)** on the county's P25 Phase II trunked system.

Sibling repos, same box, same conventions:
[`lora-rocket-telemetry`](../lora-rocket-telemetry) (the rocket ground
station; owns the LoRa radio, the LEDs, the OLED) and
[`aprs-igate`](../aprs-igate) (the APRS I-Gate; owns the RTL-SDR while it runs).

## Mission

1. **Hear MCFRS dispatch and fireground ops** — clear (unencrypted)
   talkgroups only; the decoder mutes encrypted calls and this project never
   attempts to defeat encryption.
2. **Deliver the audio somewhere useful.** The box is headless in a
   basement with HDMI-only audio, so "useful" means a LAN stream or a web
   page, not a speaker on the box (decision pending — `docs/BRINGUP.md`).
3. **Coexist with the other two jobs** without anyone editing configs by
   hand at 2 a.m. The rocket radio is separate hardware and never contends.
   The I-Gate and the scanner share ONE dongle, so they are mutually
   exclusive by construction (`systemd/`, `bin/sdr-mode`).

## The radio system (the one-paragraph version)

Montgomery County, MD runs a Motorola P25 **Phase II** 800 MHz simulcast
system. All identifiers, control channels, and the talkgroup table are
stated once in `docs/SYSTEM.md` and cited from there; the machine-readable
copies the decoder actually loads are `config/mcfrs.tsv` (talkgroup tags)
and `config/mcfrs-trunk.tsv.example` (system definition).

## The decoder

**OP25 (boatbod fork, `gr310` branch)** — see ADR
[`docs/adr/0001-decoder-op25.md`](docs/adr/0001-decoder-op25.md) for why it
beat trunk-recorder and SDRTrunk. The short reason: the system's channel
span is wider than one RTL-SDR can see at once, and OP25 is the one that
follows voice grants by retuning a single dongle.

## Status

**2026-09-02 — LIVE on `apogee-gs`.** OP25 built, control channel locked on
the roof J-pole, dispatch and ops calls heard, Icecast stream holding.
Listen at the mount named in `docs/AUDIO.md`; add the USB audio adapter
described there for the 3.5 mm AUX path. I-Gate stays the boot default. Live status and the
verification bar: `docs/BRINGUP.md`; phases: `docs/PLAN.md`.

## Switching jobs on the box

```
sdr-mode            # who owns the dongle right now
sdr-mode scanner    # stop the I-Gate, start the scanner (+ audio)
sdr-mode igate      # back to the default job
```
`bin/sdr-mode`, installed to `/usr/local/bin` by `bin/install-on-box.sh`.
