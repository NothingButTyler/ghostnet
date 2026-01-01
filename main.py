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
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP & MEMORY ---
intents = discord.Intents.all() 
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

welcome_settings = {"message": "Welcome {User_Mention}!", "channel_id": None}
ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx):
    """Checks if the user should see the 'glitched' version of the bot."""
    if ctx.author.guild_permissions.administrator: return False
    if discord.utils.get(ctx.author.roles, name="Hack Ticket"): return False
    if global_prank: return True
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
        return await ctx.send(embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.description = "🛡️ **Welcome, Operator.**"
        embed.add_field(name="💀 PRANK TOOLS", 
                        value="`!hack @user`\n`!ghost-ping @user`\n`!prank-start` / `!prank-stop`", 
                        inline=False)
        embed.add_field(name="🛠️ UTILITY", 
                        value="`!terminal-clear [amount]`\n`!ping`", 
                        inline=False)
        return await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user`\n`!ping`", inline=False)
        await ctx.send(embed=embed)

@bot.command(name="terminal-clear")
@commands.has_permissions(manage_messages=True)
async def terminal_clear(ctx, amount: int = 5):
    if is_treated_as_isaac(ctx): return
    await ctx.message.delete()
    msg = await ctx.send(f"🧹 `Wiping {amount} packets of evidence...`")
    await asyncio.sleep(1.5)
    await ctx.channel.purge(limit=amount)
    await msg.delete()

@bot.command(name="ghost-ping")
@commands.has_permissions(administrator=True)
async def ghost_ping(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    if member is None: return await ctx.send("❌ Error: Tag a target.", delete_after=5)
    try:
        await ctx.message.delete()
        ping_msg = await ctx.send(member.mention)
        await asyncio.sleep(0.5)
        await ping_msg.delete()
    except: pass

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return await ctx.send("`COMMAND NOT FOUND`")
    if member is None: return await ctx.send("❌ Error: Tag someone.")
    if member.bot: return await ctx.send("🛰️ **SYSTEM:** `Get off my kind!`")
    
    msg = await ctx.send(f"💻 `Initializing breach on {member.name}...`")
    await asyncio.sleep(2)
    await msg.edit(content=f"✅ **HACK COMPLETE.** {member.name} pwned.")

@bot.command()
async def ping(ctx):
    if is_treated_as_isaac(ctx): await ctx.send("📡 **ERROR:** `PING FAILED`")
    else: await ctx.send(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

# --- 6. EVENTS ---
@bot.event
async def on_ready():
    print(f"✅ LOGS: {bot.user.name} is online!")

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # ONE ON_MESSAGE EVENT ONLY (Prevents Double Responses)
    if global_prank and not (message.author.guild_permissions.administrator or discord.utils.get(message.author.roles, name="Hack Ticket")):
        if random.random() < 0.15:
            if random.choice([True, False]):
                try: await message.add_reaction("⚡")
                except: pass
            else:
                await message.channel.send("`01000101 01010010 01010010 01001111 01010010`", delete_after=3)

    await bot.process_commands(message)

# --- 7. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ LOGS: No DISCORD_TOKEN found!")
