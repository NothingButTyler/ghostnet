import discord
from discord.ext import commands
from discord import ui
import os
import asyncio
from flask import Flask
from threading import Thread

bot.remove_command('help')

# --- 1. WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "GHOSTNET: ONLINE"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

welcome_settings = {
    "message": "Welcome {User_Mention} to {Server_Name}!",
    "channel_id": None
}

# --- 3. HELPER FUNCTIONS ---
def get_ordinal(n):
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}**{suffix.upper()}**"

# --- 4. UI CLASSES ---
class WelcomeModal(ui.Modal, title='Step 2: Set Welcome Message'):
    welcome_msg = ui.TextInput(
        label='Enter message',
        style=discord.TextStyle.paragraph,
        placeholder='Tags: {User_Mention}, {Server_Name}, {Member_Count_Ordinal}',
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        welcome_settings["message"] = self.welcome_msg.value
        await interaction.response.send_message(f"✅ Message saved! Click 'Next Step' in the setup menu.", ephemeral=True)

class WelcomeSetupView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.step = 1

    @ui.button(label="Next Step ➡️", style=discord.ButtonStyle.primary)
    async def next_step(self, interaction: discord.Interaction, button: ui.Button):
        if self.step == 1:
            self.step = 2
            await interaction.response.edit_message(content="🛰️ **STEP 2: THE MESSAGE**\nClick 'Set Message' to type your greeting.", view=self)
            # Add the Modal button
            modal_btn = ui.Button(label="Set Message", style=discord.ButtonStyle.secondary)
            async def m_callback(itn): await itn.response.send_modal(WelcomeModal())
            modal_btn.callback = m_callback
            self.add_item(modal_btn)

        elif self.step == 2:
            self.step = 3
            await interaction.response.edit_message(content="🛰️ **STEP 3: THE CHANNEL**\nSelect the broadcast channel below.", view=self)
            select = ui.ChannelSelect(placeholder="Pick a channel...")
            async def s_callback(itn):
                welcome_settings["channel_id"] = select.values[0].id
                await itn.response.send_message(f"✅ Channel set to {select.values[0].mention}", ephemeral=True)
            select.callback = s_callback
            self.add_item(select)

        elif self.step == 3:
            self.step = 4
            button.label = "💾 SAVE & FINALIZE"
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(content="🛰️ **FINAL STEP: CONFIRMATION**\nReady to hard-code these settings?", view=self)

        elif self.step == 4:
            await interaction.response.edit_message(content="✅ **SUCCESS!**\nSettings saved. Use `!welcome-edit` to modify or `!welcome-test` to test.\n\n*Closing terminal in 5 seconds...*", view=None)
            await asyncio.sleep(5)
            await interaction.delete_original_response()

# --- 5. COMMANDS & EVENTS ---

@bot.command(name="welcome-setup")
async def welcome_setup(ctx):
    if welcome_settings["channel_id"] is not None:
        await ctx.send("You already made a welcome message, silly! To edit or delete the welcome message, use `!welcome-edit`!")
        return
    await ctx.send("🛠️ **GhostNet Configuration Mainframe**\nClick 'Next Step' to begin.", view=WelcomeSetupView())

@bot.command(name="welcome-test")
async def welcome_test(ctx):
    channel_id = welcome_settings.get("channel_id")
    if not channel_id:
        await ctx.send("❌ **ERROR:** Use `!welcome-setup` first.", delete_after=5)
        return

    channel = bot.get_channel(channel_id)
    if channel:
        count = ctx.guild.member_count
        final_msg = welcome_settings["message"].replace("{User_Mention}", ctx.author.mention).replace("{Server_Name}", ctx.guild.name).replace("{Member_Count_Ordinal}", get_ordinal(count))
        await channel.send(f"⚠️ **SYSTEM TEST - GHOSTNET SIMULATION** ⚠️\n{final_msg}")
        await ctx.send("Message sent successfully! ✅", delete_after=5)

@bot.command(name="welcome-edit")
    async def delete_callback(interaction: discord.Interaction):
        # Create a new sub-view for the confirmation buttons
        confirm_view = ui.View()
        
        # --- THE YES BUTTON ---
        yes_btn = ui.Button(label="Confirm Wipe", style=discord.ButtonStyle.danger)
        async def yes_callback(itn: discord.Interaction):
            welcome_settings["message"] = "Welcome {User_Mention} to {Server_Name}!"
            welcome_settings["channel_id"] = None
            await itn.response.edit_message(
                content="🧨 **SYSTEM PURGE COMPLETE.** Files erased.", 
                view=None
            )
            await asyncio.sleep(5)
            await itn.delete_original_response()
        
        # --- THE NO BUTTON ---
        no_btn = ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def no_callback(itn: discord.Interaction):
            await itn.response.edit_message(
                content="🛰️ **PURGE ABORTED.** System stable.", 
                view=None
            )
        
        yes_btn.callback = yes_callback
        no_btn.callback = no_callback
        confirm_view.add_item(yes_btn)
        confirm_view.add_item(no_btn)

        # Edit the message to show the safety prompt
        await interaction.response.edit_message(
            content="⚠️ **WARNING: DATA PURGE DETECTED** ⚠️\n"
                    "Are you sure you want to erase all welcome configurations?",
            view=confirm_view
        )



@bot.event
async def on_member_join(member):
    channel_id = welcome_settings.get("channel_id")
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            count = member.guild.member_count
            final_msg = welcome_settings["message"].replace("{User_Mention}", member.mention).replace("{Server_Name}", member.guild.name).replace("{Member_Count_Ordinal}", get_ordinal(count))
            await channel.send(f"🛰️ **NEW INITIATE DETECTED**\n{final_msg}")

@bot.command()
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("```diff\n+ [SYSTEM]: Slash commands synced.```")

# The new !help command

@bot.command(name="help")
async def custom_help(ctx):
    # Create the fancy embed box
    embed = discord.Embed(
        title="🛰️ GHOSTNET OPERATING SYSTEM: DIRECTORY",
        description="Welcome to the mainframe. Use the commands below to navigate.",
        color=0x2b2d31 # A sleek dark gray/blue color
    )

    # Grouping the commands in the style you liked
    embed.add_field(
        name="🛠️ UTILITY", 
        value="`!help` - sends this message\n"
              "`!sync` - syncs slash commands to mainframe", 
        inline=False
    )

    embed.add_field(
        name="🛰️ WELCOME MODULE", 
        value="`!welcome-setup` - create a welcome message\n"
              "`!welcome-edit` - edit the welcome message\n"
              "`!welcome-test` - test the welcome message", 
        inline=False
    )

    # Adding your Sambucha quote at the bottom
    embed.set_footer(text="\"Pretty cool, right?\" - Sambucha")
    
    await ctx.send(embed=embed)



# --- 6. STARTUP ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
