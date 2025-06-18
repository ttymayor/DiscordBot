import lightbulb

class chennalSelector(lightbulb.components.Menu):
    def __init__(self) -> None:
        super().__init__()

        self.add_channel_select(
            self.on_channel_selected,
        )

    async def on_channel_selected(self, ctx: lightbulb.components.MenuContext) -> None:
        """處理頻道選擇"""
        selected_channel = ctx.interaction.selected_channel
        await ctx.respond(f"你選擇的頻道是：{selected_channel.mention}", ephemeral=True)


# general = lightbulb.Loader()

settings = lightbulb.Group("settings", "General settings commands")

@settings.command
class WelcomeChennalSetting(
    lightbulb.SlashCommand,
    name="welcome-channel",
    description="Sets the welcome channel for the server.",
):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """Displays a list of available commands."""
        await ctx.respond(f"請選擇歡迎頻道：", components=chennalSelector())