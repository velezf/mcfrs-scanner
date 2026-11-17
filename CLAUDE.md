# CLAUDE.md — working memory for mcfrs-scanner

P25 Phase II scanner for Montgomery County (MD) Fire/Rescue, running on the
same Pi 5 (`apogee-gs`) as the rocket ground station and the APRS I-Gate.

**To resume work, read `docs/PLAN.md` (phases + next gate) and
`docs/BRINGUP.md` (open decisions, verification bar) first.**

## Working agreement

Gates, TDD and commit format: `~/.claude/CLAUDE.md`. Cross-project conventions
(cite, don't restate; hollow checks; the Pi is exclusive to the main thread):
`~/code/CLAUDE.md`. Authorities for literal values in this repo: `docs/SYSTEM.md`
(radio system identifiers, talkgroups — the prose copy), `config/*.tsv` (the
copies the decoder loads), `systemd/*.service` (paths, ports, unit relationships).

## Box facts (measured 2026-09-02 over ssh, `ssh apogee-gs`)

- Raspberry Pi 5 Model B, 4 cores, 8 GB, Debian 13 (trixie) aarch64,
  Python 3.13, ~24 GB free on the card.
- ONE RTL-SDR (Blog V4, `0bda:2838`), packaged `rtl-sdr` 2.0.2 already
  detects it. `gnuradio` 3.10.12 and `gr-osmosdr` 0.2.6 are available from
  apt (not yet installed).
- Running services: `apogee-ingest`, `apogee-panel` (rocket), `aprs-igate`
  (owns the dongle whenever it runs). Audio hardware: HDMI only.
- **TCP ports already taken on the box** (measured 2026-09-02, `ss -ltnp`):
  8080 = rocket ingest dashboard, 8000/8001 = direwolf AGW/KISS (the I-Gate),
  8421–8423 = pisugar-server. Ours are stated once: Icecast in
  `config/audio.env.example`, the OP25 web terminal in
  `systemd/mcfrs-scanner.service`, the listening page in
  `systemd/mcfrs-ui.service`. Never pick 8000 or 8080.
- Operator account `rocketman` (in `audio`, `plugdev`, `sudo`).
- Antenna on the dongle (Frank, 2026-11-17): a small antenna, NOT the roof
  Arrow J-pole. It heard nothing at 853 MHz (`docs/adr/0002-over-the-air-dispatch-data.md`,
  Evidence). The J-pole (2 m / 70 cm, not resonant at 853 MHz) locked first try
  on 2026-09-02 (`docs/BRINGUP.md`). Anything that needs the control channel
  waits for the J-pole or an 800 MHz antenna.

## What must never happen

- Never start the scanner while `aprs-igate` holds the dongle, or vice
  versa. The systemd `Conflicts=` pair is the guard; `bin/sdr-mode` is the
  only sanctioned switch. Do not `systemctl start` either unit by hand.
- Never touch `apogee-ingest` / `apogee-panel` / the LoRa radio from this
  repo. They are a different failure domain and a different repo.
- Never attempt to decode encrypted talkgroups. OP25 is run with encrypted
  audio muted; the tags file marks them `[ENC]` so nobody wonders.
