from core.classes import Cog_Extension
from discord.ext import commands
from discord import app_commands
import json
import random as rd
from datetime import datetime

with open("config.json", "r", encoding="utf8") as jfile:
    jdata = json.load(jfile)

admin = int(jdata["roles"]["adminID"])


class Main(Cog_Extension):
    # say hi
    @commands.command()
    async def hi(self, ctx):
        await ctx.send("hi there!")

    @commands.command()
    async def hii(self, ctx):
        await ctx.send("hiiiiiii there!")

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello, world!")

    @commands.command(name="老師說", description="老師說")
    async def teacher_says(self, ctx):
        await ctx.message.delete()
        await ctx.send(rd.choice(jdata["teacherSays"]))

    @commands.command(name="分組")
    async def group(self, ctx):
        members = ctx.author.voice.channel.members

        rd.shuffle(members)

        channel1 = ctx.guild.get_channel(int(jdata["valorants"]["attackerChannelID"]))
        channel2 = ctx.guild.get_channel(int(jdata["valorants"]["defenderChannelID"]))

        for i, member in enumerate(members):
            if i % 2 == 0:
                await member.move_to(channel1)
            else:
                await member.move_to(channel2)

    @commands.command(name="時間戳")
    async def timestamp(self, ctx):
        # 轉換成 UTC+8 的時間戳
        await ctx.send(f"<t:{int(datetime.now().timestamp())}:R>")


async def setup(bot):
    await bot.add_cog(Main(bot))
