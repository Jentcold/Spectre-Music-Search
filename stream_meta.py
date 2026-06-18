"""
Advanced scraper helper to pull project titles from untitled.stream links.
"""

import aiohttp
import re

async def fetch_stream_title(project_url: str, timeout_seconds: float = 8.0) -> str | None:
    """
    Scrapes the page source of an untitled.stream link using complete browser headers
    to bypass Cloudflare defenses and extract the real metadata title.
    """
    # Thorough browser headers derived from a real session to bypass automated flags
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(project_url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as resp:
                if resp.status != 200:
                    print(f"[Scraper Warning] Received status code {resp.status} for URL: {project_url}")
                    return None
                
                html_content = await resp.text()

                # 1: Check OpenGraph title attribute (Most reliable for rich embeds)
                og_title_match = re.search(
                    r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', 
                    html_content, 
                    re.IGNORECASE
                )
                if og_title_match:
                    title = og_title_match.group(1).strip()
                    if title and title.lower() != "untitled":
                        return title

                # 2: Check Twitter title attribute
                twitter_title_match = re.search(
                    r'<meta\s+name=["\']twitter:title["\']\s+content=["\'](.*?)["\']', 
                    html_content, 
                    re.IGNORECASE
                )
                if twitter_title_match:
                    title = twitter_title_match.group(1).strip()
                    if title and title.lower() != "untitled":
                        return title

                # 3: Standard document title fallback
                meta_title = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
                if meta_title:
                    raw_title = meta_title.group(1).strip()
                    # Strip generic branding suffix if applicable
                    cleaned_title = re.sub(r'\s*\|\s*\[?untitled\]\??', '', raw_title, flags=re.IGNORECASE).strip()
                    if cleaned_title and cleaned_title.lower() != "untitled":
                        return cleaned_title

    except Exception as e:
        print(f"[Scraper Error] Failed parsing untitled.stream meta tracking details: {e}")
        
    return None