# Bring-up — open decisions, then the runbook grows here

## Decisions needed from Frank (2026-09-02)

1. **Where does the audio go?** Box is headless, basement, HDMI audio
   only. Options, recommended first:
   - **Icecast stream on the box** — play in any browser/VLC on the LAN,
     OP25's web page alongside. Adds `icecast2` + `ffmpeg` (both in apt).
   - USB audio dongle + powered speaker on the box — only if the box is
     somewhere you sit.
   - OP25 UDP audio to your laptop — works, but only while the laptop
     runs the receiver script.
2. **Antenna at 853 MHz.** The roof Arrow J-pole is a 2 m / 70 cm
   antenna; at 800 MHz it is a compromise. The county simulcast site is
   strong in-county, so it may simply work — phase 2 measures it before
   we buy anything. Fallbacks: the V4 kit's telescopic whip cut short, an
   800 MHz whip on a mag mount, or (with a 2nd dongle) a dedicated
   antenna and no switching at all.
3. **Default mode after reboot** — I-Gate (current behaviour) or last
   selected? Plan assumes I-Gate stays the default; the scanner is the
   thing you switch to on purpose.
4. **Repo name / origin.** Scaffolded as `mcfrs-scanner`; no remote yet.

## Verification bar (write results here, dated)

- [ ] OP25 builds on Debian 13 / GR 3.10.12 — record commit hash + build time
- [ ] Control channel lock on one of the four CCs (`SYSTEM.md`); NAC `8E2`
- [ ] First clear voice call heard (talkgroup id + time)
- [ ] Encrypted talkgroup produces silence, not garbage
- [ ] Gain setting recorded (start from the I-Gate's measured value in
      `../aprs-igate/systemd/aprs-igate.service`)
- [ ] Audio delivery works from a phone on the LAN for 10 min
- [ ] `sdr-mode` round-trip ×5 leaves exactly one dongle owner
- [ ] Survives reboot in the chosen default mode
- [ ] I-Gate still verified on aprs.fi after switching back

## Legal note (so it is written down once)

Receiving public-safety radio at home is lawful in Maryland; retransmitting
it or using it in furtherance of a crime is not, and decrypting encrypted
traffic is never attempted (`../CLAUDE.md`). Nothing here streams outside
the LAN.
