import discord
from discord.ext import commands
import random
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="/", intents=intents)

DISCORD_BOT_TOKEN = 'MTA5NjE2NDM3OTE4MDk0MTM4Mw.GwtksM.aq6av9XoWi1Uy7-VCx8Y14wQV0ge99fXvTGbyQ'
GOOGLE_API_KEY = 'AIzaSyCUeJzbNBJ3L1LusiIzeZbW69-nWk4ejH8'
CX = '551d46812ea734e0f'


@client.event
async def on_ready():
    print("CrisisBot is online!")
    channel = client.get_channel(1096284252125012068)
    await channel.send("CrisisBot is online!")


async def fetchRandomMedia(context, search, options):
    service = build("customsearch", "v1",
                    developerKey=GOOGLE_API_KEY).cse()
    try:
        response = service.list(**options).execute()
    except HttpError as error:
        if error.resp.status == 429:
            await context.reply("Too many requests, please try again later.")
        else:
            await context.reply("An unhandled HTTP error occurred: %s" % error)
        return
    response = service.list(**options).execute()
    results = response['items']
    selection = results[random.randint(0, len(results) - 1)]

    embed = discord.Embed(
        title=search, timestamp=context.message.created_at, color=0x0099ff)
    embed.set_image(url=selection['link'])
    embed.set_footer(text=f'{results.index(selection) + 1} of {len(results)}')
    await context.reply(embed=embed)


@client.command(aliases=["image"])
async def randomImage(context, *, search):
    options = {
        'q': search,
        'cx': CX,
        'searchType': 'image',
        'imgSize': 'MEDIUM',
    }
    await fetchRandomMedia(context, search, options)


@client.command(aliases=["gif"])
async def randomGif(context, *, search):
    options = {
        'q': search,
        'cx': CX,
        'searchType': 'image',
        'imgSize': 'MEDIUM',
        'fileType': 'gif'
    }
    await fetchRandomMedia(context, search, options)


@client.command(aliases=["oracle"])
async def magic8Ball(context):
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
async def on_command_error(context, error):
    if isinstance(error, commands.CommandNotFound):
        await context.reply("Invalid command.")
    else:
        await context.reply(f"An unhandled error occurred: {error}")

client.run(DISCORD_BOT_TOKEN)
