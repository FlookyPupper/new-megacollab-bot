import discord
from utils.dbcommands import db_showartists, showfriendlyartistnames
from utils.isadmin import isadmin


async def artist_autocomplete(ctx: discord.AutocompleteContext):
    bot = ctx.bot

    if not await isadmin(ctx.interaction.user):
        return []

    songs = await db_showartists(bot, ctx.interaction.guild)
    friendly_artists = await showfriendlyartistnames(songs)

    return friendly_artists