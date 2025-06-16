import hikari
import lightbulb

ping = lightbulb.Loader()

@ping.command
class Greet(
    lightbulb.SlashCommand,
    name="greet",
    description="Greets the specified user",
):
    user = lightbulb.user("user", "User to greet")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        """Greets the specified user."""
        await ctx.respond(f"Hello, {self.user.mention}!")