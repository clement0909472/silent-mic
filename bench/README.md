# Banc de mesure Silent Mic

But : chiffrer ce que l'appareil laisse sortir (micro extérieur) et ce que la dictée garde (micro intérieur), avec et sans l'appareil, dans la même pièce et le même jour.

## Matériel

- **Intérieur** : DJI Mic Mini 2, émetteur dans l'appareil, récepteur USB-C branché au Mac.
- **Extérieur** : Blue Yeti en USB, mode cardioïde, posé face à la bouche à **50 cm**, à hauteur de bouche.
- Pièce calme, fenêtres fermées, ventilation coupée si possible.

## Réglages, une fois pour toutes

1. DJI : **réduction de bruit désactivée**, gain fixe, pas de limiteur ni de piste de sécurité.
2. Yeti : bouton de gain au milieu, puis **scotché**. Ne plus y toucher entre les prises.
3. macOS, Réglages > Son > Entrée : désactiver « Isolation de la voix » ou tout traitement.
4. Le micro DJI reste à la même place pour les prises sans appareil : tenu à 3 cm de la bouche, comme dans l'appareil.

## Lancer

```bash
python bench/record.py --list
python bench/record.py --inside "DJI" --outside "Yeti" --device-name v2 --session v2-$(date +%Y%m%d)
python bench/analyze.py bench/sessions/v2-$(date +%Y%m%d)
```

Le script guide : 15 s de silence (bruit de fond), puis 5 paires sans / avec appareil à voix normale, puis 5 à voix douce, en lisant `bench/texte.md`. Environ 20 minutes. Une session interrompue reprend où elle s'était arrêtée.

## Lire le résultat

| Mesure | Ce qu'elle dit | Cible v3 |
|---|---|---|
| Atténuation dB(A) | baisse du niveau perçu à 50 cm | 10 dB(A) mini sur personne |
| Bandes « >= » | bande noyée dans le bruit de fond, l'atténuation réelle est au moins ce chiffre | |
| Crête DJI | une crête à 0 dBFS ou des prises écrêtées = micro saturé dans l'appareil | aucune prise écrêtée |
| Erreurs dedans avec / sans | la dictée se dégrade-t-elle dans l'appareil ? | écart de 3 points maxi |
| Erreurs dehors avec | ce qu'un voisin comprendrait | le plus haut possible |

## Pièges connus

- Un traitement automatique (DJI ou macOS) fausse tout : il remonte le niveau des prises avec appareil.
- Parler plus fort dans l'appareil : garder le même effort, c'est pour ça que les prises alternent.
- Les sons qui passent par le nez ne sont pas arrêtés par l'appareil : c'est normal, ils limitent le résultat sur une vraie personne.
- Les deux micros ont chacun leur horloge : les niveaux restent justes, mais ne pas comparer les signaux échantillon par échantillon.
