import traceback
import discord
from discord.ext import commands
from googleapiclient.errors import HttpError
from media import *
from music import *

# Set the intents for the bot
intents = discord.Intents.default()
intents.message_content = True
# Create the bot with '/' as the prefix for commands
bot = commands.Bot(command_prefix=".", intents=intents)

# Keys and secrets
DISCORD_BOT_TOKEN = '***REMOVED***'
GOOGLE_API_KEY = '***REMOVED***'
CX = '***REMOVED***'

# Other constants
CHANNEL_ID = ***REMOVED***
VOICE_QUEUE = []


@bot.event
async def on_ready():
    # Inform the server that the bot is online
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("CrisisBot is online!")


@bot.event
async def on_command_error(ctx, error):
    # Format the log message
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f'Timestamp: {timestamp}\nUser Input: {ctx.message}\nError: {error}\n{traceback.format_exc()}\n'
    # Log the message in the errorlog.txt file
    with open('errorlog.txt', 'a') as log_file:
        log_file.write(log_message)

    # If the error is a command not found, inform the user
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply("Invalid command.")
    # Else if the error is an HTTP error
    elif isinstance(error, HttpError):
        # If the error is a 429, inform the user
        # Else display the error
        if error.resp.status == 429:
            await ctx.reply("Too many requests today. Please try again later.")
        else:
            await ctx.reply(f"An unhandled HTTP error occurred: {error}")
    # Else display the unhandled error
    else:
        await ctx.reply(f"An unhandled error occurred: {error}")


@bot.command()
async def image(ctx, *, query):
    await image_search(ctx, query=query, CX=CX, GOOGLE_API_KEY=GOOGLE_API_KEY)


@bot.command()
async def gif(ctx, *, query):
    await gif_search(ctx, query=query, CX=CX, GOOGLE_API_KEY=GOOGLE_API_KEY)


@bot.command()
async def video(ctx, *, query):
    await video_search(ctx, query=query, GOOGLE_API_KEY=GOOGLE_API_KEY)


@bot.command()
async def play(ctx, *, query):
    await play_music(ctx, query=query, queue=VOICE_QUEUE)


@bot.command()
async def stop(ctx):
    await stop_music(ctx, queue=VOICE_QUEUE)


@bot.command()
async def skip(ctx):
    await skip_song(ctx)


@bot.command()
async def queue(ctx, *, query):
    await add_to_queue(ctx, query=query, queue=VOICE_QUEUE)


@bot.command()
async def clear(ctx):
    await clear_queue(ctx, queue=VOICE_QUEUE)


@bot.command()
async def help(ctx):
    help_embed = discord.Embed(
        title="Bot Commands", color=discord.Color.blurple())
    help_embed.add_field(name="/image <image query>",
                         value="Get a random image based on the search query.", inline=False)
    help_embed.add_field(name="/gif <gif query>",
                         value="Get a random GIF based on the search query.", inline=False)
    help_embed.add_field(name="/video <video query>",
                         value="Get a random video based on the search query.", inline=False)
    help_embed.add_field(name="/play <song name or URL>",
                         value="Play a song in the voice channel.", inline=False)
    help_embed.add_field(
        name="/stop", value="Stop playing the current song.", inline=False)
    help_embed.add_field(name="/queue <song name or URL>",
                         value="Queue a song to play next.", inline=False)
    help_embed.add_field(
        name="/skip", value="Skip the current song.", inline=False)
    help_embed.add_field(
        name="/clear", value="Clear the song queue.", inline=False)
    help_embed.add_field(
        name="/help", value="Show a list of all the bot commands.", inline=False)
    await ctx.reply(embed=help_embed)


# Run the bot
bot.run(DISCORD_BOT_TOKEN)
