import time
from discord.ext import commands, tasks
from config.groups import SONG_TMP, MAX_AGE_SECONDS
from pathlib import Path


class CleanupTempMP3(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_temp_mp3s.start()

    def cog_unload(self):
        self.cleanup_temp_mp3s.cancel()

    @tasks.loop(minutes=2)
    async def cleanup_temp_mp3s(self):
        now = time.time()
        for file in SONG_TMP.iterdir():
            if file.is_file() and now - file.stat().st_mtime > MAX_AGE_SECONDS:
                file.unlink(missing_ok=True)

    @cleanup_temp_mp3s.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(CleanupTempMP3(bot))