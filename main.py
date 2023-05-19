import discord
from discord.ext import commands
from googleapiclient.errors import HttpError
import openai
from media import *
from chat import *
from music import *

# Set the intents for the bot
intents = discord.Intents.default()
intents.message_content = True
# Create the bot with '/' as the prefix for commands
bot = commands.Bot(command_prefix="/", intents=intents)

# Keys and secrets
DISCORD_BOT_TOKEN = '***REMOVED***'
GOOGLE_API_KEY = '***REMOVED***'
CX = '***REMOVED***'
OPENAI_API_KEY = '***REMOVED***'

# Other constants
CHANNEL_ID = ***REMOVED***
VOICE_QUEUE = []


@bot.event
async def on_ready():
    # Inform the server that the bot is online
    print("CrisisBot is online!")
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("CrisisBot is online!")
    # Begin the OpenAI keep alive function
    asyncio.create_task(keep_openai_alive(OPENAI_API_KEY))


@bot.event
async def on_command(ctx):
    # If the message was not in the allowed channel, log it
    # Else log the command and who made it
    if ctx.message.channel.id != CHANNEL_ID:
        print(
            f"Command '{ctx.message.content}' was not in the allowed channel.")
    else:
        print(f"Command used by {ctx.author.name}: {ctx.message.content}")


@bot.event
async def on_command_error(ctx, error):
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
    # Else if the error is an OpenAI error
    elif isinstance(error, openai.error.APIError):
        # If the error is a 429, inform the user
        # Else display the error
        if error.status == 429:
            return "Too many requests have been made. Please try again later."
        else:
            await ctx.reply(f"An unhandled OpenAI error occurred: {error}")
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
async def chat(ctx, *, query):
    await chat_bot(ctx, query=query, OPENAI_API_KEY=OPENAI_API_KEY)


@bot.command()
async def play(ctx, *, query):
    await play_music(ctx, query=query, queue=VOICE_QUEUE)


@bot.command()
async def stop(ctx):
    await stop_music(ctx, queue=VOICE_QUEUE)


@bot.command()
async def skip(ctx):
    await skip_song(ctx, queue=VOICE_QUEUE)


@bot.command()
async def queue(ctx, *, query):
    await add_to_queue(ctx, query=query, queue=VOICE_QUEUE)


@bot.command()
async def clear(ctx):
    await clear_queue(ctx, queue=VOICE_QUEUE)


@bot.command()
async def bothelp(ctx):
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
    help_embed.add_field(name="/chat <AI chat query>",
                         value="Talk to an AI.", inline=False)
    help_embed.add_field(
        name="/bothelp", value="Show a list of all the bot commands.", inline=False)
    await ctx.reply(embed=help_embed)


# Run the bot
bot.run(DISCORD_BOT_TOKEN)
