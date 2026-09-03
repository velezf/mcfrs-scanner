# The listening page — authority for the UI

`bin/mcfrs-ui`, served by `systemd/mcfrs-ui.service` (port stated there), in
every mode; it says "scanner off" when the I-Gate has the dongle.

## What it shows

- **The current call**: zone-channel and name from the OP25 tag
  (`7A2 · Disp`, `7A4 · Inc 10` — the names on the county fleetmap,
  `SYSTEM.md`), the **radio that is keying up now** in yellow, and every
  other radio heard on the same call ("also on this call"). Encrypted calls
  show in red as muted.
- **Recent calls**, newest first, with all radios heard on each and the
  length. Fifty kept, in memory only; restart empties it.
- The Icecast player, so the page is the whole thing on a phone.

## Where it comes from

OP25's http terminal answers a JSON `update` with `change_freq`
(talkgroup id, tag, frequency) and `trunk_update` (`srcaddr` = the radio
transmitting, `grpaddr`, `encrypted`). The page polls that twice a second
and folds it in `Tracker` (`tests/test_ui.py`): a call is one talkgroup
held continuously; a different talkgroup or two idle seconds closes it.

## Radio IDs → names

`config/radio-ids.tsv.example` → `/etc/mcfrs-scanner/radio-ids.tsv` on the
box, reloaded on change. **No public alias list exists any more** —
RadioReference removed the county's alias page by policy, and the forum
thread that used to maintain one says all IDs changed with the P25
cutover. So the file starts empty and is learned from the air: unknown
IDs are shown raw; when a unit says who it is, add the line. Once a
pattern emerges (station/apparatus/position digits), a single `re:` line
covers the whole fleet.

## Not (yet) on the page

- A switch button (start/stop the scanner from the phone). Needs the page
  to run `sdr-mode` with privileges — a later, deliberate step.
- Persistence of history across restarts.
