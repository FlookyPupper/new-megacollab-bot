import discord
from discord.ext import commands
from config.groups import prop
from views.message import Message
from utils.dbcommands import getschemaversion, db_showrank

class EnableRanks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @prop.command(name="enableranks", description="Pings something")
    async def enableranks(
        self, 
        ctx,
        value: bool = discord.Option(
            description = 'Specify "True" to enable ranks, "False" to disable them.',
            required=True
            )
        ):
        if not await isadmin(ctx.interaction.user):
            embed = Message(bot, title="Error", text="You don't have permission to use this command.", messagetype="Error")
            return
        
        if value:
            verb = "enab"
        else:
            verb = "disab"

        required = {
            'API_VERSION': 1,
            'REVISION': 2,
            'VERSION_STRING': "1.1"
        }

        schemaversion = await getschemaversion()

        try:
            if schemaversion['API_VERSION'] == required['API_VERSION'] and schemaversion['REVISION'] >= required['REVISION']:
                async with bot.db.acquire() as conn:
                    if value:
                        await conn.execute(
                            'SELECT "Core".enablerank($1)',
                            ctx.guild.id
                        )

                    else:
                        guild = ctx.guild

                        idoluserid = await conn.fetchval(
                            'select userid from "Core".showidol($1)',
                            guild.id
                        )

                        idol = guild.get_member(idoluserid)

                        idolrole_id = await conn.fetchval(
                            'select roleid from "Associations".idolroles where guildid = $1',
                            guild.id
                        )

                        idolrole = guild.get_role(idolrole_id)

                        if idolrole is None:
                            try:
                                idolrole = await guild.fetch_role(idolrole_id)
                            except Exception as e:
                                idolrole = None
                        
                        if idolrole is not None:
                            for member in idolrole.members:
                                await member.add_roles(idolrole, reason="Disable ranks")
                        
                        for member in guild.members:
                            if not member.bot:
                                userseasontokens = await conn.fetchval(
                                    'select seasontokens from "Core".users where guildid = $1 and userid = $2',
                                    member.guild.id, member.id
                                )

                                if userseasontokens is not None:
                                    correspondingrank = await db_showrank(bythreshold=userseasontokens, conn=conn)

                                    rankrole_id = await conn.fetchval(
                                        'SELECT roleid from "Junctions".ranksxdiscordroles where rankname = $1 and guildid = $2',
                                            correspondingrank['rankname'], member.guild.id
                                    )

                                    rankrole = guild.get_role(rankrole_id)

                                    if rankrole and rankrole in member.roles:
                                        await member.add_roles(rankrole)
                        
                        await conn.execute(
                            'SELECT "Core".disablerank($1)',
                            ctx.guild.id
                        )
                
                guild_cache[ctx.guild.id] = value
                
                embed = Message(bot, title="Enabled ranks", text=f"Successfully {verb}led ranks on this guild.", messagetype="Success")
            else:
                embed = Message(bot, title="Incompatible Icy version", text=f"Your database is not compatible with this command. This command requires version {required['VERSION_STRING']} to function.", messagetype="Error")
        except Exception as e:
            embed = Message(bot, title="An error occurred", subtitle=f"An error occurred while {verb}ing ranks for this guild.", text=f"{e}", messagetype="Error")

def setup(bot):
    bot.add_cog(EnableRanks(bot))