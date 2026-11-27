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

Bosses dans le conduit (1D, 25 nov. 2026, idée de Clément inspirée des plaques de mousse à bosses) : 19 bosses rigides de
1 mm tous les 8 mm, +0,6 dB(A) pour 135 Pa à 0,2 L/s ; de 2 mm, +1,6 dB(A) pour 224 Pa ; un conduit lisse de 36 mm²
donne +1,4 dB(A) pour 58 Pa. En PLA, les bosses ne font que rétrécir le conduit par endroits, avec des pertes de
tourbillon en plus. Ce qui fait marcher la mousse à bosses, c'est la mousse qui absorbe : un garnissage absorbant de 1 à
2 mm (feutre ou mousse, section d'air gardée à 42 mm²) amortit le creux du conduit vers 1 kHz mais perd plus vers 500 à
800 Hz, soit −0,6 à −1,7 dB(A), et garderait l'humidité du souffle. Conclusion : le conduit lisse, réglé par sa section.

Section retenue : 42 mm² (25 nov. 2026, avec Clément). Balayage fin, 1D, conduit décalé, joint fermé ; 0,2 L/s est le
débit de la parole, 0,5 L/s une expiration par la bouche entre deux phrases :

| Conduit | Atténuation | Effort à 0,2 L/s | à 0,5 L/s |
|---|---|---|---|
| 36 mm² | 28,8 dB(A) | 58 Pa | 255 Pa |
| 38 mm² | 28,3 dB(A) | 53 Pa | 233 Pa |
| 40 mm² | 27,8 dB(A) | 50 Pa | 215 Pa |
| **42 mm²** | **27,4 dB(A)** | **47 Pa** | **200 Pa** |
| 44 mm² | 26,9 dB(A) | 44 Pa | 186 Pa |
| 48 mm² | 26,1 dB(A) | 40 Pa | 164 Pa |

La courbe n'a pas de coude : chaque 2 mm² retirés donnent environ 0,5 dB(A) pour 3 Pa de plus. Le critère de confort de
la cible v3 (50 Pa au plus à 0,2 L/s) s'atteint à 40 mm² ; 42 mm² garde une marge de 3 Pa. L'effort à l'expiration
(200 Pa) est le point à vérifier au premier essai porté : s'il gêne, 48 mm² rend 36 Pa pour 1,3 dB(A).

## Tenue des vissages et parois de la chambre (26 nov. 2026)

Statique linéaire 3D, openCFS et tétraèdres quadratiques gmsh : `mechanics/fem/run.py` (`--selfcheck`, `--col`, `--boss`, `--shell`, `--post` pour relire un calcul). PLA plein isotrope (E = 3,5 GPa, ν = 0,36), écrous M3 en acier collés au seul plafond de leur logement. Validation : console sous charge répartie, flèche à 1,4 % et contrainte à 1,9 % de la théorie. Le PLA imprimé tient moins entre couches que dans leur plan : seuils de 15 à 25 MPa entre couches et de 40 à 50 MPa dans le plan (fourchettes de fiches, non mesurées sur nos pièces). Contraintes lues au 99e centile autour de chaque vis, pour écarter les pointes des angles vifs (singularités du modèle, émoussées dans une vraie pièce). Solveur : gradient conjugué natif d'openCFS (CHOLMOD dépasse 8 Go au-delà d'environ 100 000 tétraèdres quadratiques ; LIS, PETSc et Pardiso ne sont pas compilés), 5 à 30 minutes par calcul.

| Vissage | Premières fissures | Rupture | Pour fermer le joint |
|---|---|---|---|
| Col sur capot v05 (peau de 1,2 mm sur l'écrou) | 130 à 210 N par vis | 480 à 600 N | 50 à 200 N (néoprène, estimation) |
| Col sur capot v06 (peau de 2 mm) | 190 à 320 N | 650 à 810 N | idem |
| Capot sur coque (tête fraisée dans le bossage) | 750 N : la tête marque sa fraisure | 1 800 N dans le bossage ; la vis plie vers 2 200 N | butée : écrasement fixé |

Le col posé sur ses diamants ne touche pas la plaque au-dessus des écrous : la peau travaille en poinçonnement et la plaque fléchit (l'écrou monte de 0,9 µm par newton). Au joint capot/coque, tout est en compression entre deux bossages en butée. Repères de serrage d'une M3 (coefficient 0,2, estimation) : 0,1 N·m du bout des doigts, environ 170 N ; 0,5 N·m à pleine main, environ 800 N. Le col se serre donc du bout des doigts, le capot peut se serrer franchement.

**Parois de la chambre.** Capot et coque collés au plan de joint, appui du col tenu, 1 Pa sur les 26 400 mm² qui bordent l'air de la chambre et du conduit : le volume d'air gagne 1,18 × 10⁻¹² m³/Pa, 0,08 % de la souplesse de l'air lui-même, et 2,6 fois moins que l'hypothèse du modèle 1D (3,06 × 10⁻¹²). Dans le modèle 1D, le chemin par les parois descend alors de 50-54 à 59-62 dB d'atténuation, quand l'évent est à 6-36 dB : 26,3 dB(A) dans les trois cas (hypothèse, calcul, parois rigides). Valable sous la première résonance des parois, non calculée (pas de solveur de valeurs propres compilé) : un panneau de PLA de 3 mm, encastré, de 50 à 80 mm de portée, résonne vers 1,6 à 4 kHz (calcul de plaque, estimation), là où la voix pondérée A pèse peu.

## Temps de calcul

Sur ce Mac (openCFS 26.09 ARM64, 1 cœur) : 0,03 s de résolution par fréquence (6 700 à 15 300 nœuds avec le dispositif). Il faut 17 s pour v3-A complet (deux jeux, 20 bandes, maillage compris) et 3 s pour la validation.

## Limites

Équivalent axisymétrique seulement : ni l'hélice, ni les sorties latérales, ni la tête. Parois rigides (justifié sous 1,5 kHz environ : voir « Parois de la chambre »). Écrans ignorés. Mousse et fente en fluides équivalents (lois empiriques). Le prochain pas utile est une mesure au banc, pas un modèle 3D.

## Modèle 3D de l'appareil assemblé (27 nov. 2026)

Demande de Clément : simuler l'appareil complet, bouche appliquée sur le coussin. `acoustics/fem3d/run.py` (maillage `mesh3d.py`, gmsh, 114 000 nœuds ; `--selfcheck`, puis `--per-band 3`). Air de la chambre et du conduit tel que dessiné (STEP technique v12, inchangé en v13), mousses Mr Propre en fluide équivalent (Delany-Bazley, σ = 12 000 Pa·s/m², 23,1 et 20,5 cm³), conduit et fentes avec pertes visqueuses (Zwikker-Kosten), joint capot / coque et coussin hermétiques, parois et visage rigides, bouche = disque de 10 mm de rayon au centre du visage, sorties de l'évent (434 mm²) rayonnant comme un piston bafflé. Puissance et débit recalculés sur les triangles des sorties (le `acouPower` d'openCFS était faux sur le galet, juste sur un tube de contrôle).

Estimations, non mesurées : **23,9 dB(A)** d'atténuation de la voix en puissance, 25,6 en débit (1D hermétique 27,7 ; 2D 25,9). Sous 1 kHz, le 3D suit le 1D à 1 dB près ; au-dessus, il voit des creux dus aux modes réels de la chambre et du conduit : 17 à 18 dB vers 1 et 2 kHz, 21 dB à 3,15 kHz. Micro : 137 dB SPL efficace, 149 en crête, pour 120 au DJI : la saturation reste le premier risque. Maillage : 114 000 contre 181 000 nœuds, 23,1 contre 23,0 dB(A).

Limites : pas de domaine extérieur maillé (ni écran du corps, ni couplage entre fentes), bonnette comptée comme de l'air, point du micro supposé 1 mm au-dessus du DJI, coque et coussin rigides et étanches.
