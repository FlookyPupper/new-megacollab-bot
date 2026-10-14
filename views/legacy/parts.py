import discord
from utils.dbcommands import (db_showclaims, db_showcollabs, db_showcollabidbymessage, pullcollabrole, db_showuserclaims)
from utils.parseintodict import parseintodict

class ConfirmPartSelect(discord.ui.View):

    def __init__(self, collabid: int, collabname: str, partid: int, backup: bool, lock_registry: set[int]):
        super().__init__(timeout=120)
        self.confirm = None
        self.collabid = collabid
        self.collabname = collabname
        self.partid = partid
        self.isbackup = backup
        self.lock_registry = lock_registry

    async def on_timeout(self):
        self.lock_registry.discard(ctx.user.id)
    
    @discord.ui.button(
        label="✅ Yes",
        style=discord.ButtonStyle.success
    )
    async def confirmclaim(
        self,
        button: discord.ui.Button,
        ctx
    ):
        useridtolock = ctx.user.id

        try:
            async with client.db.acquire() as conn:
                await db_claimpart(conn, ctx.guild.id, ctx.user.id, self.collabid, self.partid)
        except Exception as e:
            embed = discord.Embed(title=f"❌ An error occurred while claiming the part: {e}", color=0xff0000)
        else:
            if self.isbackup:
                embed = discord.Embed(title=f"✅ You have joined {self.collabname} at Part {self.partid} as a backup. You will be notified when that part is available.", color=0x00ff00)
            else:
                embed = discord.Embed(title=f"✅ Congratulations! You have joined {self.collabname} at Part {self.partid}!", color=0x00ff00)
        finally:
            await ctx.response.edit_message(
                content="",
                embed=embed,
                view=None
            )
            self.lock_registry.discard(useridtolock)
            self.stop()
    
    @discord.ui.button(
        label="❌ No",
        style=discord.ButtonStyle.danger
    )
    async def cancelclaim(
        self,
        button: discord.ui.Button,
        ctx
    ):
        useridtolock = ctx.user.id

        self.confirm = False
        embed = discord.Embed(title="❌ Cancelled", color=0xff0000)

        await ctx.response.edit_message(
            content="",
            embed=embed,
            view=None
        )
        self.lock_registry.discard(useridtolock)
        self.stop()

class PartSelect(discord.ui.Select):
    _used_by: set[int] = set()

    def __init__(self, collabid: int, parts: list[dict], bot, guild):
        self.bot = bot
        self.guild = guild

        options = [
            discord.SelectOption(
                label=f"Part {part['partnumber']}",
                value=f"{collabid}:{part['partnumber']}:{part['rating']}",
                description=f"{"⭐" * part['rating']} {"(Boring Part)" if part['rating'] <= 2 else ("(Neutral)" if part['rating'] == 3 else "(Expressive Part)")}"
            )
            for part in parts
        ]

        super().__init__(
            custom_id=f"collab_part_select:{collabid}",
            placeholder="Choose a part to claim...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, ctx):
        useridtolock = ctx.user.id

        if useridtolock in PartSelect._used_by:
            return

        PartSelect._used_by.add(useridtolock)

        collabid, partid, partrating = self.values[0].split(":")
        partrating = int(partrating)

        userclaims, partclaim, collab_dict = await db_showclaims(self.bot, self.guild, bycollabid=int(collabid), byuserid=ctx.user.id), await db_showclaims(self.bot, self.guild, bycollabid=int(collabid), bypartid=int(partid)), await parseintodict(await db_showcollabs(self.bot, self.guild, bycollabid=int(collabid)))

        collabid = int(collabid)
        partid = int(partid)
        partrating = int(partrating)

        try:
            if len(userclaims) == 1:
                for userclaim in userclaims:
                    if userclaim['collabid'] == collabid and userclaim['partid'] == partid and userclaim['status'] != "Dropped":
                        raise TypeError("You cannot claim a part that you've already claimed.")
                        break

                if userclaims[0]['ratingatclaimtime'] >= 3:
                    raise TypeError("We're sorry, but you cannot claim any more parts at this time.")
                elif userclaims[0]['ratingatclaimtime'] <= 2 and partrating <= 3:
                    raise TypeError("You cannot claim a low-tier part while you already claim a low-tier part.")

            elif len(userclaims) >= 2:
                raise TypeError("We're sorry, but you cannot claim any more parts at this time.")
            
            if partclaim[0]['status'] == "Finished":
                raise TypeError("You cannot claim a part that is finished.")

        except Exception as e:
            embed = discord.Embed(title=f"❌ {e}", color=0xff0000)
            view = None
            PartSelect._used_by.discard(useridtolock)

        else:
            title = f"❓ Are you sure you want to claim Part {partclaim[0]['partid']}"

            embed = discord.Embed(color=0xffff00)

            if partclaim[0]['status'] is not None:
                title += " as a backup?"
                isbackup = True
                embed.add_field(name="", value=f"Since this part is already taken by <@{partclaim[0]['userid']}>, you will be set as a backup. Once they drop, you may be automatically promoted (depending on backup order).")
            else:
                title += "?"
                isbackup = False

            if partrating <= 2:
                embed.set_footer(text="💡 Since you have chosen a low-tier part, you have the right to choose a high-tier (>3 star) part.")

            embed.title = title

            view = ConfirmPartSelect(
                collabid=collabid, 
                collabname=collab_dict[0]['collabname'], 
                partid=partclaim[0]['partid'], 
                backup=isbackup, 
                lock_registry=PartSelect._used_by
            )
            
        finally:
            if view is not None:
                await ctx.respond(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

            else:
                await ctx.respond(
                    embed=embed,
                    ephemeral=True
                )

class ChoosePartToDrop_Dropdown(discord.ui.Select):
    def __init__(self, claims: list):
        options = []

        for claim in claims:
            options.append(discord.SelectOption(label=f"Part {claim['partid']}", value=f"{claim['collabid']};{claim['partid']}"))

        options.append(discord.SelectOption(label=f"All of them", value="all"))

        super().__init__( 
            placeholder="Choose a part",
            min_values=1,
            max_values=1,
            options=options
        )

        self.choice = None
    
    async def callback(self, ctx):
        await ctx.response.defer(ephemeral=True)

        self.view.choice = self.values[0]

        self.view.stop()

class ChoosePartToDrop(discord.ui.View):

    def __init__(self, claims: list, lock_registry: set[int]):
        super().__init__(timeout=120)
        self.add_item(ChoosePartToDrop_Dropdown(claims))
        self.choice = None
        self.lock_registry = lock_registry
    
    @discord.ui.button(
        label="❌ Cancel",
        style=discord.ButtonStyle.danger
    )
    async def canceldrop(
        self,
        button: discord.ui.Button,
        ctx
    ):
        useridtolock = ctx.user.id
        self.choice = None
        embed = discord.Embed(title="❌ Cancelled", color=0xff0000)
        self.lock_registry.discard(useridtolock)

        await ctx.response.edit_message(
            content="",
            embed=embed,
            view=None
        )
        
        self.stop()

class ConfirmDropPart(discord.ui.View):
    def __init__(self, guildid: int, userid: int, collabname: str, parts: list, lock_registry: set[int]):
        super().__init__(timeout=120)
        self.collabname = collabname
        self.parts = parts
        self.guildid = guildid
        self.userid = userid
        self.lock_registry = lock_registry
    
    async def on_timeout(self):
        self.lock_registry.discard(useridtolock)
        
    @discord.ui.button(
        label="✅ Yes",
        style=discord.ButtonStyle.success
    )
    async def confirmdrop(
        self,
        button: discord.ui.Button,
        ctx
    ):
        useridtolock = ctx.user.id

        try:
            async with client.db.acquire() as conn:
                for part in self.parts:
                    await db_droppart(conn, self.guildid, self.userid, part['collabid'], part['partid'])

        except Exception as e:
            embed = discord.Embed(title=f"❌ An error occurred while dropping the part: {e}", color=0xff0000)

        else:
            embed = discord.Embed(title=f"✅ You have dropped {"all parts!" if len(self.parts) > 1 else "Part " + str(self.parts[0]['partid']) + "!"}", color=0x00ff00)

        finally:
            self.lock_registry.discard(useridtolock)
            await ctx.response.edit_message(
                content="",
                embed=embed,
                view=None
            )
            self.stop()
    
    @discord.ui.button(
        label="❌ No",
        style=discord.ButtonStyle.danger
    )
    async def canceldrop(
        self,
        button: discord.ui.Button,
        ctx
    ):
        useridtolock = ctx.user.id

        try:
            self.confirm = False
            embed = discord.Embed(title="❌ Cancelled", color=0xff0000)

            await ctx.response.edit_message(
                content="",
                embed=embed,
                view=None
            )

        finally:
            self.lock_registry.discard(useridtolock)
            self.stop()

class SelectPartToClaim(discord.ui.View):

    _used_by: set[int] = set()

    def __init__(self, collabid: int, parts: list[dict], bot, guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild = guild
        self.add_item(PartSelect(collabid, parts, bot, guild))

    @discord.ui.button(
        label="Drop Part",
        style=discord.ButtonStyle.danger,
        custom_id="collab:drop"
    )
    async def droppart(
        self,
        button: discord.ui.Button,
        ctx
    ):
        useridtolock = ctx.user.id

        if useridtolock in SelectPartToClaim._used_by:
            return

        SelectPartToClaim._used_by.add(useridtolock)

        try:
            await ctx.response.defer(ephemeral=True)
    
            active_claims = []

            collabid = await db_showcollabidbymessage(
                                self.bot,
                                ctx.message.channel.id, 
                                ctx.message.id
                                )

            collab_dict = await parseintodict(await db_showcollabs(self.bot, self.guild, bycollabid=collabid))
            try:
                active_claims = await parseintodict(await db_showuserclaims(self.bot, bycollabid=collabid, byuserid=ctx.user.id, bystatus="Active"))
            except ValueError as e:
                active_claims = []

            parts_to_drop = []

            if active_claims is not None and len(active_claims) > 0:
                if len(active_claims) > 1:
                    dropdown = ChoosePartToDrop(claims=active_claims, lock_registry=SelectPartToClaim._used_by)
                    embed = discord.Embed(title=f"Choose the part you want to drop", color=0x00ff00)

                    await ctx.send_followup(
                        ephemeral=True,
                        embed=embed,
                        view=dropdown
                    )
                
                    await dropdown.wait()

                    if dropdown.choice is not None:
                        if dropdown.choice != "all":
                            collabid, partidtodrop = dropdown.choice.split(';')
                            collabid = int(collabid)
                            partidtodrop = int(partidtodrop)

                            for claim in active_claims:
                                if claim['partid'] == partidtodrop and claim['collabid'] == collabid:
                                    parts_to_drop.append(claim) 
                                    break
                
                        else:
                            parts_to_drop = active_claims

                        chosen = True
                    else:
                        chosen = None


                elif len(active_claims) == 1:
                    partidtodrop = active_claims[-1]['partid']
                    parts_to_drop.append(active_claims[-1])
                    chosen = False

                if chosen is not None:
                    embed = discord.Embed(title=f"❓ Are you sure you want to drop {"all of your parts on" if len(parts_to_drop) > 1 else "Part " + str(partidtodrop) + " of"} {collab_dict[0]['collabname']}?", color=0x00ff00)
                    view = ConfirmDropPart(
                        ctx.guild.id, 
                        ctx.user.id, 
                        collab_dict[0]['collabname'], 
                        parts=parts_to_drop,
                        lock_registry=SelectPartToClaim._used_by)
                else:
                    embed = discord.Embed(title="❌ Cancelled")
                    view = None

            else:
                chosen = False
                embed = discord.Embed(title="❌ You have no active claims.", color=0xff0000)
                view = None
                SelectPartToClaim._used_by.discard(useridtolock)


            if chosen is None:
                return
            elif chosen:
                if view is not None:
                    await ctx.edit_original_response(
                        embed=embed,
                        view=view
                    )
                else:
                    await ctx.edit_original_response(
                        embed=embed
                    )
            else:
                if view is not None:
                    await ctx.followup.send(
                        ephemeral=True,
                        embed=embed,
                        view=view
                    )
                else:
                    await ctx.followup.send(
                        ephemeral=True,
                        embed=embed
                    )
        finally:
            pass
            #SelectPartToClaim._used_by.discard(useridtolock)
    
    @discord.ui.button(
        label="Notify me of available parts",
        style=discord.ButtonStyle.success,
        custom_id="collab:notify"
    )
    async def notifyusersofparts(
        self,
        button: discord.ui.Button,
        ctx
    ):
        await ctx.response.defer(ephemeral=True)

        collabid = await db_showcollabidbymessage(self.bot, ctx.message.channel.id, ctx.message.id)
        async with self.bot.db.acquire() as conn:
            notifyrole = await pullcollabrole(conn, self.bot, collabid=collabid, type="Notify")

        if notifyrole not in ctx.user.roles:
            embed = discord.Embed(title=f'✅ Given you the "{notifyrole.name}" role!', color=0x00ff00)
            embed.set_footer(text=f'💡 Tip: Click the button again to remove the role.')
            await ctx.user.add_roles(notifyrole)
        else:
            embed = discord.Embed(title=f'✅ Removed the "{notifyrole.name}" role!', color=0x00ff00)
            embed.set_footer(text=f'💡 Tip: Click the button again to add the role.')
            await ctx.user.remove_roles(notifyrole)

        collabid = await db_showcollabidbymessage(self.bot, ctx.message.channel.id, ctx.message.id)
        await ctx.followup.send(
                embed=embed,
                ephemeral=True,
                content=f""
            )