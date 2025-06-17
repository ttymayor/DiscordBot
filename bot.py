import hikari
import lightbulb
import os
from dotenv import load_dotenv

import extensions

# Load environment variables from .env file
load_dotenv()

bot = hikari.GatewayBot(
    intents=hikari.Intents.ALL,
    token=os.getenv("BOT_TOKEN"),
)
client = lightbulb.client_from_app(bot)
bot.subscribe(hikari.StartingEvent, client.start)

@bot.listen()
async def on_starting(_: hikari.StartingEvent) -> None:
    # Load any extensions
    await client.load_extensions(
        "extensions.ping",
        "extensions.autoComplete",
        "extensions.rock_paper_scissors",
    )
    # Start the bot - make sure commands are synced properly
    await client.start()

@client.register
class Echo(
    lightbulb.SlashCommand,
    name="echo",
    description="echo",
):
    text = lightbulb.string("text", "the text to repeat")
    
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond(self.text)

@client.register
class GetMessageId(
    lightbulb.MessageCommand,
    name="Get ID",
):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # 'self.target' contains the message object the command was executed on
        await ctx.respond(self.target.id)

@client.register
class GetUserId(
    lightbulb.UserCommand,
    name="Get ID",
):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # 'self.target' contains the user object the command was executed on
        await ctx.respond(self.target.id)

bot.run(asyncio_debug=True)
