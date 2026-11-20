# Silent Mic v3 : dimensionnement acoustique (modèle 1D)

Statut : **estimation de modèle**, non mesurée. Le banc (étape 6) recale le modèle.

Commande : `python acoustics/tmm.py --sweep v3-A` (paramètres dans `acoustics/params.json`, contrôle analytique par `--selfcheck`).

## Résultat

| | v2-compact | v3-A |
|---|---|---|
| Atténuation voix, fuite nominale 0,2 x 30 mm | 6,6 dB(A) (6 à 14 selon le coussin) | **20,8 dB(A)** |
| Pire bande | 100 Hz, +2 dB | 100 Hz, 0 dB |
| Perte de charge à 0,2 / 0,3 L/s | 2 / 5 Pa | 46 / 80 Pa |
| Niveau au micro, voix normale, crête | 124 dB SPL | 154 dB SPL (limite DJI : 120) |

## Ce que le modèle dit

1. **Le v2 fuit surtout par la paroi souple du coussin** (30 mm de mousse à mémoire de forme). L'évent n'est pas son point faible. Son résultat dépend d'une raideur de coussin inconnue : la mesure du v2 sur banc est la meilleure donnée de recalage.
2. **Le v3 tient par trois choix** : cavité de 130 cm³, conduit de 48 mm² (4,5 x 10,7) sur 200 mm à extrémités évasées, joint ferme avec 3 mm de paroi souple exposée.
3. **Le joint visage décide de tout** :

   | Jeu du joint | Fuite locale 30 mm | Tout le périmètre |
   |---|---|---|
   | 0 | 23,0 dB(A) | 23,0 dB(A) |
   | 0,2 mm | 21,8 | 12,2 |
   | 0,5 mm | 9,4 | -5,0 |
   | 1,0 mm | -2,2 | -11,7 |

4. **Compromis confort / atténuation** : 42 mm² donne 21,8 dB(A) pour 67 Pa ; 54 mm² donne 19,8 dB(A) pour 40 Pa. 48 mm² est retenu (46 Pa).
5. **Volume** : 170 cm³ gagnerait 2,4 dB(A) mais agrandit l'objet. 90 cm³ en perd 3.

## Risque principal : saturation du micro

Plus la cavité est étanche, plus la pression y monte. Le modèle (source à débit constant, hypothèse pessimiste sous 300 Hz) prévoit plus de 140 dB SPL dans le v3, au-delà des 120 dB du DJI Mic Mini 2. Le chiffre réel est probablement plus bas (souplesse des joues, effort vocal réduit), mais l'écart est trop grand pour l'ignorer.

- Mesure à faire en premier : enregistrer dans le v2 à voix normale et douce, regarder l'écrêtage.
- Parade dessinée dans la CAO v3 : le support micro accepte un **pod tampon** (le DJI enfermé derrière une membrane rigide de 0,4 à 0,6 mm, -25 à -35 dB à plat sous sa résonance, estimation de plaque encastrée). Il ne s'imprime que si la mesure le justifie.

## Limites du modèle

- Cavité supposée uniforme : faux au-dessus d'environ 2,5 kHz (modes internes).
- Chemins sommés en puissance, pas de rayonnement des tissus ni du nez : sur une vraie personne, compter 3 à 8 dB de moins.
- Bandes 100 et 125 Hz du spectre de voix estimées (ANSI S3.5 commence à 160 Hz).
