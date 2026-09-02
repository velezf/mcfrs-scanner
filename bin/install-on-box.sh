#!/bin/sh
# install-on-box.sh — put this repo's pieces where systemd and the shell find them.
# Run ON apogee-gs from a checkout (rsync the repo over, then: sudo ./bin/install-on-box.sh).
# Idempotent. Does NOT enable the scanner at boot: the I-Gate is the default job
# (decided 2026-09-02); the scanner is what you switch to with `sdr-mode scanner`.
set -eu
cd "$(dirname "$0")/.."
export DEBIAN_FRONTEND=noninteractive
apt-get install -y icecast2 ffmpeg

install -d /etc/mcfrs-scanner
install -m 0644 config/mcfrs.tsv config/mcfrs-whitelist.tsv /etc/mcfrs-scanner/
[ -f /etc/mcfrs-scanner/mcfrs-trunk.tsv ] || install -m 0644 config/mcfrs-trunk.tsv.example /etc/mcfrs-scanner/mcfrs-trunk.tsv
[ -f /etc/mcfrs-scanner/audio.env ]      || install -m 0640 -o root -g rocketman config/audio.env.example /etc/mcfrs-scanner/audio.env
# The trunk.tsv names its tags/whitelist files relative to the OP25 apps dir; point them at /etc.
sed -i 's#\tmcfrs.tsv\t#\t/etc/mcfrs-scanner/mcfrs.tsv\t#; s#\tmcfrs-whitelist.tsv\t#\t/etc/mcfrs-scanner/mcfrs-whitelist.tsv\t#' /etc/mcfrs-scanner/mcfrs-trunk.tsv

install -m 0755 bin/sdr-mode bin/mcfrs-audio bin/op25-pcm-pace /usr/local/bin/
install -m 0644 systemd/mcfrs-scanner.service systemd/mcfrs-audio.service /etc/systemd/system/

# Icecast: source password from audio.env; Debian's unit needs ENABLE=true on older packages.
PW=$(sed -n 's/^ICECAST_PW=//p' /etc/mcfrs-scanner/audio.env)
if [ "$PW" = "change-me" ] || [ -z "$PW" ]; then
    echo "!! set ICECAST_PW in /etc/mcfrs-scanner/audio.env, then re-run" >&2; exit 1
fi
PORT=$(sed -n 's/^ICECAST_PORT=//p' /etc/mcfrs-scanner/audio.env)
sed -i "s#<source-password>.*</source-password>#<source-password>${PW}</source-password>#" /etc/icecast2/icecast.xml
# Icecast's stock listen port (8000) is direwolf's AGW port on this box; move it (audio.env is the authority).
sed -i "s#<port>8000</port>#<port>${PORT:-8100}</port>#" /etc/icecast2/icecast.xml
[ -f /etc/default/icecast2 ] && sed -i 's/^ENABLE=false/ENABLE=true/' /etc/default/icecast2 || true
systemctl enable icecast2
systemctl restart icecast2

systemctl daemon-reload
echo "installed. switch with: sdr-mode scanner | sdr-mode igate | sdr-mode"
