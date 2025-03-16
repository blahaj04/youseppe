import yt_dlp
import asyncio
import discord
from discord import FFmpegPCMAudio

# Opciones de yt-dlp
ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': False,  # Permitir listas de reproducción
    'nocheckcertificate': True,
    'quiet': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'geo_bypass': True,
    'geo_bypass_country': 'US',
    'logger': None,
    'logtostderr': True,
    'verbose': True,
    'ignoreerrors': True,  # Evita que el bot crashee si hay un error con un video
    'skip_download': True,  # Evita descargar metadata innecesaria
    'extractor_args': {
        'youtube': {
            'client': 'web'  # IMPORTANTE: No usa el cliente de iOS
        }
    }
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
    async def from_url(cls, url: str, *, loop=None, stream=True, retries=3):
        loop = loop or asyncio.get_event_loop()
        
        for attempt in range(retries):
            try:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
                if 'entries' in data:
                    data = data['entries'][0]

                filename = data['url'] if stream else ytdl.prepare_filename(data)
                return cls(FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

            except yt_dlp.utils.DownloadError as e:
                print(f"[ERROR] Intento {attempt + 1} de {retries}: No se pudo descargar {url}: {e}")
                await asyncio.sleep(2)  # Espera antes de reintentar

        print(f"[AVISO] Video {url} no disponible después de {retries} intentos. Saltando...")
        return None  # Devuelve None si no se pudo obtener el video
