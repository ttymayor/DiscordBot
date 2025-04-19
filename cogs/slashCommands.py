from core.get_config import bot_settings, set_config
from core.classes import Cog_Extension
from datetime import datetime
from discord import app_commands
import discord
import random as rd

class moraButton(discord.ui.View):
    def __init__(self, myself: discord.Member, competitor: discord.Member, db, client_logger):
        super().__init__(timeout=180)
        self.myself = myself
        self.competitor = competitor
        self.choices = {myself: None, competitor: None}
        self.db = db
        self.client_logger = client_logger

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
        await interaction.response.send_message("勝方 `+3 exp`，敗方 `-1 exp`", ephemeral=True)
        return
    
    @discord.ui.button(label="塊陶", style=discord.ButtonStyle.danger)
    async def rock_paper_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in [self.myself, self.competitor]:
            await interaction.response.send_message("這不是你的按鈕！", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"{interaction.user.mention} 按下了塊陶！")
        return

    async def handle_choice(self, interaction: discord.Interaction, choice: str, button: discord.ui.Button):
        # Check if the user is one of the participants
        if interaction.user not in self.choices:
            await interaction.response.send_message("這不是你的按鈕！", ephemeral=True)
            return

        # Check if the user has already made a choice
        if self.choices[interaction.user] is not None and self.choices[interaction.user] != choice:
            await interaction.response.send_message("你已經選擇過了！", ephemeral=True)
            return

        # Record the user's choice
        self.choices[interaction.user] = choice
        await interaction.response.send_message(f"你選擇了 {choice}", ephemeral=True)

        # if competitor is dcbot
        if bot_settings.get("botID") and str(self.competitor.id) == bot_settings["botID"]:
            bot_choice = rd.choice(["Paper", "Scissors", "Stone"])
            self.choices[self.competitor] = bot_choice
        else:
            bot_choice = None  # Ensure bot_choice is defined even if condition fails

        # Check if both participants have made their choices
        if all(self.choices.values()):
            # Disable all buttons after both participants have made their choices
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)  # Update the message to disable buttons

            if not hasattr(self, "_result_sent"):  # Ensure result is sent only once
                self._result_sent = True
                result, playAgainView = self.determine_winner()
                await interaction.followup.send(result, view=playAgainView)
                self.stop()
        else:
            await interaction.response.send_message("等待對手選擇...", ephemeral=True)

    def determine_winner(self):
        # Extract choices
        choice1 = self.choices[self.myself]
        choice2 = self.choices[self.competitor]

        # Determine the result
        if choice1 == choice2:
            self.record_result(self.myself, self.competitor, "draw")
            result_message = f"平手！雙方都選擇了 {choice1}！"
        elif (choice1 == "Paper" and choice2 == "Stone") or \
             (choice1 == "Scissors" and choice2 == "Paper") or \
             (choice1 == "Stone" and choice2 == "Scissors"):
            self.update_exp(self.myself, 3)
            self.update_exp(self.competitor, -1)
            self.record_result(self.myself, self.competitor, "win")
            result_message = f"{self.myself.mention}: {choice1} 打敗了 {self.competitor.mention}: {choice2}"
        else:
            self.update_exp(self.competitor, 3)
            self.update_exp(self.myself, -1)
            self.record_result(self.myself, self.competitor, "lose")
            result_message = f"{self.competitor.mention}: {choice2} 打敗了 {self.myself.mention}: {choice1}"
        # Add play again button
        playAgainView = playAgainButton(self.myself, self.competitor, self.db, self.client_logger)
        result_message += "\n" + "再來一局？"
        return result_message, playAgainView


    def update_exp(self, user, exp):
        try:
            # 確保使用者存在於 users 表
            self.db.ensure_user_exists(user.id, user.name)
            # 更新經驗值
            self.db.cursor.execute('UPDATE users SET exp = exp + (?) WHERE user_id = ?', (exp, str(user.id)))
            self.db.conn.commit()
        except Exception as e:
            print(f"Failed to update exp for user {user.id}: {e}")

    def record_result(self, winner, loser, result):
        try:
            # 確保贏家存在於 users 表
            self.db.ensure_user_exists(winner.id, winner.name)

            # 確保輸家存在於 users 表
            self.db.ensure_user_exists(loser.id, loser.name)

            # 紀錄結果
            self.db.cursor.execute('INSERT INTO rps_record (builder_id, receiver_id, date, result) VALUES (?, ?, ?, ?)',
                                    (str(winner.id), str(loser.id), datetime.now(), result))
            self.db.conn.commit()
            self.client_logger.info(f"[猜拳結果紀錄結果] @{winner.name} ({winner.id}) vs @{loser.name} ({loser.id}) 結果：{result}")
        except Exception as e:
            self.client_logger.error(f"[猜拳結果紀錄結果] Failed to record result: {e}")

class playAgainButton(discord.ui.View):
    def __init__(self, myself: discord.Member, competitor: discord.Member, db, client_logger):
        super().__init__(timeout=180)
        self.myself = myself
        self.competitor = competitor
        self.db = db
        self.client_logger = client_logger

    @discord.ui.button(label="再來一局", style=discord.ButtonStyle.primary)
    async def play_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the user is one of the participants
        if interaction.user not in [self.myself, self.competitor]:
            await interaction.response.send_message("這不是你的按鈕！", ephemeral=True)
            return

        # confirm the competitor
        view = moraButton(myself=self.myself, competitor=self.competitor, db=self.db, client_logger=self.client_logger)
        if interaction.user == self.myself:
            await interaction.response.edit_message(content=f"{self.myself.mention} 按下再來一局與 {self.competitor.mention} 再次猜拳！", view=view)
        else:
            await interaction.response.edit_message(content=f"{self.competitor.mention} 按下再來一局與 {self.myself.mention} 再次猜拳！", view=view)
        # Create a new moraButton view for a rematch
        self.stop()

    @discord.ui.button(label="結束遊戲", style=discord.ButtonStyle.danger)
    async def end_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable all buttons
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="遊戲結束！", view=button.view)
        self.stop()

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
        self.client_logger.info(f"[指令語音頻道隨機使用者] @{interaction.user.name} ({interaction.user.id}) 隨機選擇了 @{user.name} ({user.id})！")
    
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

    @app_commands.command(name="運勢統計", description="運勢統計")
    async def fortune_statistic(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        username = str(interaction.user.name)
        try:
            # 確保使用者存在於 users 表
            self.db.ensure_user_exists(user_id, username)

            # 獲取運勢統計
            fortune_list = self.db.get_all_fortune(user_id)

            if not fortune_list:
                await interaction.response.send_message("您還沒有獲得任何運勢。", ephemeral=True)
                return

            # 構建運勢統計列表
            fortune_count = {}
            for fortune in fortune_list:
                fortune_name = fortune[2]
                if fortune_name in fortune_count:
                    fortune_count[fortune_name] += 1
                else:
                    fortune_count[fortune_name] = 1
            # 構建運勢統計字串
            fortune_statistic = ""
            i = 1
            for fortune_name, count in fortune_count.items():
                fortune_statistic += f"{i}. {fortune_name} `{count}` 次\n"
                i += 1
            # 構建嵌入訊息
            embed = discord.Embed(title=f"{username} 的運勢統計", description=fortune_statistic, color=discord.Color.blue())
            embed.set_footer(text="運勢統計由 bot 提供")
            await interaction.response.send_message(embed=embed)
            self.client_logger.info(f"[指令運勢統計] 使用者 {username} ({user_id}) 獲取運勢統計：{fortune_statistic}")
        except Exception as e:
            await interaction.response.send_message(f"運勢統計獲取失敗：請告知 bot 管理者", ephemeral=True)
            self.client_logger.error(f"[指令運勢統計] 獲取運勢統計失敗：{str(e)}")

    @app_commands.command(name="運勢樣本", description="運勢樣本")
    async def fortune_sample(self, interaction: discord.Interaction):
        try:
            self.db.cursor.execute('SELECT fortune, COUNT(*) FROM fortune_record GROUP BY fortune')
            fortune_counts = self.db.cursor.fetchall()
            total_count = sum(count for _, count in fortune_counts)
            if total_count == 0:
                await interaction.response.send_message("目前沒有任何運勢資料。", ephemeral=True)
                return
            
            # 轉換為列表並按機率排序（從高到低）
            fortune_list = [(fortune, count, (count / total_count) * 100) for fortune, count in fortune_counts]
            fortune_list.sort(key=lambda x: x[2], reverse=True)
            
            # 構建運勢機率列表
            fortune_probability = ""
            i = 1
            for fortune, count, probability in fortune_list:
                fortune_probability += f"{i}. **{fortune}** 被抽出 `{count}` 次 (`{probability:.2f}%`)\n"
                i += 1
                
            # 構建嵌入訊息
            embed = discord.Embed(title="運勢樣本", description=fortune_probability, color=discord.Color.blue())
            embed.set_footer(text="運勢機率由 bot 提供")
            await interaction.response.send_message(embed=embed)
            self.client_logger.info(f"[指令運勢機率] 獲取運勢機率：{fortune_probability}")
        except Exception as e:
            await interaction.response.send_message(f"運勢機率獲取失敗：請告知 bot 管理者", ephemeral=True)
            self.client_logger.error(f"[指令運勢機率] 獲取運勢機率失敗：{str(e)}")

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
            embed = discord.Embed(title="使用者資訊", color=discord.Color.blue())
            embed.add_field(name="使用者名稱", value=f"`{user_info["username"]}`", inline=False)
            embed.add_field(name="簽到次數", value=f"`{user_info["sign_in_count"]}`", inline=False)
            embed.add_field(name="經驗值", value=f"`{user_info["exp"]}`", inline=False)
            embed.set_footer(text="使用者資訊由 bot 提供")
            await interaction.response.send_message(embed=embed)
            self.client_logger.info(f"[指令使用者資訊] 使用者 {username} ({user_id}) 取得使用者資訊：{user_info}")
        except Exception as e:
            await interaction.response.send_message(f"取得使用者資訊失敗：請告知 bot 管理者", ephemeral=True)
            self.client_logger.error(f"[指令使用者資訊] 取得使用者資訊失敗：{str(e)}")
    
    # 猜拳
    @app_commands.command(name="猜拳", description="猜拳")
    @app_commands.describe(competitor="The competitor to play with")
    async def mora(self, interaction: discord.Interaction, competitor: discord.Member):
        if interaction.user == competitor:
            await interaction.response.send_message("為甚麼你要跟自己猜拳？？？", ephemeral=True)
            return
        view = moraButton(myself=interaction.user, competitor=competitor, db=self.db, client_logger=self.client_logger)
        await interaction.response.send_message(f"{interaction.user.mention} 與 {competitor.mention} 開始猜拳！", view=view)
        self.client_logger.info(f"[指令猜拳] @{interaction.user.name} ({interaction.user.id}) 與 @{competitor.name} ({competitor.id}) 開始猜拳！")

    # 排名
    @app_commands.command(name="排名", description="取得使用者排名")
    async def rank(self, interaction: discord.Interaction):
        try:
            # 獲取當前伺服器的成員ID列表
            guild_member_ids = [str(member.id) for member in interaction.guild.members]
            
            # 取得所有使用者的經驗值，但只顯示當前伺服器的使用者
            self.db.cursor.execute('SELECT user_id, username, exp FROM users WHERE user_id IN ({}) ORDER BY exp DESC'.format(
                ','.join(['?' for _ in guild_member_ids])), guild_member_ids)
            users = self.db.cursor.fetchall()

            if not users:
                await interaction.response.send_message("目前沒有任何排名資料。", ephemeral=True)
                return

            # 構建排名列表
            rank_list = ""
            for idx, user in enumerate(users):
                rank_list += f"{idx + 1}. `{user[1]}` - `{user[2]} exp`\n"

            embed = discord.Embed(title=f"`{interaction.guild.name}` 使用者排名", description=rank_list, color=discord.Color.blue())
            embed.set_footer(text="僅顯示此伺服器的使用者")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"取得排名失敗：請告知 bot 管理者", ephemeral=True)
            self.client_logger.error(f"[指令排名] 取得排名失敗：{str(e)}")

    # Quote
    @app_commands.command(name="quote", description="Quote a message")
    async def quote(self, interaction: discord.Interaction, message_id_or_text: str):
        # Defer the response to prevent timeout
        await interaction.response.defer()
        
        # 檢查訊息是否存在
        if message_id_or_text.isdigit():
            try:
                message = await interaction.channel.fetch_message(message_id_or_text)
                content = message.content
                author = message.author
                
                # 檢查消息
                if content == "":
                    await interaction.followup.send("該訊息沒有內容。", ephemeral=True)
                    return
                # 確保訊息內容不超過 200 字元
                elif len(content) > 200:
                    await interaction.followup.send("訊息內容過長，請選擇較短的訊息。", ephemeral=True)
                    return
                # 確保訊息使用者不為機器人
                elif author.bot:
                    await interaction.followup.send("無法引用機器人的訊息。", ephemeral=True)
                    return
            except discord.NotFound:
                await interaction.followup.send("找不到該訊息。", ephemeral=True)
                return
            except discord.Forbidden:
                await interaction.followup.send("無法訪問該訊息。", ephemeral=True)
                return
        else:
            # 直接使用輸入的文字作為引用內容
            content = message_id_or_text
            author = interaction.user
        quote_image = self.generate_quote_image(content, author)

        # Convert PIL image to discord file
        import io
        with io.BytesIO() as image_binary:
            quote_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            await interaction.followup.send(file=discord.File(fp=image_binary, filename='quote.png'))

    def generate_quote_image(self, text, author):
        from PIL import Image, ImageFont, ImageDraw
        import os
        import io
        import textwrap
        import requests
        
        bg_image_path = author.avatar.url  # Default to None, will be set later if needed
        
        # Set default background image path if none provided
        if bg_image_path is None:
            bg_image_path = os.path.join(os.path.dirname(__file__), "headshot.jpg")
        
        # Create basic canvas dimensions
        width, height = 800, 600
        
        try:
            # Check if the path is a URL (starts with http:// or https://)
            if bg_image_path.startswith(('http://', 'https://')):
                # Download the image from URL
                response = requests.get(bg_image_path, stream=True)
                response.raise_for_status()  # Raise an exception for bad responses
                
                # Open the image from the response content
                background = Image.open(io.BytesIO(response.content))
            else:
                # Open from local file path
                background = Image.open(bg_image_path)
                
            # Resize the background image
            background = background.resize((width, height))
            # Convert to RGBA to support transparency
            image = background.convert("RGBA")
            
            # Add semi-transparent overlay for text readability
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 160))  # 160 for ~60% opacity
            image = Image.alpha_composite(image, overlay)
            
            # Add left-to-right gradient effect while preserving the background image
            gradient_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient_image)
            
            # Draw gradient effect - using transparency instead of solid color
            for x in range(0, width, 1):
                ratio = x / width
                # Adjust transparency rather than color value, darker on the right
                alpha_value = int(180 * ratio**1.2)
                gradient_draw.line([(x, 0), (x, height)], fill=(0, 0, 0, alpha_value))
            
            # Composite gradient onto main image
            image = Image.alpha_composite(image, gradient_image)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            # Fallback to gradient if image loading fails
            image = Image.new('RGB', (width, height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            for x in range(width):
                for y in range(height):
                    gradient_value = max(0, min(255, int(255 * (1 - (x/width)**1.5))))
                    draw.point((x, y), fill=(gradient_value, gradient_value, gradient_value))
        
        # Prepare to draw text
        draw = ImageDraw.Draw(image)
        
        # 載入字體（調整字體文件的路徑）
        try:
            quote_font = ImageFont.truetype("LXGWWenKaiMonoTC-Regular.ttf", 48, encoding="unic")
            author_font = ImageFont.truetype("LXGWWenKaiMonoTC-Regular.ttf", 32, encoding="unic")
        except IOError:
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
            print("由於載入自定義字體時出錯，使用默認字體。")

        # 文字換行處理
        margin = 60

        # 處理中文文字的換行
        if any('\u4e00' <= char <= '\u9fff' for char in text):  # 檢查是否包含中文
            # 中文字符寬度大致相同，所以可以按字符數量計算
            chars_per_line = 15
            word_list = [text[i:i+chars_per_line] for i in range(0, len(text), chars_per_line)]
        else:
            # 英文文字換行
            wrapper = textwrap.TextWrapper(width=30)
            word_list = wrapper.wrap(text=text)
        
        quote_text = '\n'.join(word_list)
        
        # 計算文字尺寸以進行右對齊
        # 針對不同 PIL 版本調整文字測量方法
        try:
            # 較新的 PIL 版本
            text_width = max([draw.textlength(line, font=quote_font) for line in word_list])
        except AttributeError:
            # 較舊的 PIL 版本
            text_width = max([quote_font.getmask(line).getbbox()[2] for line in word_list])
        
        # 計算右對齊文字的 x 座標
        y_position = height // 2 - len(word_list) * 30
        x_position = width - margin - text_width
        
        # 繪製引言（帶引號）
        quote_with_marks = f'"{quote_text}"'
        draw.text(
            (x_position, y_position),
            quote_with_marks,
            font=quote_font,
            fill=(255, 255, 255, 255)
        )
        
        # 繪製作者名稱
        author_text = f"- {author.name}"
        try:
            author_width = draw.textlength(author_text, font=author_font)
        except AttributeError:
            author_width = author_font.getmask(author_text).getbbox()[2]
        draw.text(
            (width - margin - author_width, y_position + len(word_list) * 60 + 20),
            author_text,
            font=author_font,
            fill=(200, 200, 200, 255)
        )
        
        # 轉換回 RGB 格式以便儲存
        return image.convert('RGB')

async def setup(bot):
    await bot.add_cog(slashCommands(bot))
