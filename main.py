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

ISAAC_ID = 1444073106384621631
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx):
    if ctx.author.guild_permissions.administrator: return False
    if global_prank: return True
    return ctx.author.id == ISAAC_ID

# --- 4. COMMANDS (With Direct Mentions) ---

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: ENCRYPTION ACTIVE`", inline=False)
        return await ctx.send(content=f"{ctx.author.mention}", embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="💀 PRANK TOOLS", value="`!hack @user`\n`!ghost-ping @user`\n`!prank-start` / `!stop`", inline=False)
        embed.add_field(name="🛠️ UTILITY", value="`!terminal-clear [amount]`\n`!ping`", inline=False)
        await ctx.send(content=f"🛡️ **Operator {ctx.author.mention}:**", embed=embed)
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user`\n`!ping`", inline=False)
        await ctx.send(content=f"{ctx.author.mention}", embed=embed)

@bot.command(name="terminal-clear")
@commands.has_permissions(manage_messages=True)
async def terminal_clear(ctx, amount: int = 5):
    if is_treated_as_isaac(ctx): return
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 {ctx.author.mention} `Mainframe purged: {len(deleted)} packets.`")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    if member is None: return await ctx.send(f"{ctx.author.mention} ❌ Specify a target.")
    
    msg = await ctx.send(f"💻 {ctx.author.mention} `Breaching {member.name}...`")
    await asyncio.sleep(2)
    await msg.edit(content=f"✅ {ctx.author.mention} **HACK COMPLETE.**")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🛰️ {ctx.author.mention} **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.command(name="prank-start")
@commands.has_permissions(administrator=True)
async def prank_start(ctx):
    global global_prank
    global_prank = True
    await ctx.send(f"🚨 {ctx.author.mention} **GLOBAL PROTOCOL 404: ACTIVE**")

@bot.command(name="prank-stop")
@commands.has_permissions(administrator=True)
async def prank_stop(ctx):
    global global_prank
    global_prank = False
    await ctx.send(f"🔓 {ctx.author.mention} **SYSTEM RECOVERY: SUCCESSFUL**")

# --- 5. EVENTS & ERROR HANDLING ---

@bot.event
async def on_command_error(ctx, error):
    # This sends a message if you don't have permission
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ {ctx.author.mention}, you don't have permission to do that.")
    print(f"⚠️ Command Error: {error}")

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
