"""Extracteur LearnyBox — vidéos hébergées sur CloudFront en MP4 direct."""
import re
from pathlib import Path

DETECT_PATTERN = re.compile(r"learnybox\.com")
SOURCE_PATTERN = re.compile(r'<source\s+src="(https://[^"]+\.mp4)"', re.IGNORECASE)
VIDEO_ID_PATTERN = re.compile(r'id="video_(\d+)"')


def detect(html: str) -> bool:
    return bool(DETECT_PATTERN.search(html))


def extract(html: str) -> list[dict]:
    results = []
    urls = SOURCE_PATTERN.findall(html)
    ids = VIDEO_ID_PATTERN.findall(html)

    for i, url in enumerate(urls):
        media_id = ids[i] if i < len(ids) else str(i + 1)
        filename = Path(url.split("?")[0]).name
        results.append({"id": media_id, "url": url, "filename": filename})

    return results
