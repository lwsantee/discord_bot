import asyncio
import datetime
import discord
import yt_dlp as youtube_dl
from discord.ext import commands

# Function to convert a duration in seconds to a human-readable format
def humanize_duration(seconds: int) -> str:
    SECONDS = 1
    MINUTES = 60 * SECONDS
    HOURS = 60 * MINUTES

    hours = seconds // HOURS
    seconds = seconds % HOURS
    minutes = seconds // MINUTES
    seconds = seconds % MINUTES

    human_duration = ""
    if hours > 1:
        human_duration += f"{hours} hours "
    elif hours == 1:
        human_duration += "1 hour "

    if minutes > 1:
        human_duration += f"{minutes} minutes "
    elif minutes == 1:
        human_duration += "1 minute "

    if seconds > 1:
        human_duration += f"{seconds} seconds"
    elif seconds == 1:
        human_duration += "1 second"

    return human_duration


# The Music class defines the behavior of the music bot commands
class Music(commands.Cog):
    def __init__(self, client):
        self.client = client  # Bot client
        self.song_queue = []  # Song queue
        self.song_history = []  # List of previously played songs
        self.currently_playing = None  # The current song being played

    # Function to ensure the bot joins the same voice channel as the command issuer
    async def join_voice_channel(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            if ctx.guild.voice_client is None:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.guild.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.reply("You need to be in a voice channel to use this command.")

    # Function to add a song to the queue
    async def add_to_queue(self, ctx, query):
        await self.join_voice_channel(ctx)  # Ensure the bot joins the voice channel
        ydl_opts = {
            "format": "bestaudio/best",
            "geo-bypass": True,
            "rm-cache-dir": True,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if (
                info
                and "entries" in info
                and len(info["entries"]) > 0
                and "url" in info["entries"][0]
            ):
                info = info["entries"][0]  # Get the first search result
                print(f"Found media url: {info['url']}")
            else:
                print(f"Got an unexpected result from YouTube search. Query: {query}. Response: {info}")
                await ctx.reply(f'No results found for "{query}"')
                return

        self.song_queue.append(info)  # Add the song to the queue

        if self.currently_playing is not None:
            await self.send_now_playing(ctx, info)  # Send now playing message

    # Function to send an embedded message with the current song's details
    async def send_now_playing(self, ctx, info):
        embed = discord.Embed(
            title=info["title"], url=info["webpage_url"], color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=info["thumbnail"])  # Set thumbnail for the embed
        embed.add_field(
            name="Duration",
            value=humanize_duration(info["duration"]),  # Format the song's duration
            inline=False,
        )
        await ctx.reply(embed=embed)  # Send the embed message

    # Function to play the next song in the queue
    async def play_next(self, ctx):
        voice_client = ctx.guild.voice_client
        if len(self.song_queue) == 0:  # If the queue is empty
            if voice_client is not None:
                await ctx.reply("There are no songs in the queue to play, disconnecting.")
                await voice_client.disconnect()
            return
        else:
            info = self.song_queue.pop(0)  # Get the next song from the queue
            self.currently_playing = info  # Set the current song to the next one

            def after_playing(error):
                if error:
                    print(f"Error occurred: {error}")
                self.song_history.append(self.currently_playing)  # Add the song to history
                self.currently_playing = None  # Clear the current song
                if len(self.song_queue) > 0:
                    coro = self.play_next(ctx)  # Schedule the next song
                    fut = asyncio.run_coroutine_threadsafe(coro, self.client.loop)
                    try:
                        fut.result()
                    except Exception as e:
                        print(f"Error in after_playing: {e}")

                else:
                    coro = voice_client.disconnect()  # Disconnect if no songs remain in the queue
                    fut = asyncio.run_coroutine_threadsafe(coro, self.client.loop)
                    try:
                        fut.result()
                    except Exception as e:
                        print(f"Error in after_playing: {e}")

            FFMPEG_OPTIONS = {"options": "-vn"}  # Options for the audio stream (no video)

            source = discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS)  # Create audio source
            voice_client.play(source, after=after_playing)  # Play the audio
            await self.send_now_playing(ctx, info)  # Send now playing message

    # Command to play a song
    @commands.command()
    async def play(self, ctx, *, query):
        await self.add_to_queue(ctx, query)  # Add song to the queue
        voice_client = ctx.guild.voice_client
        if (
            voice_client and not voice_client.is_playing()
        ):
            await self.play_next(ctx)  # Play the song if nothing is playing

    # Command to stop the current song and clear the queue
    @commands.command()
    async def stop(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            if voice_client.is_playing():
                voice_client.stop()  # Stop the song
                await voice_client.disconnect()  # Disconnect from the voice channel
                self.song_queue.clear()  # Clear the song queue
                await ctx.reply("Stopped playing the current song, disconnecting.")
                return
            else:
                await voice_client.disconnect()  # Disconnect if no song is playing
                self.song_queue.clear()
                self.song_history.clear()
        await ctx.reply("I am not playing any songs right now.")

    # Command to skip the current song
    @commands.command()
    async def skip(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            if voice_client.is_playing():
                voice_client.pause()  # Pause the current song
                await ctx.reply("Skipped the current song.")
                self.song_history.append(self.currently_playing)  # Add the song to history

                if len(self.song_queue) > 0:
                    await self.play_next(ctx)  # Play the next song
                else:
                    await ctx.reply("There are no songs in the queue to play, disconnecting.")
                    await voice_client.disconnect()
        else:
            await ctx.reply("I am not playing any songs right now.")

    # Command to go back to the previous song in history
    @commands.command()
    async def back(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing() and not voice_client.is_paused():
            if len(self.song_history) > 0:
                voice_client.pause()  # Pause the current song
                self.song_queue.insert(0, self.currently_playing)  # Insert the current song back into the queue
                self.song_queue.insert(0, self.song_history.pop())  # Add the last played song from history
                await self.play_next(ctx)  # Play the song
            else:
                await ctx.reply("No history before this song.")
        else:
            await ctx.reply("I am not playing any songs right now.")

    # Command to pause the current song
    @commands.command()
    async def pause(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing() and not voice_client.is_paused():
            voice_client.pause()  # Pause the playback
            await ctx.reply("Pausing playback.")
        else:
            await ctx.reply("I am not playing any songs right now.")

    # Command to resume the playback of the song
    @commands.command()
    async def resume(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()  # Resume the playback
            await ctx.reply("Resuming playback.")
        else:
            await ctx.reply("Not paused.")

    # Command to rewind the current song to the start
    @commands.command()
    async def rewind(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing() and not voice_client.is_paused():
            voice_client.pause()  # Pause the current song
            self.song_queue.insert(0, self.currently_playing)  # Insert the current song at the start of the queue
            await self.play_next(ctx)  # Play the song again from the start
        else:
            await ctx.reply("I am not playing any songs right now.")

    # Command to clear the song queue
    @commands.command()
    async def clear(self, ctx):
        if len(self.song_queue) != 0:
            self.song_queue.clear()  # Clear the queue
            await ctx.reply("Cleared the queue.")
        else:
            await ctx.reply("Nothing in the queue to clear.")

    # Command to clear the song history
    @commands.command()
    async def clearhistory(self, ctx):
        if len(self.song_history) != 0:
            self.song_history.clear()  # Clear the history
            await ctx.reply("Cleared the history.")
        else:
            await ctx.reply("Nothing in the history to clear.")

    # Command to display the song queue
    @commands.command()
    async def queue(self, ctx):
        embed = discord.Embed(
            title="Song Queue",
            description="Here is the list of songs in the queue:",
            color=discord.Color.blurple(),
        )

        for index, song in enumerate(self.song_queue, start=1):
            embed.add_field(name=f"Song {index}", value=song["title"], inline=False)

        await ctx.send(embed=embed)

    # Command to display the song history
    @commands.command()
    async def history(self, ctx):
        embed = discord.Embed(
            title="Song History",
            description="Here is the list of previously played songs:",
            color=discord.Color.blurple(),
        )

        for index, song in enumerate(self.song_history, start=1):
            embed.add_field(name=f"Song {index}", value=song["title"], inline=False)

        await ctx.send(embed=embed)

# Function to set up the Music cog
async def setup(client):
    await client.add_cog(Music(client))
