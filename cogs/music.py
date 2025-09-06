import discord
from discord.ext import commands
import os
import urllib.parse
import requests
import urllib.parse
import spotify_controller


def humanize_duration(seconds: int) -> str:
    """
    Converts a duration given in seconds to a human-readable format (e.g., "1 hour 30 minutes").

    Parameters:
    - seconds (int): The duration in seconds to be converted.

    Returns:
    - str: The human-readable format of the duration.
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

        Parameters:
        - bot (commands.Bot): The bot instance to which the cog will be added.
        """
        self.bot = bot

    # ======== Data Processing ========

    async def join_voice_channel(self, ctx):
        """
        Ensures the bot joins the same voice channel as the user who invoked the command.

        Parameters:
        - ctx (commands.Context): The context of the command invocation.
        """

        if os.getenv("SPOTIFY_ACCESS_TOKEN") is None:
            response = requests.get(f"{os.getenv('AUTH_SERVER')}/access-token/{os.getenv('AUTH_SERVER_SECURITY')}")
            if 300 > response.status_code >= 200:
                os.environ["SPOTIFY_ACCESS_TOKEN"] = response.text
            else: 
                await ctx.reply("You are logged out.")
                await self.login_command(ctx)

        if spotify_controller.librespot is None:
            spotify_controller.start_librespot()

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

        Parameters:
        - ctx (commands.Context): The context of the command invocation.
        - query (str): The song name or YouTube link to search for.
        """
        await self.join_voice_channel(ctx)
        search_results = spotify_controller.search(f'"{query}"')
        track_uri = search_results["tracks"]["items"][0]["uri"]
        print("adding to queue", spotify_controller.add_to_queue(track_uri))
        spotify_controller.switch_to_device()
        if not spotify_controller.is_playing():
            spotify_controller.play()

        # if self.currently_playing is not None:
        #     await self.send_now_playing(ctx, info)

    async def send_now_playing(self, ctx, info):
        """
        Sends an embedded message with the current song's details, including title, duration, and thumbnail.

        Parameters:
        - ctx (commands.Context): The context of the command invocation.
        - info (dict): Information about the song currently playing.
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

        Parameters:
        - ctx (commands.Context): The context of the command invocation.
        """

        voice_client = ctx.guild.voice_client
        source = discord.FFmpegPCMAudio(
            pipe=True, 
            source=spotify_controller.librespot.stdout, 
            before_options="-f s16le -ar 44100 -ac 2",
            options="-f s16le -ar 48000 -ac 2",     
        )

        voice_client.play(source)
        # await self.send_now_playing(ctx, info)

    # ======== Commands ========

    @commands.command(name="login", help="Login to a Spotify Premium account to play music.")
    async def login_command(self, ctx): 
        """
        **Usage:** `.login`

        **Example:** 
        - `.login` -> responds with a link to login to spotify 

        **Description:** 
        Shares a link to login to a Spotify Premium account 
        """
        search_params = {
            "scope": "streaming user-read-email user-read-private user-read-playback-state",
            "response_type": "code",
            "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
            "redirect_uri": f"{os.getenv('AUTH_SERVER')}/callback",
            "state": os.getenv("AUTH_SERVER_SECURITY"),
        }
        query_string = urllib.parse.urlencode(search_params)
        url = f"https://accounts.spotify.com/authorize/?{query_string}"

        embed = discord.Embed(
            title="Spotify Premium Login", url=url, color=discord.Color.blurple()
        )

        await ctx.send(embed=embed)
        

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
            spotify_controller.skip("next")
            await ctx.reply("Skipping to the next song")
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
            spotify_controller.skip("previous")
            await ctx.reply("Returning to previous song")
        else:
            await ctx.reply("I am not playing any songs right now.")

    @commands.command(name="pause", help="Pauses the current song if it's playing.")
    async def pause_command(self, ctx):
        """
        **Usage:** `.pause`

        **Description:**
        Pauses the current song if it's playing. If no song is playing, informs the user.
        """
        if spotify_controller.is_playing():
            spotify_controller.pause()
            await ctx.reply("Pausing playback")
        else:
            await ctx.reply("Already paused. You may have meant to use `.resume`")

    @commands.command(
        name="resume", help="Resumes the playback of the current song if it's paused."
    )
    async def resume_command(self, ctx):
        """
        **Usage:** `.resume`

        **Description:**
        Resumes the playback of the current song if it's paused. If no song is paused, informs the user.
        """
        if not spotify_controller.is_playing():
            spotify_controller.play()
            await ctx.reply("Resuming playback")
        else:
            await ctx.reply("Already playing. You may have meant to use `.pause`")

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

    Parameters:
    - bot (commands.Bot): The bot instance to which the cog will be added.
    """
    await bot.add_cog(Music(bot))
