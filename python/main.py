import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio, app_commands
from decouple import config
import yt_dlp
from typing import Optional
import log_manager

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
    """
    try:
        await client.tree.sync()
        print("Comandos slash sincronizados en el server")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")
    """
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
ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': False,  # Permite extraer listas de reproducción
    'extract_flat': True,  # No descarga, solo obtiene URLs
    'nocheckcertificate': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'geo_bypass': True,  # Evita restricciones de país
    'geo_bypass_country': 'US',  # Usa un país sin bloqueos
    'logtostderr': True,  # Forzar logs en stderr
    'verbose': True,  # Modo detallado
}
ffmpeg_opts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -multiple_requests 1',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_opts)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume=volume)
        self.data = data

    @classmethod
    async def from_url(cls, url: str, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except yt_dlp.utils.DownloadError as e:
            print(f"[ERROR] No se pudo descargar el video: {e}")
            return None  # Devuelve None si hay un error

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(FFmpegPCMAudio(filename), data=data)

async def play_next(guild, channel):
    global isPlaying
    voice_client = guild.voice_client
    if not voice_client:
        return

    while queue:
        url = queue.pop(0)  # Obtiene el siguiente video
        player = await YTDLSource.from_url(url, loop=client.loop, stream=True)

        if player is None:  # Si el video no se pudo descargar, pasa al siguiente
            print(f"[AVISO] Video no disponible. Saltando...")
            continue  # Intenta el siguiente video en la cola
        
        isPlaying = True

        def after_play(error):
            asyncio.run_coroutine_threadsafe(play_next(guild, channel), client.loop)

        voice_client.play(player, after=after_play)

        if channel:
            await channel.send(f'Reproduciendo ahora: {player.data["title"]}')
        return

    # Si la cola está vacía después de intentar todos los videos
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

    try:
        info = ytdl.extract_info(url, download=False)

        if 'entries' in info:
            # Es una playlist, añadimos todas las canciones disponibles
            song_urls = [entry['url'] for entry in info['entries'] if entry and 'url' in entry]
            queue.extend(song_urls)
            await interaction.followup.send(f"Se añadieron {len(song_urls)} canciones a la cola.")
        else:
            # Es una canción individual
            queue.append(info['url'])
            await interaction.followup.send(f"Se añadió **{info['title']}** a la cola.")

    except Exception as e:
        await interaction.followup.send(f"Error al obtener la playlist: {e}")
        return

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



client.run(botToken)
