from core.get_config import bot_settings, set_config
from core.classes import Cog_Extension
from datetime import datetime
from discord import app_commands
import discord
import random as rd

class moraButton(discord.ui.View):
    def __init__(self, myself: discord.Member, competitor: discord.Member, db):
        super().__init__(timeout=180)
        self.myself = myself
        self.competitor = competitor
        self.choices = {myself: None, competitor: None}
        self.db = db

    @discord.ui.button(label="📄 Paper", style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "Paper", button)

    @discord.ui.button(label="✂️ Scissors", style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "Scissors", button)

    @discord.ui.button(label="🪨 Stone", style=discord.ButtonStyle.primary)
    async def stone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "Stone", button)

    @discord.ui.button(label="加分機制", style=discord.ButtonStyle.secondary)
    async def add_exp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("勝方 `+3 exp`，敗方 `+1 exp`，平手各 `+1 exp`", ephemeral=True)
        return

    async def handle_choice(self, interaction: discord.Interaction, choice: str, button: discord.ui.Button):
        # Check if the user is one of the participants
        if interaction.user not in self.choices:
            await interaction.response.send_message("這不是你的按鈕！", ephemeral=True)
            return

        # Check if the user has already made a choice
        if self.choices[interaction.user] is not None:
            await interaction.response.send_message("你已經選擇過了！", ephemeral=True)
            return

        # Disable all buttons after a choice is made
        for child in self.children:
            child.disabled = True

        # Record the user's choice
        self.choices[interaction.user] = choice
        await interaction.response.send_message(f"你選擇了 {choice}", ephemeral=True)

        # Check if both participants have made their choices
        if all(self.choices.values()):
            if not hasattr(self, "_result_sent"):  # Ensure result is sent only once
                self._result_sent = True
                result = self.determine_winner()
                await interaction.followup.send(result)
                self.stop()
        else:
            await interaction.response.send_message("等待對手選擇...", ephemeral=True)

    def determine_winner(self):
        # Extract choices
        choice1 = self.choices[self.myself]
        choice2 = self.choices[self.competitor]

        # Determine the result
        if choice1 == choice2:
            self.update_exp(self.myself, 1)
            self.update_exp(self.competitor, 1)
            self.record_result(self.myself, self.competitor, "draw")
            return f"平手！雙方都選擇了 {choice1}！"
        elif (choice1 == "Paper" and choice2 == "Stone") or \
             (choice1 == "Scissors" and choice2 == "Paper") or \
             (choice1 == "Stone" and choice2 == "Scissors"):
            self.update_exp(self.myself, 3)
            self.update_exp(self.competitor, 1)
            self.record_result(self.myself, self.competitor, "win")
            return f"{self.myself.mention}: {choice1} 打敗了 {self.competitor.mention}: {choice2}"
        else:
            self.update_exp(self.competitor, 3)
            self.update_exp(self.myself, 1)
            self.record_result(self.myself, self.competitor, "lose")
            return f"{self.competitor.mention} 獲勝！{choice2} 打敗了 {choice1}！"

    def update_exp(self, user, exp):
        try:
            # 確保使用者存在於 users 表
            self.db.cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user.id,))
            if not self.db.cursor.fetchone():
                self.db.cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user.id, user.name))
                self.db.conn.commit()
            # 更新經驗值
            self.db.cursor.execute('UPDATE users SET exp = exp + ? WHERE user_id = ?', (exp, str(user.id)))
            self.db.conn.commit()
        except Exception as e:
            print(f"Failed to update exp for user {user.id}: {e}")
    def record_result(self, winner, loser, result):
        try:
            # 確保贏家存在於 users 表
            self.db.cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (winner.id,))
            if not self.db.cursor.fetchone():
                self.db.cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (winner.id, winner.name))
                self.db.conn.commit()

            # 確保輸家存在於 users 表
            self.db.cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (loser.id,))
            if not self.db.cursor.fetchone():
                self.db.cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (loser.id, loser.name))
                self.db.conn.commit()

            # 紀錄結果
            self.db.cursor.execute('INSERT INTO rps_record (builder_id, receiver_id, date, result) VALUES (?, ?, ?, ?)',
                                    (str(winner.id), str(loser.id), datetime.now(), result))
            self.db.conn.commit()
        except Exception as e:
            print(f"Failed to record result: {e}")

class slashCommands(Cog_Extension):
    def __init__(self, bot):
        self.bot = bot
        self.client_logger = bot.client_logger
        self.db = bot.db

    # ping
    @app_commands.command(name="ping", description="return bot leatency")
    async def ping(self, interaction: discord.Interaction):
        # 檢查是否有管理員權限
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("您沒有權限使用這個指令。", ephemeral=True)
            return
        await interaction.response.send_message(f"The Bot Latency: `{round(self.bot.latency * 1000)}ms`")

    # kick user
    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.describe(member="The member to kick")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        # 檢查是否有管理員權限
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("您沒有權限使用這個指令。", ephemeral=True)
            return

        # 檢查是否有足夠的權限踢出指定用戶
        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message("我沒有足夠的權限來踢出這個成員。", ephemeral=True)
            return

        # 踢出成員
        await member.kick(reason=reason)
        await interaction.response.send_message(f"已經踢出 {member.mention}。")

    # ban user
    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.describe(member="The member to ban")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        # 檢查是否有管理員權限
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("您沒有權限使用這個指令。", ephemeral=True)
            return

        # 檢查是否有足夠的權限封鎖指定用戶
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("我沒有足夠的權限來封鎖這個成員。", ephemeral=True)
            return

        # 封鎖成員
        await member.ban(reason=reason)
        await interaction.response.send_message(f"已經封鎖 {member.mention}。")

    # set welcome channel
    settings_command = app_commands.Group(name="settings", description="Bot settings commands")
    @settings_command.command(name="welcome", description="Set welcome channel")
    @app_commands.describe(channel="The channel to set as welcome channel")
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # 檢查是否有管理員權限
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("您沒有權限使用這個指令。", ephemeral=True)
            return

        # 設定歡迎頻道
        bot_settings["guilds"]["welcomeChannelID"] = str(channel.id)
        # 儲存設定到檔
        set_config(bot_settings)
        await interaction.response.send_message(f"已經設定歡迎頻道為 {channel.mention}。")
    
    @settings_command.command(name="leave", description="Set leave channel")
    @app_commands.describe(channel="The channel to set as leave channel")
    async def set_leave_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # 檢查是否有管理員權限
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("您沒有權限使用這個指令。", ephemeral=True)
            return

        # 設定離開頻道
        bot_settings["guilds"]["leaveChannelID"] = str(channel.id)
        # 儲存設定到檔案
        set_config(bot_settings)
        await interaction.response.send_message(f"已經設定離開頻道為 {channel.mention}。")

    @app_commands.command(name="特戰隨機地圖", description="特戰隨機地圖")
    async def random_valorant_map(self, interaction: discord.Interaction):
        await interaction.response.send_message("抽到的地圖是：" + rd.choice(bot_settings["valorants"]["maps"]))

    @app_commands.command(name="特戰隨機角色", description="特戰隨機角色")
    async def random_valorant_agent(self, interaction: discord.Interaction):
        await interaction.response.send_message("抽到的角色是：" + rd.choice(bot_settings["valorants"]["agents"]))

    @app_commands.command(name="語音頻道隨機使用者", description="語音頻道隨機使用者")
    async def random_voice_channel_user(self, interaction: discord.Interaction):
        # 檢查是否在語音頻道
        if interaction.user.voice is None:
            await interaction.response.send_message("您不在任何語音頻道中。", ephemeral=True)
            return

        # 隨機選擇一個使用者
        user = rd.choice(interaction.user.voice.channel.members)
        await interaction.response.send_message(f":index_pointing_at_the_viewer: 就決定是你了：{user.mention}")
    
    # 今日運勢
    @app_commands.command(name="今日運勢", description="今日運勢")
    async def fortune(self, interaction: discord.Interaction):
        today = str(datetime.today().strftime("%Y-%m-%d"))
        user_id = str(interaction.user.id)
        username = str(interaction.user.name)

        try:
            # 確保使用者存在於 users 表
            self.db.cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            if not self.db.cursor.fetchone():
                self.db.cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))

            # 檢查今天是否已經獲得運勢
            self.db.cursor.execute('SELECT 1 FROM fortune_record WHERE user_id = ? AND date = ?', (user_id, today))
            if self.db.cursor.fetchone():
                await interaction.response.send_message("您今天已經使用過今日運勢了，請明天再來！", ephemeral=True)
                return

            # 紀錄運勢
            if bot_settings.get("fortune") is None or bot_settings["fortune"].get("fortunes") is None:
                await interaction.response.send_message("運勢設定不存在，請聯繫管理員。", ephemeral=True)
                return
            fortune = rd.choice(bot_settings["fortune"]["fortunes"])
            self.db.cursor.execute('INSERT INTO fortune_record (user_id, date, fortune) VALUES (?, ?, ?)', (user_id, today, fortune["name"]))
            # 更新經驗值
            self.db.cursor.execute('UPDATE users SET exp = exp + ? WHERE user_id = ?', (int(fortune["exp"]), user_id))
            self.db.conn.commit()
            await interaction.response.send_message(f"今日運勢：{fortune["name"]}，獲得經驗值：{fortune["exp"]} 點。")
            self.client_logger.info(f"[指令今日運勢] 使用者 {username} ({user_id}) 獲得運勢：{fortune['name']}，經驗值：{fortune['exp']}")
        except Exception as e:
            await interaction.response.send_message(f"今日運勢獲取失敗：請告知 bot 管理者", ephemeral=True)
            self.client_logger.error(f"[指令今日運勢] 獲得運勢失敗：{str(e)}")

    # 簽到
    @app_commands.command(name="簽到", description="簽到")
    async def sign_in(self, interaction: discord.Interaction):
        today = str(datetime.today().strftime("%Y-%m-%d"))
        user_id = str(interaction.user.id)
        username = str(interaction.user.name)

        try:
            # 確保使用者存在於 users 表
            self.db.cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            if not self.db.cursor.fetchone():
                self.db.cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))

            # 檢查今天是否已簽到
            self.db.cursor.execute('SELECT 1 FROM sign_in_records WHERE user_id = ? AND date = ?', (user_id, today))
            if self.db.cursor.fetchone():
                await interaction.response.send_message("您今天已經簽到過了，請明天再來！", ephemeral=True)
                return

            # 插入簽到紀錄
            self.db.cursor.execute('INSERT INTO sign_in_records (user_id, date) VALUES (?, ?)', (user_id, today))
            # 更新簽到次數
            self.db.cursor.execute('UPDATE users SET sign_in_count = sign_in_count + 1 WHERE user_id = ?', (user_id,))
            # 獲得經驗
            self.db.cursor.execute('UPDATE users SET exp = exp + 5 WHERE user_id = ?', (user_id,))
            self.db.conn.commit()
            await interaction.response.send_message("簽到成功！您獲得了 5 點經驗值。")
        except Exception as e:
            await interaction.response.send_message(f"簽到失敗：請告知 bot 管理者", ephemeral=True)
            self.client_logger.error(f"[指令簽到] 簽到失敗：{str(e)}")

    # 取得使用者資訊
    @app_commands.command(name="使用者資訊", description="取得使用者資訊")
    async def user_info(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        username = str(interaction.user.name)

        try:
            # 確保使用者存在於 users 表
            self.db.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user_data = self.db.cursor.fetchone()
            if not user_data:
                self.db.cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
                self.db.conn.commit()

            # 取得使用者資訊
            user_info = {
                "user_id": user_data[0],
                "username": user_data[1],
                "sign_in_count": user_data[2],
                "exp": user_data[3]
            }
            print(user_info)
            await interaction.response.send_message(f"使用者資訊：\n使用者名稱: {user_info['username']}\n簽到次數: {user_info['sign_in_count']}\n經驗值: {user_info['exp']}")
            self.client_logger.info(f"[指令使用者資訊] 使用者 {username} ({user_id}) 取得使用者資訊：{user_info}")
        except Exception as e:
            await interaction.response.send_message(f"取得使用者資訊失敗：請告知 bot 管理者", ephemeral=True)
            self.client_logger.error(f"[指令使用者資訊] 取得使用者資訊失敗：{str(e)}")
    
    # 猜拳
    @app_commands.command(name="猜拳", description="猜拳")
    @app_commands.describe(competitor="The competitor to play with")
    async def mora(self, interaction: discord.Interaction, competitor: discord.Member):
        view = moraButton(myself=interaction.user, competitor=competitor, db=self.db)
        await interaction.response.send_message(f"{interaction.user.mention} 與 {competitor.mention} 開始猜拳！", view=view)

async def setup(bot):
    await bot.add_cog(slashCommands(bot))
