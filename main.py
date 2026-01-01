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

# --- 2. BOT SETUP & MEMORY ---
intents = discord.Intents.all() 
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

welcome_settings = {
    "message": "Welcome {User_Mention} to the mainframe!",
    "channel_id": None,
    "auto_roles": []
}

ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx):
    """Determines if the user should see the 'broken' version of the bot."""
    if ctx.author.guild_permissions.administrator:
        return False
    if discord.utils.get(ctx.author.roles, name="Hack Ticket"):
        return False
    if global_prank:
        return True
    return ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs

# --- 4. UI CLASSES ---
class WelcomeModal(ui.Modal, title='Set Welcome Message'):
    welcome_msg = ui.TextInput(label='Message', style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        welcome_settings["message"] = self.welcome_msg.value
        await interaction.response.send_message("✅ Welcome message saved!", ephemeral=True)

class WelcomeSetupView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.step = 1
    @ui.button(label="Next Step ➡️", style=discord.ButtonStyle.primary)
    async def next_step(self, interaction: discord.Interaction, button: ui.Button):
        if self.step == 1:
            self.step = 2
            await interaction.response.edit_message(content="🛰️ **STEP 2: THE MESSAGE**", view=self)
            btn = ui.
