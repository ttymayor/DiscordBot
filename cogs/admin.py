from core.get_config import bot_settings
from core.classes import Cog_Extension
from discord.ext import commands
from discord import app_commands
import discord

admin = int(bot_settings["roles"]["adminID"])

class Admin(Cog_Extension):
    # bot say
    @commands.command()
    @commands.has_role(admin)
    async def say(self, ctx, *, msg):
        await ctx.message.delete()
        await ctx.send(msg)

    # clear message
    @commands.command()
    @commands.has_role(admin)
    async def clean(self, ctx, num: int):
        await ctx.channel.purge(limit=num + 1)

    # bot say in specific channel
    @commands.command()
    @commands.has_role(admin)
    async def say_in(self, ctx, channel: discord.TextChannel, *, msg):
        await ctx.message.delete()
        await channel.send(msg)

    # ban user
    @commands.command()
    @commands.has_role(admin)
    async def ban(self, ctx, member: discord.Member, *, reason="無"):
        await member.ban(reason=reason)
        await ctx.send(f"{member} 已被封鎖")


async def setup(bot):
    await bot.add_cog(Admin(bot))
