from discord.ext import commands
from discord.commands import slash_command
import discord

from utils.cache import guild_cache
from utils.dbcommands import show_user_info
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
                usertocheck = user

                if usertocheck == None:
                    user_info = await show_user_info(self.bot, ctx.interaction.user, ctx.interaction.user.guild)
                    usertocheck = ctx.interaction.user
                else:
                    user_info = await show_user_info(self.bot, usertocheck, usertocheck.guild)
                    usertocheck = user

                if user_info is None:
                    embed = discord.Embed(title="❌ User not found", color=0xff0000)

                else:
                    embed = discord.Embed( 
                        color=usertocheck.accent_color)

                    embed.set_author(name=usertocheck.global_name, icon_url=usertocheck.display_avatar.url)

                    if user_info['isleaderboardenabled']:
                        position = await db_showleaderboard(user=usertocheck, guild=usertocheck.guild)
                        position = position[-1]['position']
                    else:
                        position = None

                    if position == 1:
                        embed.add_field(name="Rank", value="Idol")
                    else:
                        embed.add_field(name="Rank", value=user_info['currentrank'])

                    if user_info['isleaderboardenabled']:
                        description = f"{user_info['seasontokens']}"
                        embed.add_field(name="Leaderboard Position", value=f"{p.ordinal(position)}")
                    else:
                        description = f"{user_info['seasontokens']}/{user_info['tokensrequiredfornextrank']} ({user_info['tokenslefttonextrank']} left for {user_info['nextrank']})"
        
                    embed.add_field(name="Your Season Tokens", value=description)

                    embed.set_footer(text=await generate_random_lyric())
            else:
                embed = discord.Embed(title="❌ Ranks are disabled on this server.", color=0xff0000)

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Rank(bot))