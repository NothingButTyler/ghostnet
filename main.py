import discord
from discord import app_commands
from discord.ext import commands
import os, asyncio, uuid, time
from flask import Flask, jsonify, request
from threading import Thread

# --- 1. SHARED SECURITY DATA ---
# In a production app, you'd use a database like SQLite or MongoDB.
security_logs = []
blacklist = set()

# --- 2. WEB SERVER (Security API Routes) ---
app = Flask('')

@app.route('/api/security/logs', methods=['GET'])
def get_logs():
    # JavaScript fetch() will hit this to get the audit log
    return jsonify(security_logs[-50:]) # Return last 50 events

@app.route('/api/security/blacklist', methods=['GET', 'POST'])
def manage_blacklist():
    if request.method == 'POST':
        user_id = request.json.get('user_id')
        blacklist.add(int(user_id))
        return jsonify({"status": "success", "added": user_id})
    return jsonify(list(blacklist))

@app.route('/')
def home(): return "GHOSTNET DASHBOARD API: ONLINE"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# --- 3. BOT CORE ---
class GhostNet(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.SESSION_ID = str(uuid.uuid4())[:8]

    async def setup_hook(self):
        await self.tree.sync()

bot = GhostNet()

def log_event(event_type, details):
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "details": details
    }
    security_logs.append(entry)

# --- 4. SLASH COMMANDS ---

@bot.tree.command(name="security-logs", description="View recent security audit events")
@app_commands.checks.has_permissions(administrator=True)
async def security_logs_cmd(interaction: discord.Interaction):
    if not security_logs:
        return await interaction.response.send_message("📭 No logs recorded yet.")
    
    recent = security_logs[-5:]
    log_text = "\n".join([f"[{l['timestamp']}] **{l['event']}**: {l['details']}" for l in recent])
    
    embed = discord.Embed(title="🛡️ Security Audit Log", description=log_text, color=0xff0000)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="blacklist-add", description="Add a user to the security blacklist")
@app_commands.checks.has_permissions(administrator=True)
async def blacklist_add(interaction: discord.Interaction, user: discord.Member):
    blacklist.add(user.id)
    log_event("BLACKLIST_ADD", f"User {user.name} added by {interaction.user.name}")
    await interaction.response.send_message(f"🚫 {user.mention} has been blacklisted from terminal access.")

# --- 5. AUTOMATED AUDIT EVENTS ---

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log_event("MSG_DELETE", f"Message by {message.author} deleted in #{message.channel}")

@bot.event
async def on_member_ban(guild, user):
    log_event("MEMBER_BAN", f"User {user.name} was banned from the server.")

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
