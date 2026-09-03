# Bring-up — open decisions, then the runbook grows here

## Decisions (2026-09-02, Frank)

1. **Audio: Icecast stream + a 3.5 mm AUX output.** Pipeline and the
   USB-audio-adapter recommendation: `AUDIO.md`.
2. **Antenna:** measure the J-pole at 853 MHz in phase 2 before buying.
3. **I-Gate is the default job after reboot.** The scanner is never
   enabled at boot; `sdr-mode scanner` is the deliberate switch.
4. **Repo name `mcfrs-scanner`**; origin `git@github.com:velezf/mcfrs-scanner` (public, created 2026-09-03).
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
- [x] First clear voice calls heard — 2026-09-02 ~15:12: 7A2 Disp (4005) and
      7A1 Ops 1 (4000), both whitelisted, receiver followed the grants.
- [ ] Encrypted talkgroup produces silence, not garbage (the page flags them red;
      confirm by ear when one shows)
- [x] Gain: `LNA:49` (the unit file) locks first try; not yet swept for best BER.
- [x] Audio pipeline up — 2026-09-02: first with `audio.py -s` the mount flapped
      (Icecast source timeout between calls); with `op25-pcm-pace` the mount held
      for 150 s idle-and-busy with zero unit restarts. OP25 web page answers on its port.
- [x] Stream plays on a phone on the LAN — 2026-09-03, Frank: "working great".
- [~] `sdr-mode` round-trip: 2 of 5 done 2026-09-02, both clean (I-Gate reconnected
      to APRS-IS each time; scanner + audio came up together, `NRestarts=0`).
- [ ] Survives reboot in the chosen default mode
- [ ] I-Gate still verified on aprs.fi after switching back

## Legal note (so it is written down once)

Receiving public-safety radio at home is lawful in Maryland; retransmitting
it or using it in furtherance of a crime is not, and decrypting encrypted
traffic is never attempted (`../CLAUDE.md`). Nothing here streams outside
the LAN.
