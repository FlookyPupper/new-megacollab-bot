import discord
from discord.ext import commands
from config.groups import prop
from views.message import Message
from utils.isadmin import isadmin
from pycord.multicog import subcommand

class SetServerVerification(commands.Cog):   
    def __init__(self, bot):
        self.bot = bot

    @subcommand("prop", independent=True)
    @discord.slash_command(
        name="setserververification", 
        description="Sets the role to identify a member in this guild."
        )
    @discord.default_permissions(manage_guild=True)
    async def setmemberrolecmd(
        self,
        ctx,
        value: bool = discord.Option(
            bool,
            description = 'Specify "True" to require verification, "False" to disable it.',
            required=True
        )
    ):
        if not await isadmin(ctx.interaction.user):
            embed = Message(self.bot, title="Error", text="You don't have permission to use this command.", messagetype="Error")
            await ctx.respond(view=embed, ephemeral=True)
            return

        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    'SELECT "Core".setserververification($1, $2)',
                    ctx.interaction.guild.id, value
                )

            embed = Message(self.bot, title="Success", text=f"Successfully set this server verification to {value}.", messagetype="Success")
        except Exception as e:
            embed = Message(self.bot, title="Error", subtitle=f"An error occurred while setting server verification to {value}", text=f"{e}", messagetype="Error")
        finally:
            await ctx.respond(view=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(SetServerVerification(bot))