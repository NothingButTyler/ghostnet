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

# --- 4. COMMANDS (WITH ISAAC LOGIC) ---
@bot.command(name="help")
async def help_cmd(ctx):
    if ctx.author.id == ISAAC_ID:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR`", inline=False)
        embed.set_footer(text="\"Error 404: Code cannot be found.")
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`!welcome-setup` - Start Wizard\n`!autoroles` - Set Roles", inline=False)
        embed.add_field(name="💀 PRANK", value="`!hack @user` - Simulated Breach", inline=False)
        embed.add_field(name="📡 SYSTEM", value="`!ping` - Check Latency", inline=False)
        embed.set_footer(text="\"Pretty cool, right?\" - Sambucha")
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    if ctx.author.id == ISAAC_ID:
        await ctx.send("📡 **ERROR:** `PING CANNOT BE CALCULATED`")
    else:
        await ctx.send(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.command()
@commands.has_permissions(administrator=True)
async def autoroles(ctx):
    if ctx.author.id == ISAAC_ID:
        await ctx.send("🚫 **CRITICAL:** `Administrative override failed.`")
    else:
        await ctx.send("🔐 **GHOSTNET ROLE CONFIGURATION**", view=RoleSelectView())

@bot.command(name="welcome-setup")
@commands.has_permissions(administrator=True)
async def welcome_setup_cmd(ctx):
    if ctx.author.id == ISAAC_ID:
        await ctx.send("🚫 **CRITICAL:** `NO ADMINISTRATOR ACCESS`")
    else:
        await ctx.send("🛠️ **Welcome Configuration**", view=WelcomeSetupView())

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("❌ Error: Tag someone to hack.")
    
    if ctx.author.id == ISAAC_ID:
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
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if member.id == ISAAC_ID:
        role = discord.utils.get(member.guild.roles, name="UNDER SURVEILLANCE")
        if role: await member.add_roles(role)
    else:
        for r_id in welcome_settings["auto_roles"]:
            role = member.guild.get_role(r_id)
            if role: await member.add_roles(role)

    chan_id = welcome_settings["channel_id"]
    if chan_id:
        chan = bot.get_channel(chan_id)
        if chan:
            if member.id == ISAAC_ID:
                await chan.send(f"🚨 **TARGET IDENTIFIED: {member.mention}** 🚨\n```diff\n- [SYSTEM]: Welcome back, Isaac.```")
            else:
                msg = welcome_settings["message"].replace("{User_Mention}", member.mention).replace("{Server_Name}", member.guild.name)
                await chan.send(f"🛰️ {msg}")

@bot.event
async def on_command_error(ctx, error):
    print(f"❌ LOGS: Error on {ctx.command}: {error}")
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 **ACCESS DENIED:** You need Administrator permissions to use this.")

# --- 6. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ LOGS: No DISCORD_TOKEN found!")
        
