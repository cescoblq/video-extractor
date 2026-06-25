# video-extractor

Outil de récupération de vidéos embarquées dans des pages HTML (formations en ligne, etc.).

## Contexte

Créé pour récupérer des vidéos de formation perdues suite à une panne de disque dur. Les vidéos étaient intégrées via Wistia dans des pages Kajabi.

## Usage

```bash
python3 video_extractor.py [dossier_pages] [dossier_sortie]
# Par défaut : pages/ → recovered/
```

1. Sauvegarder le code source HTML de chaque page (connecté au site) → `pages/`
2. Lancer le script
3. Les vidéos sont téléchargées dans `recovered/`
4. Le log détaillé est dans `recovered/extract.log`

Les vidéos déjà présentes sont automatiquement skippées.

## Structure

```
video_extractor.py       # point d'entrée, détecte la plateforme
extractors/
  wistia.py              # Wistia (Kajabi, Wistia natif)
  # vimeo.py            # à venir
  # youtube.py          # à venir
```

## Ajouter une plateforme

Créer `extractors/<nom>.py` avec trois fonctions :
- `detect(html: str) -> bool` — détecte si la page utilise cette plateforme
- `extract(html: str) -> list[dict]` — retourne `[{id, url, filename}]`

Puis l'importer dans `video_extractor.py` et l'ajouter à `EXTRACTORS`.

## Repo

https://github.com/cescoblq/video-extractor
