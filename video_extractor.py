#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                      video_extractor.py                         ║
║          Extraction de vidéos embarquées dans des pages HTML    ║
╚══════════════════════════════════════════════════════════════════╝

USAGE
    python3 video_extractor.py [dossier_pages] [dossier_sortie]

    dossier_pages   : dossier contenant les .html sources  (défaut : pages/)
    dossier_sortie  : dossier de destination des .mp4      (défaut : recovered/)

    Les vidéos déjà présentes dans dossier_sortie sont automatiquement skippées.
    Les vidéos sont nommées d'après le fichier HTML source (ex : "01 - Intro.html"
    → "01 - Intro.mp4"). Si une page contient plusieurs vidéos : _1, _2, etc.

LOG
    Un fichier extract.log est écrit dans dossier_sortie à chaque exécution.

PLATEFORMES SUPPORTÉES
    ┌─────────────────┬───────────────────────────┬──────────────────────┐
    │ Plateforme      │ Détection                 │ Auth requise         │
    ├─────────────────┼───────────────────────────┼──────────────────────┤
    │ Wistia (Kajabi) │ wistia_async_* dans HTML  │ Non                  │
    │ LearnyBox       │ learnybox.com dans HTML   │ Non                  │
    │ Loom (Skool…)   │ loom.com/share/* dans HTML│ Cookies (voir ci-bas)│
    └─────────────────┴───────────────────────────┴──────────────────────┘

COOKIES (Loom uniquement)
    Déposer un fichier *cookies*.txt au format Netscape HTTP Cookie File
    à la racine du projet (même dossier que ce script).
    Le script le détecte automatiquement via glob("*cookies*.txt").

    Export depuis Chrome : extension "Get cookies.txt LOCALLY" (Chrome Web Store).
    → Se connecter à la plateforme hôte (ex : skool.com), exporter, déposer ici.

    Les cookies Skool suffisent pour les vidéos Loom embedées dans Skool
    (les vidéos sont unlisted/publiques côté Loom — pas besoin de cookies loom.com).

    Expiration : vérifier les dates dans le fichier (colonne 5 = timestamp Unix).
    Ré-exporter via l'extension dès expiration.

DÉPENDANCES
    - Python 3.10+ (walrus operator :=)
    - yt-dlp  : requis uniquement pour Loom  →  uv tool install yt-dlp
    - ffmpeg  : optionnel, améliore la qualité yt-dlp si présent

CHANGEMENT DE MACHINE
    Le fichier cookies est dans .gitignore — non versionné.
    À copier manuellement (clé USB, etc.) sur chaque nouvelle machine.
    Le script lui-même est versionné sur github.com/cescoblq/video-extractor.
"""
import logging
import subprocess
import sys
import urllib.request
from pathlib import Path

from extractors import learnybox, loom, wistia

EXTRACTORS = [wistia, learnybox, loom]


def setup_logging(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("video_extractor")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    return logger


def find_cookies_file() -> Path | None:
    candidates = sorted(Path(".").glob("*cookies*.txt"))
    return candidates[0] if candidates else None


def download(url: str, dest: Path, logger: logging.Logger, timeout: int = 600):
    logger.info(f"  Téléchargement: {dest.name}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        with open(dest, "wb") as f:
            while buf := r.read(1024 * 1024):
                f.write(buf)
    logger.info(f"  ✓ OK ({dest.stat().st_size:,} octets)")


def download_ytdlp(url: str, dest: Path, logger: logging.Logger, cookies: Path | None = None):
    logger.info(f"  Téléchargement (yt-dlp): {dest.name}")
    cmd = ["yt-dlp", "-o", str(dest), "--no-playlist"]
    if cookies:
        cmd += ["--cookies", str(cookies)]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip().splitlines()[-1] if result.stderr else "yt-dlp failed")
    logger.info(f"  ✓ OK ({dest.stat().st_size:,} octets)")


def process_html(html_path: Path, out_dir: Path, logger: logging.Logger, cookies: Path | None = None):
    html = html_path.read_text(errors="ignore")

    extractor = next((e for e in EXTRACTORS if e.detect(html)), None)
    if extractor is None:
        logger.warning(f"[{html_path.name}] aucune plateforme reconnue, ignoré")
        return

    logger.info(f"[{html_path.name}] plateforme: {extractor.__name__.split('.')[-1]}")
    videos = extractor.extract(html)

    for i, v in enumerate(videos):
        if "error" in v:
            logger.error(f"  {v['id']}: {v['error']}")
            continue
        suffix = f"_{i + 1}" if len(videos) > 1 else ""
        dest = out_dir / f"{html_path.stem}{suffix}.mp4"
        if dest.exists():
            logger.debug(f"  {dest.name} déjà présent, skip")
            continue
        logger.info(f"  {v['id']} -> {v['filename']}")
        try:
            if v.get("downloader") == "ytdlp":
                download_ytdlp(v["url"], dest, logger, cookies=cookies)
            else:
                download(v["url"], dest, logger)
        except Exception as e:
            logger.warning(f"  SKIP {v['id']} ({type(e).__name__}: {e})")
            if dest.exists():
                dest.unlink()


def main():
    pages_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("pages")
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("recovered")
    out_dir.mkdir(parents=True, exist_ok=True)

    cookies = find_cookies_file()

    logger = setup_logging(out_dir / "extract.log")
    logger.info("=== Démarrage extraction vidéos ===")
    logger.info(f"Pages : {pages_dir.absolute()}")
    logger.info(f"Sortie : {out_dir.absolute()}")
    if cookies:
        logger.info(f"Cookies : {cookies}")

    html_files = sorted(pages_dir.glob("*.html")) + sorted(pages_dir.glob("*.htm"))
    if not html_files:
        logger.error(f"Aucun fichier .html trouvé dans {pages_dir}")
        return

    logger.info(f"{len(html_files)} fichier(s) à traiter")
    for i, html_path in enumerate(html_files, 1):
        logger.info(f"\n--- [{i}/{len(html_files)}] {html_path.name} ---")
        process_html(html_path, out_dir, logger, cookies=cookies)

    logger.info("\n=== Extraction terminée ===")


if __name__ == "__main__":
    main()
