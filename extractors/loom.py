"""Extracteur Loom — utilisé notamment par Skool."""
import re
from pathlib import Path

DETECT_PATTERN = re.compile(r"loom\.com/share/([a-f0-9]{32})")


def detect(html: str) -> bool:
    return bool(DETECT_PATTERN.search(html))


def extract(html: str) -> list[dict]:
    ids = list(dict.fromkeys(DETECT_PATTERN.findall(html)))  # déduplique, garde l'ordre
    return [
        {
            "id": video_id,
            "url": f"https://www.loom.com/share/{video_id}",
            "filename": f"{video_id}.mp4",
            "downloader": "ytdlp",
        }
        for video_id in ids
    ]
