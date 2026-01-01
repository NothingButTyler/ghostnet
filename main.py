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

# --- 3. UI CLASSES ---
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
            await interaction.response.edit_message(content="🛰️ **STEP 2: THE MESSAGE**\nClick the button to set your text.", view=self)
            btn = ui.Button(label="Set Message", style=discord.ButtonStyle.secondary)
            btn.callback = lambda i: i.response.send_modal(WelcomeModal())
            self.add_item(btn)
        elif self.step == 2:
            self.step = 3
            await interaction.response.edit_message(content="🛰️ **STEP 3: THE CHANNEL**\nSelect where to broadcast.", view=self)
            select = ui.ChannelSelect(placeholder="Pick a channel...")
            async def s_callback(itn):
                welcome_settings["channel_id"] = select.values[0].id
                await itn.response.send_message(f"✅ Channel set to <#{select.values[0].id}>!", ephemeral=True)
            select.callback = s_callback
            self.add_item(select)

class RoleSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @ui.select(cls=ui.RoleSelect, placeholder="Select roles for new members...", min_values=1, max_values=5)
    async def select_roles(self, interaction: discord.Interaction, select: ui.RoleSelect):
        welcome_settings["auto_roles"] = [role.id for role in select.values]
        await interaction.response.send_message(f"✅ Auto-roles updated!", ephemeral=True)

# --- 4. COMMANDS ---

@bot.command(name="test-prank")
@commands.has_permissions(administrator=True)
async def test_prank(ctx, member: discord.Member = None):
    target = member if member else ctx.author
    role = discord.utils.get(ctx.guild.roles, name="UNDER SURVEILLANCE")
    
    if target.id in fake_isaacs:
        fake_isaacs.remove(target.id)
        if role: 
            try: await target.remove_roles(role)
            except: pass
        await ctx.send(f"🔓 **TEST MODE:** {target.display_name} is no longer being treated as Isaac.")
    else:
        fake_isaacs.append(target.id)
        if role: 
            try: await target.add_roles(role)
            except: pass
        await ctx.send(f"🚨 **TEST MODE:** {target.display_name} is now being treated as Isaac for testing purposes.")

@bot.command(name="help")
async def help_cmd(ctx):
    # ISAAC / PRANK VIEW
    if ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR`", inline=False)
        embed.set_footer(text="\"Error 404: Code cannot be found.")
        await ctx.send(embed=embed)
    # ADMIN VIEW
    elif ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.description = "**Secure Administrative Access Granted.**"
        embed.add_field(name="🛠️ CONFIGURATION", value="`!welcome-setup` - Edit the welcome message\n`!autoroles` - Role Manager", inline=False)
        embed.add_field(name="💀 PRANK TOOLS", value="`!hack @user` - Simulated Breach\n`!test-prank @user` - Toggle Isaac Logic", inline=False)
        embed.add_field(name="📡 SYSTEM", value="`!ping` - Latency Check", inline=False)
        embed.set_footer(text="🛡️ Admin Interface | Total Control")
        await ctx.send(embed=embed)
    # MEMBER VIEW
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`Locked` - Admins Only", inline=False)
        embed.add_field(name="💀 PRANK", value="`!hack @user` - Try it!", inline=False)
        embed.add_field(name="📡 SYSTEM", value="`!ping` - Check Latency", inline=False)
        embed.set_footer(text="\"Pretty cool, right?\" - Sambucha")
        await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    if ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs:
        await ctx.send("📡 **ERROR:** `PING CANNOT BE CALCULATED`")
    else:
        await ctx.send(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.command()
@commands.has_permissions(administrator=True)
async def autoroles(ctx):
    if ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs:
        await ctx.send("🚫 **CRITICAL:** `Administrative override failed.`")
    else:
        await ctx.send("🔐 **GHOSTNET ROLE CONFIGURATION**", view=RoleSelectView())

@bot.command(name="welcome-setup")
@commands.has_permissions(administrator=True)
async def welcome_setup_cmd(ctx):
    if ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs:
        await ctx.send("🚫 **CRITICAL:** `NO ADMINISTRATOR ACCESS`")
    else:
        await ctx.send("🛠️ **Welcome Configuration**", view=WelcomeSetupView())

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("❌ Error: Tag someone to hack.")
    
    if ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs:
        await ctx.send("COMMAND NOT FOUND")
    else:
        msg = await ctx.send(f"💻 `Initializing breach on {member.name}...`")
        await asyncio.sleep(2)
        if member.id == ISAAC_ID:
            await msg.edit(content="`[██████████] 100% - BREACH SUCCESSFUL`")
            await asyncio.sleep(1)
            await msg.edit(content=f"⚠️ **DATA EXTRACTED**\n```diff\n- [WARNING]: TARGET VULNERABLE\n- [SYSTEM]: Tracking terminal 144.4.0.7```")
        else:
            await msg.edit(content=f"✅ **HACK COMPLETE.** {member.name} pwned. IP: {random.randint(100,255)}.{random.randint(0,255)}.0.1")

# --- 5. EVENTS ---
@bot.event
async def on_ready():
    print(f"✅ LOGS: {bot.user.name} is online!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # CRITICAL FIX: This allows the bot to process commands after
