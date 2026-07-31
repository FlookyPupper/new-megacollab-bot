import discord
from pathlib import Path

prop = discord.SlashCommandGroup(
    "prop", 
    "Settings related commands",
    default_member_permissions=discord.Permissions(administrator=True)
)

megacollab = discord.SlashCommandGroup(
    "megacollab", 
    "Megacollab related commands",
    default_member_permissions=discord.Permissions(administrator=True)
)

song = discord.SlashCommandGroup(
    "song", 
    "Song related commands",
    default_member_permissions=discord.Permissions(administrator=True)
)

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)

SONG_DIR = BASE_DIR / "Songs"

SONG_TMP = SONG_DIR / "tmp"

UPLOAD_DIR = BASE_DIR / "Uploads"

UPLOAD_TMP = BASE_DIR / "Uploads"

SONG_DIR.mkdir(exist_ok=True)
SONG_TMP.mkdir(exist_ok=True)

UPLOAD_DIR.mkdir(exist_ok=True)
UPLOAD_TMP.mkdir(exist_ok=True)

MAX_AGE_SECONDS = 1200

CSV_MAXSIZE = 1 * 1024 * 1024
XML_MAXSIZE = 2 * 1024 * 1024
MP3_MAXSIZE = 10 * 1024 * 1024

BITRATES = {
    (1, 3): [None,32,40,48,56,64,80,96,112,128,160,192,224,256,320,None],
    (2, 3): [None,8,16,24,32,40,48,56,64,80,96,112,128,144,160,None],
}

SAMPLERATES = {
    1: [44100, 48000, 32000, None],
    2: [22050, 24000, 16000, None],
}