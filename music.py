import asyncio
import datetime
import discord
import humanize
import yt_dlp as youtube_dl


# Method to play music in a voice channel
async def play_music(ctx, *, query, queue):
    try:
        # Get the voice state of the user
        voice_state = ctx.author.voice
        # If the user is not in a voice channel, inform them and exit
        if not voice_state or not voice_state.channel:
            await ctx.reply("You need to be in a voice channel to use this command.")
            return
        # Set options for YouTube DL
        ydl_opts = {'format': 'bestaudio'}
        # Use YouTube DL to extract information about the query
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query} audio", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
        # Connect to the voice channel if not already connected
        if ctx.guild.voice_client is None:
            voice_client = await voice_state.channel.connect()
        # Create an audio source from the URL
        source = discord.FFmpegPCMAudio(url)
        # Queue the audio source
        queue.append(source)
        # Create an embed with information about the queued song
        embed = discord.Embed(
            title=info['title'], url=info['webpage_url'], color=discord.Color.blurple())
        embed.set_thumbnail(url=info['thumbnail'])
        embed.add_field(name="Duration", value=humanize.naturaldelta(
            datetime.timedelta(seconds=info['duration'])), inline=False)
        await ctx.reply(embed=embed)
        # If the bot is not currently playing, start playing from the queue
        if not voice_client.is_playing():
            await play_next(ctx, queue=queue)
    except Exception as error:
        raise error


# Method to stop playing music in a voice channel
async def stop_music(ctx, queue):
    try:
        # Get the voice state of the user
        voice_state = ctx.author.voice
        # If the user is not in a voice channel, inform them and exit
        if not voice_state or not voice_state.channel:
            await ctx.reply("You need to be in a voice channel to use this command.")
            return
        voice_client = ctx.guild.voice_client
        if voice_client is not None:
            # If the bot is playing music, stop playing and inform the user
            if voice_client.is_playing():
                voice_client.stop()
                await voice_client.disconnect()
                queue.clear()
                await ctx.reply("Stopped playing the current song, disconnecting.")
                return
            else:
                await voice_client.disconnect()
                queue.clear()
        await ctx.reply("I am not playing any songs right now.")
    except Exception as error:
        raise error


# Method to skip the current song and play the next song in the queue
async def skip_song(ctx, queue):
    try:
        # Get the voice state of the user
        voice_state = ctx.author.voice
        # If the user is not in a voice channel, inform them and exit
        if not voice_state or not voice_state.channel:
            await ctx.reply("You need to be in a voice channel to use this command.")
            return
        voice_client = ctx.guild.voice_client
        # If connected to the voice channel
        if voice_client is not None:
            # If the bot is playing music, stop playing the current song and play the next song
            if voice_client.is_playing():
                voice_client.stop()
                await ctx.reply("Skipped the current song.")
                await play_next(ctx, queue=queue)
                return
        await ctx.reply("I am not playing any songs right now.")
    except Exception as error:
        raise error


# Method to add a song to the queue
async def add_to_queue(ctx, *, query, queue):
    try:
        # Get the voice state of the user
        voice_state = ctx.author.voice
        # If the user is not in a voice channel, inform them and exit
        if not voice_state or not voice_state.channel:
            await ctx.reply("You need to be in a voice channel to use this command.")
            return
        voice_client = ctx.guild.voice_client
        # Set options for YouTube DL
        ydl_opts = {'format': 'bestaudio'}
        # Use YouTube DL to extract information about the query
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query} audio", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
        # Create an audio source from the URL
        source = discord.FFmpegPCMAudio(url)
        # Queue the audio source
        queue.append(source)
        # Create an embed with information about the queued song
        embed = discord.Embed(
            title=info['title'], url=info['webpage_url'], color=discord.Color.blurple())
        embed.set_thumbnail(url=info['thumbnail'])
        embed.add_field(name="Duration", value=humanize.naturaldelta(
            datetime.timedelta(seconds=info['duration'])), inline=False)
        await ctx.reply(embed=embed)
        # Connect to the voice channel if not already connected
        if voice_client is None:
            voice_client = await voice_state.channel.connect()
        # If the bot is not currently playing, start playing from the queue
        if not voice_client.is_playing():
            await play_next(ctx, queue=queue)
    except Exception as error:
        raise error


# Method to play the next song in the queue
async def play_next(ctx, queue):
    try:
        # Check if the author is in a voice channel
        voice_state = ctx.author.voice
        if not voice_state or not voice_state.channel:
            await ctx.reply("You need to be in a voice channel to use this command.")
            return
        # Retrieve the voice client for the guild
        voice_client = ctx.guild.voice_client
        # Check if the queue is empty
        if len(queue) == 0:
            # If the queue is empty, send a reply and disconnect the voice client
            await ctx.reply("There are no songs in the queue to play, disconnecting.")
            await voice_client.disconnect()
        else:
            # Stop the voice client from playing any audio
            voice_client.stop()
            # Get the first song from the queue and play it
            source = queue.pop(0)
            voice_client.play(source)
            # Wait until the voice client finishes playing the audio
            while voice_client.is_playing():
                await asyncio.sleep(1)
            # Check if there are more songs in the queue
            if len(queue) != 0:
                # If there are more songs, recursively call the function to play the next one
                await play_next(ctx, queue)
    except Exception as error:
        raise error


# Method to clear the queue
async def clear_queue(ctx, queue):
    try:
        if len(queue) != 0:
            queue.clear()
            await ctx.reply("Cleared the queue.")
        else:
            await ctx.reply("Nothing in the queue to clear.")
    except Exception as error:
        raise error
