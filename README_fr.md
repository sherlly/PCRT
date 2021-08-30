# PCRT (PNG Check & Repair Tool)

Traduction par: [ret42](https://github.com/ret42)

## Description:

**PCRT** (PNG Check & Repair Tool), est un outil qui permet de regarder si une image PNG n'est pas corrompue et essaye automatiquement de fixer l'erreur. C'est multiplateforme, ceci marche sous **Windows**, **Linux** et **Mac OS**.

Ça peut:
```
Montrer les informations d'une image
Corriger les erreurs header d'un PNG
Corriger les mauvais chunk IHDR crc dû à une erreur liée à la largeur et la hauteur d'une image
Corriger les mauvais chunk IDAT data lenght dû à la version DOS->UNIX
Corriger les mauvais chunk IDAT crc causé par sa propre erreur
Corriger les chunk IEND perdus
Extrait les données après le chunk IEND (Les programmes malveillants aiment utiliser cette méthode pour se cacher)
Affiche l'image réparée
Injection de payload dans une image
Décompresse les données d'une image et affiche l'image originale
Peut-être plus dans le futur :)
```


## Installation:

- #### **Installer Python 2.7**
    - [Python 2.7](https://www.python.org/downloads/)

- #### **Installer les packages Python**
    - Tkinter
    - [PIL](https://pypi.python.org/pypi/PIL/1.1.6)
    - ctypes (Pour Windows)


- #### **Cloner le source code:**

```
  git clone https://github.com/sherlly/PCRT.git
  cd PCRT
  python PCRT.py
```

## Utilisation:

```
> python PCRT.py -h
usage: PCRT.py [-h] [-q] [-y] [-v] [-m] [-n NAME] [-p PAYLOAD] [-w WAY]
             [-d DECOMPRESS] [-i INPUT] [-f] [-o OUTPUT]

optional arguments:
-h, --help            show this help message and exit
-q, --quiet           don't show the banner infomation
-y, --yes             auto choose yes
-v, --verbose         use the safe way to recover
-m, --message         show the image information
-n NAME, --name NAME  payload name [Default: random]
-p PAYLOAD, --payload PAYLOAD
                      payload to hide
-w WAY, --way WAY     payload chunk: [1]: ancillary [2]: critical
                      [Default:1]
-d DECOMPRESS, --decompress DECOMPRESS
                      decompress zlib data file name
-i INPUT, --input INPUT
                      Input file name (*.png) [Select from terminal]
-f, --file            Input file name (*.png) [Select from window]
-o OUTPUT, --output OUTPUT
                      Output repaired file name [Default: output.png]
```

**[Notice]** sans l'option `-v` signifie que l'on supppose que touts les chunk IDAT lenght sont correctes


## Exemples:

- Windows:

![](http://i.imgur.com/Ksk2ctV.png)

- Linux:

![](http://i.imgur.com/ZXnPqYD.png)

- Mac OS:

![](http://i.imgur.com/re4gQux.png)


## Quelques problèmes:

- Pour Windows:

> Impossible d'afficher l'image réparée

1. Trouver le fichier nommé `ImageShow.py` sous un chemin tel que `X:\Python27\lib\site-packages\PIL\ImageShow.py`
2. Trouver la ligne de code: `return "start /wait %s && ping -n 2 127.0.0.1 >NUL && del /f %s" % (file, file)` autour de la centième ligne et mettez le en commentaire
3. Ajoutez cette nouvelle ligne de code: `return "start /wait %s && PING 127.0.0.1 -n 5 > NUL && del /f %s" % (file, file)` et sauvegarder
4. Relancer l'IDE Python

## Journal de mise à jour

### Version 1.1:

**Ajouts**:

- Montre les informations d'une image (`-m`)
- Injection de payload dans une image (`-p`)
    - Ajout dans un chunk auxiliaire (Le nom du chunk peut généré aléatoirement ou peut être auto-définis) (`-w 1`)
    - Ajout dans un chunk critique (Supporte uniquement le chunk IDAT) (`-w 2`)
- Décompresse les données d'une image et affiche l'image originale (`-d`)

### Version 1.0:
**Options**:
- Corrige les erreurs header d'un PNG
- Corrige les mauvais chunk IHDR crc dû à une erreur liée à la largeur et la hauteur d'une image
- Corrige les mauvais chunk IDAT data lenght dû à la version DOS->UNIX
- Corrige les mauvais chunk IDAT crc causé par sa propre erreur
- Corrige les chunk IEND perdus
- Extrait les données après le chunk IEND (Les programmes malveillants aiment utiliser cette méthode pour se cacher)
- Affiche l'image réparée
