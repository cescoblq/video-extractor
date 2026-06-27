# video-extractor

Outil CLI Python pour extraire et télécharger les vidéos embarquées dans des pages HTML de formations en ligne.

## Usage

```bash
python3 video_extractor.py [dossier_pages] [dossier_sortie]
# Par défaut : pages/ → recovered/
```

1. Sauvegarder le code source HTML de chaque page (connecté au site) → `pages/`
2. Lancer le script
3. Les vidéos sont téléchargées dans `recovered/`, nommées d'après le fichier HTML source
4. Le log détaillé est dans `recovered/extract.log`

Les vidéos déjà présentes sont automatiquement skippées (reprise sûre).

## Plateformes supportées

| Plateforme | Exemple d'usage | Auth requise |
|---|---|---|
| Wistia | Kajabi, Wistia natif | Non |
| LearnyBox | Formations FR sur LearnyBox | Non |
| Loom | Skool, embeds divers | Cookies (voir ci-dessous) |

## Dépendances

- Python 3.10+
- `yt-dlp` — requis pour Loom uniquement : `uv tool install yt-dlp`
- `ffmpeg` — optionnel, améliore la qualité yt-dlp si présent

## Cookies (Loom)

Les vidéos Loom nécessitent un fichier de cookies au format Netscape HTTP Cookie File.

**Export depuis Chrome :** extension [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
→ Se connecter à la plateforme hôte (ex : skool.com), exporter, déposer le fichier `.txt` à la racine du projet.

Le script détecte automatiquement tout fichier nommé `*cookies*.txt` dans le répertoire courant.

> Les cookies Skool suffisent pour les vidéos Loom embedées dans Skool.
> Les cookies expirent : vérifier la colonne 5 du fichier (timestamp Unix).

## Changement de machine

Le script est versionné sur [github.com/cescoblq/video-extractor](https://github.com/cescoblq/video-extractor) — un `git clone` suffit pour le récupérer.

Le fichier cookies est dans `.gitignore` (données de session sensibles) : le copier manuellement sur chaque nouvelle machine.

## Structure

```
video_extractor.py     # point d'entrée — détecte la plateforme et orchestre
extractors/
  wistia.py            # Wistia (Kajabi, Wistia natif)
  learnybox.py         # LearnyBox (MP4 CloudFront direct)
  loom.py              # Loom via yt-dlp
pages/                 # HTML sources à déposer ici (gitignored)
recovered/             # vidéos téléchargées + extract.log (gitignored)
```

## Ajouter une plateforme

Créer `extractors/<nom>.py` avec :
- `detect(html: str) -> bool` — détecte si la page utilise cette plateforme
- `extract(html: str) -> list[dict]` — retourne `[{id, url, filename, ?downloader}]`

Puis l'importer dans `video_extractor.py` et l'ajouter à `EXTRACTORS`.
