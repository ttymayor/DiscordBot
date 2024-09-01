import discord
from discord import app_commands
from discord.ext import commands
import random as rd
import yt_dlp
import asyncio

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}
YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.timer_task = None
        # 離開詞
        self.leave_words = [
            "五分鐘了，沒人使用我，有點空虛，T_T 掰掰", 
            "已經五分鐘了，還不聽歌？先下了",
            "三小，不會讓我直接離開嗎？硬要讓等時間過了才讓我退出，還是你喜歡我？",
            "雞雞"
        ]

    @app_commands.command(name="播放音樂", description="播放音樂")
    @app_commands.describe(url="YouTube 影片網址或搜尋詞")
    async def play(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("你必須先加入一個語音頻道！")
            return

        # 如果輸入的不是網址，則搜尋
        if not url.startswith("http"):
            url = f"ytsearch:{url}"

        voice_channel = interaction.user.voice.channel
        if not interaction.guild.voice_client:
            await voice_channel.connect()

        # 下載音樂並加入佇列
        async with interaction.channel.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                sound_source = info["url"]
                title = info["title"]
                self.queue.append((sound_source, title, url))
                await interaction.followup.send(f"新增歌曲：**{title}**")

        # 如果當前沒有歌曲在播放，則播放下一首
        if not interaction.guild.voice_client.is_playing():
            await self.play_next(interaction)

    async def play_next(self, interaction):
        if self.queue:
            sound_source, title, url = self.queue[0]
            source = await discord.FFmpegOpusAudio.from_probe(sound_source, **FFMPEG_OPTIONS)
            self.queue.pop(0)
            interaction.guild.voice_client.play(
                source, after=lambda _: self.bot.loop.create_task(self.play_next(interaction))
            )
            await interaction.followup.send(f"正在播放：**{title}**")
        else:
            await interaction.followup.send("沒有歌曲在佇列中！")
            # 設置計時器，僅當佇列為空時
            if not self.timer_task:
                self.timer_task = self.bot.loop.create_task(self.leave_after_delay(interaction))

    @app_commands.command(name="跳過當前歌曲", description="跳過當前歌曲")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("已跳過當前歌曲！")
        else:
            await interaction.response.send_message("目前沒有歌曲在播放。")

    @app_commands.command(name="顯示音樂佇列", description="顯示音樂佇列")
    async def queue(self, interaction: discord.Interaction):
        if not self.queue:
            await interaction.response.send_message("沒有歌曲在佇列中！")
            return
        try:
            embed = discord.Embed(title="音樂佇列", color=discord.Color.blurple())
            for i, (sound_source, title, search) in enumerate(self.queue):
                embed.add_field(name=f"{i+1}. {title}", value=search, inline=False)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error sending queue embed: {str(e)}")
            await interaction.response.send_message(f"顯示佇列時發生錯誤：{str(e)}")

    @app_commands.command(name="暫停當前歌曲", description="暫停當前歌曲")
    async def pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.pause()
                await interaction.response.send_message("音樂已暫停。")
            else:
                await interaction.response.send_message("目前沒有音樂在播放。")
        else:
            await interaction.response.send_message("我沒有連接到任何語音頻道。")

    @app_commands.command(name="繼續播放", description="恢復播放暫停的歌曲")
    async def resume(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.is_paused():
                interaction.guild.voice_client.resume()
                await interaction.response.send_message("音樂已恢復播放。")
            else:
                await interaction.response.send_message("音樂沒有被暫停。")
        else:
            await interaction.response.send_message("我沒有連接到任何語音頻道。")

    @app_commands.command(name="離開語音頻道", description="離開語音頻道")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            self.queue.clear()
            await interaction.response.send_message("已離開語音頻道！")
        else:
            await interaction.response.send_message("我沒有連接到任何語音頻道。")

    async def leave_after_delay(self, interaction):
        await asyncio.sleep(300)  # 5 分鐘後
        if not interaction.guild.voice_client.is_playing():
            await interaction.guild.voice_client.disconnect()
            await interaction.followup.send(rd.choice(self.leave_words))
        self.timer_task = None  # 重置計時器任務

async def setup(bot):
    await bot.add_cog(Music(bot))
