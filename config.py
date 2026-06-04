from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.API_ID = int(getenv("API_ID", 0))
        self.API_HASH = getenv("API_HASH")

        self.BOT_TOKEN = getenv("BOT_TOKEN")
        self.MONGO_URL = getenv("MONGO_URL")

        self.LOGGER_ID = int(getenv("LOGGER_ID", 0))
        self.OWNER_ID = int(getenv("OWNER_ID", 0))

        self.DURATION_LIMIT = int(getenv("DURATION_LIMIT", 700)) * 60
        self.QUEUE_LIMIT = int(getenv("QUEUE_LIMIT", 20))
        self.PLAYLIST_LIMIT = int(getenv("PLAYLIST_LIMIT", 20))
        self.API_URL = getenv("API_URL","https://portal.arcmusic.fun/")
        self.YOUTUBE_API_KEY = getenv("YOUTUBE_API_KEY", "ARC11cec58639ed7021866f48")
        
        self.SESSION1 = getenv("SESSION", None)
        self.SESSION2 = getenv("SESSION2", None)
        self.SESSION3 = getenv("SESSION3", None)


        self.SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/myanmarbot_music")
        self.SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/myanmar_music_Bot2027")
        
        self.AUTO_LEAVE: bool = False
        self.AUTO_END: bool = False
    
        self.THUMB_GEN: bool = getenv("THUMB_GEN", "True").lower() == "true"
        self.VIDEO_PLAY: bool = getenv("VIDEO_PLAY", "True").lower() == "true"

        self.LANG_CODE = getenv("LANG_CODE", "en")
        self.RAW_COOKIES = getenv("RAW_COOKIES", None)

        self.COOKIES_URL = [
            url for url in getenv("COOKIES_URL", "").split(" ")
            if url and " " in url
        ]

       
        self.DEFAULT_THUMB = getenv("DEFAULT_THUMB", "https://te.legra.ph/file/3e40a408286d4eda24191.jpg")
        self.PING_IMG = getenv("PING_IMG", "https://graph.org//file/389a372e8ae039320ca6c.png")
        self.START_IMG = getenv("START_IMG", "https://files.catbox.moe/83zj85.jpg")
        
    def check(self):
        missing = [
            var
            for var in ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL", "LOGGER_ID", "OWNER_ID", "SESSION1"]
            if not getattr(self, var)
        ]
        if missing:
            raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
