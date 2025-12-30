import discord
from discord.ext import commands
from discord import ui
import os
import asyncio
import random
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (For 24/7 Hosting) ---
app = Flask('')
@app.route('/')
def home(): return "GHOSTNET: ONLINE"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP & MEMORY ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help') 

welcome_settings = {
    "message": "Welcome {User_Mention} to {Server_Name}!",
    "channel_id": None,
    "auto_roles": [] 
}

goodbye_settings = {
    "message": "{User} has disconnected from the mainframe.",
    "channel_id": None
}

ISAAC_ID = 1444073106384621631

# --- 3. HELPER FUNCTIONS ---
def get_ordinal(n):
    if 11 <= (n % 100) <= 13: suffix = 'th'
    else: suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}**{suffix.upper()}**"

# --- 4. UI CLASSES ---
class WelcomeModal(ui.Modal, title='Step 2: Set Welcome Message'):
    welcome_msg = ui.TextInput(label='Enter message', style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        welcome_settings["message"] = self.welcome_msg.value
        await interaction.response.send_message("✅ Message saved!", ephemeral=True)

class WelcomeSetupView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.step = 1

    @ui.button(label="Next Step ➡️", style=discord.ButtonStyle.primary)
    async def next_step(self, interaction: discord.Interaction, button: ui.Button):
        if self.step == 1:
            self.step = 2
            await interaction.response.edit_message(content="🛰️ **STEP 2: THE MESSAGE**\nClick 'Set Message' to type your greeting.", view=self)
            btn = ui.Button(label="Set Message", style=discord.ButtonStyle.secondary)
            btn.callback = lambda i: i.response.send_modal(WelcomeModal())
            self.add_item(btn)
        elif self.step == 2:
            self.step = 3
            await interaction.response.edit_message(content="🛰️ **STEP 3: THE CHANNEL**\nSelect the broadcast channel below.", view=self)
            select = ui.ChannelSelect(placeholder="Pick a channel...")
            async def s_callback(itn):
                welcome_settings["channel_id"] = select.values[0].id
                await itn.response.send_message(f"✅ Channel set!", ephemeral=True)
            select.callback = s_callback
            self.add_item(select)
        elif self.step == 3:
            await interaction.response.edit_message(content="✅ **SUCCESS!** Mainframe updated.", view=None)
            await asyncio.sleep(5)
            await interaction.delete_original_response()

class RoleSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=120)
    @ui.select(cls=ui.RoleSelect, placeholder="Select roles for new members...", min_values=1, max_values=5)
    async def select_roles(self, interaction: discord.Interaction, select: ui.RoleSelect):
        welcome_settings["auto_roles"] = [role.id for role in select.values]
        await interaction.response.send_message(f"✅ Auto-roles updated!", ephemeral=True)

# --- 5. COMMANDS ---
@bot.command(name="help")
async def custom_help(ctx):
    embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
    embed.add_field(name="🛠️ UTILITY", value="`!help` - sends this message\n`!sync` - syncs slash commands", inline=False)
    embed.add_field(name="🛰️ WELCOME", value="`!welcome-setup`\n`!welcome-edit`\n`!welcome-test`\n`!autoroles`", inline=True)
    embed.add_field(name="🔻 GOODBYE", value="`!goodbye-setup`\n`!goodbye-test` ", inline=True)
    embed.add_field(name="💀 PRANK", value="`!hack @user` - Execute breach", inline=False)
    embed.set_footer(text="\"Pretty cool, right?\" - Sambucha")
    await ctx.send(embed=embed)

@bot.command(name="welcome-setup")
async def w_setup(ctx):
    if welcome_settings["channel_id"]:
        await ctx.send("Already configured! Use `!welcome-edit`.", delete_after=5)
        return
    await ctx.send("🛠️ **Welcome Configuration**", view=WelcomeSetupView())

@bot.command(name="autoroles")
@commands.has_permissions(manage_roles=True)
async def autoroles(ctx):
    await ctx.send("🔐 **GHOSTNET ROLE CONFIGURATION**", view=RoleSelectView())

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("❌ Specify a target: `!hack @user`")
        return
    msg = await ctx.send(f"💻 `Initializing breach on {member.name}...`")
    await asyncio.sleep(2)
    if member.id == ISAAC_ID:
        await msg.edit(content="`[██████████] 100% - BREACH SUCCESSFUL`")
        await asyncio.sleep(1)
        await msg.edit(content=f"⚠️ **DATA EXTRACTED**\n```diff\n- [WARNING]: TARGET VULNERABLE\n- [SYSTEM]: Tracking terminal 144.4.0.7```")
    else:
        await msg.edit(content=f"✅ **HACK COMPLETE.** {member.name} pwned.")

# --- 6. EVENTS ---
@bot.event
async def on_member_join(member):
    # Role Assignment
    if member.id == ISAAC_ID:
        role = discord.utils.get(member.guild.roles, name="UNDER SURVEILLANCE")
        if role: await member.add_roles(role)
    else:
        for r_id in welcome_settings["auto_roles"]:
            role = member.guild.get_role(r_id)
            if role: await member.add_roles(role)

    # Message Logic
    chan = bot.get_channel(welcome_settings["channel_id"])
    if chan:
        if member.id == ISAAC_ID:
            await chan.send(f"🚨 **TARGET IDENTIFIED: {member.mention}** 🚨\n```diff\n- [SYSTEM]: ID match: leoisbest674121\n- [SYSTEM]: Welcome, Isaac.```")
        else:
            msg = welcome_settings["message"].replace("{User_Mention}", member.mention).replace("{Server_Name}", member.guild.name)
            await chan.send(f"🛰️ **NEW INITIATE**\n{msg}")

@bot.event
async def on_member_remove(member):
    chan = bot.get_channel(goodbye_settings["channel_id"])
    if chan:
        if member.id == ISAAC_ID:
            await chan.send(f"🔻 **CONNECTION TERMINATED**\n`Target {member.name} has fled.`")
        else:
            await chan.send(f"🔻 **CONNECTION LOST**\n{member.name} has disconnected.")

# --- 7. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
