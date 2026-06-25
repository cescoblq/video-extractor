"""Extracteur Wistia — utilisé notamment par Kajabi."""
import json
import re
import urllib.request

PATTERN = re.compile(r"wistia_async_([a-z0-9]+)")


def detect(html: str) -> bool:
    return bool(PATTERN.search(html))


def extract(html: str) -> list[dict]:
    """Retourne une liste de {id, url, filename} pour chaque vidéo Wistia trouvée."""
    ids = sorted(set(PATTERN.findall(html)))
    results = []
    for media_id in ids:
        try:
            media = _fetch_media(media_id)
            asset = _best_asset(media)
            name = media.get("name") or media_id
            results.append({
                "id": media_id,
                "url": asset["url"],
                "filename": _safe_filename(name),
            })
        except Exception as e:
            results.append({"id": media_id, "url": None, "error": str(e)})
    return results


def _fetch_media(media_id: str) -> dict:
    url = f"https://fast.wistia.com/embed/medias/{media_id}.json"
    with urllib.request.urlopen(url, timeout=30) as r:
        raw = re.sub(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", b"", r.read())
    return json.loads(raw)["media"]


def _best_asset(media: dict) -> dict:
    for a in media["assets"]:
        if a.get("type") == "original":
            return a
    return max(media["assets"], key=lambda a: a.get("size", 0))


def _safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    fname = re.sub(r"[^A-Za-z0-9._-]", "", name) or "video"
    import pathlib
    if not pathlib.Path(fname).suffix.lower() in (".mp4", ".mov", ".webm"):
        fname += ".mp4"
    return fname
