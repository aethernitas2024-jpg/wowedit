# wowedit — montage TikTok calé au beat

Prend un morceau + un dossier de clips, rend un edit vertical 1080×1920 dont
**chaque coupe tombe sur un temps** du morceau.

## Utilisation

```bash
py -3.11 wowedit.py --audio "alquimia.mp3" --clips "C:/.../clips_edit" --out "edit.mp4" --dur 30
```

Toujours commencer par un aperçu (540×960) pour juger le rythme et le choix des
plans, puis relancer sans `--preview`. L'analyse des clips est mise en cache :
seul le premier passage est lent.

```bash
py -3.11 wowedit.py --audio "alquimia.mp3" --clips "C:/.../clips_edit" --out "apercu.mp4" --dur 30 --preview
```

## Options

| option | effet |
|---|---|
| `--dur 30` | durée de l'edit |
| `--start auto` | démarre sur le premier gros drop ; sinon `--start 42.5` ou `--start drop:2` |
| `--seed 7` | rejoue exactement le même montage ; change le chiffre pour une autre version |
| `--ref video.mp4` | recopie le rythme de montage d'une vidéo de référence |
| `--fluid 0.7` | part d'enchaînements fondus (ignoré si `--ref`) |
| `--fx 1.0` | intensité des effets globaux calés sur la grille (`0` pour aucun) |
| `--sun 1.1` | poids donné aux plans à contre-jour |
| `--vista 1.4` | poids donné aux plans de paysage dégagé |
| `--water 0` | poids plans d'eau — **détecteur non fiable**, laisser à 0 |
| `--combat 0` | pénalité combat — **détecteur non fiable**, laisser à 0 |
| `--logo x.png` | image incrustée en fin de montage |
| `--outro "TEXTE"` | carton de fin typographique, si aucun `--logo` |
| `--outro-at 3` | secondes avant la fin où le carton apparaît |
| `--no-decursor` | ne pas effacer le curseur de souris |
| `--must "826,1150"` | instants de la source à inclure d'office |
| `--min-gap 20` | écart minimal entre deux extraits d'un même fichier |
| `--no-autocrop` | garde les bordures de la capture |
| `--title "WOW FOREVER"` | carton Impact au départ et sur chaque drop |
| `--credits credits.json` | affiche `@pseudo` en bas de chaque plan |
| `--bpm 138` | force le tempo si la détection se trompe |
| `--grain 0` | coupe le grain |
| `--res`, `--fps`, `--maxrate` | 1080x1920, 60, 16 Mbit/s par défaut |
| `--keep` | garde les plans intermédiaires pour inspection |

## Ce que fait la machine

**`beat.py` — la grille rythmique.** STFT maison (numpy ; ni librosa ni scipy
sur cette install), flux spectral, autocorrélation pondérée par un prior
log-normal pour éviter les erreurs d'octave, puis calage fin de la période *et*
de la phase par peigne. La grille est régulière, donc les coupes ne dérivent
pas sur 30 s. `find_drops` repère les entrées de drop pour choisir le départ.

**`border.py` — les bordures de capture.** Le chrome de Windows (barre de
titre, barre des tâches) est rigoureusement immobile pendant toute la capture,
alors que l'image de jeu change en permanence : on échantillonne des trames sur
toute la durée et on garde les lignes et colonnes qui varient. Plus fiable que
`cropdetect`, qui ne sait repérer que des bords noirs — or une barre des tâches
est pleine d'icônes colorées.

Le critère est la **proportion d'instants** où la bande bouge, jamais sa
variation moyenne. La différence compte dès qu'une fenêtre est redimensionnée
en cours de capture — ce qui est arrivé sur la capture de 45 min : une ligne
couverte par la barre de titre pendant la moitié du film présente une forte
variation moyenne, puisqu'elle change quand la barre s'en va, et une moyenne
la classait comme du jeu en laissant la barre dans le montage sur toute
l'autre moitié.

**`scout.py` — le choix des beaux plans.** Vignettes 256×144 à 8 im/s, en flux
(45 min passent sans saturer la RAM). Notation sur le mouvement, la saturation,
la texture et l'exposition ; pénalités progressives sur les fondus au noir, les
blancs cramés et les écrans d'interface.

Cinq détecteurs, chacun jugé en extrayant les images où il culmine — jamais sur
ses statistiques. Deux ne marchent pas et sont signalés comme tels plutôt que
laissés actifs :

- **HUD du jeu** — repéré comme *du détail qui ne bouge pas*. Les deux
  conditions comptent ensemble : mesurer la seule immobilité fait prendre un
  ciel uni ou du sable lisse pour une barre d'action, puisqu'une surface sans
  détail ne peut de toute façon produire aucune différence entre deux trames.
  On compare donc la part de pixels structurés-et-gelés de chaque zone d'UI à
  celle du décor ; si le joueur s'arrête, tout gèle et l'écart s'annule seul.
- **Rais de lumière** — hautes lumières chaudes et étendues. Vérifié 8/8.
- **Paysage** — grande plage lisse et plus claire en haut de l'image, donc du
  ciel ou un lointain dégagé. Vérifié 7/8 ; c'est le levier principal, et il
  évite les combats sans avoir à les détecter : on ne se fait pas attaquer au
  milieu d'un grand plan de désert.
- **Eau** — *ne marche pas*, trois versions essayées. Une cascade de WoW
  classic vue de loin est une large bande pâle et **lisse**, donc tout critère
  de micro-contraste l'exclut ; et tout critère de couleur échoue puisque
  chaque zone a sa dominante (sous le brouillard vert de Zangarmarsh, une
  cascade est verte). Laisser `--water 0` et passer par `--must`.
- **Combat** — *ne marche pas*. Se déclenche sur les torches, les cascades
  éclairées et les gros textes de zone : « clair + saturé + net » décrit le feu
  et le texte aussi bien qu'un affrontement. Laisser `--combat 0`.

Les résultats sont mis en cache dans `.scout_cache`.

**`cursor.py` — l'effacement du curseur.** Le curseur est un petit objet net
qui ne bouge pas alors que le décor défile : même signature que le HUD, mais
localisée. La différence de deux moyennes glissantes écarte les grandes zones
stables et ne laisse que les petits objets isolés ; `delogo` rebouche ensuite
la zone en interpolant depuis ses bords. On n'efface que si le curseur reste
au même endroit pendant tout le plan — sinon le rebouchage suivrait mal et
laisserait une traînée plus visible que le curseur.

**`shotfx.py` — l'animation d'un plan.** Punch in/out, slam, dérive, secousse,
ralenti sur les passages calmes, accéléré sur les gros temps. À chaque attaque,
un éclat très bref — aberration chromatique + flash qui retombe en ~3 trames ;
au-delà l'image vire au barbouillage et on ne lit plus le plan. La marge de
sécurité au-delà du cadre est à 1,06 : elle se paie en netteté, puisque tout ce
qui dépasse est agrandi puis jeté.

**`refrhythm.py` — recopier le rythme d'une référence.** On ne regarde pas la
vidéo, on la mesure : ses coupes sont détectées par différence entre trames,
son tempo par la même analyse audio que le reste, et la durée de chaque plan
est exprimée **en temps musicaux** — c'est ce qui permet de transposer le
rythme sur un morceau d'un autre tempo. Une coupe franche fait un pic isolé
d'une ou deux trames, un fondu étale la différence sur plusieurs : la largeur
du pic donne donc la proportion de fondus.

Recopier la seule *forme* de la distribution ne suffit pas à retrouver la
densité. Un temps fort engendre d'office quatre plans d'un quart, ce qui les
surreprésente : sur une mesure à 561 ms de plan moyen, la simple recopie
donnait 277 ms. Le quantile est donc décalé par bissection jusqu'à retrouver
la durée moyenne mesurée, en plus de la forme.

**`joins.py` — les raccords.** Coupe franche sur les plus gros temps (c'est
elle qui fait claquer le montage), fondu ailleurs : `zoomin`, `hblur`,
`dissolve`, `radial`… Une transition doit être **centrée** sur le temps pour
que la coupe reste calée, donc chaque plan est rendu avec une demi-transition
de rab à chaque bout. Tout est compté en trames et non en secondes : sur
soixante raccords, l'arrondi au flottant décalerait la fin du montage.

**`wowedit.py` — le montage.** Plus le temps tape fort, plus la coupe est
courte : 2 à 4 temps au calme, 1 temps en régime normal, demi-temps sur les
gros temps, et parfois une rafale de quatre doubles-croches. La passe finale
ajoute les effets globaux calés sur la grille (respiration, secousse, flash,
tick chromatique à chaque mesure), l'étalonnage et le son.

## Limites connues

- Le texte de dégâts flottant s'affiche au milieu de l'image, hors des zones
  d'interface : la détection de HUD ne peut structurellement pas l'attraper.
- Enregistrer avec `Alt+Z` (interface masquée) reste le meilleur moyen
  d'obtenir des plans propres, même avec l'effacement du curseur.
- Une source 16:9 recadrée en 9:16 n'utilise qu'environ un tiers de la largeur
  et se retrouve agrandie ~1,4× : c'est inhérent au format, pas un défaut du
  rendu.
- Un logo sans canal alpha (fond noir) est fusionné en mode *screen*, où le
  noir n'ajoute rien. Cette fusion se fait **en RVB, jamais en YUV** : `screen`
  appliquée aux canaux de chrominance est un non-sens — un gris neutre à 128
  ressort à 192 — et teinte toute la vidéo en magenta.
- Aucun logo de jeu n'est redessiné : `--logo` incruste le fichier fourni,
  sinon `--outro` pose un carton typographique original.
- La détection de tempo vise 70–200 BPM avec un a priori à 140. Vérifier le BPM
  annoncé et forcer `--bpm` au besoin.
