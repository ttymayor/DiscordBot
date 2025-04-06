import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="=", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Discord"))
    slash = await bot.tree.sync()
    print(f'>>> "{bot.user}" is logged in! <<<')
    print(f">>> load {len(slash)} slash commands <<<")


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
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f">>> {filename[:-3]} is loaded! <<<")


async def main():
    async with bot:
        await load_extension()
        await bot.start(str(os.getenv("BOT_TOKEN")))


if __name__ == "__main__":
    asyncio.run(main())