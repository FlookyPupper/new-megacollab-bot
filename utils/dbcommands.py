import asyncpg
import discord
from utils.parseintodict import parseintodict

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
                'SELECT "Core".setmessagetype($1, $2, $3, $4)', 
                collabid, typetoset, int(objecttoadd.id), int(objecttoadd.channel.id)
            )
        case discord.TextChannel():
            await conn.execute(
                'SELECT "Core".setchanneltype($1, $2, $3)', 
                collabid, typetoset, int(objecttoadd.id)
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

async def db_showcollabs(bot, bycollabid: int=None, bycollabname: str=None):
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showcollabs($1, $2)', 
            bycollabid, bycollabname
        )
        
    return info

async def db_showartistname(bot, guild, artistid: int):
    query = await db_showartists(bot, guild, artistid)
    query = await parseintodict(query)
    return query[0]['artistname']

async def pullcollabrole(conn, collabid: int, type: str) -> discord.Role:
    info = await conn.fetchrow(
        'SELECT * from "Core".showrole($1, $2)',
        collabid, type
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

async def pullcollabmessage(conn, collabid: int, type: str) -> discord.Message:
    info = await conn.fetchrow(
        'SELECT * from "Core".showmessage($1, $2)',
        collabid, type
    )

    if info is None:
        raise TypeError("Message doesn't exist")
    
    channel = await bot.fetch_channel(info['channelid'])
    message = await channel.fetch_message(info['messageid'])

    return message

async def pullcollabchannel(conn, collabid: int, type: str) -> discord.TextChannel:
    info = await conn.fetchval(
        'SELECT "Core".showchannel($1, $2)',
        collabid, type
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

async def db_showparts(bot, collabid: int):
    collabid = int(collabid)

    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showparts($1)', 
            collabid
        )
    
    return info

async def db_showclaims(bot, bycollabid: Optional[int]=None, bypartid: Optional[int]=None, byuserid: Optional[int]=None):
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showclaims($1, $2, $3)', 
            bycollabid, bypartid, byuserid
        )
    
    return info

async def db_showuserclaims(
    bot,
    bycollabid: Optional[int]=None, 
    bypartid: Optional[int]=None, 
    byuserid: Optional[int]=None, 
    byclaimid: Optional[int]=None, 
    bystatus=None, 
    bytype=None
):
    async with bot.db.acquire() as conn:
        info = await conn.fetch(
            'SELECT * from "Core".showuserclaims($1, $2, $3, $4, $5, $6)', 
            bycollabid, bypartid, byuserid, byclaimid, bystatus, bytype
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