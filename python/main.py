import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from decouple import config
import yt_dlp as youtube_dl
import random



botToken = config('YOUSEPPE_TOKEN')
print(botToken)

# Define the bot with all intents
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

isPlaying = False

# Cola de reproducción (ahora con tuplas para almacenar url y título)
queue = []

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

# Funcinones asincronas----------------------------------------------------------------------------------
async def play_next(ctx):
    global isPlaying
    
    if len(queue) == 0:
        isPlaying = False  # No hay más canciones en la cola
        return

    
    next_song_url = queue.pop(0)  # Obtiene y elimina la primera canción de la cola
    await play_song(ctx, next_song_url)  

async def play_song(ctx, url):
    global isPlaying
    
    
    try:
        
        ytdl = youtube_dl.YoutubeDL({'format': 'bestaudio/best'})
        info = ytdl.extract_info(url, download=False)
        title = info['title']  
        duration = info['duration']

        
        player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
        ctx.voice_client.play(player)
        
        isPlaying = True
        await ctx.send(f'Reproduciendo ahora: {title}, {url}')

        await asyncio.sleep(duration + 1)  # Espera la duración de la canción + 1 segundo
        isPlaying = False

        await play_next(ctx)  # Llama a play_next después de que la canción termine

    except commands.CommandError as e:
        await ctx.send(f"An error occurred: {e}")
    except Exception as e:
        await ctx.send(f"Unexpected error: {e}")
    
        
# Eventos-----------------------------------------------------------------------------------------
@client.event
async def on_ready():
    print("Youseppe está despierto ;3")
    print("---------------------------")
    await client.tree.sync()
    
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
        
# Comandos de texto--------------------------------------------------------------------------

@client.command()
async def haiii(ctx):
    await ctx.send("haiii :3")

@client.command()
async def byeee(ctx):
    await ctx.send("byeee :3")

# Comandos de voz----------------------------------------------------------------------------
    

@client.command()
async def play(ctx: commands.Context, url: str):
    global isPlaying

    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("No estás en ningún canal de voz. No puedo reproducir nada sin ti :(")
            return

    ytdl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': False,  # Permitir listas de reproducción
        'quiet': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }

    ytdl = youtube_dl.YoutubeDL(ytdl_opts)

    try:
        info = ytdl.extract_info(url, download=False)
        
        if 'entries' in info:  # Si es una lista de reproducción
            playlist = info['entries']
            await ctx.send(f'Lista de reproducción agregada con {len(playlist)} canciones.')

            for entry in playlist:
                video_url = entry['url']
                queue.append(video_url)  # Agregar la URL del video a la cola
                await ctx.send(f'Se agregó a la cola: {entry["title"]}')  # Muestra el título de cada video agregado
        else:
            queue.append(url)  # Agregar una sola canción si no es lista
            await ctx.send(f'Se ha agregado a la cola: {info["title"]}')
        
        if not isPlaying:
            await play_next(ctx)  # Comienza a reproducir la primera canción si no hay otra en curso

    except Exception as e:
        await ctx.send(f"Error al procesar la lista de reproducción o URL: {e}")

   
@client.command()
async def add(ctx: commands.Context, url: str):
    queue.append(url)  # Agrega la URL a la cola
    await ctx.send(f'Se ha agregado a la cola: {url}')
    
@client.command()
async def stop(ctx: commands.Context):
    global isPlaying  # Asegúrate de que sea la variable global
    if ctx.voice_client:
        queue.clear()  # Vacía la cola cuando se detiene la reproducción
        await ctx.voice_client.disconnect()
        isPlaying = False  # Cambia a False al detener la música
    else:
        await ctx.send("No estoy en ningun canal de voz. ¿Es que no me quieres aqui? :(")

@client.command()
async def skip(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()  # Detiene la canción actual
        await ctx.send("Canción saltada. Reproduciendo la siguiente en la cola...")
        await play_next(ctx)
    else:
        await ctx.send("No hay ninguna canción reproduciéndose en este momento.")

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

#Comandos grasiosos----------------------------------------------------------------------------------


@client.command()
async def caracu(ctx: commands.Context, member: discord.Member):
    # Obtén el canal de voz usando el ID
    channel = client.get_channel(int(config('CARACU_ID')))
    
    if channel is None or not isinstance(channel, discord.VoiceChannel):
        await ctx.send(f'El canal de voz con ID "{channel}" no existe o no es un canal de voz.')
        return

    if not member.voice:
        await ctx.send(f'{member.name} no está en ningún canal de voz.')
        return

    original_channel = member.voice.channel  # Guardar el canal original del miembro

    # Mueve al miembro al canal de voz especificado
    await member.move_to(channel)
    await ctx.send(f'Merecido caracu {member.name}')

    # Leer el archivo de GIFs y seleccionar uno al azar
    try:
        with open("./.txt/gifs.txt", "r") as file:
            gifs = file.readlines()
        if gifs:
            gif_url = random.choice(gifs).strip()  # Selecciona un GIF aleatorio y elimina espacios en blanco
            await ctx.send(gif_url)  # Envía el enlace del GIF seleccionado
        else:
            await ctx.send("No se encontraron GIFs en el archivo.")
    except FileNotFoundError:
        await ctx.send("El archivo de GIFs no fue encontrado.")
    except Exception as e:
        await ctx.send(f"Ocurrió un error: {e}")

    # Espera 5 segundos antes de devolver al miembro al canal original
    await asyncio.sleep(5)

    if original_channel is not None:  # Asegúrate de que el canal original sigue siendo válido
        await member.move_to(original_channel)  # Devuelve al miembro a su canal de voz original
        await ctx.send(f'{member.name} ha sido devuelto a su canal original.')


client.run(botToken)
