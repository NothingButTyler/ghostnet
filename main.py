import discord
from discord.ext import commands
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
                        value="`!hack @user`\n`!test-prank [user]`\n`!system-logs @user`\n`!prank-start` / `!stop`", inline=False)
        embed.add_field(name="🛠️ UTILITY", 
                        value="`!terminal-clear [amount]`\n`!scan-network`\n`!ping`", inline=False)
        await ctx.reply(content="🛡️ **Terminal Access Granted.**", embed=embed)
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user`\n`!ping`", inline=False)
        await ctx.reply(embed=embed)

@bot.command(name="system-logs")
async def system_logs(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    target = member if member else (ctx.guild.get_member(ISAAC_ID) or ctx.author)
    
    # Pool of fake "hacker" events
    log_templates = [
        "Intercepted packet from {user}: 'Search: how to bypass bot'",
        "Target {user} attempted unauthorized access to #staff-chat",
        "Keystroke log captured from {user}: [REDACTED PASSWORD]",
        "Target {user} detected downloading 'unlimited_nitro_free.exe'",
        "Metadata leak: {user} is currently using a 'Windows XP' simulator",
        "Connection from {user} flagged for 'Excessive Skill Issue'",
        "Encrypted DM intercepted from {user}: 'Is the bot watching me?'",
        "{user} attempted to bypass firewall using "admin123".",
        "{User} searched for "how to talk to girls" in #general.",
        "Intercepting private packet: "I love this bot" - Sent by {user}.",
        "Unauthorized handshake detected from {user} via Port 8080.",
        "Local files of {user} accessed: found folder 'Top Secret (Not a virus)'.",
        
    ]
    
    selected_logs = random.sample(log_templates, 3)
    formatted_logs = "\n".join([f"[{random.randint(10,23)}:{random.randint(10,59)}] {log.format(user=target.name)}" for log in selected_logs])
    
    embed = discord.Embed(title=f"📜 SYSTEM LOGS: {target.name}", color=0x5865f2)
    embed.description = f"```ini\n[LOG START]\n{formatted_logs}\n[LOG END]```"
    embed.set_footer(text="GHOSTNET Surveillance Protocol v4.0")
    
    await ctx.reply(embed=embed)

@bot.command(name="test-prank")
@commands.has_permissions(administrator=True)
async def test_prank(ctx, member: discord.Member = None):
    target = member if member else ctx.author
    if target.id in fake_isaacs:
        fake_isaacs.remove(target.id)
        await ctx.reply(f"🔓 **RECOVERY:** `{target.name}` cleared.")
    else:
        fake_isaacs.append(target.id)
        await ctx.reply(f"☣️ **INFECTED:** `{target.name}` flagged.")

@bot.command(name="scan-network")
async def scan_network(ctx):
    if is_treated_as_isaac(ctx): return
    isaac_member = ctx.guild.get_member(ISAAC_ID)
    active_test_targets = [m for m in ctx.guild.members if m.id in fake_isaacs]
    all_threats = ([isaac_member] if isaac_member else []) + active_test_targets

    if all_threats:
        status, vulnerability, color = "UNSTABLE", 100, 0xff0000
        threat_label = f"🚨 THREATS DETECTED ({len(all_threats)})"
        threat_display = ", ".join([m.mention for m in all_threats])
        content_msg = f"`[SYSTEM SCAN INITIATED...]` - ⚠️ ALERT: {threat_display}"
        ping_user = True
    else:
        status, vulnerability, color = "STABLE", random.randint(5, 40), 0x00ff00
        threat_label, threat_display = "🚨 ANOMALY", "NONE"
        content_msg, ping_user = "`[SYSTEM SCAN INITIATED...]`", False

    embed = discord.Embed(title="🛰️ GHOSTNET DIAGNOSTIC", color=color)
    embed.add_field(name="🔒 STATUS", value=f"`{status}`", inline=True)
    embed.add_field(name="⚠️ VULNERABILITY", value=f"`{vulnerability}%`", inline=True)
    embed.add_field(name=threat_label, value=threat_display, inline=False)
    await ctx.reply(content=content_msg, embed=embed, mention_author=ping_user)

@bot.command(name="terminal-clear")
@commands.has_permissions(manage_messages=True)
async def terminal_clear(ctx, amount: int = 5):
    if is_treated_as_isaac(ctx): return
    mention = ctx.author.mention
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 {mention} `Purged: {len(deleted)} packets.`")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command()
async def ping(ctx):
    if is_treated_as_isaac(ctx): return await ctx.reply("`ERR_TIMEOUT`")
    await ctx.reply(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

# --- 5. EVENTS ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
