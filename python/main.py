import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from decouple import config
import youtube_dl

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)
botToken = config('YOUSEPPE_TOKEN')

# Configuración de youtube_dl
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '10.28.1.14'  # Bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# ACCIONES AUTOMÁTICAS
@client.event
async def on_ready():
    print("Youseppe está despierto ;3")
    print("---------------------------")
    await client.tree.sync()

@client.event
async def on_member_join(member):
    channel = client.get_channel(1265659906996961321)
    await channel.send(f"tevacae {member.name}")

@client.event
async def on_member_leave(member):
    channel = client.get_channel(1265659906996961321)
    await channel.send(f"sacaio {member.name}")

# COMANDOS DE TEXTO
@client.command()
async def haiii(ctx):
    await ctx.send("haiii :3")

@client.command()
async def byeee(ctx):
    await ctx.send("byeee :3")

# COMANDOS DE CHAT DE VOZ
@client.command(pass_context=True)
async def play(ctx, url):
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    await ctx.send(f'Ahora suena: {player.title}')

@client.command(pass_context=True)
async def stop(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send("No estoy en ningun canal de voz. ¿Es que no me quieres aqui? :(")

@client.command(pass_context=True)
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Música pausada.")
    else:
        await ctx.send("ZA WARUDO. Ups, solo funciona cuando reproduzco algo :(")

@client.command(pass_context=True)
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
    else:
        await ctx.send("TOKI WA UGOKIDASU. Upsie, primero tengo que parar algo, ¿no crees :p?")

@play.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("No estás conectado a un canal de voz.")
            raise commands.CommandError("Autor no está conectado a un canal de voz.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()

client.run(botToken)
