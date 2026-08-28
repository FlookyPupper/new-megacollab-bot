#!/bin/python
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.icylogger import logger
from bot import bot
from pathlib import Path
import asyncio
import argparse
from utils.syncer import sync_server_to_database
from utils.version import icyversion
from utils.version import icycommitdate
from utils.version import isstable
#import config.groups as groups
from config.groups import prop

parser = argparse.ArgumentParser(description="Start the Icy bot")

parser.add_argument(
    "--admin-role",
    type=str,
    help="<GuildID>;<RoleID>"
)

parser.add_argument(
    "--refresh-views", "-rv",
    action="store_true",
    help="Proactively regenerate persistent view messages"
)

parser.add_argument(
    "-v",
    action="store_true",
    help=""
)

args = parser.parse_args()

if args.v:
    print(f'Icy version {icyversion()} {f"({icycommitdate()})" if not isstable(icyversion()) else ""}')
    exit()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN == None:
    logger.error("No token specified. Specify one in .venv or on your operating system's environment variables.")
    exit()
DATABASE_URL = os.getenv("DATABASE_URL")

for file in Path("cogs").rglob("*.py"):
    if file.name.startswith("_"):
        continue

    module = str(file.with_suffix("")).replace("/", ".").replace("\\", ".")
    logger.info(f"Loaded cog: {module}")
    bot.load_extension(module)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    #await bot.sync_commands()
    logger.info("Commands synced")
    await sync_server_to_database(bot, args)

bot.run(TOKEN)