import discord
from discord.ext import commands
from config.groups import prop
from views.message import Message
from utils.isadmin import isadmin
from pycord.multicog import subcommand

class SetMemberRole(commands.Cog):   
    def __init__(self, bot):
        self.bot = bot

    @subcommand("prop")
    @discord.slash_command(
        name="memberrole", 
        description="Sets the role to identify a member in this guild."
        )
    @discord.default_permissions(manage_guild=True)
    async def setmemberrolecmd(
        self,
        ctx,
        role: discord.Role = discord.Option(
            discord.Role,
            description="Role to use to identify members in this guild.",
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
                    'SELECT "Core".setmemberroles($1, $2)',
                    role.guild.id, role.id
                )

            embed = Message(self.bot, title="Success", text=f"Successfully set @{role.name} as the member role.", messagetype="Success")
        except Exception as e:
            embed = Message(self.bot, title="Error", text=f"An error occurred while setting @{role.name} as the member role: {e}", messagetype="Error")
        finally:
            await ctx.respond(view=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(SetMemberRole(bot))