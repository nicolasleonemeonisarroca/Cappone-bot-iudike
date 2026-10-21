import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime, timedelta

# Configurazione Intent e Prefisso
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

# File JSON per salvare permanentemente i warn degli utenti
WARN_FILE = 'warns.json'

def load_warns():
    if os.path.exists(WARN_FILE):
        with open(WARN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_warns(warns_data):
    with open(WARN_FILE, 'w', encoding='utf-8') as f:
        json.dump(warns_data, f, indent=4, ensure_ascii=False)

@bot.event
async def on_ready():
    print(f'Logged in successfully as: {bot.user.name}')

# ---------------------------------------------------------
# COMANDO: .mute @user <tempo> (es. .mute @nero 5h oppure 30m)
# ---------------------------------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def mute(ctx, member: discord.Member, time_str: str):
    unit = time_str[-1].lower()
    try:
        duration = int(time_str[:-1])
    except ValueError:
        await ctx.send("Formato tempo non valido. Usa ad esempio: `5h` per 5 ore o `30m` per 30 minuti.")
        return

    if unit == 'h':
        delta = timedelta(hours=duration)
    elif unit == 'm':
        delta = timedelta(minutes=duration)
    elif unit == 'd':
        delta = timedelta(days=duration)
    else:
        await ctx.send("Unità di tempo non valida. Usa `m` (minuti), `h` (ore), o `d` (giorni).")
        return

    try:
        await member.timeout(delta, reason=f"Muted da {ctx.author.name}")
        await ctx.send(f"Successfully muted {member.mention} for {time_str}.")
    except Exception as e:
        await ctx.send(f"Impossibile isolare l'utente: {e}")

# ---------------------------------------------------------
# COMANDO: .ban @user [motivo]
# ---------------------------------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, *, reason: str = "Nessun motivo specificato"):
    try:
        await member.ban(reason=f"{reason} (Eseguito da {ctx.author.name})")
        await ctx.send(f"Successfully banned {member.mention}.")
    except Exception as e:
        await ctx.send(f"Impossibile bannare l'utente: {e}")

# ---------------------------------------------------------
# COMANDO: .c (Cancella i messaggi inviati dal bot negli ultimi 5 minuti)
# ---------------------------------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def c(ctx):
    # Cancella prima il comando .c inviato dall'admin
    try:
        await ctx.message.delete()
    except Exception:
        pass

    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

    def check_bot_message(m):
        return m.author == bot.user and m.created_at >= five_minutes_ago

    deleted = await ctx.channel.purge(limit=100, check=check_bot_message)
    
    # Notifica temporanea di conferma
    confirm = await ctx.send(f"Cancellati {len(deleted)} messaggi inviati da me negli ultimi 5 minuti.")
    await asyncio.sleep(3)
    try:
        await confirm.delete()
    except Exception:
        pass

# ---------------------------------------------------------
# COMANDO: .warn @user <motivo personalizzato>
# ---------------------------------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason: str):
    warns = load_warns()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    if guild_id not in warns:
        warns[guild_id] = {}
    if user_id not in warns[guild_id]:
        warns[guild_id][user_id] = []

    warn_entry = {
        "reason": reason,
        "moderator": str(ctx.author),
        "date": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    warns[guild_id][user_id].append(warn_entry)
    save_warns(warns)

    await ctx.send(f"Successfully warned {member.mention}.")

# ---------------------------------------------------------
# COMANDO: .modlogs @user (Visualizza la cronologia dei warn)
# ---------------------------------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def modlogs(ctx, member: discord.Member):
    warns = load_warns()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    user_warns = warns.get(guild_id, {}).get(user_id, [])

    if not user_warns:
        await ctx.send(f"Nessun avvertimento presente per {member.mention}.")
        return

    embed = discord.Embed(
        title=f"Modlogs per {member.display_name}",
        color=discord.Color.dark_red()
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    for idx, w in enumerate(user_warns, 1):
        embed.add_field(
            name=f"Warn #{idx} - {w['date']}",
            value=f"**Motivo:** {w['reason']}\n**Moderatore:** {w['moderator']}",
            inline=False
        )

    await ctx.send(embed=embed)

# Gestione errore permessi mancanti
@mute.error
@ban.error
@c.error
@warn.error
@modlogs.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Non hai i permessi da Amministratore per usare questo comando.")

# Inserisci qui la chiave/token del bot
bot.run('MTU2MjQwOTUyMzY3Nzc1NzUyMA.GwOxZU.523tLTK8EZvrwptM')
