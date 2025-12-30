import discord
from discord.ext import commands
from discord import ui
import os
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER ---
app = Flask('')
@app.route('/')
def home():
    return "GHOSTNET: ONLINE"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# This is the "Memory" for your welcome settings
welcome_settings = {
    "message": "Welcome {User_Mention} to {Server_Name}!",
    "channel_id": None
}

# --- 3. UI CLASSES ---
class WelcomeModal(ui.Modal, title='Step 2: Set Welcome Message'):
    welcome_msg = ui.TextInput(
        label='Enter your welcome message',
        style=discord.TextStyle.paragraph,
        placeholder='Use {User_Mention} or {Server_Name}',
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        welcome_settings["message"] = self.welcome_msg.value
        await interaction.response.send_message(f"✅ Message saved!", ephemeral=True)

class WelcomeSetupView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="1. Intro", style=discord.ButtonStyle.primary)
    async def intro(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("📡 **GHOSTNET SETUP**\nTags: `{User_Mention}`, `{User}`, `{Server_Name}`", ephemeral=True)

    @ui.button(label="2. Set Message", style=discord.ButtonStyle.secondary)
    async def set_msg(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(WelcomeModal())

    @ui.button(label="3. Select Channel", style=discord.ButtonStyle.success)
    async def set_channel(self, interaction: discord.Interaction, button: ui.Button):
        view = ui.View()
        select = ui.ChannelSelect(placeholder="Pick a welcome channel...")
        async def callback(inter):
            welcome_settings["channel_id"] = select.values[0].id
            await inter.response.send_message(f"✅ Set to {select.values[0].mention}", ephemeral=True)
        select.callback = callback
        view.add_item(select)
        await interaction.response.send_message("Where should I post?", view=view, ephemeral=True)

# --- 4. COMMANDS & EVENTS ---
@bot.command(name="welcome-setup")
async def welcome_setup(ctx):
    await ctx.send("🛠️ **GhostNet Configuration Mainframe**", view=WelcomeSetupView())

def get_ordinal(n):
    # This handles the special cases like 11th, 12th, 13th
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        # This handles 1st, 2nd, 3rd, and everything else (th)
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}**{suffix.upper()}**"

@bot.command(name="welcome-edit")
async def welcome_edit(ctx):
    # Check if they have even started the setup
    if welcome_settings["channel_id"] is None:
        await ctx.send(
            "❌ **ERROR: NO CONFIGURATION FOUND**\n"
            "I can't edit a system that hasn't been initialized.\n"
            "Please use `!welcome-setup` first to start the mainframe."
        )
        return

    # If it exists, show the edit view (we can reuse our SetupView!)
    view = WelcomeSetupView()
    
    # Let's add a "Save" button specifically for the edit command
    save_btn = ui.Button(label="💾 Save & Exit", style=discord.ButtonStyle.success)
    
    async def save_callback(interaction: discord.Interaction):
        await interaction.response.send_message("🛰️ **Mainframe Updated.** All changes have been hard-coded.", ephemeral=True)
        # This stops the buttons from working after saving
        view.stop() 

    save_btn.callback = save_callback
    view.add_item(save_btn)

    await ctx.send("⚙️ **GHOSTNET EDIT MODE**\nModify your welcome parameters below:", view=view)


@bot.event
async def on_member_join(member):
    channel_id = welcome_settings.get("channel_id")
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            raw_msg = welcome_settings["message"]
            count = member.guild.member_count # Gets the total number of members
            
            # 🛰️ PROCESSING TAGS
            final_msg = raw_msg.replace("{User_Mention}", member.mention)
            final_msg = final_msg.replace("{User}", member.name)
            final_msg = final_msg.replace("{Server_Name}", member.guild.name)
            
            # --- NEW TAGS ---
            final_msg = final_msg.replace("{Server_Members}", str(count))
            final_msg = final_msg.replace("{Member_Count_Ordinal}", get_ordinal(count))
            # My choice: A "Account Age" tag to see how new the user's account is!
            account_age = (discord.utils.utcnow() - member.created_at).days
            final_msg = final_msg.replace("{Account_Age}", f"{account_age} days")

            await channel.send(f"🛰️ **NEW INITIATE**\n{final_msg}")


@bot.command()
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("```diff\n+ [SYSTEM]: Slash commands synced to mainframe.```")

# --- 5. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("TOKEN NOT FOUND")
