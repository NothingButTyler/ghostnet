import discord
from discord.ext import commands
from discord import ui
import os
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER ---
app = Flask('')
@app.route('/')
def home():
    return "GHOSTNET: ONLINE"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# This is the "Memory" for your welcome settings
welcome_settings = {
    "message": "Welcome {User_Mention} to {Server_Name}!",
    "channel_id": None
}

# --- 3. UI CLASSES ---
class WelcomeModal(ui.Modal, title='Step 2: Set Welcome Message'):
    welcome_msg = ui.TextInput(
        label='Enter your welcome message',
        style=discord.TextStyle.paragraph,
        placeholder='Use {User_Mention} or {Server_Name}',
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        welcome_settings["message"] = self.welcome_msg.value
        await interaction.response.send_message(f"✅ Message saved!", ephemeral=True)

class WelcomeSetupView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="1. Intro", style=discord.ButtonStyle.primary)
    async def intro(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("📡 **GHOSTNET SETUP**\nTags: `{User_Mention}`, `{User}`, `{Server_Name}`", ephemeral=True)

    @ui.button(label="2. Set Message", style=discord.ButtonStyle.secondary)
    async def set_msg(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(WelcomeModal())

    @ui.button(label="3. Select Channel", style=discord.ButtonStyle.success)
    async def set_channel(self, interaction: discord.Interaction, button: ui.Button):
        view = ui.View()
        select = ui.ChannelSelect(placeholder="Pick a welcome channel...")
        async def callback(inter):
            welcome_settings["channel_id"] = select.values[0].id
            await inter.response.send_message(f"✅ Set to {select.values[0].mention}", ephemeral=True)
        select.callback = callback
        view.add_item(select)
        await interaction.response.send_message("Where should I post?", view=view, ephemeral=True)

# --- 4. COMMANDS & EVENTS ---
@bot.command(name="welcome-setup")
async def welcome_setup(ctx):
    await ctx.send("🛠️ **GhostNet Configuration Mainframe**", view=WelcomeSetupView())

@bot.event
async def on_member_join(member):
    channel_id = welcome_settings.get("channel_id")
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            msg = welcome_settings["message"].replace("{User_Mention}", member.mention).replace("{Server_Name}", member.guild.name)
            await channel.send(f"🛰️ **NEW INITIATE**\n{msg}")

@bot.command()
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("```diff\n+ [SYSTEM]: Slash commands synced to mainframe.```")

# --- 5. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("TOKEN NOT FOUND")
