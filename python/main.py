import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from decouple import config
import yt_dlp
import random
from flask import Flask
from threading import Thread

botToken = config('YOUSEPPA_TOKEN')

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
    """ try:
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
        await channel.send(f"tevacae {member.name}")

@client.event
async def on_member_ban(member):
    channel = client.get_channel(int(config('BIENVENIDO_ID')))
    if channel:
        await channel.send(f"sacaio {member.name}")

# Funciones de reproducción------------------------------------------------------------------------
ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ytdl = yt_dlp.YoutubeDL(ytdl_opts)

# 🔹 Clase para manejar la reproducción con yt-dlp
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
            raise commands.CommandError(f"Error descargando video: {e}")
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(FFmpegPCMAudio(filename), data=data)

# 🔹 Función para reproducir la siguiente canción en la cola
async def play_next(guild):
    global isPlaying

    voice_client = guild.voice_client
    if not voice_client:
        return

    if len(queue) == 0:
        isPlaying = False
        await asyncio.sleep(idle_time)
        if not isPlaying and voice_client.is_connected():
            await voice_client.disconnect()
        return

    isPlaying = True
    url = queue.pop(0)
    player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
    
    def after_play(error):
        asyncio.run_coroutine_threadsafe(play_next(guild), client.loop)

    voice_client.play(player, after=after_play)
    await guild.system_channel.send(f'Reproduciendo ahora: {player.data["title"]}')


# Comandos de texto--------------------------------------------------------------------------
@client.tree.command(name="haiii", description="Dise haiii :3")
async def haiii(interaction: discord.Interaction):
    await interaction.response.send_message("haiii :3")

@client.tree.command(name="byeee", description="Dise byeee :3")
async def byeee(interaction: discord.Interaction):
    await interaction.response.send_message("byeee :3")

# Comandos de voz----------------------------------------------------------------------------
@client.tree.command(name="play", description="Reproduce una canción. Si ya hay una en curso, la añade como la siguiente en la cola.")
async def play(interaction: discord.Interaction, url: str):
    global isPlaying
    
    await interaction.response.defer()  # Evita que la interacción expire
    
    if not interaction.user.voice:
        await interaction.followup.send("Debes estar en un canal de voz para usar este comando.")
        return
    
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        voice_client = await interaction.user.voice.channel.connect()
    
    if isPlaying:
        queue.insert(0, url)  # Inserta la nueva canción justo después de la actual
        await interaction.followup.send("Saltando la cancion actual. Reproduciendo " + url)
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
        
    else:
        queue.insert(0, url)  # Si no hay nada, agrégala normal
        await play_next(interaction.guild)  # Inicia la reproducción
        await interaction.followup.send("Reproduciendo " + url)
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

client.run(botToken)
