import lightbulb
import asyncio
import hikari

class RockPaperScissorsButton(lightbulb.components.Menu):
    def __init__(self, inviter, invited) -> None:
        self.choices = {}
        self.inviter = inviter
        self.invited = invited
        self.scissors_btn = self.add_interactive_button(
            hikari.ButtonStyle.PRIMARY,
            self.on_button_press,
            label="✂️ 剪刀", 
            custom_id="scissors"
        )
        self.rock_btn = self.add_interactive_button(
            hikari.ButtonStyle.PRIMARY,
            self.on_button_press,
            label="🪨 石頭",
            custom_id="rock"
        )
        self.paper_btn = self.add_interactive_button(
            hikari.ButtonStyle.PRIMARY,
            self.on_button_press,
            label="📄 布",
            custom_id="paper"
        )
    
    def determine_winner(self, choice1, choice2):
        if choice1 == choice2:
            return "平手！"

        player1 = self.inviter.mention
        player2 = self.invited.mention
        
        if choice1 == "rock":
            return f"{player1} 獲勝！" if choice2 == "scissors" else f"{player2} 獲勝！"
        if choice1 == "paper":
            return f"{player1} 獲勝！" if choice2 == "rock" else f"{player2} 獲勝！"
        if choice1 == "scissors":
            return f"{player1} 獲勝！" if choice2 == "paper" else f"{player2} 獲勝！"

    async def on_button_press(self, ctx: lightbulb.components.MenuContext) -> None:
        # 檢查是否為遊戲玩家
        if ctx.user.id not in [self.inviter.id, self.invited.id]:
            await ctx.respond("你不是遊戲玩家之一，不能參與！", ephemeral=True)
            return

        player_id = str(ctx.user.id)
        if player_id in self.choices:
            await ctx.respond(f"你已經選擇了", ephemeral=True)
            return

        self.choices[player_id] = ctx.interaction.custom_id
        # Get the button label based on custom_id
        label_map = {
            "scissors": "✂️ 剪刀",
            "rock": "🪨 石頭",
            "paper": "📄 布"
        }
        button_label = label_map[ctx.interaction.custom_id]
        await ctx.respond(f"你選擇了：{button_label}", ephemeral=True)

        if len(self.choices) == 2:
            choices = list(self.choices.values())
            result = self.determine_winner(choices[0], choices[1])
            
            await ctx.interaction.message.edit(
                content=f"{self.inviter.username} 選擇了 {choices[0].capitalize()}，{self.invited.username} 選擇了 {choices[1].capitalize()}。\n結果：{result}",
                components=[]
            )
            ctx.stop_interacting()

rock_paper_scissors = lightbulb.Loader()

@rock_paper_scissors.command
class RockPaperScissors(
    lightbulb.SlashCommand,
    name="rps",
    description="Play Rock, Paper, Scissors with the bot",
):
    player = lightbulb.user("對手", "選擇你想要邀請的玩家")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, client: lightbulb.Client) -> None:
        if self.player.id == ctx.user.id:
            await ctx.respond("你不能邀請自己玩遊戲！", ephemeral=True)
            return

        if self.player is None:
            self.player = ctx.bot.get_me()

        menu = RockPaperScissorsButton(ctx.user, self.player)
        
        resp = await ctx.respond(
            f"{ctx.user.mention} 邀請 {self.player.mention} 玩石頭剪刀布！\n",
            components=menu,
        )

        try:
            await menu.attach(client, timeout=300)
        except asyncio.TimeoutError:
            await ctx.edit_response(
                resp,
                "遊戲超時，請重新開始遊戲。",
                components=[]
            )
