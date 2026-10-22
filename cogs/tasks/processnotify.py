import asyncio
import json

import asyncpg
import discord
from discord.ext import commands, tasks
from utils.icylogger import logger
from utils.dbcommands import (
    db_showclaims,
    showtext,
    pullcollabmessage,
    pullcollabchannel,
    pullcollabrole
)

CHANNEL = "table_changed"

class DbNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.listen_conn = None
        self._tasks = set()

    def cog_unload(self):
        self.watchdog.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.watchdog.is_running():
            self.watchdog.start()

    @tasks.loop(seconds=30)
    async def watchdog(self):
        if not await self._is_healthy():
            await self._connect()

    @watchdog.after_loop
    async def after_watchdog(self):
        # also runs when the loop is cancelled (cog unload/reload)
        await self._disconnect()

    async def _is_healthy(self):
        if self.listen_conn is None or self.listen_conn.is_closed():
            return False
        try:
            await self.listen_conn.execute("SELECT 1", timeout=10)
            return True
        except Exception:
            return False

    async def _connect(self):
        await self._disconnect()
        conn = None
        try:
            conn = await asyncpg.connect(dsn=self.bot.DB_DSN)
            await conn.add_listener(CHANNEL, self.handle_notify)
            self.listen_conn = conn
            logger.info("Listening on '%s'", CHANNEL)
        except Exception:
            logger.exception("Couldn't start DB listener, will retry")
            if conn is not None:
                await conn.close()

    async def _disconnect(self):
        conn, self.listen_conn = self.listen_conn, None
        if conn is not None and not conn.is_closed():
            try:
                await conn.close(timeout=5)
            except Exception:
                pass


    def handle_notify(self, connection, pid, channel, payload):
        task = asyncio.create_task(self.process_notify(payload))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def process_notify(self, payload):
        logger.info("DB changed: %s", payload)
        data = json.loads(payload)

        try:
            async with self.bot.db.acquire() as conn:
                if data["table"] == "leaderboardhistory":
                    guild = self.bot.get_guild(data['gid'])
                    user = guild.get_member(data['uid'])

                    if data['np'] == 1:
                        idolrole_id = await conn.fetchval(
                            'select roleid from "Associations".idolroles where guildid = $1',
                            guild.id
                            )

                        idolrole = guild.get_role(idolrole_id)

                        for member in idolrole.members:
                            await member.remove_roles(idolrole, reason="New idol crowned")
                            
                        await user.add_roles(idolrole)

                    if data['pp'] is not None:
                        if data['np'] is not None and data['np'] <= data['pp']:
                            ranknotifychannel = await db_pullrankchannel(conn, data['gid'])

                            text = f"**🆙 LEADERBOARD UP!** "
                            if data['np'] == 1:
                                text += f"- {user.mention} **IS THE NEW IDOL!!** (**{p.ordinal(data['np'])}** place)"
                            else:   
                                text += f"{user.mention} - **{p.ordinal(data['np'])}** place!"

                            await ranknotifychannel.send(content=text)


                if data["table"] == "rankhistory":
                    guild = self.bot.get_guild(data['gid'])
                    user = guild.get_member(data['uid'])

                    leaderboardenabledrank = await conn.fetchval(
                        'SELECT rankname from "Core".ranks where isleaderboardenabled = $1',
                        True
                    )

                    text = f"**🆙 RANK UP!** {user.mention} - {data['pr']} → {data['nr']}"
                    # role setting

                    if data['nr'] is not None:
                        nextrankrole_id = await conn.fetchval(
                            'SELECT roleid from "Junctions".ranksxdiscordroles where rankname = $1 and guildid = $2',
                            data['nr'], guild.id
                        )

                        nextrankrole = guild.get_role(nextrankrole_id)

                        if nextrankrole not in user.roles:
                            await user.add_roles(nextrankrole)
                        ...

                    if data['pr'] is not None:
                        prevrankrole_id = await conn.fetchval(
                            'SELECT roleid from "Junctions".ranksxdiscordroles where rankname = $1 and guildid = $2',
                            data['pr'], guild.id
                        )
                        prevrankrole = guild.get_role(prevrankrole_id)

                        if prevrankrole in user.roles:
                            await user.remove_roles(prevrankrole)

                        ranknotifychannel = await db_pullrankchannel(conn, data['gid'])
                    
                        if data['nr'] == leaderboardenabledrank:
                            text += f"\nYou are now on the **{p.ordinal(data['lp'])}** place in the leaderboard!"

                        await ranknotifychannel.send(content=text)

                elif data["table"] == "partsubmissions":
                    submission = await conn.fetchrow(
                        'select storagelocation, levelid from "Core".partsubmissions where submissionid = $1',
                        data['subid']
                    )

                    collabid = await conn.fetchval(
                        'select collabid from "Core".claims where claimid = $1',
                        data['clid']
                    )

                    collabname = await conn.fetchval(
                        'select collabname from "Core".megacollabs where collabid = $1',
                        collabid
                    )

                    userclaim = await db_showuserclaims(byclaimid=data["clid"])

                    user = await self.bot.fetch_user(userclaim[0]['userid'])

                    inboxchannel = await pullcollabchannel(self.bot, conn, collabid=collabid, guild=int(data["gid"]), type="Inbox")

                    text = f"**Part {userclaim[0]['partid']}** submission by {user.mention}"

                    text += f"\n**ID**: {submission['levelid']}" if submission['levelid'] is not None else (f"\n**GDShare file**:" if submission['storagelocation'] is not None else "")

                    if submission['storagelocation'] is not None:
                        path = Path(submission['storagelocation'])
    
                        if path is None:
                            file = None
                        elif path.exists():
                            file = discord.File(path, filename=f"{user.name} - {collabname} Part {userclaim[0]['partid']}.gmd")
                        else:
                            raise FileNotFoundError("File doesn't exist")

                        await inboxchannel.send(
                            content=text,
                            file=file
                        )
                    else:
                        await inboxchannel.send(
                            content=text
                        )

                elif data["table"] == "claims":
                    partclaim = await db_showclaims(self.bot, data["gid"], bycollabid=int(data["cid"]), bypartid=int(data["pid"]))

                    if data['isbk'] or data['prmt']:
                        messagetype = "Backups"
                    else:
                        messagetype = "Claims"
                
                    text = await showtext(self.bot, data["gid"], collabid=int(data["cid"]), texttoshow=messagetype, mentions=True)
                    message = await pullcollabmessage(self.bot, conn, collabid=int(data["cid"]), guild=int(data["gid"]), type=messagetype)

                    try:
                        await message.edit(content=text)
                    except discord.HTTPException as e:
                        if e.code == 30046:
                            await regeneratemessage(conn, message, message.channel, data["cid"], messagetype, message.view)
                            if messagetype == "Claims":
                                backup_message = await pullcollabmessage(self.bot, conn, collabid=int(data["cid"]), guild=int(data["gid"]), type="Backups")
                                await regeneratemessage(conn, backup_message, backup_message.channel, data["cid"], "Backups", backup_message.view)

                    notifychannel = await pullcollabchannel(self.bot, conn, collabid=int(data["cid"]), guild=int(data["gid"]), type="Announcements")
                    notifyrole = await pullcollabrole(conn, self.bot, collabid=int(data['cid']), guild=int(data["gid"]), type="Notify")

                    guild = notifychannel.guild

                    user = guild.get_member(data['uid'])

                    backuprole = await pullcollabrole(conn, self.bot, collabid=int(data['cid']), guild=int(data["gid"]), type="Backup")
                    memberrole = await pullcollabrole(conn, self.bot, collabid=int(data['cid']), guild=int(data["gid"]), type="Member")
                
                    if data['pc'] == 0:
                        if memberrole in user.roles:
                            await user.remove_roles(memberrole)
                    else:
                        if memberrole not in user.roles:
                            await user.add_roles(memberrole)     

                    if data['bc'] == 0:
                        if memberrole in user.roles:
                            await user.remove_roles(backuprole)
                    else:
                        if memberrole not in user.roles:
                            await user.add_roles(backuprole)

                    if partclaim[0]['status'] is None and partclaim[0]['backups'] is None:
                        await notifychannel.send(f"❗ **PART {data["pid"]} IS NOW VACANT!** {notifyrole.mention}")
                    elif partclaim[0]['status'] == "Active" and partclaim[0]['userid'] is not None and not data["isbk"] and not data["drop"] and not data["prmt"]:
                        await notifychannel.send(f"✅ **Part {data["pid"]}** has been claimed by <@{partclaim[0]['userid']}>!")
                    elif partclaim[0]['status'] == "Active" and partclaim[0]['userid'] is not None and not data["isbk"] and not data["drop"]:
                        await notifychannel.send(f"✅ **Part {data["pid"]}** has been dropped, and <@{partclaim[0]['userid']}> has claimed it!")
                    elif partclaim[0]['status'] == "Pending":
                        await notifychannel.send(f"🗒️ <@{partclaim[0]['userid']}> has sent **Part {data["pid"]}** for review.") 
                    elif partclaim[0]['status'] == "Finished":
                        await notifychannel.send(f"✅ <@{partclaim[0]['userid']}> has finished **Part {data["pid"]}**! Congratulations!") 
    
        except Exception:
            logger.exception("process_notify crashed")


def setup(bot):
    bot.add_cog(DbNotify(bot))