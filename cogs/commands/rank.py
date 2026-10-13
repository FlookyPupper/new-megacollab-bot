from discord.ext import commands
from discord.commands import slash_command
import discord

from views.rank import RankView
from views.message import Message

from utils.cache import guild_cache
from utils.dbcommands import (show_user_info, db_showleaderboard)
from utils.generaterandomlyric import generate_random_lyric

class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="rank")
    async def ping(
        self, 
        ctx,
        user: discord.Option(
            discord.Member,
            description="User to show rank.",
            required=False
            ),
        newdesign: discord.Option(
            bool,
            description="Shows the new modal.",
            default=False,
            required=False
        )
        ):
        if not self.bot.isBotSynced:
            embed = discord.Embed(title="❌ Bracelety has not finished starting up. Try again in a bit.", color=0xff0000)
        else:
            if ctx.guild.id not in guild_cache:
                async with self.bot.db.acquire() as conn:
                    guild_cache[ctx.guild.id] = await conn.fetchval(
                        'SELECT ranksenabled from "Discord".guilds where guildid = $1',
                        ctx.guild.id
                    )
            
            if guild_cache[ctx.guild.id]:

                if user == None:
                    usertocheck = ctx.interaction.user
                    user_info = await show_user_info(self.bot, ctx.interaction.user, ctx.interaction.user.guild)
                else:
                    usertocheck = user
                    user_info = await show_user_info(self.bot, usertocheck, usertocheck.guild)
                    
                if user_info is None:
                    embed = Message(self.bot, title="Error", text="User not found.", messagetype="Error")
                else:
                    if user_info['isleaderboardenabled']:
                        position = await db_showleaderboard(self.bot, user=usertocheck, guild=usertocheck.guild)
                        position = position[-1]['position']
                    else:
                        position = None

                    embed = RankView(
                        self.bot, 
                        usertocheck, 
                        user_info['seasontokens'], 
                        user_info['tokensrequiredfornextrank'], 
                        user_info['currentrank'], 
                        user_info['nextrank'],
                        position)

                await ctx.respond(view=embed)
                    
            
        

def setup(bot):
    bot.add_cog(Rank(bot))