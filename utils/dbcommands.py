import asyncpg
import discord
from utils.parseintodict import parseintodict
from utils.timeparser import (parse_time_to_seconds, parse_seconds_to_time)
from pathlib import Path

async def db_associatehostwithcollab(
    conn,
    guildid: int,
    userid: int,
    collabid: int
):
    await conn.execute(
        'CALL "Core".associatehostwithcollab($1, $2, $3)', 
        guildid, userid, collabid
    )

async def db_claimpart(
    conn,
    guildid: int,
    userid: int,
    collabid: int,
    partid: int
):
    await conn.execute(
        'SELECT "Core".claimpart($1, $2, $3, $4)', 
        guildid, userid, collabid, partid
    )

async def db_droppart(
    conn,
    guildid: int,
    userid: int,
    collabid: int,
    partid: int
):
    await conn.execute(
        'SELECT "Core".droppart($1, $2, $3, $4)', 
        guildid, userid, collabid, partid
    )

async def db_createmegacollab(
    conn,
    guild: discord.Guild,
    name: str, 
    songid: int, 
    durationindays: int, 
    difficultyid: int,
    maxgroups: Optional[int]=500,
    seasontokensrequired: Optional[int]=0, 
    customstartdate: Optional[int]=None,
    acknowledgeduplication: Optional[bool]=False,
):
    collabid = await conn.fetchval(
        'SELECT "Core".createmegacollab($1, $2, $3, $4, $5, $6, $7, $8, $9)', 
        name, guild.id, songid, durationindays, difficultyid, maxgroups, seasontokensrequired, customstartdate, acknowledgeduplication
    )

    return collabid

async def db_addpartsubmission(
    conn,
    claimid: int,
    level: str=None, 
    levelid: int=None
):
    await conn.execute(
        'SELECT "Core".addpartsubmission($1, $2, $3)', 
        claimid, level, levelid
    )

async def db_associatesongwithartist(
    conn,
    songid: int,
    artistid: int
):
    await conn.execute(
        'CALL "Core".associatesongwithartist($1, $2)', 
        songid, artistid
    )

async def db_addpart(
    conn,
    newpartid: int, # this is int2 in the procedure and in the table
    collabid: int, # this is int4 in the procedure and in the table
    guildid: int, 
    offsetstart: int, # this is numeric in the procedure and in the table 
    offsetend: int, # this is numeric in the procedure and in the table
    rating: int # this is between 1 and 5
):
    await conn.execute(
        'CALL "Core".addpart($1, $2, $3, $4, $5, $6)', 
        newpartid, collabid, guildid, offsetstart, offsetend, rating
        )

async def db_addsonglink(
    conn,
    songid: int, 
    platformofchoice: str, 
    idoraddresstoadd: str, 
    idusertoadd: str=None,
    replacementidtoadd: int=None
):
    await conn.execute(
        'SELECT "Core".addsonglink($1, $2, $3, $4, $5)', 
        songid, platformofchoice, idoraddresstoadd, replacementidtoadd, idusertoadd
        )


async def db_createsong(
    conn,
    name: str, 
    guild: discord.Guild,
    acknowledgeduplication: Optional[bool]=False,
):
    songid = await conn.fetchval(
        'SELECT "Core".createsong($1, $2, $3)', 
        name, guild.id, acknowledgeduplication
    )
            
    return songid

async def db_createartist(
    conn,
    name: str, 
    guild: discord.Guild,
    acknowledgeduplication: Optional[bool]=False,
):
    artistid = await conn.fetchval(
        'SELECT "Core".createartist($1, $2, $3)', 
        name, guild.id, acknowledgeduplication
    )
            
    return artistid

async def db_adddiscordrole(
    conn,
    roleid: int,
    rolename: str
):
    await conn.execute(
        'SELECT "Core".adddiscordrole($1, $2)', 
        roleid, rolename
    )

async def db_adddiscordmessage(
    conn,
    messageid: int,
    channelid: int
):
    await conn.execute(
        'SELECT "Core".adddiscordmessage($1, $2)', 
        messageid, channelid
    )

async def db_adddiscordguild(
    conn,
    guildid: int
):
    await conn.execute(
        'SELECT "Core".adddiscordguild($1)', 
        guildid
    )

async def db_deletemessage(
    conn,
    channelid: int,
    messageid: int
):
    await conn.execute(
        'SELECT "Core".deletemessage($1, $2)', 
        channelid, messageid
    )

async def db_addandsettype(
    conn,
    collabid: int,
    typetoset: str,
    objecttoadd: Union[discord.Role, discord.Message, discord.TextChannel]
):
    match objecttoadd:
        case discord.Role():
            await conn.execute(
                'SELECT "Core".setroletype($1, $2, $3, $4)', 
                collabid, typetoset, int(objecttoadd.id), int(objecttoadd.guild.id)
            )
        case discord.Message():               
            await conn.execute(
                'SELECT "Core".setmessagetype($1, $2, $3, $4, $5)', 
                collabid, typetoset, int(objecttoadd.id), int(objecttoadd.channel.id), int(objecttoadd.guild.id)
            )
        case discord.TextChannel():
            await conn.execute(
                'SELECT "Core".setchanneltype($1, $2, $3, $4)', 
                collabid, typetoset, int(objecttoadd.id), int(objecttoadd.guild.id)
            )

async def getschemaversion(bot) -> dict:
    async with bot.db.acquire() as conn:
        schemaversion = await conn.fetchrow('select * from "Core".showversion()')
    
    schemaversion = {
        'API_VERSION': schemaversion['apiversion'],
        'REVISION': schemaversion['revision'],
        'VERSION_STRING': schemaversion['versionstring'],
    }
    
    return schemaversion

async def addtodatabase_helper(objecttoadd: Union[discord.Role, discord.Member, discord.User, discord.Guild, discord.Message, discord.TextChannel], guild: discord.Guild, conn):
    match objecttoadd:
        case discord.Role():
            if not isinstance(guild, discord.Guild):
                raise TypeError("Not a Guild")

            if objecttoadd is not None and guild is not None:
                await conn.execute(
                    'SELECT "Core".adddiscordrole($1, $2, $3)', 
                    guild.id, objecttoadd.id, objecttoadd.name
                )
            else:
                raise ValueError("Guild is missing")
        case discord.Message():
            await conn.execute(
                'SELECT "Core".adddiscordmessage($1, $2)', 
                objecttoadd.id, objecttoadd.channel.id
            )
        case discord.User() | discord.Member():
            if objecttoadd is not None and guild is not None:
                await conn.execute(
                    'SELECT "Core".adduser($1, $2)', 
                    objecttoadd.id, guild.id
                )
            else:
                raise ValueError("Guild is missing")
        case discord.Guild():
            await conn.execute(
                'SELECT "Core".adddiscordguild($1)', 
                objecttoadd.id
            )
        case discord.TextChannel():
            await conn.execute(
                'SELECT "Core".adddiscordchannel($1)', 
                objecttoadd.id
            )
        case _:
            raise TypeError("Not a discord object.")

async def regeneratemessage(conn, message: discord.Message, channel: discord.TextChannel, collabid: int, type: str, view: discord.ui.View):
    channeltoresendin = channel
    await db_deletemessage(message.channel, message)
    await message.delete()

    texttorefresh = await showtext(collabid, messagetype, mentions=False)

    message = await channel.send(content=texttorefresh, view=view)

    await addtodatabase(message)
    await db_addandsettype(conn, type, message)

    texttorefresh = await showtext(collabid, messagetype, mentions=True)

    message.edit(content=texttorefresh)

async def addtodatabase(bot, objecttoadd: Union[discord.Role, discord.Member, discord.User, discord.Guild, discord.Message, discord.TextChannel], guild: discord.Guild=None, conn=None):
    """Adds a discord object to the database, takes discord role object as parameter"""
    if conn is not None:
        await addtodatabase_helper(objecttoadd, guild, conn)
    else:
        async with bot.db.acquire() as conn:
            await addtodatabase_helper(objecttoadd, guild, conn)

async def show_user_info(bot, user: Union[discord.User, discord.Member], guild: discord.Guild):
    async with bot.db.acquire() as conn:
        info = await conn.fetchrow(
            'SELECT * from "Core".showuser($1, $2)', 
            user.id, guild.id
        )

    return info

async def db_showleaderboard(bot, user: Union[discord.User, discord.Member]=None, guild: discord.Guild=None) -> list[dict]:
    new_dict = []

    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showleaderboard($1, $2)', 
            guild.id, user.id
        )

    for user in info:
        new_dict.append(
            {
                'guildid': user['guildid'],
                'position': user['leaderboardposition'],
                'userid': user['userid'],
                'seasontokens': user['seasontokens'],
                'rank': user['rank'],
                'isleaderboardenabled': user['isleaderboardenabled']
            }
        )
        
    return new_dict

async def db_showrank(bot, bythreshold: int=None, conn: asyncpg.Connection=None) -> Union[list, list[dict]]:
    sql = 'select rankname from "Core".showrank($1)'

    if conn is None:
        async with bot.db.acquire() as conn:
            if bythreshold is not None:
                rank = await conn.fetchrow(sql, bythreshold)
            else:
                rank = await conn.fetch(sql, bythreshold)
    else:
        if bythreshold is not None:
            rank = await conn.fetchrow(sql, bythreshold)
        else:
            rank = await conn.fetch(sql, bythreshold)
    
    return rank

async def db_showrankroles(bot, guild: discord.Guild, bythreshold: int=None, conn: asyncpg.Connection=None) -> list:
    ranks = await db_showrank(bot, bythreshold=bythreshold, conn=conn)

    rankrole_dict = {}

    if conn is not None:
        rankroles = await conn.fetch(
            'select rankname, roleid from "Junctions".ranksxdiscordroles where guildid = $1',
            guild.id
        )
    else:
        async with bot.db.acquire() as conn:
            rankroles = await conn.fetch(
                'select rankname, roleid from "Junctions".ranksxdiscordroles where guildid = $1',
                guild.id
            )
    
    for rankrole in rankroles:
        role = guild.get_role(rankrole["roleid"])

        if role is None:
            role = guild.fetch_role(rankrole["roleid"])

        rankrole_dict[rankrole["rankname"]] = role

    return rankrole_dict

async def db_showidol(bot, guild: discord.Guild) -> list[dict]:
    new_dict = {}
    
    async with bot.db.acquire() as conn:
        info = await conn.fetchrow(
            'SELECT * from "Core".showidol($1)', 
            guild.id
        )

    new_dict = {
        'guildid': info['guildid'],
        'position': info['leaderboardposition'],
        'userid': info['userid'],
        'seasontokens': info['seasontokens'],
        'rank': info['rank'],
        'isleaderboardenabled': info['isleaderboardenabled']
    }
    
    return new_dict

async def db_showcollabs(bot, guild, bycollabid: int=None, bycollabname: str=None):
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showcollabs($1, $2, $3)', 
            guild.id if not isinstance(guild, int) else guild, bycollabid, bycollabname
        )
        
    return info

async def db_showartistname(bot, guild, artistid: int):
    query = await db_showartists(bot, guild, artistid)
    query = await parseintodict(query)
    return query[0]['artistname']

async def pullcollabrole(conn, bot, collabid: int, guild: discord.Guild, type: str) -> discord.Role:
    info = await conn.fetchrow(
        'SELECT * from "Core".showrole($1, $2, $3)',
        collabid, guild if isinstance(guild, int) else guild.id, type
    )
    
    guild = bot.get_guild(info['guildid'])
            
    if guild is None:
        raise EnvironmentError("Bot not in guild or not cached")

    role = guild.get_role(info['roleid'])
   
    return role

async def showallroles(bot, conn, exceptcollab: bool=False) -> discord.Role:
    info = await conn.fetch(
        'SELECT * from "Core".showallroles($1)',
        exceptcollab
    )

    roles = []

    for role in info:
        guild = bot.get_guild(role['guildid'])
            
        if guild is None:
            raise EnvironmentError("Bot not in guild or not cached")

        roletoadd = guild.get_role(role['roleid'])

        if roletoadd is None:
            roles.append({'guildid': role['guildid'], 'roleid': role['roleid'], 'deleted': True})
        else:
            roles.append(roletoadd)
   
    return roles

async def db_deleterole(conn, guildid: int, roleid: int, exceptcollab: bool=False) -> discord.Role:
    info = await conn.fetch(
        'SELECT * from "Core".deleterole($1, $2, $3)',
        guildid, roleid, exceptcollab
    )

async def db_showallmessagetypes(bot) -> list[str]:
    async with bot.db.acquire() as conn:
        types = await conn.fetchval(
            'select "Core".showmessagetypes()'
        )

    return types

async def pullcollabmessage(bot, conn, collabid: int, guild: discord.Guild, type: str) -> discord.Message:
    info = await conn.fetchrow(
        'SELECT * from "Core".showmessage($1, $2, $3)',
        collabid, guild if isinstance(guild, int) else guild.id, type
    )

    if info is None:
        raise TypeError("Message doesn't exist")
    
    channel = await bot.fetch_channel(info['channelid'])
    message = await channel.fetch_message(info['messageid'])

    return message

async def pullcollabchannel(bot, conn, collabid: int, guild: discord.Guild, type: str) -> discord.TextChannel:
    info = await conn.fetchval(
        'SELECT "Core".showchannel($1, $2, $3)',
        collabid, guild if isinstance(guild, int) else guild.id, type
    )

    if info is None:
        raise TypeError("Channel doesn't exist")
    
    channel = await bot.fetch_channel(int(info))

    return channel

async def db_pullrankchannel(conn, guildid: int) -> discord.TextChannel:
    info = await conn.fetchrow(
        'SELECT guildid, channelid from "Associations".ranknotificationchannels where guildid = $1',
        guildid
    )

    if info is None:
        raise TypeError("Channel doesn't exist")

    channel = bot.get_channel(info['channelid'])

    if channel is None:
        guild = await bot.fetch_guild(info['guildid'])
        channel = await guild.fetch_channel(info['channelid'])

    return channel

async def showadminroles(bot, asdiscordobjects: bool=False) -> list[dict]:
    new_dict = []

    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showadminroles()'
        )

    for row in info:
        if not isinstance(row, asyncpg.Record):
            raise ValueError("List does not seem to contain Records")

        if asdiscordobjects:
            guild = bot.get_guild(row['guildid'])
            
            if guild is None:
                raise EnvironmentError("Bot not in guild or not cached")

            role = guild.get_role(row['roleid'])

            new_dict.append(role)

        else:
            new_dict.append(
                {
                    "roleid": row['roleid'],
                    "guildid": row['guildid']
                }
            )
        
    return new_dict

async def showmemberroles(bot, asdiscordobjects: bool=False) -> list[dict]:
    new_dict = []

    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showmemberroles()'
        )
    
    for row in info:
        if not isinstance(row, asyncpg.Record):
            raise ValueError("List does not seem to contain Records")

        if asdiscordobjects:
            guild = bot.get_guild(row['guildid'])
            
            if guild is None:
                raise EnvironmentError("Bot not in guild or not cached")

            role = guild.get_role(row['roleid'])

            new_dict.append(role)

        else:
            new_dict.append(
                {
                    "roleid": row['roleid'],
                    "guildid": row['guildid']
                }
            )
        
    return new_dict

async def showjudgeroles(bot, asdiscordobjects: bool=False) -> list[dict]:
    new_dict = []

    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showjudgeroles()'
        )
    
    for row in info:
        if not isinstance(row, asyncpg.Record):
            raise ValueError("List does not seem to contain Records")

        if asdiscordobjects:
            guild = bot.get_guild(row['guildid'])
            
            if guild is None:
                raise EnvironmentError("Bot not in guild or not cached")

            role = guild.get_role(row['roleid'])

            new_dict.append(role)

        else:
            new_dict.append(
                {
                    "roleid": row['roleid'],
                    "guildid": row['guildid']
                }
            )
        
    return new_dict

async def concatenateartists(artistnames: list) -> str:
    
    artist_list = artistnames

    if len(artist_list) == 0:
        concatenated_artists = ""
    elif len(artist_list) == 1:
        concatenated_artists = artist_list[0]
    else:
        concatenated_artists = ", ".join(artist_list[:-1]) + f" and {artist_list[-1]}"

    return concatenated_artists

async def showfriendlysongnames(songs: list) -> list[discord.OptionChoice]:
    list_of_songs = []

    for row in songs:
        artistnames = await concatenateartists(row['artistname'])

        label = f"{row['songname']} by {artistnames}"

        #list_of_songs[label] = str(row['songid'])
        list_of_songs.append(
            discord.OptionChoice(
                name=label,
                value=str(row['songid'])
            )
        )

    return list_of_songs

async def showfriendlycollabnames(collabs: list) -> list[discord.OptionChoice]:
    list_of_collabs = []

    for row in collabs:
        label = f"{row['collabname']} (ID: {row['collabid']})"

        #list_of_collabs[label] = str(row['collabid'])
        list_of_collabs.append(
            discord.OptionChoice(
                name=label,
                value=str(row['collabid'])
            )
        )

    return list_of_collabs

async def showfriendlyartistnames(collabs: list) -> dict:
    list_of_artists = []

    for row in collabs:
        #label = f"{row['artistname']} (ID: {row['artistid']})"
        label = f"{row['artistname']}"

        #list_of_artists[label] = str(row['artistid'])
        list_of_artists.append(
            discord.OptionChoice(
                name=label,
                value=str(row['artistid'])
            )
        )

    return list_of_artists

async def showfriendlydifficulties(difficulties: list) -> list[discord.OptionChoice]:
    list_of_difficulties = []
    for row in difficulties:
        return

async def showfriendlyparts(parts: list) -> dict:
    list_of_parts = []

    for row in parts:
        label = f"Part {row['partid']} / {await parse_seconds_to_time(row['offsetstart'])} - {await parse_seconds_to_time(row['offsetend'])} (Rating: {row['rating']})"

        #list_of_parts[label] = str(row['partid'])
        list_of_parts.append(
            discord.OptionChoice(
                name=label,
                value=str(row['partid'])
            )
        )

    return list_of_parts

async def getschemaversion(bot) -> dict:
    async with bot.db.acquire() as conn:
        schemaversion = await conn.fetchrow('select * from "Core".showversion()')
    
    schemaversion = {
        'API_VERSION': schemaversion['apiversion'],
        'REVISION': schemaversion['revision'],
        'VERSION_STRING': schemaversion['versionstring'],
    }
    
    return schemaversion

async def db_showsong(bot, guild, bysongid=None, byartistid=None, byname=None):
    print(f"Bot: {bot}\nGuild: {guild.id}\nSongID: {bysongid}\nArtistID: {byartistid}\nName: {byname}")
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showsong($1, $2, $3, $4)', 
            guild.id, bysongid, byartistid, byname
        )
    
    return info

async def db_doesartistexist(bot, artistid: int):
    async with bot.db.acquire() as conn:
        info = await conn.fetchval(
            'SELECT "Core".doesartistexist($1)', 
            artistid
        )

    return info

# e


async def db_checkduplicates(bot, guild: discord.Guild, name: str, table: str):
    async with bot.db.acquire() as conn:
        match table:
            case 'megacollabs':
                info = await conn.fetch(
                    '''
                    SELECT id AS collabid, 
                           name AS collabname, 
                           normalizedname AS normalizedname,
                           extraid as songid
                    FROM "Core".checkduplicates($1, $2, $3)
                    ''', 
                    guild.id, name, table
                )
            case 'songs':
                info = await conn.fetch(
                    '''
                    SELECT id AS songid, 
                           name AS songname, 
                           normalizedname AS normalizedname 
                    FROM "Core".checkduplicates($1, $2, $3)
                    ''', 
                    guild.id, name, table
                )
            case 'artists':
                info = await conn.fetch(
                    '''
                    SELECT id AS artistid, 
                           name AS artistname, 
                           normalizedname AS normalizedname 
                    FROM "Core".checkduplicates($1, $2, $3)
                    ''', 
                    guild.id, name, table
                )
            case _:
                raise ValueError("Invalid table")

    return info

async def db_showparts(bot, guild, collabid: int):
    collabid = int(collabid)

    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showparts($1, $2)', 
            collabid, guild.id if not isinstance(guild, int) else guild
        )
    
    return info

async def db_showclaims(bot, guild, bycollabid: Optional[int]=None, bypartid: Optional[int]=None, byuserid: Optional[int]=None):
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showclaims($1, $2, $3, $4)', 
            guild.id if not isinstance(guild, int) else guild, bycollabid, bypartid, byuserid
        )
    
    return info

async def db_showuserclaims(
    bot,
    guild, 
    bycollabid: Optional[int]=None, 
    bypartid: Optional[int]=None, 
    byuserid: Optional[int]=None, 
    byclaimid: Optional[int]=None, 
    bystatus=None, 
    bytype=None
):
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showuserclaims($1, $2, $3, $4, $5, $6, $7)', 
            guild.id, bycollabid, bypartid, byuserid, byclaimid, bystatus, bytype
        )
    
    return info

async def db_setranknotificationchannel(bot, channel: discord.TextChannel):
    async with bot.db.acquire() as conn:
        await conn.execute(
            'SELECT * from "Core".setranknotificationchannel($1, $2)', 
            channel.guild.id, channel.id
        )

async def db_associaterolewithrank(bot, rank: str, role: discord.Role):
    async with bot.db.acquire() as conn:
        await conn.execute(
            'SELECT * from "Core".associaterolewithrank($1, $2, $3)', 
            rank, role.guild.id, role.id
        )

async def db_setidolrole(bot, role: discord.Role):
    async with bot.db.acquire() as conn:
        await conn.execute(
            'SELECT * from "Core".setidolrole($1, $2)', 
            role.guild.id, role.id
        )

async def db_setjudgerole(bot, role: discord.Role):
    async with bot.db.acquire() as conn:
        await conn.execute(
            'SELECT * from "Core".setjudgerole($1, $2)', 
            role.guild.id, role.id
        )

async def db_showcollabidbymessage(bot, channelid: int, messageid: int):
    async with bot.db.acquire() as conn:
        info = await conn.fetchval(
            'SELECT * from "Core".showcollabidfrommessage($1, $2)', 
            channelid, messageid
        )
    
    return info

async def db_showartists(bot, guild: discord.Guild, byartistid: int=None, byartistname: str=None, bylistofartists: list=None):
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showartists($1, $2, $3, $4)', 
            guild.id, byartistid, byartistname, bylistofartists
        )
        
    return info

async def db_showdifficulties(bot, query=None):
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * FROM "Core".showdifficulties($1)', 
            query
        )
    
    return info

async def showfriendlydifficultynames(difficulties: list) -> list[discord.OptionChoice]:
    list_of_difficulties = []

    for row in difficulties:
        label = f"{row['difficulty']}"

        if row['difficulty'] == "Demon":
            label = f"{row['demondifficulty']} {label}"

        label += f" {row['stars']}⭐"

        #list_of_songs[label] = str(row['songid'])
        list_of_difficulties.append(
            discord.OptionChoice(
                name=label,
                value=str(row['difficultyid'])
            )
        )

    return list_of_difficulties

async def pulllocalsong(bot, guild, collabid: int):
    pull_collab = await db_showcollabs(bot, guild, bycollabid=int(collabid))
    collab_dict = await parseintodict(pull_collab)
    pull_song = await db_showsong(bot, guild, bysongid=collab_dict[0]['songid'])
    song_dict = await parseintodict(pull_song)

    path = Path(song_dict[0]['storagelocation'])
    
    if path is None:
        file = None
    elif path.exists():
        file = discord.File(path, filename=f"{song_dict[0]['replacementid']}.mp3")
    else:
        raise FileNotFoundError("File doesn't exist")

    return file

async def showtext(bot, guild, collabid: int, texttoshow: str, mentions: bool, filename: str=None):
    pull_collab = await db_showcollabs(bot, guild, bycollabid=int(collabid))
    record = await db_showparts(bot, guild, int(collabid))
    claim_record = await db_showclaims(bot, guild, bycollabid=int(collabid))
        
    parts_dict, collab_dict, claim_dict = await parseintodict(record), await parseintodict(pull_collab), await parseintodict(claim_record)

    text = ""
        
    if len(parts_dict) != len(claim_dict):
        raise ValueError("no")

    lines = []

    if texttoshow == "Claims":
        groups = 500
        totalparts = len(parts_dict)

        total_part_groups = int(groups / totalparts)

        for row, row2 in zip(parts_dict, claim_dict):
            if row2['userid'] is None:
                user = f"*Unclaimed*"
            else:
                if mentions:
                    user = f"<@{row2['userid']}>"
                else:
                    user = f"{row2['userid']}"

            partdurationinseconds = int(row['offsetendseconds']) - int(row['offsetstartseconds'])

            partdefinitiontext = f"**Part {row['partnumber']}** - {user}"

            if row2['status'] == 'Pending':
                lines.append(f"## {partdefinitiontext}")
                lines.append("🗒️ **Pending Review**")

            elif row2['status'] == 'Finished':
                lines.append(f"## ~~{partdefinitiontext}~~")
                lines.append("✅ **Finished**")

            else:
                lines.append(f"## {partdefinitiontext}")

                offsettext = f"{row['offsetstartseconds']} - {row['offsetendseconds']}\n({await parse_seconds_to_time(row['offsetstartseconds'])} - {await parse_seconds_to_time(row['offsetendseconds'])})"

                if partdurationinseconds >= 15:
                    offsettext += f"\n**(Long Part)**"

                lines.append(offsettext)

                if row['partnumber'] == 1:
                    initialgroups = 4
                    limitgroups = total_part_groups
                else:
                    initialgroups = total_part_groups * (row['partnumber'] - 1) + 1
                    limitgroups = total_part_groups * row['partnumber']

                group_text = f"**Groups/Colours**: {initialgroups} - {limitgroups}"

                lines.append(group_text)

                stars = f"**{row['rating']}**⭐"

                rating_text = f"{stars} "

                # Rating description
                if row['rating'] <= 2:
                    rating_text += "- *Boring Part*"
                elif row['rating'] == 3:
                    rating_text += "- *Neutral*"
                else:
                    rating_text += "- *Expressive Part*"

                lines.append(rating_text)

            lines.append("")  # extra newline

    elif texttoshow == "Info":
        lines.append(f"# {collab_dict[0]['collabname']}")

        totaldurationinseconds = parts_dict[-1]['offsetendseconds'] - parts_dict[0]['offsetstartseconds']

        totaldurationintime = await parse_seconds_to_time(totaldurationinseconds)

        duration_text = f"**Duration**: {totaldurationintime} "

        theme_text = f"**Theme**: {collab_dict[0]['category']}"

        prefix = ""
        if (
            collab_dict[0]["demondifficulty"] is not None
            and collab_dict[0]["difficulty"] == "Demon"
            and collab_dict[0]["stars"] == 10
        ):
            prefix = collab_dict[0]["demondifficulty"] + " "

        difficulty_conc = f"{prefix}{collab_dict[0]['difficulty']} **{collab_dict[0]['stars']}**⭐"

        difficulty_text = f"**Difficulty**: {difficulty_conc}"
        
        if totaldurationinseconds in range(0, 9):
            geometrydashlength = "Tiny"
        elif totaldurationinseconds in range(10, 29):
            geometrydashlength = "Short"
        elif totaldurationinseconds in range(30, 59):
            geometrydashlength = "Medium"
        elif totaldurationinseconds in range(60, 119):
            geometrydashlength = "Long"
        else:
            geometrydashlength = "XL"

        duration_text += f"*({geometrydashlength})*"

        lines.append(duration_text)

        lines.append(difficulty_text)

        lines.append(theme_text)

        song = await db_showsong(bot, guild, bysongid=collab_dict[0]['songid'])

        print(song)

        song_dict = await parseintodict(song)

        if song_dict[0]['newgroundslink'] is not None:
            linktoshow = f"{song_dict[0]['newgroundslink']}"
        elif song_dict[0]['youtubelink'] is not None:
            linktoshow = f"{song_dict[0]['youtubelink']}"
        elif song_dict[0]['bandcamplink'] is not None:
            linktoshow = f"{song_dict[0]['bandcamplink']}"
        elif song_dict[0]['soundcloudlink'] is not None:
            linktoshow = f"{song_dict[0]['soundcloudlink']}"
        else:
            linktoshow = None

        lines.append("")        
        
        songname = f'🎵 {f"[{song_dict[0]['songname']}]({linktoshow})" if linktoshow is not None else f"{song_dict[0]['songname']}"}'
        songname += f" by {await concatenateartists(song_dict[0]['artistname'])} {"***(NONG)***" if song_dict[0]['isnong'] else ""}"

        lines.append(songname)  

        replacementid_text = f"**Replacement ID**: {song_dict[0]['replacementid']}"

        if filename is not None and song_dict[0]['replacementid'] is not None:
            if not filename.isdigit() or int(filename) != song_dict[0]['replacementid']:
                lines.append(replacementid_text)
     

        lines.append("")  # extra newline

        timetext = f"**Deadline**: <t:{int(collab_dict[0]['finishdate'].timestamp())}:f>"

        lines.append(timetext)

    elif texttoshow == "GroupInfo":
        group_info = f"# Reserved Colours and Groups\n"

        group_info += f"**Colour 1** - Black\n"
        group_info += f"**Colour 2** - White\n"
        group_info += f"**Group 1** - Alpha 0\n"
        group_info += f"**Group 2** - Alpha 0.5\n"
        group_info += f"**Group 3** - Follow Player Y\n"
        
        lines.append(group_info)

    elif texttoshow == "Backups":
        lines.append("# Backups")

        backup_list = []

        for row, row2 in zip(parts_dict, claim_dict):
            part_text = f"- **Part {row['partnumber']}** - "   
            if row2['backups'] is not None:
                if mentions:
                    backup_text = f"{" ".join(f"<@{b}>" for b in row2['backups'])}\n"
                else:
                    backup_text = f"{" ".join(f"{b}" for b in row2['backups'])}\n"
                if len(backup_text.strip()) >= 1:
                    part_text += backup_text
                    backup_list.append(part_text)

        if len(backup_list) >= 1:
            lines.extend(backup_list)
        else:
            lines.append("*None yet*")


    elif texttoshow == "Prizes":
        lines.append("# Prizes")
        lines.append(f"Prizes will be awarded to the three best parts of {collab_dict[0]['collabname']}:")
        lines.append(f"- 🥇 **1st Place** - Discord Nitro *(1 month)*")
        lines.append(f"- 🥈 **2nd Place** - Discord Nitro Basic *(1 month)*")
        lines.append(f"- 🥉 **3rd Place** - A pat on the back")
        
        
        
    
    elif texttoshow == "GroupInfo":
        lines.append("Group Info WIP")

    text = "\n".join(lines)

    return text