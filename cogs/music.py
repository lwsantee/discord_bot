import asyncio
import discord
import yt_dlp as youtube_dl
from discord.ext import commands


def humanize_duration(seconds: int) -> str:
    """
    Converts a duration given in seconds to a human-readable format (e.g., "1 hour 30 minutes").
    """
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


class Music(commands.Cog):
    def __init__(self, bot):
        """
        Initializes the Music cog with the bot instance, song queue, and song history.
        """
        self.bot = bot
        self.song_queue = []
        self.song_history = []
        self.currently_playing = None

    # ======== Data Processing ========

    async def join_voice_channel(self, ctx):
        """
        Ensures the bot joins the same voice channel as the user who invoked the command.
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
        Adds a song to the queue based on the search query.
        """
        await self.join_voice_channel(ctx)
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
                info = info["entries"][0]
                print(f"Found media url: {info['url']}")
            else:
                print(
                    f"Got an unexpected result from YouTube search. Query: {query}. Response: {info}"
                )
                await ctx.reply(f'No results found for "{query}"')
                return

        self.song_queue.append(info)

        if self.currently_playing is not None:
            await self.send_now_playing(ctx, info)

    async def send_now_playing(self, ctx, info):
        """
        Sends an embedded message with the current song's details, including title, duration, and thumbnail.
        """
        embed = discord.Embed(
            title=info["title"], url=info["webpage_url"], color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=info["thumbnail"])
        embed.add_field(
            name="Duration",
            value=humanize_duration(info["duration"]),
            inline=False,
        )
        await ctx.reply(embed=embed)

    async def play_next(self, ctx):
        """
        Plays the next song in the queue.
        If no songs remain, disconnects the bot from the voice channel.
        """
        voice_client = ctx.guild.voice_client
        if len(self.song_queue) == 0:
            if voice_client is not None:
                await ctx.reply(
                    "There are no songs in the queue to play, disconnecting."
                )
                await voice_client.disconnect()
            return
        else:
            info = self.song_queue.pop(0)
            self.currently_playing = info

            def after_playing(error):
                """
                Callback function executed after a song finishes playing.
                Adds the current song to history, and plays the next song in the queue.
                """
                if error:
                    print(f"Error occurred: {error}")
                self.song_history.append(self.currently_playing)
                self.currently_playing = None
                if len(self.song_queue) > 0:
                    coro = self.play_next(ctx)
                    fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                    fut.result()

                else:
                    coro = voice_client.disconnect()
                    fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                    fut.result()

            FFMPEG_OPTIONS = {"options": "-vn"}

            source = discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS)
            voice_client.play(source, after=after_playing)
            await self.send_now_playing(ctx, info)

    # ======== Commands ========

    @commands.command(
        name="play", help="Adds a song to the queue and plays it if nothing is playing."
    )
    async def play_command(self, ctx, *, query):
        """
        **Usage:** `.play <query>`

        **Parameters:**
        - `<query>` - The name of (or link to) a YouTube video.

        **Example:**
        - `.play Never Gonna Give You Up` → "Joins the voice channel the user is in and begins playing Never Gonna Give You Up."

        **Description:**
        Adds a song to the queue and plays it if nothing is playing.
        """
        await self.add_to_queue(ctx, query)
        voice_client = ctx.guild.voice_client
        if voice_client and not voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command(
        name="stop", help="Stops the current song and clears the song queue."
    )
    async def stop_command(self, ctx):
        """
        **Usage:** `.stop`

        **Description:**
        Stops the current song and clears the song queue. Disconnects the bot from the voice channel if no song is playing.
        """
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            if voice_client.is_playing():
                voice_client.stop()
                await voice_client.disconnect()
                self.song_queue.clear()
                await ctx.reply("Stopped playing the current song, disconnecting.")
                return
            else:
                await voice_client.disconnect()
                self.song_queue.clear()
                self.song_history.clear()
        await ctx.reply("I am not playing any songs right now.")

    @commands.command(
        name="skip", help="Skips the current song and plays the next one in the queue."
    )
    async def skip_command(self, ctx):
        """
        **Usage:** `.skip`

        **Description:**
        Skips the current song and plays the next one in the queue. If no songs remain, disconnects the bot from the voice channel.
        """
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            if voice_client.is_playing():
                voice_client.pause()
                await ctx.reply("Skipped the current song.")
                self.song_history.append(self.currently_playing)

                if len(self.song_queue) > 0:
                    await self.play_next(ctx)
                else:
                    await ctx.reply(
                        "There are no songs in the queue to play, disconnecting."
                    )
                    await voice_client.disconnect()
        else:
            await ctx.reply("I am not playing any songs right now.")

    @commands.command(
        name="back", help="Goes back to the previous song in history if available."
    )
    async def back_command(self, ctx):
        """
        **Usage:** `.back`

        **Description:**
        Goes back to the previous song in history if available. If no history exists, informs the user.
        """
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing() and not voice_client.is_paused():
            if len(self.song_history) > 0:
                voice_client.pause()
                self.song_queue.insert(0, self.currently_playing)
                self.song_queue.insert(0, self.song_history.pop())
                await self.play_next(ctx)
            else:
                await ctx.reply("No history before this song.")
        else:
            await ctx.reply("I am not playing any songs right now.")

    @commands.command(name="pause", help="Pauses the current song if it's playing.")
    async def pause_command(self, ctx):
        """
        **Usage:** `.pause`

        **Description:**
        Pauses the current song if it's playing. If no song is playing, informs the user.
        """
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing() and not voice_client.is_paused():
            voice_client.pause()
            await ctx.reply("Pausing playback.")
        else:
            await ctx.reply("I am not playing any songs right now.")

    @commands.command(
        name="resume", help="Resumes the playback of the current song if it's paused."
    )
    async def resume_command(self, ctx):
        """
        **Usage:** `.resume`

        **Description:**
        Resumes the playback of the current song if it's paused. If no song is paused, informs the user.
        """
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.reply("Resuming playback.")
        else:
            await ctx.reply("Not paused.")

    @commands.command(name="rewind", help="Rewinds the current song to the start.")
    async def rewind_command(self, ctx):
        """
        **Usage:** `.rewind`

        **Description:**
        Rewinds the current song to the start and plays it again. If no song is playing, informs the user.
        """
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing() and not voice_client.is_paused():
            voice_client.pause()
            self.song_queue.insert(0, self.currently_playing)
            await self.play_next(ctx)
        else:
            await ctx.reply("I am not playing any songs right now.")

    @commands.command(name="clear", help="Clears the song queue.")
    async def clear_queue_command(self, ctx):
        """
        **Usage:** `.clear`

        **Description:**
        Clears the song queue if there are any songs in the queue.
        """
        if len(self.song_queue) != 0:
            self.song_queue.clear()
            await ctx.reply("Cleared the queue.")
        else:
            await ctx.reply("Nothing in the queue to clear.")

    @commands.command(name="clearhistory", help="Clears the song history.")
    async def clear_history_command(self, ctx):
        """
        **Usage:** `.clearhistory`

        **Description:**
        Clears the song history if there are any songs in history.
        """
        if len(self.song_history) != 0:
            self.song_history.clear()
            await ctx.reply("Cleared the history.")
        else:
            await ctx.reply("Nothing in the history to clear.")

    @commands.command(
        name="queue", help="Displays the list of songs currently in the queue."
    )
    async def queue_command(self, ctx):
        """
        **Usage:** `.queue`

        **Description:**
        Displays the list of songs currently in the queue.
        """
        embed = discord.Embed(
            title="Song Queue",
            description="Here is the list of songs in the queue:",
            color=discord.Color.blurple(),
        )

        for index, song in enumerate(self.song_queue, start=1):
            embed.add_field(name=f"Song {index}", value=song["title"], inline=False)

        await ctx.send(embed=embed)

    @commands.command(
        name="history", help="Displays the list of previously played songs."
    )
    async def history_command(self, ctx):
        """
        **Usage:** `.history`

        **Description:**
        Displays the list of previously played songs.
        """
        embed = discord.Embed(
            title="Song History",
            description="Here is the list of previously played songs:",
            color=discord.Color.blurple(),
        )

        for index, song in enumerate(self.song_history, start=1):
            embed.add_field(name=f"Song {index}", value=song["title"], inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    """
    Sets up the Music cog by adding it to the bot client.
    """
    await bot.add_cog(Music(bot))
