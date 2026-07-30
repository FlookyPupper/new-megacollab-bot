import discord

class Message(discord.ui.DesignerView):
    def __init__(
        self,
        bot,
        title,
        text,
        subtitle: str = None,
        messagetype: str = "Error"
    ):
        super().__init__()  # required before add_item will work

        self.bot = bot
        self.choice = None
        self.color = None

        if messagetype == "Success":
            self.title = "✅"
            self.color = 0x00FF00
        elif messagetype == "Error":
            self.title = "❌"
            self.color = 0xFF0000
        elif messagetype == "Wait":
            self.title = "✍️"
            self.color = 0xABABAB
        else:
            raise TypeError

        self.title += f" {title}"

        self.text1 = discord.ui.TextDisplay(f"## {self.title}")
        self.text2 = discord.ui.TextDisplay(f"### {subtitle}")
        self.text3 = discord.ui.TextDisplay(text or "")

        if subtitle is not None:
            container = discord.ui.Container(
                self.text1,
                self.text2,
                self.text3,
                color=self.color,
            )
        else:
            container = discord.ui.Container(
                self.text1,
                self.text3,
                color=self.color,
            )
        
        self.add_item(container)