import discord
import os
import asyncio
import random as rd
import json
from discord import app_commands
from discord.ext import commands


intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="=", intents=intents)


with open("config.json", "r", encoding="utf8") as jfile:
    jdata = json.load(jfile)


@bot.event
async def on_ready():
    # activity = discord.Activity(
    #     type=discord.ActivityType.watching,
    #     name="哈耿",
    # )
    activity = discord.Streaming(
        name="哈耿台",
        url="https://www.twitch.tv/ennaouii",
    )
    await bot.change_presence(activity=activity)
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
        await bot.start(jdata["botToken"])


if __name__ == "__main__":
    asyncio.run(main())

# https://discord.com/oauth2/authorize?client_id=1211861121678581760&permissions=8&integration_type=0&scope=bot
