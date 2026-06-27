#!/usr/bin/env python3
"""Extrait et télécharge des vidéos embarquées dans des pages HTML.

Plateformes supportées : Wistia (Kajabi), LearnyBox, Loom (Skool)

Usage:
    python3 video_extractor.py [dossier_pages] [dossier_sortie]

Par défaut : lit pages/*.html, écrit dans recovered/
Log : <dossier_sortie>/extract.log

Loom : déposer un fichier *cookies*.txt (export Netscape) à la racine du projet.
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
