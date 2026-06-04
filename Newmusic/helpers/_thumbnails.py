import os
import aiohttp
import textwrap
import io
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
import math
import random

from Newmusic import config
from Newmusic.helpers import Track

BASE_DIR = os.path.dirname(os.path.abspath(file))

class Thumbnail:
    def init(self):
        self.size = (1280, 720)
        self.session: aiohttp.ClientSession | None = None
        self.API_URL = "" 
        
        # Font paths
        title_font_path = os.path.join(BASE_DIR, "..", "helpers", "Raleway-Bold.ttf")
        info_font_path = os.path.join(BASE_DIR, "..", "helpers", "Inter-Light.ttf")

        try:
            # စာလုံးအရွယ်အစားများကို အကြီးကြီးပြင်ဆင်ထားသည်
            self.font_title = ImageFont.truetype(title_font_path, 60) # သီချင်းခေါင်းစဉ်
            self.font_info = ImageFont.truetype(info_font_path, 45)  # Now Playing
            self.font_small = ImageFont.truetype(info_font_path, 35) # Contact Text
            self.font_time = ImageFont.truetype(info_font_path, 28)
            self.font_credit = ImageFont.truetype(title_font_path, 35)
        except:
            self.font_title = self.font_info = self.font_small = self.font_time = self.font_credit = ImageFont.load_default()

    async def start(self) -> None:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def get_image(self, image_url: str):
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
            
            if os.path.exists(output):
                return output

            raw_cover = await self.get_image(song.thumbnail)
            if not raw_cover:
                raw_cover = Image.new("RGBA", (500, 500), (20, 20, 20, 255))

            # 1. Background (စာသားပေါ်အောင် ပိုမှောင်ပေးထားသည်)
            bg = ImageOps.fit(raw_cover, self.size, method=Image.Resampling.BOX)
            bg = bg.filter(ImageFilter.GaussianBlur(30)) 
            bg = ImageEnhance.Brightness(bg).enhance(0.3) # 0.3 အထိလျှော့ချ၍ ပိုမှောင်စေသည်
            draw = ImageDraw.Draw(bg)

            # 2. Album Cover with White Border
            c_size = 520
            cx, cy = 80, (self.size[1] - c_size) // 2
            
            # Draw White Glow Border
            draw.rounded_rectangle((cx-10, cy-10, cx+c_size+10, cy+c_size+10), 45, outline="white", width=8)

            cover_img = ImageOps.fit(raw_cover, (c_size, c_size), method=Image.Resampling.LANCZOS)
            mask = Image.new("L", (c_size, c_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, c_size, c_size), 40, fill=255)
            cover_img.putalpha(mask)
            bg.paste(cover_img, (cx, cy), cover_img)

            # 3. Top Contact Text (အလယ်တည့်တည့်)
            contact = "If you want to create your own music bot, please contact @HEX_KING9"
            draw.text((self.size[0]//2, 50), contact, font=self.font_small, fill="white", anchor="ma")

            # 4. Player UI (စာသားများကို ပိုကြီးပြီး အလယ်နားတိုးထားသည်)
            tx_start = 650 # စာသားစတင်မည့်နေရာကို ၆၅၀ သို့ တိုးလိုက်သည်
            
            # Now Playing
            draw.text((tx_start, 200), "Now Playing", font=self.font_info, fill=(255, 200, 50))
            
            # Song Title (အကြီးဆုံး)
            title_lines = textwrap.wrap(song.title, width=20)
            curr_y = 270
            for line in title_lines[:2]:
                draw.text((tx_start, curr_y), line, font=self.font_title, fill="white")
                curr_y += 75

 # Progress Bar
            bar_y = 500
            bar_w = 550 # Bar ကို ပိုရှည်လိုက်သည်
            draw.rounded_rectangle((tx_start, bar_y, tx_start + bar_w, bar_y + 12), 6, fill=(100, 100, 100, 150))
            draw.rounded_rectangle((tx_start, bar_y, tx_start + (bar_w * 0.5), bar_y + 12), 6, fill=(255, 200, 50))

            # Controls (အကြီးကြီး)
            ctrl_y = 580
            draw.text((tx_start + 100, ctrl_y), "<<", font=self.font_title, fill="white", anchor="ma")
            draw.text((tx_start + 275, ctrl_y), "||", font=self.font_title, fill="white", anchor="ma")
            draw.text((tx_start + 450, ctrl_y), ">>", font=self.font_title, fill="white", anchor="ma")

            # Bottom Credit
            draw.text((self.size[0]//2, self.size[1] - 60), "Credit by @HANTHAR999", font=self.font_credit, fill="white", anchor="ma")

            bg.save(output, "PNG")
            return output

        except Exception as e:
            print(f"Error: {e}")
            return config.DEFAULT_THUMB
