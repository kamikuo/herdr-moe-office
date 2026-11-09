#!/bin/sh
# Copies mods/moe-office/ into Herdr's mods folder (replacing what's there) and checks it.
set -e
cd "$(dirname "$0")"
DEST="$HOME/.config/herdr-app/mods/moe-office"
rm -rf "$DEST"
cp -R mods/moe-office "$DEST"
herdr-app check "$DEST"
