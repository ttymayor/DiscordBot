from core.classes import Cog_Extension
from discord import app_commands
from discord.ext import commands
import discord
import random as rd
import json


with open("config.json", "r", encoding="utf8") as jfile:
    jdata = json.load(jfile)


class slashCommands(Cog_Extension):
    # ping
    @app_commands.command(name="ping", description="return bot leatency")
    async def ping(self, interaction: discord.Interaction):
        # 檢查是否有管理員權限
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "您沒有權限使用這個指令。", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"The Bot Latency: `{round(self.bot.latency * 1000)}ms`"
        )

    # kick user
    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.describe(member="The member to kick")
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = None,
    ):
        # 檢查是否有管理員權限
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(
                "您沒有權限使用這個指令。", ephemeral=True
            )
            return

        # 檢查是否有足夠的權限踢出指定用戶
        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message(
                "我沒有足夠的權限來踢出這個成員。", ephemeral=True
            )
            return

        # 踢出成員
        await member.kick(reason=reason)
        await interaction.response.send_message(f"已經踢出 {member.mention}。")

    # ban user
    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.describe(member="The member to ban")
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = None,
    ):
        # 檢查是否有管理員權限
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "您沒有權限使用這個指令。", ephemeral=True
            )
            return

        # 檢查是否有足夠的權限封鎖指定用戶
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message(
                "我沒有足夠的權限來封鎖這個成員。", ephemeral=True
            )
            return

        # 封鎖成員
        await member.ban(reason=reason)
        await interaction.response.send_message(f"已經封鎖 {member.mention}。")

    @app_commands.command(name="特戰隨機地圖", description="特戰隨機地圖")
    async def random_valorant_map(self, interaction: discord.Interaction):
        await interaction.response.send_message("抽到的地圖是：" + rd.choice(jdata["valorants"]["maps"]))

    @app_commands.command(name="特戰隨機角色", description="特戰隨機角色")
    async def random_valorant_agent(self, interaction: discord.Interaction):
        await interaction.response.send_message("抽到的角色是：" + rd.choice(jdata["valorants"]["agents"]))


async def setup(bot):
    await bot.add_cog(slashCommands(bot))
