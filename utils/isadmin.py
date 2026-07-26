import discord

async def isadmin(user):
    if isinstance(user, (discord.Member, discord.User)):
        if member.guild_permissions.administrator:
            return True
        else:
            return False
    else:
        raise TypeError("Not a discord user.")