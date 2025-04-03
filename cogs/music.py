import discord
from discord import app_commands
from discord.ext import commands
import random as rd
import yt_dlp
import asyncio

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 0",
    "options": "-vn"
}

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "skip_download": True,
    "force_generic_extractor": False,
    "geo_bypass": True,  # 繞過地理限制
    "ignoreerrors": True,  # 忽略部分錯誤
}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.timer_task = None
        self.state = None
        self.song_source = tuple()
        self.playing_song = None
        self.is_playing_next = False
        self.leave_words = [
            "五分鐘了，沒人使用我，有點空虛，T_T 掰掰",
            "已經五分鐘了，還不聽歌？先下了",
            "三小，不會讓我直接離開嗎？硬要讓等時間過了才讓我退出，還是你喜歡我？",
            "雖然捨不得，但我還是得走了",
        ]


    async def start_leave_timer(self, interaction):
        # 取消現有的計時器（如果有的話）
        if self.timer_task:
            self.timer_task.cancel()

        # 創建新的計時器
        self.timer_task = asyncio.create_task(self.leave_after_delay(interaction))


    def reset_timer(self, interaction=None):
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None


    @app_commands.command(name="單曲循環", description="單曲循環")
    async def loop(self, interaction: discord.Interaction):
        if not hasattr(self, "playing_song"):
            await interaction.response.send_message(":warning: 目前沒有正在播放的歌曲！")
            return
        self.state = "loop"
        await interaction.response.send_message(":repeat: 已設定為單曲循環模式！")


    @app_commands.command(name="正常播放", description="正常播放")
    async def normal(self, interaction: discord.Interaction):
        self.state = None
        await interaction.response.send_message(":arrow_forward: 已設定為正常播放模式！")


    # 播放狀態
    @app_commands.command(name="播放狀態", description="顯示播放狀態")
    async def status(self, interaction: discord.Interaction):
        if self.state == "loop":
            await interaction.response.send_message(":repeat: 目前為單曲循環模式！")
        else:
            await interaction.response.send_message(":arrow_forward: 目前為正常播放模式！")

    # 播放音樂
    @app_commands.command(name="播放音樂", description="播放音樂")
    @app_commands.describe(url_or_query="YouTube 影片網址或搜尋詞")
    async def play(self, interaction: discord.Interaction, url_or_query: str):
        await interaction.response.defer()

        # 檢查使用者是否在語音頻道中
        if interaction.user.voice is None:
            await interaction.followup.send(":warning: 你必須先加入一個語音頻道！")
            return
        
        # 檢查機器人是否在語音頻道中
        voice_channel = interaction.user.voice.channel
        if voice_channel is None:
            await interaction.followup.send(":warning: 你必須先加入一個語音頻道！")
            return
        
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        if not url_or_query.startswith("https"):
            url_or_query = f"ytsearch1:{url_or_query}"

        async with interaction.channel.typing():
            try:
                loop = asyncio.get_event_loop()

                # 在背景執行 yt_dlp 以避免阻塞
                extract_func = lambda: self._extract_info(url_or_query)
                info_dict = await loop.run_in_executor(None, extract_func)

                if info_dict is None:
                    await interaction.followup.send(f":x: 無法找到歌曲：`{url_or_query}`")
                    return

                # 處理搜尋結果
                if "entries" in info_dict:
                    info = info_dict["entries"][0]
                else:
                    info = info_dict

                # 取得最佳音訊 URL
                title = info.get("title", "未知標題")
                audio_url = info.get("url", None)
                original_url = info.get("original_url", url_or_query)

                if not audio_url:
                    await interaction.followup.send(f":x: 無法獲取音訊源：`{title}`")
                    return
                
                song = (audio_url, title, original_url)
                self.queue.append(song)

                if len(self.queue) == 1 and not hasattr(self, "playing_song"):
                    self.playing_song = song

                await interaction.followup.send(f":white_check_mark: 新增歌曲：`{title}`")
            except Exception as e:
                print(f"Error fetching song info: {str(e)}")
                await interaction.followup.send(f":x: 無法播放歌曲：`{url_or_query}`。錯誤：{str(e)}")
                return

        if not voice_client.is_playing():
            await self.play_next(interaction)

        # Reset the timer when a new song is added
        self.reset_timer(interaction)

    # 提取音訊信息
    def _extract_info(self, url_or_query):
        """在非異步環境中提取信息"""
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url_or_query, download=False)
                print(f"成功提取信息，類型: {type(info)}")
                return info
        except Exception as e:
            print(f"yt_dlp 提取錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def play_next(self, interaction):
        if self.is_playing_next:
            return

        self.is_playing_next = True

        if not hasattr(self, "playing_song") and not self.queue:
            await interaction.channel.send(":warning: 沒有歌曲在佇列中！")
            await self.start_leave_timer(interaction)  # 開始計時
            self.is_playing_next = False
            return

        # 重置計時器
        self.reset_timer(interaction)

        if self.state != "loop" or not hasattr(self, "playing_song"):
            if self.queue:
                self.playing_song = self.queue.pop(0)
            else:
                await interaction.channel.send(":warning: 佇列中沒有更多歌曲！")
                await self.start_leave_timer(interaction)  # 開始計時
                self.is_playing_next = False
                return

        audio_url, title, original_url = self.playing_song

        try:
            print(f"正在嘗試播放：{title}")
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
                audio_url, 
                **FFMPEG_OPTIONS
            ))
            source.volume = 1.0
            print("音訊源創建成功")
        except Exception as e:
            print(f"無法創建音訊源: {str(e)}")
            # 嘗試重新提取音訊源
            try:
                print("嘗試重新擷取音訊源...")
                
                # 直接使用 yt_dlp 而不是調用方法
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info_dict = ydl.extract_info(original_url, download=False)
                
                if info_dict:
                    if "entries" in info_dict and info_dict["entries"]:
                        info = info_dict["entries"][0]
                    else:
                        info = info_dict
                    
                    new_url = info.get("url")
                    if new_url:
                        self.playing_song = (new_url, title, original_url)
                        print(f"重新擷取音訊成功: {new_url[:30] if len(new_url) > 30 else new_url}...")
                    else:
                        print("無法重新擷取有效的音訊 URL")
                        self.is_playing_next = False
                        await self.play_next(interaction)
                        return
                else:
                    print("重新擷取音訊失敗")
                    self.is_playing_next = False
                    await self.play_next(interaction)
                    return
                
                # 使用新的 URL 再次嘗試
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
                    self.playing_song[0],
                    **FFMPEG_OPTIONS
                ))
                source.volume = 1.0
                print("使用新 URL 創建音訊源成功")
            except Exception as e:
                print(f"第二次嘗試創建音訊源失敗: {str(e)}")
                self.is_playing_next = False
                await self.play_next(interaction)
                return

        def after_playing(error):
            if error:
                print(f"播放錯誤: {error}")
            else:
                print("歌曲正常結束播放")
            # 使用更安全的方式調用下一首歌
            try:
                self.is_playing_next = False
                self.bot.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.play_next(interaction))
                )
            except Exception as e:
                print(f"調用下一首歌時出錯: {e}")
                self.is_playing_next = False

        if interaction.guild.voice_client:
            try:
                interaction.guild.voice_client.play(source, after=after_playing)
                if self.state != "loop":
                    asyncio.create_task(interaction.channel.send(
                        f":musical_note: 正在播放：`{title}`"
                    ))
            except Exception as e:
                print(f"播放歌曲時發生錯誤: {e}")
                self.is_playing_next = False
                await self.play_next(interaction)
                return
        else:
            print("Voice client 不存在，無法播放")
            self.is_playing_next = False
            return

        self.is_playing_next = False

    # 目前歌曲資訊
    @app_commands.command(name="目前歌曲資訊", description="顯示目前播放的歌曲資訊")
    async def current(self, interaction: discord.Interaction):
        if hasattr(self, "playing_song"):
            _, title, original_url = self.playing_song
            await interaction.response.send_message(
                f":musical_note: 目前播放：`{title}`\n:link: URL: {original_url}"
            )
        else:
            await interaction.response.send_message(":warning: 目前沒有歌曲在播放。")


    # 跳過當前歌曲
    @app_commands.command(name="跳過當前歌曲", description="跳過當前歌曲")
    async def skip(self, interaction: discord.Interaction):
        if (
            interaction.guild.voice_client
            and interaction.guild.voice_client.is_playing()
        ):
            interaction.guild.voice_client.stop()
            if self.state == "loop":
                self.state = None  # 退出循環模式
            await interaction.response.send_message(":track_next: 已跳過當前歌曲！")
        else:
            await interaction.response.send_message(":warning: 目前沒有歌曲在播放。")


    # 顯示音樂佇列
    @app_commands.command(name="顯示音樂佇列", description="顯示音樂佇列")
    async def queue(self, interaction: discord.Interaction):
        if not self.queue:
            await interaction.response.send_message(":warning: 沒有歌曲在佇列中！")
            return
        try:
            embed = discord.Embed(title="音樂佇列", color=discord.Color.blurple())
            for i, (sound_source, title, original_url) in enumerate(self.queue):
                embed.add_field(name=f"{i+1}. `{title}`", value=original_url, inline=False)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error sending queue embed: {str(e)}")
            await interaction.response.send_message(f"顯示佇列時發生錯誤：{str(e)}")


    # 暫停當前歌曲
    @app_commands.command(name="暫停當前歌曲", description="暫停當前歌曲")
    async def pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.pause()
                await interaction.response.send_message(":pause_button: 音樂已暫停。")
                self.reset_timer(interaction)  # 重置計時器
            else:
                await interaction.response.send_message(":warning: 目前沒有音樂在播放。")
        else:
            await interaction.response.send_message(":warning: 我沒有連接到任何語音頻道。")


    @app_commands.command(name="繼續播放", description="恢復播放暫停的歌曲")
    async def resume(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.is_paused():
                interaction.guild.voice_client.resume()
                await interaction.response.send_message(":arrow_forward: 音樂已恢復播放。")
            else:
                await interaction.response.send_message(":warning: 音樂沒有被暫停。")
        else:
            await interaction.response.send_message(":warning: 我沒有連接到任何語音頻道。")


    # 離開語音頻道
    @app_commands.command(name="離開語音頻道", description="離開語音頻道")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            self.queue.clear()
            await interaction.response.send_message(":warning: 已離開語音頻道！")
        else:
            await interaction.response.send_message(":warning: 我沒有連接到任何語音頻道。")


    # 無人使用時離開
    async def leave_after_delay(self, interaction):
        try:
            await asyncio.sleep(300)  # 5 minutes
            if interaction.guild.voice_client:
                if not interaction.guild.voice_client.is_playing() and not self.queue:
                    await interaction.guild.voice_client.disconnect()
                    await interaction.channel.send(
                        f":zzz: {rd.choice(self.leave_words)}"
                    )
                    self.queue.clear()
                    if hasattr(self, "playing_song"):
                        delattr(self, "playing_song")
        except asyncio.CancelledError:
            pass  # 計時器被取消時不做任何事
        finally:
            self.timer_task = None


async def setup(bot):
    await bot.add_cog(Music(bot))
