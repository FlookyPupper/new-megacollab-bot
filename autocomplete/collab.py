from utils.dbcommands import db_showcollabs, showfriendlycollabnames
from utils.isadmin import isadmin

async def collabautocompletehelper(ctx, collabname):
    bot = ctx.bot

    if not bot.isBotSynced or not await isadmin(ctx.interaction.user): 
        return []

    collabs = await db_showcollabs(bot, ctx.interaction.guild, bycollabname=collabname)  # list[str]

    list_of_collabs = await showfriendlycollabnames(collabs)

    return list_of_collabs

async def collab_autocomplete(ctx: discord.AutocompleteContext):
    list_of_collabs = await collabautocompletehelper(ctx, ctx.value)

    return list_of_collabs