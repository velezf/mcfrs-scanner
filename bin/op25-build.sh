#!/bin/sh
# op25-build.sh — build OP25 (boatbod, gr310) on apogee-gs. Phase 1 of docs/PLAN.md.
# Mirrors op25/install.sh for GNU Radio 3.10 with three deliberate differences:
#   * non-interactive apt (-y), so it can run detached with a log;
#   * make -j4 (install.sh builds single-threaded);
#   * no `apt-get build-dep gnuradio` — Debian 13 ships no deb-src line in
#     /etc/apt/sources.list, so that step would only error; gnuradio-dev carries the headers.
# Run as:  nohup ~/op25-build.sh > ~/op25-build.log 2>&1 &
# Finishes by printing "BUILD_DONE rc=<0|apt|cmake|make|install>".
set -x
cd "$HOME/op25" || { echo "BUILD_DONE rc=noclone"; exit 1; }
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get install -y gnuradio gnuradio-dev gr-osmosdr librtlsdr-dev libuhd-dev \
    libhackrf-dev liborc-dev cmake git build-essential pkg-config doxygen clang-format \
    python3-pybind11 python3-numpy python3-waitress python3-requests libsndfile1-dev \
    libspdlog-dev || { echo "BUILD_DONE rc=apt"; exit 1; }
echo "/usr/bin/python3" > op25/gr-op25_repeater/apps/op25_python
# rtl-sdr's standard kernel-driver blacklist (same file install.sh installs)
[ -f /etc/modprobe.d/blacklist-rtl.conf ] || sudo install -m 0644 ./blacklist-rtl.conf /etc/modprobe.d/
rm -rf build && mkdir build && cd build || exit 1
cmake ../ 2>&1 | tee cmake.log
[ -f Makefile ] || { echo "BUILD_DONE rc=cmake"; exit 1; }
make -j4 2>&1 | tee make.log
[ -f op25/gr-op25_repeater/lib/libgnuradio-op25_repeater.so ] || { echo "BUILD_DONE rc=make"; exit 1; }
sudo make install 2>&1 | tee install.log || { echo "BUILD_DONE rc=install"; exit 1; }
sudo ldconfig
echo "BUILD_DONE rc=0"
