import discord

class OptionSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption]):
        super().__init__(placeholder="Choose an option...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.view.choice = self.values[0]
        self.view.stop()


class SelectList(discord.ui.DesignerView):
    def __init__(
        self,
        bot,
        options: list[discord.SelectOption],
        title: str = None,
        subtitle: str = None,
        text: str = None,
        isdisambiguation: bool = False,
    ):
        super().__init__()  # required before add_item will work

        self.bot = bot
        self.choice = None

        self.title = f"❔ {title}" if isdisambiguation else f"📄 {title}"

        self.text1 = discord.ui.TextDisplay(f"## {self.title}")
        self.text2 = discord.ui.TextDisplay(f"### {subtitle}")
        self.text3 = discord.ui.TextDisplay(text or "")

        self.select = OptionSelect(options)

        container = discord.ui.Container(
            self.text1,
            self.text2,
            self.text3,
            color=0xFFFFFF,
        )
        container.add_separator(divider=True, spacing=discord.SeparatorSpacingSize.large)

        container.add_item(discord.ui.ActionRow(self.select))
        
        self.add_item(container)