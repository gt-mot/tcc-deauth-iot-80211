#!/bin/bash
# Uso: sudo ~/captura_tcc.sh NOME CENARIO REP IP_ALVO [CANAL]
NOME=$1; CEN=$2; REP=$3; IP=$4; CANAL=${5:-6}
DIR=/home/kali/TCC_TESTES/03_capturas_originais
mkdir -p "$DIR"; BASE="$DIR/${NOME}_${CEN}_${REP}"; IFACE=wlan0mon
iw dev $IFACE set channel $CANAL 2>/dev/null
echo "[*] Capturando em $IFACE (canal $CANAL) -> ${BASE}.pcapng"
tcpdump -i $IFACE -w "${BASE}.pcapng" & TPID=$!
echo "[*] Ping -D para $IP -> ${BASE}_ping.txt"
ping -D "$IP" > "${BASE}_ping.txt" & PPID2=$!
echo "==================================================="
echo " AGORA dispare o ataque no LILYGO (Bruce) contra $IP"
echo " Observe o aparelho. Espere ele voltar (ou ~3 min)."
echo " Pressione ENTER para encerrar a captura."
echo "==================================================="
read
kill $TPID $PPID2 2>/dev/null; sleep 1
echo "[OK] Salvos: ${BASE}.pcapng  e  ${BASE}_ping.txt"
