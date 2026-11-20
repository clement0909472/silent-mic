#!/bin/bash
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Lance une commande avec un plafond de memoire et de duree, et la tue au-dela.
# Un booleen OCCT qui degenere peut prendre 280 Mo/s : le 20 nov. 2026 cela a sature la machine.
#   cad/guarded.sh [-m Go] [-t secondes] commande...     (defauts : 6 Go, 600 s)
max_gb=6; max_s=600
while getopts "m:t:" o; do case $o in m) max_gb=$OPTARG ;; t) max_s=$OPTARG ;; *) exit 2 ;; esac; done
shift $((OPTIND - 1))
"$@" &
pid=$!
while kill -0 "$pid" 2>/dev/null; do
  # empreinte reelle vue par top : le RSS de ps reste faible quand la memoire est compressee
  raw=$(top -l 1 -pid "$pid" -stats mem 2>/dev/null | tail -1 | tr -d ' +-')
  mb=$(awk -v v="$raw" 'BEGIN { n = v + 0; u = substr(v, length(v)); if (u == "G") n *= 1024; else if (u == "K") n /= 1024; else if (u == "B") n /= 1048576; printf "%d", n }')
  if [ "${mb:-0}" -gt $((max_gb * 1024)) ]; then
    kill -9 "$pid" 2>/dev/null
    echo "GARDE : arret a ${mb} Mo (plafond ${max_gb} Go) : $*" >&2
    exit 137
  fi
  if [ "$SECONDS" -gt "$max_s" ]; then
    kill -9 "$pid" 2>/dev/null
    echo "GARDE : arret apres ${max_s} s : $*" >&2
    exit 124
  fi
  sleep 1
done
wait "$pid"
