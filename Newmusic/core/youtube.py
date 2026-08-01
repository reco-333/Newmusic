# Khithlainhtet - ShrutiBots API First & 500-Limit Auto-Cache Manager
# Optimized exclusively for API Stream URL Extraction

import os
import re
import aiohttp
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict

from youtubesearchpython.future import Playlist, VideosSearch

from Newmusic import logger, config
from Newmusic.helpers import Track, utils

# --- SHRUTIBOTS API CONFIGURATION ---
API_URL = "https://api01.shrutibots.site"  # သို့မဟုတ် သင်သုံးနေသော API URL
API_KEY = "ShrutiBots7xhmAalRnTT0mTbgszR4"  # သင်၏ Personal API Key
# ------------------------------------


class LimitedCache(OrderedDict):
    """အများဆုံး သီချင်း ၅၀၀ ပုဒ်ထိ Cache သိမ်းပေးပြီး ပြည့်ရင် အဟောင်းတွေကို အလိုအလျောက်ဖျက်ပေးသည်"""
    def __init__(self, maxsize=500, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        
        # 500 ပုဒ် Limit ပါတဲ့ Cache စနစ် (API ခေါ်ဆိုမှုကို မြန်ဆန်စေရန်)
        self.url_cache = LimitedCache(maxsize=500)       
        self.cache_ttl = 3600     # 1 hour cache TTL
        
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )
        
        logger.info("⚡ [Khithlainhtet] ShrutiBots API-First & 500-Limit Auto-Cache Mode Active")

    def get_cookies(self):
        return None

    async def save_cookies(self, urls: list[str]) -> None:
        pass

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    # ---------------- SEARCH & PLAYLIST ----------------
    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            _search = VideosSearch(query, limit=1)
            results = await _search.next()
        except Exception:
            return None
        if results and results.get("result"):
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=(data.get("title") or "")[:25],
                thumbnail=(data.get("thumbnails", [{}])[-1].get("url") or "").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            videos = plist.get("videos", []) or []

            while len(videos) < limit and plist.get("hasMoreVideos"):
                plist = await Playlist.getNextVideos(plist)
                if not plist:
                    break
                videos.extend(plist.get("videos", []) or [])

            for data in videos[:limit]:
                thumbs = data.get("thumbnails") or [{}]
                link = data.get("link") or f"{self.base}{data.get('id')}"
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=(data.get("title") or "")[:25],
                    thumbnail=(thumbs[-1].get("url") or "").split("?")[0],
                    url=link.split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    # ------------------- SHRUTIBOTS API STREAM URL EXTRACTOR (API ONLY) -------------------
    async def get_stream_url(self, video_id: str, video: bool = False) -> str | None:
        """ShrutiBots API ကို သီးသန့်အဓိကထား၍ Stream URL လှမ်းယူခြင်း"""
        media_type = "video" if video else "audio"
        
        if not API_URL or not API_KEY:
            logger.error("API_URL or API_KEY is missing!")
            return None

        api_endpoint = f"{API_URL.rstrip('/')}/download?url={video_id}&type={media_type}&api_key={API_KEY}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_endpoint, timeout=12, allow_redirects=True) as response:
                    if response.status == 200:
                        content_type = response.headers.get("Content-Type", "")
                        
                        # 1. JSON ပုံစံဖြင့် လာလျှင်
                        if "application/json" in content_type:
                            try:
                                data = await response.json()
                                stream_url = data.get("url") or data.get("link") or data.get("stream_url")
                                if stream_url:
                                    return stream_url
                            except:
                                pass
                        
                        # 2. API က Redirect လုပ်ထားသော Final Direct URL ဖြစ်နေလျှင်
                        final_url = str(response.url)
                        if final_url and "shrutibots.site" not in final_url and final_url.startswith("http"):
                            return final_url
                            
                        # 3. Text သို့မဟုတ် URL သက်သက် ပြန်လာလျှင်
                        text_data = await response.text()
                        if text_data:
                            text_data = text_data.strip()
                            if text_data.startswith("http"):
                                return text_data
                                
        except Exception as e:
            logger.error(f"ShrutiBots API extraction error for {video_id}: {e}")
            
        return None

    # ------------------- CACHED VERSION (500-LIMIT LRU) -------------------
    async def get_stream_url_cached(self, video_id: str, video: bool = False) -> str | None:
        """Cache စစ်ဆေးခြင်း (အများဆုံး ၅၀၀ ပုဒ်အထိ မှတ်ထားမည်)"""
        now = datetime.now()
        key = f"{video_id}_{video}"
        
        if key in self.url_cache:
            url, expires = self.url_cache[key]
            if now < expires:
                self.url_cache.move_to_end(key)
                return url

        url = await self.get_stream_url(video_id, video)
        if url:
            self.url_cache[key] = (url, now + timedelta(seconds=self.cache_ttl))
        return url

    # ------------------- COMPATIBILITY METHOD -------------------
    async def download(self, video_id: str, video: bool = False) -> str | None:
        """Compatibility method for existing bot code"""
        return await self.get_stream_url_cached(video_id, video)
