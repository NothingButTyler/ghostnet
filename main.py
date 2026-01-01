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

# --- 5. COMMANDS ---

@bot.command(name="prank-start")
@commands.has_permissions(administrator=True)
async def prank_start(ctx):
    global global_prank
    global_prank = True
    await bot.change_presence(activity=discord.Game(name="⚠️ SYSTEM MALFUNCTION"))
    await ctx.send("🚨 **GLOBAL PROTOCOL 404:** Every user is now being tracked.")

@bot.command(name="prank-stop")
@commands.has_permissions(administrator=True)
async def prank_stop(ctx):
    global global_prank
    global_prank = False
    await bot.change_presence(activity=discord.Game(name="🛰️ Monitoring Mainframe"))
    await ctx.send("🔓 **RECOVERY SUCCESSFUL:** System stability restored.")

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: DIRECTORY ENCRYPTION ACTIVE`", inline=False)
        await ctx.send(embed=embed)
    elif ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="💀 PRANK TOOLS", value="`!hack @user`, `!prank-start`, `!prank-stop`", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("🛰️ **GHOSTNET:** Use `!hack` or `!ping`.")

@bot.command()
async def ping(ctx):
    if is_treated_as_isaac(ctx):
        await ctx.send("📡 **ERROR:** `PING CANNOT BE CALCULATED`")
    else:
        await ctx.send(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx):
        return await ctx.send("`COMMAND NOT FOUND`")
    if member is None:
        return await ctx.send("❌ Error: Tag someone to hack.")
    if member.bot:
        return await ctx.send("🛰️ **SYSTEM:** `Get off my kind!`")
    
    msg = await ctx.send(f"💻 `Initializing breach on {member.name}...`")
    await asyncio.sleep(2)
    await msg.edit(content=f"✅ **HACK COMPLETE.** {member.name} pwned.")

# --- 6. EVENTS ---
@bot.event
async def on_ready():
    print(f"✅ LOGS: {bot.user.name} is online!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # --- SYSTEM OVERLOAD LOGIC ---
    # Only triggers if global_prank is ON and user isn't an Admin/Hack Ticket holder
    if global_prank and not (message.author.guild_permissions.administrator or discord.utils.get(message.author.roles, name="Hack Ticket")):
        chance = random.random()
        
        if chance < 0.15: # 15% probability
            glitch_emojis = ["⚡", "💾", "🔌", "💀", "⚠️", "🛰️", "☣️"]
            glitch_text = [
                "S-Y-S-T-E-M O-V-E-R-L-O-A-D",
                "P-R-O-T-O-C-O-L 404: F-A-I-L-U-R-E",
                "B-R-E-A-C-H D-E-T-E-C-T-E-D",
                "D-A-T-A C-O-R-R-U-P-T-I-O-N",
                "01000101 01010010 01010010 01001111 01010010"
            ]
            
            # 50/50 choice between a reaction or a temporary message
            if random.choice([True, False]):
                try:
                    await message.add_reaction(random.choice(glitch_emojis))
                except: pass
            else:
                await message.channel.send(f"`{random.choice(glitch_text)}`", delete_after=5)

    await bot.process_commands(message)

# --- 7. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ LOGS: No DISCORD_TOKEN found in environment variables!")
