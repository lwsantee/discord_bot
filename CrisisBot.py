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

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="/", intents=intents)

DISCORD_BOT_TOKEN = 'MTA5NjE2NDM3OTE4MDk0MTM4Mw.GwtksM.aq6av9XoWi1Uy7-VCx8Y14wQV0ge99fXvTGbyQ'
GOOGLE_API_KEY = 'AIzaSyCUeJzbNBJ3L1LusiIzeZbW69-nWk4ejH8'
CX = '551d46812ea734e0f'
OPENAI_API_KEY = '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'
CHANNEL_ID = 1096284252125012068
MESSAGE_COLOR = 0xFF5733


@client.event
async def on_ready():
    print("CrisisBot is online!")
    channel = client.get_channel(CHANNEL_ID)
    await channel.send("CrisisBot is online!")
    asyncio.create_task(keep_alive())


async def keep_alive():
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
        except Exception as e:
            print(f"OpenAI API connection failed with error: {str(e)}")
        await asyncio.sleep(300)


@client.command(aliases=["image"])
async def randomImage(context, *, query):
    if context.channel.id != CHANNEL_ID:
        return
    try:
        search_url = "https://www.googleapis.com/customsearch/v1"
        search_params = {
            "q": query,
            "searchType": "image",
            "cx": CX,
            "key": GOOGLE_API_KEY,
            "num": 10
        }
        response = requests.get(search_url, params=search_params).json()
        images = [item["link"] for item in response.get("items", [])]
        if not images:
            await context.send("No images found.")
        else:
            image_url = random.choice(images)
            embed = discord.Embed(title=f"Here's a {query} image for you!", color=MESSAGE_COLOR)
            embed.set_image(url=image_url)
            embed.set_footer(text=f'{images.index(image_url) + 1} of {len(images)}')
            await context.reply(embed=embed)
    except HttpError as error:
        if error.resp.status == 429:
            await context.reply("Too many requests today. Please try again later.")
        else:
            raise error


@client.command(aliases=["gif"])
async def randomGif(context, *, query):
    if context.channel.id != CHANNEL_ID:
        return
    try:
        search_url = "https://www.googleapis.com/customsearch/v1"
        search_params = {
            "q": query,
            "searchType": "image",
            "imgType": "animated",
            "cx": CX,
            "key": GOOGLE_API_KEY,
            "num": 10
        }
        response = requests.get(search_url, params=search_params).json()
        gifs = [item["link"] for item in response.get("items", [])]
        if not gifs:
            await context.send("No GIFs found.")
        else:
            gif_url = random.choice(gifs)
            embed = discord.Embed(title=f"Here's a {query} GIF for you!", color=MESSAGE_COLOR)
            embed.set_image(url=gif_url)
            embed.set_footer(text=f'{gifs.index(gif_url) + 1} of {len(gifs)}')
            await context.reply(embed=embed)
    except HttpError as error:
        if error.resp.status == 429:
            await context.reply("Too many requests today. Please try again later.")
        else:
            raise error


@client.command(aliases=["video"])
async def randomVideo(context, *, query):
    if context.channel.id != CHANNEL_ID:
        return
    try:
        search_params = {
            "q": query,
            "type": "video",
            "part": "id",
            "maxResults": 50
        }
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=GOOGLE_API_KEY)
        results = youtube.search().list(**search_params).execute()
        videos = [item["id"]["videoId"] for item in results["items"] if item["id"]["kind"] == "youtube#video"]
        if not videos:
            await context.send("No videos found.")
        else:
            video_id = random.choice(videos)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            embed = discord.Embed(title=f"Here's a {query} video for you!", color=MESSAGE_COLOR)
            embed.add_field(name="Video URL", value=video_url, inline=False)
            embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
            embed.set_footer(text=f'{videos.index(video_id) + 1} of {len(videos)}')
            await context.reply(embed=embed)
    except HttpError as error:
        if error.resp.status == 429:
            await context.reply("Too many requests today. Please try again later.")
        else:
            raise error


@client.command(aliases=["play"])
async def playSong(context, *, query):
    try:
        voice_state = context.author.voice
        if not voice_state or not voice_state.channel:
            await context.reply("You need to be in a voice channel to use this command.")
            return
        ydl_opts = {'format': 'bestaudio'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query} audio", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
        if context.guild.voice_client is None:
            voice_client = await voice_state.channel.connect()
        source = discord.FFmpegPCMAudio(url)
        voice_client.play(source)
        embed = discord.Embed(title=info['title'], url=info['webpage_url'], color=MESSAGE_COLOR)
        embed.set_thumbnail(url=info['thumbnail'])
        embed.add_field(name="Duration", value=humanize.naturaldelta(datetime.timedelta(seconds=info['duration'])), inline=False)
        await context.reply(embed=embed)
        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()
    except Exception as error:
        raise error


@client.command(aliases=["stop"])
async def stopSong(context):
    voice_state = context.author.voice
    if not voice_state or not voice_state.channel:
        await context.reply("You need to be in a voice channel to use this command.")
        return
    voice_client = context.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await context.reply("Stopped playing the current song.")
    else:
        await context.reply("I am not playing any songs right now.")


async def ask_ai(prompt):
    try:
        openai.api_key = OPENAI_API_KEY
        response = await asyncio.to_thread(openai.Completion.create,
            engine="davinci",
            prompt=f"Q: {prompt}\nA:",
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
    except openai.error.APIError as error:
        if error.status == 429:
            return "Too many requests have been made. Please try again later."
        else:
            raise error


async def background_task(prompt, context):
    answer = await ask_ai(prompt)
    await context.reply(answer)


@client.command(aliases=["ask"])
async def askAI(context, *, prompt):
    asyncio.create_task(background_task(prompt, context))


@client.command(aliases=["oracle"])
async def magic8Ball(context):
    if context.channel.id != CHANNEL_ID:
        return
    responses = [
        "It is certain",
        "Without a doubt",
        "You may rely on it",
        "Yes, definitely",
        "It is decidedly so",
        "As I see it, yes",
        "Most likely",
        "Yes",
        "Outlook good",
        "Signs point to yes",
        "Reply hazy, try again",
        "Better not tell you now",
        "Ask again later",
        "Cannot predict now",
        "Concentrate and ask again",
        "Don't count on it",
        "Outlook not so good",
        "My sources say no",
        "Very doubtful",
        "My reply is no"
    ]
    message = random.choice(responses)
    await context.reply(message)


@client.command(aliases=["bothelp"])
async def botHelp(context):
    help_embed = discord.Embed(title="Bot Commands", color=MESSAGE_COLOR)
    help_embed.add_field(name="/image <image prompt>", value="Get a random image based on the search prompt.", inline=False)
    help_embed.add_field(name="/gif <gif prompt>", value="Get a random GIF based on the search prompt.", inline=False)
    help_embed.add_field(name="/video <video prompt>", value="Get a random video based on the search prompt.", inline=False)
    help_embed.add_field(name="/play <song name or URL>", value="Play a song in the voice channel.", inline=False)
    help_embed.add_field(name="/stop", value="Stop playing the current song.", inline=False)
    help_embed.add_field(name="/ask <chat prompt>", value="Talk to an AI.", inline=False)
    help_embed.add_field(name="/oracle <question>", value="Get a question answered by the oracle.", inline=False)
    help_embed.add_field(name="/help", value="Show a list of all the bot commands.", inline=False)
    await context.reply(embed=help_embed)


@client.event
async def on_command(context):
    if context.message.channel.id != CHANNEL_ID:
        print(f"Command '{context.message.content}' was not in the allowed channel.")
    else:
        print(f"Command used by {context.author.name}: {context.message.content}")


@client.event
async def on_command_error(context, error):
    if isinstance(error, commands.CommandNotFound):
        await context.reply("Invalid command.")
    else:
        await context.reply(f"An unhandled error occurred: {error}")

client.run(DISCORD_BOT_TOKEN)