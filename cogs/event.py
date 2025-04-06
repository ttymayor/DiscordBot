from core.classes import Cog_Extension
from core.get_config import bot_settings
from discord.ext import commands
import random as rd
import datetime
import discord

# 冷卻時間紀錄
last_used = {}

# gg/ff... 訊息 list
gg_list = ["gg", "go next", "noob", "ez", "──────▄▌▐▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▌\n───▄▄██▌█ BEEP BEEP\n▄▄▄▌▐██▌█ -22 RR DELIVERY\n███████▌█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▌\n▀(⊙)▀▀▀▀▀▀▀▀▀▀▀▀▀▀(⊙)(⊙)▀▀"]


class Event(Cog_Extension):
    def __init__(self, bot):
        self.bot = bot
        self.client_logger = bot.client_logger
        self.dynamic_channel_ids = []
        self.channel_creator = int(bot_settings["guilds"]["dynamicChannelCreatorID"])

    # welcome guild
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # 檢查是否有設定歡迎頻道
        if bot_settings.get("guilds") is None and bot_settings["guilds"].get("welcomeChannelID") is None:
            return

        if member.guild.id != int(bot_settings["guilds"]["guildID"]):
            return

        wel_channel = self.bot.get_channel(int(bot_settings["guilds"]["welcomeChannelID"]))
        await wel_channel.send(f"歡迎 {member.mention} 加入！")
        self.client_logger.info(f"歡迎 {member} 加入伺服器！")

    # leave guild
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # 檢查是否有設定離開頻道
        if bot_settings.get("guilds") is None and bot_settings["guilds"].get("leaveChannelID") is None:
            return

        if member.guild.id != int(bot_settings["guilds"]["guildID"]):
            return
        
        leave_channel = self.bot.get_channel(int(bot_settings["guilds"]["leaveChannelID"]))
        await leave_channel.send(f"{member.mention} 滾遠點")
        self.client_logger.info(f"{member} 離開伺服器！")

    # listen voice channel
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        # 檢查離開的頻道是否為專屬語音頻道，並且現在是空的
        if (before.channel and before.channel.members == [] and before.channel.id in self.dynamic_channel_ids):
            # 如果 after channel 是動態語音頻道，則拉回成員
            if after.channel and after.channel.id == self.channel_creator:
                await member.move_to(before.channel)
                self.client_logger.info(f"[語音事件] 將 @{member} 移回自己的頻道: \"{before.channel.name}\"")
                return

            if after.channel is not None:
                self.client_logger.info(f"[語音事件] @{member} 移動從 \"{before.channel}\" 到 \"{after.channel}\"")

            await before.channel.delete()
            self.client_logger.info(f"[語音事件] 刪除空的專屬語音頻道: \"{before.channel.name}\"")
            self.dynamic_channel_ids.remove(before.channel.id)

            return

        # 檢查是否加入動態語音頻道
        if after.channel and after.channel.id == self.channel_creator:
            channelCreator = self.bot.get_channel(self.channel_creator)
            if before.channel is not None:
                self.client_logger.info(f"[語音事件] @{member} 移動從 \"{before.channel}\" 到 \"{after.channel}\"")
            else:
                self.client_logger.info(f"[語音事件] @{member} 加入 \"{after.channel}\"")
            # 創建一個新的語音頻道，名稱為使用者名稱的頻道
            new_channel = await after.channel.guild.create_voice_channel(
                name=f"【{member.display_name}】的頻道",
                category=after.channel.category,
                rtc_region=after.channel.rtc_region,
            )
            self.client_logger.info(f"[語音事件] \"{channelCreator}\" 創建頻道: \"{new_channel.name}\"")
            # 將使用者移動到新創建的語音頻道
            await member.move_to(new_channel)
            self.dynamic_channel_ids.append(new_channel.id)
            self.client_logger.info(f"[語音事件] \"{channelCreator}\" 將 @{member} 移到自己的頻道: \"{new_channel.name}\"")
            return

        if before.channel is None and after.channel is not None:
            self.client_logger.info(f"[語音事件] @{member} 加入 \"{after.channel}\"")
        elif before.channel is not None and after.channel is None:
            self.client_logger.info(f"[語音事件] @{member} 離開 \"{before.channel}\"")
        else:
            if (before.channel == after.channel 
                or before.channel.id == self.channel_creator
                or after.channel.id in self.dynamic_channel_ids):
                return
            self.client_logger.info(f"[語音事件] @{member} 移動從 \"{before.channel}\" 到 \"{after.channel}\"")

    # QQ TT
    @commands.Cog.listener()
    async def on_message(self, msg):
        # 防止機器人自己觸發
        if msg.author == self.bot.user:
            return

        # 防洗頻
        user_id = msg.author.id
        now = datetime.datetime.now(datetime.timezone.utc)

        # 如果使用者不在字典中，則新增使用者，並設定上次使用時間為 1 分鐘前
        if user_id not in last_used:
            last_used[user_id] = now - datetime.timedelta(minutes=1)

        # 計算時間差
        time_since_last_message = now - last_used[user_id]

        # 如果時間差小於 15 秒，則回覆訊息
        if time_since_last_message < datetime.timedelta(seconds=5):
            return
        else:
            last_used[user_id] = now

        # 訊息偵測
        ## 如果不是連結
        if "http" not in msg.content:
            message = msg.content.lower()
            # 如果訊息長度大於 10
            if msg.content.startswith("<:"):
                if "wa3" in msg.content:
                    await msg.channel.send("<:wa3:1266342747313274891>")
            elif message == "?" or message == "？":
                await msg.channel.send(message)
            elif message == "6":
                await msg.channel.send("6")
            elif message == "qq":
                await msg.channel.send("幫 QQ")
            elif message == "tt":
                await msg.channel.send("幫 TT")
            elif message == "nt":
                await msg.channel.send(rd.choice(["nice try", "奶頭"]))
            elif message == "ff" or message == "gg" or message == "ez" or message == "noob" or message == "go next":
                # 機率回覆 50%
                for _ in range(rd.randint(1, 3)):
                    await msg.channel.send(rd.choice(gg_list))

        if self.bot.user.mentioned_in(msg):
            await msg.channel.send(rd.choice(["標三小啦，耖", "媽的標什麼標", "我有允許你標我嗎？", "到底是在靠杯三小啦", "吵什麼吵低能"]))

async def setup(bot):
    await bot.add_cog(Event(bot))
