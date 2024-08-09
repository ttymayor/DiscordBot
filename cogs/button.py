from discord.ext import commands
from discord.ui import Button, View
from core.classes import Cog_Extension
import random as rd
import discord
import json

with open("config.json", "r", encoding="utf8") as jfile:
    jdata = json.load(jfile)


class JoinParty(Button):
    def __init__(self, label: str, *args, **kwargs):
        super().__init__(label=label, *args, **kwargs)
        self.player = []  # 將 set 改為 list

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.player:
            # 如果用戶已經按過按鈕，給予回應並不再進行後續操作
            await interaction.response.send_message("你按過了！", ephemeral=True)
        else:
            # 在這裡記錄按下按鈕的用戶
            print(f"{interaction.user} 按下了按鈕")
            self.player.append(user_id)  # 使用 append 方法加入 list
            # print(self.player)
            # 給予用戶回應，確認他們的操作
            await interaction.response.send_message(
                "成功加入分隊系統！", ephemeral=True
            )

            # 更新按鈕狀態
            await interaction.message.edit(view=self.view)


class EndParty(Button):
    def __init__(self, label: str, user_id: int, *args, **kwargs):
        super().__init__(label=label, *args, **kwargs)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        # 檢查互動的用戶是否是發起指令的用戶
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "只有發起指令的用戶可以使用這個按鈕。", ephemeral=True
            )
            return
        # 獲取 JoinParty 按鈕實例中的 player 列表
        players = self.view.children[
            0
        ].player  # 假設 JoinParty 按鈕是 view 中的第一個元素
        if not players:
            await interaction.response.send_message(
                "目前沒有玩家加入！", ephemeral=True
            )
            return

        # 打亂玩家順序
        rd.shuffle(players)

        # 平分玩家到兩個語音頻道
        half = len(players) // 2
        attacker = players[:half]
        defender = players[half:]

        # 假設你已經有兩個語音頻道的 ID
        attacker_channel = int(jdata["valorants"]["attackerChannelID"])
        defender_channel = int(jdata["valorants"]["defenderChannelID"])

        guild = interaction.guild
        for index, user_id in enumerate(attacker):
            member = guild.get_member(user_id)
            if member:
                try:
                    await member.move_to(
                        discord.utils.get(guild.voice_channels, id=attacker_channel)
                    )
                except discord.HTTPException as e:
                    print(f"無法移動 {member.name}: {e}")

        for index, user_id in enumerate(defender):
            member = guild.get_member(user_id)
            if member:
                try:
                    await member.move_to(
                        discord.utils.get(guild.voice_channels, id=defender_channel)
                    )
                except discord.HTTPException as e:
                    print(f"無法移動 {member.name}: {e}")

        await interaction.response.send_message(
            "玩家已經被平分到兩個語音頻道！", ephemeral=True
        )

        # 清空 player 列表
        self.view.children[0].player.clear()
        # 刪除訊息
        await interaction.message.delete()


class ButtonCog(Cog_Extension):

    @discord.app_commands.command(name="特戰分隊", description="特戰分隊")
    async def party(self, interaction: discord.Interaction):
        join_button = JoinParty(label="點我加入分隊", style=discord.ButtonStyle.primary)
        end_button = EndParty(
            label="結束並分隊",
            user_id=interaction.user.id,
            style=discord.ButtonStyle.danger,
        )
        view = View()
        view.add_item(join_button)
        view.add_item(end_button)
        await interaction.response.send_message("點擊下面的按鈕", view=view)


async def setup(bot):
    await bot.add_cog(ButtonCog(bot))
    # 如果你需要將這個命令限制在特定的 guild 中，可以使用以下代碼
    # guild_id = discord.Object(id=你的guild_id)
    # bot.tree.add_command(ButtonCog.show_button, guild=guild_id)
