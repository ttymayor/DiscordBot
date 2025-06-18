import hikari.emojis
import hikari.impl.special_endpoints
import hikari.polls
import lightbulb
import asyncio
import uuid
import datetime
import hikari
# class VoteButton(lightbulb.components.Menu):
#     def __init__(self, options: list[str]) -> None:
#         super().__init__()
#         self.options = options
#         self.votes = {option: 0 for option in options}
#         for option in options:
#             self.add_interactive_button(
#                 lightbulb.ButtonStyle.PRIMARY,
#                 self.on_vote,
#                 label=option,
#                 custom_id=option
#             )
#     async def on_vote(self, ctx: lightbulb.components.MenuContext) -> None:
#         # Check if the user has already voted
#         if ctx.user.id in self.votes:
#             await ctx.respond("你已經投過票了！", ephemeral=True)
#             return

#         # Record the vote
#         self.votes[ctx.interaction.custom_id] += 1
#         await ctx.respond(f"你投了 {ctx.interaction.custom_id} 票！", ephemeral=True)

#         # Optionally, you can send the current vote counts
#         vote_counts = "\n".join(f"{option}: {count}" for option, count in self.votes.items())
#         await ctx.respond(f"當前投票結果：\n{vote_counts}", ephemeral=True)
#         # Optionally, you can end the voting after a certain condition
#         # For example, if a certain number of votes is reached
#         # if sum(self.votes.values()) >= 10:
#         #     await ctx.respond("投票結束！", ephemeral=True)
#         #     await self.end_menu(ctx.interaction)  # End the menu if needed
#         # Or you can keep the menu open for further voting
#         # Note: You can also implement a method to end the voting and display final results
#     def end_menu(self, interaction: lightbulb.components.InteractiveButton) -> None:
#         # This method can be used to end the voting and display final results
#         final_results = "\n".join(f"{option}: {count}" for option, count in self.votes.items())
#         interaction.respond(f"投票結束！最終結果：\n{final_results}")
#         self.stop()

class VoteModal(lightbulb.components.Modal):
    def __init__(self) -> None:
        # 添加投票標題輸入框
        self.title = self.add_short_text_input(
            "投票標題",
            required=True,
            max_length=100,
            placeholder="例如：你最喜歡的顏色？"
        )
        # 添加投票描述輸入框
        self.description = self.add_paragraph_text_input(
            "投票描述",
            required=False,
            max_length=500,
            placeholder="例如：請選擇你最喜歡的顏色。"
        )
        # 結束時間
        self.end_time = self.add_short_text_input(
            "結束時間（分鐘）",
            required=True,
            max_length=3,
            placeholder="例如：5"
        )
        # 添加選項輸入框（以逗點隔開）
        self.options = self.add_paragraph_text_input(
            "投票選項",
            required=True,
            max_length=500,
            placeholder="請以逗點隔開選項，例如：紅色,藍色,綠色,黃色"
        )
        self.items = str(self.options.value).split(",") if self.options.value else []


    async def on_submit(self, ctx: lightbulb.components.ModalContext) -> None:
        """處理投票提交"""
        embed = hikari.Embed(
            title=self.title.value,
            description=self.description.value or "無描述",
            color=hikari.Color(0x00FF00)  # 綠色
        )
        embed.add_field(
            name="投票選項",
            value="\n".join(f"{i+1}. {item} **【0 票】**" for i, item in enumerate(self.items)),
            inline=False
        )
        await ctx.respond("正在創建投票...", embed=embed, ephemeral=True)

class VoteButton(lightbulb.components.Menu):
    def __init__(self, options: list[str]) -> None:

        super().__init__()
        self.options = options
        self.votes = {option: 0 for option in options}
        for option in options:
            self.add_interactive_button(
                lightbulb.ButtonStyle.PRIMARY,
                self.on_vote,
                label=option,
                custom_id=option
            )



vote_loader = lightbulb.Loader()

@vote_loader.command
class CreateVoteCommand(
    lightbulb.SlashCommand,
    name="vote",
    description="創建一個投票"
):
    """創建一個投票命令"""
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, client: lightbulb.Client) -> None:
        """創建一個投票"""
        # vote = VoteModal()
        poll = hikari.impl.special_endpoints.PollBuilder(
            question_text="投票標題",
            duration=1, # 1 hour
            answers=[
                hikari.impl.special_endpoints.PollAnswerBuilder(text = "選項1"),
                hikari.impl.special_endpoints.PollAnswerBuilder(text = "選項2"),
                hikari.impl.special_endpoints.PollAnswerBuilder(text = "選項3")
            ],
            allow_multiselect=False,
        )
        await ctx.respond("請填寫投票信息：")

        # await ctx.respond_with_modal("建立投票", c_id := str(uuid.uuid4()), components=vote)
        
        # try:
        #     await vote.attach(client, c_id, timeout=600)
        # except asyncio.TimeoutError:
        #     await ctx.respond("投票創建超時。", ephemeral=True)
        #     return