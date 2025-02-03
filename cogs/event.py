from core.classes import Cog_Extension
from discord.ext import commands
import random as rd
import datetime
import discord
import json

with open("config.json", "r", encoding="utf8") as jfile:
    jdata = json.load(jfile)

# 冷卻時間紀錄
last_used = {}

# gg/ff... 訊息 list
gg_list = ["gg", "go next", "noob", "ez", "──────▄▌▐▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▌\n───▄▄██▌█ BEEP BEEP\n▄▄▄▌▐██▌█ -22 RR DELIVERY\n███████▌█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▌\n▀(⊙)▀▀▀▀▀▀▀▀▀▀▀▀▀▀(⊙)(⊙)▀▀"]


class Event(Cog_Extension):
    # welcome guild
    @commands.Cog.listener()
    async def on_member_join(self, member):
        wel_channel = self.bot.get_channel(int(jdata["guilds"]["welcomeChannelID"]))
        await wel_channel.send(f"歡迎 {member.mention} 加入！")

    # leave guild
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        leave_channel = self.bot.get_channel(int(jdata["guilds"]["leaveChannelID"]))
        await leave_channel.send(f"{member.mention} 滾遠點")

    # listen voice channel
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        # 檢查離開的頻道是否為專屬語音頻道，並且現在是空的
        if (
            before.channel
            and before.channel.members == []
            and before.channel.name.endswith("的頻道")
        ):
            # 如果 after channel 是動態語音頻道，則拉回成員
            if after.channel and after.channel.id == int(jdata["guilds"]["dynamicChannelID"]):
                await member.move_to(before.channel)
                print(f"Moved {member} back to their own channel: {before.channel.name}")
                return

            await before.channel.delete()
            print(f"Deleted empty custom channel: {before.channel.name}")
            return

        # 檢查是否加入了設定的動態語音頻道
        if after.channel and after.channel.id == int(
            jdata["guilds"]["dynamicChannelID"]
        ):
            # 創建一個新的語音頻道，名稱為使用者名稱的頻道
            new_channel = await after.channel.guild.create_voice_channel(
                name=f"【{member.display_name}】的頻道",
                category=after.channel.category,
                rtc_region=after.channel.rtc_region,
            )
            # 將使用者移動到新創建的語音頻道
            await member.move_to(new_channel)
            print(f"Created and moved {member} to their own channel: {new_channel.name}")
            return

        if before.channel is None and after.channel is not None:
            print(f"{member} join {after.channel}")
        elif before.channel is not None and after.channel is None:
            print(f"{member} leave {before.channel}")
        else:
            if before.channel == after.channel:
                return
            print(f"{member} move from {before.channel} to {after.channel}")

    # QQ TT
    @commands.Cog.listener()
    async def on_message(self, msg):
        # 防止機器人自己觸發
        if msg.author == self.bot.user:
            return

        # 防洗頻
        user_id = msg.author.id
        now = datetime.datetime.utcnow()

        # 如果使用者不在字典中，則新增使用者，並設定上次使用時間為 1 分鐘前
        if user_id not in last_used:
            last_used[user_id] = now - datetime.timedelta(minutes=1)

        # 計算時間差
        time_since_last_message = now - last_used[user_id]

        # 如果時間差小於 15 秒，則回覆訊息
        if time_since_last_message < datetime.timedelta(seconds=5):
            await msg.channel.send("請過", ephemeral=True)
            return
        else:
            last_used[user_id] = now

        # 訊息偵測
        ## 如果不是連結
        if "http" not in msg.content:
            # 訊息轉小寫
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
                for i in range(rd.randint(1, 3)):
                    await msg.channel.send(rd.choice(gg_list))

        if self.bot.user.mentioned_in(msg):
            await msg.channel.send("標三小啦，耖")

async def setup(bot):
    await bot.add_cog(Event(bot))
