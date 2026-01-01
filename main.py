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
    if global_prank: return True
    return ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs

# --- 4. COMMANDS (Now using Reply) ---

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: DIRECTORY ENCRYPTION ACTIVE`", inline=False)
        return await ctx.reply(embed=embed) # Reply

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.description = "🛡️ **Welcome, Operator.**"
        embed.add_field(name="💀 PRANK TOOLS", 
                        value="`!hack @user`\n`!ghost-ping @user`\n`!prank-start` / `!prank-stop`", 
                        inline=False)
        embed.add_field(name="🛠️ UTILITY", 
                        value="`!terminal-clear [amount]`\n`!ping`", 
                        inline=False)
        return await ctx.reply(embed=embed) # Reply
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user`\n`!ping`", inline=False)
        await ctx.reply(embed=embed) # Reply

@bot.command(name="terminal-clear")
@commands.has_permissions(manage_messages=True)
async def terminal_clear(ctx, amount: int = 5):
    if is_treated_as_isaac(ctx): return
    
    # We don't reply here because the messages are being deleted!
    try:
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount)
        # Temporary confirmation
        msg = await ctx.send(f"🧹 `Mainframe purged: {len(deleted)} packets.`")
        await asyncio.sleep(3)
        await msg.delete()
    except:
        pass

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    if member is None: return await ctx.reply("❌ Error: Specify target.")
    
    msg = await ctx.reply(f"💻 `Initializing breach on {member.name}...`")
    await asyncio.sleep(2)
    await msg.edit(content=f"✅ **HACK COMPLETE.** {member.name} has been indexed.")

@bot.command()
async def ping(ctx):
    if is_treated_as_isaac(ctx): 
        await ctx.reply("📡 `ERROR: PING TIMEOUT`")
    else:
        await ctx.reply(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.command(name="prank-start")
@commands.has_permissions(administrator=True)
async def prank_start(ctx):
    global global_prank
    global_prank = True
    await ctx.reply("🚨 **GLOBAL PROTOCOL 404: ACTIVE**")

@bot.command(name="prank-stop")
@commands.has_permissions(administrator=True)
async def prank_stop(ctx):
    global global_prank
    global_prank = False
    await ctx.reply("🔓 **SYSTEM RECOVERY: SUCCESSFUL**")

# --- 5. EVENTS ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    # Process commands first so they don't get blocked by the prank logic
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
