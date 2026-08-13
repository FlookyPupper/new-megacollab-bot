import discord
from discord.ext import commands
from discord.commands import slash_command
from views.message import Message
from utils.dbcommands import db_createmegacollab
from utils.isadmin import isadmin
from utils.variables import guild_cache
from config.groups import megacollab
import discord
import pandas as pd
from autocomplete.songs import song_autocomplete
from typing import Optional
from config.groups import CSV_MAXSIZE
from utils.parseintodict import parseintodict
from pycord.multicog import subcommand

class CreateMegacollab(commands.Cog):   
    def __init__(self, bot):
        self.bot = bot
    
    @subcommand("megacollab", independent=True)
    @discord.command(
        name='create', 
        description="Creates a new megacollab."
    )
    @discord.default_permissions(manage_guild=True)
    async def createmegacollab(
        ctx, 
        name: str = discord.Option(
            str,
            description="Sets the name of the megacollab.",
            required=True
        ), 
        durationindays: int = discord.Option(
            int,
            description="Sets the amount of days the megacollab will last for.",
            min_value=1,
            required=True
        ), 
        song: str = discord.Option(
            str,
            description="Sets the song to use in the megacollab.",
            autocomplete=discord.utils.basic_autocomplete(song_autocomplete),
            required=True
        ),
        difficulty: int = discord.Option(
            int,
            description="Sets the difficulty for this megacollab.",
            min_value=1,
            required=True
        ),
        parts: discord.Attachment = discord.Option(
            discord.Attachment,
            description="Upload a CSV file with all of the parts.",
            required=True
        ),
        maxgroups: Optional[int] = discord.Option(
            int,
            description="(Optional) Sets the maximum amount of groups allowed for this collab.",
            min_value=500,
            max_value=10000,
            default=500,
            required=False
        )
    ):
        logging.info(difficulty)
        if not await isadmin(ctx.interaction.user):
            embed = discord.Embed(title="❌ You don't have permission to use this command.", color=0xff0000)
            await ctx.respond(
                embed=embed,
                ephemeral=True
            )
            return

        else:    
            duplicates = await db_checkduplicates(name, 'megacollabs')

            if parts is not None:
                required_columns = ["partnumber", "offsetstart", "offsetend", "rating"]
                required_lengths = [len(col) for col in required_columns]

                if parts.size > CSV_MAXSIZE:
                    embed = Message(self.bot, title="Error", text="Uploaded attachment is too large. (max: 1MB)", messagetype="Error")
                    await ctx.respond(
                        view=embed,
                        ephemeral=True
                    )
                    return

                try:
                    if not parts.filename.lower().endswith(".csv"):
                        raise TypeError("Doesn't end with CSV.")

                    raw_bytes = await parts.read()

                    # Decode to text
                    text = raw_bytes.decode("utf-8")

                    if len(text.strip()) < 10:
                        raise ValueError("File is too small to be a CSV.")
                
                    if any(len(line) > 64 for line in text.splitlines()):
                        raise ValueError("CSV contains long lines.")

                    # Sniff CSV format
                    dialect = csv.Sniffer().sniff(text[:2048])

                    if dialect.delimiter != ",":
                        raise ValueError("CSV must use ',' as delimiter.")

                    reader = csv.reader(io.StringIO(text), dialect)
                    rows = list(reader)

                    # Must have header + at least one row
                    if len(rows) < 2:
                        raise ValueError("CSV must include a header and at least one data row.")

                    header_raw = rows[0]
                    header = [h.strip().lower() for h in header_raw]
                
                    if header[:4] != required_columns:
                        raise ValueError(
                            "CSV header must be exactly: partnumber,offsetstart,offsetend,rating"
                        )
                
                    for idx, (col, expected_len) in enumerate(zip(header, required_lengths)):
                        if len(col) != expected_len:
                            raise ValueError(
                                f"Column {idx + 1} must be exactly {expected_len} characters long."
                            )

                    if len(header) != len(required_columns):
                        raise ValueError("CSV must not contain extra columns.")

                    if len(rows) > 100:
                        raise ValueError("CSV exceeds maximum allowed rows (100).")

                    if len(header) not in range(1, 5):
                        raise ValueError("CSV must contain multiple columns.")

                    df = pd.read_csv(
                        io.StringIO(text),
                        sep=",",
                        engine="python",
                        dtype_backend="numpy_nullable"
                    )

                    parts_dict = await parseintodict(df)

                except Exception as e:
                    embed = Message(self.bot, title="Error", subtitle="Uploaded attachment is not a valid CSV.", text=f"{e}", messagetype="Error")
                    await ctx.respond(
                        view=embed,
                        ephemeral=True
                    )
                    return
            else:
                parts_dict = None

            try:
                song = int(song)
                songtoadd = await db_showsong(bysongid=song)
                friendlyname = list(await showfriendlysongnames(songtoadd))[0]
            except ValueError:
                embed = Message(self.bot, title="Error", text="You inserted an invalid song, please use one from the dropdown list.", messagetype="Error")
                await ctx.respond(
                    view=embed,
                    ephemeral=True
                )
                return

            deadline = datetime.now() + timedelta(days=durationindays)
            unix_timestamp = int(deadline.timestamp())

            text = "\n".join([
                f"**Name**: {name}",
                f"**Deadline**: <t:{unix_timestamp}:F> (<t:{unix_timestamp}:R>)",
                f"**Song**: {friendlyname.name}",
                f"**Host**: {ctx.interaction.user.mention}",
                "-# You can add other hosts later",
            ])
            
            view = ConfirmDeny(
                self.bot,
                title="You're about to create the following megacollab",
                subittle="Review your changes before proceeding.",
                text=text
            )

            if len(duplicates) != 0:
                duplicate_dict = await parseintodict(duplicates)
                text = "\n".join(
                    f'**ID: {row["collabid"]}** - {row["collabname"]}'
                    for row in duplicate_dict
                )

                duplicateview = ConfirmDeny(
                    title=f'⚠️ There are potential duplicates that are like "{name}"',
                    subtitle="Are you sure you want to continue? *(Another collab with the same name will be created)*",
                    text=text
                )
            else:
                duplicateview = None

            await ctx.respond(
                    view=duplicateview if duplicateview else view,
                    ephemeral=True
                )

def setup(bot):
    bot.add_cog(CreateMegacollab(bot))