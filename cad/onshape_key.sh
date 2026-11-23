#!/bin/bash
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Cle d'API Onshape dans le trousseau macOS. La cle secrete n'est jamais affichee, ni ecrite dans un
# fichier, ni passee en argument d'une commande (visible par ps).
#   cad/onshape_key.sh save     demande de coller la cle d'acces, puis la cle secrete (saisie masquee)
#   cad/onshape_key.sh status   verifie les deux entrees et fait une lecture reelle de l'API
#   cad/onshape_key.sh delete   retire les deux entrees du trousseau
set -euo pipefail
set +x
service="ai.clement-assistant.onshape-api"
api="https://cad.onshape.com/api/v10"

put() {  # compte, valeur ; security -i lit sa commande sur l'entree standard : la valeur n'apparait dans aucune ligne de commande
  # lettres, chiffres, tiret bas et tiret : la cle d'acces Onshape commence par un prefixe a tiret bas
  [[ $2 =~ ^[A-Za-z0-9_-]{20,}$ ]] || { echo "Ce n'est pas une cle Onshape ($1 : ${#2} caracteres recus). Rien n'est enregistre." >&2; exit 1; }
  printf 'add-generic-password -U -s %s -a %s -l onshape-api-%s -w %s\n' "$service" "$1" "$1" "$2" | security -i >/dev/null
}

read_key() { security find-generic-password -s "$service" -a "$1" -w 2>/dev/null; }

case "${1:-}" in
  save)
    printf "Colle la cle d'acces (Access key), puis Entree : "
    read -r a
    printf "Colle la cle secrete (Secret key), puis Entree (rien ne s'affiche, c'est normal) : "
    read -rs s
    echo
    a=${a//[[:space:]]/}
    s=${s//[[:space:]]/}
    put access-key "$a"
    put secret-key "$s"
    echo "Cle d'acces (${#a} caracteres) et cle secrete (${#s} caracteres) enregistrees dans le trousseau."
    "$0" status
    ;;
  status)
    a=$(read_key access-key) || { echo "cle d'acces absente du trousseau"; exit 1; }
    s=$(read_key secret-key) || { echo "cle secrete absente du trousseau"; exit 1; }
    # identifiants passes a curl par un fichier de configuration sur l'entree standard, pas en argument
    code=$(printf 'user = "%s:%s"\n' "$a" "$s" | curl -sS -K - -o /dev/null -w '%{http_code}' "$api/documents?limit=1")
    if [ "$code" = 200 ]; then echo "Onshape API : acces verifie (HTTP 200)."; else echo "Onshape API : refus (HTTP $code)."; exit 1; fi
    ;;
  delete)
    for account in access-key secret-key; do security delete-generic-password -s "$service" -a "$account" >/dev/null 2>&1 || true; done
    echo "Entrees Onshape retirees du trousseau."
    ;;
  *)
    sed -n '3,7p' "$0"; exit 2
    ;;
esac
