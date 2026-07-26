
import discord
from discord.ext import commands
from discord.commands import slash_command
from views.selectlist import SelectList
from views.confirmdeny import ConfirmDeny

class ViewTest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="viewtest")
    async def ping(self, ctx):
        await ctx.response.defer()

        selectview = SelectList(
            self.bot,
            options=[
                discord.SelectOption(
                    label="Option 1",
                    description="Test"
                ),
                discord.SelectOption(
                    label="Option 2",
                    description="Test"
                ),
                discord.SelectOption(
                    label="Option 3",
                    description="Test"
                ),
                discord.SelectOption(
                    label="Option 4",
                    description="Test"
                )
            ],
            title="Title",
            subtitle="Subtitle",
            text="Lorem ipsum dolor sit amet"
        )

        await ctx.respond(view=selectview, ephemeral=True)

        await selectview.wait()
        
        result_view = discord.ui.DesignerView()

        if selectview.choice == "Option 1":
            result_view = ConfirmDeny(
                self.bot, 
                "Title", 
                "Subtitle", 
                "Lorem ipsum",
                "Show Parts"
            )
        elif selectview.choice is not None:
            result_view.add_item(discord.ui.TextDisplay(f"You picked: **{selectview.choice}**"))
        else:
            result_view.add_item(discord.ui.TextDisplay(f"Timed out — nothing selected."))

        await ctx.edit(view=result_view)


def setup(bot):
    bot.add_cog(ViewTest(bot))