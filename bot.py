import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from core.logger import setup_logger


# Load environment variables from .env file
load_dotenv()

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Set the working directory to the script directory
os.chdir(script_dir)

# Set up loggers
bot_logger, client_logger, music_logger = setup_logger(script_dir)

# Add logger to bot attributes
commands.Bot.bot_logger = bot_logger
commands.Bot.client_logger = client_logger
commands.Bot.music_logger = music_logger

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="=", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Discord"))
    slash = await bot.tree.sync()
    print(f">>> {bot.user} is logged in! <<<")
    bot_logger.info(f">>> {bot.user} is logged in! <<<")
    bot_logger.info(f">>> load {len(slash)} slash commands <<<")


@bot.command()
async def load(ctx, extension):
    await bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Loaded {extension} done.")


@bot.command()
async def unload(ctx, extension):
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"Unloaded {extension} done.")


@bot.command()
async def reload(ctx, extension):
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"Reloaded {extension} done.")


async def load_extension():
    cogs_dir = os.path.join(script_dir, "cogs")
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            bot_logger.info(f">>> {filename[:-3]} is loaded! <<<")


async def main():
    async with bot:
        await load_extension()
        await bot.start(str(os.getenv("BOT_TOKEN")))


if __name__ == "__main__":
    asyncio.run(main())