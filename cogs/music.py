import asyncio
import datetime
import discord
import humanize
import yt_dlp as youtube_dl
from discord.ext import commands

# FFmpeg options to be used with discord.FFmpegPCMAudio
# FFMPEG_OPTIONS = {"options": "-vn -filter_complex \"[0:a]apad=pad_dur=5\""}  # Adds 5 seconds of silence to the end of each song
FFMPEG_OPTIONS = {"options": "-vn"}


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client  # Discord bot client
        self.queue = []  # Queue to store songs to be played

    async def join_voice_channel(self, ctx):
        """
        Ensures the bot joins the same voice channel as the command issuer.
        """
        if ctx.author.voice and ctx.author.voice.channel:
            if ctx.guild.voice_client is None:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.guild.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.reply("You need to be in a voice channel to use this command.")

    async def add_to_queue(self, ctx, query):
        """
        Adds a song to the queue.
        """

        await self.join_voice_channel(ctx)  # Ensure bot is in a voice channel
        ydl_opts = {"format": "bestaudio/best", "geo-bypass": True, "rm-cache-dir": True}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if info and "entries" in info and len(info["entries"]) > 0 and "url" in info["entries"][0]:
                info = info["entries"][0]  # Get the first search result
                print(f"Found media url: {info['url']}")
            else:
                print(f"Got an unexpected result from YouTube search. Query: {query}. Response: {info}")
                await ctx.reply(f"No results found for \"{query}\"")
                return 

        self.queue.append(info)
        await self.send_now_playing(ctx, info)  # Send now playing message

    async def send_now_playing(self, ctx, info):
        """
        Sends an embedded message with the current song's details.
        """
        embed = discord.Embed(
            title=info["title"], url=info["webpage_url"], color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=info["thumbnail"])
        embed.add_field(
            name="Duration",
            value=humanize.naturaldelta(datetime.timedelta(seconds=info["duration"])),
            inline=False,
        )
        await ctx.reply(embed=embed)

    async def play_next(self, ctx):
        """
        Plays the next song in the queue.
        """
        voice_client = ctx.guild.voice_client
        if len(self.queue) == 0:
            if voice_client is not None:
                await ctx.reply(
                    "There are no songs in the queue to play, disconnecting."
                )
                await voice_client.disconnect()
            return
        else:
            info = self.queue.pop(0)  # Get the next song from the queue

            def after_playing(error):
                """
                Callback to be called after the current song finishes.
                """
                if error:
                    print(f"Error occurred: {error}")
                coro = self.play_next(ctx)  # Schedule playing the next song
                fut = asyncio.run_coroutine_threadsafe(coro, self.client.loop)
                try:
                    fut.result()
                except Exception as e:
                    print(f"Error in after_playing: {e}")

            # Create an ffmpeg subprocess to stream the audio from the url provided by youtube search
            source = discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS)  
            voice_client.play(source, after=after_playing)  # Play the current song
            await self.send_now_playing(ctx, info)  # Send now playing message

    @commands.command()
    async def play(self, ctx, *, query):
        """
        Play a song.
        """
        await self.add_to_queue(ctx, query)  # Add song to the queue
        voice_client = ctx.guild.voice_client
        if voice_client and not voice_client.is_playing():  # If nothing is playing, start playing
            await self.play_next(ctx)

    @commands.command()
    async def stop(self, ctx):
        """
        Stop playing music and clear the queue.
        """
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            if voice_client.is_playing():
                voice_client.stop()
                await voice_client.disconnect()
                self.queue.clear()
                await ctx.reply("Stopped playing the current song, disconnecting.")
                return
            else:
                await voice_client.disconnect()
                self.queue.clear()
        await ctx.reply("I am not playing any songs right now.")

    @commands.command()
    async def skip(self, ctx):
        """
        Skip the current song.
        """
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            if voice_client.is_playing():
                voice_client.pause()
                await ctx.reply("Skipped the current song.")
                await self.play_next(ctx)
        else:
            await ctx.reply("I am not playing any songs right now.")

    @commands.command()
    async def add(self, ctx, *, query):
        """
        Add a song to the queue.
        """
        await self.add_to_queue(ctx, query)

    @commands.command()
    async def clear(self, ctx):
        """
        Clear the song queue.
        """
        if len(self.queue) != 0:
            self.queue.clear()
            await ctx.reply("Cleared the queue.")
        else:
            await ctx.reply("Nothing in the queue to clear.")


# Function to set up the Music cog
async def setup(client):
    await client.add_cog(Music(client))
