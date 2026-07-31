import discord
from utils.dbcommands import db_showsong
from utils.dbcommands import showfriendlysongnames


async def song_autocomplete(ctx: discord.AutocompleteContext):
    if not bot.isBotSynced or not await isadmin(ctx.interaction.user): 
        await ctx.response.send_autocomplete({})
        return

    songs = await db_showsong()

    list_of_songs = await showfriendlysongnames(songs)

    return list_of_songs