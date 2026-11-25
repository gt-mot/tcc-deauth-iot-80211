#!/usr/bin/env bash
DIR=/home/kali/TCC_TESTES/03_capturas_originais
mkdir -p "$DIR"
case "$1" in
  start)
    NAME="$2"; IP="$3"; CH="${4:-6}"; BASE="$DIR/$NAME"
    sudo pkill -f "tcpdump -i wlan0mon" 2>/dev/null; pkill -f "ping -D -i 0.5" 2>/dev/null; sleep 1
    sudo iw dev wlan0mon set channel "$CH" 2>/dev/null
    setsid sudo tcpdump -i wlan0mon -w "$BASE.pcapng" </dev/null >/dev/null 2>&1 &
    setsid ping -D -i 0.5 "$IP" </dev/null >"${BASE}_ping.txt" 2>&1 &
    sleep 3
    echo "[start] $NAME ip=$IP ch=$CH"
    echo -n "tcpdump: "; (pgrep -a tcpdump | head -1) || echo NAO
    echo -n "ping:    "; (pgrep -a ping | head -1) || echo NAO
    ls -l "$BASE.pcapng" 2>/dev/null
    ;;
  stop)
    sudo pkill -f "tcpdump -i wlan0mon" 2>/dev/null; pkill -f "ping -D -i 0.5" 2>/dev/null; sleep 1
    echo "[stop] encerrado"
    ;;
esac
