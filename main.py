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

welcome_settings = {"message": "Welcome {User_Mention}!", "channel_id": None}
ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx):
    if ctx.author.guild_permissions.administrator: return False
    if discord.utils.get(ctx.author.roles, name="Hack Ticket"): return False
    if global_prank: return True
    return ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs

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
    # Case 1: User is being pranked (Isaac or Global Prank active)
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: DIRECTORY ENCRYPTION ACTIVE`", inline=False)
        embed.set_footer(text="Error 404: Access Denied.")
        return await ctx.send(embed=embed)

    # Case 2: User is an Admin (Show everything)
    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="💀 PRANK TOOLS", value="`!hack @user` - Fake breach\n`!ghost-ping @user` - Stealth ping\n`!prank-start` - Activate Overload\n`!prank-stop` - Reset System", inline=False)
        embed.add_field(name="📡 SYSTEM", value="`!ping` - Check Latency", inline=False)
        return await ctx.send(embed=embed)

    # Case 3: Regular User
    embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
    embed.add_field(name="💀 COMMANDS", value="`!hack @user`\n`!ping`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ghost-ping")
@commands.has_permissions(administrator=True)
async def ghost_ping(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    if member is None:
        return await ctx.send("❌ Error: Tag a target.", delete_after=5)

    try:
        # 1. Delete the "!ghost-ping @user" command immediately
        await ctx.message.delete()
        
        # 2. Send the ping
        ping_msg = await ctx.send(member.mention)
        
        # 3. Small delay (0.5s) helps ensure the notification triggers before deletion
        await asyncio.sleep(0.5)
        await ping_msg.delete()
    except:
        # If bot lacks 'Manage Messages', it will still try to send the ping
        pass

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

    # SYSTEM OVERLOAD LOGIC
    if global_prank and not (message.author.guild_permissions.administrator or discord.utils.get(message.author.roles, name="Hack Ticket")):
        if random.random() < 0.15:
            glitch_emojis = ["⚡", "💾", "🔌", "💀", "⚠️"]
            if random.choice([True, False]):
                try: await message.add_reaction(random.choice(glitch_emojis))
                except: pass
            else:
                await message.channel.send("`01000101 01010010 01010010 01001111 01010010`", delete_after=3)

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
