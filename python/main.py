import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from decouple import config
import yt_dlp as youtube_dl
import random

# Define the bot with all intents
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)
# botToken = config('YOUSEPPE_TOKEN')
botToken = "MTI4NzgzMDc1MTE3MzE0ODY4Ng.GIl8ay.LDo8ZL6lG1TuNw5A9juItWfcL5IP-sxW_SWPK0"

# Cola de reproducción
queue = []  # Lista vacía para la cola de canciones

# Configuration for yt_dlp
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume=volume)
        self.data = data

    @classmethod
    async def from_url(cls, url: str, *, loop=None, stream=False):
        ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'nocheckcertificate': True,
            'quiet': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }

        ytdl = youtube_dl.YoutubeDL(ytdl_opts)
        loop = loop or asyncio.get_event_loop()
        
        ffmpeg_opts = {
            'before_options': (
                '-reconnect 1 -reconnect_streamed 1 '
                '-reconnect_delay_max 5'
            ),
            'options': '-vn'
        }

        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except youtube_dl.DownloadError as e:
            raise commands.CommandError(f"Error downloading video: {e}")
        except Exception as e:
            raise commands.CommandError(f"Unexpected error: {e}")

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)

        return cls(FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

# Manejar el fin de una canción y pasar a la siguiente en la cola
def play_next(ctx):
    if len(queue) > 0:
        next_song = queue.pop(0)  # Toma la siguiente canción de la cola
        client.loop.create_task(play_song(ctx, next_song))

async def play_song(ctx, song):
    try:
        player = await YTDLSource.from_url(song, loop=client.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: play_next(ctx))
        await ctx.send(f'Reproduciendo ahora: {player.data["title"]}')
    except commands.CommandError as e:
        await ctx.send(f"An error occurred: {e}")
    except Exception as e:
        await ctx.send(f"Unexpected error: {e}")

# Eventos
@client.event
async def on_ready():
    print("Youseppe está despierto ;3")
    print("---------------------------")
    await client.tree.sync()

# Comando para reproducir una canción y agregarla a la cola si ya hay una en curso
@client.command()
async def play(ctx: commands.Context, url: str):
    if ctx.voice_client and ctx.voice_client.is_playing():
        queue.append(url)  # Agrega la canción a la cola
        await ctx.send(f'Se ha agregado a la cola: {url}')
    else:
        await play_song(ctx, url)

@client.command()
async def stop(ctx: commands.Context):
    if ctx.voice_client:
        queue.clear()  # Vacía la cola cuando se detiene la reproducción
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("No estoy en ningun canal de voz. ¿Es que no me quieres aqui? :(")

@client.command()
async def pause(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Música pausada")
    else:
        await ctx.send("ZA WARUDO. Ups, solo funciona cuando reproduzco algo :(")

@client.command()
async def resume(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumiendo música")
    else:
        await ctx.send("TOKI WA UGOKIDASU. Upsie, primero tengo que parar algo, ¿no crees :p?")

@play.before_invoke
async def ensure_voice(ctx: commands.Context):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("No estás en ningún canal de voz. No querrás que reproduzca algo sin tí, ¿no? :(")
            raise commands.CommandError("El usuario no está conectado en ningún canal de voz")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()

# Nuevo comando para ver la cola de canciones
@client.command()
async def queue_list(ctx: commands.Context):
    if len(queue) == 0:
        await ctx.send("No hay canciones en la cola.")
    else:
        queue_display = "\n".join([f"{i + 1}. {url}" for i, url in enumerate(queue)])
        await ctx.send(f"Cola de canciones:\n{queue_display}")

# Nuevo comando para saltar la canción actual
@client.command()
async def skip(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()  # Detiene la canción actual y desencadena `play_next`
        await ctx.send("Canción saltada. Reproduciendo la siguiente en la cola...")
    else:
        await ctx.send("No hay ninguna canción reproduciéndose en este momento.")

client.run(botToken)
