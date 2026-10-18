#!/bin/bash
# Coleta o chat ao vivo da live com yt-dlp. Único dono de dados/<nome>.live_chat.json*
# Uso: ./coletar.sh <url> <nome>
cd "$(dirname "$0")/dados"
until ../venv/bin/yt-dlp --skip-download --write-subs --sub-langs live_chat -o "$2" "$1"; do
  echo "$(date +%H:%M:%S) reconectando" >&2; sleep 5
done
