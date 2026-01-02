@bot.command(name="scan-network")
async def scan_network(ctx):
    if is_treated_as_isaac(ctx): return
    
    # Check if Isaac is in the server
    isaac_member = ctx.guild.get_member(ISAAC_ID)
    
    if isaac_member:
        # --- PROTOCOL: ISAAC DETECTED (LOUD) ---
        status = "UNSTABLE"
        vulnerability = 100
        threat_label = "🚨 PRIMARY THREAT DETECTED"
        threat_display = isaac_member.mention
        color = 0xff0000 # Red
        # Mention him in the content to ensure a loud notification
        content_msg = f"`[SYSTEM SCAN INITIATED...]` - ⚠️ TARGET: {isaac_member.mention}"
        should_ping_author = True
    else:
        # --- PROTOCOL: INTERNAL ANOMALY (SILENT) ---
        status = random.choice(["VULNERABLE", "BREACHED", "COMPROMISED"])
        vulnerability = random.randint(60, 99)
        threat_label = "🚨 INTERNAL ANOMALY DETECTED"
        
        potential_targets = [m for m in ctx.guild.members if not m.bot]
        target = random.choice(potential_targets) if potential_targets else ctx.author
        
        threat_display = target.mention
        color = 0xffa500 # Orange
        # No mention in content = Silent Ping (Embed only)
        content_msg = "`[SYSTEM SCAN INITIATED...]`"
        should_ping_author = False

    embed = discord.Embed(title="🛰️ GHOSTNET NETWORK DIAGNOSTIC", color=color)
    embed.description = "```📡 Scanning Server Nodes... [Complete]```"
    embed.add_field(name="🔒 STATUS", value=f"`{status}`", inline=True)
    embed.add_field(name="⚠️ VULNERABILITY", value=f"`{vulnerability}%`", inline=True)
    embed.add_field(name=threat_label, value=threat_display, inline=False)
    
    # mention_author=False prevents the person who typed the command from being pinged
    await ctx.reply(content=content_msg, embed=embed, mention_author=should_ping_author)
