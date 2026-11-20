# Silent Mic v3 galet : impression et montage

État au 20 novembre 2026. Rien n'est encore imprimé : temps et masses viennent du tranchage Bambu Studio, le montage vient de la CAO (`cad/silent_mic_v3_galet.py`, aucune interférence détectée).

## Impression

Bambu Lab A1 mini, buse 0,4 mm, couches de 0,20 mm, 4 périmètres, 20 % de remplissage, couture alignée, plaque PEI texturée. PLA : préréglage « ELEGOO PLA Mat Flow Rate Calibrated » de Clément (débit 1,029, densité 1,32). PETG : « Bambu PETG Translucent @BBL A1M ». Fichiers dans `cad/out/v3-galet/`.

### Pièces d'essai : projets Bambu Studio prêts à imprimer

Dans `print/`, trois projets 3MF tranchés, réglages embarqués, aucun support demandé (contrôle fait avec supports automatiques et « ne pas supporter les ponts »). Ils se rouvrent et se retranchent à l'identique en ligne de commande. On les ouvre dans Bambu Studio, on choisit l'imprimante, on lance. Régénération : `cad/bambu_3mf.sh` (lit le préréglage de Clément sans le modifier).

| Plateau | Fichier | Contenu | Temps | Filament |
|---|---|---|---|---|
| 1 | `print/capot-essai.3mf` | capot d'essai du coussin | 3 h 15 | 66 g PLA |
| 2 | `print/cols-et-joint.3mf` | cols de 3, 10 et 16 mm, éprouvettes de joint avant et arrière | 1 h 36 | 28 g PLA |
| 3 | `print/lumiere-petg.3mf` | éprouvette de lumière | 5 min | 1 g PETG |

Grammes calculés par Bambu Studio avec la densité réelle du filament (1,32) : le tableau OrcaSlicer précédent comptait 1,24, d'où environ 6 % de moins.

### Corps : projets Bambu Studio prêts

| Plateau | Fichier | Contenu | Temps | Filament |
|---|---|---|---|---|
| 4 | `print/corps-capot-avant.3mf` | capot avant, appui du coussin sur le plateau | 2 h 57 | 48 g PLA |
| 5 | `print/corps-coque-arriere.3mf` | coque arrière, face arrière sur le plateau | 4 h 42 | 72 g PLA |
| 6 | `print/corps-trappe-col.3mf` | trappe et col de 14 mm | 57 min | 17 g PLA |
| 7 | `print/corps-anneau-petg.3mf` | anneau lumineux | 7 min | 2 g PETG |

Mêmes réglages que les pièces d'essai. Le corps ne s'imprime qu'après le test des cols (`bench/README.md`) et l'essai des éprouvettes de joint. Régénération : `cad/bambu_3mf.sh corps`.

Seule la coque arrière a des supports, réglés sur « Sur plateau uniquement » : ils restent sous le passage de la prise USB-C, dans la baie cachée par la trappe (de 0,2 à 10,4 mm de haut). En automatique, le trancheur monterait en plus une tour dans la cavité, sous les butées du nid du micro, et pourrait en poser dans les fentes de sortie.

## Contrôles avant impression

Trois contrôles tournent sur les fichiers à imprimer eux-mêmes, pas sur l'intention du dessin.

- **Maillages fermés.** À l'export, chaque STL est nettoyé puis refusé si une arête n'est pas partagée par exactement deux faces (`clean_stl` dans `cad/silent_mic_v3_coupons.py`). OCCT laissait un triangle vide au sommet de chaque toit conique de logement d'aimant : 4 sur la coque arrière, 2 sur une éprouvette de joint.
- **Étanchéité.** `cad/leak_check.py` remet les STL en position de montage, les découpe en voxels de 0,25 mm et « inonde » l'air de la chambre. Résultat dans `cad/out/v3-galet/leak-check.json`.
- **Ouvertures mesurées dans la CAO.** `export()` mesure la section de l'entrée et des fentes là où elles percent les parois, et refuse un modèle où elles ne débouchent pas.

![Coupes du modèle : chambre, conduit, fentes, baie](img/v3-etancheite.png)

| Contrôle d'étanchéité | Résultat |
|---|---|
| La chambre rejoint l'extérieur par le conduit | oui |
| Fentes bouchées : la chambre est étanche | oui, donc aucune autre ouverture |
| Entrée bouchée : la chambre est étanche | oui, donc une seule entrée dans le conduit |
| Conduit bouché à midi : la chambre est étanche | oui, donc l'air fait le tour complet |
| Trou témoin de 1 mm² percé dans la paroi | détecté |
| Fentes | 4, de 9,3 mm de long, passage réel de 1,7 mm, 62 mm² en tout |
| Entrée et section du conduit | 49 et 48 mm² |

Le contrôle suppose trois fermetures qu'il ne prouve pas : le joint mousse du plan de joint, le coussin collé sur son appui, le visage sur le coussin. La baie de l'électronique, la prise USB-C, la fente de l'interrupteur, le tunnel des fils et la rainure LED sont ouverts sur l'extérieur, mais séparés de la chambre par des parois pleines.

**Défauts trouvés et corrigés le 20 novembre 2026.**

- Les 4 fentes ne débouchaient pas dans le conduit (0,2 à 0,9 mm de plastique restaient au bout) et l'entrée du conduit était presque fermée côté chambre (peau de 0 à 0,5 mm). Fentes et entrée étaient posées sur la section du plan de joint, alors que conduit, gorge et chambre suivent la peau, qui s'affine vers l'arrière. Les sections annoncées venaient de formules, pas de la pièce.
- Les fentes étaient inclinées à 22° de la verticale : leur passage réel ne faisait que 0,9 mm, soit 38 mm² en tout, moins que le conduit (48 mm²). Elles sont à 38°, comme les autres surplombs internes : 1,7 mm et 62 mm². Au modèle acoustique : 21,2 dB(A) inchangés, 48 Pa à 0,2 L/s au lieu de 71 Pa.
- La quatrième fente dépassait au-dessus de la gorge, à moitié borgne. Les 4 fentes tiennent maintenant sous la gorge.
- Les logements des pastilles d'acier crevaient la peau de la trappe : 4 encoches visibles au dos. Les 4 aimants de la trappe sont déplacés entre la baie et le flanc de la trappe.

**À vérifier sur la pièce imprimée.** Souffler dans l'entrée du conduit (dans la paroi de la coque arrière, en bas à droite quand on la regarde de face) : l'air doit sortir par les 4 fentes, sous l'anneau. Une fente obstruée par un fil se dégage avec une lame fine.

## Montage

Trois coques s'empilent le long de l'axe, sans aucune vis : trappe, coque arrière, capot avant. Tout entre par deux ouvertures. La vue « Montage » de la visionneuse montre les étapes.

**Une fois, à la colle cyanoacrylate**

- 8 aimants 6 × 2 dans les bossages du bord de la coque arrière, 8 pastilles d'acier en face dans le capot avant.
- 4 aimants dans le dos de la coque arrière : deux au-dessus de la baie, un de chaque côté. Ils dépassent de 0,9 mm et centrent la trappe. 4 pastilles dans la trappe.
- Le disque d'acier de 30 mm sur la tête du pied du micro.
- La bande de mousse 3 × 2 au fond de la rainure du capot avant.

**Par l'arrière, la baie (hors du volume acoustique)**

1. La batterie au fond, le chargeur par-dessus avec sa prise USB-C vers le bas, l'interrupteur à côté. Un ruban isolant entre le chargeur et la batterie, un point de mousse double face pour caler.
2. Les deux fils du ruban LED montent par un tunnel de 2,6 mm jusqu'au bord de la coque, sans traverser la chambre.
3. La trappe se pose, tenue par ses 4 aimants.

**Par l'avant, le plan de joint (au niveau de l'anneau lumineux)**

4. Les deux couches de mousse du fond (10 mm chacune), encoche vers le bas, autour du pied du micro. Le chanfrein sous le conduit les retient.
5. Le ruban LED dans sa rainure, l'anneau translucide par-dessus.
6. Le micro sur son pied, grille vers le haut : on le descend tout droit entre les 8 butées du nid (4 mm de haut, 0,45 mm de jeu par côté), il se pose sur le disque d'acier. Pas de bonnette sur lui : elle est collée au capot avant.
7. Le capot avant, garni de son manchon de mousse et de la bonnette collée sur les bords de la découpe du manchon, se plaque sur la coque : la languette entre dans la rainure et écrase le joint. La bonnette vient alors à 0,5 mm au-dessus de la grille.
8. Le col de 14 mm se pose dans son logement. Le coussin, voile de tissu découpé, se colle autour sur son appui par un anneau continu de ruban double face : le ruban le tient et ferme le jour.

Au quotidien, seul le capot avant s'ouvre : on le tire (la bonnette part avec lui), on pince le micro par deux faces opposées, libres sur 9.5 mm au-dessus des butées, on le sort tout droit, on le recharge, on le repose entre les butées, on referme.

## Découper la mousse

Trois pièces seulement, dans deux plaques de mousse polyuréthane à cellules ouvertes du commerce. Fichiers dans `cad/out/v3-galet/foam/` : un gabarit imprimable par pièce (`gabarit-*.stl`, plaque de 1,2 mm, nom gravé, à imprimer à plat sans support) et le même contour à l'échelle 1 (`contour-*.svg`, avec une barre de 50 mm à vérifier à la règle après impression papier). Régénération : `cad/guarded.sh -m 6 -t 600 .venv/bin/python cad/foam_templates.py`.

| Ordre | Pièce | Plaque | Quantité | Contour |
|---|---|---|---|---|
| 1 | Fond | 10 mm | 2 | ellipse 60 × 42 mm, une encoche droite à 6 h |
| 2 | Manchon avant | 10 mm | 1 | bande développée : secteur d'anneau de rayons 60 et 77 mm, 175°, 8 encoches de 6 × 11 mm côté joint |
| 3 | Bonnette | 5 mm | 1 | rectangle 32,6 × 32,0 mm |

1. Poser le gabarit sur la plaque, le tenir à plat d'une main.
2. Couper au cutter à lame neuve de 18 mm, lame verticale, en plusieurs passes légères le long du gabarit. Les encoches d'abord, le contour ensuite.
3. Fond : couper deux fois le même contour. Manchon : le rayon intérieur (bord court, côté encoches) va vers le plan de joint ; les deux extrémités de la bande viennent de part et d'autre du micro. Bonnette : la coller par ses bords sur ceux de la découpe du manchon, juste sous l'ouverture du col.

Volumes découpés : fond 35,3 cm³, manchon 24,0 cm³, bonnette 5,2 cm³. Sous la bride du col, il ne reste que 2,44 mm au-dessus de la grille (22 % de sa surface) : la bonnette de 5 mm s'y écrase. Ailleurs, sous l'ouverture du col, elle garde ses 5 mm.

Abandonnés par rapport à la version précédente, pour couper moins de pièces : la mousse des flancs arrière (6 encoches, 7 morceaux) et la couche du chanfrein du joint (8 encoches). Au modèle acoustique, retirer 9 cm³ de mousse coûte moins de 0,1 dB(A). Le manchon passe en revanche à une bande d'épaisseur constante de 10 mm (le passage d'air libre reste au-dessus de 1 200 mm²).

## À acheter

| Article | Spécification | Quantité |
|---|---|---|
| Aimants néodyme | disque 6 × 2 mm | 12 |
| Pastilles d'acier | disque 6 × 2 mm, ou 12 aimants de plus en respectant la polarité | 12 |
| Bande de mousse autocollante | cellules fermées, 3 mm de large, 2 mm d'épaisseur | 25 cm |
| Mousse acoustique | polyuréthane à cellules ouvertes, plaques de 10 mm et de 5 mm | une plaque A4 de chaque |
| Ruban double face | mousse fine d'environ 1 mm, 10 à 12 mm de large | 40 cm par coussin |
| PETG translucide | naturel ou transparent | 5 g |
| Colle | cyanoacrylate | |

La plaque de 10 mm donne les deux couches du fond et le manchon avant, la plaque de 5 mm la bonnette (voir « Découper la mousse »).

Déjà en main : coussin Brainwavz 110 × 90 × 30, disque d'acier de 30 mm, DJI Mic Mini 2, PLA noir mat.

Pour la lumière, plus tard : batterie LiPo 502030 avec protection (5 × 20 × 30 mm), chargeur TP4056 USB-C (17,5 × 28 mm), interrupteur à glissière 8,6 × 3,6 × 3,5 mm, filament LED souple 3 V, fil fin.

## Revue Onshape

Le 20 novembre 2026, l'assemblage `silent-mic-v3-galet-technical.step` a été importé dans le document Onshape « Silent Mic - Référence », puis remplacé le soir même par le modèle corrigé (clic droit sur l'onglet du fichier dans le dossier « Imports CAD », « Update »). Le volume d'air y passe de 13 corps séparés à 9 : fentes, conduit et chambre communiquent maintenant.

La détection d'interférences d'Onshape ne trouve aucune collision entre les 5 pièces imprimées. Onshape affiche cependant « Some interferences may be missing » à chaque passe, même sur deux pièces : son contrôle n'est donc pas une preuve complète. Les preuves principales restent les contrôles du script (`metrics.json` : aucune interférence, jeux chiffrés) et le contrôle d'étanchéité.

Onshape ne voit pas ce que les contrôles ci-dessus ont trouvé : des pièces qui ne se touchent pas peuvent quand même avoir un passage fermé.

## Points ouverts

- **Baie de l'électronique dessinée sur des cotes de catalogue.** Le chargeur est compté à 4 mm d'épaisseur avec sa prise, la batterie à 30 mm de long avec sa carte de protection. Décision de Clément du 20 novembre 2026 : l'électronique se commande plus tard, la coque arrière s'imprime telle quelle et se réimprime (4 h 42, 72 g) si une pièce ne rentre pas.
- **Aucun clip dans la baie.** Les composants tiennent par empilement, logements ajustés à 0,5 mm et trappe. Aucune cloison imprimée entre chargeur et batterie.
- **Longueur du filament LED non choisie.** Le tour de la rainure fait environ 21 cm.
- **Levier de l'interrupteur** accessible par une fente de 4 × 2,2 mm sous la coque : à valider au doigt.
- **Tenue des aimants contre le joint** : c'est l'objet des éprouvettes de joint.
- **Accroche du coussin : ruban double face.** Décision de Clément du 20 novembre 2026. Le scratch du prototype v2 laisse un jour tout autour (calcul : de -3 à 11 dB(A) au lieu de 21). La lèvre élastique du coussin sur une gorge de la coque est réservée à une version de production : même étanchéité attendue, coussin plus simple à changer, mais gorge à ajuster au millimètre.
- **Fentes de sortie** : passage de 1,7 mm imprimé en surplomb à 38°, sans support. À contrôler au souffle sur la pièce (voir « Contrôles avant impression »).
- **Plafond de la baie** : pont d'environ 21 mm sans support, caché par la trappe.
- **Dessous du coussin** : seulement posé sur l'appui, étanche par la pression de la main. Une fente de 0,5 mm sur 3 cm fait tomber l'atténuation calculée de 21 à 12 dB(A). Un anneau de ruban double face est en réserve, à trancher au test du capot (`bench/README.md`, étape 6).
