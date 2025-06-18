import hikari.messages
import lightbulb
import hikari

quote = lightbulb.Loader()

@quote.command
class Quote(
    lightbulb.MessageCommand,
    name="引言",
    description="引用指定頻道中的消息",
):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """Quotes a message from a specified channel."""
        await ctx.defer()

        # 檢查是否有文字
        if not self.target.content:
            await ctx.respond("請選擇一條消息來引用。", ephemeral=True)
            return

        # 引用消息
        message = self.target.content
        author = self.target.author

        from PIL import Image, ImageFont, ImageDraw
        import os
        import io
        import textwrap
        import requests

        bg_image = str(author.display_avatar_url)

        if bg_image is None:
            bg_image = os.path.join(os.path.dirname(__file__), "headshot.jpg")

        width, height = 800, 600

        try:
            # Check if the path is a URL (starts with http:// or https://)
            if bg_image.startswith(('http://', 'https://')):
                # Download the image from URL
                response = requests.get(bg_image, stream=True)
                response.raise_for_status()  # Raise an exception for bad responses
                
                # Open the image from the response content
                avatar = Image.open(io.BytesIO(response.content))
            else:
                # Open from local file path
                avatar = Image.open(bg_image)
                
            # Create a black background
            image = Image.new('RGB', (width, height), color=(0, 0, 0))
            
            # Resize avatar to 600x600 (1:1 ratio, height of the image)
            avatar = avatar.resize((600, 600))
            
            # Create gradient from right (black) to left (transparent)
            gradient = Image.new('RGBA', (600, 600), (0, 0, 0, 0))
            for x in range(600):
                alpha = int((x / 600) * 255)  # Gradient from 0 (transparent) to 255 (opaque)
                for y in range(600):
                    gradient.putpixel((x, y), (0, 0, 0, alpha))
            
            # Apply gradient overlay to avatar
            avatar = avatar.convert('RGBA')
            avatar = Image.alpha_composite(avatar, gradient)
            
            # Paste avatar on the left side (0, 0)
            image.paste(avatar, (0, 0))
            
            # Convert to RGBA for overlay effects on the avatar portion only
            image = image.convert("RGBA")
            
            # Add semi-transparent overlay only on the avatar area for text readability
            overlay = Image.new('RGBA', (600, height), (0, 0, 0, 160))  # 160 for ~60% opacity
            image.paste(overlay, (0, 0), overlay)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            # Fallback to black background
            image = Image.new('RGB', (width, height), color=(0, 0, 0))

        draw = ImageDraw.Draw(image)

        # 載入字體（調整字體文件的路徑）
        try:
            quote_font = ImageFont.truetype("LXGWWenKaiMonoTC-Regular.ttf", 48, encoding="unic")
            author_font = ImageFont.truetype("LXGWWenKaiMonoTC-Regular.ttf", 32, encoding="unic")
        except IOError:
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
            print("由於載入自定義字體時出錯，使用默認字體。")

        # 文字換行處理
        margin = 60

        # 處理中文文字的換行
        if any('\u4e00' <= char <= '\u9fff' for char in message):  # 檢查是否包含中文
            # 中文字符寬度大致相同，所以可以按字符數量計算
            chars_per_line = 15
            word_list = [message[i:i+chars_per_line] for i in range(0, len(message), chars_per_line)]
        else:
            # 英文文字換行
            wrapper = textwrap.TextWrapper(width=30)
            word_list = wrapper.wrap(text=message)
        
        quote_text = '\n'.join(word_list)
        
        # 計算文字尺寸以進行右對齊
        # 針對不同 PIL 版本調整文字測量方法
        try:
            # 較新的 PIL 版本
            text_width = max([draw.textlength(line, font=quote_font) for line in word_list])
        except AttributeError:
            # 較舊的 PIL 版本
            text_width = max([quote_font.getmask(line).getbbox()[2] for line in word_list])
        
        # 計算右對齊文字的 x 座標
        y_position = height // 2 - len(word_list) * 30
        x_position = width - margin - text_width
        
        # 繪製引言（帶引號）
        quote_with_marks = f'"{quote_text}"'
        draw.text(
            (x_position, y_position),
            quote_with_marks,
            font=quote_font,
            fill=(255, 255, 255, 255)
        )
        
        # 繪製作者名稱
        author_text = f"- {author.display_name}"
        try:
            author_width = draw.textlength(author_text, font=author_font)
        except AttributeError:
            author_width = author_font.getmask(author_text).getbbox()[2]
        draw.text(
            (width - margin - author_width, y_position + len(word_list) * 60 + 20),
            author_text,
            font=author_font,
            fill=(200, 200, 200, 255)
        )

        image = image.convert("RGB")  # 確保圖像是 RGB 模式以便保存為 JPEG

        # Convert PIL image to discord file
        import io
        with io.BytesIO() as image_binary:
            image.save(image_binary, 'PNG')
            image_binary.seek(0)

            await ctx.respond(hikari.Bytes(image_binary, 'quote.png'))

