import discord

class RankView(discord.ui.DesignerView):
    def __init__(
        self,
        bot: discord.Bot,
        user: discord.Member,
        seasontokenscurrent,
        seasontokensnext,
        rankcurrent,
        ranknext,
        leaderboardposition = None
    ):
        super().__init__()  # required before add_item will work

        self.bot = bot

        text1 = discord.ui.TextDisplay(f"### {user.global_name}'s Rank")
    
        thumbnail = discord.ui.Thumbnail(user.display_avatar.url)

        section = discord.ui.Section(text1, accessory=thumbnail)
    
        container = discord.ui.Container(
            section,
            color=0xFFFFFF,
        )
        container.add_text(f"**Rank**: {rankcurrent}")
        if leaderboardposition is None:
            container.add_text(f"**ELO**: {seasontokenscurrent}/{seasontokensnext}\n*({seasontokensnext - seasontokenscurrent} left for {ranknext})*")
        else:
            container.add_text(f"**ELO**: {seasontokenscurrent}")
            container.add_text(f"**Leaderboard Position**: {leaderboardposition}")

        self.add_item(container)
    
    