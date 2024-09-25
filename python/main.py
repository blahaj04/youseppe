import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from decouple import config
import yt_dlp as youtube_dl

# Define the bot with all intents
intents = discord.Intents.all()
client = commands.Bot(command_prefix='/', intents=intents)
botToken = config('YOUSEPPE_TOKEN')
chanelId = config('CARACU_ID')

# Configuration for yt_dlp
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume=volume)
        self.data = data

    @classmethod
    async def from_url(cls, url: str, *, loop=None, stream=False):
        ytdl = youtube_dl.YoutubeDL({'format': 'bestaudio/best'})
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except youtube_dl.DownloadError as e:
            raise commands.CommandError(f"Error downloading video: {e}")
        except Exception as e:
            raise commands.CommandError(f"Unexpected error: {e}")

        if 'entries' in data:
            data = data['entries'][0]

        return cls(FFmpegPCMAudio(data['url']), data=data)

#Eventos
@client.event
async def on_ready():
    print("Youseppe está despierto ;3")
    print("---------------------------")
    await client.tree.sync()

@client.event
async def on_member_join(member):
    channel = client.get_channel(1265659906996961321)
    if channel:
        await channel.send(f"tevacae {member.name}")

@client.event
async def on_member_ban(member):
    channel = client.get_channel(1265659906996961321)
    if channel:
        await channel.send(f"sacaio {member.name}")
        
#Comandos de texto

@client.command()
async def haiii(ctx):
    await ctx.send("haiii :3")

@client.command()
async def byeee(ctx):
    await ctx.send("byeee :3")

#Comandos de voz

@client.command()
async def play(ctx: commands.Context, url: str):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await ctx.send(f'Reproduciendo ahora: {player.data["title"]}')
        except commands.CommandError as e:
            await ctx.send(f"An error occurred: {e}")
        except Exception as e:
            await ctx.send(f"Unexpected error: {e}")

@client.command()
async def stop(ctx: commands.Context):
    if ctx.voice_client:
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


@client.command()
async def caracu(ctx, member: discord.Member):
    # Obtén el canal de voz usando el ID
    channel = client.get_channel(chanelId)

    if channel is None or not isinstance(channel, discord.VoiceChannel):
        await ctx.send(f'El canal de voz con ID "{channel}" no existe o no es un canal de voz.')
        return

    if not member.voice:
        await ctx.send(f'{member.name} no está en ningún canal de voz.')
        return

    # Mueve al miembro al canal de voz especificado
    await member.move_to(channel)
    await ctx.send(f'{member.name} ha sido movido al canal de voz {channel.name}')

    # Envía un GIF al canal de texto desde donde se llamó el comando
    gif_url = "https://images-ext-1.discordapp.net/external/g5_hePq6C1KzP6TQADBc6arIlQ_zmxYY8zIw8PD1rcc/https/media.tenor.com/y5iSFIAct-EAAAPo/my-honest-reaction-my-reaction.mp4"  # Aquí puedes poner cualquier URL de un GIF
    await ctx.send(f"{member.name} ha sido movido.", file=discord.File(gif_url))
    
client.run(botToken)
