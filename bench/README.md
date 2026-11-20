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

Le script guide : 15 s de silence (bruit de fond), puis 3 paires sans / avec appareil à voix normale, douce et très douce, en lisant `bench/texte.md`, plus deux prises nez pincé. Environ 15 minutes. Une session interrompue reprend où elle s'était arrêtée.

Les prises nez pincé disent ce que le nez laisse sortir quand la bouche est couverte : c'est le plafond d'un appareil qui laisse le nez libre.

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

## Test du capot d'essai : quel col choisir

But : mesurer sur ton visage quelle hauteur de col (3, 10 ou 16 mm) laisse le moins sortir le son, avant d'imprimer le corps.

1. `python bench/cap_test.py --make-noise` écrit `bench/bruit-rose.wav`. Le jouer en boucle dans un écouteur sans fil, à volume fixe et modéré.
2. Découper le voile de tissu tendu au dos du coussin, au ras de l'ouverture : sinon le col bute dessus et le coussin ne se plaque pas. Garder le morceau, il peut servir de filtre anti-pop collé sur le haut du col.
3. Mettre l'écouteur et l'émetteur DJI dans le capot, boucher le passage de câble avec de la pâte adhésive, monter le coussin.
4. `python bench/cap_test.py --inside "DJI" --outside "Yeti" --session capot-$(date +%Y%m%d)` : le script demande chaque col trois fois, 12 s par pose, capot plaqué sur le visage, bouche fermée. Environ 10 minutes.
5. `python bench/cap_test.py --report bench/sessions/capot-AAAAMMJJ` donne la fuite par col.

6. Refaire une courte session avec le meilleur col et le dessous du coussin collé au capot par un anneau de ruban double face : `python bench/cap_test.py --inside "DJI" --outside "Yeti" --session capot-colle-$(date +%Y%m%d) --collars 16`, puis `--report`. Le coussin est seulement posé sur son appui : si la fuite baisse nettement (plus que l'écart-type du rapport), le dessous fuyait et le ruban devient une étape du montage.

La fuite est le niveau dehors moins le niveau dedans : elle ne dépend pas du volume de l'écouteur. Plus elle est basse, mieux le col isole. Le modèle prévoit environ 12 dB(A) d'écart entre le col de 3 mm et celui de 16 mm. Un écart nul voudrait dire que le flanc du coussin n'est pas le chemin de fuite principal.
