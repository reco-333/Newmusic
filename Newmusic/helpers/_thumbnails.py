import os
import aiohttp
import textwrap
import io
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from Newmusic import config
from Newmusic.helpers import Track

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Thumbnail:
    def __init__(self):
        self.size = (1280, 720)
        self.session: aiohttp.ClientSession | None = None
        # API URL မသုံးချင်ရင် ဒီအတိုင်း အလွတ်ထားလို့ရပါတယ်
        self.API_URL = "" 
        
        title_font_path = os.path.join(BASE_DIR, "..", "helpers", "Raleway-Bold.ttf")
        info_font_path = os.path.join(BASE_DIR, "..", "helpers", "Inter-Light.ttf")

        try:
            self.font_title = ImageFont.truetype(title_font_path, 45)
            self.font_info = ImageFont.truetype(info_font_path, 30)
            self.font_time = ImageFont.truetype(info_font_path, 24)
            self.font_credit = ImageFont.truetype(info_font_path, 28)
        except:
            self.font_title = self.font_info = self.font_time = self.font_credit = ImageFont.load_default()

    async def start(self) -> None:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def get_image(self, image_url: str):
        """ပုံကို ဆွဲယူတဲ့အပိုင်း (Memory ပေါ်မှာတင် လုပ်ဆောင်လို့ CPU သက်သာစေတယ်)"""
        if not self.session: await self.start()
        url = f"{self.API_URL}{image_url}" if self.API_URL else image_url
        try:
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
        except:
            return None
        return None

    async def generate(self, song: Track) -> str:
        try:
            os.makedirs("cache", exist_ok=True)
            output = f"cache/{song.id}.png"
            
            # Caching: ရှိပြီးသားပုံဆိုရင် ထပ်မလုပ်တော့ဘဲ ပြန်ပို့ပေးမယ် (CPU Save)
            if os.path.exists(output):
                return output

            raw_cover = await self.get_image(song.thumbnail)
            if not raw_cover:
                raw_cover = Image.new("RGBA", (500, 500), (40, 40, 40, 255))

            # 1. Background (Blur Radius ကို ၂၀ ပဲထားလို့ CPU အရမ်းသက်သာပါတယ်)
            bg = ImageOps.fit(raw_cover, self.size, method=Image.Resampling.BOX)
            bg = bg.filter(ImageFilter.GaussianBlur(20)) 
            bg = ImageEnhance.Brightness(bg).enhance(0.6)
            draw = ImageDraw.Draw(bg)

            # 2. Album Cover (ဘယ်ဘက်ခြမ်း Layout)
            c_size = 520
            cx, cy = 100, (self.size[1] - c_size) // 2
            cover_img = ImageOps.fit(raw_cover, (c_size, c_size), method=Image.Resampling.LANCZOS)
            
            # Rounded Corners (ပုံစံလှအောင်)
            mask = Image.new("L", (c_size, c_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, c_size, c_size), 40, fill=255)
            cover_img.putalpha(mask)
            bg.paste(cover_img, (cx, cy), cover_img)

            # 3. Text & Controls (ညာဘက်ခြမ်း Layout)
            tx_start = 700
            
            # Song Title & Info
            draw.text((tx_start, 180), "Now Playing", font=self.font_info, fill=(255, 255, 255, 180))
            
            # Title wrap (ရှည်ရင် အောက်ဆင်းပေးမယ်)
            lines = textwrap.wrap(song.title, width=25)
            curr_y = 230
            for line in lines[:2]:
                draw.text((tx_start, curr_y), line, font=self.font_title, fill="white")
                curr_y += 55

            # Progress Bar
            bar_y = 480
            bar_w = 450
            draw.rounded_rectangle((tx_start, bar_y, tx_start + bar_w, bar_y + 8), 4, fill=(100, 100, 100, 150))
            draw.rounded_rectangle((tx_start, bar_y, tx_start + (bar_w * 0.4), bar_y + 8), 4, fill=(255, 200, 50))
            draw.text((tx_start, bar_y + 20), "0:03", font=self.font_time, fill="white")
            draw.text((tx_start + bar_w, bar_y + 20), "4:33", font=self.font_time, fill="white", anchor="ra")

            # Playback Symbols
            ctrl_y = 560
            draw.text((tx_start + 70, ctrl_y), "<<", font=self.font_title, fill="white", anchor="ma")
            draw.text((tx_start + 200, ctrl_y), "||", font=self.font_title, fill="white", anchor="ma")
            draw.text((tx_start + 330, ctrl_y), ">>", font=self.font_title, fill="white", anchor="ma")

            # Credit
            draw.text((self.size[0]//2, self.size[1] - 45), "Credit by @HANTHAR999", font=self.font_credit, fill=(255, 255, 255, 180), anchor="ma")

            bg.save(output, "PNG")
            return output

        except Exception as e:
            print(f"Error: {e}")
            return config.DEFAULT_THUMB
