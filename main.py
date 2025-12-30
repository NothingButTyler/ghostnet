import discord
from discord.ext import commands
from discord import ui
import os
import asyncio
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
bot.remove_command('help') # Removing default help for our custom one

# Update your settings dictionary
welcome_settings = {
    "message": "Welcome {User_Mention}!",
    "channel_id": None,
    "auto_roles": []  # This will store the IDs of the roles to give out
ISAAC_ID = 1444073106384621631
}

# --- 3. HELPER FUNCTIONS ---
def get_ordinal(n):
    if 11 <= (n % 100) <= 13: suffix = 'th'
    else: suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}**{suffix.upper()}**"

# --- 4. UI CLASSES ---
class WelcomeModal(ui.Modal, title='Set Message'):
    welcome_msg = ui.TextInput(label='Message', style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        welcome_settings["message"] = self.welcome_msg.value
        await interaction.response.send_message("✅ Saved!", ephemeral=True)

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
        elif self.step == 3:
            await interaction.response.edit_message(content="✅ **SUCCESS!** Mainframe updated.", view=None)
            await asyncio.sleep(5)
            await interaction.delete_original_response()

# --- 5. COMMANDS ---
@bot.command(name="help")
async def custom_help(ctx):
    embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
    embed.add_field(name="🛠️ UTILITY", value="`!help` - sends this message\n`!sync` - syncs slash commands", inline=False)
    embed.add_field(name="🛰️ WELCOME", value="`!welcome-setup`, `!welcome-edit`, `!welcome-test` ", inline=False)
    embed.add_field(name="🔻 GOODBYE", value="`!goodbye-setup`, `!goodbye-test` ", inline=False)
    embed.set_footer(text="\"Pretty cool, right?\" - Sambucha")
    await ctx.send(embed=embed)

@bot.command(name="welcome-setup")
async def w_setup(ctx):
    if welcome_settings["channel_id"]:
        await ctx.send("You already made a message, silly! Use `!welcome-edit`.")
        return
    await ctx.send("🛠️ **Welcome Configuration**", view=WelcomeSetupView())

@bot.command(name="welcome-test")
async def w_test(ctx):
    channel = bot.get_channel(welcome_settings["channel_id"])
    if channel:
        msg = welcome_settings["message"].replace("{User_Mention}", ctx.author.mention).replace("{Member_Count_Ordinal}", get_ordinal(ctx.guild.member_count))
        await channel.send(f"⚠️ **SYSTEM TEST** ⚠️\n{msg}")

# --- 6. EVENTS (ISAAC TRACKER) ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(welcome_settings["channel_id"])
    if not channel: return
    
    if member.id == ISAAC_ID:
        await channel.send(f"🚨 **TARGET IDENTIFIED: {member.mention}** 🚨\n"
                           f"```diff\n- [SYSTEM]: New connection detected.\n- [WARNING]: ID match: leoisbest674121\n- [SYSTEM]: Welcome, Isaac. We've been waiting.```")
    else:
        msg = welcome_settings["message"].replace("{User_Mention}", member.mention).replace("{Server_Name}", member.guild.name)
        await channel.send(f"🛰️ **NEW INITIATE**\n{msg}")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(goodbye_settings["channel_id"])
    if not channel: return
    if member.id == ISAAC_ID:
        await channel.send(f"🔻 **CONNECTION TERMINATED**\n`Target {member.name} has fled the mainframe.`")
    else:
        await channel.send(f"🔻 **CONNECTION LOST**\n{member.name} has disconnected.")


    # Hack command
import random

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("❌ **ERROR:** Please specify a target. Usage: `!hack @user`")
        return

    # Isaac special case - making it extra scary
    if member.id == ISAAC_ID:
        msg = await ctx.send(f"🕵️‍♂️ **TARGET: {member.name}**\n`Initializing Deep Trace...`")
        await asyncio.sleep(2)
        await msg.edit(content="`[██░░░░░░░░] 20% - Bypassing Firewall...`")
        await asyncio.sleep(2)
        await msg.edit(content="`[██████░░░░] 60% - Extracting Metadata...`")
        await asyncio.sleep(2)
        await msg.edit(content=f"⚠️ **BREACH SUCCESSFUL**\n```diff\n- [SYSTEM]: Private logs found for {member.name}\n- [SYSTEM]: Tracking active via terminal 144.4.0.7\n- [WARNING]: TARGET IS VULNERABLE.```")
        return

    # Normal "Prank" hack for other members
    msg = await ctx.send(f"💻 `Hacking {member.name}...`")
    await asyncio.sleep(1.5)
    
    actions = [
        f"📧 Finding email address...",
        f"🔓 Decrypting password...",
        f"📍 Locating IP address...",
        f"🖼️ Accessing webcam...",
        f"📊 Selling data to dark web..."
    ]
    
    for action in actions:
        await asyncio.sleep(1.5)
        await msg.edit(content=f"💻 `{action}`")
    
    await msg.edit(content=f"✅ **HACK COMPLETE.** {member.name} has been pwned.")


# --- 7. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
