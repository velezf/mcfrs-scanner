# Audio delivery — authority for the audio pipeline

Decided 2026-09-02 (Frank): **Icecast stream, plus a 3.5 mm AUX output on
the box.** Both come off one pipeline; nothing is duplicated in OP25.

## The pipeline

```
rx.py  -w -W 127.0.0.1 -u 23456        decoded voice, PCM over UDP (loopback only)
   └─▶ audio.py -s -u 23456            OP25's own UDP receiver, -s = raw PCM on stdout
         └─▶ ffmpeg -f s16le -ar 8000 -ac 1 -i -
                ├─▶ icecast://…/mcfrs.mp3     LAN stream (any browser, VLC, phone)
                └─▶ ALSA (USB audio adapter)  the 3.5 mm AUX jack   [optional, see below]
```

- Format facts are OP25's, not ours: `PCM_RATE = 8000` in
  `apps/sockaudio.py`, signed 16-bit little-endian, mono unless
  `audio.py -2`. ffmpeg resamples for each output.
- The whole thing is `bin/mcfrs-audio`, run by `systemd/mcfrs-audio.service`,
  which is `BindsTo=` the scanner unit: it starts and stops with it and
  never runs alone.
- Per-box secrets/devices live in `/etc/mcfrs-scanner/audio.env`
  (template `config/audio.env.example`, never committed filled-in).
- Icecast listens on the port in `config/audio.env.example`; the mount is
  `/mcfrs.mp3`. Play it at `http://apogee-gs:<port>/mcfrs.mp3`.
- Encrypted calls are silenced upstream by `rx.py -n`; they never reach
  this pipeline.

## The 3.5 mm AUX answer

The Pi 5 has **no analog audio jack**, its USB-C port is power-only, and
the spare micro-HDMI would need an HDMI audio extractor (another box,
another PSU). The right part is a **class-compliant USB audio adapter**
in one of the free USB-A ports:

- Any "USB to 3.5 mm, no driver needed" dongle works — the Linux kernel
  driver is `snd-usb-audio`, in the box's kernel already. Known-good,
  cheap examples: Sabrent AU-MMSA, UGREEN USB External Stereo Sound
  Adapter, Plugable USB-AUDIO. About $8–12. Avoid anything advertising
  "gaming"/"7.1"/RGB — those often want vendor drivers.
- Then a plain 3.5 mm TRS stereo cable from the adapter's headphone/line
  out to the AUX IN of whatever speaker or amp is in the room. Headphone
  level into a line input is fine; set the adapter volume to ~80 % with
  `alsamixer` once and leave it.
- Enable it by setting `ALSA_DEV` in `audio.env` to the adapter's ALSA
  name (`aplay -L` lists it; it will look like `plughw:CARD=Device,DEV=0`).
  Leave it empty and the pipeline streams to Icecast only.

The adapter is dumb and the pipeline is one ffmpeg, so this can be added
after the stream is already working — no re-plumbing.
