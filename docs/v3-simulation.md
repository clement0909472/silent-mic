# Silent Mic v3 : contrôle par éléments finis (openCFS)

Statut : **modèle numérique validé sur un cas analytique**, non mesuré. Il vérifie le modèle 1D (`acoustics/tmm.py`), il ne remplace pas le banc.

Commandes : `python acoustics/fem/run.py --selfcheck`, puis `--design v3-A` (ou `v2-compact`). Sorties dans `acoustics/fem/work/<design>/result.json` (non versionné).

## Ce qui est modélisé

- 2D axisymétrique r-z, éléments quadratiques, h ≤ λ/6 à la fréquence haute de chaque bande, au moins 3 éléments dans le conduit et la fente. Un maillage et un calcul par tiers d'octave (6 fréquences par bande, 100 Hz à 8 kHz).
- Visage = baffle plan rigide infini. Bouche = piston de 10 mm de rayon à débit imposé. Référence : même bouche sans dispositif.
- Cavité = cylindre de même volume (130 cm³) et de même périmètre de joint (183 mm, R = 29,1 mm, L = 48,8 mm). Les 39 cm³ de mousse forment un anneau contre la paroi, en fluide équivalent Delany-Bazley (σ = 12 000).
- Évent = tube axial de même section (48 mm², r = 3,9 mm) et de 200 mm, en fluide équivalent Zwikker-Kosten (rayon hydraulique du conduit rectangulaire, `tmm.zk_fluid`). Pas de maillage de couche limite.
- Fuite du joint : fente annulaire sur tout le périmètre, profondeur 8 mm, fluide équivalent de Poiseuille plan (même loi que `tmm.z_slit`). Jeux 0 et 0,2 mm.
- Champ libre : PML (`inverseDist`). Perte par insertion = puissance rayonnée sans / avec dispositif, intégrée sur une frontière air/air avant la PML.

Non modélisé : écrans résistifs (impédance négligeable devant le conduit), paroi souple du coussin et coque (parois rigides), forme réelle (hélice, sorties latérales, tête), nez, tissus.

## Validation analytique

Piston plan bafflé de 10 mm dans le même montage : puissance à **±0,15 dB** de la formule exacte de 100 Hz à 8 kHz, pression sur l'axe à ±0,2 dB.
Piège trouvé : la PML axisymétrique réfléchit en basses fréquences si elle est proche (puissance x3,3 à 100 Hz avec une boîte de 12 cm). La boîte de chaque bande est donc éloignée d'au moins 0,6 λ.

## FEM contre modèle 1D, v3-A, joint fermé

« 1D équivalent » = `tmm.py` avec les mêmes simplifications (sans écrans, coussin ni coque). « FEM débit » = débit sortant de l'évent mesuré par deux points dans le conduit, comparable au 1D, qui raisonne en débits.

| Bande (Hz) | 1D nominal | 1D équivalent | FEM puissance | FEM débit | Écart débit |
|---|---|---|---|---|---|
| 100 | 0,6 | 0,5 | 0,8 | 0,5 | 0,0 |
| 125 | 6,9 | 6,8 | 7,3 | 6,8 | 0,0 |
| 160 | 12,3 | 12,3 | 13,0 | 12,2 | -0,1 |
| 200 | 16,6 | 16,5 | 17,6 | 16,4 | -0,1 |
| 250 | 20,3 | 20,3 | 22,0 | 20,2 | -0,1 |
| 315 | 23,7 | 23,7 | 26,2 | 23,5 | -0,2 |
| 400 | 26,5 | 26,5 | 29,8 | 26,3 | -0,2 |
| 500 | 28,0 | 28,0 | 31,5 | 27,6 | -0,4 |
| 630 | 26,9 | 26,8 | 29,4 | 26,2 | -0,6 |
| 800 | 15,3 | 14,7 | 16,3 | 13,8 | -0,9 |
| 1000 | 27,6 | 28,1 | 29,5 | 26,7 | -1,4 |
| 1250 | 35,3 | 35,9 | 36,9 | 33,7 | -2,2 |
| 1600 | 25,3 | 25,2 | 24,4 | 21,5 | -3,7 |
| 2000 | 37,1 | 38,4 | 35,6 | 32,6 | -5,8 |
| **dB(A) voix** | **21,8** | **21,4** | **22,5** | | |

Lecture :

1. **La physique interne concorde** : débit d'évent à 0,6 dB près jusqu'à 630 Hz, 1,4 dB à 1 kHz. La pression dans la cavité concorde à 0,3 dB jusqu'à 1 kHz.
2. **L'écart en puissance (jusqu'à 3,5 dB vers 400-500 Hz) vient du rayonnement, pas de l'évent**. Dans le modèle axisymétrique, la sortie de l'évent est à 25 cm du visage et rayonne moins qu'une bouche plaquée sur le visage. La formule de la source image explique cet écart à 0,2 dB près dans toutes les bandes jusqu'à 1 kHz. Dans l'objet réel, les sorties sont près du visage : l'hypothèse du 1D y est plus juste.
3. **Au-delà de 1,5 kHz, le 1D est optimiste** : modes de la cavité (premier mode axial vers 3,5 kHz) et du conduit. La FEM donne 12 à 25 dB vers 2,5-3,15 kHz et à 8 kHz, contre 31 à 48 dB pour le 1D. Le poids A de ces bandes est faible : l'écart sur les dB(A) reste à 1,1 dB.
4. **Jeu de 0,2 mm sur tout le périmètre** : FEM 12,4 dB(A), 1D équivalent 11,0 (doc 1D : 12,2). Le surplus de résistance de la fente en FEM vient de l'anneau de mousse que la fuite doit traverser. Sans mousse, la pression de cavité concorde à 0,4 dB.

v2-compact (axisymétrique équivalent, coussin rigide) : -8,3 dB(A) joint fermé et 2,1 dB(A) avec 0,2 mm, contre -5,2 et 1,9 pour le 1D équivalent. La résonance de Helmholtz vers 200 Hz domine. Le 1D nominal (6,6 dB(A)) est gouverné par la paroi souple du coussin, absente de la FEM.

## Galet, section du conduit (25 nov. 2026)

Évent proposé pour la coque arrière : conduit décalé vers l'extérieur (paroi vers la chambre d'au moins 3,3 mm), une seule
sortie en pente vers le bas de 41,7 × 3,6 mm, joint au visage fermé (essai de Clément : aucun jour). Même chaîne
axisymétrique équivalente que ci-dessus ; paramètres dérivés de `acoustics/params.json` (conduit allongé de 9,8 mm).

| Conduit | FEM | 1D équivalent | 1D nominal | Effort à 0,2 L/s |
|---|---|---|---|---|
| 48 mm² | 23,9 dB(A) | 25,5 | 26,1 | 40 Pa |
| 42 mm² | 25,2 dB(A) | 27,0 | 27,3 | 47 Pa |
| 36 mm² | 26,5 dB(A) | 28,7 | 28,8 | 58 Pa |

La FEM confirme les écarts entre sections (+1,2 dB de 48 à 42 mm², +1,3 de 42 à 36) et reste environ 2 dB sous le 1D,
optimiste dans les aigus (modes de la cavité et du conduit). Chicanes en travers du conduit (1D) : 3 plaques ne laissant
que 50 % de la section donnent +0,3 dB(A) pour 251 Pa à 0,2 L/s, quand rétrécir le conduit de 42 à 36 mm² donne +1,5
dB(A) pour +11 Pa : les plaques coûtent l'effort en pertes de jet, pas en masse acoustique, et leurs arêtes sifflent.
Paroi souple du coussin exposée (1D) : bande de 1 mm sur le tour, −0,2 à −1,7 dB ; de 5 mm, −3,9 à −10,7 dB ; le col de
20 mm doit donc rester au-dessus du coussin comprimé partout. Environnement : gmsh et h5py réinstallés depuis
`requirements.txt` le 25 nov. 2026 (ils manquaient au `.venv`), validation analytique repassée à 0,15 dB.

## Temps de calcul

Sur ce Mac (openCFS 26.09 ARM64, 1 cœur) : 0,03 s de résolution par fréquence (6 700 à 15 300 nœuds avec le dispositif). Il faut 17 s pour v3-A complet (deux jeux, 20 bandes, maillage compris) et 3 s pour la validation.

## Limites

Équivalent axisymétrique seulement : ni l'hélice, ni les sorties latérales, ni la tête. Parois rigides. Écrans ignorés. Mousse et fente en fluides équivalents (lois empiriques). Le prochain pas utile est une mesure au banc, pas un modèle 3D.
