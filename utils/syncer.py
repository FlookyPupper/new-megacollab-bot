from utils.dbcommands import *
from utils.icylogger import logger
from utils.parseintodict import parseintodict
import asyncpg
import argparse

async def sync_server_to_database(bot, args):
    list_of_members = []
    list_of_roles = []

    async with bot.db.acquire() as conn:
        logger.info(
            "Connected to DB=%s as %s",
            await conn.fetchval("select current_database()"),
            await conn.fetchval("select current_user")
        )
        ranks = await db_showrank(bot=bot, conn=conn)
    
        if args.admin_role:
            try:
                guildid_str, roleid_str = args.admin_role.split(';')
                guildid = int(guildid_str)
                roleid = int(roleid_str)

                await conn.execute(
                    'SELECT "Core".setadminrole($1, $2)',
                    guildid, roleid
                )
                logger.info(f"Admin role set: Guild {guildid}, Role {roleid}")

            except ValueError:
                logger.error("Invalid --admin-role format. Use <GuildID>;<RoleID> with integers.")
                os.kill(os.getpid(), signal.SIGTERM)

    logger.info(f"Synchronizing guilds to the database... This might take a while.")
    for guild in bot.guilds:
        async with bot.db.acquire() as conn:
            adminroles = await conn.fetch('select * from "Associations".adminroles where guildid = $1', guild.id)

            isrankenabled = await conn.fetchval('select ranksenabled from "Discord".guilds where guildid = $1', guild.id)

            try:
                await addtodatabase(bot, guild)
                debug = await conn.fetch(
                    'SELECT "Core".adddiscordguild($1)', 
                    guild.id
                )
            except Exception as e:
                logger.error(f"An error occurred while syncing {guild} to the database")
                logger.error(e)
            else:
                logger.info(f"Added {guild}")
                logger.info(debug)

        if adminroles is None or len(adminroles) == 0:
            #logger.warning(f"No admin role set for guild {guild.id}.")
            #logger.warning(f"If you're an admin, run Icy in a terminal with the --admin-role <GuildID>;<RoleID> to configure it, and specify your Role ID. Then, run Icy again without arguments")

            logger.info(f"Synchronizing {guild} to the database...")
            
        rankroles_dict = await db_showrankroles(bot=bot, guild=guild)

        if not rankroles_dict and isrankenabled:
            logger.warning("There are no rank roles set. An admin must manually set each role to be given for each rank with /prop rankrole.\nOnce you have done it, please restart the bot.")

        logger.info(f'Synchronizing members from "{guild}" to the database... This might take a while.')
        for member in guild.members:
            if not member.bot: 
                try:
                    member_roles = set(await showmemberroles(bot, asdiscordobjects=True))

                    if set(member.roles) & member_roles:
                        await addtodatabase(bot, member, member.guild)

                    async with bot.db.acquire() as conn:
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

                        if idol is not None and idolrole not in idol.roles:
                            for member in idolrole.members:
                                await member.remove_roles(idolrole, reason="Bot startup")
            
                            await idol.add_roles(idolrole)

                        userseasontokens = await conn.fetchval(
                            'select seasontokens from "Core".users where guildid = $1 and userid = $2',
                            member.guild.id, member.id
                        )

                        if userseasontokens is not None:
                            correspondingrank = await db_showrank(bot=bot, bythreshold=userseasontokens, conn=conn)

                            rankrole_id = await conn.fetchval(
                                'SELECT roleid from "Junctions".ranksxdiscordroles where rankname = $1 and guildid = $2',
                                    correspondingrank['rankname'], member.guild.id
                                )

                            rankrole = guild.get_role(rankrole_id)

                            if rankrole and rankrole not in member.roles:
                                await member.add_roles(rankrole)

                            rankrolestoremove = rankroles_dict.copy()

                            rankrolestoremove.pop(correspondingrank["rankname"], None)

                            rankrolestoremove = set(rankrolestoremove.values()) & set(member.roles)

                            if rankrolestoremove:
                                await member.remove_roles(*rankrolestoremove)
                        else:
                            logger.warning(f"{member.name} doesn't exist in the database. This might be caused by missing Member roles. Please set a Member role by using /prop memberrole and restart the bot.")

                except TypeError as e:
                    raise e

        logger.info(f"Synchronizing roles from {guild} to the database... This might take a while.")
        for role in guild.roles:
            try:
                await addtodatabase(bot, role, role.guild)
            except (TypeError, asyncpg.CheckViolationError):
                pass

        logger.info(f"Registering views...")
        if args.refresh_views:
            logger.warning("(You have launched Bracelety with the --refresh-views argument, which will proactively change the code of persistent views that already exist.)")
            logger.warning("(You should only use this option if you changed the source code for any of the persistent views.)")
            messagetypes = await db_showallmessagetypes()
        collabs = await db_showcollabs(bot)
        try:
            collabs = await parseintodict(collabs)
        except ValueError:
            collabs = []
        
        

        if len(collabs) > 0:
            async with bot.db.acquire() as conn:
                for collab in collabs:
                    if args.refresh_views:
                        for messagetype in messagetypes:
                            try:
                                infochannel = await pullcollabchannel(conn, collab['collabid'], "Info")
                            except TypeError as e:
                                logger.info(f"Ignoring Info channel for {collab['collabname']} (not published?)")
                                break

                            try:
                                messagetorefresh = await pullcollabmessage(conn=conn, collabid=collab['collabid'], type=messagetype)
                                texttorefresh = await showtext(collab['collabid'], messagetype, mentions=True, filename=messagetorefresh.attachments[0].filename if messagetorefresh.attachments else None)
                            except TypeError as e:
                                logger.info(f"Adding message {messagetype} for {collab['collabname']} because it does not exist")
                                texttorefresh = await showtext(collab['collabid'], messagetype, mentions=True)
                                message = await infochannel.send(texttorefresh)
                                await addtodatabase(bot, message, conn=conn)
                                await db(conn, collab['collabid'], messagetype, message)

                            else:
                                if messagetype == "Claims":
                                    view = SelectPartToClaim(
                                            collab['collabid'],
                                            await parseintodict(await db_showparts(collab['collabid']))
                                            )
                                else:
                                    view = None

                                try:
                                    await messagetorefresh.edit(
                                        content=texttorefresh,
                                        view=view)
                                except discord.HTTPException as e:
                                    if e.code == 30046:
                                        logger.info(f"Persistent message from {collab['collabname']} has reached edit limit, we are going to regenerate it")
                                        await regeneratemessage(messagetorefresh, messagetorefresh.channel, collab['collabid'], messagetype, view)
                    else:
                        bot.add_view(
                            SelectPartToClaim(
                            collab['collabid'],
                            await parseintodict(await db_showparts(collab['collabid']))
                            )
                        )
                    logger.info(f'View of collab "{collab['collabname']}" edited successfully')

        text = "All views successfully"

        if args.refresh_views:
            logger.info(f"{text} REFRESHED!")
        else:
            logger.info(f"{text} registered!")

    logger.info(f"Cleaning unused and deleted roles...")    
    async with bot.db.acquire() as conn:
        adminroles = await conn.fetch('select * from "Associations".adminroles')
        caca = await showallroles(bot, conn, exceptcollab=True)

        for role in caca:
            if not isinstance(role, discord.Role) and isinstance(role, dict) and role['deleted'] == True:
                await db_deleterole(bot, conn, role['guildid'], role['roleid'], True)

    logger.info("Server synchronization process complete!")