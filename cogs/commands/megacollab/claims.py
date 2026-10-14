import discord
from discord.ext import commands
from utils.dbcommands import (
    pulllocalsong,
    showtext
)
from pycord.multicog import subcommand
from autocomplete.collab import collab_autocomplete
from utils.isadmin import isadmin

class ClaimsMegacollab(commands.Cog):   
    def __init__(self, bot):
        self.bot = bot
    
    @subcommand("megacollab", independent=True)
    @discord.command(
        name='claims', 
        description="Shows claims of a megacollab.",
    )
    @discord.default_permissions(manage_guild=True)
    async def showclaims(
        self,
        ctx, 
        collab: str = discord.Option(
            description="Collab",
            autocomplete=discord.utils.basic_autocomplete(collab_autocomplete),
            required=True
            )
        ):
        if not await isadmin(ctx.interaction.user):
            embed = discord.Embed(title="❌ You don't have permission to use this command.", color=0xff0000)

            await ctx.respond(
                embed=embed,
                ephemeral=True
            )
        try:
            collabtext = await showtext(self.bot, ctx.interaction.guild, collabid=collab, texttoshow="Claims", mentions=True)

        except Exception as e:
            embed = discord.Embed(title=f"❌ {e}", color=0xff0000)
            await ctx.respond(embed=embed,
                ephemeral=True
            )

        else:
            await ctx.respond(collabtext,
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(ClaimsMegacollab(bot))