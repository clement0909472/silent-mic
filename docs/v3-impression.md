# Silent Mic v3 galet : impression et montage

État au 23 novembre 2026. Rien n'est encore imprimé : temps et masses viennent du tranchage Bambu Studio, le montage vient de la CAO (`cad/silent_mic_v3_galet.py`).

> **Assemblage vissé depuis le 23 novembre 2026.** Décision de Clément : tout ce qui ne s'ouvre pas au quotidien se visse, pour tenir, pour fermer le joint à coup sûr et pour qu'on ne démonte pas l'appareil par mégarde. Le capot avant se serre sur la coque par 4 vis M3 fraisées à écrous prisonniers (mêmes cotes que le v2), la trappe par 2 vis. Seul le micro tient par son aimant : il entre et sort par la bouche, capot en place. Les 12 aimants et 12 pastilles du joint et de la trappe disparaissent.
>
> **Appui visage à réviser avant toute impression (23 novembre 2026).** Clément a essayé sa bouche sur le v2 imprimé : ses lèvres descendent un peu plus bas que le fond du coussin. Trois écarts du v3 par rapport au v2 (`cad/whisper_mask_v0.py`) en découlent, non vus jusque-là :
> 1. **Assise du coussin plate.** Le v2 la creuse en cylindre de 105 mm de rayon (`FACE_RADIUS`) : ses côtés avancent vers les joues de 10 mm au milieu du coussin et de 15,6 mm à son bord. Le v3 l'a aplatie pour imprimer le capot avant appui sur le plateau.
> 2. **Règle de distance au visage abandonnée.** Le v2 exige 8 mm d'air entre le fond du coussin et le devant du micro (`AIR_GAP_TARGET`), c'est-à-dire qu'il suppose le visage au fond du coussin. Le v3 supposait les lèvres à 20 mm au-dessus de l'appui (`MOUTH_ABOVE_SEAT`). Avec la bonnette, le haut des poils est 5,5 mm au-dessus du fond du coussin : contact certain.
> 3. **Col rigide de 14 mm** là où le v2 n'a qu'un rebord de 3 mm : il appuierait sur le visage avant que le coussin soit écrasé comme sur le v2.
>
> Ne pas imprimer `print/capot-essai.3mf` ni les cols de `print/cols-et-joint.3mf` en l'état. Pistes : assise courbe rapportée sur le capot, col ramené sous l'épaisseur du coussin écrasé, micro couché sous sa bonnette.

> **Support du micro repris le 21 novembre 2026.** Le micro est debout contre une plaque dressée au centre du fond, comme sur le v2, haut du boîtier vers la bouche, bonnette DJI en place (décision de Clément). Le capot avant se pose droit, et le micro coiffé de sa bonnette passe droit par la bouche (contrôlé dans la CAO, sur les fichiers d'impression et dans Onshape). Une seconde relecture indépendante a confirmé le démontage et l'étanchéité, et fait abaisser la plaque sous la bonnette. Clément a confirmé le 21 novembre 2026 que la jupe de sa bonnette DJI descend de moins de 9 mm sur le dos du micro et qu'elle est très molle : elle s'écrase au besoin. L'ancien pied, près de la paroi basse, bloquait le capot : voir « Relecture indépendante du 21 novembre 2026 ».

## Impression

Bambu Lab A1 mini, buse 0,4 mm, couches de 0,20 mm, 4 périmètres, 20 % de remplissage, couture alignée, plaque PEI texturée. PLA : préréglage « ELEGOO PLA Mat Flow Rate Calibrated » de Clément (débit 1,029, densité 1,32). PETG : « Bambu PETG Translucent @BBL A1M ». Fichiers dans `cad/out/v3-galet/`.

> **Projets 3MF refaits le 23 novembre 2026.** Jusque-là, `cad/bambu_3mf.sh` passait à la ligne de commande les préréglages système de la machine et du procédé sans leur chaîne d'héritage. Les fichiers embarquaient donc une configuration générique : G-code de démarrage réduit à un retour à l'origine (sans la séquence de l'A1 mini : chauffe, nivellement, purge), parois à 60 mm/s, accélérations de 500 mm/s². Et à l'ouverture dans Bambu Studio, l'interface rechargeait le procédé standard en ignorant les 4 parois, les 20 % de remplissage et les supports. Les deux défauts sont corrigés : préréglages aplatis avec tout leur héritage, et écarts au procédé système inscrits dans le projet comme le fait l'interface. Les temps ci-dessous sont ceux du vrai profil A1 mini.

### Pièces d'essai : projets Bambu Studio prêts à imprimer

Dans `print/`, trois projets 3MF tranchés, réglages embarqués. Chaque plateau est d'abord tranché avec supports automatiques (« ne pas supporter les ponts ») pour voir ce que le trancheur réclame : rien pour le capot d'essai, les cols et la lumière ; un plot de 3 mm sous chacune des deux têtes de vis de l'éprouvette de joint avant, posé sur le plateau comme au corps. Ils se rouvrent et se retranchent à l'identique en ligne de commande. On les ouvre dans Bambu Studio (il affiche une fenêtre « Préréglage personnalisé » parce que le filament est le tien : valider), on vérifie dans l'onglet Supports que « Activer les supports » et « Sur plateau uniquement » sont cochés pour le plateau des éprouvettes et celui du capot avant, et « Boucles de paroi » à 4 dans l'onglet Résistance, puis on lance. Régénération : `cad/bambu_3mf.sh` (lit le préréglage de Clément sans le modifier).

| Plateau | Fichier | Contenu | Temps | Filament |
|---|---|---|---|---|
| 1 | `print/capot-essai.3mf` | capot d'essai du coussin | 1 h 51 | 70 g PLA |
| 2 | `print/cols-et-joint.3mf` | cols de 3, 10 et 16 mm, éprouvettes de joint avant et arrière (2 vis, 2 écrous) | 1 h 01 | 31 g PLA |
| 3 | `print/lumiere-petg.3mf` | éprouvette de lumière | 10 min | 1 g PETG |

Grammes calculés par Bambu Studio avec la densité réelle du filament (1,32) : le tableau OrcaSlicer précédent comptait 1,24, d'où environ 6 % de moins.

### Corps : projets Bambu Studio prêts

| Plateau | Fichier | Contenu | Temps | Filament |
|---|---|---|---|---|
| 4 | `print/corps-capot-avant.3mf` | capot avant, appui du coussin sur le plateau, 4 colonnes de support | 1 h 46 | 56 g PLA |
| 5 | `print/corps-coque-arriere.3mf` | coque arrière, face arrière sur le plateau | 2 h 27 | 78 g PLA |
| 6 | `print/corps-trappe-col.3mf` | trappe et col de 14 mm | 33 min | 17 g PLA |
| 7 | `print/corps-anneau-petg.3mf` | anneau lumineux | 11 min | 2 g PETG |

Mêmes réglages que les pièces d'essai. Le corps ne s'imprime qu'après le test des cols (`bench/README.md`) et l'essai des éprouvettes de joint. Régénération : `cad/bambu_3mf.sh corps`.

Supports, toujours réglés sur « Sur plateau uniquement » (rien dans une cavité fermée ni dans un logement d'écrou) :

- **Capot avant : une colonne dans chacun des 4 puits de vis**, debout sur le plateau dans l'ouverture du coussin, jusque sous la face du bossage (26 mm). Elle porte la première couche du pont qui ferme le bossage autour de la tête de vis. Elles se retirent à la main par l'ouverture.
- **Coque arrière : sous le passage de la prise USB-C**, dans la baie cachée par la trappe (de 0,2 à 10,4 mm de haut). En automatique, le trancheur en poserait aussi dans les fentes de sortie et sous les plafonds des logements d'écrou, où on ne pourrait pas les retirer.

Sans support, par dessin : le plafond de chaque logement d'écrou se ferme en trois couches de 0,2 mm (deux ponts droits de 5,8 mm qui laissent une fente, puis un carré, puis le trou rond), et les avant-trous de la trappe finissent en pointe.

## Contrôles avant impression

Sept contrôles tournent sur les fichiers produits eux-mêmes, pas sur l'intention du dessin.

- **Maillages fermés.** À l'export, chaque STL est nettoyé puis refusé si une arête n'est pas partagée par exactement deux faces (`clean_stl` dans `cad/silent_mic_v3_coupons.py`). OCCT laisse un triangle vide au sommet de chaque cône (aujourd'hui la pointe des avant-trous de la trappe).
- **Étanchéité.** `cad/leak_check.py` remet les STL en position de montage, les découpe en voxels de 0,25 mm et « inonde » l'air de la chambre. Résultat dans `cad/out/v3-galet/leak-check.json`.
- **Évent vu par l'acoustique.** Le même découpage sert à résoudre un écoulement d'air entre la chambre et l'extérieur, dans les pièces telles qu'elles s'impriment. Il en sort la conductivité de l'évent (une section divisée par une longueur), qui fixe sa masse acoustique, donc l'atténuation. Le contrôle échoue si elle s'écarte de plus de 5 % de celle que suppose le modèle acoustique (`acoustics/params.json`), ou le volume de la chambre de plus de 6 %.
- **Montage et sortie du micro.** `export()` translate le capot avant et la trappe le long de leur direction de pose, puis le micro coiffé de sa bonnette **par la bouche, capot et col en place** (tiré droit sur 60 mm, et décollé de 4 mm vers l'avant), et refuse le modèle si une pièce rencontre quoi que ce soit en chemin. `cad/leak_check.py` refait ce contrôle sur les fichiers d'impression, colonne par colonne : rien de ce qui reste en place ne doit se trouver au-dessus de la matière du capot.
- **Vis.** `export()` mesure la matière entre chaque perçage et ce qu'il ne doit pas crever : 7,1 mm jusqu'à l'extérieur et 1,9 mm jusqu'à la rainure du joint côté capot, 5,6 mm jusqu'à l'extérieur et 3,5 mm jusqu'au conduit côté coque, 5,2 mm entre les avant-trous de la trappe et la chambre. Il vérifie aussi qu'un tournevis du diamètre de la tête atteint chaque vis sans toucher ni le capot ni le manchon, et qu'une clé de 2 mm passe à travers le col en place.
- **STEP relisibles.** Chaque STEP est relu juste après son écriture et refusé s'il ne redonne pas les mêmes solides fermés (`export_step`). `cad/check_exports.py` refuse aussi un STEP sans solide.
- **Ouvertures mesurées dans la CAO.** `export()` mesure la section de l'entrée et des fentes là où elles percent les parois, et refuse un modèle où elles ne débouchent pas.

![Coupes du modèle : chambre, conduit, fentes, baie](img/v3-etancheite.png)

| Contrôle d'étanchéité | Résultat |
|---|---|
| La chambre rejoint l'extérieur par le conduit | oui |
| Fentes bouchées : la chambre est étanche | oui, donc aucune autre ouverture |
| Entrée bouchée : la chambre est étanche | oui, donc une seule entrée dans le conduit |
| Conduit bouché à midi : la chambre est étanche | oui, donc l'air fait le tour complet |
| Conduit bouché, matière non épaissie : la chambre est étanche | oui, donc aucun jeu de montage de plus de 0,25 mm ne relie la chambre à l'extérieur |
| Trou témoin de 1 mm² percé dans la paroi | détecté |
| Capot avant posé droit : surface accrochée | 0 mm² (110 mm² sur la version du 20 novembre, 155 avec le micro) |
| Conductivité de l'évent dans les pièces imprimées | 0,3038 mm pour 0,3035 au modèle (écart 0,1 %), soit un conduit de 48 mm² long de 158 mm ; chambre de 201 cm³ pour 194 au modèle ; résonance chambre + évent à 67 Hz |
| Fentes | 4, de 9,3 mm de long, passage réel de 1,7 mm, 62 mm² en tout |
| Entrée et section du conduit | 49 et 48 mm² |

Le contrôle suppose trois fermetures qu'il ne prouve pas : le joint mousse du plan de joint, le coussin collé sur son appui, le visage sur le coussin. La baie de l'électronique, la prise USB-C, la fente de l'interrupteur, le tunnel des fils et la rainure LED sont ouverts sur l'extérieur, mais séparés de la chambre par des parois pleines.

**Défauts trouvés et corrigés les 20 et 21 novembre 2026.**

- Les 4 fentes ne débouchaient pas dans le conduit (0,2 à 0,9 mm de plastique restaient au bout) et l'entrée du conduit était presque fermée côté chambre (peau de 0 à 0,5 mm). Fentes et entrée étaient posées sur la section du plan de joint, alors que conduit, gorge et chambre suivent la peau, qui s'affine vers l'arrière. Les sections annoncées venaient de formules, pas de la pièce.
- Les fentes étaient inclinées à 22° de la verticale : leur passage réel ne faisait que 0,9 mm, soit 38 mm² en tout, moins que le conduit (48 mm²). Elles sont à 38°, comme les autres surplombs internes : 1,7 mm et 62 mm². Au modèle acoustique : 21,2 dB(A) inchangés, 48 Pa à 0,2 L/s au lieu de 71 Pa.
- La quatrième fente dépassait au-dessus de la gorge, à moitié borgne. Les 4 fentes tiennent maintenant sous la gorge.
- Les logements des pastilles d'acier crevaient la peau de la trappe : 4 encoches visibles au dos. Les 4 aimants de la trappe sont déplacés entre la baie et le flanc de la trappe.
- Les STEP de la coque arrière, du capot avant et du volume d'air étaient défectueux : relus, ils n'étaient plus des solides (13 faces perdues sur la coque arrière, dont la gorge, les 4 fentes et l'entrée du conduit, 4 sur le capot avant). Onshape les importait en surfaces ouvertes, ce qui donnait l'impression de voir à travers sous l'anneau, et sa détection de collisions ne portait donc pas sur ces deux pièces. Les fichiers d'impression (STL, 3MF) n'étaient pas touchés. Ces trois STEP sont maintenant écrits en NURBS : mêmes surfaces, solides fermés à la relecture.
- Le pied du micro touchait le capot avant à 6 h (voir « Revue Onshape »). Ce pied a depuis disparu avec le support repris.
- **Le calcul acoustique ne lisait pas la pièce.** `acoustics/tmm.py` et la simulation openCFS calculent sur un équivalent (un volume, un conduit droit, des fentes) dont les cotes sont recopiées à la main dans `params.json`. Ils annonçaient donc 21 dB(A) pour un évent dessiné fermé. Fermé, le modèle donne d'ailleurs 24 dB(A), mieux qu'ouvert : le défaut n'était pas acoustique mais respiratoire, l'air expiré n'ayant aucune sortie, il aurait soulevé le coussin. Mesurée dans les pièces imprimées, la conductivité de l'évent vaut 0,3035 mm, 4 % de plus que ce que supposait le modèle. Le modèle est recalé dessus (longueur équivalente du conduit 146,5 mm au lieu de 152,6) : 21,15 dB(A) au lieu de 21,20, 47,5 Pa à 0,2 L/s. Aucune mesure réelle n'existe encore : ces dB restent une estimation jusqu'au banc.

### Relecture indépendante du 21 novembre 2026

Les fichiers d'impression ont été relus par un second agent, sans mes conclusions, avec ses propres outils. Il confirme l'étanchéité, la section du conduit et l'absence de collision au repos. Il a trouvé ce que mes contrôles ne cherchaient pas.

| Constat | Mesure | État |
|---|---|---|
| **Capot avant bloqué par le pied du micro** | micro jusqu'à y = -26,3 et tête du pied jusqu'à -27,8, pour une ouverture du capot à -22,3 ; levé de 2 mm, le capot recoupait la coque de 43 mm³, puis le micro jusqu'à 600 mm³ | corrigé : micro debout au centre, 5,5 mm de garde au capot, volume commun nul sur tout le retrait |
| Butées du nid du micro presque détachées | racine de 0,25 à 0,3 mm de large, départ en l'air sur une partie | corrigé : plus de butées, une plaque pleine de 28 × 4 mm |
| Languette trop juste dans sa rainure | 0,1 mm par côté sur tout le tour | corrigé : 0,2 mm par côté (languette de 2,8 mm dans une rainure de 3,2) |
| Anneau lumineux non tenu latéralement | seulement pincé entre les coques, épaisseur égale à sa feuillure | corrigé pour l'épaisseur (2,5 mm dans une feuillure de 2,6) ; pour le maintien, 4 points de colle au montage |
| Aimants pouvant s'enfoncer dans le toit conique des logements | 0,10 à 0,15 mm d'après la géométrie | sans objet depuis le 23 novembre : plus d'aimants au joint ni à la trappe |
| Parois de 0,6 à 0,7 mm entre logements de pastilles et rainure du capot | sur 2 mm de haut | sans objet depuis le 23 novembre : 1,9 mm entre les perçages des vis et la rainure |

### Seconde relecture indépendante, sur la version au micro debout

Même méthode, par un autre agent. Elle confirme, par ses propres mesures : capot, col, coussin et manchon tirés droit sans qu'aucune matière fixe se trouve au-dessus d'eux (balayage à 0,2 mm), jeu de languette de 0,19 à 0,21 mm sur tout le tour, chambre isolée de l'extérieur et de la baie quand l'entrée ou les fentes sont bouchées, conduit de 48,1 à 50,3 mm² sur tout le tour, cinq fichiers d'impression fermés.

| Constat | Mesure | État |
|---|---|---|
| **Plaque et disque dans la zone de la jupe de la bonnette** | plaque jusqu'à z = 17,0 et disque jusqu'à 17,5, pour un haut de micro à 16,5 : une bonnette qui coiffe le boîtier sur ses quatre faces ne pouvait pas se mettre | corrigé : plaque et disque arrêtés 9,5 mm sous le haut du micro ; micro et bonnette tirés droit ou décollés de 4 mm vers l'avant ne rencontrent rien ; 0,5 mm entre bonnette et plaque |
| Plafond de la baie plus long qu'annoncé | pont de 31 mm au plus court (36 × 31 mm, 837 mm²), annoncé à 21 | doc corrigée ; imprimé en pont sans support, vérifié sur les couches tranchées |
| Plaque du micro sollicitée à travers ses couches | 0,46 MPa par newton appliqué au centre du micro, angles vifs au pied | pied évasé de 2 mm par face sur 3 mm de haut, plaque raccourcie de 10 mm |
| Force du joint contre force des aimants | 0,55 mm d'écrasement sur 570 mm², 0,2 mm d'entrefer aux aimants | réglé le 23 novembre : 4 vis serrent le joint jusqu'en butée |
| Arêtes fines au bord des 4 fentes | moins de 0,8 mm sur 1,2 mm de haut | sans effet : le trancheur les supprime, ce qui élargit un peu les fentes |

Cette dernière retouche (plaque abaissée, pied évasé) n'a pas été relue par un troisième agent : elle est couverte par les contrôles automatiques et par Onshape.

Non retenus : le recouvrement du ruban LED et du manchon de mousse avec les coques vient des maillages grossiers de la visionneuse, les solides exacts ne se recoupent pas.

**À vérifier sur la pièce imprimée.** Souffler dans l'entrée du conduit (dans la paroi de la coque arrière, en bas à droite quand on la regarde de face) : l'air doit sortir par les 4 fentes, sous l'anneau. Une fente obstruée par un fil se dégage avec une lame fine.

### Troisième relecture indépendante, sur l'assemblage vissé (23 novembre 2026)

Même méthode : un agent sans accès à mes conclusions, sur les STL seuls. **Rien de bloquant.** Il confirme par ses propres mesures l'étanchéité (chambre isolée dès que l'entrée du conduit est bouchée, perçages des vis tous à l'intérieur de la chambre, 4,9 mm au moins jusqu'à l'extérieur), la pose droite du capot, la longueur des vis (la tige traverse tout l'écrou, 1 mm de marge au fond), le serrage en compression, et la sortie du micro par la bouche.

| Constat | Mesure | Suite |
|---|---|---|
| **Fraisures à 72° pour des vis à 90°** | pente 0,72 au capot et à la trappe : la tête ne portait que sur l'arête du haut | corrigé : fraisures à 90°, 3,7 mm de matière sous la tête au capot |
| Bord de la fraisure du capot imprimé en porte-à-faux | 0,3 à 1 mm au-dessus du puits | une colonne de support par puits porte la première couche ; la tête porte plus bas, sur le cône |
| Logement d'écrou juste en hauteur | 2,6 mm pour un écrou de 2,4, sous un plafond en pont | corrigé : 2,8 mm |
| Éprouvette de joint avant différente du vrai bossage | elle reproduit la vis, la fraisure, sa fermeture en trois couches et son support, pas les deux nervures de 1,3 mm ni le puits de 26 mm | laissé tel quel : ces deux points ne se jugeront que sur le capot |
| Éprouvette arrière pas posée à z = 0 | de -8 à +2 mm | corrigé |
| Outil pour rouvrir, coussin en place | tête à 56 mm sous le haut du coussin, qui passe à 5,8 mm de l'axe | noté au montage : tournevis six pans de 2 mm, lame de 60 mm au moins, tige de moins de 4,9 mm |
| Siège du col et dessous du coussin fermés par simple contact | entre z = 29,6 et 31 | déjà en point ouvert (ruban double face) |

## Montage

Trois coques s'empilent le long de l'axe : trappe, coque arrière, capot avant. Elles se vissent. Seul le micro reste amovible. La vue « Montage » de la visionneuse montre les étapes.

![Coupes du montage vissé : une vis du joint, les 4 écrous vus de face, la trappe](img/v3-vis.png)

**Où sont les vis, et pourquoi là**

- **Joint capot avant / coque arrière : 4 vis M3 × 10 fraisées**, à l'intérieur de la chambre, à 13 mm de la peau, deux en haut et deux en bas (rien à 6 h, où passent le barrage du conduit, l'entrée d'air et le tunnel des fils). Chaque vis traverse un bossage du capot et se prend dans un **écrou M3 prisonnier** glissé dans un bossage de la coque.
- **Rien ne traverse la paroi.** Vis, écrous et têtes sont tous à l'intérieur de la rainure du joint, donc dans le volume déjà fermé : le vissage n'ajoute aucun chemin de fuite, et aucune vis ne se voit de l'extérieur.
- **Aucune surépaisseur au plan de joint.** L'écrou est noyé 1,2 mm sous le plan de joint, la tête fraisée est au fond d'un puits. Les bossages se touchent face contre face en même temps que les bords des coques : c'est cette butée qui fixe l'écrasement du joint mousse à 0,55 mm, quel que soit le serrage.
- **Le serrage écrase, il n'arrache pas.** Tête et écrou pincent les deux bossages l'un contre l'autre. Aucun filet dans le plastique, donc on peut rouvrir autant de fois qu'on veut pendant la mise au point.
- **Trappe : 2 vis M3 × 10 fraisées** par le dos, têtes au fond de deux puits ronds, vissées dans des avant-trous de 2,7 mm de la coque. La baie est hors du volume acoustique et la trappe ne serre aucun joint : la vis taille son filet dans le PLA. Ce sont les deux seules vis visibles.

**Avant tout : retirer les supports du capot avant.** Il sort du plateau avec une colonne de support dans chacun des 4 puits de vis, debout dans l'ouverture du coussin. Elles se cassent à la main ou à la pince plate, puis on passe une vis dans chaque trou pour vérifier que la tête descend jusqu'à sa fraisure.

**Une fois, à la colle cyanoacrylate**

- Le disque d'acier de 30 mm sur la face avant de la plaque du micro, son bord haut au ras du haut de la plaque (il dépasse de 1 mm de chaque côté).
- L'anneau translucide sur le bord de la coque arrière, par 4 points de colle.
- La bande de mousse 3 × 2 au fond de la rainure du capot avant.

**Par l'arrière, la baie (hors du volume acoustique)**

1. La batterie au fond, le chargeur par-dessus avec sa prise USB-C vers le bas, l'interrupteur à côté. Un ruban isolant entre le chargeur et la batterie, un point de mousse double face pour caler.
2. Les deux fils du ruban LED montent par un tunnel de 2,6 mm jusqu'au bord de la coque, sans traverser la chambre.
3. La trappe se pose et se visse par ses 2 vis, sans forcer : dès que la tête touche le fond de sa fraisure, on s'arrête.

**Par l'avant, le plan de joint (au niveau de l'anneau lumineux)**

4. Les 4 écrous M3 dans leurs logements : chacun se glisse à plat dans la fente de son bossage, par le côté, un angle en avant, jusqu'à ce que son trou tombe en face de celui du bossage. Les fentes du haut s'ouvrent vers le bas, celles du bas vers le haut. Un point de colle sur une face de l'écrou si l'un d'eux retombe.
5. Les deux couches de mousse du fond (10 mm chacune), encoche vers le bas : la plaque du micro passe dans l'encoche. Le chanfrein sous le conduit les retient.
6. Le ruban LED dans sa rainure, derrière l'anneau translucide.
7. Le capot avant, garni de son manchon de mousse, se pose droit : la languette entre dans la rainure. Le col n'est pas encore en place.
8. Les 4 vis par l'ouverture de l'appui du coussin (77 × 57 mm), avec une clé six pans de 2 mm ou un tournevis à lame longue. Chaque tête descend dans son puits, entre les deux nervures de son bossage ; la mousse du manchon s'écarte au passage. Serrer en croix, en deux passes, jusqu'au contact : les bords des coques se touchent, il n'y a plus de jour au plan de joint.
9. Le col de 14 mm se pose dans son logement. Le coussin, voile de tissu découpé, se colle autour sur son appui par un anneau continu de ruban double face : le ruban le tient et ferme le jour.
10. Le micro, bonnette DJI en place, entre par la bouche, haut du boîtier vers soi, et se pose debout contre la plaque : son aimant le tient sur le disque d'acier, son bas arrive au ras de la mousse du fond.

Au quotidien, rien ne s'ouvre : on sort le micro par la bouche pour le recharger, on le remet de même. Son haut est à 28,3 mm sous le bord du col (11,8 mm d'après la CAO du v2) et le haut de la bonnette à 6,3 mm : on le tire par la bonnette, ou on le pince par ses petits côtés, qui gardent 15 mm libres de chaque côté jusqu'au bord du col.

**Pour rouvrir le corps** (mise au point, changement de mousse) : sortir le micro, desserrer les 4 vis avec une clé six pans de 2 mm passée par la bouche, col et coussin en place (1,2 mm de jeu entre la clé et le col ; avec le coussin, il faut un tournevis six pans de 2 mm à lame d'au moins 60 mm et à tige de moins de 4,9 mm, une clé coudée bute sur le coussin). Les vis restent dans leurs puits, le capot se lève droit. Pas besoin de décoller le coussin.

## Découper la mousse

Deux pièces seulement, dans une plaque de mousse polyuréthane à cellules ouvertes de 10 mm du commerce. Fichiers dans `cad/out/v3-galet/foam/` : un gabarit imprimable par pièce (`gabarit-*.stl`, plaque de 1,2 mm, nom gravé, à imprimer à plat sans support) et le même contour à l'échelle 1 (`contour-*.svg`, avec une barre de 50 mm à vérifier à la règle après impression papier). Régénération : `cad/guarded.sh -m 6 -t 600 .venv/bin/python cad/foam_templates.py`.

| Ordre | Pièce | Plaque | Quantité | Contour |
|---|---|---|---|---|
| 1 | Fond | 10 mm | 2 | ellipse 60 × 40 mm, une encoche droite à 6 h où passe la plaque du micro |
| 2 | Manchon avant | 10 mm | 1 | bande développée : secteur d'anneau de rayons 60 et 77 mm, 175°, 8 fentes de 2 × 14 mm côté joint, une par nervure des bossages de vis |

1. Poser le gabarit sur la plaque, le tenir à plat d'une main.
2. Couper au cutter à lame neuve de 18 mm, lame verticale, en plusieurs passes légères le long du gabarit. Les encoches d'abord, le contour ensuite.
3. Fond : couper deux fois le même contour. Manchon : le rayon intérieur (bord court, côté encoches) va vers le plan de joint ; les deux extrémités de la bande se rejoignent bout à bout en bas (6 h).

Volumes découpés : fond 31,8 cm³, manchon 33,2 cm³. Pas de bonnette en mousse : c'est celle du DJI, sur le micro.

Abandonnés par rapport à la version précédente, pour couper moins de pièces : la mousse des flancs arrière (6 encoches, 7 morceaux) et la couche du chanfrein du joint (8 encoches). Au modèle acoustique, retirer 9 cm³ de mousse coûte moins de 0,1 dB(A). Le manchon passe en revanche à une bande d'épaisseur constante de 10 mm (le passage d'air libre autour du micro reste de 1368 mm², plus de 20 fois la section du conduit).

## À acheter

| Article | Spécification | Quantité |
|---|---|---|
| Vis M3 × 10 mm à tête fraisée | acier noir, six pans creux de 2 mm (DIN 7991 / ISO 10642) | 6 |
| Écrous M3 | hexagonaux standard, 5,5 mm sur plats, 2,4 mm d'épaisseur (DIN 934) | 4 |
| Bande de mousse autocollante | cellules fermées, 3 mm de large, 2 mm d'épaisseur | 25 cm |
| Mousse acoustique | polyuréthane à cellules ouvertes, plaque de 10 mm | une plaque A4 |
| Ruban double face | mousse fine d'environ 1 mm, 10 à 12 mm de large | 40 cm par coussin |
| PETG translucide | naturel ou transparent | 5 g |
| Colle | cyanoacrylate | |

La plaque de 10 mm donne les deux couches du fond et le manchon avant (voir « Découper la mousse »).

Déjà en main : les 4 écrous M3 du v2 conviennent (pas ses vis M3 × 6, trop courtes), coussin Brainwavz 110 × 90 × 30, disque d'acier de 30 mm, DJI Mic Mini 2 et sa bonnette, PLA noir mat.

Pour la lumière, plus tard : batterie LiPo 502030 avec protection (5 × 20 × 30 mm), chargeur TP4056 USB-C (17,5 × 28 mm), interrupteur à glissière 8,6 × 3,6 × 3,5 mm, filament LED souple 3 V, fil fin.

## Revue Onshape

Le document Onshape « Silent Mic - Référence » contient l'assemblage `silent-mic-v3-galet-technical.step` (import du 20 novembre 2026, mis à jour le soir même par un clic droit sur l'onglet du fichier, « Update »).

Jusqu'au 20 novembre au soir, la coque arrière et le capot avant y étaient des « Composite parts » faits de 11 surfaces ouvertes, à cause du STEP défectueux décrit plus haut. Toute revue faite avant cette date sur ces deux pièces est sans valeur, y compris l'absence de collision annoncée alors.

Le 20 novembre au soir, après correction, Onshape importe 50 vraies pièces (aucun composite, aucune surface) et l'assemblage compte 20 instances sans erreur. Sa détection de collisions, enfin sur de vrais solides, a trouvé un contact : le cône du pied du micro touchait le coin intérieur de la bride du capot avant à 6 h, sur 2,8 mm de large et 0,1 mm de profondeur (0,03 mm³, sous le seuil de 0,1 mm³ que le script appliquait). Le pied est depuis dégagé de 0,85 mm, mesuré à l'export, et le seuil du script est descendu à 0,005 mm³. Ce pied a ensuite été remplacé par la plaque dressée du micro.

Le 21 novembre, la version au micro debout est rechargée (49 pièces, 20 instances sans erreur, micro et disque réinsérés). Détection de collisions sur la coque arrière, le capot avant, la trappe, l'anneau, le col, le micro, son disque et la bonnette, refaite après l'abaissement de la plaque : **aucune interférence**, sans avertissement d'Onshape.

Le 23 novembre, l'assemblage vissé est importé comme un assemblage neuf, « silent-mic-v3-galet-technical (1) » (l'ancien, mis à jour sur place, perdait les vis et les écrous, et les réinsérer à la main les plaçait mal). Détection de collisions sur la coque arrière, le capot avant, la trappe, l'anneau, le col, le micro, son disque, la bonnette, les 4 vis du joint, les 4 écrous et les 2 vis de trappe : **aucune interférence**. Ce contrôle porte sur la version aux fraisures à 72°.

**Depuis le 23 novembre, le contrôle se fait par l'API d'Onshape, sans interface** : `python3 cad/onshape_check.py` envoie le STEP d'assemblage dans le document, le fait traduire à plat dans un seul Part Studio, y lance un script FeatureScript (`evCollision`) et écrit `cad/out/v3-galet/onshape-check.json`. Il réutilise le même fichier et le même Part Studio à chaque fois, en deux minutes environ. La clé d'API est dans le trousseau macOS (`cad/onshape_key.sh save`), le document est noté dans un fichier local hors Git.

Résultat sur la version aux fraisures à 90° : 27 pièces, **aucun recouvrement entre pièces rigides** (coques, trappe, anneau, col, micro, disque, vis, écrous, électronique), 13 paires en simple contact. Un recouvrement est signalé entre la coque arrière et le fond de mousse : le fond est taillé sur la coque puis écrit en surfaces approchées, et la pointe des contreforts des bossages d'écrou y entre d'un millimètre. La mousse s'y écrase, rien à corriger.

Onshape ne voit pas les défauts de passage trouvés par le contrôle d'étanchéité : des pièces qui ne se touchent pas peuvent quand même avoir un évent fermé.

## Points ouverts

- **Baie de l'électronique dessinée sur des cotes de catalogue.** Le chargeur est compté à 4 mm d'épaisseur avec sa prise, la batterie à 30 mm de long avec sa carte de protection. Décision de Clément du 20 novembre 2026 : l'électronique se commande plus tard, la coque arrière s'imprime telle quelle et se réimprime (4 h 42, 72 g) si une pièce ne rentre pas.
- **Aucun clip dans la baie.** Les composants tiennent par empilement, logements ajustés à 0,5 mm et trappe. Aucune cloison imprimée entre chargeur et batterie.
- **Longueur du filament LED non choisie.** Le tour de la rainure fait environ 21 cm.
- **Levier de l'interrupteur** accessible par une fente de 4 × 2,2 mm sous la coque : à valider au doigt.
- **Vissage du joint à essayer sur les éprouvettes** (`print/cols-et-joint.3mf`) : l'écrou doit se glisser dans sa fente, la tête fraisée s'asseoir au fond de son puits, les deux moitiés se toucher sans jour une fois serrées. L'éprouvette arrière porte aussi, dessous, un avant-trou de 2,7 mm : y visser une M3 × 10 pour vérifier que le filet de la trappe prend sans fendre la pièce.
- **Micro plus profond que sur le v2** : 28,3 mm sous le bord du col contre 11,8 mm, parce que le col de 14 mm s'ajoute. Le passage est libre (contrôlé), mais la prise en main ne se juge que sur la pièce. Si elle est malcommode : col plus court (10 mm, déjà dans les pièces d'essai) ou plaque du micro plus haute.
- **Serrage des vis** : rien ne limite le couple à part la main. Bossage contre bossage, le serrage s'arrête net ; forcer au-delà peut fendre un bossage entre deux couches.
- **Accroche du coussin : ruban double face.** Décision de Clément du 20 novembre 2026. Le scratch du prototype v2 laisse un jour tout autour (calcul : de -3 à 11 dB(A) au lieu de 21). La lèvre élastique du coussin sur une gorge de la coque est réservée à une version de production : même étanchéité attendue, coussin plus simple à changer, mais gorge à ajuster au millimètre.
- **Bonnette DJI : hauteur mesurée, largeur et épaisseur encore estimées.** Clément a mesuré le 23 novembre 2026 environ 48 mm du bas du micro au haut des poils, soit 20 mm au-dessus du boîtier (28,04 mm). La CAO garde 22 mm, comme enveloppe prudente, pour un encombrement estimé de 36 × 26 mm et une jupe de 9 mm sur le haut du boîtier. Il reste 4,2 mm autour, jusqu'au capot et au col. Avec la cote mesurée, le haut des poils est à 8,3 mm sous le bord rigide du col (6,3 mm dans la CAO) et à 14,5 mm des lèvres supposées (12,5 mm dans la CAO). Sur le v2, sans col, le haut du micro était à 11,8 mm sous l'appui du coussin : les poils seraient montés à 8 mm au-dessus de l'appui (5,5 mm sur le v3), sans butée rigide entre eux et les lèvres. Sur le v3, pour toucher les poils, il faut écraser le coussin jusqu'au col et avancer les lèvres de plus de 8 mm dans son ouverture.
- **Micro couché : option pour une version plus courte (proposition de Clément, 23 novembre 2026), non dessinée.** Debout avec sa bonnette, le micro occupe 48 mm sur l'axe. Couché, il en occuperait environ 26 avec la bonnette et 13,5 sans. Le corps ne raccourcit pas pour autant sans perte : la profondeur sert d'abord au volume d'air. D'après le modèle 1D (estimation, non mesurée), la cavité de 194 cm³ donne 21,3 dB(A), 150 cm³ donnent 19,0, 135 cm³ donnent 18,0 et 120 cm³ donnent 17,0, soit environ 1 dB perdu par 5 à 6 mm de corps retirés (section de 30 à 45 cm² dans le capot avant), et le niveau au micro monte de 2 à 3 dB. À décider après la mesure du premier corps imprimé. La plaque laisse 9,5 mm libres au dos du micro, ce qui suffit d'après Clément (jupe de moins de 9 mm, très molle). Les cotes se règlent par `BONNET` dans `cad/silent_mic_v3_galet.py`.
- **Fentes de sortie** : passage de 1,7 mm imprimé en surplomb à 38°, sans support. À contrôler au souffle sur la pièce (voir « Contrôles avant impression »).
- **Plafond de la baie** : pont de 31 mm dans son sens le plus court (36 × 31 mm), imprimé sans support et caché par la trappe. Les seuls supports de la coque restent sous le passage de la prise USB-C. Un fléchissement de quelques dixièmes est possible : à mesurer sur la pièce avant de commander l'électronique.
- **Dessous du coussin** : seulement posé sur l'appui, étanche par la pression de la main. Une fente de 0,5 mm sur 3 cm fait tomber l'atténuation calculée de 21 à 12 dB(A). Un anneau de ruban double face est en réserve, à trancher au test du capot (`bench/README.md`, étape 6).
