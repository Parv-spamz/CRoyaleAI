#!/bin/bash
# Capture the MuMu screen for nav-template calibration: bash scratchpad/gauntlet/L69/nav/capture.sh <screen_name>
set -eu
cd /c/Users/benpe/ClashBot
name="${1:?usage: capture.sh <screen_name>}"
out="scratchpad/gauntlet/L69/nav/raw/${name}_$(date +%H%M%S).png"
"/c/Program Files/Netease/MuMuPlayer/nx_device/15.0/shell/adb.exe" -s 127.0.0.1:16384 exec-out screencap -p > "$out"
echo "saved $out ($(stat -c %s "$out") bytes)"
