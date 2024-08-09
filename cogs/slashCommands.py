from core.classes import Cog_Extension
from discord import app_commands
from discord.ext import commands
import discord
import random as rd


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
    @discord.app_commands.command(name="kick", description="Kick a member")
    @discord.app_commands.describe(member="The member to kick")
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
    @discord.app_commands.command(name="ban", description="Ban a member")
    @discord.app_commands.describe(member="The member to ban")
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


async def setup(bot):
    await bot.add_cog(slashCommands(bot))
