import discord
from discord.ext import commands
from utils.dbcommands import (
    pulllocalsong,
    addtodatabase,
    showtext,
    db_showcollabs,
    db_showparts,
    db_addandsettype,
    showadminroles,
    showmemberroles,
    showjudgeroles
)
from utils.parseintodict import parseintodict
from pycord.multicog import subcommand
from autocomplete.collab import collab_autocomplete
from utils.isadmin import isadmin
from views.legacy.parts import (SelectPartToClaim, PartSelect)

class PublishMegacollab(commands.Cog):   
    def __init__(self, bot):
        self.bot = bot
    
    @subcommand("megacollab", independent=True)
    @discord.command(
        name='publish', 
        description="Creates the appropriate server items for a given megacollab and publishes it to the server.",
    )
    @discord.default_permissions(manage_guild=True)
    async def publishmegacollab(
        self,
        ctx, 
        collab: str = discord.Option(
            description="Collab to publish.",
            autocomplete=discord.utils.basic_autocomplete(collab_autocomplete),
            required=True
        )
    ):
        if not await isadmin(ctx.interaction.user) and ctx.interaction.user.has_permissions.manage_channels:
            embed = discord.Embed(title="❌ You don't have permission to use this command.", color=0xff0000)
            await ctx.respond(
                embed=embed,
                ephemeral=True
            )
            return

        try:
            roles = []
            channels = []

            await ctx.response.defer(ephemeral=True)

            collab = int(collab)

            collab_dict = await db_showcollabs(self.bot, ctx.interaction.guild, bycollabid=int(collab))
            collab_dict = await parseintodict(collab_dict)

            parts_dict = await db_showparts(self.bot, ctx.interaction.guild, int(collab))
            parts_dict = await parseintodict(parts_dict)

            async with self.bot.db.acquire() as conn:
                async with conn.transaction():
                    guild = ctx.guild 

                    hostuser_records = await conn.fetch(
                        'select * from "Associations".megacollabhosts where collabid = $1 and guildid = $2',
                        collab, guild.id
                    )

                    hostusers = []

                    for user in hostuser_records:
                        hostusers.append(guild.get_member(user['userid']))        
                        
                    category = await ctx.guild.create_category(name=f'{collab_dict[0]['collabname']} - {collab_dict[0]['category'] if collab_dict[0]['category'] is not None else 'Community'} Collab')

                    host_role = await ctx.guild.create_role(
                        name=f"{collab_dict[0]['collabname']} - Host",
                        color=0xff00ff,  
                        hoist=True, 
                        mentionable=False, 
                        reason=f"Creation of host role for collab {collab_dict[0]['collabname']}"
                    )

                    roles.append(host_role)

                    member_role = await ctx.guild.create_role(
                        name=f"{collab_dict[0]['collabname']} - Member",
                        color=0x00ffff,  
                        hoist=True, 
                        mentionable=False, 
                        reason=f"Creation of member role for collab {collab_dict[0]['collabname']}"
                    )

                    roles.append(member_role)

                    backup_role = await ctx.guild.create_role(
                        name=f"{collab_dict[0]['collabname']} - Backup",
                        color=0x00ffaa,  
                        hoist=False, 
                        mentionable=False, 
                        reason=f"Creation of backup member role for collab {collab_dict[0]['collabname']}"
                    )

                    roles.append(backup_role)

                    notify_role = await ctx.guild.create_role(
                        name=f"{collab_dict[0]['collabname']} - Notify",
                        color=0xffcc00,  
                        hoist=False, 
                        mentionable=False, 
                        reason=f"Creation of notification role for collab {collab_dict[0]['collabname']}"
                    )

                    roles.append(notify_role)
          
                    await addtodatabase(self.bot, member_role, guild=member_role.guild, conn=conn)
                    await addtodatabase(self.bot, host_role, guild=host_role.guild, conn=conn)
                    await addtodatabase(self.bot, backup_role, guild=backup_role.guild, conn=conn)
                    await addtodatabase(self.bot, notify_role, guild=notify_role.guild, conn=conn)

                    await db_addandsettype(conn, collab, "Member", member_role)
                    await db_addandsettype(conn, collab, "Host", host_role)
                    await db_addandsettype(conn, collab, "Backup", backup_role) 
                    await db_addandsettype(conn, collab, "Notify", notify_role) 

                    for user in hostusers:
                        if host_role not in user.roles:
                            await user.add_roles(host_role)

                    """
                    Structure of a Collab Category:
                    - Info channel (tells you all of the parts and you can claim there and collab info etc)
                    - Announcements channel (announces all drops and claims, notifies users of deadlines, etc)
                    - Finished channel (puts all of the submitted parts' videos there)
                    - Discussion channel (private channel that collab members can use to discuss collab plans and etc.)
                    """

                    admin_roles = await showadminroles(self.bot, asdiscordobjects=True)
                    member_roles = await showmemberroles(self.bot, asdiscordobjects=True)
                    judge_roles = await showjudgeroles(self.bot, asdiscordobjects=True)
                
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    }
                
                    private_overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        host_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        member_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }

                    inbox_overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        host_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    }

                    for role in member_roles:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
                        private_overwrites[role] = discord.PermissionOverwrite(read_messages=False, send_messages=False)

                    for role in admin_roles:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                        private_overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
                    for role in judge_roles:
                        inbox_overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)

                    infotext = await showtext(self.bot, ctx.interaction.guild, collabid=collab, texttoshow="Info", mentions=True)

                    claimstext = await showtext(self.bot, ctx.interaction.guild, collabid=collab, texttoshow="Claims", mentions=True)

                    backupstext = await showtext(self.bot, ctx.interaction.guild, collabid=collab, texttoshow="Backups", mentions=True)

                    groupinfotext = await showtext(self.bot, ctx.interaction.guild, collabid=collab, texttoshow="GroupInfo", mentions=True)

                    prizestext = await showtext(self.bot, ctx.interaction.guild, collabid=collab, texttoshow="Prizes", mentions=True)

                    info_channel = await category.create_text_channel(
                        name="info",
                        reason=None, 
                        position=0, 
                        topic=f'Here is what you need to know about the "{collab_dict[0]['collabname']}" megacollab.', 
                        overwrites=overwrites
                    )

                    channels.append(info_channel)

                    await addtodatabase(self.bot, info_channel, conn=conn)
                    await db_addandsettype(conn, collab, "Info", info_channel)

                    file = await pulllocalsong(self.bot, ctx.interaction.guild, collabid=collab)

                    info_message = await info_channel.send(infotext, file=file)
                
                    await addtodatabase(self.bot, info_message, conn=conn)
                    await db_addandsettype(conn, collab, "Info", info_message)

                    groupinfo_message = await info_channel.send(groupinfotext)  
                        
                    await addtodatabase(self.bot, groupinfo_message, conn=conn)
                    await db_addandsettype(conn, collab, "GroupInfo", groupinfo_message)

                    prizes_message = await info_channel.send(prizestext)  
                        
                    await addtodatabase(self.bot, prizes_message, conn=conn)
                    await db_addandsettype(conn, collab, "Prizes", prizes_message)

                    parts_channel = await category.create_text_channel(
                        name="parts",
                        reason=None, 
                        position=0, 
                        topic=f'Shows the parts from the "{collab_dict[0]['collabname']}" megacollab.', 
                        overwrites=overwrites
                    )

                    channels.append(parts_channel)

                    await addtodatabase(self.bot, parts_channel, conn=conn)
                    await db_addandsettype(conn, collab, "Claims", parts_channel)

                    viewtoput = SelectPartToClaim(int(collab), parts_dict, self.bot, ctx.interaction.guild)

                    claims_message = await parts_channel.send(claimstext, view=viewtoput)  
                        
                    await addtodatabase(self.bot, claims_message, conn=conn)
                    await db_addandsettype(conn, collab, "Claims", claims_message)

                    backups_message = await parts_channel.send(backupstext)  
                        
                    await addtodatabase(self.bot, backups_message, conn=conn)
                    await db_addandsettype(conn, collab, "Backups", backups_message)

                    announcements_channel = await category.create_text_channel(
                        name="announcements",
                        reason=None, 
                        position=1, 
                        topic=f'Announces claims, drops and vacant parts from the "{collab_dict[0]['collabname']}" megacollab.', 
                        overwrites=overwrites
                    )

                    channels.append(announcements_channel)

                    finished_channel = await category.create_text_channel(
                        name="finished",
                        reason=None, 
                        position=2, 
                        topic=f'All the finished parts from the "{collab_dict[0]['collabname']}" megacollab.', 
                        overwrites=overwrites
                    )

                    channels.append(finished_channel)

                    discussion_channel = await category.create_text_channel(
                        name="discussion",
                        reason=None, 
                        position=3, 
                        topic=f'Welcome to the "{collab_dict[0]['collabname']}" megacollab! Here you can discuss with other members about collab matters.', 
                        overwrites=private_overwrites
                    )

                    channels.append(discussion_channel)

                    inbox_channel = await category.create_text_channel(
                        name="inbox",
                        reason=None, 
                        position=3, 
                        topic=f'All submitted parts from "{collab_dict[0]['collabname']}".', 
                        overwrites=inbox_overwrites
                    )

                    channels.append(inbox_channel)

                    await addtodatabase(self.bot, announcements_channel, conn=conn)
                    await addtodatabase(self.bot, finished_channel, conn=conn)
                    await addtodatabase(self.bot, discussion_channel, conn=conn)
                    await addtodatabase(self.bot, inbox_channel, conn=conn)
                
                    await db_addandsettype(conn, collab, "Announcements", announcements_channel)
                    await db_addandsettype(conn, collab, "Finished", finished_channel)
                    await db_addandsettype(conn, collab, "Discussion", discussion_channel)
                    await db_addandsettype(conn, collab, "Inbox", inbox_channel)

                    await conn.execute(
                        'UPDATE "Core".megacollabs set published = $1 where collabid = $2',
                        True, collab_dict[0]['collabid']
                    )
                
        except Exception as e:
            for role in roles:
                await role.delete()
        
            for channel in channels:
                await channel.delete()

            embed = discord.Embed(title=f"❌ An error occurred while publishing {collab_dict[0]['collabname']}, reverting: {e}", color=0xff0000)
            raise
        
        else:
            embed = discord.Embed(title=f"✅ Successfully published {collab_dict[0]['collabname']}", color=0x00ff00)
        
        finally:
            await ctx.followup.send(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(PublishMegacollab(bot))