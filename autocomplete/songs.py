import discord
from utils.dbcommands import db_showsong, showfriendlysongnames
from utils.isadmin import isadmin


async def song_autocomplete(ctx: discord.AutocompleteContext):
    bot = ctx.bot

    if not await isadmin(ctx.interaction.user):
        return []

    songs = await db_showsong(bot, ctx.interaction.guild)
    friendly_songs = await showfriendlysongnames(songs)

    return friendly_songs