# Silent Mic v3 galet : impression et montage

État au 20 novembre 2026. Rien n'est encore imprimé : temps et masses viennent du tranchage OrcaSlicer, le montage vient de la CAO (`cad/silent_mic_v3_galet.py`, aucune interférence détectée).

## Impression

Bambu Lab A1 mini, buse 0,4 mm, couches de 0,20 mm, 4 périmètres, 20 % de remplissage, supports automatiques avec « ne pas supporter les ponts ». PLA noir mat, sauf l'anneau et l'éprouvette de lumière en PETG translucide. Fichiers dans `cad/out/v3-galet/`.

| Ordre | Pièce | Fichier | Temps | Filament |
|---|---|---|---|---|
| 1 | Capot d'essai | `coupons/pad-test-cap.stl` | 3 h 22 | 62 g |
| 1 | Cols de 3, 10 et 16 mm | `coupons/collar-insert-*.stl` | 20, 29 et 36 min | 20 g |
| 2 | Éprouvettes de joint | `coupons/joint-coupon-front.stl`, `-rear.stl` | 22 min chacune | |
| 2 | Éprouvette de lumière (PETG) | `coupons/light-coupon-petg.stl` | 17 min | |
| 3 | Capot avant, appui du coussin sur le plateau | `silent-mic-v3-galet-front.stl` | 2 h 53 | 46 g |
| 3 | Coque arrière, face arrière sur le plateau | `silent-mic-v3-galet-rear.stl` | 4 h 44 | 70 g |
| 3 | Trappe, col de 14 mm, anneau (PETG) | `-cover.stl`, `-collar-insert-14mm.stl`, `-ring.stl` | 32, 33 et 21 min | 17 g |

Le corps (ordre 3) ne s'imprime qu'après le test des cols (`bench/README.md`) et l'essai des éprouvettes de joint. Les seuls supports du corps sont dans la baie de la coque arrière, cachée par la trappe.

## Montage

Trois coques s'empilent le long de l'axe, sans aucune vis : trappe, coque arrière, capot avant. Tout entre par deux ouvertures. La vue « Montage » de la visionneuse montre les étapes.

**Une fois, à la colle cyanoacrylate**

- 8 aimants 6 × 2 dans les bossages du bord de la coque arrière, 8 pastilles d'acier en face dans le capot avant.
- 4 aimants dans le dos de la coque arrière. Ils dépassent de 0,9 mm et centrent la trappe. 4 pastilles dans la trappe.
- Le disque d'acier de 30 mm sur la tête du pied du micro.
- La bande de mousse 3 × 2 au fond de la rainure du capot avant.

**Par l'arrière, la baie (hors du volume acoustique)**

1. La batterie au fond, le chargeur par-dessus avec sa prise USB-C vers le bas, l'interrupteur à côté. Un ruban isolant entre le chargeur et la batterie, un point de mousse double face pour caler.
2. Les deux fils du ruban LED montent par un tunnel de 2,6 mm jusqu'au bord de la coque, sans traverser la chambre.
3. La trappe se pose, tenue par ses 4 aimants.

**Par l'avant, le plan de joint (au niveau de l'anneau lumineux)**

4. Le disque de mousse de 20 mm au fond, passé autour du pied du micro, puis la mousse des flancs.
5. Le ruban LED dans sa rainure, l'anneau translucide par-dessus.
6. Le micro sur son pied : il tient par son aimant. Sa bonnette de mousse par-dessus.
7. Le capot avant, garni de son manchon de mousse, se plaque sur la coque : la languette entre dans la rainure et écrase le joint.
8. Le col de 14 mm se pose dans son logement, le coussin s'enfile dessus et le tient. Le voile de tissu du coussin est découpé avant.

Au quotidien, seul le capot avant s'ouvre : on le tire, on prend le micro pour le recharger, on referme.

## À acheter

| Article | Spécification | Quantité |
|---|---|---|
| Aimants néodyme | disque 6 × 2 mm | 12 |
| Pastilles d'acier | disque 6 × 2 mm, ou 12 aimants de plus en respectant la polarité | 12 |
| Bande de mousse autocollante | cellules fermées, 3 mm de large, 2 mm d'épaisseur | 25 cm |
| Mousse acoustique | polyuréthane à cellules ouvertes, plaques de 10 mm et de 5 mm | une plaque A4 de chaque |
| PETG translucide | naturel ou transparent | 5 g |
| Colle | cyanoacrylate | |

La mousse de 10 mm fait le disque du fond (deux couches) et le manchon avant. Les flancs arrière sont prévus à 8 mm : 5 mm à défaut. La bonnette prend la plaque de 5 mm.

Déjà en main : coussin Brainwavz 110 × 90 × 30, disque d'acier de 30 mm, DJI Mic Mini 2, PLA noir mat.

Pour la lumière, plus tard : batterie LiPo 502030 avec protection (5 × 20 × 30 mm), chargeur TP4056 USB-C (17,5 × 28 mm), interrupteur à glissière 8,6 × 3,6 × 3,5 mm, filament LED souple 3 V, fil fin.

## Points ouverts

- **Baie de l'électronique dessinée sur des cotes de catalogue.** Le chargeur est compté à 4 mm d'épaisseur avec sa prise, la batterie à 30 mm de long avec sa carte de protection. Décision de Clément du 20 novembre 2026 : l'électronique se commande plus tard, la coque arrière s'imprime telle quelle et se réimprime (4 h 44, 70 g) si une pièce ne rentre pas.
- **Aucun clip dans la baie.** Les composants tiennent par empilement, logements ajustés à 0,5 mm et trappe. Aucune cloison imprimée entre chargeur et batterie.
- **Longueur du filament LED non choisie.** Le tour de la rainure fait environ 21 cm.
- **Levier de l'interrupteur** accessible par une fente de 4 × 2,2 mm sous la coque : à valider au doigt.
- **Tenue des aimants contre le joint** : c'est l'objet des éprouvettes de joint.
- **Dessous du coussin** : seulement posé sur l'appui, étanche par la pression de la main. Une fente de 0,5 mm sur 3 cm fait tomber l'atténuation calculée de 21 à 12 dB(A). Un anneau de ruban double face est en réserve, à trancher au test du capot (`bench/README.md`, étape 6).
