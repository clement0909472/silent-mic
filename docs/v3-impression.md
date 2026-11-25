# Silent Mic v3 galet : impression et montage

État au 23 novembre 2026. Rien n'est encore imprimé : temps et masses viennent du tranchage Bambu Studio, le montage vient de la CAO (`cad/silent_mic_v3_galet.py`).

> **Assemblage vissé depuis le 23 novembre 2026.** Décision de Clément : tout ce qui ne s'ouvre pas au quotidien se visse, pour tenir, pour fermer le joint à coup sûr et pour qu'on ne démonte pas l'appareil par mégarde. Le capot avant se serre sur la coque par 4 vis M3 fraisées à écrous prisonniers (mêmes cotes que le v2), la trappe par 2 vis. Seul le micro tient par son aimant : il entre et sort par la bouche, capot en place. Les 12 aimants et 12 pastilles du joint et de la trappe disparaissent.
>
> **Appui visage révisé le 23 novembre 2026.** Clément a essayé sa bouche sur le v2 imprimé : coussin écrasé d'environ moitié (28 à 15 mm), ses lèvres descendent un peu sous le fond du coussin. Le v3 avait perdu trois choses du v2 (`cad/whisper_mask_v0.py`) : l'assise creusée qui fait épouser les joues au coussin, la règle des 8 mm d'air entre le fond du coussin et le micro, et un bord rigide plus bas. Corrigé ainsi :
> 1. **Assise courbe rapportée** (`cp.saddle_collar`) : une pièce posée à plat sur l'appui du capot avant et collée au ruban double face, comme le coussin. Son dessus est creusé en cylindre de 105 mm de rayon, comme le v2 : 4 mm d'épaisseur au centre, les côtés avancent vers les joues jusqu'à 13,8 mm de plus au bord. Le capot avant ne change pas.
> 2. **Col bombé d'une pièce avec l'assise** : sa crête suit la courbe, 10 mm au-dessus du fond du coussin au centre, là où est la bouche, et plus haut sur les côtés (idée de Clément). Essai de Clément du 24 nov. 2026 sur l'assise de 10 mm : taille juste, mais pas assez courbée et col trop bas. Variantes d'essai : col de 20 mm, rayons de 85 et 70 mm au lieu de 105. Sur la R85, Clément a relevé les bords par deux paires de cales de 12 mm, puis validé la courbure à l'essai (« c'est vraiment ce qu'on veut »). **Assise du corps depuis le 24 nov. 2026** (`cp.BODY_SEAT`, plateau `print/corps-assise.3mf`) : la même d'une pièce, dessus au rayon de 53 mm (bords 24 mm plus haut qu'avec la R85), col à 20 mm au-dessus de l'assise partout, qui remonte avec elle sur les côtés (demande de Clément). Les cales empilées finissaient en lame presque coupante : le dessus se prolonge en droite au-delà de 60° de pente et toute l'arête du haut du contour est arrondie de 2 mm (Clément voulait des bords bien arrondis dans l'épaisseur comme dans la largeur). La pointe culmine à 35,4 mm au lieu de 45,8 avec les cales ; c'est une lèvre ronde de 3,5 mm d'épais à 1 mm sous son sommet, 4,9 mm à 3 mm (2,1 et 2,9 mm avec un arrondi de 1 mm). La courbure est la même jusqu'à 46 mm du centre, donc sous toute la ligne d'appui du coussin (45 mm). Vu de face, le contour reste une ellipse : rayon de 28,5 mm aux pointes, aucun angle. La crête du col est un demi-rond complet sur ses 2 mm d'épaisseur. Même dos plat et même contour : elle se colle sur le capot sans rien y changer.
> 3. **Micro descendu de 20 mm, au fond de la chambre** : il tient sur son disque, 1 mm au-dessus des nervures du fond, et les deux couches de mousse sont entaillées autour de lui. Le disque d'acier de 30 mm se recoupe d'une bande de 10 mm en bas, toute sous le bas du micro : la surface sous l'aimant ne change pas. Avec la bonnette à la cote mesurée (48 mm du bas du micro au haut des poils), le haut des poils serait à 18 mm sous le fond du coussin au centre, à longueur égale. `export()` refuse le modèle sous 8 mm.
> 5. **Capot avant raccourci de 5 mm** (décision de Clément, meilleur compromis compacité / isolation) : le corps passe à 81 mm, 100,7 mm avec l'assise et le col (105,7 avant). La chambre perd 18 cm³ : 21,2 dB(A) au modèle 1D au lieu de 22,2 (estimation, non mesurée). Le haut des poils reste à 13 mm sous le fond du coussin, 5 mm de mieux que la règle du v2. Avec l'assise R53 du 24 nov. 2026, le corps garde 81 mm, mais ses bords montent : 120,8 mm aux pointes des joues (100,7 avant). Le col de 20 mm ajoute 22 cm³ à la chambre et ferme toute la paroi souple du coussin : 25,1 dB(A) au modèle 1D au lieu de 21,2 (estimation, non mesurée).
>
> 4. **Coussin aux cotes mesurées par Clément** (108 × 81 mm, ouverture 72,6 × 48,5, 28 mm d'épaisseur, contre 110 × 90 × 30 sur la fiche) : l'appui du capot passe de 104 × 84 à 104 × 77 mm, 2 mm sous le coussin de chaque côté, et le col suit la vraie ouverture (1 mm de jeu par côté, passage intérieur 66,6 × 42,5).
>
> Le micro couché, envisagé, ne passe pas : dans un sens, ses 48 mm de long heurtent les 4 bossages de vis du joint ; dans l'autre, il ne ressort plus par le col (42 mm de haut).

> **Support du micro repris le 21 novembre 2026.** Le micro est debout contre une plaque dressée au centre du fond, comme sur le v2, haut du boîtier vers la bouche, bonnette DJI en place (décision de Clément). Le capot avant se pose droit, et le micro coiffé de sa bonnette passe droit par la bouche (contrôlé dans la CAO, sur les fichiers d'impression et dans Onshape). Une seconde relecture indépendante a confirmé le démontage et l'étanchéité, et fait abaisser la plaque sous la bonnette. Clément a confirmé le 21 novembre 2026 que la jupe de sa bonnette DJI descend de moins de 9 mm sur le dos du micro et qu'elle est très molle : elle s'écrase au besoin. L'ancien pied, près de la paroi basse, bloquait le capot : voir « Relecture indépendante du 21 novembre 2026 ».

## Impression

Bambu Lab A1 mini, buse 0,4 mm, couches de 0,20 mm, 4 périmètres, 20 % de remplissage (100 %, en rectiligne, pour les pièces qui ferment la chambre du corps : assises, capot avant, coque arrière), couture alignée, plaque PEI texturée. PLA : préréglage « ELEGOO PLA Mat Flow Rate Calibrated » de Clément (débit 1,029, densité 1,32). PETG : « Bambu PETG Translucent @BBL A1M ». Fichiers dans `cad/out/v3-galet/`.

> **Pièces pleines depuis le 23 novembre 2026** (question de Clément sur les 20 %). Le modèle 1D ne voit pas d'effet de la paroi : 4 fois moins raide, l'isolation reste à 25,1 dB(A), et 10 fois moins raide elle ne perd que 0,4 dB(A) ; les fuites du joint et l'évent dominent (estimation, non mesurée). Les parois de 3 mm sortent de toute façon pleines (4 périmètres de chaque côté) : le remplissage ne change que les zones épaisses. Une pièce pleine coûte peu et retire ce doute : plus de vide entre les périmètres, plus de peau mince qui vibre. Depuis le 24 novembre, la trappe est pleine aussi : Clément veut le poids et la sensation d'un produit fini. Appareil complet d'environ 310 g en plein (pièces imprimées 268 g d'après le trancheur, composants environ 40 g), 220 g à 20 %. Les éprouvettes de joint et le capot d'essai gardent 20 % : ils servent à la forme.

> **Projets 3MF refaits le 23 novembre 2026.** Jusque-là, `cad/bambu_3mf.sh` passait à la ligne de commande les préréglages système de la machine et du procédé sans leur chaîne d'héritage. Les fichiers embarquaient donc une configuration générique : G-code de démarrage réduit à un retour à l'origine (sans la séquence de l'A1 mini : chauffe, nivellement, purge), parois à 60 mm/s, accélérations de 500 mm/s². Et à l'ouverture dans Bambu Studio, l'interface rechargeait le procédé standard en ignorant les 4 parois, les 20 % de remplissage et les supports. Les deux défauts sont corrigés : préréglages aplatis avec tout leur héritage, et écarts au procédé système inscrits dans le projet comme le fait l'interface. Les temps ci-dessous sont ceux du vrai profil A1 mini.

### Pièces d'essai : projets Bambu Studio prêts à imprimer

Dans `print/`, trois projets 3MF tranchés, réglages embarqués. Chaque plateau est d'abord tranché avec supports automatiques (« ne pas supporter les ponts ») pour voir ce que le trancheur réclame : rien pour le capot d'essai, les cols et la lumière ; un plot de 3 mm sous chacune des deux têtes de vis de l'éprouvette de joint avant, posé sur le plateau comme au corps. Ils se rouvrent et se retranchent à l'identique en ligne de commande. On les ouvre dans Bambu Studio (il affiche une fenêtre « Préréglage personnalisé » parce que le filament est le tien : valider), on vérifie dans l'onglet Supports que « Activer les supports » et « Sur plateau uniquement » sont cochés pour le plateau des éprouvettes et celui du capot avant, et « Boucles de paroi » à 4 dans l'onglet Résistance, puis on lance. Régénération : `cad/bambu_3mf.sh` (lit le préréglage de Clément sans le modifier).

| Plateau | Fichier | Contenu | Temps | Filament |
|---|---|---|---|---|
| 1 | `print/capot-essai.3mf` | capot d'essai du coussin et témoin de bonnette | 1 h 51 | 71 g PLA |
| 2 | `print/cols-et-joint.3mf` | assise courbe et col de 10 mm (celle du corps), éprouvettes de joint avant et arrière (2 vis, 2 écrous) ; assise pleine | 1 h 53 | 66 g PLA |
| 2 bis | `print/assises-20mm.3mf` | assises à col de 20 mm, plus courbées (rayons 85 et 70, gravés dessous), essai de forme à 20 % de remplissage : la retenue sera réimprimée pleine | 2 h 15 | 76 g PLA |
| 2 ter | `print/cales-assise.3mf` | deux cales posées sur l'assise R85 déjà imprimée, une de chaque côté sous le coussin : bord relevé de 12 mm (dessus au rayon 60, 3,9 mm contre le col, rien au centre), au lieu de réimprimer l'assise | 40 min | 12 g PLA |
| 2 quater | `print/cales-assise-2.3mf` | seconde paire de cales, posée sur la première : encore 12 mm au bord, 24 au total (dessus au rayon 53, 2,1 mm de plus contre le col, rien avant 27 mm du centre) | 36 min | 9 g PLA |
| 3 | `print/lumiere-petg.3mf` | éprouvette de lumière | 10 min | 1 g PETG |

L'assise se pose à plat sur le capot d'essai comme sur le corps : leurs appuis ont le même contour (104 × 77 mm, 2 mm sous le coussin de chaque côté). Elle s'imprime dos au plateau, sans support (contrôlé couche par couche). Sa hauteur de col est gravée dessous.

**Témoin de bonnette** (sur le plateau du capot d'essai, idée de Clément) : un plot ovale de 36 × 26 mm, haut de 19 mm, marqué « 13 ». Posé au fond du capot d'essai, centré sous le col, son dessus est exactement où sera le haut de la bonnette dans le corps : 13 mm sous le fond du coussin. Assise et coussin en place, appuyer le visage comme pour parler. Si les lèvres touchent le plot, elles toucheraient la bonnette. Pour mesurer la marge, glisser des cales dessous (pièces de monnaie, rondelles) jusqu'au contact : leur épaisseur est la marge. `export()` refuse le corps si sa marge s'écarte du témoin.

Grammes calculés par Bambu Studio avec la densité réelle du filament (1,32) : le tableau OrcaSlicer précédent comptait 1,24, d'où environ 6 % de moins.

### Corps : un seul projet pour la vague d'impression

`print/silent-mic-corps.3mf` (demande de Clément, 24 nov. 2026) : un projet Bambu Studio, un plateau par impression, dans l'ordre. Les réglages de chaque pièce y sont déjà, par objet : pleine, supports sur plateau seulement pour la coque et le capot. Rien à cocher ni décocher : « Imprimer plateau » n'imprime que la plaque affichée. Régénération et preuve : `python3 cad/bambu_projet.py`, qui retranche le projet en entier et exige que chaque plateau redonne la durée et la masse de son projet d'une pièce (vérifié le 24 nov. 2026 ; coque arrière refaite le 25 nov. 2026 au matin, baie sans fuite de lumière : plaque 1 en 3 h 13, 108,09 g, projet à rouvrir dans l'interface).

| Plaque | Pièce | Temps | Filament |
|---|---|---|---|
| 1 | coque arrière (supports sous le passage de la prise USB-C, dans la baie) | 3 h 17 | 111 g PLA noir |
| 2 | capot avant (une colonne de support sous chaque puits de vis) | 1 h 52 | 56 g PLA noir |
| 3 | trappe | 28 min | 16 g PLA noir |
| 4 | anneau de la V0, en noir avec la même bobine (la version lumineuse s'imprime en PETG translucide avec `print/corps-anneau-petg.3mf`) | 9 min | 2 g PLA noir |

L'anneau est en filament 1, comme le reste : on change de bobine avant la plaque 4 (la ligne de commande de Bambu Studio 2.9 plante quand un projet mélange deux filaments). Seules pièces imprimées du corps : ces quatre plaques et l'assise, déjà imprimée le 24 novembre ; tout le reste de la vue « Montage » s'achète ou se découpe (micro, disque, coussin, mousses, joint, filament LED, électronique, vis et écrous).

Orientations vérifiées le 24 nov. 2026 en tranchant chaque coque dans les deux sens. Capot avant, appui du coussin sur le plateau : 4 colonnes de support dans les puits de vis, 3 g et 10 min ; retourné, face de joint au plateau, le trancheur réclame environ 1 500 blocs de support dans la chambre, impossibles à retirer, ou laisse les surplombs intérieurs dans le vide. Coque arrière, dos au plateau : 0,3 g de support sous le passage de la prise USB-C ; retournée, 9 à 11 g de plus et 26 min de plus.

Pour lancer une plaque :
1. Imprimante allumée, plateau propre, au moins 110 g de filament noir sur la bobine pour la plaque 1.
2. Bambu Studio : Fichier > Ouvrir projet > `print/silent-mic-corps.3mf`. S'il demande d'enregistrer le projet précédent : « Non ». Avertissement d'imprimante non connectée : « Plus tard ».
3. Onglet Aperçu, cliquer la vignette de la plaque à gauche (1, 2 ou 3), puis « Trancher le plateau » en haut à droite. Vérifier la durée et la masse du tableau.
4. « Imprimer plateau » (pas « Imprimer tout »), puis « Envoyer ».

### Corps : projets Bambu Studio prêts

| Plateau | Fichier | Contenu | Temps | Filament |
|---|---|---|---|---|
| 4 | `print/corps-capot-avant.3mf` | capot avant, appui du coussin sur le plateau, 4 colonnes de support, plein | 1 h 52 | 56 g PLA |
| 5 | `print/corps-coque-arriere.3mf` | coque arrière, face arrière sur le plateau, pleine | 3 h 13 | 108 g PLA |
| 5 bis | `print/corps-assise.3mf` | assise du corps (R53, col de 20 mm, gravée « 20 R53 » dessous), dos au plateau, sans support, pleine | 2 h 17 | 87 g PLA |
| 6 | `print/corps-trappe.3mf` | trappe, pleine | 29 min | 16 g PLA |
| 7 | `print/corps-anneau-petg.3mf` | anneau lumineux | 11 min | 2 g PETG |

Mêmes réglages que les pièces d'essai. Le corps ne s'imprime qu'après le test de l'assise sur le capot d'essai (`bench/README.md`) et l'essai des éprouvettes de joint. Régénération : `cad/bambu_3mf.sh corps`.

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
- **Ouvertures mesurées dans la CAO.** `export()` mesure la section de l'entrée et de la sortie là où elles percent les parois, et refuse un modèle où elles ne débouchent pas, une sortie de moins de 100 mm² en section droite, ou une paroi de moins de 3 mm entre l'évent et la chambre du micro.

![Coupes du modèle : chambre, conduit, sortie, baie](img/v3-etancheite.png)

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
| Fentes | 4, de 9,3 mm de long, horizontales depuis le 25 nov. 2026 : passage de 2,75 mm, 102 mm² en tout (62 mm² quand elles étaient inclinées) |
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
| Anneau lumineux non tenu latéralement | seulement pincé entre les coques, épaisseur égale à sa feuillure | corrigé : 2,5 mm de profondeur dans une feuillure de 2,6 ; depuis le 25 nov. 2026, plaqué contre le capot par 8 plots écrasés de 0,2 mm au fond de la feuillure, sans colle et démontable |
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

**À vérifier sur la pièce imprimée.** Souffler dans l'entrée du conduit (dans la paroi de la coque arrière, en bas à droite quand on la regarde de face) : l'air doit sortir par les 4 ouvertures en pente, sous le conduit, côté dos. Une ouverture obstruée par un fil se dégage avec une lame fine.

### Troisième relecture indépendante, sur l'assemblage vissé (23 novembre 2026)

Même méthode : un agent sans accès à mes conclusions, sur les STL seuls. **Rien de bloquant.** Il confirme par ses propres mesures l'étanchéité (chambre isolée dès que l'entrée du conduit est bouchée, perçages des vis tous à l'intérieur de la chambre, 4,9 mm au moins jusqu'à l'extérieur), la pose droite du capot, la longueur des vis (la tige traverse tout l'écrou, 1 mm de marge au fond), le serrage en compression, et la sortie du micro par la bouche.

| Constat | Mesure | Suite |
|---|---|---|
| **Fraisures à 72° pour des vis à 90°** | pente 0,72 au capot et à la trappe : la tête ne portait que sur l'arête du haut | corrigé : fraisures à 90°, 3,7 mm de matière sous la tête au capot |
| Bord de la fraisure du capot imprimé en porte-à-faux | 0,3 à 1 mm au-dessus du puits | une colonne de support par puits porte la première couche ; la tête porte plus bas, sur le cône |
| Logement d'écrou juste en hauteur | 2,6 mm pour un écrou de 2,4, sous un plafond en pont | corrigé : 2,8 mm |
| Éprouvette de joint avant différente du vrai bossage | elle reproduit la vis, la fraisure, sa fermeture en trois couches et son support, pas les deux nervures de 1,3 mm ni le puits de 26 mm | laissé tel quel : ces deux points ne se jugeront que sur le capot |
| Éprouvette arrière pas posée à z = 0 | de -8 à +2 mm | corrigé |
| Outil pour rouvrir, coussin en place | tête à 56 mm sous le haut du coussin (58 avec l'assise R53 du 24 nov. 2026), qui passe à 5,8 mm de l'axe | noté au montage : tournevis six pans de 2 mm, lame de 75 mm conseillée (60 au moins), tige de moins de 4,9 mm |
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

- Le disque d'acier de 30 mm, **recoupé d'abord à la cisaille** : retirer une bande de 10 mm (corde de 24 mm) d'un côté, pour qu'il descende jusqu'au fond sans y buter. Il se colle sur la face avant de la plaque du micro, bord droit en bas, bord rond au ras du haut de la plaque (il dépasse de 1 mm de chaque côté).
- L'anneau dans sa feuillure, sur le bord de la coque arrière, plots vers le bas, sans colle : le capot le plaque en se fermant et les 8 plots s'écrasent de 0,2 mm. Pas de jour au ras du capot, donc ni ligne visible ni lumière directe. Pour le retirer, ôter le capot et le soulever.
- La bande de mousse 3 × 2 au fond de la rainure du capot avant.

**Par l'arrière, la baie (hors du volume acoustique)**

1. La batterie au fond, le chargeur par-dessus avec sa prise USB-C vers le bas, l'interrupteur à côté. Un ruban isolant entre le chargeur et la batterie, un point de mousse double face pour caler.
2. Les deux fils du ruban LED montent par un tunnel de 2,6 mm jusqu'au bord de la coque, sans traverser la chambre.
3. La trappe se pose et se visse par ses 2 vis, sans forcer : dès que la tête touche le fond de sa fraisure, on s'arrête.

**Par l'avant, le plan de joint (au niveau de l'anneau lumineux)**

4. Les 4 écrous M3 dans leurs logements : chacun se glisse à plat dans la fente de son bossage, par le côté, un angle en avant, jusqu'à ce que son trou tombe en face de celui du bossage. Les fentes du haut s'ouvrent vers le bas, celles du bas vers le haut. Un point de colle sur une face de l'écrou si l'un d'eux retombe.
5. Les deux couches de mousse du fond (10 mm chacune, identiques), encoche vers le bas : la plaque du micro et le micro lui-même passent dans l'encoche. Le chanfrein sous le conduit les retient.
6. Le ruban LED dans sa rainure, derrière l'anneau translucide.
7. Le capot avant, garni de son manchon de mousse, se pose droit : la languette entre dans la rainure. Le col n'est pas encore en place.
8. Les 4 vis par l'ouverture de l'appui du coussin (77 × 57 mm), avec une clé six pans de 2 mm ou un tournevis à lame longue. Chaque tête descend dans son puits, entre les deux nervures de son bossage ; la mousse du manchon s'écarte au passage. Serrer en croix, en deux passes, jusqu'au contact : les bords des coques se touchent, il n'y a plus de jour au plan de joint.
9. L'assise courbe (R53, col de 20 mm) se colle sur l'appui du capot par un anneau continu de ruban double face, contour aligné sur celui du capot. Le coussin, voile de tissu découpé, se colle de même sur l'assise : le ruban le tient et ferme le jour.
10. Le micro, bonnette DJI en place, entre par la bouche, haut du boîtier vers soi, logo DJI blanc tourné vers l'avant : l'aimant du boîtier est dans la face opposée au logo (Clément, 24 nov. 2026), c'est elle qui se pose contre le disque. Il se pose debout contre la plaque, au fond de l'encoche de la mousse : son aimant le tient sur le disque d'acier.

Au quotidien, rien ne s'ouvre : on sort le micro par la bouche pour le recharger, on le remet de même. **On le prend par sa bonnette**, qui sert de poignée : Clément a vérifié le 24 nov. 2026 que l'aimant ne la déclipse pas quand on tire. Depuis le col de 20 mm, le haut des poils est à 33 mm sous la crête du col au centre et le boîtier à 53 mm. Doigts adultes simulés dans la CAO (bout d'index de 14 mm, de pouce de 17 mm, doigts droits venus d'en haut) : pouce et index pincent la bonnette par ses flancs, 5 mm sous le haut des poils, fourrure écrasée de 3 mm, sans toucher aucune pièce rigide (seulement la fourrure et un peu la mousse du manchon), puis le micro sort tiré tout droit sur 60 mm sans que la main heurte rien (contrôlé à chaque export). Une glissière captive qui remontait le micro de 22 à 45 mm a été dessinée puis abandonnée le même jour : inutile, puisque la bonnette suffit comme poignée. Le corps du micro, lui, reste hors de portée des doigts dans l'appareil : la chambre fait environ 57 mm de large à sa hauteur, pour 28,6 mm de micro et deux doigts.

**Pour rouvrir le corps** (mise au point, changement de mousse) : sortir le micro, desserrer les 4 vis avec une clé six pans de 2 mm passée par la bouche, col et coussin en place (1,2 mm de jeu entre la clé et le col ; avec le coussin, il faut un tournevis six pans de 2 mm à lame d'au moins 60 mm et à tige de moins de 4,9 mm, une clé coudée bute sur le coussin). Les vis restent dans leurs puits, le capot se lève droit. Pas besoin de décoller le coussin.

## Découper la mousse

Deux pièces seulement, dans une plaque de mousse polyuréthane à cellules ouvertes de 10 mm du commerce. Fichiers dans `cad/out/v3-galet/foam/` : un gabarit imprimable par pièce (`gabarit-*.stl`, plaque de 1,2 mm, nom gravé, à imprimer à plat sans support) et le même contour à l'échelle 1 (`contour-*.svg`, avec une barre de 50 mm à vérifier à la règle après impression papier). Régénération : `cad/guarded.sh -m 6 -t 600 .venv/bin/python cad/foam_templates.py`.

| Ordre | Pièce | Plaque | Quantité | Contour |
|---|---|---|---|---|
| 1 | Fond | 10 mm | 2 | ellipse 60 × 40 mm, une encoche droite à 6 h où passent la plaque et le micro |
| 2 | Manchon avant | 10 mm | 1 | bande développée : secteur d'anneau de rayons 58 et 70 mm, 187°, 8 fentes de 2 × 9 mm côté joint, une par nervure des bossages de vis |

1. Poser le gabarit sur la plaque, le tenir à plat d'une main.
2. Couper au cutter à lame neuve de 18 mm, lame verticale, en plusieurs passes légères le long du gabarit. Les encoches d'abord, le contour ensuite.
3. Fond : couper deux fois le même contour. Manchon : le rayon intérieur (bord court, côté encoches) va vers le plan de joint ; les deux extrémités de la bande se rejoignent bout à bout en bas (6 h).

Volumes découpés : fond 23,2 cm³ (deux couches), manchon 22,6 cm³. Pas de bonnette en mousse : c'est celle du DJI, sur le micro.

Abandonnés par rapport à la version précédente, pour couper moins de pièces : la mousse des flancs arrière (6 encoches, 7 morceaux) et la couche du chanfrein du joint (8 encoches). Au modèle acoustique, retirer 9 cm³ de mousse coûte moins de 0,1 dB(A). Le manchon passe en revanche à une bande d'épaisseur constante de 10 mm (le passage d'air libre autour du micro reste de 1368 mm², plus de 20 fois la section du conduit).

## À acheter

| Article | Spécification | Quantité |
|---|---|---|
| Vis M3 × 10 mm à tête fraisée | acier noir, six pans creux de 2 mm (DIN 7991 / ISO 10642) | 6 |
| Écrous M3 | hexagonaux standard, 5,5 mm sur plats, 2,4 mm d'épaisseur (DIN 934) | 4 |
| Bande de mousse autocollante | cellules fermées (néoprène ou EPDM), 2 mm d'épaisseur ; pas de bande de 3 mm de large toute faite : en recouper au cutter et à la règle métallique dans une bande plus large, par exemple [néoprène 30 mm × 2 mm, 10 m](https://www.amazon.fr/Caoutchouc-N%C3%A9opr%C3%A8ne-auto-adh%C3%A9sif-large-%C3%A9paisseur/dp/B008ASE91U) ou [EPDM 50 mm × 2 mm, 10 m](https://www.amazon.fr/d%C3%A9tanch%C3%A9it%C3%A9-caoutchouc-cellulaire-autocollante-mousse/dp/B0841LXXSQ) | 25 cm de lanière de 3 mm |
| Mousse acoustique | polyuréthane à cellules ouvertes, plaque de 10 mm | une plaque A4 |
| Ruban double face | mousse fine d'environ 1 mm, 10 à 12 mm de large | 40 cm par coussin |
| PETG translucide | naturel ou transparent | 5 g |
| Colle | cyanoacrylate | |

La plaque de 10 mm donne les deux couches du fond et le manchon avant (voir « Découper la mousse »).

Déjà en main : les 4 écrous M3 du v2 conviennent (pas ses vis M3 × 6, trop courtes), coussin Brainwavz (mesuré par Clément : 108 × 81 mm, ouverture 72,6 × 48,5, épaisseur 28 ; la fiche annonçait 110 × 90, 70 × 50, 30), disque d'acier de 30 mm, DJI Mic Mini 2 et sa bonnette, PLA noir mat.

Pour la lumière (références choisies le 24 nov. 2026) : batterie LiPo 502025 avec protection, 200 mAh, 27 × 20 × 5 mm (une 502030 dépasse 30 mm avec sa carte) ; chargeur DFRobot DFR0668 USB-C, 16,5 × 28 mm, 50 mA par défaut, 200 mA en pontant une pastille (un TP4056 du commerce charge à 1 A, cinq fois trop pour 200 mAh ; épaisseur avec la prise à mesurer avant d'imprimer la coque arrière) ; interrupteur SS12D00G3 ; filament LED souple de 290 mm, 2,9 V, 1,5 mm de diamètre (Tinytronics), 33 Ω en série ; fil silicone 30 AWG.

Paniers revus le 25 nov. 2026 (rien de commandé) : filaments chez 3DJake (Bambu PLA Matte Charcoal sur bobine, Bambu PETG Translucent Clear pour l'anneau et l'éprouvette de lumière), chargeur DFR0668 et filament LED chez Berrybase, en **nOOds bleu à contacts d'un seul côté, 300 mm (Adafruit 6149)** pour un bleu franc façon manette PS5, au lieu du bleu glacier (6147). Le reste (vis, adhésifs, joint EPDM, batterie, interrupteurs, résistances, fil, gaine, fer et étain) chez Amazon.

Mousse intérieure (choix du 24 nov. 2026) : une vraie mousse acoustique à cellules ouvertes, de la mélamine Basotect. Le kit n'en demande qu'environ 50 cm² en 10 mm (`foam/kit-mousse.json`) : deux lots de gommes magiques Mr. Propre Original suffisent (2,37 € le lot de 2, environ 11,7 × 5,9 × 2,6 cm, en Basotect d'après BASF). Chaque gomme se tranche en deux couches de 10 mm ; le manchon se fait en 3 morceaux, les deux fonds dans les tranches restantes. Une plaque de 120 × 60 cm (27,90 €) ferait la même chose en beaucoup trop grand. BASF publie ses courbes d'absorption mais pas sa résistivité ; les valeurs qui circulent (environ 12 à 13 kPa·s/m²) rejoignent celle du modèle 1D (12 000 Pa·s/m²), sans vérification. Pas de mousse de calage ni de mousse de façade d'enceinte, faite pour laisser passer le son. Vérifié le 24 nov. 2026 : BASF présente la Magic Eraser de P&G comme faite en Basotect W, sa qualité nettoyage, certifiée OEKO-TEX Standard 100 classe I (certificat 10.0.74938, valide) ; la fiche de sécurité P&G ne cite que la résine mélamine-formaldéhyde et signale seulement que la poussière peut irriter les voies respiratoires. Précautions pour le prototype : découper au cutter neuf au-dessus d'une poubelle, faire tomber la poussière en tapotant et à l'air, laisser aérer un jour, **ne pas mouiller** (dans les essais de BASF, une mousse imprégnée d'eau libère environ 7 fois plus de formaldéhyde), laisser sécher l'appareil ouvert entre deux séances, et changer la mousse si elle s'effrite.

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

- **À refaire : l'assise vissée, plus collée** (décision de Clément, 25 nov. 2026). Coller l'assise sur le capot laisse un joint rigide collé juste devant la bouche, impossible à rouvrir pour mettre au point : elle doit être serrée par vis sur un joint mousse comprimé (même principe que le plan de joint, butée face contre face), le coussin seul reste collé. Aucune vis directement dans le PLA : écrous prisonniers ou inserts laiton M3. Touche le capot avant (points d'ancrage) et l'assise : les deux sont à réimprimer, le capot avant de la plaque 2 n'est pas à lancer d'ici là.

- **Baie de l'électronique dessinée sur des cotes de catalogue.** Le chargeur est compté à 4 mm d'épaisseur avec sa prise, la batterie à 30 mm de long avec sa carte de protection. Décision de Clément du 20 novembre 2026 : l'électronique se commande plus tard, la coque arrière s'imprime telle quelle et se réimprime (4 h 42, 72 g) si une pièce ne rentre pas.
- **Aucun clip dans la baie.** Les composants tiennent par empilement, logements ajustés à 0,5 mm et trappe. Aucune cloison imprimée entre chargeur et batterie.
- **Longueur du filament LED.** La rainure fait 212,7 mm sur sa ligne moyenne, le tunnel des fils 40,1 mm jusqu'à la baie. Un filament à contacts d'un seul côté peut partir de la baie, monter par le tunnel (partie cachée) et faire le tour complet : 253 mm en tout, sans trou de lumière. Le nOOds de 30 cm du panier convient ainsi, avec environ 47 mm lovés dans la baie, à condition que son diamètre passe dans le tunnel de 2,6 mm et la rainure de 2,4 × 2,2 mm (Adafruit ne le publie pas : à mesurer à réception). Un filament plus court laisserait un arc éteint en bas (26 mm pour un 185 mm). Pas d'électronique dans la V0 (Clément, 24 nov. 2026).
- **Anneau de la V0** : sans LED, il s'imprime en noir avec la même bobine (plaque 4, 9 min). La version lumineuse viendra avec l'électronique, en **PETG translucide** (Bambu PETG Translucent Clear, choisi le 25 nov. 2026 à la place du Polymaker Panchroma Matte Cotton White : ce PLA mat chargé est quasi opaque, il éteindrait la lumière sous 2,5 mm). Imprimé, le PETG translucide devient laiteux : les lignes de couche diffusent. Son épaisseur se choisit d'abord sur l'éprouvette de lumière (`print/lumiere-petg.3mf`, marches de 0,8 à 2,4 mm, 5 min) : la marche la plus fine qui donne une lueur uniforme sans laisser voir le filament. L'anneau (2,5 mm aujourd'hui) s'amincit ensuite par l'arrière si besoin, sans toucher à la coque. La luminosité se règle à part, par la résistance (33 Ω, environ 50 mA ; plus forte, moins de lumière).
- **Chargeur DFR0668 réel contre la baie** (fiche DFRobot lue le 24 nov. 2026) : carte de 28 × 16,5 mm, mais sa prise batterie PH 2.0 dépasse d'environ 2,4 mm à un bout et la prise USB-C d'environ 0,9 mm à l'autre, et la fiche batterie s'y branche dans l'axe. La poche de la baie fait 29 mm de long pour une carte plate de 4 mm d'épaisseur : la carte ne rentre pas avec sa prise batterie. Soit dessouder la prise et souder les fils sous la carte (pastilles BAT+ et BAT−), soit reprendre la baie sur les pièces mesurées et réimprimer la coque arrière, comme décidé le 20 novembre. Sans effet sur l'acoustique : la baie est hors de la chambre.
- **Épaisseur de l'anneau, premier proto** (25 nov. 2026) : anneau en Bambu PLA Basic blanc, la bobine de 20 g fournie avec l'imprimante (l'anneau en prend environ 2 g). Avant de l'imprimer, l'éprouvette `print/lumiere-pla-basic.3mf` (15 min, 1,6 g, sans support) : cinq parois debout de 0,8, 1,2, 1,6, 2,0 et 2,4 mm, la plus fine la plus basse, que la lumière traverse comme l'anneau (des périmètres côte à côte, pas des couches). On pose une lumière contre leur dos (lampe du téléphone, ou le filament bleu quand il arrive), dans la pénombre puis dans une pièce éclairée, à côté d'une manette PS5 si possible, et on retient la paroi la plus fine qui donne une lueur uniforme sans laisser voir la source. L'anneau s'amincit ensuite par l'arrière à cette épaisseur (`RING_LIGHT` dans `cad/silent_mic_v3_galet.py` : une gorge au dos, côté LED, entre deux rebords de 0,6 mm), sans toucher à la coque ni au serrage : chaque export vérifie qu'à 0,8 mm les faces serrées (dessus, plots, dessous, face extérieure) restent identiques. Imprimé en PLA Basic blanc : `print/corps-anneau-pla-basic.3mf`, 9 min, 1,7 g. La luminosité, elle, se règle par la résistance. Teinte : la barre PS5 est commandée en bleu pur (0, 0, 128 sur 255 dans le pilote Linux écrit par Sony), la même famille de LED bleue que le nOOds 6149 ; aucune mesure de sa luminosité n'est publiée.
- **Joint au visage, essai de Clément du 25 nov. 2026** : aucun jour entre le coussin et le visage, avec l'assise R53 et le col de 20 mm ; l'inspiration se fait par le nez. Le joint au visage n'est donc plus la fuite principale : tout le souffle passe par l'évent, qui devient le réglage de l'atténuation. Le modèle 1D garde par prudence un jour de 0,2 mm sur 3 cm ; sans jour, il donne 26,1 dB(A) avec le conduit de 48 mm², 27,4 avec 42 mm², 28,8 avec 36 mm² (estimations, non mesurées). Rappel : 0,5 mm de jour ferait retomber vers 13 dB(A).
- **Fuites de lumière** (`cad/light_check.py`, 25 nov. 2026, sur les fichiers à imprimer) : l'air éclairé par le filament (rainure, tunnel, baie) ne touche pas la chambre, donc rien ne sort par le col ni par les fentes de l'évent, et il reste au moins 1 mm de plastique noir partout. Hors anneau, la lumière ne peut sortir que par la prise USB-C et la fente de l'interrupteur, et seulement si la baie est éclairée. Corrigé le 25 nov. 2026 avant l'impression de la coque arrière : le corps s'affine vers l'arrière alors que les logements sont droits, si bien que le dégagement sous le chargeur traversait la paroi (deux fentes de 3 mm de part et d'autre de la prise) et que le coin du logement de l'interrupteur perçait la peau. Le dégagement est supprimé, le chargeur reculé de 0,8 mm (prise USB-C d'autant plus profonde dans sa fente) et l'interrupteur de 1,5 mm (levier d'autant plus enfoncé dans la sienne), avec moins de jeu côté peau. Collisions revues dans Onshape : aucun recouvrement entre pièces rigides. Pour une baie sombre : filament caché gainé de noir sur deux couches, une goutte de colle noire à l'entrée du tunnel, voyant de charge du DFR0668 masqué ou laissé visible par la prise comme témoin.
- **Fils du filament LED** : ils descendent de la rainure, à 6 h, jusqu'à la baie par le tunnel, qui fait un coude (3,2 mm depuis le 24 nov. 2026 au soir, pour que le filament nOOds de 1,7 × 1,9 mm y passe lui-même, vrillé d'un quart de tour : il ne plie pas sur sa largeur). La partie du filament cachée dans le tunnel et la baie se gaine de noir (gaine thermo), sinon la baie s'éclaire et la lumière sort par la prise USB-C et la fente de l'interrupteur. Y faire passer d'abord un fil de nylon, puis tirer les deux fils 30 AWG torsadés. La soudure au bout du filament doit tenir dans la rainure, près de l'entrée du tunnel : à vérifier sur la pièce.
- **Levier de l'interrupteur** accessible par une fente de 4 × 2,2 mm sous la coque : à valider au doigt.
- **Vissage du joint à essayer sur les éprouvettes** (`print/cols-et-joint.3mf`) : l'écrou doit se glisser dans sa fente, la tête fraisée s'asseoir au fond de son puits, les deux moitiés se toucher sans jour une fois serrées. L'éprouvette arrière porte aussi, dessous, un avant-trou de 2,7 mm : y visser une M3 × 10 pour vérifier que le filet de la trappe prend sans fendre la pièce.
- **Micro plus profond que sur le v2** : haut du boîtier à 53 mm sous la crête du col, haut de la bonnette à 33 mm depuis le col de 20 mm, pour garder les lèvres loin des poils sans allonger le corps. On le sort par la bonnette (prise simulée dans la CAO, essai de Clément) ; si la prise est malcommode sur la pièce, remonter le micro (`MIC_Z0`, jusqu'à 9 mm en gardant les 8 mm du v2 entre lèvres et poils) coûte de la marge, pas d'isolation.
- **Serrage des vis** : rien ne limite le couple à part la main. Bossage contre bossage, le serrage s'arrête net ; forcer au-delà peut fendre un bossage entre deux couches.
- **Accroche du coussin : ruban double face.** Décision de Clément du 20 novembre 2026. Le scratch du prototype v2 laisse un jour tout autour (calcul : de -3 à 11 dB(A) au lieu de 21). La lèvre élastique du coussin sur une gorge de la coque est réservée à une version de production : même étanchéité attendue, coussin plus simple à changer, mais gorge à ajuster au millimètre.
- **Bonnette DJI : hauteur mesurée, largeur et épaisseur encore estimées.** Clément a mesuré le 23 novembre 2026 environ 48 mm du bas du micro au haut des poils, soit 20 mm au-dessus du boîtier : c'est la cote de la CAO depuis la révision de l'appui visage. Largeur et épaisseur restent estimées à 36 × 26 mm, avec une jupe de 9 mm sur le haut du boîtier ; il reste 3,4 mm jusqu'au capot et au col. La simulation de la visionneuse (bouton « Bouche »), calée sur l'essai du v2 (coussin de 28 mm écrasé à 15, lèvres juste sous son fond), donne 12,5 mm entre les lèvres et les poils ; visage en butée sur le col, 7,6 mm ; lèvres avancées de 22 mm au-delà des joues et visage en butée, encore 1,1 mm. Visage schématique : à confirmer sur la pièce. Les cotes se règlent par `BONNET` dans `cad/silent_mic_v3_galet.py`.
- **Micro couché : écarté le 23 novembre 2026.** Couché dans le sens de la largeur, il heurte les 4 bossages de vis du joint ; dans le sens de la hauteur, ses 48 mm ne ressortent plus par le col (42 mm). Pour raccourcir le corps plus tard : d'après le modèle 1D (estimation, non mesurée), environ 1 dB(A) perdu par 5 à 6 mm retirés.
- **Fentes de sortie, horizontales depuis le 25 nov. 2026** (Clément : inclinées, elles descendaient vers le conduit et, l'appareil posé debout sur le dos, miettes et poussière y glissaient) : rien n'y entre plus par gravité, et le bas de la gorge d'ombre est en pente vers l'extérieur, comme son haut, pour que rien ne s'y pose. Passage de 2,75 mm (102 mm² au lieu de 62), plafond imprimé en pont de 9,3 mm, sans support (vérifié au tranchage : ponts vers 41 mm, supports seulement dans la baie). Évent : le modèle 1D et l'écoulement dans les pièces imprimées restent d'accord (rapport 1,004) ; atténuation estimée 24,9 dB(A) au lieu de 25,1, perte de charge 41 Pa au lieu de 48 à 0,2 L/s (estimations de modèle, non mesurées). À contrôler au souffle sur la pièce (voir « Contrôles avant impression »). Avant et après, en coupe : ![Fente d'évent avant et après](img/v3-fente-event-avant-apres.png)
- **Plafond de la baie** : pont de 31 mm dans son sens le plus court (36 × 31 mm), imprimé sans support et caché par la trappe. Les seuls supports de la coque restent sous le passage de la prise USB-C. Un fléchissement de quelques dixièmes est possible : à mesurer sur la pièce avant de commander l'électronique.
- **Dessous du coussin** : seulement posé sur l'appui, étanche par la pression de la main. Une fente de 0,5 mm sur 3 cm fait tomber l'atténuation calculée de 21 à 12 dB(A). Un anneau de ruban double face est en réserve, à trancher au test du capot (`bench/README.md`, étape 6).
