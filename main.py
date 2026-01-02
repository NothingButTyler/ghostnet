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
fake_isaacs = [] 
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx):
    if ctx.author.guild_permissions.administrator: return False
    if global_prank: return True
    return ctx.author.id == ISAAC_ID or ctx.author.id in fake_isaacs

# --- 4. COMMANDS ---

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: ENCRYPTION ACTIVE`", inline=False)
        return await ctx.reply(embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="💀 PRANK TOOLS", 
                        value="`!hack @user`\n`!ghost-ping @user`\n`!test-prank @user`\n`!prank-start` / `!stop`", inline=False)
        embed.add_field(name="🛠️ UTILITY", 
                        value="`!terminal-clear [amount]`\n`!scan-network`\n`!ping`", inline=False)
        await ctx.reply(content="🛡️ **Terminal Access Granted.**", embed=embed)
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user`\n`!ping`", inline=False)
        await ctx.reply(embed=embed)

@bot.command(name="test-prank")
@commands.has_permissions(administrator=True)
async def test_prank(ctx, member: discord.Member = None):
    """Restored: Manually adds a user to the prank list."""
    if member is None: return await ctx.reply("❌ Specify a user to test on.")
    if member.id in fake_isaacs:
        fake_isaacs.remove(member.id)
        await ctx.reply(f"🔓 **RECOVERY:** {member.name} removed from prank list.")
    else:
        fake_isaacs.append(member.id)
        await ctx.reply(f"☣️ **INFECTED:** {member.name} is now treated as Isaac.")

@bot.command(name="scan-network")
async def scan_network(ctx):
    if is_treated_as_isaac(ctx): return
    
    isaac_member = ctx.guild.get_member(ISAAC_ID)
    
    if isaac_member:
        # PROTOCOL: ISAAC (LOUD PING)
        status, vulnerability, color = "UNSTABLE", 100, 0xff0000
        threat_label, threat_display = "🚨 PRIMARY THREAT DETECTED", isaac_member.mention
        content_msg = f"`[SYSTEM SCAN INITIATED...]` - ⚠️ TARGET: {isaac_member.mention}"
        ping_user = True
    else:
        # PROTOCOL: ANOMALY (SILENT PING)
        status = random.choice(["VULNERABLE", "BREACHED", "COMPROMISED"])
        vulnerability = random.randint(60, 99)
        threat_label = "🚨 INTERNAL ANOMALY DETECTED"
        potential_targets = [m for m in ctx.guild.members if not m.bot]
        target = random.choice(potential_targets) if potential_targets else ctx.author
        threat_display, color = target.mention, 0xffa500
        content_msg = "`[SYSTEM SCAN INITIATED...]`"
        ping_user = False # Silent reply

    embed = discord.Embed(title="🛰️ GHOSTNET NETWORK DIAGNOSTIC", color=color)
    embed.description = "```📡 Scanning Server Nodes... [Complete]```"
    embed.add_field(name="🔒 STATUS", value=f"`{status}`", inline=True)
    embed.add_field(name="⚠️ VULNERABILITY", value=f"`{vulnerability}%`", inline=True)
    embed.add_field(name=threat_label, value=threat_display, inline=False)
    
    await ctx.reply(content=content_msg, embed=embed, mention_author=ping_user)

@bot.command(name="terminal-clear")
@commands.has_permissions(manage_messages=True)
async def terminal_clear(ctx, amount: int = 5):
    if is_treated_as_isaac(ctx): return
    author_mention = ctx.author.mention
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 {author_mention} `Mainframe purged: {len(deleted)} packets.`")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    if member is None: return await ctx.reply("❌ Specify a target.")
    msg = await ctx.reply(f"💻 `Initializing breach on {member.name}...`")
    await asyncio.sleep(2)
    await msg.edit(content=f"✅ **HACK COMPLETE.** Target indexed.")

@bot.command()
async def ping(ctx):
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
async def on_ready():
    print(f"✅ GHOSTNET Online: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
