import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio, app_commands
from decouple import config
import yt_dlp
from typing import Optional
import log_manager
from ytdl_source import YTDLSource,ytdl

botToken = config('YOUSEPPE_TOKEN')

# Define el bot con todos los intents
class MiBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()  # Sincroniza los comandos con Discord
        print("Comandos internos sincronizados :3")

intents = discord.Intents.all()
client = MiBot(command_prefix='?', intents=intents)

isPlaying = False
queue = []
idle_time = 300  # Tiempo en segundos para desconectar si está inactivo

# Eventos-----------------------------------------------------------------------------------------
@client.event
async def on_ready():
    update_commands = config('UPDATE_COMMANDS', default=False, cast=bool)
    print(f"UPDATE_COMMANDS: {update_commands}")
    if update_commands:
        try:
            await client.tree.sync()
            print("Comandos slash sincronizados en el servidor.")
            for command in client.tree.get_commands():
                print(f"Comando registrado: {command.name}")
        except Exception as e:
            print(" Error al sincronizar comandos: {e}")
        
    print("Youseppe está despierto ;3")
    print("---------------------------")

@client.event
async def on_member_join(member):
    channel = client.get_channel(int(config('BIENVENIDO_ID')))
    if channel:
        await channel.send(f"De donde habeis sacao a {member.name}?")

@client.event
async def on_member_ban(member):
    channel = client.get_channel(int(config('BIENVENIDO_ID')))
    if channel:
        await channel.send(f"baneo por perra pa {member.name}")

@client.event
async def on_member_remove(member):
    channel = client.get_channel(int(config('BIENVENIDO_ID')))
    if channel:
        await channel.send(f"Te va {member.name}? . Po llévate esta ;)")

@client.event
async def on_member_kick(member):
    channel = client.get_channel(int(config('BIENVENIDO_ID')))
    if channel:
        await channel.send(f"{member.name} ha sido expulsado del servidor. Hasta nunca >:D")

# Funciones de reproducción------------------------------------------------------------------------
async def get_playlist_urls(playlist_url):
    ytdl_opts = {
        'extract_flat': True,  # No descarga, solo obtiene información
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
        try:
            info = ytdl.extract_info(playlist_url, download=False)
            if 'entries' in info:
                urls = [entry['url'] for entry in info['entries'] if 'url' in entry]
                return urls
        except Exception as e:
            print(f"Error obteniendo URLs de la playlist: {e}")

    return []

async def play_next(guild, channel):
    global isPlaying
    voice_client = guild.voice_client
    if not voice_client:
        return

    while queue:
        url = queue.pop(0)  # Saca el siguiente video de la cola
        player = await YTDLSource.from_url(url, loop=client.loop, stream=True)

        if player is None:
            print(f"[AVISO] No se pudo reproducir {url}, saltando...")
            continue  # Intenta la siguiente canción

        isPlaying = True

        def after_play(error):
            if error:
                print(f"[ERROR] FFmpeg falló con: {error}. Reintentando reproducción.")
                asyncio.run_coroutine_threadsafe(play_next(guild, channel), client.loop)
            else:
                asyncio.run_coroutine_threadsafe(play_next(guild, channel), client.loop)

        voice_client.play(player, after=after_play)

        if channel:
            await channel.send(f'Reproduciendo ahora: {player.data["title"]}')
        return

    isPlaying = False
    await asyncio.sleep(idle_time)
    if not isPlaying and voice_client.is_connected():
        await voice_client.disconnect()

# Comandos de texto--------------------------------------------------------------------------

@client.tree.command(name="haiii", description="Dice haiii :3")
async def haiii(interaction: discord.Interaction):
    await interaction.response.send_message("haiii :3")

@client.tree.command(name="byeee", description="Dice byeee :3")
async def byeee(interaction: discord.Interaction):
    await interaction.response.send_message("byeee :3")

# Comandos de voz----------------------------------------------------------------------------
@client.tree.command(name="play", description="Reproduce una canción o añade una playlist a la cola.")
async def play(interaction: discord.Interaction, url: str):
    global isPlaying
    await interaction.response.defer()

    if not interaction.user.voice:
        await interaction.followup.send("Debes estar en un canal de voz para usar este comando.")
        return

    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        voice_client = await interaction.user.voice.channel.connect()

    new_songs = []

    try:
        if "playlist" in url:
            new_songs = await get_playlist_urls(url)  # Usa await aquí
            if not new_songs:
                await interaction.followup.send("No se pudieron obtener canciones de la playlist.")
                return
        else:
            new_songs.append(url)

    except Exception as e:
        await interaction.followup.send(f"Error al obtener la playlist: {e}")
        return

    queue.extend(new_songs)
    await interaction.followup.send(f"Se añadieron {len(new_songs)} canciones a la cola.")

    if not isPlaying:
        await play_next(interaction.guild, interaction.channel)



@client.tree.command(name="add", description="Añade una canción a la cola sin interrumpir la actual.")
async def add(interaction: discord.Interaction, url: str):
    queue.append(url)
    await interaction.response.send_message("Canción añadida a la cola.")

@client.tree.command(name="pause", description="Pausa la canción actual.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("Música pausada.")
    else:
        await interaction.response.send_message("No hay ninguna canción en reproducción.")

@client.tree.command(name="resume", description="Reanuda la canción pausada.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("Música reanudada.")
    else:
        await interaction.response.send_message("No hay ninguna canción pausada.")

@client.tree.command(name="skip", description="Salta a la siguiente canción de la cola.")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Canción saltada.")
    else:
        await interaction.response.send_message("No hay ninguna canción en reproducción.")

@client.tree.command(name="stop", description="Detiene la reproducción y desconecta el bot si está inactivo.")
async def stop(interaction: discord.Interaction):
    global isPlaying
    voice_client = interaction.guild.voice_client
    queue.clear()

    if voice_client and voice_client.is_playing():
        voice_client.stop()
    
    if voice_client:
        await voice_client.disconnect()

    isPlaying = False
    await interaction.response.send_message("Reproducción detenida y bot desconectado.")

#Comandos grasiosos_________________________________________________________________________________________________________________________

@client.tree.command(name="caracu", description="Envía hasta 5 usuarios a otro canal de voz unos segundos")
@app_commands.describe(
    user1="Primer usuario",
    user2="Segundo usuario (opcional)",
    user3="Tercer usuario (opcional)",
    user4="Cuarto usuario (opcional)",
    user5="Quinto usuario (opcional)"
)
async def caracu(
    interaction: discord.Interaction,
    user1: discord.Member,
    user2: Optional[discord.Member] = None,
    user3: Optional[discord.Member] = None,
    user4: Optional[discord.Member] = None,
    user5: Optional[discord.Member] = None
):
    await interaction.response.defer()  # Evita que la interacción expire

    # Crear la lista de usuarios sin los None
    members = [user for user in [user1, user2, user3, user4, user5] if user]

    # Comprobar si todos están en un canal de voz
    non_voice_members = [member for member in members if not member.voice]
    if non_voice_members:
        await interaction.followup.send(f'Los siguientes usuarios no están en un canal de voz: {", ".join(member.name for member in non_voice_members)}')
        return

    # Obtener el canal de castigo
    channel = client.get_channel(int(config('CARACU_ID')))
    if channel is None or not isinstance(channel, discord.VoiceChannel):
        await interaction.followup.send(f'El canal de voz con ID "{channel}" no existe o no es un canal de voz.')
        return

    # Guardar los canales originales
    original_channels = {member: member.voice.channel for member in members}

    # Mover a los usuarios al canal de castigo
    for member in members:
        await member.move_to(channel)

    await interaction.followup.send(f'Merecido caracu para {", ".join(member.name for member in members)}.')

    # Esperar 5 segundos antes de devolverlos
    await asyncio.sleep(5)

    # Devolver a los usuarios a su canal original
    for member, original_channel in original_channels.items():
        if original_channel is not None:
            await member.move_to(original_channel)

    await interaction.followup.send(f'{", ".join(member.name for member in members)} han sido devueltos a su canal original.')

@client.tree.command(name="arcane", description="Toda la playlist de Arcane su primo")
async def arcane(interaction: discord.Interaction):
    url_arcane = config('URL_ARCANE')
    command = client.tree.get_command("play") 
    await play.callback(interaction, url_arcane)

@client.tree.command(name="caracu_majemase", description="Envía a Majemase al canal de castigo repetidamente y le envía un mensaje privado.")
async def caracu_majemase(interaction: discord.Interaction):
    if interaction.user.name != "_blahaj_enjoyer_":
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
        return

    # Buscar a Majemase en la guild
    majemase = discord.utils.get(interaction.guild.members, name="majemase")

    if not majemase:
        await interaction.response.send_message("No se encontró a Majemase en el servidor.", ephemeral=True)
        return

    try:
        # Confirmar inicio en el canal de texto
        await interaction.response.send_message("Ejecutando caracu infinito para Majemase...")

        # Enviar mensaje privado inicial
        try:
            await majemase.send("Prepara el culito >:)")
        except discord.Forbidden:
            await interaction.followup.send("No puedo enviarle mensajes privados a Majemase. Asegúrate de que tiene los DMs activados.", ephemeral=True)

        # Obtener el canal de castigo
        caracu_channel = client.get_channel(int(config('CARACU_ID')))
        if caracu_channel is None or not isinstance(caracu_channel, discord.VoiceChannel):
            await interaction.followup.send("El canal de castigo no es válido.", ephemeral=True)
            return

        # Guardar el canal original de Majemase
        original_channel = majemase.voice.channel if majemase.voice else None

        # Bucle infinito
        while True:
            if majemase.voice:
                await majemase.move_to(caracu_channel)  # Enviar al canal de castigo
                await asyncio.sleep(3)  # Espera 3 segundos
                if original_channel:  # Devolverlo al canal original
                    await majemase.move_to(original_channel)

                # Enviar mensaje privado después de cada movimiento
                try:
                    await majemase.send("Miradme, soy MJ y no puedo hablar por chupapitos.")
                except discord.Forbidden:
                    pass  # Ignorar si no puede recibir mensajes

            await asyncio.sleep(3)  # Espera antes de la siguiente iteración

    except Exception as e:
        await interaction.followup.send(f"Error al ejecutar el caracu infinito: {e}", ephemeral=True)

client.run(botToken)
