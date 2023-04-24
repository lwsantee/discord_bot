import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {'format': 'bestaudio/best', 'quiet': True}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []

    async def play_next(self, ctx):
        """Plays the next song in the queue."""
        if len(self.song_queue) > 0:
            url = self.song_queue.pop(0)
            voice = get(self.bot.voice_clients, guild=ctx.guild)
            with ytdl:
                info = ytdl.extract_info(url, download=False)
                url2 = info['formats'][0]['url']
                voice.play(discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))

    @commands.command()
    async def play(self, ctx, url):
        """Plays a song in a voice call."""
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            return await ctx.send('You must be in a voice channel to use this command.')

        # Join the voice channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(voice_channel)
        else:
            voice = await voice_channel.connect()

        # Queue up the song
        self.song_queue.append(url)

        # Start playing the song if there are no other songs in the queue
        if len(self.song_queue) == 1:
            await self.play_next(ctx)

    @commands.command()
    async def stop(self, ctx):
        """Stops playing music in a voice call."""
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.stop()

    @commands.command()
    async def queue(self, ctx, url):
        """Queues a song to be played in a voice call."""
        self.song_queue.append(url)
        await ctx.send(f'Queued {url}.')
