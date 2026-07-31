import discord

class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Yes",
            style=discord.ButtonStyle.green,
            custom_id="confirm_button",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.view.choice = True
        self.view.stop()


class DenyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="No",
            style=discord.ButtonStyle.red,
            custom_id="deny_button",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.view.choice = False
        self.view.stop()

class ExtraButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id="extra_button",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.view.choice = "Extra"
        self.view.stop()

class ConfirmDeny(discord.ui.DesignerView):
    def __init__(
        self,
        bot,
        title: str = None,
        subtitle: str = None,
        text: str = None,
        extrabutton: str = None,
        attachment: discord.Attachment = None
    ):
        super().__init__()  # required before add_item will work

        self.bot = bot
        self.choice = None

        self.title = f"❔ {title}"

        self.text1 = discord.ui.TextDisplay(f"## {self.title}")
        self.text2 = discord.ui.TextDisplay(f"### {subtitle}")
        self.text3 = discord.ui.TextDisplay(text or "")

        if subtitle is not None:
            container = discord.ui.Container(
                self.text1,
                self.text2,
                self.text3,
                color=0xFFFFFF,
            )
        else:
            container = discord.ui.Container(
                self.text1,
                self.text3,
                color=0xFFFFFF
            )

        if attachment is not None:
            container.add_file(
                f"attachment://{attachment.filename}"
            )

        container.add_separator(divider=True, spacing=discord.SeparatorSpacingSize.large)

        actionrow = discord.ui.ActionRow()
        actionrow.add_item(ConfirmButton())
        actionrow.add_item(DenyButton())
        if extrabutton is not None:
            actionrow.add_item(ExtraButton(extrabutton))
        container.add_item(actionrow)

        self.add_item(container)