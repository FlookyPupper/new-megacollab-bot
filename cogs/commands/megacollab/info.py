import discord
from discord.ext import commands
from utils.dbcommands import (
    pulllocalsong,
    showtext
)
from pycord.multicog import subcommand
from autocomplete.collab import collab_autocomplete
from utils.isadmin import isadmin

class InfoMegacollab(commands.Cog):   
    def __init__(self, bot):
        self.bot = bot
    
    @subcommand("megacollab", independent=True)
    @discord.command(
        name='info', 
        description="Shows info of a megacollab.",
    )
    @discord.default_permissions(manage_guild=True)
    async def showinfo(
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
        await ctx.response.defer(ephemeral=True)

        try:
            collabtext = await showtext(self.bot, ctx.interaction.guild, collabid=collab, texttoshow="Info", mentions=True)

            file = await pulllocalsong(self.bot, ctx.interaction.guild, collabid=collab)

        except Exception as e:
            embed = discord.Embed(title=f"❌ {e}", color=0xff0000)
            collabtext = None
            raise

        finally:
            if collabtext is None:
                await ctx.followup.send(embed=embed,
                        ephemeral=True
                    )
            else:
                await ctx.followup.send(collabtext,
                        ephemeral=True,
                        file=file
                    )

def setup(bot):
    bot.add_cog(InfoMegacollab(bot))