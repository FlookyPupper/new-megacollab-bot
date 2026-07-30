import discord

prop = discord.SlashCommandGroup(
    "prop", 
    "Settings related commands",
    default_member_permissions=discord.Permissions(administrator=True)
)