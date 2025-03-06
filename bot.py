import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", help_command=None, intents=intents)

load_dotenv()


@bot.event
async def on_ready():
    """
    Event triggered when the bot is ready.
    """
    print(f"Logged in as {bot.user.name}")

    channel = bot.get_channel(int(os.getenv("CHANNEL_ID")))

    if channel:
        await channel.send(f"{bot.user.name} is online!")
    else:
        print(f"Could not find channel with provided ID")

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
