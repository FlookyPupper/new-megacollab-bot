import discord
from utils.dbcommands import db_showdifficulties, showfriendlydifficultynames
from utils.isadmin import isadmin

async def difficulty_autocomplete(ctx: discord.AutocompleteContext):
    bot = ctx.bot

    if not await isadmin(ctx.interaction.user):
        return []

    songs = await db_showdifficulties(bot)
    friendly_difficulties = await showfriendlydifficultynames(songs)

    return friendly_difficulties