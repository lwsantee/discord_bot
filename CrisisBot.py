import discord
from discord.ext import commands
import random
import googleapiclient.discovery
from googleapiclient.errors import HttpError
import requests
import openai

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="/", intents=intents)

DISCORD_BOT_TOKEN = 'MTA5NjE2NDM3OTE4MDk0MTM4Mw.GwtksM.aq6av9XoWi1Uy7-VCx8Y14wQV0ge99fXvTGbyQ'
GOOGLE_API_KEY = 'AIzaSyCUeJzbNBJ3L1LusiIzeZbW69-nWk4ejH8'
CX = '551d46812ea734e0f'
OPEN_API_KEY = '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'
CHANNEL_ID = 1096284252125012068


@client.event
async def on_ready():
    print("CrisisBot is online!")
    channel = client.get_channel(CHANNEL_ID)
    await channel.send("CrisisBot is online!")


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
            embed = discord.Embed(title=f"Here's a {query} image for you!", color=0xFF5733)
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
            embed = discord.Embed(title=f"Here's a {query} GIF for you!", color=0xFF5733)
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
            embed = discord.Embed(title=f"Here's a {query} video for you!", color=0xFF5733)
            embed.add_field(name="Video URL", value=video_url, inline=False)
            embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
            embed.set_footer(text=f'{videos.index(video_id) + 1} of {len(videos)}')
            await context.reply(embed=embed)
    except HttpError as error:
        if error.resp.status == 429:
            await context.reply("Too many requests today. Please try again later.")
        else:
            raise error


@client.command(aliases=["ask"])
async def askAI(context, *, prompt):
    if context.channel.id != CHANNEL_ID:
        return
    try:
        openai.api_key = OPEN_API_KEY
        response = openai.Completion.create(
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
            await context.reply(answer)
        else:
            await context.reply("Sorry, I couldn't generate a response. Please try again later.")
    except HttpError as error:
        if error.resp.status == 429:
            await context.reply("Too many requests have been made. Please try again later.")
        else:
            raise error 


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