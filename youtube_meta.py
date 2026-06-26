"""
Small helper to fetch a YouTube video's title via the public oEmbed endpoint.
No API key required. Used so search results show the real video title.
"""

import re

import aiohttp

OEMBED_URL = "https://www.youtube.com/oembed"

# Regex to isolate just the pure clean youtube link.
# Covers /shorts/, /embed/, /live/, /v/ and youtu.be paths...
YT_ID_RE = re.compile(
    r"(?:youtube\.com/(?:shorts/|embed/|live/|v/)|youtu\.be/)([\w-]+)", re.IGNORECASE
)
# ...and the ?v= query form (which may sit behind other params, e.g. ?app=desktop&v=ID)
YT_WATCH_RE = re.compile(r"[?&]v=([\w-]+)", re.IGNORECASE)


async def fetch_youtube_title(video_url: str, timeout_seconds: float = 5.0) -> str | None:
    """
    Returns the video title, or None if it couldn't be fetched for any reason.
    Cleans URLs to prevent historical tracking flags from breaking the oEmbed request.
    """
    match = YT_ID_RE.search(video_url) or YT_WATCH_RE.search(video_url)
    if not match:
        return None

    # Rebuild a clean URL for the API request (removes &t=, &list=, etc.)
    clean_url = f"https://www.youtube.com/watch?v={match.group(1)}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                OEMBED_URL,
                params={"url": clean_url, "format": "json"},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data.get("title")
    except Exception:
        return None
