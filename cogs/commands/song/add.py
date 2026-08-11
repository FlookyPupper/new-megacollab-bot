import discord
from discord.ext import commands
from discord.commands import slash_command
import uuid
from collections import Counter
from urllib.parse import urlparse, parse_qs
from utils.isadmin import isadmin
from utils.dbcommands import (
    db_showartists,
    db_createsong,
    db_associatesongwithartist,
    db_doesartistexist,
    db_checkduplicates,
    db_showartistname,
    db_createartist,
    db_addsonglink,
    showfriendlyartistnames
)
from config.groups import (
    song,
    SONG_TMP,
    SONG_DIR,
    MP3_MAXSIZE,
    BITRATES
)
from utils.ismp3 import ismp3
from views.selectlist import SelectList
from views.confirmdeny import ConfirmDeny
from views.message import Message
from utils.concatenateartists import concatenateartists
from utils.parseintodict import parseintodict

class AddSong(commands.Cog):
    song = song
    
    def __init__(self, bot):
        self.bot = bot

    @song.command(
        name='add', 
        description="Adds a song."
    )
    @discord.default_permissions(administrator=True)
    async def songcmdadd(
        self,
        ctx,
        name: str = discord.Option(
            str,
            description="Name of the new song.",
            required=True
        ), 
        artist: str = discord.Option(
            str,
            description="Name of the artist. (Use ; to separate multiple artists)",
            required=True
        ),
        youtubelink: str = discord.Option(
            str,
            description="The user that the claim will be attached to",
            required=True
        ),
        newgroundslink: str = discord.Option(
            str,
            description="The user that the claim will be attached to",
            required=False
        ),
        bandcamplink: str = discord.Option(
            str,
            description="The user that the claim will be attached to",
            required=False
        ),
        soundcloudlink: str = discord.Option(
            str,
            description="The user that the claim will be attached to",
            required=False
        ),
        songupload: discord.Attachment = discord.Option(
            discord.Attachment,
            description="Song upload",
            required=False
        ),
    ):
        if not await isadmin(ctx.interaction.user):
            embed = Message(self.bot, title="Error", text="You don't have permission to use this command.", messagetype="Error")
            await ctx.respond(view=embed, ephemeral=True)
            return

        try:
            temp_file = None
            final_file = None
        
            await ctx.response.defer(ephemeral=True)

            toparse = {
                'name': str(name),
                'artist': [],
                'artistdisplay': [],
                'youtubeid': None,
                'newgroundsid': None,
                'bandcampusername': None,
                'bandcamptrack': None,
                'soundcloudusername': None,
                'soundcloudtrack': None,
                'file': None
            }

            if ";" in artist:
                artist_list = artist.split(';')
            else:
                artist_list = [artist]

            if songupload is None and newgroundslink is None:
                raise Exception("You need to specify a file for this NONG.")
            elif songupload is not None and newgroundslink is not None:
                raise Exception("For a Newgrounds song, it is invalid to specify a file upload.")


            inbetweener = await db_showartists(self.bot, ctx.interaction.guild)
            print(inbetweener)

            autocomplete_artistlist = await showfriendlyartistnames(inbetweener)

            for i, artistname in enumerate(artist_list):
                if artistname in autocomplete_artistlist:
                    artist_list[i] = autocomplete_artistlist[artistname]

            for artistname in artist_list:
                try:
                    if artistname.isdigit() and await db_doesartistexist(int(artistname)):
                        toparse['artist'].append(int(artistname))
                    elif artistname.isdigit() and not await db_doesartistexist(int(artistname)):
                        raise TypeError("ID doesn't exist.")
                    else:
                        toparse['artist'].append(artistname)
    
                except ValueError:
                    toparse['artist'].append(artistname)

            if songupload is not None:
                if songupload.size > MP3_MAXSIZE:
                    embed = Message(self.bot, title="Error", text="Uploaded attachment is too large. (max: 10MB)", messagetype="Error")
                    await ctx.respond(
                        view=embed,
                        ephemeral=True
                    )
                    return

                try:
                    if not songupload.filename.lower().endswith(".mp3"):
                        raise TypeError("Doesn't end with MP3.")

                    file = await songupload.read()

                    if len(file) < 10:
                        del file
                        raise ValueError("File is too small to be a MP3.")

                    if not await ismp3(file):
                        del file
                        raise TypeError("File is not an MP3.")

                    filename = f"{uuid.uuid4()}.mp3"

                    file_path = SONG_TMP / filename
                
                    await songupload.save(file_path)
                except Exception as e:
                    embed = Message(self.bot, title="Error", subtitle="File is not a valid MP3.", text=f"{e}", messagetype="Error")
                    await ctx.respond(
                        view=embed
                    )
                    return
            else:
                file_path = None

            links = {
                'youtube': urlparse(youtubelink),
                'newgrounds': urlparse(newgroundslink),
                'bandcamp': urlparse(bandcamplink),
                'soundcloud': urlparse(soundcloudlink),
            }

            print(links['youtube'])

            toparse['file'] = file_path
            temp_file = toparse["file"]

            # YouTube

            yt = links['youtube']
            video_id = None

            if not yt.scheme and not yt.netloc:
                raise ValueError("Invalid YouTube URL")

            if yt.hostname not in {"www.youtube.com", "youtube.com"} or yt.path != "/watch":
                raise ValueError("Invalid YouTube URL")

            youtube_ok = (
                links['youtube'].hostname in {"www.youtube.com", "youtube.com"}
                and links['youtube'].path == "/watch"
            )

            if not youtube_ok:
                raise ValueError("Invalid YouTube URL")

            yt_qs = parse_qs(yt.query or "")
            toparse['youtubeid'] = yt_qs.get("v", [None])[0]

            # Bandcamp
            bc = links['bandcamp']

            if bc.scheme and bc.netloc:
                if (
                    not bc.hostname
                    or not bc.hostname.endswith(".bandcamp.com")
                    or not bc.path.startswith("/track/")
                ):
                    raise ValueError("Invalid Bandcamp URL")
                
                bandcamp_username = bc.hostname[:-len(".bandcamp.com")]
                bandcamp_track = bc.path[len("/track/"):]

                if not bandcamp_username or not bandcamp_track:
                    raise ValueError ("Invalid Bandcamp URL")

                toparse['bandcampusername'] = bandcamp_username
                toparse['bandcamptrack'] = bandcamp_track

            # SoundCloud
            RESERVED_SOUNDCLOUD_USERS = {
                "you",
                "discover",
                "stream",
                "charts",
                "feed",
                "upload",
                "settings",
                "messages",
                "search",
                "terms",
                "privacy",
                "jobs"
            }

            sc = links['soundcloud']
            if sc.scheme and sc.netloc:
                if sc.hostname not in {"soundcloud.com", "www.soundcloud.com"}:
                    raise ValueError("Invalid SoundCloud URL")

                parts = sc.path.strip("/").split("/")

                if (
                    len(parts) != 2
                    or not parts[0]
                    or not parts[1]
                    or parts[0].lower() in RESERVED_SOUNDCLOUD_USERS
                ):
                    raise ValueError("Invalid SoundCloud URL")
                
                toparse["soundcloudusername"], toparse["soundcloudtrack"] = parts

            ng = links['newgrounds']

            if ng.scheme or ng.netloc or ng.path:
                if (
                    ng.scheme != "https"
                    or ng.hostname != "www.newgrounds.com"
                    and not ng.path.startswith("/audio/listen/")
                ):
                    raise ValueError("Invalid Newgrounds URL")

                newgrounds_id = ng.path[len("/audio/listen/")]

                if not newgrounds_id.isdigit():
                    raise ValueError("Invalid Newgrounds URL")

                toparse['newgroundsid'] = int(newgrounds_id)

            print(ng)

            text = ""

            duplicates = []
            ofduplicate = []

            for artist in toparse['artist']:
                if isinstance(artist, str):
                    foundduplicates = await db_checkduplicates(self.bot, ctx.interaction.guild, artist, 'artists')
                    if len(foundduplicates) != 0:
                        duplicates.append(foundduplicates)
                        ofduplicate.append(artist)

            duplicatetoolings = []

            tempauxlist = []

            acknowledgeartistduplication = False
            acknowledgesongduplication = False

            if len(duplicates) != 0:
                for record, matched_name in zip(duplicates, ofduplicate):
                    foundrecords = await parseintodict(record)

                    options = [
                        discord.SelectOption(
                            label=row["artistname"],
                            value=f"id:{row['artistid']}",
                            description=f"Artist ID: {row['artistid']}",
                        )
                        for row in foundrecords
                    ]

                    options.extend([
                        discord.SelectOption(
                            label="Create new artist",
                            value="create",
                            description=f'Create "{matched_name}" as a new artist.',
                        ),
                        discord.SelectOption(
                            label="Cancel",
                            value="cancel_operation",
                            description="Cancel this operation.",
                        ),
                    ])                

                    view = SelectList(
                        bot=self.bot,
                        options=options,
                        title="Potential duplicate",
                        subtitle=f'Artists matching "{matched_name}"',
                        text="Choose an existing artist or create a new one.",
                        isdisambiguation=True,
                    )

                    await ctx.edit(
                        content=None,
                        view=view
                    )

                    await view.wait()

                    choice = view.choice

                    if choice is None or choice == "cancel_operation":
                        toparse["artist"] = None
                        embed = Message(self.bot, title="Cancelled", text="Action cancelled.", messagetype="Error")
                        await ctx.edit(
                            view=embed
                        )
                        await ctx.stop()
                        break

                    if choice == "create":
                        acknowledgeartistduplication = True
                        tempauxlist.append(matched_name)
                    else:
                        tempauxlist.append(int(choice.removeprefix("id:")))
                
                if toparse ["artist"] is not None:
                    for artist in toparse["artist"]:
                        if artist not in ofduplicate:
                            tempauxlist.append(artist)
                    
                    toparse["artist"] = tempauxlist

            else:
                choice = toparse['artist']

            seen = set()
            final_artists = []

            for artist in toparse['artist']:
                if isinstance(artist, int):
                    if artist in seen:
                        continue
                    seen.add(artist)
                final_artists.append(artist)

            toparse['artist'] = final_artists
        
            for artist in toparse['artist']:
                if isinstance(artist, int):
                    toparse['artistdisplay'].append(f"{await db_showartistname(self.bot, ctx.interaction.guild, int(artist))}")
                else:
                    toparse['artistdisplay'].append(f"{artist} *(new)*")

            toparse['artistdisplay'] = await concatenateartists(toparse['artistdisplay'])

            new_names = [a for a in toparse['artist'] if isinstance(a, str)]
            dupes = [name for name, c in Counter(new_names).items() if c > 1]

            if dupes:
                acknowledgesongduplication = True
                await ctx.followup.send(
                f"ℹ️ **Note** - The following new artist names were entered multiple times: `"
                f"{', '.join(dupes)}`",
                ephemeral=True
            )

            view = ConfirmDeny(
                self.bot, 
                title="You're about to create the following song", 
                text=f"**Title**: {toparse['name']}\n{"**Artists**" if len(toparse['artist']) > 1 else "**Artist**"}: {toparse['artistdisplay']}\n**File**:",
                attachment=songupload
            )

            file = await songupload.to_file()

            await ctx.edit(
                view=view,
                files=[file]
            )

            await view.wait()
        
            if view.choice or not view.choice:
                if not await isadmin(ctx.user):
                    embed = Message(self.bot, title="Error", text="You do not have permission to run this command", messagetype="Error")
                    return

            if not view.choice:
                embed = Message(self.bot, title="Cancelled", text="Action cancelled.", messagetype="Error")

            elif view.choice:
                embed = Message(self.bot, title="Hold on, working now!", text=f"Creating song {toparse['name']}...", messagetype="Wait")
                await ctx.edit(
                    view=embed
                )

                newsong = None

                final_file = None

                newartists = []


                async with self.bot.db.acquire() as conn:
                    async with conn.transaction():
                        for artist in toparse['artist']:
                            if isinstance(artist, str):
                                newartists.append(await db_createartist(conn, artist, ctx.interaction.guild, acknowledgeartistduplication))
                            elif isinstance(artist, int):
                                newartists.append(artist)
                            
                        newsong = await db_createsong(conn, toparse['name'], ctx.interaction.guild, acknowledgeartistduplication)

                        for artist in newartists:
                            await db_associatesongwithartist(conn, newsong, artist)
                    
                        if toparse['youtubeid'] is not None:
                            await db_addsonglink(conn, newsong, 'YouTube', toparse['youtubeid'])

                        if toparse['newgroundsid'] is not None:
                            await db_addsonglink(conn, newsong, 'Newgrounds', toparse['newgroundsid'])

                        if toparse['soundcloudtrack'] is not None and toparse['soundcloudusername'] is not None:
                            await db_addsonglink(conn, newsong, 'SoundCloud', toparse['soundcloudtrack'], toparse['soundcloudusername'])

                        if toparse['bandcamptrack'] is not None and toparse['bandcampusername'] is not None:
                            await db_addsonglink(conn, newsong, 'Bandcamp', toparse['bandcamptrack'], toparse['bandcampusername'])
                    

                        if temp_file is not None:
                            if temp_file.exists():
                                final_file = SONG_DIR / temp_file.name
                                temp_file.rename(final_file)

                                await db_addsonglink(conn, newsong, 'Local', str(final_file))
                            else:
                                raise FileNotFoundError(f"{temp_file} not found")
                        
                embed = Message(self.bot, title="Success", text=f"Successfully created song {toparse['name']}!", messagetype="Success")

        except Exception as e:
            if final_file is not None and final_file.exists():
                final_file.unlink(missing_ok=True)
            if temp_file is not None and temp_file.exists():
                temp_file.unlink(missing_ok=True)
            embed = Message(self.bot, title="An error occurred", subtitle=f"An error occurred while adding this song.", text=f"{e}", messagetype="Error")
            raise Exception(e)
        
        finally:
            await ctx.edit(
                view=embed
            )  

def setup(bot):
    bot.add_cog(AddSong(bot))