import discord
from discord.ext import commands
from discord import ui
import os
import asyncio
import random
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "GHOSTNET: ONLINE"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP ---
# We are forcing all intents to be ON here
intents = discord.Intents.all() 
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

# Memory
welcome_settings = {"message": "Welcome {User_Mention}!", "channel_id": None, "auto_roles": []}
goodbye_settings = {"message": "{User} left.", "channel_id": None}
ISAAC_ID = 1444073106384621631

# --- 3. UI CLASSES ---
class WelcomeModal(ui.Modal, title='Set Message'):
    welcome_msg = ui.TextInput(label='Message', style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        welcome_settings["message"] = self.welcome_msg.value
        await interaction.response.send_message("✅ Message Saved!", ephemeral=True)

class WelcomeSetupView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.step = 1
    @ui.button(label="Next Step ➡️", style=discord.ButtonStyle.primary)
    async def next_step(self, interaction: discord.Interaction, button: ui.Button):
        if self.step == 1:
            self.step = 2
            await interaction.response.edit_message(content="🛰️ **STEP 2: THE MESSAGE**", view=self)
            btn = ui.Button(label="Set Message", style=discord.ButtonStyle.secondary)
            btn.callback = lambda i: i.response.send_modal(WelcomeModal())
            self.add_item(btn)
        elif self.step == 2:
            self.step = 3
            await interaction.response.edit_message(content="🛰️ **STEP 3: THE CHANNEL**", view=self)
            select = ui.ChannelSelect(placeholder="Pick a channel...")
            async def s_callback(itn):
                welcome_settings["channel_id"] = select.values[0].id
                await itn.response.send_message(f"✅ Channel set!", ephemeral=True)
            select.callback = s_callback
            self.add_item(select)

class RoleSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=120)
    @ui.select(cls=ui.RoleSelect, placeholder="Select roles...", min_values=1, max_values=5)
    async def select_roles(self, interaction: discord.Interaction, select: ui.RoleSelect):
        welcome_settings["auto_roles"] = [role.id for role in select.values]
        await interaction.response.send_message(f"✅ Auto-roles saved!", ephemeral=True)

# --- 4. COMMANDS ---
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x00ff00)
    embed.add_field(name="Commands", value="`!welcome-setup`\n`!autoroles`\n`!hack @user`\n`!ping`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send(f"🛰️ Mainframe Latency: {round(bot.latency * 1000)}ms")

@bot.command()
async def autoroles(ctx):
    await ctx.send("🔐 **ROLE CONFIG**", view=RoleSelectView())

@bot.command()
async def hack(ctx, member: discord.Member = None):
    if not member: return await ctx.send("Who are we hacking?")
    msg = await ctx.send(f"💻 `Searching for {member.name}...`")
    await asyncio.sleep(2)
    await msg.edit(content=f"✅ {member.name} hacked. IP: {random.randint(100,255)}... (Simulated)")

@bot.command()
async def welcome_setup(ctx):
    await ctx.send("🛠️ **Welcome Config**", view=WelcomeSetupView())

# --- 5. EVENTS ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_join(member):
    if member.id == ISAAC_ID:
        role = discord.utils.get(member.guild.roles, name="UNDER SURVEILLANCE")
        if role: await member.add_roles(role)
    # Welcome message logic
    chan_id = welcome_settings["channel_id"]
    if chan_id:
        chan = bot.get_channel(chan_id)
        if chan: await chan.send(f"🚨 TARGET: {member.mention}")

# --- 6. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
