import asyncio
import datetime
import discord
from discord.ext import commands
import random
import googleapiclient.discovery
from googleapiclient.errors import HttpError
import humanize
import requests
import openai
import yt_dlp as youtube_dl

# set the intents for the bot
intents = discord.Intents.default()
intents.message_content = True
# create the bot with '/' as the prefix for commands
bot = commands.Bot(command_prefix="/", intents=intents)

# keys and secrets
DISCORD_BOT_TOKEN = '***REMOVED***'
GOOGLE_API_KEY = '***REMOVED***'
CX = '***REMOVED***'
OPENAI_API_KEY = '***REMOVED***'

# other constants
CHANNEL_ID = ***REMOVED***
MESSAGE_COLOR = 0xFF5733


@bot.event
async def on_ready():
    # inform the server that the bot is online
    print("CrisisBot is online!")
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("CrisisBot is online!")
    # begin the openai keep alive function
    asyncio.create_task(keep_openai_alive())


@bot.event
async def on_command(ctx):
    # if the message was not in the allowed channel, log it
    # else log the command and who made it
    if ctx.message.channel.id != CHANNEL_ID:
        print(
            f"Command '{ctx.message.content}' was not in the allowed channel.")
    else:
        print(f"Command used by {ctx.author.name}: {ctx.message.content}")


@bot.event
async def on_command_error(ctx, error):
    # if the error is a command not found, inform the user
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply("Invalid command.")
    # else if the error is an HTTP error
    elif isinstance(error, HttpError):
        # if the error is a 429, inform the user
        # else display the error
        if error.resp.status == 429:
            await ctx.reply("Too many requests today. Please try again later.")
        else:
            await ctx.reply(f"An unhandled HTTP error occurred: {error}")
    # else if the error is an open ai error
    elif isinstance(error, openai.error.APIError):
        # if the error is a 429, inform the user
        # else display the error
        if error.status == 429:
            return "Too many requests have been made. Please try again later."
        else:
            await ctx.reply(f"An unhandled OpenAI error occurred: {error}")
    # else display the unhandled error
    else:
        await ctx.reply(f"An unhandled error occurred: {error}")


@bot.command()
async def image(ctx, *, query):
    try:
        # set the search url and the params for the search
        search_url = "https://www.googleapis.com/customsearch/v1"
        search_params = {
            "q": query,
            "searchType": "image",
            "cx": CX,
            "key": GOOGLE_API_KEY,
            "num": 10
        }
        # get the response from the url
        response = requests.get(search_url, params=search_params).json()
        images = [item["link"] for item in response.get("items", [])]
        # if there were no images found, inform the user
        if not images:
            await ctx.send("No images found.")
        else:
            # chose a random image from the results
            image_url = random.choice(images)
            # create and return the embed
            embed = discord.Embed(
                title=f"Here's a {query} image for you!", color=MESSAGE_COLOR)
            embed.set_image(url=image_url)
            embed.set_footer(
                text=f'{images.index(image_url) + 1} of {len(images)}')
            await ctx.reply(embed=embed)
    except Exception as error:
        raise error


@bot.command()
async def gif(ctx, *, query):
    try:
        # set the search url and the params for the search
        search_url = "https://www.googleapis.com/customsearch/v1"
        search_params = {
            "q": query,
            "searchType": "image",
            "imgType": "animated",
            "cx": CX,
            "key": GOOGLE_API_KEY,
            "num": 10
        }
        # get the response from the url
        response = requests.get(search_url, params=search_params).json()
        gifs = [item["link"] for item in response.get("items", [])]
        # if there were no gifs found, inform the user
        if not gifs:
            await ctx.send("No GIFs found.")
        else:
            # chose a random image from the results
            gif_url = random.choice(gifs)
            # create and return the embed
            embed = discord.Embed(
                title=f"Here's a {query} GIF for you!", color=MESSAGE_COLOR)
            embed.set_image(url=gif_url)
            embed.set_footer(text=f'{gifs.index(gif_url) + 1} of {len(gifs)}')
            await ctx.reply(embed=embed)
    except Exception as error:
        raise error


@bot.command()
async def video(ctx, *, query):
    try:
        # set the params for the search
        search_params = {
            "q": query,
            "type": "video",
            "part": "id",
            "maxResults": 50
        }
        # get the response from the url
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=GOOGLE_API_KEY)
        results = youtube.search().list(**search_params).execute()
        videos = [item["id"]["videoId"] for item in results["items"]
                  if item["id"]["kind"] == "youtube#video"]
        # if there were no videos found, inform the user
        if not videos:
            await ctx.send("No videos found.")
        else:
            # chose a random video from the results
            video_id = random.choice(videos)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            # create and return the embed
            embed = discord.Embed(
                title=f"Here's a {query} video for you!", color=MESSAGE_COLOR)
            embed.add_field(name="Video URL", value=video_url, inline=False)
            embed.set_image(
                url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
            embed.set_footer(
                text=f'{videos.index(video_id) + 1} of {len(videos)}')
            await ctx.reply(embed=embed)
    except Exception as error:
        raise error


@bot.command()
async def play(ctx, *, query):
    try:
        voice_state = ctx.author.voice
        # if the user is not in a voice channel, inform them they need to be and exit
        if not voice_state or not voice_state.channel:
            await ctx.reply("You need to be in a voice channel to use this command.")
            return
        ydl_opts = {'format': 'bestaudio'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query} audio", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
        if ctx.guild.voice_client is None:
            voice_client = await voice_state.channel.connect()
        source = discord.FFmpegPCMAudio(url)
        voice_client.play(source)
        embed = discord.Embed(
            title=info['title'], url=info['webpage_url'], color=MESSAGE_COLOR)
        embed.set_thumbnail(url=info['thumbnail'])
        embed.add_field(name="Duration", value=humanize.naturaldelta(
            datetime.timedelta(seconds=info['duration'])), inline=False)
        await ctx.reply(embed=embed)
        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()
    except Exception as error:
        raise error


@bot.command()
async def stop(ctx):
    try:
        voice_state = ctx.author.voice
        # if the user is not in a voice channel, inform them they need to be and exit
        if not voice_state or not voice_state.channel:
            await ctx.reply("You need to be in a voice channel to use this command.")
            return
        voice_client = ctx.guild.voice_client
        # if the bot is playing music, stop playing and inform the user
        if voice_client.is_playing():
            voice_client.stop()
            await ctx.reply("Stopped playing the current song.")
        # else inform the user that there are no songs playing
        else:
            await ctx.reply("I am not playing any songs right now.")
    except Exception as error:
        raise error


@bot.command()
async def chat(ctx, *, query):
    asyncio.create_task(background_task(query, ctx))


@bot.command()
async def bothelp(ctx):
    help_embed = discord.Embed(title="Bot Commands", color=MESSAGE_COLOR)
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
    help_embed.add_field(name="/chat <AI chat query>",
                         value="Talk to an AI.", inline=False)
    help_embed.add_field(
        name="/bothelp", value="Show a list of all the bot commands.", inline=False)
    await ctx.reply(embed=help_embed)


async def background_task(query, ctx):
    answer = await chatbot(query)
    await ctx.reply(answer)


async def chatbot(query):
    try:
        openai.api_key = OPENAI_API_KEY
        response = await asyncio.to_thread(openai.Completion.create,
                                           engine="davinci",
                                           prompt=f"Q: {query}\nA:",
                                           temperature=0.5,
                                           max_tokens=100,
                                           n=1,
                                           stop=["\nQ:"]
                                           )
        if response and response.choices and response.choices[0].text:
            answer = response.choices[0].text.strip()
            if len(response) > 2000:
                response = response[:2000]
            return answer
        else:
            return "Sorry, I couldn't generate a response. Please try again later."
    except Exception as error:
        raise error


async def keep_openai_alive():
    while True:
        try:
            openai.api_key = OPENAI_API_KEY
            response = openai.Completion.create(
                engine="davinci",
                prompt="ping",
                max_tokens=1,
                n=1,
                stop=None,
                temperature=0.5
            )
            if response.choices[0].text.strip() == "pong":
                print("OpenAI API connection is live!")
        except Exception as error:
            print(f"OpenAI API connection failed with error: {str(error)}")
        await asyncio.sleep(300)

# run the bot
bot.run(DISCORD_BOT_TOKEN)
