import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Initialize Discord bot intents
intents = discord.Intents.default()
# Enable message content intent to allow the bot to read message content
intents.message_content = True

# Create a bot instance with a specified command prefix and intents
bot = commands.Bot(command_prefix=".", intents=intents)

# Load environment variables from the .env file
load_dotenv()


# Event triggered when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    # Retrieve the channel object using the stored CHANNEL_ID from environment variables
    channel = bot.get_channel(int(os.getenv("CHANNEL_ID")))

    # Check if the channel exists, then send an online message
    if channel:
        await channel.send(f"{bot.user.name} is online!")
    else:
        print(f"Could not find channel with provided ID")

    # Load all Python files in the 'cogs' directory as bot extensions
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")


# Run the bot using the Discord bot token from environment variables
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
