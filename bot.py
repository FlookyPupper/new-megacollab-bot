import discord
from pycord.multicog import Bot
from discord.ext import commands
from utils.icylogger import logger
from utils.dbconnector import create_pool
from utils.syncer import sync_server_to_database

class MyBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pool = None

    async def start(self, *args, **kwargs):
        await create_pool(self)
        logger.info("Pool created, waking up...")
        await super().start(*args, **kwargs)

    async def close(self):
        await super().close()
        logger.info("I'm coming home now...")

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = MyBot(command_prefix="!", intents=intents)