# ADR 0003 — System context: this repo's role

Status: PROPOSED 2026-11-17. The full system map is canonical in
`mcfrs-incidents/docs/adr/0002-system-architecture.md`; this ADR states only
this repo's place in it.

## Role

The radio front end. It receives the county's P25 Phase II system on
`apogee-gs` and turns it into things other repos and people can use. It is
the only MCFRS repo that touches radio hardware, and it does so only while
`apogee-sdr` gives it the dongle.

```
 apogee-sdr (owns the dongle; scanner is one tenant)
   ▼
 mcfrs-scanner: OP25 rx.py (control channel + clear voice)
   ├─► live audio (Icecast) + listening page          → people   BUILT
   ├─► per-call audio files + call metadata           → mcfrs-dispatch-transcribe   PLANNED
   └─► control-channel events (grants, affiliations)  → mcfrs-dispatch-transcribe   PLANNED
```

## Owns

- The decoder setup and system facts: `docs/SYSTEM.md`, `config/*.tsv`, the
  units in `systemd/` (ADR 0001).
- The **formats of what it emits**: the per-call audio and metadata, and
  control-channel events (formats not yet written; `docs/PLAN.md` phase 7).
- The radio-ID → name file used by the listening page (`docs/UI.md`). That
  file is also what `mcfrs-dispatch-transcribe` ADR 0003 proposes to fill
  from transcripts.

## Boundaries

- Never decodes encrypted traffic (`CLAUDE.md`).
- Does not transcribe or interpret dispatches. That is
  `mcfrs-dispatch-transcribe`.
- Does not schedule the dongle. Today `bin/sdr-mode` lives here, but
  `apogee-sdr` ADR 0001 proposes moving it there.
- Never touches the rocket ground station or the LoRa radio (`CLAUDE.md`).

## Trigger to revisit

`apogee-sdr` takes over switching, or a second dongle gives the scanner a
continuous control-channel receiver (`mcfrs-dispatch-transcribe` ADR 0003).
