# Bring-up — open decisions, then the runbook grows here

## Decisions (2026-09-02, Frank)

1. **Audio: Icecast stream + a 3.5 mm AUX output.** Pipeline and the
   USB-audio-adapter recommendation: `AUDIO.md`.
2. **Antenna:** measure the J-pole at 853 MHz in phase 2 before buying.
3. **I-Gate is the default job after reboot.** The scanner is never
   enabled at boot; `sdr-mode scanner` is the deliberate switch.
4. **Repo name `mcfrs-scanner`**; no remote yet.
5. **OP25 install approved** ("commit and move forward on the OP25").

## The original decision list (kept for the reasoning)

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

## Found during install (2026-09-02)

- Icecast's default port collides with direwolf's AGW port, and OP25's usual
  web port with the rocket dashboard. Both moved; the port map is in
  `../CLAUDE.md`, box facts. Icecast had silently failed to start (the LSB
  wrapper reports nothing); `install-on-box.sh` now restarts it and the bar
  below checks the listener.

## Verification bar (write results here, dated)

- [x] OP25 builds on Debian 13 / GR 3.10.12 — 2026-09-02, boatbod gr310 @ `5b58335`
      (2026-08-23), `bin/op25-build.sh`, 12 min wall (apt → `make install`),
      `from gnuradio import op25, op25_repeater` OK, `rx.py --help` shows `-2 -n -T -l`.
      `blacklist-rtl.conf` installed but the `dvb_usb_rtl28xxu` module stays loaded
      until the next reboot (rtl_fm/osmosdr detach it themselves, so not blocking).
- [x] Control channel lock — 2026-09-02 15:10, first try, on the J-pole: OP25 status
      `NAC 0x8e2 WACN 0xbee00 SYSID 0x8e0 853.862500`, 1888 TSBKs in ~2 min,
      the other three CCs listed as secondaries, voice grants tracked on seven
      voice frequencies. Gain `LNA:49`, ppm 0. (Antenna decision 2 closed: it works.)
- [ ] First clear voice call heard (talkgroup id + time)
- [ ] Encrypted talkgroup produces silence, not garbage
- [ ] Gain setting recorded (start from the I-Gate's measured value in
      `../aprs-igate/systemd/aprs-igate.service`)
- [x] Audio pipeline up — 2026-09-02: `audio.py` listening, ffmpeg feeding, Icecast
      mount `/mcfrs.mp3` live (`status-json.xsl`), OP25 web page answers on its port.
- [ ] Stream plays on a phone on the LAN for 10 min (Frank: `http://apogee-gs:8100/mcfrs.mp3`)
- [ ] `sdr-mode` round-trip ×5 leaves exactly one dongle owner
- [ ] Survives reboot in the chosen default mode
- [ ] I-Gate still verified on aprs.fi after switching back

## Legal note (so it is written down once)

Receiving public-safety radio at home is lawful in Maryland; retransmitting
it or using it in furtherance of a crime is not, and decrypting encrypted
traffic is never attempted (`../CLAUDE.md`). Nothing here streams outside
the LAN.
